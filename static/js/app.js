// ===== SYSTEM SIEGE FRONTEND ENGINE =====
// State
let currentAttemptId = null;
let currentCandidate = null;
let statsAnalyzed = 0;
let statsFlagged = 0;

// Preset payloads matching demo_runner.py
const PRESETS = {
  aria: {
    name: "Aria Sterling", role: "Full Stack Engineer",
    skills: { Algorithms:85, "Data Structures":90, Debugging:80, "System Design":75, "SQL Optimization":80, "Code Quality":95, "Test Writing":85 },
    payload: {
      candidate_id: "aria_sterling",
      code: "def max_unique_substring(s):\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        if s[right] in char_map and char_map[s[right]] >= left:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len",
      history_codes: [
        "def sum_array(arr):\n    total = 0\n    for item in arr:\n        total += item\n    return total",
        "def find_min(arr):\n    min_val = arr[0]\n    for val in arr:\n      if val < min_val: min_val = val\n    return min_val"
      ],
      telemetry: [
        {type:"type",timestamp:100,length:1,char:"d"},
        {type:"type",timestamp:350,length:1,char:"e"},
        {type:"type",timestamp:600,length:1,char:"f"},
        {type:"type",timestamp:1100,length:1,char:"m"},
        {type:"type",timestamp:1300,length:1,char:"a"},
        {type:"type",timestamp:1550,length:1,char:"x"}
      ],
      qa_responses: [
        {q:"Explain your approach in 3-4 sentences.",a:"I used a sliding window approach with two pointers, left and right. The right pointer expands the window to add elements. When the constraint is violated, I increment the left pointer to shrink the window and restore the constraint, tracking the maximum window size along the way."},
        {q:"What is the time complexity and why?",a:"The time complexity is O(N) because both the left and right pointers only move forward. Each element is visited at most twice."},
        {q:"Why did you choose this data structure?",a:"I chose a hash map to keep count of character occurrences in O(1) time, making the window validity check instantaneous."}
      ],
      reference_code: "def longest_substring(string):\n    seen = set()\n    l = 0\n    ans = 0\n    for r in range(len(string)):\n        while string[r] in seen:\n            seen.remove(string[l])\n            l += 1\n        seen.add(string[r])\n        ans = max(ans, r - l + 1)\n    return ans"
    }
  },
  devon: {
    name: "Devon Carter", role: "Backend Engineer",
    skills: { Algorithms:25, "Data Structures":20, Debugging:15, "System Design":40, "SQL Optimization":20, "Code Quality":30, "Test Writing":15 },
    payload: {
      candidate_id: "devon_carter",
      code: "def max_unique_substring(s):\n    # Textbook LLM Solution\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        if s[right] in char_map and char_map[s[right]] >= left:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len\n\n# Certainly! Here is a solution to find the longest unique substring.",
      history_codes: ["def helper(x):\n  return x * 2"],
      telemetry: [
        {type:"type",timestamp:100,length:1,char:"#"},
        {type:"type",timestamp:300,length:1,char:" "},
        {type:"tab",timestamp:2000,length:0,char:null},
        {type:"paste",timestamp:5000,length:395,content:"def max_unique_substring(s):\n    # Textbook LLM Solution\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        if s[right] in char_map and char_map[s[right]] >= left:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len\n\n# Certainly! Here is a solution."}
      ],
      qa_responses: [
        {q:"Explain your approach.",a:"We declare char_map map pointer values. Then we iterate indexes right pointer and increment left index references, returning max_len space variables."},
        {q:"What is the time complexity and why?",a:"The time complexity is O(N) because the node indices are traversed one at a time."},
        {q:"Why did you choose this data structure?",a:"A sliding window layout allows memory allocations. Reversing index lists needs maps."}
      ],
      reference_code: "def max_unique_substring(s):\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        if s[right] in char_map and char_map[s[right]] >= left:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len"
    }
  },
  marcus: {
    name: "Marcus Vance", role: "Database Developer",
    skills: { Algorithms:75, "Data Structures":65, Debugging:80, "System Design":65, "SQL Optimization":90, "Code Quality":70, "Test Writing":60 },
    payload: {
      candidate_id: "marcus_vance",
      code: "def max_unique_substring(s):\n    char_map = {}\n    left = 0\n    max_len = 0\n    # Manual helper block\n    for right in range(len(s)):\n        if s[right] in char_map and char_map[s[right]] >= left:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len",
      history_codes: ["def sum_array(arr):\n    total = 0\n    for item in arr:\n        total += item\n    return total"],
      telemetry: [
        {type:"type",timestamp:100,length:1,char:"d"},
        {type:"type",timestamp:350,length:1,char:"e"},
        {type:"tab",timestamp:3000,length:0},
        {type:"tab",timestamp:5000,length:0},
        {type:"tab",timestamp:7000,length:0},
        {type:"paste",timestamp:9000,length:320,content:"def max_unique_substring(s):\n    char_map = {}\n    left = 0\n    max_len = 0\n    for right in range(len(s)):\n        if s[right] in char_map:\n            left = char_map[s[right]] + 1\n        char_map[s[right]] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len"}
      ],
      qa_responses: [
        {q:"Explain your approach in 3-4 sentences.",a:"I initialized a character index map. As I expand the sliding window, if a character is repeated inside the active frame, I contract left bounds to ensure uniqueness."},
        {q:"What is the time complexity and why?",a:"O(N) because the array is parsed once by the boundary offsets."},
        {q:"Why did you choose this data structure?",a:"Using mapping dictionary indexes ensures we perform presence tests in constant time."}
      ],
      reference_code: "def longest_substring(string):\n    seen = set()\n    l = 0\n    ans = 0\n    for r in range(len(string)):\n        while string[r] in seen:\n            seen.remove(string[l])\n            l += 1\n        seen.add(string[r])\n        ans = max(ans, r - l + 1)\n    return ans"
    }
  }
};

// ===== UTILITY HELPERS =====
function esc(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function showLoader(msg = "Analyzing submission...") {
  document.getElementById("loader").classList.remove("hidden");
  document.getElementById("loader-msg").textContent = msg;
}
function hideLoader() { document.getElementById("loader").classList.add("hidden"); }

function showToast(msg, type = "ok") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = `toast ${type}`;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 3500);
}

function getRiskColor(risk) {
  if (risk >= 70) return "var(--danger)";
  if (risk >= 30) return "var(--warning)";
  return "var(--safe)";
}

function getRiskClass(risk) {
  if (risk >= 70) return "danger";
  if (risk >= 30) return "warning";
  return "safe";
}

function getStatusLabel(status) {
  if (status === "danger") return "⚠ CRITICAL RISK";
  if (status === "warning") return "⚡ WARNING";
  return "✅ SAFE";
}

// Animated ring fill (SVG stroke-dashoffset trick)
function animateRing(fillId, valId, pct, riskClass) {
  const circumference = 2 * Math.PI * 42; // r=42
  const fill = document.getElementById(fillId);
  const val = document.getElementById(valId);
  if (!fill || !val) return;
  fill.style.strokeDasharray = circumference;
  fill.style.strokeDashoffset = circumference - (pct / 100) * circumference;
  fill.style.stroke = getRiskColor(pct);
  val.textContent = Math.round(pct) + "%";
  val.style.color = getRiskColor(pct);
}

// ===== RENDER RESULTS =====
function renderResults(data, presetKey) {
  const preset = PRESETS[presetKey] || {};
  const name = preset.name || data.candidate_id;
  const role = preset.role || "Candidate";
  const skills = preset.skills || {};

  const graph = data.trust_graph;
  const velocity = data.velocity_analysis;
  const style = data.style_analysis;
  const interview = data.interview_analysis;
  const humane = data.humane_evaluation;
  const overall = graph.overall_risk;
  const statusCls = getRiskClass(overall);

  // Header
  document.getElementById("res-name").textContent = name;
  document.getElementById("res-role").textContent = role;
  const badge = document.getElementById("res-badge");
  badge.textContent = getStatusLabel(graph.status);
  badge.className = `verdict-badge ${statusCls}`;

  // Rings
  setTimeout(() => {
    animateRing("ring-overall-fill", "ring-overall-val", overall, statusCls);
    animateRing("ring-sim-fill", "ring-sim-val", data.similarity_score, getRiskClass(data.similarity_score));
    animateRing("ring-vel-fill", "ring-vel-val", velocity.risk_score, getRiskClass(velocity.risk_score));
    animateRing("ring-style-fill", "ring-style-val", style.risk_score, getRiskClass(style.risk_score));
  }, 100);

  // Trust graph nodes
  const nodeIcons = { safe:"✅", warning:"⚡", danger:"🚨", info:"ℹ️" };
  const graphEl = document.getElementById("trust-graph-nodes");
  graphEl.innerHTML = graph.nodes.map(n => `
    <div class="trust-node ${esc(n.type)}">
      <div class="node-icon">${nodeIcons[n.type] || "🔵"}</div>
      <div class="node-body">
        <div class="node-label">${esc(n.label)}</div>
        <div class="node-desc">${esc(n.desc)}</div>
      </div>
      ${n.risk > 0 ? `<div class="node-risk ${getRiskClass(n.risk)}">+${esc(n.risk)} Risk</div>` : ''}
    </div>
  `).join("");

  // Skill radar
  const radarEl = document.getElementById("radar-bars");
  const adjustedSkills = Object.entries(skills).map(([k, v]) => ({
    name: k,
    val: overall > 50 ? Math.max(5, Math.round(v * (100 - overall) / 100)) : v
  }));
  radarEl.innerHTML = adjustedSkills.map(s => `
    <div class="radar-row">
      <div class="radar-skill">${s.name}</div>
      <div class="radar-track"><div class="radar-fill" style="width:0%;background:${getRiskColor(100 - s.val)}" data-target="${s.val}"></div></div>
      <div class="radar-val" style="color:${getRiskColor(100 - s.val)}">${s.val}%</div>
    </div>
  `).join("");
  setTimeout(() => {
    radarEl.querySelectorAll(".radar-fill").forEach(el => {
      el.style.width = el.dataset.target + "%";
    });
  }, 150);

  // Telemetry
  document.getElementById("telemetry-detail").innerHTML = `
    <div class="tele-chip"><div class="tele-label">Pasted Chars</div><div class="tele-val" style="color:${velocity.pasted_chars > 0 ? 'var(--danger)' : 'var(--safe)'}">${velocity.pasted_chars}</div></div>
    <div class="tele-chip"><div class="tele-label">Paste Blocks</div><div class="tele-val" style="color:${velocity.pasted_blocks > 0 ? 'var(--danger)' : 'var(--safe)'}">${velocity.pasted_blocks}</div></div>
    <div class="tele-chip"><div class="tele-label">Tab Switches</div><div class="tele-val" style="color:${velocity.tab_switches > 2 ? 'var(--warning)' : 'var(--safe)'}">${velocity.tab_switches}</div></div>
    <div class="tele-chip"><div class="tele-label">Corrections</div><div class="tele-val">${velocity.corrections || 0}</div></div>
    <div class="tele-chip"><div class="tele-label">Paste Ratio</div><div class="tele-val" style="color:${velocity.paste_ratio > 50 ? 'var(--danger)' : 'var(--safe)'}">${velocity.paste_ratio}%</div></div>
    <div class="tele-chip"><div class="tele-label">Interview Match</div><div class="tele-val" style="color:${interview.consistency_score < 60 ? 'var(--danger)' : 'var(--safe)'}">${interview.consistency_score}%${getLLMBadge(interview.powered_by)}</div></div>
  `;

  // Humane evaluation
  if (humane) {
    document.getElementById("humane-detail").innerHTML = `
      <div class="humane-box">
        <div class="humane-scores">
          <div class="humane-score"><span>Syntax Score</span><strong style="color:${humane.syntax_score === 100 ? 'var(--safe)' : 'var(--danger)'}">${humane.syntax_score}%</strong></div>
          <div class="humane-score"><span>Logic Score</span><strong style="color:${getRiskColor(100 - humane.logic_score)}">${humane.logic_score}%</strong></div>
        </div>
        <div class="humane-verdict">${humane.verdict}</div>
      </div>
    `;
  }

  // Evidence bundle
  const evidenceItems = buildEvidenceBundle(data, overall);
  const existingBundle = document.querySelector(".evidence-bundle");
  if (existingBundle) existingBundle.remove();
  const bundleHtml = `
    <div class="evidence-bundle">
      <h4>📋 Evidence Bundle — ${statusCls === 'danger' ? 'High' : statusCls === 'warning' ? 'Medium' : 'Low'} Risk (${overall}%)</h4>
      ${evidenceItems.map(e => `
        <div class="evidence-item">
          <div class="evidence-icon">${e.icon}</div>
          <div class="evidence-text">${e.text}</div>
        </div>
      `).join("")}
    </div>
  `;
  document.getElementById("trust-graph-nodes").insertAdjacentHTML("afterend", bundleHtml);

  // Appeal panel — show for warning/borderline
  const appealPanel = document.getElementById("appeal-panel");
  if (graph.status === "warning" || graph.status === "danger") {
    appealPanel.classList.remove("hidden");
  } else {
    appealPanel.classList.add("hidden");
  }

  // Show the panel
  const panel = document.getElementById("results-panel");
  panel.classList.remove("hidden");
  panel.scrollIntoView({ behavior: "smooth", block: "start" });

  // Update stats
  statsAnalyzed++;
  if (overall >= 40) statsFlagged++;
  document.getElementById("stat-analyzed").textContent = statsAnalyzed;
  document.getElementById("stat-flagged").textContent = statsFlagged;

  currentAttemptId = data.attempt_id;
  currentCandidate = presetKey;
}

// ===== EVIDENCE BUNDLE BUILDER =====
function buildEvidenceBundle(data, overall) {
  const items = [];
  const v = data.velocity_analysis;
  const s = data.style_analysis;
  const i = data.interview_analysis;

  if (v.pasted_blocks > 0) {
    items.push({ icon: "📋", text: `<strong>Paste burst detected:</strong> ${esc(v.pasted_chars)} characters pasted in ${esc(v.pasted_blocks)} block(s) — unnatural insertion pattern.` });
  }
  if (v.tab_switches > 2) {
    items.push({ icon: "🔀", text: `<strong>Tab switching:</strong> ${esc(v.tab_switches)} context switches during assessment — possible AI tool consultation.` });
  }
  if (data.similarity_score > 70) {
    items.push({ icon: "🔎", text: `<strong>AST plagiarism:</strong> ${data.similarity_score}% structural match against reference solution — code topology nearly identical.` });
  }
  if (s.found_artifacts && s.found_artifacts.length > 0) {
    items.push({ icon: "🤖", text: `<strong>AI prompt artifacts:</strong> Phrases detected — "${s.found_artifacts.join('", "')}" — ChatGPT/Claude response markers.` });
  }
  if (s.reasons && s.reasons.length > 0) {
    s.reasons.forEach(r => items.push({ icon: "📊", text: `<strong>Stylometrics:</strong> ${r}` }));
  }
  if (i.consistency_score < 60) {
    items.push({ icon: "🗣️", text: `<strong>Explanation divergence:</strong> ${i.verdict} — candidate cannot articulate their own code.` });
  }
  if (v.corrections === 0 && v.pasted_chars === 0) {
    items.push({ icon: "✨", text: `<strong>Unnatural perfection:</strong> Zero corrections on a complex solution — humans make mistakes.` });
  }
  if (items.length === 0) {
    items.push({ icon: "✅", text: `<strong>No significant flags found.</strong> Candidate demonstrates consistent, incremental coding behavior with coherent explanations.` });
  }
  return items;
}

// ===== PRESET RUNNER =====
async function runPreset(key) {
  const preset = PRESETS[key];
  if (!preset) return;
  showLoader(`Auditing ${preset.name}...`);
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(preset.payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || "API error");
    }
    const data = await res.json();
    renderResults(data, key);
    showToast(`Audit complete for ${preset.name}`, "ok");
  } catch (e) {
    showToast(`Error: ${e.message}`, "err");
  } finally {
    hideLoader();
  }
}

// ===== CUSTOM AUDIT =====
async function runCustomAudit() {
  const id = document.getElementById("custom-id").value.trim().replace(/[^a-zA-Z0-9_-]/g, "_") || "custom_candidate";
  const code = document.getElementById("custom-code").value.trim();
  const ref = document.getElementById("custom-ref").value.trim() || "def solution():\n    pass";
  const explanation = document.getElementById("custom-explanation").value.trim() || "No explanation provided.";
  const pasted = document.getElementById("custom-pasted").value === "yes";
  const tabs = parseInt(document.getElementById("custom-tabs").value) || 0;

  if (!code) { showToast("Please enter candidate code.", "err"); return; }

  const telemetry = [];
  if (pasted) {
    telemetry.push({ type: "paste", timestamp: 1000, length: code.length, content: code });
  } else {
    Array.from(code.slice(0, 30)).forEach((ch, i) => {
      telemetry.push({ type: "type", timestamp: 100 * i, length: 1, char: ch });
    });
  }
  for (let i = 0; i < tabs; i++) {
    telemetry.push({ type: "tab", timestamp: 2000 + i * 500, length: 0 });
  }

  const payload = {
    candidate_id: id,
    code,
    history_codes: ["def helper():\n    return 42"],
    telemetry,
    qa_responses: [{ q: "Explain your approach in 3-4 sentences.", a: explanation }],
    reference_code: ref
  };

  showLoader("Running custom integrity audit...");
  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || "API error");
    }
    const data = await res.json();
    const customKey = "__custom__";
    PRESETS[customKey] = {
      name: id.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase()),
      role: "Custom Audit",
      skills: { Algorithms:70, "Data Structures":70, Debugging:70, "System Design":70, "SQL Optimization":70, "Code Quality":70, "Test Writing":70 }
    };
    renderResults(data, customKey);
    document.getElementById("custom-results").classList.remove("hidden");
    document.getElementById("results-panel").scrollIntoView({ behavior: "smooth" });
    showToast("Custom audit complete!", "ok");
  } catch (e) {
    showToast(`Error: ${e.message}`, "err");
  } finally {
    hideLoader();
  }
}

// ===== APPEAL FLOW =====
async function submitAppeal() {
  if (!currentAttemptId || currentAttemptId < 0) { showToast("No attempt to appeal.", "err"); return; }
  const reason = document.getElementById("appeal-reason").value.trim();
  if (reason.length < 5) { showToast("Please enter a reason (min 5 characters).", "err"); return; }

  showLoader("Submitting appeal...");
  try {
    const res = await fetch(`/api/attempts/${currentAttemptId}/appeal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ reason })
    });
    if (!res.ok) throw new Error("Appeal submission failed.");
    document.getElementById("appeal-status").textContent = "✅ Appeal submitted. Awaiting recruiter review.";
    document.getElementById("appeal-status").className = "appeal-status ok";
    document.getElementById("resolve-btn").style.display = "inline-flex";
    document.getElementById("reject-btn").style.display = "inline-flex";
    showToast("Appeal submitted successfully.", "ok");
  } catch (e) {
    showToast(e.message, "err");
  } finally {
    hideLoader();
  }
}

async function resolveAppeal() {
  if (!currentAttemptId || currentAttemptId < 0) return;
  showLoader("Resolving appeal...");
  try {
    const res = await fetch(`/api/attempts/${currentAttemptId}/resolve-appeal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "resolved", reviewer_note: "Appeal approved by recruiter after manual review." })
    });
    if (!res.ok) throw new Error("Resolution failed.");
    document.getElementById("appeal-status").textContent = "✅ Appeal APPROVED — flags cleared. Risk reset to safe.";
    document.getElementById("appeal-status").className = "appeal-status ok";
    document.getElementById("res-badge").textContent = "✅ SAFE (Appeal Approved)";
    document.getElementById("res-badge").className = "verdict-badge safe";
    showToast("Appeal approved. Candidate cleared.", "ok");
  } catch (e) {
    showToast(e.message, "err");
  } finally {
    hideLoader();
  }
}

async function rejectAppeal() {
  if (!currentAttemptId || currentAttemptId < 0) return;
  showLoader("Rejecting appeal...");
  try {
    const res = await fetch(`/api/attempts/${currentAttemptId}/resolve-appeal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status: "rejected", reviewer_note: "Appeal rejected after recruiter review. Flags upheld." })
    });
    if (!res.ok) throw new Error("Rejection failed.");
    document.getElementById("appeal-status").textContent = "❌ Appeal REJECTED — original flags upheld.";
    document.getElementById("appeal-status").className = "appeal-status err";
    showToast("Appeal rejected. Flags maintained.", "err");
  } catch (e) {
    showToast(e.message, "err");
  } finally {
    hideLoader();
  }
}

// ===== VOICE ENGINE =====
async function runTTS() {
  const text = document.getElementById("tts-text").value.trim();
  if (!text) { showToast("Enter text to synthesize.", "err"); return; }
  showLoader("Synthesizing speech...");
  try {
    const res = await fetch("/api/voice/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });
    if (!res.ok) throw new Error("Synthesis failed.");
    const data = await res.json();
    const audioSrc = `data:audio/mp3;base64,${data.audio_base64}`;
    document.getElementById("tts-result").innerHTML = `
      <p style="color:var(--safe);font-size:.85rem;margin-bottom:8px">✅ Synthesized via ${data.engine}</p>
      <audio controls src="${audioSrc}"></audio>
    `;
    showToast("Speech synthesized!", "ok");
  } catch (e) {
    showToast(e.message, "err");
  } finally {
    hideLoader();
  }
}

async function runSTT() {
  const mockAudio = "SUQzBAAAAAAAI1RTU0UAAAAPAAADTGFtZTMuOTguNFVVVVVVVVVV";
  showLoader("Transcribing audio...");
  try {
    const res = await fetch("/api/voice/transcribe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ audio_base64: mockAudio })
    });
    if (!res.ok) throw new Error("Transcription failed.");
    const data = await res.json();
    document.getElementById("stt-result").innerHTML = `
      <p style="color:var(--safe);font-size:.85rem;margin-bottom:8px">✅ Transcribed (Confidence: ${Math.round(data.confidence * 100)}%)</p>
      <div class="transcription-box">"${data.transcription}"</div>
    `;
    showToast("Transcription complete!", "ok");
  } catch (e) {
    showToast(e.message, "err");
  } finally {
    hideLoader();
  }
}

// ===== INIT =====
document.addEventListener("DOMContentLoaded", () => {
  // Animate stat counters on load
  const targets = [0, 0, 4];
  const els = ["stat-analyzed", "stat-flagged"];
  els.forEach(id => { document.getElementById(id).textContent = "0"; });
});

// ===== SETTINGS / BYOK =====
function onProviderChange() {
  const provider = document.getElementById("cfg-provider").value;
  const modelSel = document.getElementById("cfg-model");
  if (provider === "openai") {
    modelSel.innerHTML = `
      <option value="gpt-4o">gpt-4o</option>
      <option value="gpt-4o-mini">gpt-4o-mini</option>
      <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>`;
    document.getElementById("cfg-apikey").placeholder = "sk-...";
  } else {
    modelSel.innerHTML = `
      <option value="llama-3.3-70b-versatile">llama-3.3-70b-versatile</option>
      <option value="llama3-8b-8192">llama3-8b-8192 (faster)</option>
      <option value="mixtral-8x7b-32768">mixtral-8x7b-32768</option>`;
    document.getElementById("cfg-apikey").placeholder = "gsk_...";
  }
}

function toggleKeyVisibility() {
  const inp = document.getElementById("cfg-apikey");
  inp.type = inp.type === "password" ? "text" : "password";
}

async function saveConfig() {
  const key = document.getElementById("cfg-apikey").value.trim();
  const model = document.getElementById("cfg-model").value;
  const provider = document.getElementById("cfg-provider").value;
  const resultEl = document.getElementById("cfg-result");

  if (!key) { resultEl.textContent = "⚠ Please enter an API key."; resultEl.className = "cfg-result err"; return; }

  showLoader("Activating LLM configuration...");
  try {
    const res = await fetch("/api/config/llm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ api_key: key, model, provider })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Config failed");

    resultEl.textContent = `✅ ${data.message}`;
    resultEl.className = "cfg-result ok";
    document.getElementById("llm-status-dot").className = "status-dot configured";
    document.getElementById("llm-status-text").textContent =
      `LLM active — ${provider} / ${model}`;
    document.getElementById("cfg-apikey").value = "";
    showToast("LLM configured! Interview scoring now powered by AI.", "ok");
  } catch (e) {
    resultEl.textContent = `❌ ${e.message}`;
    resultEl.className = "cfg-result err";
    document.getElementById("llm-status-dot").className = "status-dot error";
    showToast("Config failed: " + e.message, "err");
  } finally {
    hideLoader();
  }
}

// Check LLM status on page load
async function checkLLMStatus() {
  try {
    const res = await fetch("/api/config/llm");
    if (!res.ok) return;
    const data = await res.json();
    if (data.key_configured) {
      document.getElementById("llm-status-dot").className = "status-dot configured";
      document.getElementById("llm-status-text").textContent =
        `LLM active — ${data.provider} / ${data.model}`;
    }
  } catch (_) {}
}

// Show LLM attribution badge in results if present
function getLLMBadge(poweredBy) {
  if (!poweredBy || poweredBy.includes("Rule-based")) return "";
  return `<span class="llm-badge">🤖 ${poweredBy}</span>`;
}

// Override DOMContentLoaded to also check LLM status
document.addEventListener("DOMContentLoaded", () => {
  checkLLMStatus();
});
