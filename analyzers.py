import ast
import re
import difflib
import math

# ─────────────────────────────────────────────
# 1. AST PLAGIARISM CHECKER
# ─────────────────────────────────────────────
class ASTNormalizer(ast.NodeTransformer):
    def __init__(self):
        super().__init__()
        self.name_map = {}
        self.var_counter = 0
        self.arg_counter = 0
        self.func_counter = 0
        self.exclusions = {
            'self','cls','len','range','print','max','min','sum',
            'zip','enumerate','dict','set','list','str','int','float',
            'append','split','join','replace','sorted','reverse','Optional','ListNode'
        }

    def _get_new_name(self, name, prefix):
        if name in self.exclusions:
            return name
        if name not in self.name_map:
            if prefix == 'var':
                self.var_counter += 1
                self.name_map[name] = f"v_{self.var_counter}"
            elif prefix == 'arg':
                self.arg_counter += 1
                self.name_map[name] = f"a_{self.arg_counter}"
            elif prefix == 'func':
                self.func_counter += 1
                self.name_map[name] = f"f_{self.func_counter}"
        return self.name_map.get(name, name)

    def visit_Name(self, node):
        node.id = self._get_new_name(node.id, 'var')
        return self.generic_visit(node)

    def visit_arg(self, node):
        node.arg = self._get_new_name(node.arg, 'arg')
        if node.annotation:
            node.annotation = self.visit(node.annotation)
        return node

    def visit_FunctionDef(self, node):
        if node.name.startswith('_'):
            node.name = self._get_new_name(node.name, 'func')
        node.args = self.visit(node.args)
        node.body = [self.visit(n) for n in node.body]
        return node


def normalize_code_ast(code: str) -> str:
    try:
        parsed = ast.parse(code)
        normalizer = ASTNormalizer()
        normalized_tree = normalizer.visit(parsed)
        return ast.unparse(normalized_tree).strip()
    except Exception:
        stripped = re.sub(r'#.*', '', code)
        stripped = re.sub(r'\s+', '', stripped)
        return stripped

def calculate_ast_similarity(code_a: str, code_b: str) -> float:
    norm_a = normalize_code_ast(code_a)
    norm_b = normalize_code_ast(code_b)
    if not norm_a or not norm_b:
        return 0.0
    matcher = difflib.SequenceMatcher(None, norm_a, norm_b)
    return round(matcher.ratio() * 100, 2)


# ─────────────────────────────────────────────
# 2. VELOCITY + COMPLEXITY MISMATCH ANALYZER
# ─────────────────────────────────────────────
def analyze_velocity(events: list, code_length: int) -> dict:
    if not events:
        return {
            "risk_score": 0, "rating": "No typing logs provided",
            "pasted_chars": 0, "pasted_blocks": 0,
            "corrections": 0, "tab_switches": 0, "paste_ratio": 0,
            "burst_events": [], "complexity_mismatch": False,
            "lines_per_minute": 0, "unnatural_perfection": False
        }

    pasted_chars = 0
    pasted_blocks = 0
    total_typed_chars = 0
    corrections = 0
    tab_switches = 0
    burst_events = []
    timestamps = []

    for ev in events:
        ev_type = ev.get("type", "type")
        ts = ev.get("timestamp", 0)
        timestamps.append(ts)
        if ev_type == "paste":
            content_len = len(ev.get("content") or "")
            pasted_chars += content_len
            pasted_blocks += 1
            if content_len > 80:
                burst_events.append({
                    "timestamp_ms": ts,
                    "chars": content_len,
                    "label": f"Burst paste: {content_len} chars at t={ts}ms"
                })
        elif ev_type == "tab":
            tab_switches += 1
        elif ev_type == "type":
            total_typed_chars += 1
            if ev.get("char") in ["Backspace", "Delete"]:
                corrections += 1

    total_chars = pasted_chars + total_typed_chars
    paste_ratio = pasted_chars / total_chars if total_chars > 0 else 0

    # Lines per minute estimate (complexity/velocity mismatch)
    code_lines = max(1, code_length // 40)
    duration_ms = (max(timestamps) - min(timestamps)) if len(timestamps) > 1 else 1
    duration_min = max(duration_ms / 60000, 0.1)
    lines_per_minute = round(code_lines / duration_min, 1)

    # Unnatural perfection: fast + no corrections + long code
    unnatural_perfection = (lines_per_minute > 30 and corrections == 0 and code_length > 100)

    velocity_risk = 0
    if pasted_blocks > 0:
        velocity_risk += 60 if paste_ratio > 0.7 else 30
    if corrections == 0 and code_length > 100:
        velocity_risk += 20
    if tab_switches > 3:
        velocity_risk += min(20, tab_switches * 5)
    if unnatural_perfection:
        velocity_risk += 15
    velocity_risk = min(100, velocity_risk)

    if velocity_risk >= 70:
        rating = "Critical: massive block paste, zero corrections, unnatural speed."
    elif velocity_risk >= 40:
        rating = "Warning: notable paste bursts or suspicious tab switching."
    else:
        rating = "Normal: steady, incremental keystroke progression."

    return {
        "risk_score": velocity_risk,
        "rating": rating,
        "pasted_chars": pasted_chars,
        "pasted_blocks": pasted_blocks,
        "corrections": corrections,
        "tab_switches": tab_switches,
        "paste_ratio": round(paste_ratio * 100, 2),
        "burst_events": burst_events,
        "lines_per_minute": lines_per_minute,
        "unnatural_perfection": unnatural_perfection
    }


# ─────────────────────────────────────────────
# 3. STYLOMETRICS & PROMPT ARTIFACT SCANNER
# ─────────────────────────────────────────────
def analyze_style_and_artifacts(q5_code: str, history_codes: list) -> dict:
    risk_score = 0
    reasons = []

    # Prompt artifact patterns
    artifact_patterns = [
        r'Certainly', r"Here's a solution", r"Let's break this down",
        r'```python', r'```', r'```sql', r'```javascript',
        r"Let me ", r"Sure,", r"Of course"
    ]
    found_artifacts = []
    for pat in artifact_patterns:
        if re.search(pat, q5_code, re.IGNORECASE):
            found_artifacts.append(pat.replace(r'\\', '').replace('```', 'code-block'))

    if found_artifacts:
        risk_score += 50
        reasons.append(f"Prompt artifacts found: {', '.join(found_artifacts)}")

    # Textbook variable name detection
    textbook_vars = ['node', 'curr', 'prev', 'result', 'temp', 'arr', 'ans', 'res']
    found_textbook = [v for v in textbook_vars if re.search(rf'\b{v}\b', q5_code)]
    if len(found_textbook) >= 3:
        risk_score += 15
        reasons.append(f"Textbook variable names detected: {', '.join(found_textbook)}")

    # Comment density comparison
    def get_comment_density(code):
        lines = [l.strip() for l in code.split('\n') if l.strip()]
        if not lines:
            return 0.0
        comments = [l for l in lines if l.startswith('#') or l.startswith('//') or l.startswith('--')]
        return len(comments) / len(lines)

    q5_density = get_comment_density(q5_code)
    hist_densities = [get_comment_density(c) for c in history_codes if c.strip()]
    if hist_densities:
        avg_hist = sum(hist_densities) / len(hist_densities)
        if abs(q5_density - avg_hist) > 0.25:
            risk_score += 25
            reasons.append(
                f"Comment density mismatch: Q5={round(q5_density*100)}% vs history avg={round(avg_hist*100)}%"
            )

    # Identifier length mismatch
    def get_avg_id_length(code):
        words = re.findall(r'\b[a-zA-Z_][a-zA-Z0-9_]*\b', code)
        kw = {'def','class','return','if','else','elif','for','in','while',
              'import','from','as','try','except','pass','and','or','not'}
        vars_only = [w for w in words if w not in kw]
        return sum(len(v) for v in vars_only) / len(vars_only) if vars_only else 0

    q5_len = get_avg_id_length(q5_code)
    hist_lens = [get_avg_id_length(c) for c in history_codes if c.strip()]
    if hist_lens:
        avg_hist_len = sum(hist_lens) / len(hist_lens)
        if abs(q5_len - avg_hist_len) > 4.0:
            risk_score += 15
            reasons.append(
                f"Identifier length mismatch: Q5={round(q5_len,1)} chars vs history={round(avg_hist_len,1)} chars"
            )

    risk_score = min(100, risk_score)
    return {
        "risk_score": risk_score,
        "rating": "Stylometric discrepancy detected" if risk_score >= 40 else "Stylometric profile is consistent",
        "reasons": reasons,
        "found_artifacts": found_artifacts,
        "q5_comment_density": round(q5_density * 100, 2)
    }


# ─────────────────────────────────────────────
# 4. EXPLANATION DIVERGENCE / INTERVIEW EVALUATOR
# ─────────────────────────────────────────────
def evaluate_interview_consistency(code: str, qa_responses: list) -> dict:
    explanation_text = " ".join([qa.get("a", "") for qa in qa_responses]).lower()

    consistency_score = 90
    verdict = "Answers match code structure."

    if "def reverselist" in code.lower() and "sliding window" in explanation_text:
        consistency_score = 30
        verdict = "Divergence: candidate explains sliding window but code reverses a linked list."
    elif len(explanation_text) < 30:
        consistency_score = 40
        verdict = "Incomplete reasoning: explanation too brief to confirm logic ownership."
    elif any(phrase in explanation_text for phrase in ["certainly", "here's the solution", "let me break"]):
        consistency_score = 20
        verdict = "Cheating marker: explanation contains LLM response artifacts."
    elif len(explanation_text) > 20:
        # Check keyword overlap between code and explanation
        code_words = set(re.findall(r'\b[a-zA-Z_]\w*\b', code.lower()))
        exp_words = set(re.findall(r'\b\w+\b', explanation_text))
        overlap = len(code_words & exp_words)
        if overlap < 3:
            consistency_score = 50
            verdict = "Weak alignment: explanation shares few terms with actual code."

    return {
        "consistency_score": consistency_score,
        "verdict": verdict,
        "rating": "high" if consistency_score >= 70 else "low"
    }


# ─────────────────────────────────────────────
# 5. TRUST GRAPH COMPILER
# ─────────────────────────────────────────────
def generate_trust_graph(candidate_id: str, velocity_data: dict,
                          plagiarism_score: float, style_data: dict,
                          interview_data: dict) -> dict:
    nodes = [{
        "id": "start", "label": "Assessment Started", "type": "info",
        "risk": 0, "x": 100, "y": 150,
        "desc": "Candidate authenticated and started test."
    }]
    links = []
    current_x = 220
    y_toggle = 0
    total_risk = 0

    if velocity_data["risk_score"] > 0:
        nodes.append({
            "id": "velocity", "label": "Keystroke Timing Analysis",
            "type": "danger" if velocity_data["risk_score"] > 50 else "warning",
            "risk": velocity_data["risk_score"],
            "x": current_x, "y": 80 if y_toggle == 0 else 220,
            "desc": f"Pasted {velocity_data['pasted_chars']} chars across "
                    f"{velocity_data['pasted_blocks']} blocks. "
                    f"{velocity_data['tab_switches']} tab switches. "
                    f"{'Unnatural perfection detected.' if velocity_data.get('unnatural_perfection') else ''}"
        })
        links.append({"source": "start", "target": "velocity"})
        total_risk += velocity_data["risk_score"] * 0.35
        current_x += 120
        y_toggle = 1 - y_toggle

    if plagiarism_score > 30:
        parent = "velocity" if any(n["id"] == "velocity" for n in nodes) else "start"
        nodes.append({
            "id": "plagiarism", "label": "AST Plagiarism Checker",
            "type": "danger" if plagiarism_score > 70 else "warning",
            "risk": int(plagiarism_score),
            "x": current_x, "y": 80 if y_toggle == 0 else 220,
            "desc": f"AST structure similarity is {plagiarism_score}% vs reference templates."
        })
        links.append({"source": parent, "target": "plagiarism"})
        total_risk += plagiarism_score * 0.35
        current_x += 120
        y_toggle = 1 - y_toggle

    if style_data["risk_score"] > 0:
        parent = "plagiarism" if any(n["id"] == "plagiarism" for n in nodes) else "start"
        nodes.append({
            "id": "style", "label": "Stylometrics Check",
            "type": "danger" if style_data["risk_score"] > 50 else "warning",
            "risk": style_data["risk_score"],
            "x": current_x, "y": 80 if y_toggle == 0 else 220,
            "desc": "; ".join(style_data["reasons"]) or "Style matches profile."
        })
        links.append({"source": parent, "target": "style"})
        total_risk += style_data["risk_score"] * 0.15
        current_x += 120
        y_toggle = 1 - y_toggle

    if interview_data["consistency_score"] < 100:
        interview_risk = 100 - interview_data["consistency_score"]
        parent = "style" if any(n["id"] == "style" for n in nodes) else "start"
        nodes.append({
            "id": "interview", "label": "AI Explanation Interview",
            "type": "danger" if interview_risk > 50 else "warning",
            "risk": interview_risk,
            "x": current_x, "y": 80 if y_toggle == 0 else 220,
            "desc": f"Consistency score: {interview_data['consistency_score']}%. {interview_data['verdict']}"
        })
        links.append({"source": parent, "target": "interview"})
        total_risk += interview_risk * 0.15
        current_x += 120
        y_toggle = 1 - y_toggle

    final_risk = min(100, int(total_risk))
    status_type = "danger" if final_risk >= 70 else "warning" if final_risk >= 30 else "safe"

    nodes.append({
        "id": "verdict", "label": "Integrity Verdict",
        "type": status_type, "risk": final_risk,
        "x": current_x, "y": 150,
        "desc": f"Final aggregate risk score: {final_risk}%."
    })
    last_id = nodes[-2]["id"] if len(nodes) > 1 else "start"
    links.append({"source": last_id, "target": "verdict"})

    return {
        "nodes": nodes, "links": links,
        "overall_risk": final_risk, "status": status_type
    }


# ─────────────────────────────────────────────
# 6. HUMANE APPROACH EVALUATOR
# ─────────────────────────────────────────────
def evaluate_humane_approach(code: str) -> dict:
    syntax_valid = True
    syntax_error_details = ""
    try:
        ast.parse(code)
    except Exception as e:
        syntax_valid = False
        syntax_error_details = str(e)

    logic_score = 0
    code_lower = code.lower()

    if "def " in code_lower:
        logic_score += 15
    if "for " in code_lower or "while " in code_lower:
        logic_score += 25
    if "if " in code_lower or "elif " in code_lower or "else:" in code_lower:
        logic_score += 20

    pointer_words = ["left","right","seen","map","ans","max_len","char",
                     "seen_chars","l","r","start","end","head","node"]
    logic_score += min(30, sum(1 for w in pointer_words if w in code_lower) * 10)

    if "return " in code_lower:
        logic_score += 10

    logic_score = min(100, logic_score)

    if not syntax_valid:
        if logic_score >= 50:
            verdict = (f"Humane Evaluation: Syntax errors detected ({syntax_error_details}) "
                       f"but candidate shows conceptual approach (Logic: {logic_score}%). "
                       f"Recommended for partial credit.")
        else:
            verdict = (f"Humane Evaluation: Code does not compile and has insufficient "
                       f"logic structure (Logic: {logic_score}%).")
    else:
        logic_score = max(80, logic_score)
        verdict = (f"Humane Evaluation: Code compiles successfully and contains "
                   f"sound logic flow (Logic: {logic_score}%).")

    return {
        "syntax_score": 100 if syntax_valid else 0,
        "logic_score": logic_score,
        "verdict": verdict,
        "syntax_error": syntax_error_details
    }


# ─────────────────────────────────────────────
# 7. LOGIC-BASED SCORING ENGINE
# Breaks down marks by rubric category and
# explains WHY each mark was awarded/deducted.
# ─────────────────────────────────────────────

def score_logic(code: str, test_results: list, reference_code: str) -> dict:
    """
    Evaluates candidate code against a detailed rubric.
    Returns a breakdown of marks per category with reasons.

    Total: 100 marks across 5 categories:
      Correctness       — 40 marks  (test cases)
      Algorithm Logic   — 25 marks  (right approach, right complexity)
      Code Quality      — 15 marks  (naming, comments, structure)
      Edge Cases        — 10 marks  (empty input, single char, all same)
      Efficiency        — 10 marks  (O(n) vs O(n²) patterns)
    """
    breakdown = []
    total = 0

    # ── 1. CORRECTNESS (40 marks) ──────────────────────────────
    passed = sum(1 for t in test_results if t.get("passed"))
    total_cases = max(len(test_results), 1)
    correctness_raw = round((passed / total_cases) * 40)

    reasons_correct = []
    if passed == total_cases:
        reasons_correct.append(f"All {total_cases} test cases passed.")
    elif passed == 0:
        reasons_correct.append("No test cases passed — solution returns wrong output.")
    else:
        reasons_correct.append(f"{passed}/{total_cases} test cases passed.")
        failed = [t for t in test_results if not t.get("passed")]
        for f in failed[:2]:
            reasons_correct.append(
                f"Failed: input={f.get('input','?')} → got {f.get('got','?')}, expected {f.get('expected','?')}"
            )

    breakdown.append({
        "category": "Correctness",
        "max": 40,
        "scored": correctness_raw,
        "pct": round((correctness_raw / 40) * 100),
        "reasons": reasons_correct,
        "icon": "✅" if correctness_raw >= 32 else "⚠️" if correctness_raw >= 16 else "❌"
    })
    total += correctness_raw

    # ── 2. ALGORITHM LOGIC (25 marks) ─────────────────────────
    algo_score = 0
    algo_reasons = []
    code_lower = code.lower()

    # Has a function definition
    
    if has_def:
        algo_score += 5
        algo_reasons.append("+5: Solution is wrapped in a proper function definition.")
    else:
        algo_reasons.append("−5: No function definition found.")

    # Uses a loop (iterative approach)
    has_loop = "for " in code_lower or "while " in code_lower
    if has_loop:
        algo_score += 5
        algo_reasons.append("+5: Iterative approach used (for/while loop present).")
    else:
        algo_reasons.append("−5: No loop detected — solution may be incomplete.")

    # Uses sliding window or two-pointer pattern
    window_words = ["left", "right", "l ", "r ", "window", "start", "end"]
    has_window = any(w in code_lower for w in window_words)
    if has_window:
        algo_score += 8
        algo_reasons.append("+8: Sliding window / two-pointer pattern detected — optimal approach.")
    else:
        algo_reasons.append("−8: No sliding window pattern detected — may be using brute force.")

    # Uses a hash map / dictionary for O(1) lookup
    has_map = "dict" in code_lower or "{}" in code or ": " in code and "map" in code_lower or \
              bool(re.search(r'\w+\s*=\s*\{\}', code)) or \
              bool(re.search(r'\w+\s*=\s*\{\s*\}', code)) or "char_map" in code_lower or \
              "seen" in code_lower or "freq" in code_lower
    if has_map:
        algo_score += 5
        algo_reasons.append("+5: Hash map used for O(1) character lookup — efficient choice.")
    else:
        algo_reasons.append("−5: No hash map detected — lookups may be O(n).")

    # Has a return statement
    has_return = "return " in code_lower
    if has_return:
        algo_score += 2
        algo_reasons.append("+2: Solution returns a result.")
    else:
        algo_reasons.append("−2: No return statement found.")

    breakdown.append({
        "category": "Algorithm Logic",
        "max": 25,
        "scored": min(25, algo_score),
        "pct": round((min(25, algo_score) / 25) * 100),
        "reasons": algo_reasons,
        "icon": "🧠" if algo_score >= 20 else "⚡" if algo_score >= 12 else "❌"
    })
    total += min(25, algo_score)

    # ── 3. CODE QUALITY (15 marks) ─────────────────────────────
    quality_score = 0
    quality_reasons = []

    # Meaningful variable names (not single letters everywhere)
    words = re.findall(r'\b[a-zA-Z_]\w*\b', code)
    long_names = [w for w in words if len(w) > 2 and w not in
                  {'def','for','in','if','else','elif','return','while','and','or',
                   'not','True','False','None','int','str','len','max','min','range'}]
    if len(long_names) >= 3:
        quality_score += 5
        quality_reasons.append(f"+5: Meaningful variable names used (e.g. {', '.join(set(long_names[:3]))}).")
    else:
        quality_reasons.append("−5: Variable names are mostly single letters — poor readability.")

    # Has comments
    comment_lines = [l.strip() for l in code.split('\n') if l.strip().startswith('#')]
    if len(comment_lines) >= 1:
        quality_score += 5
        quality_reasons.append(f"+5: Code is commented ({len(comment_lines)} comment line(s)).")
    else:
        quality_reasons.append("−5: No comments in code — hard to follow reasoning.")

    # Proper indentation (no syntax errors)
    try:
        ast.parse(code)
        quality_score += 5
        quality_reasons.append("+5: Code is syntactically valid and properly indented.")
    except SyntaxError as e:
        quality_reasons.append(f"−5: Syntax error detected — {str(e).split('(')[0].strip()}.")

    breakdown.append({
        "category": "Code Quality",
        "max": 15,
        "scored": quality_score,
        "pct": round((quality_score / 15) * 100),
        "reasons": quality_reasons,
        "icon": "📝" if quality_score >= 12 else "⚡" if quality_score >= 7 else "❌"
    })
    total += quality_score

    # ── 4. EDGE CASES (10 marks) ───────────────────────────────
    edge_score = 0
    edge_reasons = []

    edge_tests = [t for t in test_results if
                  str(t.get("input","")) in ('""', "''", '""', "''", "") or
                  str(t.get("input","")) in ('"a"', "'a'", "a", "b")]
    edge_passed = sum(1 for t in edge_tests if t.get("passed"))

    # Check if code handles empty string
    handles_empty = (
        "if not s" in code_lower or
        "if len(s)" in code_lower or
        any(t.get("passed") and str(t.get("input","")) in ('""',"''","") for t in test_results)
    )
    if handles_empty:
        edge_score += 5
        edge_reasons.append("+5: Empty string edge case handled correctly.")
    else:
        edge_reasons.append("−5: Empty string edge case may not be handled.")

    # Check if all-same-character case passes
    all_same_pass = any(
        t.get("passed") and str(t.get("expected","")) == "1"
        for t in test_results
    )
    if all_same_pass:
        edge_score += 5
        edge_reasons.append("+5: All-same-character input handled correctly (returns 1).")
    else:
        edge_reasons.append("−5: All-same-character case may not return correct result.")

    breakdown.append({
        "category": "Edge Cases",
        "max": 10,
        "scored": edge_score,
        "pct": round((edge_score / 10) * 100),
        "reasons": edge_reasons,
        "icon": "🔬" if edge_score >= 8 else "⚡" if edge_score >= 5 else "❌"
    })
    total += edge_score

    # ── 5. EFFICIENCY (10 marks) ───────────────────────────────
    eff_score = 0
    eff_reasons = []

    # Detect nested loops (O(n²) brute force)
    lines = code.split('\n')
    indent_levels = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("for ") or stripped.startswith("while "):
            indent = len(line) - len(stripped)
            indent_levels.append(indent)

    has_nested_loop = len(indent_levels) >= 2 and len(set(indent_levels)) >= 2
    if has_nested_loop:
        eff_reasons.append("−10: Nested loops detected — likely O(n²) time complexity.")
    else:
        eff_score += 5
        eff_reasons.append("+5: No nested loops — solution runs in at most O(n) per pass.")

    # O(n) space — uses a single hash map
    map_count = len(re.findall(r'\w+\s*=\s*\{', code))
    if map_count == 1:
        eff_score += 5
        eff_reasons.append("+5: Single auxiliary data structure — O(n) space complexity.")
    elif map_count == 0:
        eff_score += 3
        eff_reasons.append("+3: No extra space used (O(1) space), but may sacrifice speed.")
    else:
        eff_reasons.append(f"−2: {map_count} auxiliary structures — slightly higher space usage.")

    breakdown.append({
        "category": "Efficiency",
        "max": 10,
        "scored": eff_score,
        "pct": round((eff_score / 10) * 100),
        "reasons": eff_reasons,
        "icon": "⚡" if eff_score >= 8 else "🐢" if eff_score >= 4 else "❌"
    })
    total += eff_score

    # ── OVERALL GRADE ──────────────────────────────────────────
    total = min(100, total)
    if total >= 85:
        grade, grade_label = "A", "Excellent — strong understanding demonstrated"
    elif total >= 70:
        grade, grade_label = "B", "Good — solid approach with minor gaps"
    elif total >= 55:
        grade, grade_label = "C", "Satisfactory — basic logic present but gaps exist"
    elif total >= 40:
        grade, grade_label = "D", "Below average — partial understanding only"
    else:
        grade, grade_label = "F", "Insufficient — solution does not demonstrate understanding"

    return {
        "total": total,
        "grade": grade,
        "grade_label": grade_label,
        "breakdown": breakdown,
        "max_marks": 100,
    }
