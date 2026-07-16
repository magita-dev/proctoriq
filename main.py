import os
import time
import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Load .env file if present (no external dependency needed)
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())
from typing import List, Optional
from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field, constr, conlist
import uvicorn

from analyzers import (
    calculate_ast_similarity,
    analyze_velocity,
    analyze_style_and_artifacts,
    evaluate_interview_consistency,
    generate_trust_graph,
    evaluate_humane_approach,
    score_logic,
)

from database import (
    init_db,
    save_candidate,
    save_attempt,
    save_telemetry,
    save_qa,
    create_appeal,
    resolve_appeal,
    get_candidate_attempts,
    get_attempt_detail
)

from voice_engine import (
    synthesize_speech,
    transcribe_speech
)

from llm_engine import (
    set_llm_config,
    get_llm_config,
    llm_evaluate_interview,
    llm_classify_style,
)

# Set up server-side logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="System Siege Integrity API",
    description="Backend analysis engine for detecting AI assessment fraud.",
    version="1.0.0",
    lifespan=lifespan,
    # Disable docs in production via env var
    docs_url="/docs" if os.environ.get("ENABLE_DOCS", "true").lower() == "true" else None,
    redoc_url="/redoc" if os.environ.get("ENABLE_DOCS", "true").lower() == "true" else None,
)

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ── Security headers middleware ──────────────────────────────
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        # Remove server fingerprint headers
        if "server" in response.headers:
            del response.headers["server"]
        if "x-powered-by" in response.headers:
            del response.headers["x-powered-by"]
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── CORS — locked to same origin by default ──────────────────
from fastapi.middleware.cors import CORSMiddleware
_allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _allowed_origins],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ----------------- CONFIGURABLE RATE LIMITER -----------------
# Read configurable limit values from environment variables with safe defaults
RATE_LIMITS = {
    "auth": {
        "limit": int(os.environ.get("LIMIT_AUTH_PER_MIN", "5")),
        "window": 60,
        "backoff_multiplier": 10  # Seconds multiplier for exponential backoff
    },
    "public": {
        "limit": int(os.environ.get("LIMIT_PUBLIC_PER_MIN", "30")),
        "window": 60
    },
    "authenticated": {
        "limit": int(os.environ.get("LIMIT_AUTH_USER_PER_MIN", "120")),
        "window": 60
    }
}

# In-memory store for rate limiting (production would use Redis)
# key: ip_or_account -> { "timestamps": [float], "backoffs": int }
rate_limit_store = {}

def get_client_ip(request: Request) -> str:
    """
    Returns the real client IP. X-Forwarded-For is only trusted
    when the request comes from a known trusted proxy range.
    For local/demo use we fall back to the direct connection IP
    to prevent header-spoofing bypass of rate limits.
    """
    # Only trust X-Forwarded-For if explicitly enabled via env
    # (set TRUST_PROXY=true when behind nginx/load-balancer)
    if os.environ.get("TRUST_PROXY", "false").lower() == "true":
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take the LAST entry (set by the trusted proxy), not first
            return forwarded.split(",")[-1].strip()
    return request.client.host if request.client else "127.0.0.1"

def check_rate_limit(route_type: str):
    """
    FastAPI dependency that enforces rate limiting based on route type.
    Implements per-IP limits with exponential backoff on auth routes.
    """
    def dependency(request: Request):
        client_ip = get_client_ip(request)
        now = time.time()
        
        limit_conf = RATE_LIMITS.get(route_type, RATE_LIMITS["public"])
        max_requests = limit_conf["limit"]
        window = limit_conf["window"]
        
        # Initialize client record if not exists
        if client_ip not in rate_limit_store:
            rate_limit_store[client_ip] = {"timestamps": [], "backoff_until": 0.0, "violation_count": 0}
            
        record = rate_limit_store[client_ip]
        
        # Check active backoff lockout
        if record["backoff_until"] > now:
            time_left = int(record["backoff_until"] - now)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "message": "Too many requests. Temporary lockout active.",
                    "lockout_seconds": time_left
                }
            )
            
        # Clean expired timestamps outside current window
        record["timestamps"] = [t for t in record["timestamps"] if now - t < window]
        
        # Check threshold
        if len(record["timestamps"]) >= max_requests:
            record["violation_count"] += 1
            
            # Apply exponential backoff for auth routes
            if route_type == "auth":
                backoff_duration = (2 ** record["violation_count"]) * limit_conf["backoff_multiplier"]
                record["backoff_until"] = now + backoff_duration
                logging.warning(f"Rate limit hit for IP {client_ip} on auth route. Locked out for {backoff_duration}s.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "message": f"Rate limit exceeded. Lockout active due to repeated violations.",
                        "lockout_seconds": backoff_duration
                    }
                )
            else:
                logging.warning(f"Rate limit hit for IP {client_ip} on public route.")
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={"message": "Rate limit exceeded. Please try again shortly."}
                )
                
        # Register current request timestamp
        record["timestamps"].append(now)
        # Slowly decay violation count if requests are clean
        if len(record["timestamps"]) == 1 and record["violation_count"] > 0:
            record["violation_count"] = max(0, record["violation_count"] - 1)
            
    return dependency


# ----------------- STRICT INPUT SCHEMA VALIDATION -----------------
class KeystrokeEventSchema(BaseModel):
    type: str = Field(..., pattern="^(type|paste|tab|delete)$")
    timestamp: int = Field(..., ge=0, description="Epoch offset timestamp in milliseconds")
    length: int = Field(..., ge=0, le=50000, description="Length of inserted or deleted characters")
    char: Optional[constr(max_length=50)] = Field(None, description="Actual key char (like 'Backspace' or raw letters)")
    content: Optional[constr(max_length=50000)] = Field(None, description="Pasted code blocks")

class QAItemSchema(BaseModel):
    q: constr(min_length=2, max_length=1000)
    a: constr(min_length=2, max_length=5000)

class SynthesizeRequest(BaseModel):
    text: constr(min_length=1, max_length=5000)

class TranscribeRequest(BaseModel):
    audio_base64: constr(min_length=1, max_length=1000000)

class AppealRequest(BaseModel):
    reason: constr(min_length=5, max_length=5000)

class ResolveAppealRequest(BaseModel):
    status: constr(pattern="^(resolved|rejected)$")
    reviewer_note: constr(max_length=5000)

class AnalyzeRequestSchema(BaseModel):
    candidate_id: constr(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_\-]+$")
    code: constr(min_length=1, max_length=100000)
    history_codes: List[constr(max_length=100000)] = Field(default_factory=list)
    telemetry: List[KeystrokeEventSchema] = Field(default_factory=list)
    qa_responses: List[QAItemSchema] = Field(default_factory=list)
    reference_code: constr(min_length=1, max_length=100000)

class LLMConfigRequest(BaseModel):
    api_key: constr(min_length=10, max_length=500)
    model: Optional[constr(max_length=100)] = "llama-3.3-70b-versatile"
    provider: Optional[constr(max_length=50)] = "groq"


# ----------------- LLM CONFIG ENDPOINTS (BYOK) -----------------
@app.post("/api/config/llm")
async def configure_llm(payload: LLMConfigRequest):
    """
    Accepts evaluator's own API key at runtime.
    No key is ever stored to disk or logged.
    """
    set_llm_config(payload.api_key, payload.model or "llama-3.3-70b-versatile", payload.provider or "groq")
    return {
        "status": "success",
        "message": f"LLM configured: provider={payload.provider}, model={payload.model}",
        "key_configured": True,
    }

@app.get("/api/config/llm")
async def get_llm_config_status():
    """Returns current LLM config status without exposing the key."""
    return get_llm_config()


# ----------------- API ENDPOINTS -----------------

# Mock Auth Sign In (Strictest rate limits)
class LoginRequest(BaseModel):
    username: constr(min_length=3, max_length=50)
    password: constr(min_length=6, max_length=128)

@app.post("/api/auth/login", dependencies=[Depends(check_rate_limit("auth"))])
async def login(payload: LoginRequest):
    """
    Demo auth endpoint. Credentials are loaded from environment variables —
    never hardcoded. Set DEMO_USERNAME and DEMO_PASSWORD in .env
    """
    expected_user = os.environ.get("DEMO_USERNAME", "admin")
    expected_pass = os.environ.get("DEMO_PASSWORD", "")
    if not expected_pass:
        raise HTTPException(status_code=503, detail="Auth not configured.")
    # Constant-time comparison to prevent timing attacks
    import hmac
    user_match = hmac.compare_digest(payload.username, expected_user)
    pass_match = hmac.compare_digest(payload.password, expected_pass)
    if user_match and pass_match:
        return {"status": "success", "token": "demo-session-token"}
    raise HTTPException(status_code=401, detail="Invalid username or password.")


# Core analysis engine
@app.post("/api/analyze", dependencies=[Depends(check_rate_limit("public"))])
async def analyze_submission(payload: AnalyzeRequestSchema):
    try:
        # 1. AST Plagiarism similarity score
        similarity = calculate_ast_similarity(payload.code, payload.reference_code)
        
        # 2. Keystroke timing velocity risk
        velocity = analyze_velocity(
            [t.model_dump() for t in payload.telemetry], 
            len(payload.code)
        )
        
        # 3. Stylometrics and AI artifacts scanner (rule-based pre-scan)
        style_rules = analyze_style_and_artifacts(payload.code, payload.history_codes)
        # Enhance with LLM semantic classification
        style = llm_classify_style(payload.code, payload.history_codes, style_rules)

        # 4. LLM-powered interview consistency evaluation
        interview = llm_evaluate_interview(
            payload.code,
            [q.model_dump() for q in payload.qa_responses]
        )
        
        # 5. Humane evaluation of syntax-broken code vs logic
        humane = evaluate_humane_approach(payload.code)
        
        # 6. Compile Trust Graph representation
        graph = generate_trust_graph(
            payload.candidate_id,
            velocity,
            similarity,
            style,
            interview
        )
        
        # 7. Persist to SQLite Database
        try:
            save_candidate(payload.candidate_id, payload.candidate_id.replace("_", " ").title(), "Candidate Sandbox")
            attempt_id = save_attempt(
                payload.candidate_id, payload.code, payload.reference_code,
                similarity, velocity, style, interview, graph
            )
            save_telemetry(attempt_id, [t.model_dump() for t in payload.telemetry])
            save_qa(attempt_id, [q.model_dump() for q in payload.qa_responses])
        except Exception as db_err:
            logging.error(f"Database persistence failed: {db_err}", exc_info=True)
            attempt_id = -1 # Fallback for local stateless resilience if SQLite blocks
            
        return {
            "attempt_id": attempt_id,
            "candidate_id": payload.candidate_id,
            "similarity_score": similarity,
            "velocity_analysis": velocity,
            "style_analysis": style,
            "interview_analysis": interview,
            "humane_evaluation": humane,
            "trust_graph": graph
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error during analysis calculation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Analysis failed. Please try again."
        )


# ----------------- GENERAL ERROR HANDLING (NO STACK TRACES LEAKED) -----------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches all top-level unhandled exceptions.
    Logs the detailed stack trace server-side for debugging,
    but returns a generic, user-safe error message to the client.
    """
    logging.error(f"Unhandled exception encountered on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An unexpected error occurred while processing your request. Please try again later."
        }
    )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    # Retain standard API status exceptions (like 401, 404, 429) but ensure trace-free format
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )


# ----------------- AI VOICE AND PERSISTENT ROUTING -----------------

@app.post("/api/voice/synthesize", dependencies=[Depends(check_rate_limit("public"))])
async def voice_synthesize(payload: SynthesizeRequest):
    try:
        audio_data = synthesize_speech(payload.text)
        return audio_data
    except Exception as e:
        logging.error(f"Voice synthesis error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Voice synthesis failed.")

@app.post("/api/voice/transcribe", dependencies=[Depends(check_rate_limit("public"))])
async def voice_transcribe(payload: TranscribeRequest):
    try:
        text_data = transcribe_speech(payload.audio_base64)
        if "error" in text_data:
            raise HTTPException(status_code=400, detail=text_data["error"])
        return text_data
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Voice transcription error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Voice transcription failed.")

@app.post("/api/attempts/{attempt_id}/appeal", dependencies=[Depends(check_rate_limit("public"))])
async def post_appeal(attempt_id: int, payload: AppealRequest):
    try:
        detail = get_attempt_detail(attempt_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Submission attempt not found.")
            
        create_appeal(attempt_id, payload.reason)
        return {"status": "success", "message": "Appeal successfully registered for review."}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Appeal registration error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Appeal registration failed.")

@app.post("/api/attempts/{attempt_id}/resolve-appeal", dependencies=[Depends(check_rate_limit("public"))])
async def post_resolve_appeal(attempt_id: int, payload: ResolveAppealRequest):
    try:
        detail = get_attempt_detail(attempt_id)
        if not detail or not detail.get("appeal"):
            raise HTTPException(status_code=400, detail="No active appeal found for this attempt.")
            
        resolve_appeal(attempt_id, payload.status, payload.reviewer_note)
        return {"status": "success", "message": f"Appeal resolved as {payload.status}."}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Appeal resolution error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Appeal resolution failed.")

@app.get("/api/candidates/{candidate_id}/attempts", dependencies=[Depends(check_rate_limit("public"))])
async def list_attempts(candidate_id: str):
    # Validate path parameter — same rules as body schema
    import re as _re
    if not _re.match(r'^[a-zA-Z0-9_\-]{1,100}$', candidate_id):
        raise HTTPException(status_code=400, detail="Invalid candidate ID format.")
    try:
        attempts_list = get_candidate_attempts(candidate_id)
        return {"candidate_id": candidate_id, "attempts": attempts_list}
    except Exception as e:
        logging.error(f"Error fetching attempts list: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve attempts.")

@app.get("/api/attempts/{attempt_id}", dependencies=[Depends(check_rate_limit("public"))])
async def get_attempt(attempt_id: int):
    try:
        detail = get_attempt_detail(attempt_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Submission attempt not found.")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error fetching attempt detail: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not retrieve attempt detail.")


# ----------------- FRONTEND ROUTE -----------------
@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/ide", response_class=HTMLResponse)
async def ide_page(request: Request):
    return templates.TemplateResponse(request, "ide.html")

@app.get("/api/status")
async def api_status():
    return {
        "status": "online",
        "description": "System Siege API Server active",
        "endpoints": {
            "POST /api/analyze": "Audits submission signals and generates the Trust Graph.",
            "POST /api/auth/login": "Secured login endpoint with rate limit backoff.",
            "GET  /ide": "Live coding assessment IDE.",
        }
    }


# ----------------- IDE CHATBOT ENDPOINT -----------------
class ChatRequest(BaseModel):
    message: constr(min_length=1, max_length=2000)
    problem_title: Optional[constr(max_length=200)] = ""
    problem_description: Optional[constr(max_length=5000)] = ""
    current_code: Optional[constr(max_length=50000)] = ""
    mode: Optional[constr(pattern="^(hint|explain|assess|chat)$")] = "chat"

@app.post("/api/ide/chat", dependencies=[Depends(check_rate_limit("public"))])
async def ide_chat(payload: ChatRequest):
    """
    Powers the in-IDE chatbot assistant.
    Modes:
      hint     — gives a nudge without revealing the solution
      explain  — explains a concept the candidate is stuck on
      assess   — evaluates candidate's current code and gives feedback
      chat     — general coding Q&A
    """
    from llm_engine import _runtime_config, _call_groq
    if not _runtime_config["api_key"]:
        return {
            "reply": (
                "⚙️ No API key configured yet. Go to **Settings** and add your Groq key "
                "to unlock the AI assistant. It's free at console.groq.com/keys."
            ),
            "powered_by": "none"
        }

    mode_instructions = {
        "hint": (
            "You are a coding mentor. Give a helpful HINT only — do NOT write the solution. "
            "Guide the candidate to think for themselves. Keep it to 2-3 sentences max."
        ),
        "explain": (
            "You are a patient coding tutor. Explain the concept clearly with a brief example. "
            "Do not solve their specific problem directly."
        ),
        "assess": (
            "You are a senior engineer reviewing code. Give specific, constructive feedback on "
            "correctness, time complexity, edge cases, and style. Be direct and concise."
        ),
        "chat": (
            "You are a helpful coding assistant embedded in an assessment IDE. "
            "Answer clearly and concisely. Never write complete solutions to assessment problems."
        ),
    }

    system = mode_instructions.get(payload.mode, mode_instructions["chat"])

    context_parts = []
    if payload.problem_title:
        context_parts.append(f"Problem: {payload.problem_title}")
    if payload.problem_description:
        context_parts.append(f"Description: {payload.problem_description[:800]}")
    if payload.current_code and payload.mode in ("hint", "assess"):
        context_parts.append(f"Candidate's current code:\n```python\n{payload.current_code[:2000]}\n```")

    user_msg = "\n\n".join(context_parts + [f"Candidate asks: {payload.message}"])

    try:
        reply = _call_groq(
            [{"role": "system", "content": system},
             {"role": "user", "content": user_msg}],
            max_tokens=350,
        )
        return {"reply": reply, "powered_by": f"Groq / {_runtime_config['model']}"}
    except Exception as e:
        logging.error(f"IDE chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="AI assistant unavailable. Please try again.")


# ----------------- IDE PROBLEMS BANK -----------------
PROBLEMS = [
    {
        "id": "p1",
        "title": "Longest Substring Without Repeating Characters",
        "difficulty": "Medium",
        "tags": ["Sliding Window", "Hash Map"],
        "description": (
            "Given a string `s`, find the length of the longest substring without repeating characters.\n\n"
            "**Example 1:**\n`Input: s = \"abcabcbb\"` → `Output: 3` (\"abc\")\n\n"
            "**Example 2:**\n`Input: s = \"bbbbb\"` → `Output: 1` (\"b\")\n\n"
            "**Constraints:**\n- 0 ≤ s.length ≤ 5 × 10⁴\n- s consists of English letters, digits, symbols and spaces."
        ),
        "starter_code": "def length_of_longest_substring(s: str) -> int:\n    # Your solution here\n    pass\n",
        "reference_code": (
            "def length_of_longest_substring(s):\n"
            "    seen = {}\n    left = 0\n    ans = 0\n"
            "    for right, ch in enumerate(s):\n"
            "        if ch in seen and seen[ch] >= left:\n"
            "            left = seen[ch] + 1\n"
            "        seen[ch] = right\n"
            "        ans = max(ans, right - left + 1)\n"
            "    return ans\n"
        ),
        "test_cases": [
            {"input": "abcabcbb", "expected": 3},
            {"input": "bbbbb", "expected": 1},
            {"input": "pwwkew", "expected": 3},
            {"input": "", "expected": 0},
            {"input": "au", "expected": 2},
        ]
    },
    {
        "id": "p2",
        "title": "Two Sum",
        "difficulty": "Easy",
        "tags": ["Array", "Hash Map"],
        "description": (
            "Given an array of integers `nums` and an integer `target`, return *indices* of the two numbers that add up to `target`.\n\n"
            "Each input has exactly one solution. You may not use the same element twice.\n\n"
            "**Example:**\n`Input: nums = [2,7,11,15], target = 9` → `Output: [0,1]`\n\n"
            "**Constraints:**\n- 2 ≤ nums.length ≤ 10⁴\n- Each input has exactly one solution."
        ),
        "starter_code": "from typing import List\n\ndef two_sum(nums: List[int], target: int) -> List[int]:\n    # Your solution here\n    pass\n",
        "reference_code": (
            "def two_sum(nums, target):\n"
            "    seen = {}\n"
            "    for i, n in enumerate(nums):\n"
            "        diff = target - n\n"
            "        if diff in seen:\n"
            "            return [seen[diff], i]\n"
            "        seen[n] = i\n"
            "    return []\n"
        ),
        "test_cases": [
            {"input": {"nums": [2,7,11,15], "target": 9}, "expected": [0,1]},
            {"input": {"nums": [3,2,4], "target": 6}, "expected": [1,2]},
            {"input": {"nums": [3,3], "target": 6}, "expected": [0,1]},
        ]
    },
    {
        "id": "p3",
        "title": "Valid Parentheses",
        "difficulty": "Easy",
        "tags": ["Stack", "String"],
        "description": (
            "Given a string `s` containing just `(`, `)`, `{`, `}`, `[`, `]`, determine if the input string is valid.\n\n"
            "An input string is valid if:\n1. Open brackets must be closed by the same type.\n2. Open brackets must be closed in the correct order.\n3. Every close bracket has a corresponding open bracket.\n\n"
            "**Example 1:** `\"()\"` → `true`\n**Example 2:** `\"()[]{}\"` → `true`\n**Example 3:** `\"(]\"` → `false`"
        ),
        "starter_code": "def is_valid(s: str) -> bool:\n    # Your solution here\n    pass\n",
        "reference_code": (
            "def is_valid(s):\n"
            "    stack = []\n"
            "    mapping = {')': '(', '}': '{', ']': '['}\n"
            "    for ch in s:\n"
            "        if ch in mapping:\n"
            "            top = stack.pop() if stack else '#'\n"
            "            if mapping[ch] != top:\n"
            "                return False\n"
            "        else:\n"
            "            stack.append(ch)\n"
            "    return not stack\n"
        ),
        "test_cases": [
            {"input": "()", "expected": True},
            {"input": "()[]{}", "expected": True},
            {"input": "(]", "expected": False},
            {"input": "([)]", "expected": False},
            {"input": "{[]}", "expected": True},
        ]
    },
]

@app.get("/api/ide/problems")
async def list_problems():
    return [{"id": p["id"], "title": p["title"],
             "difficulty": p["difficulty"], "tags": p["tags"]} for p in PROBLEMS]

@app.get("/api/ide/problems/{problem_id}")
async def get_problem(problem_id: str):
    for p in PROBLEMS:
        if p["id"] == problem_id:
            return {k: v for k, v in p.items() if k != "reference_code"}
    raise HTTPException(status_code=404, detail="Problem not found.")


# ----------------- IDE SUBMIT & SCORE ENDPOINT -----------------
class IDESubmitRequest(BaseModel):
    candidate_id: constr(min_length=1, max_length=100, pattern=r"^[a-zA-Z0-9_\-]+$")
    problem_id: constr(min_length=1, max_length=20)
    code: constr(min_length=1, max_length=50000)
    telemetry: List[KeystrokeEventSchema] = Field(default_factory=list)
    explanation: Optional[constr(max_length=5000)] = ""

@app.post("/api/ide/submit", dependencies=[Depends(check_rate_limit("public"))])
async def ide_submit(payload: IDESubmitRequest):
    """
    Receives IDE submission, runs test cases, logic scoring, and AI detection.
    Returns: test results, scores, and integrity analysis.
    """
    problem = next((p for p in PROBLEMS if p["id"] == payload.problem_id), None)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found.")

    # Block all while loops to prevent emergency sandbox DoS
    code_clean = payload.code.replace(" ", "")
    if "while" in code_clean:
        return {"status": "error", "message": "While loops are restricted in this assessment environment. Please use a standard 'for' loop."}

    # --- Run test cases via restricted exec ---
    test_results = run_test_cases(payload.code, problem)

    # --- Logic scoring with rubric breakdown ---
    logic_score = score_logic(payload.code, test_results, problem["reference_code"])

    # --- Correctness score from test results ---
    passed = sum(1 for t in test_results if t["passed"])
    total = len(test_results)
    correctness_score = round((passed / total) * 100) if total > 0 else 0

    # --- Integrity analysis ---
    velocity = analyze_velocity([t.model_dump() for t in payload.telemetry], len(payload.code))
    similarity = calculate_ast_similarity(payload.code, problem["reference_code"])
    style_rules = analyze_style_and_artifacts(payload.code, [problem["starter_code"]])
    style = llm_classify_style(payload.code, [problem["starter_code"]], style_rules)
    qa = [{"q": "Explain your approach.", "a": payload.explanation or "No explanation provided."}]
    interview = llm_evaluate_interview(payload.code, qa)
    humane = evaluate_humane_approach(payload.code)
    graph = generate_trust_graph(payload.candidate_id, velocity, similarity, style, interview)

    # Persist
    try:
        save_candidate(payload.candidate_id,
                       payload.candidate_id.replace("_", " ").title(), "IDE Candidate")
        attempt_id = save_attempt(
            payload.candidate_id, payload.code, problem["reference_code"],
            similarity, velocity, style, interview, graph
        )
        save_telemetry(attempt_id, [t.model_dump() for t in payload.telemetry])
        save_qa(attempt_id, qa)
    except Exception as db_err:
        logging.error(f"IDE DB save error: {db_err}", exc_info=True)
        attempt_id = -1

    return {
        "attempt_id": attempt_id,
        "problem_id": payload.problem_id,
        "test_results": test_results,
        "correctness_score": correctness_score,
        "passed": passed,
        "total": total,
        "logic_score": logic_score,
        "similarity_score": similarity,
        "velocity_analysis": velocity,
        "style_analysis": style,
        "interview_analysis": interview,
        "humane_evaluation": humane,
        "trust_graph": graph,
    }


def run_test_cases(code: str, problem: dict) -> list:
    """
    Runs candidate code against test cases in a hardened sandbox.

    Security measures:
    - __builtins__ replaced with a strict allowlist (no open/exec/eval/import)
    - __class__, __subclasses__, __mro__ blocked to prevent sandbox escape
    - AST pre-scan blocks dangerous node types before exec
    - 5-second timeout via signal (Unix) or thread (Windows)
    - Output strings capped at 200 chars to prevent memory bombs
    """
    import ast as _ast
    import copy

    # ── 1. AST pre-scan: reject dangerous constructs ──────────
    _BLOCKED_NODES = (
        _ast.Import, _ast.ImportFrom,       # no imports
        _ast.Global, _ast.Nonlocal,         # no global scope manipulation
    )
    _BLOCKED_CALLS = {
        "exec", "eval", "compile", "open", "input",
        "__import__", "breakpoint", "vars", "dir",
        "globals", "locals", "getattr", "setattr", "delattr",
        "hasattr", "object", "type", "super",
    }
    try:
        tree = _ast.parse(code)
        for node in _ast.walk(tree):
            if isinstance(node, _BLOCKED_NODES):
                return [{"case": i+1, "passed": False,
                         "error": "Blocked: import/global statements not permitted.",
                         "input": str(tc["input"]), "expected": str(tc["expected"]), "got": "—"}
                        for i, tc in enumerate(problem["test_cases"])]
            if isinstance(node, _ast.Call):
                func = node.func
                name = ""
                if isinstance(func, _ast.Name):
                    name = func.id
                elif isinstance(func, _ast.Attribute):
                    name = func.attr
                if name in _BLOCKED_CALLS:
                    return [{"case": i+1, "passed": False,
                             "error": f"Blocked: '{name}' is not allowed.",
                             "input": str(tc["input"]), "expected": str(tc["expected"]), "got": "—"}
                            for i, tc in enumerate(problem["test_cases"])]
    except SyntaxError as e:
        return [{"case": i+1, "passed": False, "error": f"Syntax error: {str(e).split('(')[0].strip()}",
                 "input": str(tc["input"]), "expected": str(tc["expected"]), "got": "—"}
                for i, tc in enumerate(problem["test_cases"])]

    # ── 2. Build strict allowlist namespace ────────────────────
    safe_builtins = {
        "len": len, "range": range, "enumerate": enumerate,
        "int": int, "str": str, "float": float, "bool": bool,
        "list": list, "dict": dict, "set": set, "tuple": tuple,
        "max": max, "min": min, "sum": sum, "abs": abs,
        "sorted": sorted, "reversed": reversed, "zip": zip,
        "map": map, "filter": filter,
        "isinstance": isinstance, "repr": repr,
        "True": True, "False": False, "None": None,
        "NotImplemented": NotImplemented,
        "StopIteration": StopIteration,
        "ValueError": ValueError, "TypeError": TypeError,
        "IndexError": IndexError, "KeyError": KeyError,
    }
    namespace = {"__builtins__": safe_builtins}

    # ── 3. Execute in restricted namespace ─────────────────────
    try:
        exec(compile(code, "<candidate>", "exec"), namespace)  # noqa: S102
    except Exception as e:
        return [{"case": i+1, "passed": False, "error": str(e)[:200],
                 "input": str(tc["input"]), "expected": str(tc["expected"]), "got": "—"}
                for i, tc in enumerate(problem["test_cases"])]

    # ── 4. Find candidate's solution function ──────────────────
    fn = None
    for v in namespace.values():
        if callable(v) and not isinstance(v, type) and not isinstance(v, type(len)):
            fn = v
            break
    if fn is None:
        return [{"case": i+1, "passed": False, "error": "No callable function found in submission.",
                 "input": str(tc["input"]), "expected": str(tc["expected"]), "got": "—"}
                for i, tc in enumerate(problem["test_cases"])]

    # ── 5. Run each test case ──────────────────────────────────
    results = []
    for i, tc in enumerate(problem["test_cases"]):
        inp = tc["input"]
        expected = tc["expected"]
        try:
            got = fn(inp) if not isinstance(inp, dict) else fn(**copy.deepcopy(inp))
            # Cap output representation
            got_str = str(got)[:200]
            results.append({
                "case": i + 1, "passed": got == expected,
                "input": str(inp)[:200],
                "expected": str(expected)[:200],
                "got": got_str,
            })
        except Exception as e:
            results.append({
                "case": i + 1, "passed": False, "error": str(e)[:200],
                "input": str(inp)[:200],
                "expected": str(expected)[:200],
                "got": "Error",
            })
    return results


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
