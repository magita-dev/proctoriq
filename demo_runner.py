import json
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

# Preloaded Preset Datasets
presets = {
    "aria": {
        "candidate_id": "aria_sterling",
        "code": (
            "def max_unique_substring(s):\n"
            "    char_map = {}\n"
            "    left = 0\n"
            "    max_len = 0\n"
            "    \n"
            "    for right in range(len(s)):\n"
            "        # Check if character has been seen in window\n"
            "        if s[right] in char_map and char_map[s[right]] >= left:\n"
            "            left = char_map[s[right]] + 1\n"
            "        char_map[s[right]] = right\n"
            "        max_len = max(max_len, right - left + 1)\n"
            "        \n"
            "    return max_len"
        ),
        "history_codes": [
            "def sum_array(arr):\n    total = 0\n    for item in arr:\n        total += item\n    return total",
            "def find_min(arr):\n    min_val = arr[0]\n    for val in arr:\n      if val < min_val: min_val = val\n    return min_val"
        ],
        "telemetry": [
            {"type": "type", "timestamp": 100, "length": 1, "char": "d"},
            {"type": "type", "timestamp": 350, "length": 1, "char": "e"},
            {"type": "type", "timestamp": 600, "length": 1, "char": "f"},
            {"type": "type", "timestamp": 1100, "length": 1, "char": "m"},
            {"type": "type", "timestamp": 1300, "length": 1, "char": "a"},
            {"type": "type", "timestamp": 1550, "length": 1, "char": "x"}
            # Natural gradual keystrokes (simplified here)
        ],
        "qa_responses": [
            {"q": "Explain your approach in 3-4 sentences.", "a": "I used a sliding window approach with two pointers, left and right. The right pointer expands the window to add elements. When the constraint is violated, I increment the left pointer to shrink the window and restore the constraint, tracking the maximum window size along the way."},
            {"q": "What is the time complexity and why?", "a": "The time complexity is O(N) because both the left and right pointers only move forward. Each element is visited at most twice (once by right, once by left)."},
            {"q": "Why did you choose this data structure?", "a": "I chose a hash map to keep count of character occurrences in O(1) time complexity, making the window validity check instantaneous."}
        ],
        "reference_code": (
            "def longest_substring(string):\n"
            "    seen = set()\n"
            "    l = 0\n"
            "    ans = 0\n"
            "    for r in range(len(string)):\n"
            "        while string[r] in seen:\n"
            "            seen.remove(string[l])\n"
            "            l += 1\n"
            "        seen.add(string[r])\n"
            "        ans = max(ans, r - l + 1)\n"
            "    return ans"
        ),
        "radar_skills": {
            "Algorithms": 85,
            "Data Structures": 90,
            "Debugging": 80,
            "System Design": 75,
            "SQL Optimization": 80,
            "Code Quality": 95,
            "Test Writing": 85
        }
    },
    
    "devon": {
        "candidate_id": "devon_carter",
        "code": (
            "def max_unique_substring(s):\n"
            "    # Textbook LLM Solution\n"
            "    char_map = {}\n"
            "    left = 0\n"
            "    max_len = 0\n"
            "    for right in range(len(s)):\n"
            "        if s[right] in char_map and char_map[s[right]] >= left:\n"
            "            left = char_map[s[right]] + 1\n"
            "        char_map[s[right]] = right\n"
            "        max_len = max(max_len, right - left + 1)\n"
            "    return max_len\n\n"
            "# Certainly! Here is a solution to find the longest unique substring."
        ),
        "history_codes": [
            "def helper(x):\n  return x * 2"
        ],
        "telemetry": [
            {"type": "type", "timestamp": 100, "length": 1, "char": "#"},
            {"type": "type", "timestamp": 300, "length": 1, "char": " "},
            {"type": "type", "timestamp": 500, "length": 1, "char": "I"},
            {"type": "tab", "timestamp": 2000, "length": 0, "char": None}, # Tab switch to ChatGPT
            {"type": "paste", "timestamp": 5000, "length": 395, "content": (
                "def max_unique_substring(s):\n"
                "    # Textbook LLM Solution\n"
                "    char_map = {}\n"
                "    left = 0\n"
                "    max_len = 0\n"
                "    for right in range(len(s)):\n"
                "        if s[right] in char_map and char_map[s[right]] >= left:\n"
                "            left = char_map[s[right]] + 1\n"
                "        char_map[s[right]] = right\n"
                "        max_len = max(max_len, right - left + 1)\n"
                "    return max_len\n\n"
                "# Certainly! Here is a solution to find the longest unique substring."
            )}
        ],
        "qa_responses": [
            {"q": "Explain your approach.", "a": "We declare char_map map pointer values. Then we iterate indexes right pointer and increment left index references, returning max_len space variables."},
            {"q": "What is the time complexity and why?", "a": "The time complexity is O(N) because the node indices are traversed one at a time. Space complexity is O(N) since we allocate maps."},
            {"q": "Why did you choose this data structure?", "a": "A sliding window layout allows memory allocations. Reversing index lists needs maps."}
        ],
        "reference_code": (
            "def max_unique_substring(s):\n"
            "    char_map = {}\n"
            "    left = 0\n"
            "    max_len = 0\n"
            "    for right in range(len(s)):\n"
            "        if s[right] in char_map and char_map[s[right]] >= left:\n"
            "            left = char_map[s[right]] + 1\n"
            "        char_map[s[right]] = right\n"
            "        max_len = max(max_len, right - left + 1)\n"
            "    return max_len"
        ),
        "radar_skills": {
            "Algorithms": 25,
            "Data Structures": 20,
            "Debugging": 15,
            "System Design": 40,
            "SQL Optimization": 20,
            "Code Quality": 30,
            "Test Writing": 15
        }
    },

    "marcus": {
        "candidate_id": "marcus_vance",
        "code": (
            "def max_unique_substring(s):\n"
            "    char_map = {}\n"
            "    left = 0\n"
            "    max_len = 0\n"
            "    \n"
            "    # Manual helper block\n"
            "    for right in range(len(s)):\n"
            "        if s[right] in char_map and char_map[s[right]] >= left:\n"
            "            left = char_map[s[right]] + 1\n"
            "        char_map[s[right]] = right\n"
            "        max_len = max(max_len, right - left + 1)\n"
            "        \n"
            "    return max_len"
        ),
        "history_codes": [
            "def sum_array(arr):\n    total = 0\n    for item in arr:\n        total += item\n    return total"
        ],
        "telemetry": [
            {"type": "type", "timestamp": 100, "length": 1, "char": "d"},
            {"type": "type", "timestamp": 350, "length": 1, "char": "e"},
            {"type": "tab", "timestamp": 3000, "length": 0}, # Tab switches
            {"type": "tab", "timestamp": 5000, "length": 0},
            {"type": "tab", "timestamp": 7000, "length": 0},
            {"type": "paste", "timestamp": 9000, "length": 320, "content": (
                "def max_unique_substring(s):\n"
                "    char_map = {}\n"
                "    left = 0\n"
                "    max_len = 0\n"
                "    \n"
                "    # Manual helper block\n"
                "    for right in range(len(s)):\n"
                "        if s[right] in char_map and char_map[s[right]] >= left:\n"
                "            left = char_map[s[right]] + 1\n"
                "        char_map[s[right]] = right\n"
                "        max_len = max(max_len, right - left + 1)\n"
                "        \n"
                "    return max_len"
            )}
        ],
        "qa_responses": [
            {"q": "Explain your approach in 3-4 sentences.", "a": "I initialized a character index map. As I expand the sliding window, if a character is repeated inside the active frame, I contract left bounds to ensure uniqueness."},
            {"q": "What is the time complexity and why?", "a": "O(N) because the array is parsed once by the boundary offsets."},
            {"q": "Why did you choose this data structure?", "a": "Using mapping dictionary indexes ensures we perform presence tests in constant time."}
        ],
        "reference_code": (
            "def longest_substring(string):\n"
            "    seen = set()\n"
            "    l = 0\n"
            "    ans = 0\n"
            "    for r in range(len(string)):\n"
            "        while string[r] in seen:\n"
            "            seen.remove(string[l])\n"
            "            l += 1\n"
            "        seen.add(string[r])\n"
            "        ans = max(ans, r - l + 1)\n"
            "    return ans"
        ),
        "radar_skills": {
            "Algorithms": 75,
            "Data Structures": 65,
            "Debugging": 80,
            "System Design": 65,
            "SQL Optimization": 90,
            "Code Quality": 70,
            "Test Writing": 60
        }
    }
}


def print_title(text):
    print("=" * 65)
    print(f" {text.upper()} ".center(65, "="))
    print("=" * 65)

def draw_radar_bar(skill, score):
    filled = int(score / 10)
    bar = "#" * filled + "-" * (10 - filled)
    print(f"  {skill:<18} [{bar}] {score}%")

def print_candidate_profile(name, role, analysis_result, skills):
    print(f"\nCandidate: {name}")
    print(f"Role: {role}")

    # Support both the live API response shape and the DB detail shape
    if "velocity_analysis" in analysis_result:
        velocity = analysis_result["velocity_analysis"]
        style = analysis_result["style_analysis"]
        interview = analysis_result["interview_analysis"]
        plagiarism = analysis_result["similarity_score"]
    else:
        # Reconstructed from flat DB columns
        velocity = {
            "risk_score": analysis_result.get("velocity_score", 0),
            "rating": analysis_result.get("velocity_rating", ""),
            "pasted_chars": 0,
            "pasted_blocks": 0,
            "tab_switches": 0,
        }
        style = {
            "risk_score": analysis_result.get("style_score", 0),
            "rating": analysis_result.get("style_rating", ""),
        }
        interview_risk = analysis_result.get("interview_score", 0)
        interview = {
            "consistency_score": 100 - interview_risk,
            "verdict": analysis_result.get("interview_verdict", ""),
        }
        plagiarism = analysis_result.get("similarity_score", 0.0)

    graph = analysis_result.get("trust_graph") or analysis_result.get("trust_graph_json")
    if isinstance(graph, str):
        import json
        graph = json.loads(graph)
    
    # Verdict Status and Risk Score
    status = graph["status"].upper()
    risk = graph["overall_risk"]
    
    status_symbol = "SAFE" if status == "SAFE" else "WARNING" if status == "WARNING" else "CRITICAL"
    print(f"Assessment Status: {status_symbol} (calculated overall risk: {risk}%)")
    
    print("\nAudited Telemetry Metrics:")
    print(f"  +- Timing Velocity  : {velocity['risk_score']}% risk ({velocity['rating']})")
    print(f"  +- AST Similarity   : {plagiarism}% overlap match against reference solutions")
    print(f"  +- Stylometrics     : {style['risk_score']}% risk ({style['rating']})")
    print(f"  +- Interview Match  : {100 - interview['consistency_score']}% mismatch ({interview['verdict']})")
    
    # Print Humane Evaluation if available in response
    if "humane_evaluation" in analysis_result:
        he = analysis_result["humane_evaluation"]
        print(f"  +- Humane Evaluation: Syntax Pass: {he['syntax_score']}% | Logic Score: {he['logic_score']}%")
        print(f"                       Feedback: {he['verdict']}")
    
    print("\nCandidate Skill DNA Profile (Strengths & Gaps radar mapping):")
    for skill, val in skills.items():
        # Scale values down if candidate is caught cheating to demonstrate talent gap correlation
        score = int(val * (100 - risk) / 100) if risk > 50 else val
        draw_radar_bar(skill, score)
        
    print("\nExplainable Trust Graph Representation:")
    for i, node in enumerate(graph["nodes"]):
        indent = " " * (i * 3)
        icon = "[SAFE]" if node["type"] == "safe" else "[WARN]" if node["type"] == "warning" else "[RISK]" if node["type"] == "danger" else "[INFO]"
        risk_tag = f" (+{node['risk']} Risk)" if node['risk'] > 0 else ""
        print(f"  {indent}+-> {icon} [{node['label']}]{risk_tag}")
        print(f"  {indent}    Note: {node['desc']}")
        
    print("\n" + "-" * 65)

def run_preset_demo(preset_id):
    preset = presets[preset_id]
    
    # Strip manual fields that API schema doesn't use
    api_payload = {
        "candidate_id": preset["candidate_id"],
        "code": preset["code"],
        "history_codes": preset["history_codes"],
        "telemetry": preset["telemetry"],
        "qa_responses": preset["qa_responses"],
        "reference_code": preset["reference_code"]
    }
    
    # Call FastAPI local test client
    response = client.post("/api/analyze", json=api_payload)
    if response.status_code != 200:
        print(f"API Call failed on preset {preset_id}: {response.text}")
        return None
        
    return response.json()


import os
from database import init_db

if __name__ == "__main__":
    # 0. Reset SQLite DB before starting demo to guarantee clean logs
    if os.path.exists("system_siege.db"):
        try:
            os.remove("system_siege.db")
            print("[Database] Cleaned system_siege.db from previous runs.")
        except Exception as e:
            print(f"[Database] Could not reset SQLite db: {e}")
            
    # Call init_db to recreate tables for this runner instance
    init_db()
            
    print_title("System Siege Backend Engine Demonstration")
    
    # Preset A: Aria (Honest)
    print("\n\n" + "*" * 65)
    print(" PRESET A: HONEST CANDIDATE ".center(65, "*"))
    print("*" * 65)
    aria_res = run_preset_demo("aria")
    if aria_res:
        print_candidate_profile(
            "Aria Sterling", 
            "Full Stack Engineer", 
            aria_res, 
            presets["aria"]["radar_skills"]
        )
        
        # Feature 11: AI Voice Synthesis demo
        question_text = "Explain your approach in 3-4 sentences."
        print(f"\n[AI Voice Synthesis] Requesting Speech Synthesis for interview question:")
        print(f"   Text: \"{question_text}\"")
        voice_resp = client.post("/api/voice/synthesize", json={"text": question_text})
        if voice_resp.status_code == 200:
            v_data = voice_resp.json()
            # Truncate base64 logs for readability
            b64_trunc = v_data["audio_base64"][:40] + "..."
            print(f"   Success: Formatted audio stream ({v_data['format']}) generated via {v_data['engine']}")
            print(f"   Payload (Base64 audio header): {b64_trunc}")
        else:
            print("   Voice synthesis failed.")
        
    # Preset B: Devon (Cheater)
    print("\n\n" + "*" * 65)
    print(" PRESET B: CHEATER CANDIDATE ".center(65, "*"))
    print("*" * 65)
    devon_res = run_preset_demo("devon")
    if devon_res:
        print_candidate_profile(
            "Devon Carter", 
            "Backend Engineer", 
            devon_res, 
            presets["devon"]["radar_skills"]
        )

    # Preset C: Marcus (Borderline & Appeal)
    print("\n\n" + "*" * 65)
    print(" PRESET C: BORDERLINE CANDIDATE (INITIAL AUDIT) ".center(65, "*"))
    print("*" * 65)
    marcus_res = run_preset_demo("marcus")
    if marcus_res:
        print_candidate_profile(
            "Marcus Vance", 
            "Database Developer", 
            marcus_res, 
            presets["marcus"]["radar_skills"]
        )
        
        attempt_id = marcus_res.get("attempt_id", 1)
        
        # SQLite Query candidate history log
        print(f"\n[SQLite Database] Querying attempt history list for Candidate: marcus_vance")
        hist_resp = client.get("/api/candidates/marcus_vance/attempts")
        if hist_resp.status_code == 200:
            h_data = hist_resp.json()
            print(f"   Found {len(h_data['attempts'])} attempt logs in database.")
            for att in h_data["attempts"]:
                print(f"     +- Attempt #{att['id']}: Calculated Risk = {att['risk_score']}% | Status = {att['status']}")
        
        # Simulate Audio Transcription (STT) Appeal Submission
        print("\n[AI Voice transcription] Transcribing verbal explanation audio submission...")
        mock_audio_input = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGFtZTMuOTguNFVVVVVVVVVV..."
        stt_resp = client.post("/api/voice/transcribe", json={"audio_base64": mock_audio_input})
        appeal_reason = "My local workspace router disconnected. The page reloaded multiple times causing tab switches. I copied code I drafted locally in notepad."
        if stt_resp.status_code == 200:
            stt_data = stt_resp.json()
            print(f"   Transcribed Speech text: \"{stt_data['transcription']}\" (Confidence: {stt_data['confidence'] * 100}%)")
            
        print(f"\n[Appeal] Candidate Marcus Vance submits an appeal for attempt #{attempt_id} flags:")
        print(f"   Appeal notes: \"{appeal_reason}\"")
        client.post(f"/api/attempts/{attempt_id}/appeal", json={"reason": appeal_reason})
        
        # Recruiter resolves appeal via DB write
        print(f"\n[Recruiter] Recruiter processes the appeal for attempt #{attempt_id}, accepts justification.")
        print("[Action] Sending resolution POST request to `/api/attempts/{id}/resolve-appeal`")
        client.post(
            f"/api/attempts/{attempt_id}/resolve-appeal", 
            json={
                "status": "resolved", 
                "reviewer_note": "Flags cleared after manual recruiter appeal validation (approved)."
            }
        )
        
        # Query fresh updated detailed record from DB
        print(f"\n[SQLite Database] Querying updated attempt details for #{attempt_id}...")
        detail_resp = client.get(f"/api/attempts/{attempt_id}")
        if detail_resp.status_code == 200:
            resolved_res = detail_resp.json()
            resolved_radar = presets["marcus"]["radar_skills"]
            
            print("\n" + "*" * 65)
            print(" PRESET C: CANDIDATE STATUS (APPEAL APPROVED - SQLite PULLED) ".center(65, "*"))
            print("*" * 65)
            print_candidate_profile(
                "Marcus Vance", 
                "Database Developer", 
                resolved_res, 
                resolved_radar
            )
        
    print_title("Demonstration finished successfully")
    
    # --- INTERACTIVE USER INPUT AUDITING ---
    print("\n" + "=" * 65)
    print(" CUSTOM SUBMISSION AUDITOR ".center(65, "="))
    print("=" * 65)
    print("You can now enter a custom candidate submission to audit live via the backend!")
    
    try:
        run_custom = input("\nDo you want to audit a custom submission? (y/n): ").strip().lower()
        if run_custom == 'y':
            cand_id = input("Enter candidate name/ID (e.g. custom_eval_1): ").strip()
            cand_id = "".join([c if c.isalnum() or c in ['_', '-'] else '_' for c in cand_id])
            if not cand_id:
                cand_id = "custom_candidate"
                
            print("\nEnter candidate's CODE (type 'END' on a new line when done):")
            code_lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                code_lines.append(line)
            code_text = "\n".join(code_lines)
            
            print("\nEnter REFERENCE standard solution (type 'END' on a new line when done):")
            ref_lines = []
            while True:
                line = input()
                if line.strip() == "END":
                    break
                ref_lines.append(line)
            ref_text = "\n".join(ref_lines)
            if not ref_text.strip():
                ref_text = "def solution():\n    pass"
                
            tabs_count = 0
            try:
                tabs_count = int(input("\nEnter number of window tab switches detected: ") or "0")
            except ValueError:
                pass
                
            pasted = input("Did the candidate copy-paste their solution? (y/n): ").strip().lower() == 'y'
            
            print("\nEnter candidate's explanation: 'Explain your algorithm approach in 3-4 sentences.'")
            exp_text = input().strip()
            if not exp_text:
                exp_text = "Sample explanation text"
            
            # Build telemetry logs
            telemetry = []
            if pasted:
                telemetry.append({"type": "paste", "timestamp": 1000, "length": len(code_text), "content": code_text})
            else:
                for idx, char in enumerate(code_text[:50]):
                    telemetry.append({"type": "type", "timestamp": 100 * idx, "length": 1, "char": char})
                    
            for i in range(tabs_count):
                telemetry.append({"type": "tab", "timestamp": 2000 + i * 500, "length": 0})
                
            custom_payload = {
                "candidate_id": cand_id,
                "code": code_text,
                "history_codes": [
                    "def helper():\n    return 42"
                ],
                "telemetry": telemetry,
                "qa_responses": [
                    {"q": "Explain your approach in 3-4 sentences.", "a": exp_text}
                ],
                "reference_code": ref_text
            }
            
            print("\n🚀 Submitting custom payload to FastAPI `/api/analyze`...")
            response = client.post("/api/analyze", json=custom_payload)
            if response.status_code == 200:
                result = response.json()
                custom_skills = {
                    "Algorithms": 70,
                    "Data Structures": 70,
                    "Debugging": 70,
                    "System Design": 70,
                    "SQL Optimization": 70,
                    "Code Quality": 70,
                    "Test Writing": 70
                }
                print_candidate_profile(
                    cand_id.replace("_", " ").title(), 
                    "Custom Audit Profile", 
                    result, 
                    custom_skills
                )
            else:
                print(f"❌ Custom audit failed: {response.text}")
    except (KeyboardInterrupt, EOFError):
        print("\nExited custom auditor.")

