"""
LLM Engine — System Siege Integrity API
Provider : Groq  (https://console.groq.com)
Model    : llama-3.3-70b-versatile
Purpose  : Powers interview-consistency scoring and AI-artifact classification.

The API key is never hardcoded. It is supplied at runtime via:
  • POST /api/config/llm   (frontend settings panel, BYOK)
  • GROQ_API_KEY env var   (optional fallback for server operators)
"""

import os
import json
import logging
import urllib.request
import urllib.error
from pathlib import Path

# Load .env on import — works in both reloader parent and child processes
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip())

logger = logging.getLogger(__name__)

# ── Runtime key store (in-memory; survives restarts via env var fallback) ──
_runtime_config: dict = {
    "api_key": os.environ.get("GROQ_API_KEY", ""),
    "provider": "groq",
    "model": os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile"),
}

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def set_llm_config(api_key: str, model: str = "llama-3.3-70b-versatile", provider: str = "groq") -> None:
    """Called by the /api/config/llm endpoint when an evaluator supplies their key."""
    _runtime_config["api_key"] = api_key.strip()
    _runtime_config["model"] = model.strip() or "llama-3.3-70b-versatile"
    _runtime_config["provider"] = provider.strip() or "groq"
    logger.info(f"LLM config updated: provider={provider}, model={model}")


def get_llm_config() -> dict:
    return {
        "provider": _runtime_config["provider"],
        "model": _runtime_config["model"],
        "key_configured": bool(_runtime_config["api_key"]),
    }


def _call_groq(messages: list, max_tokens: int = 512) -> str:
    """
    Direct HTTPS call to Groq chat-completions endpoint.
    Uses stdlib urllib so no extra dependency is required.
    """
    api_key = _runtime_config["api_key"]
    if not api_key:
        raise ValueError("No LLM API key configured. Please add your Groq key in Settings.")

    model = _runtime_config["model"]
    payload = json.dumps({
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }).encode("utf-8")

    req = urllib.request.Request(
        GROQ_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "SystemSiege/1.0 (python-urllib)",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return body["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        logger.error(f"Groq HTTP error {e.code}: {error_body}")
        raise RuntimeError(f"Groq API error {e.code}: {error_body[:200]}")


def llm_evaluate_interview(code: str, qa_responses: list) -> dict:
    """
    Sends candidate code + Q&A explanations to the LLM.
    Returns a structured consistency score, verdict, and reasoning.
    Falls back to rule-based scoring if no key is configured.
    """
    if not _runtime_config["api_key"]:
        logger.warning("LLM key not set — falling back to rule-based interview evaluation.")
        return _rule_based_interview(code, qa_responses)

    qa_text = "\n".join(
        f"Q: {qa.get('q','')}\nA: {qa.get('a','')}" for qa in qa_responses
    )

    system_prompt = (
        "You are an expert technical interviewer and AI-fraud detection engine. "
        "Your job is to evaluate whether a candidate's verbal explanation genuinely "
        "matches their submitted code, or whether there are signs they used an AI tool "
        "(ChatGPT, Copilot, Claude, etc.) without understanding the solution.\n\n"
        "Respond ONLY with a valid JSON object — no markdown, no prose — in this exact shape:\n"
        '{"consistency_score": <int 0-100>, "verdict": "<one sentence>", '
        '"reasoning": "<2-3 sentences>", "red_flags": ["<flag1>", "<flag2>"]}'
    )

    user_prompt = (
        f"## Submitted Code\n```python\n{code[:3000]}\n```\n\n"
        f"## Candidate Explanations\n{qa_text[:2000]}\n\n"
        "Evaluate: Does the explanation demonstrate genuine understanding of this code? "
        "Flag if: explanation uses LLM phrasing ('Certainly', 'Here is a solution'), "
        "uses terminology inconsistent with the code, or cannot articulate the algorithm."
    )

    try:
        raw = _call_groq(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            max_tokens=400,
        )
        # Strip any accidental markdown fences
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(raw)
        score = int(result.get("consistency_score", 70))
        score = max(0, min(100, score))
        return {
            "consistency_score": score,
            "verdict": result.get("verdict", "LLM evaluation complete."),
            "reasoning": result.get("reasoning", ""),
            "red_flags": result.get("red_flags", []),
            "rating": "high" if score >= 70 else "low",
            "powered_by": f"Groq / {_runtime_config['model']}",
        }
    except Exception as e:
        logger.error(f"LLM interview eval failed: {e}", exc_info=True)
        fallback = _rule_based_interview(code, qa_responses)
        fallback["reasoning"] = f"LLM call failed ({e}); rule-based fallback used."
        return fallback


def llm_classify_style(code: str, history_codes: list, rule_result: dict) -> dict:
    """
    Uses the LLM to enhance stylometric analysis with semantic understanding.
    Classifies whether the code reads like AI-generated output vs human-written.
    Falls back to returning the rule_result unchanged if no key is set.
    """
    if not _runtime_config["api_key"]:
        logger.warning("LLM key not set — using rule-based style analysis only.")
        return rule_result

    history_sample = "\n---\n".join(history_codes[:2])[:1500] if history_codes else "No history available."

    system_prompt = (
        "You are a code stylometrics expert specialising in AI-generated code detection. "
        "Respond ONLY with a valid JSON object — no markdown — in this shape:\n"
        '{"ai_likelihood": <int 0-100>, "style_verdict": "<one sentence>", '
        '"indicators": ["<indicator1>", "<indicator2>"]}'
    )

    user_prompt = (
        f"## Current Submission\n```python\n{code[:2000]}\n```\n\n"
        f"## Historical Code (same candidate)\n```python\n{history_sample}\n```\n\n"
        "Assess: Does the current submission look AI-generated compared to the candidate's "
        "history? Check for: overly uniform naming, textbook variable names (node/curr/prev), "
        "unusual comment style, excessive defensive coding, or structural patterns typical of "
        "GPT-4/Claude outputs. Also consider the rule-based pre-scan found these artifacts: "
        f"{rule_result.get('found_artifacts', [])}."
    )

    try:
        raw = _call_groq(
            [{"role": "system", "content": system_prompt},
             {"role": "user", "content": user_prompt}],
            max_tokens=300,
        )
        raw = raw.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        result = json.loads(raw)
        ai_likelihood = int(result.get("ai_likelihood", rule_result["risk_score"]))
        ai_likelihood = max(0, min(100, ai_likelihood))

        enhanced = dict(rule_result)
        enhanced["risk_score"] = ai_likelihood
        enhanced["rating"] = (
            "Stylometric discrepancy detected" if ai_likelihood >= 40
            else "Stylometric profile is consistent"
        )
        enhanced["llm_style_verdict"] = result.get("style_verdict", "")
        enhanced["llm_indicators"] = result.get("indicators", [])
        enhanced["powered_by"] = f"Groq / {_runtime_config['model']}"
        return enhanced
    except Exception as e:
        logger.error(f"LLM style classification failed: {e}", exc_info=True)
        rule_result["llm_style_verdict"] = f"LLM call failed ({e}); rule-based result used."
        return rule_result


# ── Rule-based fallback (used when no API key is present) ──────────────────
def _rule_based_interview(code: str, qa_responses: list) -> dict:
    import re
    explanation_text = " ".join([qa.get("a", "") for qa in qa_responses]).lower()
    score = 90
    verdict = "Answers match code structure."

    if len(explanation_text) < 30:
        score, verdict = 40, "Incomplete reasoning: explanation too brief."
    elif any(p in explanation_text for p in ["certainly", "here's the solution", "let me break"]):
        score, verdict = 20, "Cheating marker: LLM response artifacts in explanation."
    else:
        code_words = set(re.findall(r'\b[a-zA-Z_]\w*\b', code.lower()))
        exp_words = set(re.findall(r'\b\w+\b', explanation_text))
        if len(code_words & exp_words) < 3:
            score, verdict = 50, "Weak alignment: explanation shares few terms with actual code."

    return {
        "consistency_score": score,
        "verdict": verdict,
        "reasoning": "Rule-based evaluation (no LLM key configured).",
        "red_flags": [],
        "rating": "high" if score >= 70 else "low",
        "powered_by": "Rule-based (no API key)",
    }
