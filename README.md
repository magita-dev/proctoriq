# ⚔️ System Siege — AI Assessment Integrity Engine

> **Real-time AI-cheating detection for technical assessments.**  
> Combines a live coding IDE, behavioural telemetry, AST analysis, LLM-powered scoring, and an explainable trust graph — all in one platform.

---

## Table of Contents

1. [What It Does](#what-it-does)
2. [Live Demo URLs](#live-demo-urls)
3. [Tech Stack](#tech-stack)
4. [Architecture & Workflow](#architecture--workflow)
5. [Detection Engines](#detection-engines)
6. [AI / LLM Disclosure (BYOK)](#ai--llm-disclosure-byok)
7. [Project Structure](#project-structure)
8. [API Reference](#api-reference)
9. [Quick Start](#quick-start)
10. [Environment Variables](#environment-variables)
11. [Running Tests](#running-tests)
12. [Security Highlights](#security-highlights)

---

## What It Does

System Siege is a full-stack platform that detects whether a candidate used AI tools (ChatGPT, Copilot, Claude) during a live coding assessment. It does this through **8 layered detection engines**:

| # | Engine | What it catches |
|---|--------|-----------------|
| 1 | **Keystroke Velocity Analysis** | Paste bursts, zero corrections, unnatural speed |
| 2 | **AST Plagiarism Checker** | Structural code similarity vs reference solutions |
| 3 | **Stylometrics Scanner** | Comment density shift, identifier naming patterns |
| 4 | **Prompt Artifact Detection** | "Certainly", markdown fences, textbook variable names |
| 5 | **LLM Interview Consistency** | Explanation doesn't match what the code actually does |
| 6 | **Tab-Switch Correlation** | Context switches right before code appears |
| 7 | **Humane Evaluator** | Gives partial credit for logic even if syntax fails |
| 8 | **Trust Graph Compiler** | Aggregates all signals into a weighted risk score |

The result is an **evidence bundle** recruiters can actually read:  
> *"High risk (87%) — code pasted in 2 bursts, ChatGPT artifacts detected, AST matches reference at 94%, candidate couldn't explain sliding window in follow-up."*

---

## Live Demo URLs

| URL | What you see |
|-----|-------------|
| `http://localhost:8000` | Recruiter dashboard — demo candidates, custom audit, appeals |
| `http://localhost:8000/ide` | Live coding IDE with chatbot assistant |
| `http://localhost:8000/docs` | Interactive Swagger API docs |
| `http://localhost:8000/#settings` | BYOK settings panel |

---

## Tech Stack

### Backend
| Component | Technology |
|-----------|-----------|
| Web framework | **FastAPI** 0.111 (Python 3.10) |
| ASGI server | **Uvicorn** 0.30 with hot-reload |
| Database | **SQLite** via stdlib `sqlite3` |
| HTML templating | **Jinja2** 3.1 |
| Input validation | **Pydantic** v2 strict schemas |
| Rate limiting | Custom in-memory per-IP + exponential backoff |
| LLM calls | **Groq API** via stdlib `urllib` (no SDK needed) |
| Text-to-Speech | **gTTS** 2.5 (Google TTS) |
| Testing | **pytest** 8.2 + **httpx** 0.27 |

### Frontend
| Component | Technology |
|-----------|-----------|
| Code editor | **Monaco Editor** 0.44 (CDN, same engine as VS Code) |
| Styling | Vanilla CSS with CSS custom properties |
| Scripting | Vanilla JavaScript (no framework) |
| Charts | Pure CSS animated SVG rings + bar charts |
| Fonts | System UI stack |

### AI / LLM
| Component | Provider | Model |
|-----------|----------|-------|
| Interview consistency scoring | **Groq** | `llama-3.3-70b-versatile` |
| Stylometric AI classification | **Groq** | `llama-3.3-70b-versatile` |
| IDE hint/explain/assess chatbot | **Groq** | `llama-3.3-70b-versatile` |
| Text-to-Speech | **gTTS** | Google TTS |

---

## Architecture & Workflow

```
┌─────────────────────────────────────────────────────────┐
│                   CANDIDATE FLOW                        │
│                                                         │
│  1. Opens /ide → selects problem → starts coding       │
│  2. Monaco Editor captures every keystroke silently    │
│  3. Paste events, tab switches recorded automatically  │
│  4. Asks chatbot for hints (LLM-powered, hint mode)    │
│  5. Submits code → writes explanation in chat panel    │
│                                                         │
└───────────────────────┬─────────────────────────────────┘
                        │  POST /api/ide/submit
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 ANALYSIS PIPELINE                        │
│                                                         │
│  ┌─────────────────┐   ┌─────────────────┐             │
│  │  Test Runner    │   │ Velocity Analyzer│             │
│  │  (sandboxed     │   │ (paste bursts,  │             │
│  │   Python exec)  │   │  tab switches,  │             │
│  │                 │   │  corrections)   │             │
│  └────────┬────────┘   └────────┬────────┘             │
│           │                     │                       │
│  ┌────────▼────────┐   ┌────────▼────────┐             │
│  │  AST Plagiarism │   │  Stylometrics   │             │
│  │  (normalize →   │   │  + LLM classify │             │
│  │   SequenceMatch)│   │  (Groq API)     │             │
│  └────────┬────────┘   └────────┬────────┘             │
│           │                     │                       │
│  ┌────────▼─────────────────────▼────────┐             │
│  │        LLM Interview Evaluator        │             │
│  │   (code + explanation → Groq LLM)     │             │
│  │   Returns: score, verdict, red_flags  │             │
│  └────────────────────┬──────────────────┘             │
│                       │                                 │
│  ┌────────────────────▼──────────────────┐             │
│  │         Trust Graph Compiler          │             │
│  │   Weights: velocity×0.35 + AST×0.35  │             │
│  │            style×0.15 + interview×0.15│             │
│  │   Output: nodes, links, overall_risk  │             │
│  └────────────────────┬──────────────────┘             │
│                       │                                 │
│  ┌────────────────────▼──────────────────┐             │
│  │         SQLite Persistence            │             │
│  │   candidates / attempts / telemetry   │             │
│  │   interview_answers / appeals         │             │
│  └───────────────────────────────────────┘             │
└───────────────────────┬─────────────────────────────────┘
                        │  JSON response
                        ▼
┌─────────────────────────────────────────────────────────┐
│                  RECRUITER VIEW (/ide)                   │
│                                                         │
│  • Test results (pass/fail per case)                   │
│  • Integrity panel: risk score + 4 sub-scores          │
│  • Evidence bundle: human-readable flag list           │
│  • LLM verdict + reasoning                             │
│                                                         │
│                  RECRUITER VIEW (/)                     │
│                                                         │
│  • Trust graph (visual node chain)                     │
│  • Skill DNA radar (adjusted for cheating)             │
│  • Appeal submit → approve/reject lifecycle            │
│  • Voice TTS/STT demo                                  │
└─────────────────────────────────────────────────────────┘
```

### Telemetry Capture (automatic, invisible to candidate)

Every event in the Monaco editor is logged client-side and sent with the submission:

```
type: "type"   → single keypress
type: "paste"  → insert > 60 chars at once  ← HIGH SIGNAL
type: "delete" → backspace/delete
type: "tab"    → browser tab hidden event   ← HIGH SIGNAL
```

A candidate who types their own solution produces a gradual histogram: `5% → 8% → 12% → 19%...`  
A candidate who pastes from ChatGPT produces: `2% → 2% → 2% → 98%` ← flagged immediately.

### Appeal Flow

```
Submission flagged (WARNING/DANGER)
        ↓
Candidate submits appeal reason via UI
        ↓
Recruiter reviews → Approve or Reject
        ↓
If Approved: risk_score reset to 15, status → SAFE
If Rejected: status → DANGER, flags upheld
        ↓
Full audit trail stored in SQLite
```

---

## Detection Engines

### 1. Keystroke Velocity Analyzer (`analyzers.py`)
- Tracks every paste event, tab switch, and backspace
- Calculates paste ratio: `pasted_chars / total_chars`
- Flags `unnatural_perfection`: >30 lines/min with zero corrections
- Risk contribution: **35% of overall score**

### 2. AST Plagiarism Checker (`analyzers.py`)
- Parses candidate code into Python AST
- Normalises variable names, argument names, helper function names
- Runs `difflib.SequenceMatcher` on normalised trees
- Catches renamed variables — structure similarity still exposed
- Risk contribution: **35% of overall score**

### 3. Stylometrics & Artifact Scanner (`analyzers.py`)
- Regex scan for LLM phrasing: `"Certainly"`, ` ```python`, `"Here's a solution"`
- Comment density comparison vs candidate's history
- Identifier name length distribution comparison
- Enhanced by **Groq LLM** semantic classification
- Risk contribution: **15% of overall score**

### 4. LLM Interview Consistency (`llm_engine.py`)
- Sends code + Q&A explanation to `llama-3.3-70b-versatile`
- LLM returns: `consistency_score`, `verdict`, `reasoning`, `red_flags[]`
- Fallback to rule-based scoring if no API key configured
- Risk contribution: **15% of overall score**

### 5. Humane Evaluator (`analyzers.py`)
- Checks syntax validity via `ast.parse()`
- Scores logic keywords: `def`, `for/while`, `if/elif`, pointer words
- Gives partial credit even if code has syntax errors
- Ensures candidates aren't penalised for minor bugs

### 6. Trust Graph Compiler (`analyzers.py`)
```
final_risk = (velocity × 0.35) + (AST × 0.35) + (style × 0.15) + (interview_risk × 0.15)
```
Output is a JSON graph with nodes and links, rendered as a visual chain in the UI.

---

## AI / LLM Disclosure (BYOK)

**No API key is hardcoded.** Keys are supplied at runtime via:

1. **Frontend Settings panel** → `http://localhost:8000/#settings`
2. **Environment variable** → `GROQ_API_KEY=gsk_...`

The key is stored in memory only — never written to disk, never logged, never returned via API.

| Feature | Provider | Model | Version |
|---------|----------|-------|---------|
| Interview scoring | Groq | `llama-3.3-70b-versatile` | Meta Llama 3.3 70B |
| Style classification | Groq | `llama-3.3-70b-versatile` | Meta Llama 3.3 70B |
| IDE chatbot | Groq | `llama-3.3-70b-versatile` | Meta Llama 3.3 70B |

**For evaluators:** Go to Settings, paste your free Groq key (get one at [console.groq.com/keys](https://console.groq.com/keys)), select model, click Save. All AI features activate immediately — no server restart needed.

---

## Project Structure

```
system seige/
├── main.py              ← FastAPI app, all routes, rate limiting, schemas
├── analyzers.py         ← AST checker, velocity, stylometrics, trust graph, humane eval
├── llm_engine.py        ← Groq API calls, BYOK config, rule-based fallbacks
├── database.py          ← SQLite schema + all CRUD helpers
├── voice_engine.py      ← gTTS text-to-speech + mock STT transcription
├── demo_runner.py       ← CLI demo: runs Aria, Devon, Marcus presets
├── test_main.py         ← pytest test suite (8 tests)
├── requirements.txt     ← Pinned dependencies
├── README.md            ← This file
├── system_siege.db      ← SQLite database (auto-created on startup)
│
├── templates/
│   ├── index.html       ← Recruiter dashboard (demo + audit + settings)
│   └── ide.html         ← Live coding IDE with chatbot
│
└── static/
    ├── css/
    │   ├── style.css    ← Main dashboard styles
    │   └── ide.css      ← IDE-specific layout styles
    └── js/
        ├── app.js       ← Dashboard logic (presets, appeals, voice, settings)
        └── ide.js       ← IDE logic (Monaco, telemetry, submission, chatbot)
```

---

## API Reference

### Core

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Recruiter dashboard UI |
| `GET` | `/ide` | Live coding IDE |
| `GET` | `/docs` | Swagger interactive docs |
| `GET` | `/api/status` | Health check |

### Analysis

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/analyze` | Full integrity audit (custom submission) |
| `POST` | `/api/ide/submit` | IDE submission: test cases + integrity |
| `GET` | `/api/ide/problems` | List all problems |
| `GET` | `/api/ide/problems/{id}` | Get single problem |

### Database

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/candidates/{id}/attempts` | List candidate's attempts |
| `GET` | `/api/attempts/{id}` | Get attempt details |
| `POST` | `/api/attempts/{id}/appeal` | Submit appeal |
| `POST` | `/api/attempts/{id}/resolve-appeal` | Approve or reject appeal |

### AI Config (BYOK)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/config/llm` | Set API key + model at runtime |
| `GET` | `/api/config/llm` | Get config status (key presence, not value) |
| `POST` | `/api/ide/chat` | IDE chatbot (hint/explain/assess/chat) |

### Auth & Voice

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login` | Rate-limited login (demo) |
| `POST` | `/api/voice/synthesize` | Text → Speech (gTTS) |
| `POST` | `/api/voice/transcribe` | Speech → Text (simulated STT) |

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Set Groq API key as env var
set GROQ_API_KEY=gsk_your_key_here      # Windows
export GROQ_API_KEY=gsk_your_key_here   # Mac/Linux

# 3. Start the server
python main.py

# 4. Open in browser
# Dashboard:  http://localhost:8000
# IDE:        http://localhost:8000/ide
# API Docs:   http://localhost:8000/docs
```

Or run the terminal demo (no browser needed):

```bash
python demo_runner.py
```

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | — | Groq API key (can also be set via UI) |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Override default LLM model |
| `LIMIT_AUTH_PER_MIN` | `5` | Max login attempts per minute per IP |
| `LIMIT_PUBLIC_PER_MIN` | `30` | Max requests/min on public endpoints |
| `LIMIT_AUTH_USER_PER_MIN` | `120` | Max requests/min for authenticated actions |

---

## Running Tests

```bash
python -m pytest test_main.py -v
```

**8 tests covering:**
- ✅ Frontend page loads (HTTP 200)
- ✅ Honest candidate scores as SAFE
- ✅ Cheater candidate scores as DANGER (pasted + artifacts)
- ✅ Invalid candidate ID rejected (422)
- ✅ Oversized payload rejected (422)
- ✅ Auth rate limiter triggers 429 with lockout
- ✅ TTS synthesis + STT transcription endpoints
- ✅ Full DB lifecycle: save → query → appeal → resolve

---

## Security Highlights

| Concern | Implementation |
|---------|---------------|
| Input validation | Pydantic strict schemas: type, length, regex pattern on every field |
| Rate limiting | Per-IP limits with exponential backoff on auth routes — configurable via env vars |
| Error handling | Global exception handler returns generic messages; full traces logged server-side only |
| Secrets | No hardcoded keys; API key stored in memory only, never returned via API |
| Code execution | Test runner uses restricted `__builtins__` namespace — no file I/O, no imports |
| SQL injection | All queries use parameterised statements via `sqlite3` |
| Stack trace leakage | Custom HTTP exception handler strips all internal details from responses |
