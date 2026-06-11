const state = {
  sessionId: localStorage.getItem("arceus.sessionId") || null,
  latestHandoffPrompt: "",
  latestHandoffId: "",
};

const els = {
  runtimePill: document.querySelector("#runtimePill"),
  codexPill: document.querySelector("#codexPill"),
  refreshButton: document.querySelector("#refreshButton"),
  quickSearch: document.querySelector("#quickSearch"),
  sessionState: document.querySelector("#sessionState"),
  messageLog: document.querySelector("#messageLog"),
  chatForm: document.querySelector("#chatForm"),
  chatInput: document.querySelector("#chatInput"),
  presenceTitle: document.querySelector("#presenceTitle"),
  presenceText: document.querySelector("#presenceText"),
  handoffFocus: document.querySelector("#handoffFocus"),
  copyHandoffButton: document.querySelector("#copyHandoffButton"),
  runHandoffButton: document.querySelector("#runHandoffButton"),
  resultForm: document.querySelector("#resultForm"),
  resultHandoffId: document.querySelector("#resultHandoffId"),
  resultSummary: document.querySelector("#resultSummary"),
  resultMemory: document.querySelector("#resultMemory"),
  memoryPulse: document.querySelector("#memoryPulse"),
  handoffList: document.querySelector("#handoffList"),
  activeTaskMetric: document.querySelector("#activeTaskMetric"),
};

function setPresence(title, text) {
  els.presenceTitle.textContent = title;
  els.presenceText.textContent = text;
}

function addMessage(role, content) {
  const message = document.createElement("div");
  message.className = `message ${role}`;
  message.textContent = content;
  els.messageLog.appendChild(message);
  els.messageLog.scrollTop = els.messageLog.scrollHeight;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || "Arceus request failed.");
  }
  return payload;
}

async function refreshAll() {
  await Promise.allSettled([refreshSummary(), refreshRuntime(), refreshHandoffs()]);
}

async function refreshSummary() {
  try {
    const summary = await api("/api/summary?limit=5");
    els.runtimePill.textContent = `Runtime: ${summary.runtime_mode}`;
    renderMemoryPulse(summary);
  } catch (error) {
    els.memoryPulse.textContent = `Memory unavailable: ${error.message}`;
  }
}

async function refreshRuntime() {
  try {
    const report = await api("/api/runtime-doctor");
    els.codexPill.textContent = report.available ? "Codex: available" : "Codex: missing";
  } catch (error) {
    els.codexPill.textContent = "Codex: unknown";
  }
}

async function refreshHandoffs() {
  try {
    const handoffs = await api("/api/handoffs?limit=6");
    renderHandoffs(handoffs);
    restoreRunnableHandoff(handoffs);
  } catch (error) {
    els.handoffList.textContent = `Handoffs unavailable: ${error.message}`;
  }
}

function renderMemoryPulse(summary) {
  const sessions = summary.recent_sessions || [];
  const taskCounts = summary.task_counts || {};
  const activeTasks = Number(taskCounts.running || 0) + Number(taskCounts.pending || 0);
  if (els.activeTaskMetric) {
    els.activeTaskMetric.textContent = String(activeTasks);
  }
  const items = [
    `${sessions.length} recent session(s) visible`,
    `${(summary.recent_handoffs || []).length} recent handoff(s) visible`,
    `${Object.entries(taskCounts).map(([key, value]) => `${key}: ${value}`).join(", ") || "no remote tasks"}`,
  ];
  els.memoryPulse.innerHTML = `<ul class="summary-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
}

function renderHandoffs(handoffs) {
  if (!handoffs.length) {
    els.handoffList.innerHTML = `<p class="muted">No handoffs yet.</p>`;
    return;
  }
  els.handoffList.innerHTML = `<ul class="summary-list">${handoffs.map((handoff) => {
    const detail = handoff.memory_summary || handoff.result_summary || handoff.user_intent;
    return `<li><strong>${escapeHtml(handoff.status)}</strong> - ${escapeHtml(detail || "No detail")}</li>`;
  }).join("")}</ul>`;
}

function restoreRunnableHandoff(handoffs) {
  if (state.latestHandoffId) return;
  const runnable = handoffs.find((handoff) => ["drafted", "failed"].includes(handoff.status));
  if (!runnable) return;
  state.latestHandoffId = runnable.id;
  els.resultHandoffId.value = runnable.id;
  els.runHandoffButton.disabled = false;
}

els.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  await sendMessage(els.chatInput.value.trim());
});

async function sendMessage(message) {
  if (!message) return;

  els.chatInput.value = "";
  if (els.quickSearch) {
    els.quickSearch.value = "";
  }
  addMessage("user", message);
  setPresence("Thinking", "Sorting conversation from action.");

  try {
    const response = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: state.sessionId, message }),
    });

    state.sessionId = response.session_id;
    localStorage.setItem("arceus.sessionId", state.sessionId);
    els.sessionState.textContent = `Session ${state.sessionId.slice(0, 8)}`;
    addMessage("arceus", response.message);

    if (response.handoff_prompt) {
      state.latestHandoffPrompt = response.handoff_prompt;
      state.latestHandoffId = response.handoff_id;
      els.resultHandoffId.value = response.handoff_id;
      els.copyHandoffButton.disabled = false;
      els.runHandoffButton.disabled = false;
      els.handoffFocus.textContent = response.handoff_prompt;
      setPresence("Handoff Drafted", "Codex packet ready for supervised execution.");
    } else {
      setPresence("Watchful", "Conversation held. No handoff needed.");
    }
    await refreshAll();
  } catch (error) {
    addMessage("arceus", `The dashboard fractured: ${error.message}`);
    setPresence("Fractured", "Something failed. Useful, if annoying.");
  }
}

els.resultForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const handoffId = els.resultHandoffId.value.trim();
  if (!handoffId) return;

  try {
    await api(`/api/handoffs/${handoffId}/result`, {
      method: "POST",
      body: JSON.stringify({
        summary: els.resultSummary.value.trim(),
        memory: els.resultMemory.value.trim(),
      }),
    });
    els.resultSummary.value = "";
    els.resultMemory.value = "";
    setPresence("Remembering", "Codex result recorded into local memory.");
    await refreshAll();
  } catch (error) {
    setPresence("Fractured", error.message);
  }
});

els.copyHandoffButton.addEventListener("click", async () => {
  if (!state.latestHandoffPrompt) return;
  await navigator.clipboard.writeText(state.latestHandoffPrompt);
  setPresence("Copied", "Handoff packet copied. Try not to paste it into the void.");
});

els.runHandoffButton.addEventListener("click", async () => {
  const handoffId = state.latestHandoffId || els.resultHandoffId.value.trim();
  if (!handoffId) return;
  els.runHandoffButton.disabled = true;
  setPresence("Executing", "Codex is running the handoff locally with project-scoped write access.");
  try {
    await api(`/api/handoffs/${handoffId}/run`, {
      method: "POST",
      body: JSON.stringify({ confirm: "run_codex" }),
    });
    setPresence("Forging", "Codex autorun started. I will refresh the ledger while it works.");
    await refreshAll();
  } catch (error) {
    els.runHandoffButton.disabled = false;
    setPresence("Fractured", error.message);
  }
});

els.refreshButton.addEventListener("click", refreshAll);

if (els.quickSearch) {
  els.quickSearch.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") return;
    event.preventDefault();
    await sendMessage(els.quickSearch.value.trim());
  });
}

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    els.chatInput.value = button.dataset.prompt || "";
    els.chatInput.focus();
  });
});

document.addEventListener("keydown", (event) => {
  const isMac = navigator.platform.toLowerCase().includes("mac");
  const comboPressed = isMac ? event.metaKey : event.ctrlKey;
  if (!comboPressed || event.key.toLowerCase() !== "k" || !els.quickSearch) return;
  event.preventDefault();
  els.quickSearch.focus();
});

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

if (state.sessionId) {
  els.sessionState.textContent = `Session ${state.sessionId.slice(0, 8)}`;
}

refreshAll();
setInterval(refreshAll, 10000);
