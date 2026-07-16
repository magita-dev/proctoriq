// ============================================================
// System Siege — Live Coding IDE
// Monaco Editor + Telemetry capture + Chatbot + Submission
// ============================================================

let monacoEditor = null;
let currentProblem = null;
let currentMode = "hint";
let sessionStart = Date.now();

// Telemetry log — captured automatically
let telemetry = [];
let lastContent = "";

// ── Toast ──────────────────────────────────────────────────
function showToast(msg, type = "ok") {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.className = `toast ${type}`;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 3500);
}

// ── Monaco Init ────────────────────────────────────────────
require.config({ paths: { vs: "https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.44.0/min/vs" } });

require(["vs/editor/editor.main"], function () {
  monacoEditor = monaco.editor.create(document.getElementById("monaco-editor"), {
    value: "# Select a problem to begin\n",
    language: "python",
    theme: "vs-dark",
    fontSize: 14,
    fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', monospace",
    fontLigatures: true,
    minimap: { enabled: false },
    scrollBeyondLastLine: false,
    lineNumbers: "on",
    roundedSelection: true,
    automaticLayout: true,
    padding: { top: 12 },
    suggestOnTriggerCharacters: true,
    quickSuggestions: true,
    tabSize: 4,
    insertSpaces: true,
    wordWrap: "on",
  });

  // Telemetry: track content changes
  monacoEditor.onDidChangeModelContent((e) => {
    const now = Date.now() - sessionStart;
    const newContent = monacoEditor.getValue();
    document.getElementById("char-count").textContent = newContent.length + " chars";

    for (const change of e.changes) {
      const insertedLen = change.text.length;
      const deletedLen = change.rangeLength;

      if (insertedLen > 60 && !change.text.includes("\n\n")) {
        // Large single insert = paste
        telemetry.push({
          type: "paste",
          timestamp: now,
          length: insertedLen,
          content: change.text.slice(0, 5000),
          char: null,
        });
      } else if (deletedLen > 0 && insertedLen === 0) {
        telemetry.push({ type: "delete", timestamp: now, length: deletedLen, char: "Delete" });
      } else if (insertedLen === 1) {
        telemetry.push({ type: "type", timestamp: now, length: 1, char: change.text });
      } else if (insertedLen > 1) {
        // Multi-char non-paste (autocomplete, snippet)
        telemetry.push({ type: "type", timestamp: now, length: insertedLen, char: null });
      }
    }
    lastContent = newContent;
  });

  // Telemetry: tab visibility (tab switching)
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) {
      telemetry.push({ type: "tab", timestamp: Date.now() - sessionStart, length: 0, char: null });
    }
  });

  // Load problems list on start
  loadProblemsList();
});

// ── Problem Loading ────────────────────────────────────────
async function loadProblemsList() {
  try {
    const res = await fetch("/api/ide/problems");
    const problems = await res.json();
    const sel = document.getElementById("problem-select");
    problems.forEach(p => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = `${p.title} (${p.difficulty})`;
      sel.appendChild(opt);
    });
  } catch (e) {
    showToast("Could not load problems list.", "err");
  }
}

async function loadProblem(id) {
  if (!id) return;
  try {
    const res = await fetch(`/api/ide/problems/${id}`);
    if (!res.ok) throw new Error("Problem not found");
    currentProblem = await res.json();

    // Update UI
    document.getElementById("problem-title-display").textContent = currentProblem.title;
    document.getElementById("problem-tags").innerHTML =
      (currentProblem.tags || []).map(t => `<span class="prob-tag">${t}</span>`).join("");

    // Render description with basic markdown-ish formatting
    document.getElementById("problem-description-display").innerHTML =
      renderDesc(currentProblem.description);

    const diff = currentProblem.difficulty || "";
    const badge = document.getElementById("problem-difficulty");
    badge.textContent = diff;
    badge.className = `diff-badge ${diff}`;

    // Set starter code in editor
    if (monacoEditor) {
      monacoEditor.setValue(currentProblem.starter_code || "# Write your solution here\n");
      monacoEditor.setPosition({ lineNumber: 3, column: 1 });
      monacoEditor.focus();
    }

    // Reset telemetry for new problem
    telemetry = [];
    sessionStart = Date.now();
    lastContent = currentProblem.starter_code || "";

    // Clear results
    document.getElementById("test-summary").innerHTML = "";
    document.getElementById("test-cases-display").innerHTML = "";
    document.getElementById("integrity-panel").innerHTML =
      '<p class="integrity-placeholder">Submit your solution to see the integrity report.</p>';

    // Send context to chat
    appendBotMsg(`Loaded: <strong>${currentProblem.title}</strong> (${diff})<br>Ask me for a 💡 Hint whenever you're stuck!`);
    showToast(`Problem loaded: ${currentProblem.title}`, "ok");
  } catch (e) {
    showToast("Failed to load problem: " + e.message, "err");
  }
}

function renderDesc(text) {
  if (!text) return "";
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\n/g, "<br>");
}

function resetCode() {
  if (!currentProblem || !monacoEditor) return;
  if (confirm("Reset code to starter template?")) {
    monacoEditor.setValue(currentProblem.starter_code || "# Write your solution here\n");
    telemetry = [];
    sessionStart = Date.now();
    showToast("Code reset.", "ok");
  }
}

// --- Render Results ---
function renderSubmissionResults(data) {
  // Test results tab
  const passed = data.passed, total = data.total;
  const summaryEl = document.getElementById('test-summary');
  const cls = passed === total ? 'all-pass' : passed === 0 ? 'all-fail' : 'some-fail';
  const emoji = passed === total ? '✅' : passed === 0 ? '❌' : '⚠️';
  summaryEl.className = 'test-summary ' + cls;
  summaryEl.textContent = `${emoji}  ${passed} / ${total} Test Cases Passed  —  Correctness: ${data.correctness_score}%`;

  const listEl = document.getElementById('test-cases-display');
  listEl.innerHTML = data.test_results.map(tc => `
    <div class="test-case ${tc.passed ? 'pass' : 'fail'}">
      <div class="test-case-header">
        <span>Case ${tc.case}</span>
        <span class="${tc.passed ? 'test-pass-label' : 'test-fail-label'}">${tc.passed ? '✓ PASS' : '✗ FAIL'}</span>
      </div>
      <div class="test-io">Input: <span>${escHtml(tc.input)}</span></div>
      <div class="test-io">Expected: <span>${escHtml(tc.expected)}</span></div>
      <div class="test-io">Got: <span style="color:${tc.passed ? '#22c55e' : '#ef4444'}">${escHtml(tc.got || tc.error || '—')}</span></div>
    </div>
  `).join('');

  // Integrity tab
  renderIntegrityPanel(data);

  // Chat auto-message
  const riskCls = data.trust_graph.overall_risk >= 70 ? '🚨 High' :
                  data.trust_graph.overall_risk >= 30 ? '⚡ Medium' : '✅ Low';
  appendChatMsg('bot',
    `Submission received! <strong>${passed}/${total}</strong> tests passed (${data.correctness_score}% correctness).<br>
    Integrity risk: <strong>${riskCls} Risk (${data.trust_graph.overall_risk}%)</strong><br>
    Check the <strong>🔍 Integrity</strong> tab for the full report.`);
}

function renderIntegrityPanel(data) {
  const v = data.velocity_analysis;
  const s = data.style_analysis;
  const i = data.interview_analysis;
  const h = data.humane_evaluation;
  const g = data.trust_graph;

  const riskColor = g.overall_risk >= 70 ? '#ef4444' : g.overall_risk >= 30 ? '#f59e0b' : '#22c55e';

  // Build flags list
  const flags = [];
  if (v.pasted_blocks > 0) flags.push({ cls: 'danger', text: `📋 Paste burst: ${v.pasted_chars} chars in ${v.pasted_blocks} block(s)` });
  if (v.tab_switches > 2) flags.push({ cls: 'warning', text: `🔀 ${v.tab_switches} tab switches during session` });
  if (data.similarity_score > 70) flags.push({ cls: 'danger', text: `🔎 AST similarity: ${data.similarity_score}% match to reference` });
  if (s.found_artifacts && s.found_artifacts.length > 0) flags.push({ cls: 'danger', text: `🤖 AI artifacts: "${s.found_artifacts.join('", "')}"` });
  if (i.consistency_score < 60) flags.push({ cls: 'warning', text: `🗣️ Explanation mismatch: ${i.verdict}` });
  if (v.unnatural_perfection) flags.push({ cls: 'warning', text: `✨ Unnatural perfection: no corrections on complex code` });
  if (s.llm_style_verdict) flags.push({ cls: s.risk_score >= 50 ? 'warning' : 'safe', text: `🧠 Style AI: ${s.llm_style_verdict}` });
  if (i.red_flags && i.red_flags.length > 0) {
    i.red_flags.forEach(f => flags.push({ cls: 'warning', text: `⚑ ${f}` }));
  }
  if (flags.length === 0) flags.push({ cls: 'safe', text: '✅ No significant integrity flags detected.' });

  document.getElementById('integrity-panel').innerHTML = `
    <div class="correctness-big">
      <div class="score-num" style="color:${data.correctness_score >= 80 ? '#22c55e' : data.correctness_score >= 40 ? '#f59e0b' : '#ef4444'}">
        ${data.correctness_score}%
      </div>
      <div class="score-sub">Correctness Score — ${data.passed}/${data.total} tests</div>
    </div>

    <div>
      <div class="int-section-title">Integrity Risk</div>
      ${renderIntBar('Overall Risk', g.overall_risk, riskColor)}
      ${renderIntBar('AST Similarity', data.similarity_score, data.similarity_score > 70 ? '#ef4444' : '#f59e0b')}
      ${renderIntBar('Velocity Risk', v.risk_score, v.risk_score > 50 ? '#ef4444' : '#f59e0b')}
      ${renderIntBar('Style Risk', s.risk_score, s.risk_score > 50 ? '#ef4444' : '#f59e0b')}
    </div>

    <div>
      <div class="int-section-title">Evidence Flags</div>
      <div class="int-flags">
        ${flags.map(f => `<div class="int-flag ${f.cls}">${f.text}</div>`).join('')}
      </div>
    </div>

    <div>
      <div class="int-section-title">Interview Consistency ${i.powered_by ? `<span style="font-size:.68rem;color:#6c63ff">[${i.powered_by}]</span>` : ''}</div>
      <div class="int-verdict">${i.verdict}${i.reasoning ? '<br><em>' + i.reasoning + '</em>' : ''}</div>
    </div>

    <div>
      <div class="int-section-title">Humane Evaluation</div>
      <div class="int-verdict">Syntax: ${h.syntax_score}% &nbsp;|&nbsp; Logic: ${h.logic_score}%<br>${h.verdict}</div>
    </div>
  `;
}

function renderIntBar(label, pct, color) {
  return `
    <div class="int-score-row">
      <span class="int-score-label">${label}</span>
      <span class="int-score-val" style="color:${color}">${Math.round(pct)}%</span>
    </div>
    <div class="int-bar-track">
      <div class="int-bar-fill" style="width:${Math.round(pct)}%;background:${color}"></div>
    </div>`;
}

// ── Tab switching in problem panel ─────────────────────────
function switchPTab(name, btn) {
  document.querySelectorAll(".ptab").forEach(b => b.classList.remove("active"));
  document.querySelectorAll(".ptab-content").forEach(p => {
    p.classList.remove("active");
    p.style.display = "none";
  });
  btn.classList.add("active");
  const el = document.getElementById(`ptab-${name}`);
  el.classList.add("active");
  el.style.display = "block";
}

// ── Submit ─────────────────────────────────────────────────
async function submitSolution() {
  if (!currentProblem) { showToast("Select a problem first.", "err"); return; }
  if (!monacoEditor) return;

  const code = monacoEditor.getValue().trim();
  if (!code || code === currentProblem.starter_code.trim()) {
    showToast("Write some code before submitting.", "err"); return;
  }

  let candidateId = document.getElementById("candidate-id").value.trim()
    .replace(/[^a-zA-Z0-9_-]/g, "_") || "candidate";
  const explanation = document.getElementById("explanation-input").value.trim();

  // Show overlay
  const overlay = document.getElementById("submit-overlay");
  overlay.classList.remove("hidden");
  document.getElementById("submit-msg").textContent = "Running test cases...";

  // Clamp telemetry to valid schema (timestamp must be int ≥ 0, length ≥ 0)
  const cleanTelemetry = telemetry
    .filter(e => ["type","paste","tab","delete"].includes(e.type))
    .map(e => ({
      type: e.type,
      timestamp: Math.max(0, Math.round(e.timestamp || 0)),
      length: Math.max(0, Math.min(50000, e.length || 0)),
      char: e.char ? String(e.char).slice(0, 50) : null,
      content: e.content ? String(e.content).slice(0, 50000) : null,
    }));

  const payload = {
    candidate_id: candidateId,
    problem_id: currentProblem.id,
    code,
    telemetry: cleanTelemetry,
    explanation: explanation || "No explanation provided.",
  };

  try {
    document.getElementById("submit-msg").textContent = "Running integrity analysis...";
    const res = await fetch("/api/ide/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || "Submission failed");
    }
    const data = await res.json();
    overlay.classList.add("hidden");

    renderTestResults(data);
    renderIntegrityPanel(data);

    // Switch to results tab
    switchPTab("results", document.querySelectorAll(".ptab")[1]);

    const passed = data.passed;
    const total = data.total;
    const risk = data.trust_graph?.overall_risk ?? 0;
    showToast(`${passed}/${total} tests passed · Risk: ${risk}%`, passed === total ? "ok" : "err");

    // Auto bot comment
    const botMsg = passed === total
      ? `✅ All ${total} tests passed! Overall risk: <strong>${risk}%</strong>. Check the 🔍 Integrity tab for details.`
      : `⚠️ ${passed}/${total} tests passed. Overall risk: <strong>${risk}%</strong>. Ask me to <em>Assess</em> your code!`;
    appendBotMsg(botMsg);

    // Reset telemetry for next attempt
    telemetry = [];
    sessionStart = Date.now();

  } catch (e) {
    overlay.classList.add("hidden");
    showToast("Submission error: " + e.message, "err");
    appendBotMsg(`❌ Submission error: ${e.message}`);
  }
}

// ── Render test results ────────────────────────────────────
function renderTestResults(data) {
  const passed = data.passed;
  const total = data.total;
  const pct = Math.round((passed / total) * 100);
  const color = passed === total ? "var(--safe)" : passed > 0 ? "var(--warning)" : "var(--danger)";

  document.getElementById("test-summary").innerHTML = `
    <span style="font-size:1.3rem;font-weight:800;color:${color}">${passed}/${total}</span>
    <span style="color:var(--muted)">test cases passed</span>
    <span style="margin-left:auto;font-size:0.82rem;color:var(--muted)">
      Correctness: <strong style="color:${color}">${pct}%</strong>
    </span>
  `;

  // Logic score rubric
  const ls = data.logic_score;
  if (ls) {
    const gradeColor = ls.grade === "A" ? "var(--safe)" :
                       ls.grade === "B" ? "var(--safe)" :
                       ls.grade === "C" ? "var(--warning)" :
                       ls.grade === "D" ? "var(--warning)" : "var(--danger)";

    const rubricHtml = `
      <div class="rubric-box">
        <div class="rubric-header">
          <div>
            <div class="rubric-title">📊 Logic-Based Score</div>
            <div class="rubric-sub">${ls.grade_label}</div>
          </div>
          <div class="rubric-total" style="color:${gradeColor}">
            <span class="rubric-grade">${ls.grade}</span>
            <span class="rubric-marks">${ls.total}/${ls.max_marks}</span>
          </div>
        </div>
        <div class="rubric-bar-track">
          <div class="rubric-bar-fill" style="width:${ls.total}%;background:${gradeColor}"></div>
        </div>
        <div class="rubric-categories">
          ${ls.breakdown.map(cat => `
            <div class="rubric-cat">
              <div class="rubric-cat-header">
                <span class="rubric-cat-icon">${cat.icon}</span>
                <span class="rubric-cat-name">${cat.category}</span>
                <span class="rubric-cat-score" style="color:${cat.pct>=80?'var(--safe)':cat.pct>=50?'var(--warning)':'var(--danger)'}">
                  ${cat.scored}/${cat.max}
                </span>
              </div>
              <div class="rubric-cat-bar">
                <div style="width:${cat.pct}%;height:4px;border-radius:2px;background:${cat.pct>=80?'var(--safe)':cat.pct>=50?'var(--warning)':'var(--danger)'}"></div>
              </div>
              <ul class="rubric-reasons">
                ${cat.reasons.map(r => `<li class="${r.startsWith('+') ? 'reason-pass' : 'reason-fail'}">${r}</li>`).join("")}
              </ul>
            </div>
          `).join("")}
        </div>
      </div>
    `;
    document.getElementById("test-cases-display").insertAdjacentHTML("beforebegin", rubricHtml);
  }

  document.getElementById("test-cases-display").innerHTML = data.test_results.map(tc => `
    <div class="tc-row ${tc.passed ? "pass" : "fail"}">
      <div class="tc-header">
        <span class="tc-label">Case ${tc.case}</span>
        <span class="${tc.passed ? "tc-status-pass" : "tc-status-fail"}">
          ${tc.passed ? "✓ PASS" : "✗ FAIL"}
        </span>
      </div>
      <div class="tc-detail">
        Input: <span>${escHtml(tc.input)}</span><br>
        Expected: <span>${escHtml(String(tc.expected))}</span><br>
        Got: <span style="color:${tc.passed ? "var(--safe)" : "var(--danger)"}">${escHtml(String(tc.got || "—"))}</span>
        ${tc.error ? `<br><span style="color:var(--danger)">Error: ${escHtml(tc.error)}</span>` : ""}
      </div>
    </div>
  `).join("");
}

function escHtml(s) {
  return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");
}

// ── Render integrity panel ─────────────────────────────────
function renderIntegrityPanel(data) {
  const graph = data.trust_graph;
  const v = data.velocity_analysis;
  const s = data.style_analysis;
  const i = data.interview_analysis;
  const risk = graph.overall_risk;

  const riskColor = risk >= 70 ? "var(--danger)" : risk >= 30 ? "var(--warning)" : "var(--safe)";
  const statusLabel = risk >= 70 ? "🚨 HIGH RISK" : risk >= 30 ? "⚡ MEDIUM RISK" : "✅ LOW RISK";

  // Build flags list
  const flags = [];
  if (v.pasted_blocks > 0) flags.push({cls:"danger", icon:"📋", text:`Paste burst: ${v.pasted_chars} chars in ${v.pasted_blocks} block(s)`});
  if (v.tab_switches > 2)  flags.push({cls:"danger", icon:"🔀", text:`${v.tab_switches} tab switches detected`});
  if (v.unnatural_perfection) flags.push({cls:"danger", icon:"✨", text:"Unnatural perfection: fast + zero corrections"});
  if (data.similarity_score > 70) flags.push({cls:"danger", icon:"🔎", text:`AST match: ${data.similarity_score}% similarity to reference`});
  if (s.found_artifacts?.length) flags.push({cls:"danger", icon:"🤖", text:`AI artifacts: "${s.found_artifacts.join('", "')}"`});
  if (s.llm_indicators?.length)  flags.push({cls:"danger", icon:"🧠", text:`LLM: ${s.llm_indicators[0]}`});
  if (i.red_flags?.length)        flags.push({cls:"danger", icon:"🗣️", text:`Interview: ${i.red_flags[0]}`});
  if (flags.length === 0) flags.push({cls:"safe", icon:"✅", text:"No significant integrity flags detected."});

  document.getElementById("integrity-panel").innerHTML = `
    <div style="margin-bottom:14px;padding:10px 14px;background:var(--bg3);border-radius:8px;border-left:4px solid ${riskColor}">
      <div style="font-size:0.75rem;color:var(--muted);margin-bottom:4px">INTEGRITY VERDICT</div>
      <div style="font-size:1.1rem;font-weight:800;color:${riskColor}">${statusLabel}</div>
      <div style="font-size:0.82rem;color:var(--muted);margin-top:2px">Overall risk score: ${risk}%</div>
    </div>
    <div class="integrity-score-row">
      <div class="int-chip">
        <div class="int-label">AST Similarity</div>
        <div class="int-val" style="color:${data.similarity_score>70?"var(--danger)":data.similarity_score>30?"var(--warning)":"var(--safe)"}">${data.similarity_score}%</div>
      </div>
      <div class="int-chip">
        <div class="int-label">Velocity Risk</div>
        <div class="int-val" style="color:${v.risk_score>70?"var(--danger)":v.risk_score>30?"var(--warning)":"var(--safe)"}">${v.risk_score}%</div>
      </div>
      <div class="int-chip">
        <div class="int-label">Style Risk</div>
        <div class="int-val" style="color:${s.risk_score>70?"var(--danger)":s.risk_score>30?"var(--warning)":"var(--safe)"}">${s.risk_score}%</div>
      </div>
      <div class="int-chip">
        <div class="int-label">Interview Match</div>
        <div class="int-val" style="color:${i.consistency_score<60?"var(--danger)":i.consistency_score<80?"var(--warning)":"var(--safe)"}">${i.consistency_score}%</div>
      </div>
    </div>
    <div class="int-verdict">
      <div class="int-verdict-label">AI Interview Analysis ${i.powered_by ? `<span style="font-size:.7rem;color:var(--accent2)">(${i.powered_by})</span>` : ""}</div>
      <div class="int-verdict-text">${i.verdict}</div>
      ${i.reasoning ? `<div style="color:var(--muted);font-size:.8rem;margin-top:6px">${i.reasoning}</div>` : ""}
    </div>
    <div class="int-flags">
      ${flags.map(f => `<div class="int-flag ${f.cls}"><span>${f.icon}</span><span>${f.text}</span></div>`).join("")}
    </div>
    <div style="margin-top:12px;padding:10px;background:var(--bg3);border-radius:8px;font-size:.8rem;color:var(--muted)">
      Humane evaluation: ${data.humane_evaluation?.verdict || "—"}
    </div>
  `;
}

// --- Chat ---
function setMode(mode, btn) {
  chatMode = mode;
  document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
  btn.classList.add('active');
  const hints = {
    hint: 'Ask me for a nudge — I won\'t give you the answer.',
    explain: 'Ask me to explain any concept.',
    assess: 'I\'ll review your current code and give feedback.',
    chat: 'Ask me anything about coding.',
  };
  showToast(hints[mode] || '', 'ok');
}

function chatKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
}

async function sendChat() {
  const inp = document.getElementById('chat-input');
  const msg = inp.value.trim();
  if (!msg) return;
  inp.value = '';

  appendChatMsg('user', escHtml(msg));
  const typingEl = appendChatMsg('bot', '...', true);

  try {
    const res = await fetch('/api/ide/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: msg,
        problem_title: currentProblem?.title || '',
        problem_description: currentProblem?.description || '',
        current_code: chatMode === 'hint' || chatMode === 'assess' ? monacoEditor.getValue() : '',
        mode: chatMode,
      })
    });
    const data = await res.json();
    typingEl.remove();
    appendChatMsg('bot', renderMarkdown(data.reply) +
      (data.powered_by && data.powered_by !== 'none'
        ? `<br><span style="font-size:.7rem;color:#6c63ff;margin-top:4px;display:inline-block">🤖 ${data.powered_by}</span>`
        : ''));
  } catch (e) {
    typingEl.remove();
    appendChatMsg('bot', '❌ Could not reach the AI assistant. Check your API key in Settings.');
  }
}

function appendChatMsg(role, html, typing = false) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-msg ${role}${typing ? ' msg-typing' : ''}`;
  const bubble = document.createElement('div');
  bubble.className = 'msg-bubble';
  bubble.innerHTML = html;
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

// --- Tab switching ---
function switchPTab(name, btn) {
  document.querySelectorAll('.ptab-content').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.ptab').forEach(el => el.classList.remove('active'));
  const tab = document.getElementById('ptab-' + name);
  if (tab) tab.classList.add('active');
  if (btn) btn.classList.add('active');
}

// --- Submit overlay ---
function showSubmitOverlay(msg) {
  document.getElementById('submit-msg').textContent = msg;
  document.getElementById('submit-overlay').classList.remove('hidden');
}
function hideSubmitOverlay() {
  document.getElementById('submit-overlay').classList.add('hidden');
}

// --- Toast ---
function showToast(msg, type = 'ok') {
  const t = document.getElementById('toast');
  t.textContent = msg;
  t.className = `toast ${type}`;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 3000);
}

// --- Helpers ---
function escHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function renderMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/```[\w]*\n?([\s\S]*?)```/g, '<pre>$1</pre>')
    .replace(/\n/g, '<br>');
}

// ── Chatbot ────────────────────────────────────────────────
function setMode(mode, btn) {
  currentMode = mode;
  document.querySelectorAll(".mode-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  const hints = {
    hint:    "💡 Hint mode: I'll nudge you in the right direction without giving away the answer.",
    explain: "📖 Explain mode: Ask me about any concept, algorithm, or data structure.",
    assess:  "🔎 Assess mode: I'll review your current code and give specific feedback.",
    chat:    "💬 Chat mode: Ask me anything coding-related.",
  };
  appendBotMsg(hints[mode] || "");
}

function chatKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
}

async function sendChat() {
  const input = document.getElementById("chat-input");
  const msg = input.value.trim();
  if (!msg) return;
  input.value = "";

  appendUserMsg(msg);
  const thinkingEl = appendBotMsg("...", true);

  const payload = {
    message: msg,
    mode: currentMode,
    problem_title: currentProblem?.title || "",
    problem_description: currentProblem?.description || "",
    current_code: monacoEditor?.getValue() || "",
  };

  try {
    const res = await fetch("/api/ide/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.message || "Chat error");

    // Replace thinking bubble
    thinkingEl.querySelector(".msg-bubble").innerHTML = formatBotReply(data.reply);
    thinkingEl.querySelector(".msg-bubble").classList.remove("msg-thinking");
    if (data.powered_by && data.powered_by !== "none") {
      const attr = document.createElement("div");
      attr.style.cssText = "font-size:.7rem;color:var(--muted);margin-top:6px;text-align:right";
      attr.textContent = `🤖 ${data.powered_by}`;
      thinkingEl.querySelector(".msg-bubble").appendChild(attr);
    }
  } catch (e) {
    thinkingEl.querySelector(".msg-bubble").innerHTML = `❌ ${e.message}`;
    thinkingEl.querySelector(".msg-bubble").classList.remove("msg-thinking");
  }

  scrollChat();
}

function formatBotReply(text) {
  // Safely escape the raw text first, then apply formatting
  // This prevents XSS from LLM-generated content
  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
  // Process code blocks before escaping inline content
  const parts = text.split(/(```[\s\S]*?```)/g);
  return parts.map((part, idx) => {
    if (part.startsWith("```")) {
      const inner = part.replace(/^```\w*\n?/, "").replace(/```$/, "");
      return `<pre><code>${escapeHtml(inner)}</code></pre>`;
    }
    // Escape then apply safe inline formatting
    let safe = escapeHtml(part);
    safe = safe.replace(/`([^`]+)`/g, "<code>$1</code>");
    safe = safe.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    safe = safe.replace(/\*(.*?)\*/g, "<em>$1</em>");
    safe = safe.replace(/\n/g, "<br>");
    return safe;
  }).join("");
}

function appendUserMsg(text) {
  const el = document.createElement("div");
  el.className = "chat-msg user";
  el.innerHTML = `<div class="msg-bubble">${escHtml(text)}</div>`;
  document.getElementById("chat-messages").appendChild(el);
  scrollChat();
  return el;
}

function appendBotMsg(html, thinking = false) {
  const el = document.createElement("div");
  el.className = "chat-msg bot";
  el.innerHTML = `<div class="msg-bubble${thinking ? " msg-thinking" : ""}">${thinking ? "Thinking…" : html}</div>`;
  document.getElementById("chat-messages").appendChild(el);
  scrollChat();
  return el;
}

function scrollChat() {
  const el = document.getElementById("chat-messages");
  el.scrollTop = el.scrollHeight;
}

// ── Init ───────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  // Show first ptab
  const first = document.querySelector(".ptab-content");
  if (first) { first.style.display = "block"; }
});
