import pytest
import os
from fastapi.testclient import TestClient
from main import app, rate_limit_store
from database import init_db

client = TestClient(app)

@pytest.fixture(scope="session", autouse=True)
def init_test_db():
    if os.path.exists("system_siege.db"):
        try:
            os.remove("system_siege.db")
        except Exception:
            pass
    init_db()

@pytest.fixture(autouse=True)
def clear_rate_limits():
    rate_limit_store.clear()

# Helper preset data for testing
honest_payload = {
    "candidate_id": "test_aria_sterling",
    "code": "def max_unique_substring(s):\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        if s[right] in char_map and char_map[s[right]] >= left:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len",
    "history_codes": [
        "def helper(x): return x"
    ],
    "telemetry": [
        {"type": "type", "timestamp": 100, "length": 1, "char": "d"},
        {"type": "type", "timestamp": 200, "length": 1, "char": "e"}
    ],
    "qa_responses": [
        {"q": "Explain your approach in 3-4 sentences.", "a": "I used a sliding window approach with two pointers, left and right. The right pointer expands the window to add elements. When the constraint is violated, I increment the left pointer to shrink the window and restore the constraint, tracking the maximum window size along the way."}
    ],
    "reference_code": "def longest_substring(string):\n    seen = set()\n    l = 0\n    ans = 0\n    for r in range(len(string)):\n        while string[r] in seen:\n            seen.remove(string[l])\n            l += 1\n        seen.add(string[r])\n        ans = max(ans, r - l + 1)\n    return ans"
}

cheater_payload = {
    "candidate_id": "test_devon_carter",
    "code": "def max_unique_substring(s):\n    # Textbook LLM Solution\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        if s[right] in char_map and char_map[s[right]] >= left:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len\n\n# Certainly! Here's a solution.",
    "history_codes": [],
    "telemetry": [
        {"type": "type", "timestamp": 100, "length": 1, "char": "#"},
        {"type": "paste", "timestamp": 1000, "length": 300, "content": "def max_unique_substring(s):\n    # Textbook LLM Solution..."}
    ],
    "qa_responses": [
        {"q": "Explain your approach.", "a": "We declare char_map pointer lists. Increment sliding left boundaries."}
    ],
    "reference_code": "def max_unique_substring(s):\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        if s[right] in char_map and char_map[s[right]] >= left:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len"
}

def test_api_static_serve():
    """Verify home page loads static template or message."""
    response = client.get("/")
    assert response.status_code == 200

def test_api_validation_success():
    """Verify validation passes for properly formatted honest payload."""
    response = client.post("/api/analyze", json=honest_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["candidate_id"] == "test_aria_sterling"
    assert data["similarity_score"] < 60  # Different AST topology
    assert data["velocity_analysis"]["risk_score"] <= 40  # Normal typing
    assert data["trust_graph"]["overall_risk"] < 50
    assert data["trust_graph"]["status"] in ("safe", "warning")

def test_api_validation_cheating():
    """Verify cheating payload flags appropriate indicators."""
    response = client.post("/api/analyze", json=cheater_payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["candidate_id"] == "test_devon_carter"
    assert data["similarity_score"] > 80  # Direct AST match
    assert data["velocity_analysis"]["pasted_chars"] > 0
    assert data["style_analysis"]["risk_score"] >= 50  # Found "Certainly" prompt artifact
    assert data["trust_graph"]["overall_risk"] >= 70
    assert data["trust_graph"]["status"] == "danger"

def test_api_strict_validation_reject_invalid_types():
    """Verify schema rejects candidate_id with forbidden special characters (e.g. spaces or symbols)."""
    invalid_payload = honest_payload.copy()
    invalid_payload["candidate_id"] = "invalid candidate id!!"
    
    response = client.post("/api/analyze", json=invalid_payload)
    # Reject with 422 Unprocessable Entity
    assert response.status_code == 422

def test_api_strict_validation_reject_excessive_lengths():
    """Verify schema rejects payload when string boundaries are violated."""
    invalid_payload = honest_payload.copy()
    invalid_payload["code"] = "X" * 150000  # Exceeds max length limit (100000)
    
    response = client.post("/api/analyze", json=invalid_payload)
    assert response.status_code == 422

def test_api_rate_limiting_auth():
    """Verify rate limiter throws 429 after exceeding limit on Login."""
    # Stricter rate limits apply (e.g. 5 requests)
    for _ in range(10):
        response = client.post("/api/auth/login", json={"username": "admin", "password": "wrongpassword"})
        if response.status_code == 429:
            data = response.json()
            assert data["status"] == "error"
            assert "lockout_seconds" in data["message"]
            return
            
    # If we didn't hit it (due to state caching across runs), run again
    pytest.fail("Rate limit 429 was not triggered on repeated invalid auth attempts.")


def test_voice_synthesis_and_transcription():
    """Verify that TTS voice synthesis and STT voice transcription endpoints work cleanly."""
    # 1. Test Voice Synthesis (TTS)
    resp_synth = client.post("/api/voice/synthesize", json={"text": "Synthesize this mock question"})
    assert resp_synth.status_code == 200
    synth_data = resp_synth.json()
    assert "audio_base64" in synth_data
    assert synth_data["format"] == "mp3"
    
    # 2. Test Voice Transcription (STT)
    resp_trans = client.post("/api/voice/transcribe", json={"audio_base64": synth_data["audio_base64"]})
    assert resp_trans.status_code == 200
    trans_data = resp_trans.json()
    assert "transcription" in trans_data
    assert trans_data["confidence"] > 0.5


def test_database_and_appeals_lifecycle():
    """Verify candidate attempt persistence, querying, and recruiter appeals resolution lifecycle."""
    # 1. Post analysis to save in database
    resp_anal = client.post("/api/analyze", json=honest_payload)
    assert resp_anal.status_code == 200
    anal_data = resp_anal.json()
    attempt_id = anal_data["attempt_id"]
    assert attempt_id > 0
    
    # 2. Query attempts list by candidate ID
    resp_list = client.get(f"/api/candidates/{honest_payload['candidate_id']}/attempts")
    assert resp_list.status_code == 200
    list_data = resp_list.json()
    assert len(list_data["attempts"]) > 0
    
    # 3. Retrieve detailed attempt record
    resp_detail = client.get(f"/api/attempts/{attempt_id}")
    assert resp_detail.status_code == 200
    detail_data = resp_detail.json()
    assert detail_data["candidate_id"] == honest_payload["candidate_id"]
    
    # 4. Post an appeal
    resp_appeal = client.post(
        f"/api/attempts/{attempt_id}/appeal",
        json={"reason": "Workspace connection timeout occurred during typing."}
    )
    assert resp_appeal.status_code == 200
    
    # Verify attempt is now under warning status in DB
    resp_detail_2 = client.get(f"/api/attempts/{attempt_id}")
    assert resp_detail_2.status_code == 200
    assert resp_detail_2.json()["status"] == "warning"
    assert resp_detail_2.json()["appeal"] is not None
    
    # 5. Resolve the appeal as approved
    resp_resolve = client.post(
        f"/api/attempts/{attempt_id}/resolve-appeal",
        json={"status": "resolved", "reviewer_note": "Approved router dropout excuse."}
    )
    assert resp_resolve.status_code == 200
    
    # Verify overall risk resets to 15 (safe)
    resp_detail_3 = client.get(f"/api/attempts/{attempt_id}")
    assert resp_detail_3.status_code == 200
    assert resp_detail_3.json()["status"] == "safe"
    assert resp_detail_3.json()["risk_score"] == 15

