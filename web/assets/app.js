const state = {
  sessionId: localStorage.getItem("arceus.sessionId") || null,
  latestHandoffPrompt: "",
  latestHandoffId: "",
  powerState: localStorage.getItem("arceus.powerState") || "booting",
  subtitleTimer: null,
  latestHandoffs: [],
  taskSummary: { activeTasks: 0, failed: 0, pending: 0, running: 0 },
  currentStatus: null,
  localActions: [],
  localRuns: [],
  pendingLocalActionKey: "",
  activeZone: localStorage.getItem("arceus.activeZone") || "Chats",
  activeProjectSlug: "",
  zonePayload: null,
  zoneSearchTimer: null,
};

const els = {
  powerOverlay: document.querySelector("#powerOverlay"),
  powerEyebrow: document.querySelector("#powerEyebrow"),
  powerTitle: document.querySelector("#powerTitle"),
  powerText: document.querySelector("#powerText"),
  powerStatus: document.querySelector("#powerStatus"),
  wakeButton: document.querySelector("#wakeButton"),
  sleepButton: document.querySelector("#sleepButton"),
  runtimePill: document.querySelector("#runtimePill"),
  codexPill: document.querySelector("#codexPill"),
  controlButton: document.querySelector("#controlButton"),
  refreshButton: document.querySelector("#refreshButton"),
  quickSearch: document.querySelector("#quickSearch"),
  sessionState: document.querySelector("#sessionState"),
  messageLog: document.querySelector("#messageLog"),
  chatForm: document.querySelector("#chatForm"),
  chatInput: document.querySelector("#chatInput"),
  selectedMode: document.querySelector("#selectedMode"),
  presenceTitle: document.querySelector("#presenceTitle"),
  presenceText: document.querySelector("#presenceText"),
  subtitleBar: document.querySelector("#subtitleBar"),
  subtitleSpeaker: document.querySelector("#subtitleSpeaker"),
  subtitleText: document.querySelector("#subtitleText"),
  avatarCore: document.querySelector("#avatarCore"),
  runtimeState: document.querySelector("#runtimeState"),
  runtimeMode: document.querySelector("#runtimeMode"),
  runtimeCopy: document.querySelector("#runtimeCopy"),
  runtimeKind: document.querySelector("#runtimeKind"),
  agentMetric: document.querySelector("#agentMetric"),
  activeTaskMetric: document.querySelector("#activeTaskMetric"),
  taskPlateNote: document.querySelector("#taskPlateNote"),
  memoryState: document.querySelector("#memoryState"),
  memoryMetric: document.querySelector("#memoryMetric"),
  memoryDetail: document.querySelector("#memoryDetail"),
  memoryRingLabel: document.querySelector("#memoryRingLabel"),
  dailyBriefList: document.querySelector("#dailyBriefList"),
  handoffDrawer: document.querySelector("#handoffDrawer"),
  handoffFocus: document.querySelector("#handoffFocus"),
  copyHandoffButton: document.querySelector("#copyHandoffButton"),
  runHandoffButton: document.querySelector("#runHandoffButton"),
  resultForm: document.querySelector("#resultForm"),
  resultHandoffId: document.querySelector("#resultHandoffId"),
  resultSummary: document.querySelector("#resultSummary"),
  resultMemory: document.querySelector("#resultMemory"),
  memoryPulse: document.querySelector("#memoryPulse"),
  handoffList: document.querySelector("#handoffList"),
  localControlDrawer: document.querySelector("#localControlDrawer"),
  localControlState: document.querySelector("#localControlState"),
  localActionList: document.querySelector("#localActionList"),
  localRunList: document.querySelector("#localRunList"),
  refreshLocalActionsButton: document.querySelector("#refreshLocalActionsButton"),
  localApprovalCard: document.querySelector("#localApprovalCard"),
  approvalTitle: document.querySelector("#approvalTitle"),
  approvalDescription: document.querySelector("#approvalDescription"),
  approvalRisk: document.querySelector("#approvalRisk"),
  approvalExpected: document.querySelector("#approvalExpected"),
  approvalDeclineButton: document.querySelector("#approvalDeclineButton"),
  approvalRunButton: document.querySelector("#approvalRunButton"),
  zonePanel: document.querySelector("#zonePanel"),
  zoneTitle: document.querySelector("#zoneTitle"),
  zoneSummary: document.querySelector("#zoneSummary"),
  zoneBody: document.querySelector("#zoneBody"),
  zoneSearch: document.querySelector("#zoneSearch"),
  zoneSearchShell: document.querySelector("#zoneSearchShell"),
  zoneCloseButton: document.querySelector("#zoneCloseButton"),
};

const powerCopy = {
  booting: {
    eyebrow: "Origin boot",
    title: "Arceus is dormant.",
    text: "Local command surface is loaded. Wake the system when you want judgment, memory, or execution.",
    status: "Awaiting wake command",
    button: "Wake Arceus",
  },
  sleeping: {
    eyebrow: "Sleep mode",
    title: "Arceus is sleeping.",
    text: "The command surface is quiet. Memory stays intact; execution stays paused until you wake it.",
    status: "Low-power watch",
    button: "Wake Arceus",
  },
  awake: {
    eyebrow: "Awake",
    title: "Arceus is awake.",
    text: "Command surface active.",
    status: "Online",
    button: "Awake",
  },
};

function applyPowerState(nextState) {
  const safeState = powerCopy[nextState] ? nextState : "booting";
  state.powerState = safeState;
  document.body.dataset.powerState = safeState;
  const copy = powerCopy[safeState];

  setText(els.powerEyebrow, copy.eyebrow);
  setText(els.powerTitle, copy.title);
  setText(els.powerText, copy.text);
  setText(els.powerStatus, copy.status);
  setText(els.wakeButton, copy.button);

  const isAwake = safeState === "awake";
  if (els.powerOverlay) {
    els.powerOverlay.hidden = isAwake;
    els.powerOverlay.setAttribute("aria-hidden", String(isAwake));
  }
  if (els.sleepButton) {
    els.sleepButton.disabled = !isAwake;
    els.sleepButton.textContent = isAwake ? "Sleep" : "Sleeping";
  }

  if (isAwake) {
    localStorage.setItem("arceus.powerState", "awake");
    setPresence("Watchful", "Command surface awake. Try not to spend divine compute on busywork.", 5500);
    requestAnimationFrame(() => els.chatInput?.focus());
  }
}

function wakeArceus() {
  localStorage.setItem("arceus.powerState", "awake");
  applyPowerState("awake");
}

function sleepArceus() {
  localStorage.setItem("arceus.powerState", "sleeping");
  showSubtitle("Arceus", "Sleeping. Memory remains intact; execution stays paused.", { duration: 2400 });
  applyPowerState("sleeping");
}

function setPresence(title, text, duration = 7000) {
  setText(els.presenceTitle, title);
  setText(els.presenceText, text);
  showSubtitle("Arceus", text, { status: title, duration });
}

function setMode(mode) {
  setText(els.selectedMode, mode || "Chat");
}

function addMessage(role, content) {
  if (els.messageLog) {
    const message = document.createElement("div");
    message.className = `message ${role}`;
    message.textContent = content;
    els.messageLog.appendChild(message);
  }

  const speaker = role === "user" ? "You" : "Arceus";
  showSubtitle(speaker, content, { duration: role === "user" ? 4200 : 8500 });
}

function showSubtitle(speaker, content, options = {}) {
  if (!els.subtitleBar || !els.subtitleSpeaker || !els.subtitleText) return;
  const duration = options.duration ?? 7000;
  const status = options.status ? `${options.status}: ` : "";

  window.clearTimeout(state.subtitleTimer);
  els.subtitleSpeaker.textContent = speaker;
  els.subtitleText.textContent = `${status}${content}`;
  els.subtitleBar.classList.add("visible");

  if (duration > 0) {
    state.subtitleTimer = window.setTimeout(() => {
      els.subtitleBar.classList.remove("visible");
    }, duration);
  }
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
  const zoneRefresh = state.activeProjectSlug && document.body.dataset.zoneOpen === "true"
    ? openProjectDetail(state.activeProjectSlug)
    : refreshZone();
  await Promise.allSettled([refreshSummary(), refreshRuntime(), refreshHandoffs(), refreshLocalActions(), zoneRefresh]);
}

async function refreshSummary() {
  try {
    const summary = await api("/api/summary?limit=5");
    const mode = summary.runtime_mode || "unknown";
    setText(els.runtimePill, `Runtime: ${mode}`);
    setText(els.runtimeMode, mode);
    setText(els.runtimeKind, mode);
    setText(els.runtimeState, "Online");
    setText(els.runtimeCopy, mode === "codex_manual" ? "Manual Codex bridge active." : "Local placeholder runtime.");
    state.currentStatus = summary.current_status || null;
    renderMemoryPulse(summary);
  } catch (error) {
    setText(els.memoryPulse, `Memory unavailable: ${error.message}`);
    setText(els.memoryState, "Unavailable");
    setText(els.memoryDetail, error.message);
    showSubtitle("Arceus", `Memory unavailable: ${error.message}`, { status: "Fractured", duration: 8000 });
  }
}

async function refreshRuntime() {
  try {
    const report = await api("/api/runtime-doctor");
    setText(els.codexPill, report.available ? "Codex: available" : "Codex: missing");
    if (els.runtimeState) {
      els.runtimeState.textContent = report.available ? "Ready" : "Needs setup";
      els.runtimeState.dataset.state = report.available ? "ready" : "warning";
    }
  } catch (_error) {
    setText(els.codexPill, "Codex: unknown");
    if (els.runtimeState) {
      els.runtimeState.textContent = "Unknown";
      els.runtimeState.dataset.state = "warning";
    }
  }
}

async function refreshHandoffs() {
  try {
    const handoffs = await api("/api/handoffs?limit=6");
    state.latestHandoffs = handoffs;
    renderHandoffs(handoffs);
    restoreRunnableHandoff(handoffs);
    renderDailyBrief();
  } catch (error) {
    setText(els.handoffList, `Handoffs unavailable: ${error.message}`);
  }
}

async function refreshLocalActions() {
  if (!els.localActionList || !els.localRunList) return;
  try {
    const payload = await api("/api/local-actions?limit=8");
    state.localActions = payload.actions || [];
    state.localRuns = payload.recent_runs || [];
    renderLocalActions();
    renderLocalRuns();
    setText(els.localControlState, state.localRuns.length ? `${state.localRuns.length} run(s)` : "Ready");
  } catch (error) {
    setText(els.localControlState, "Unavailable");
    els.localActionList.innerHTML = `<p class="muted">Local Control unavailable: ${escapeHtml(error.message)}</p>`;
  }
}

async function refreshZone(zone = state.activeZone) {
  if (!els.zoneBody) return;
  const safeZone = zone || "Chats";
  const query = safeZone === "Chats" && els.zoneSearch ? els.zoneSearch.value.trim() : "";
  const suffix = query ? `?q=${encodeURIComponent(query)}` : "";

  try {
    const payload = await api(`/api/zones/${encodeURIComponent(safeZone.toLowerCase())}${suffix}`);
    state.zonePayload = payload;
    renderZone(payload);
  } catch (error) {
    setText(els.zoneTitle, safeZone);
    setText(els.zoneSummary, "This zone could not load.");
    els.zoneBody.innerHTML = `<p class="muted">Zone unavailable: ${escapeHtml(error.message)}</p>`;
  }
}

function renderMemoryPulse(summary) {
  const sessions = summary.recent_sessions || [];
  const handoffs = summary.recent_handoffs || [];
  const taskCounts = summary.task_counts || {};
  const pending = Number(taskCounts.pending || 0);
  const claimed = Number(taskCounts.claimed || 0);
  const running = Number(taskCounts.running || 0);
  const failed = Number(taskCounts.failed || 0);
  const activeTasks = pending + claimed + running;
  state.taskSummary = { activeTasks, failed, pending, running };
  if (handoffs.length) state.latestHandoffs = handoffs;

  setText(els.activeTaskMetric, String(activeTasks));
  setText(els.taskPlateNote, activeTasks ? `${activeTasks} task(s) need attention.` : "No running tasks.");
  setText(els.memoryMetric, sessions.length || handoffs.length ? "Enabled" : "Local");
  setText(els.memoryState, failed > 0 ? "Review" : "Synced");
  setText(els.memoryRingLabel, failed > 0 ? "!" : "On");
  setText(els.memoryDetail, `${sessions.length} sessions · ${handoffs.length} handoffs`);

  const items = [
    `${sessions.length} recent session(s) visible`,
    `${handoffs.length} recent handoff(s) visible`,
    `${formatTaskCounts(taskCounts) || "no remote tasks"}`,
  ];
  if (els.memoryPulse) {
    els.memoryPulse.innerHTML = `<ul class="summary-list">${items.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>`;
  }

  renderDailyBrief();
}

function renderDailyBrief() {
  if (!els.dailyBriefList) return;
  const { activeTasks, failed, pending, running } = state.taskSummary;
  const latest = state.latestHandoffs[0];
  const latestStatus = state.currentStatus?.latest_update;

  const items = [];
  if (latestStatus?.summary) {
    items.push(`Current state: ${latestStatus.status} / ${latestStatus.workstream} - ${latestStatus.summary}`);
  }
  if (failed > 0) items.push(`${failed} failed task(s) need review before new execution.`);
  if (activeTasks > 0) items.push(`${activeTasks} local task(s) are active or queued: ${running} running, ${pending} pending.`);
  if (latest) {
    const detail = latest.memory_summary || latest.result_summary || latest.user_intent || "No detail";
    items.push(`Latest Codex activity: ${statusLabel(latest.status)} - ${detail}`);
  }
  items.push("Daily research is not connected yet; overnight findings will appear here when that agent exists.");
  items.push("Use a shortcut below when you want Arceus to frame the request before execution.");

  els.dailyBriefList.innerHTML = items.slice(0, 4).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
}

function renderHandoffs(handoffs) {
  if (!els.handoffList) return;
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
  if (els.resultHandoffId) els.resultHandoffId.value = runnable.id;
  if (els.runHandoffButton) els.runHandoffButton.disabled = false;
  if (els.copyHandoffButton) els.copyHandoffButton.disabled = !state.latestHandoffPrompt;
}

function renderLocalActions() {
  if (!els.localActionList) return;
  if (!state.localActions.length) {
    els.localActionList.innerHTML = `<p class="muted">No local actions registered.</p>`;
    return;
  }

  els.localActionList.innerHTML = state.localActions.map((action) => {
    const approval = action.approval_required ? "Approval required" : "No approval needed";
    const buttonText = action.approval_required ? "Review approval" : "Run check";
    return `
      <article class="local-action-card risk-${escapeHtml(action.risk_level)}">
        <div>
          <span class="risk-tag">${escapeHtml(action.risk_level)}</span>
          <h3>${escapeHtml(action.title)}</h3>
          <p>${escapeHtml(action.description)}</p>
        </div>
        <div class="local-action-footer">
          <small>${escapeHtml(approval)} · ${escapeHtml(action.expected_output)}</small>
          <button type="button" data-local-action="${escapeHtml(action.key)}">${escapeHtml(buttonText)}</button>
        </div>
      </article>
    `;
  }).join("");
}

function renderLocalRuns() {
  if (!els.localRunList) return;
  if (!state.localRuns.length) {
    els.localRunList.innerHTML = `<p class="muted">No local action runs yet.</p>`;
    return;
  }

  els.localRunList.innerHTML = `<ul class="summary-list local-run-items">${state.localRuns.map((run) => {
    const detail = run.output_summary || run.error_message || run.title || "No detail";
    return `
      <li class="run-${escapeHtml(run.status)}">
        <strong>${escapeHtml(statusLabel(run.status))}</strong>
        <span>${escapeHtml(run.title || run.action_key)} - ${escapeHtml(detail)}</span>
      </li>
    `;
  }).join("")}</ul>`;
}

function renderZone(payload) {
  if (!els.zoneBody) return;
  const zone = payload.zone || state.activeZone.toLowerCase();
  setText(els.zoneTitle, payload.title || state.activeZone);
  setText(els.zoneSummary, payload.summary || "No summary yet.");

  const isChatZone = zone === "chats";
  if (els.zoneSearchShell) els.zoneSearchShell.hidden = !isChatZone;

  if (zone === "chats") {
    renderChatZone(payload.items || []);
    return;
  }
  if (zone === "agents") {
    renderAgentZone(payload.items || []);
    return;
  }
  if (zone === "tasks") {
    renderTaskZone(payload);
    return;
  }
  if (zone === "workflows") {
    renderWorkflowZone(payload.items || []);
    return;
  }
  if (zone === "projects") {
    renderProjectZone(payload.items || []);
    return;
  }
  els.zoneBody.innerHTML = `<p class="muted">No view exists for this zone yet.</p>`;
}

function openZonePanel() {
  if (!els.zonePanel) return;
  document.body.dataset.zoneOpen = "true";
  els.zonePanel.setAttribute("aria-hidden", "false");
  requestAnimationFrame(() => els.zonePanel.classList.add("open"));
}

function closeZonePanel() {
  if (!els.zonePanel) return;
  state.activeProjectSlug = "";
  document.body.dataset.zoneOpen = "false";
  els.zonePanel.classList.remove("open");
  els.zonePanel.setAttribute("aria-hidden", "true");
  if (location.hash && isZoneHash(location.hash)) {
    history.replaceState(null, "", `${location.pathname}${location.search}`);
  }
}

function renderChatZone(items) {
  if (!items.length) {
    els.zoneBody.innerHTML = `<p class="muted">No matching chats yet.</p>`;
    return;
  }

  const groups = items.reduce((acc, item) => {
    const key = formatDay(item.updated_at || item.created_at);
    if (!acc[key]) acc[key] = [];
    acc[key].push(item);
    return acc;
  }, {});

  els.zoneBody.innerHTML = Object.entries(groups).map(([day, chats]) => `
    <section class="zone-group">
      <div class="zone-group-title">
        <span>${escapeHtml(day)}</span>
        <small>${chats.length} chat${chats.length === 1 ? "" : "s"}</small>
      </div>
      <div class="zone-record-list">
        ${chats.map((chat) => {
          const tags = Array.isArray(chat.tags) ? chat.tags : [];
          return `
            <article class="zone-record chat-record">
              <div>
                <h3>${escapeHtml(chat.title || "Arceus Conversation")}</h3>
                <p>${escapeHtml(chat.runtime || "offline")} · ${escapeHtml(chat.message_count || 0)} message(s) · ${escapeHtml(formatDate(chat.updated_at))}</p>
              </div>
              <div class="tag-row">
                ${tags.length ? tags.map((tag) => `<span class="tag tag-${escapeHtml(tag.color || "cyan")}">${escapeHtml(tag.name)}</span>`).join("") : `<span class="tag">untagged</span>`}
              </div>
            </article>
          `;
        }).join("")}
      </div>
    </section>
  `).join("");
}

function renderAgentZone(items) {
  setText(els.agentMetric, String(items.length));
  if (!items.length) {
    els.zoneBody.innerHTML = `<p class="muted">No agents registered yet.</p>`;
    return;
  }

  els.zoneBody.innerHTML = `
    <div class="zone-card-grid agents-grid">
      ${items.map((agent) => `
        <article class="agent-card zone-card">
          <div class="zone-card-head">
            <span class="agent-mark">${escapeHtml(agent.name?.slice(0, 2) || "AG")}</span>
            <div>
              <h3>${escapeHtml(agent.name)}</h3>
              <p>${escapeHtml(agent.role)} · ${escapeHtml(agent.category)}</p>
            </div>
          </div>
          <p>${escapeHtml(agent.summary)}</p>
          <div class="tag-row">
            <span class="tag tag-gold">${escapeHtml(agent.lore_identity || "Specialist")}</span>
            <span class="tag">${escapeHtml(agent.status)}</span>
            <span class="tag">${escapeHtml(agent.trust_level)}</span>
            ${agent.can_run_local ? `<span class="tag tag-teal">local</span>` : `<span class="tag">cloud-safe later</span>`}
          </div>
        </article>
      `).join("")}
    </div>
  `;
}

function renderTaskZone(payload) {
  const items = payload.items || [];
  const remoteTasks = payload.remote_tasks || [];
  const localRuns = payload.local_runs || [];
  if (!items.length && !remoteTasks.length && !localRuns.length) {
    els.zoneBody.innerHTML = `<p class="muted">No tasks recorded yet.</p>`;
    return;
  }

  const activeCount = items.filter((task) => ["queued", "awaiting_approval", "running"].includes(task.status)).length;
  setText(els.activeTaskMetric, String(activeCount || state.taskSummary.activeTasks || 0));
  if (items.length) setText(els.taskPlateNote, `${items.length} planned dashboard task(s).`);

  els.zoneBody.innerHTML = `
    <div class="task-lanes">
      ${renderTaskLane("Planned Work", items)}
      ${renderCompactRunLane("Recent Local Runs", localRuns, "title", "output_summary")}
      ${renderCompactRunLane("Remote Queue", remoteTasks, "kind", "error_message")}
    </div>
  `;
}

function renderTaskLane(title, items) {
  if (!items.length) return `<section class="task-lane"><h3>${escapeHtml(title)}</h3><p class="muted">None.</p></section>`;
  return `
    <section class="task-lane">
      <h3>${escapeHtml(title)}</h3>
      ${items.map((task) => `
        <article class="task-row risk-${escapeHtml(task.risk_level)}">
          <div>
            <strong>${escapeHtml(task.title)}</strong>
            <p>${escapeHtml(task.summary)}</p>
            <small>${escapeHtml(task.project_name || "No project")} · ${escapeHtml(task.agent_name || "No agent")}</small>
          </div>
          <div class="task-status-stack">
            <span class="tag">${escapeHtml(statusLabel(task.status))}</span>
            <span class="tag">${escapeHtml(task.risk_level)} risk</span>
            <span class="tag">${escapeHtml(statusLabel(task.approval_state))}</span>
          </div>
        </article>
      `).join("")}
    </section>
  `;
}

function renderCompactRunLane(title, items, primaryKey, detailKey) {
  if (!items.length) return `<section class="task-lane"><h3>${escapeHtml(title)}</h3><p class="muted">None.</p></section>`;
  return `
    <section class="task-lane compact-lane">
      <h3>${escapeHtml(title)}</h3>
      ${items.map((item) => `
        <article class="compact-row">
          <strong>${escapeHtml(item[primaryKey] || "Untitled")}</strong>
          <span>${escapeHtml(statusLabel(item.status))}</span>
          <p>${escapeHtml(item[detailKey] || item.error_message || item.worker_role || "No detail")}</p>
        </article>
      `).join("")}
    </section>
  `;
}

function renderWorkflowZone(items) {
  if (!items.length) {
    els.zoneBody.innerHTML = `<p class="muted">No workflows mapped yet.</p>`;
    return;
  }

  els.zoneBody.innerHTML = items.map((workflow) => {
    const graph = workflow.graph || {};
    const nodes = Array.isArray(graph.nodes) ? graph.nodes : [];
    const edges = Array.isArray(graph.edges) ? graph.edges : [];
    return `
      <article class="workflow-card">
        <div class="zone-card-head">
          <div>
            <h3>${escapeHtml(workflow.name)}</h3>
            <p>${escapeHtml(workflow.summary)}</p>
          </div>
          <span class="tag tag-violet">${escapeHtml(workflow.status)}</span>
        </div>
        <div class="workflow-map">
          ${nodes.map((node) => `<span class="workflow-node node-${escapeHtml(node.kind || "step")}">${escapeHtml(node.label)}</span>`).join("")}
        </div>
        <div class="workflow-edges">
          ${edges.map((edge) => `<span>${escapeHtml(edge.from)} → ${escapeHtml(edge.to)} · ${escapeHtml(edge.label)}</span>`).join("")}
        </div>
      </article>
    `;
  }).join("");
}

function renderProjectZone(items) {
  state.activeProjectSlug = "";
  if (!items.length) {
    els.zoneBody.innerHTML = `<p class="muted">No projects registered yet.</p>`;
    return;
  }

  els.zoneBody.innerHTML = `
    <div class="zone-card-grid project-grid">
      ${items.map((project) => `
        <article class="project-card zone-card" data-project-slug="${escapeHtml(project.slug)}">
          <div class="zone-card-head">
            <div>
              <h3>${escapeHtml(project.name)}</h3>
              <p>${escapeHtml(project.focus || "No focus set.")}</p>
            </div>
            <span class="tag tag-teal">${escapeHtml(project.status)}</span>
          </div>
          <p>${escapeHtml(project.summary)}</p>
          <div class="project-metrics">
            <span><strong>${escapeHtml(project.task_count || 0)}</strong> tasks</span>
            <span><strong>${escapeHtml(project.active_task_count || 0)}</strong> active</span>
            <span><strong>${escapeHtml(project.completed_task_count || 0)}</strong> done</span>
          </div>
          <button class="secondary-button project-open-button" type="button" data-project-open="${escapeHtml(project.slug)}">Open project</button>
        </article>
      `).join("")}
    </div>
  `;
}

async function openProjectDetail(slug) {
  if (!slug || !els.zoneBody) return;
  state.activeProjectSlug = slug;
  if (els.zoneSearchShell) els.zoneSearchShell.hidden = true;
  setText(els.zoneTitle, "Projects");
  setText(els.zoneSummary, "Loading project folder.");
  els.zoneBody.innerHTML = `<p class="muted">Opening project...</p>`;
  openZonePanel();

  try {
    const payload = await api(`/api/projects/${encodeURIComponent(slug)}`);
    renderProjectDetail(payload);
    const nextHash = `#projects/${slug}`;
    if (location.hash !== nextHash) history.replaceState(null, "", nextHash);
  } catch (error) {
    setText(els.zoneSummary, "Project detail could not load.");
    els.zoneBody.innerHTML = `<p class="muted">Project unavailable: ${escapeHtml(error.message)}</p>`;
  }
}

function renderProjectDetail(payload) {
  const project = payload.project || {};
  const tasks = payload.tasks || [];
  const agents = payload.agents || [];
  const slug = project.slug || state.activeProjectSlug;

  setText(els.zoneTitle, project.name || "Project");
  setText(els.zoneSummary, project.focus || project.summary || "Project folder.");

  els.zoneBody.innerHTML = `
    <section class="project-detail">
      <div class="project-detail-hero">
        <button class="secondary-button project-back-button" type="button" data-project-back>Back to projects</button>
        <div>
          <p class="eyebrow">Project folder</p>
          <h3>${escapeHtml(project.name || "Untitled project")}</h3>
          <p>${escapeHtml(project.summary || "No summary recorded yet.")}</p>
        </div>
        <div class="project-metrics project-detail-metrics">
          <span><strong>${escapeHtml(project.task_count || 0)}</strong> tasks</span>
          <span><strong>${escapeHtml(project.active_task_count || 0)}</strong> active</span>
          <span><strong>${escapeHtml(project.completed_task_count || 0)}</strong> done</span>
        </div>
      </div>

      <div class="project-detail-grid">
        <section class="task-lane project-task-list">
          <h3>Attached Tasks</h3>
          ${tasks.length ? tasks.map((task) => renderProjectTask(task)).join("") : `<p class="muted">No tasks attached yet.</p>`}
        </section>

        <section class="task-create-card">
          <p class="eyebrow">Supervised capture</p>
          <h3>Create planned task</h3>
          <p>Creates a dashboard task only. It does not run Codex or touch local files.</p>
          <form class="task-create-form" id="taskCreateForm" data-project-slug="${escapeHtml(slug)}">
            <label>
              <span>Task</span>
              <input name="title" type="text" placeholder="e.g. Draft this week's Instagram content plan" required />
            </label>
            <label>
              <span>Summary</span>
              <textarea name="summary" rows="3" placeholder="What should Arceus preserve as the intent, expected output, and constraint?"></textarea>
            </label>
            <div class="task-create-grid">
              <label>
                <span>Specialist</span>
                <select name="agent_slug">
                  <option value="">Let Arceus route later</option>
                  ${agents.map((agent) => `<option value="${escapeHtml(agent.slug)}">${escapeHtml(agent.name)} · ${escapeHtml(agent.category)}</option>`).join("")}
                </select>
              </label>
              <label>
                <span>Risk</span>
                <select name="risk_level">
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </label>
            </div>
            <label>
              <span>Approval</span>
              <select name="approval_state">
                <option value="required">Approval required</option>
                <option value="not_required">No approval needed later</option>
              </select>
            </label>
            <button type="submit">Create planned task</button>
          </form>
        </section>
      </div>
    </section>
  `;
}

function renderProjectTask(task) {
  return `
    <article class="task-row risk-${escapeHtml(task.risk_level)}">
      <div>
        <strong>${escapeHtml(task.title)}</strong>
        <p>${escapeHtml(task.summary)}</p>
        <small>${escapeHtml(task.agent_name || "No specialist assigned")} · ${escapeHtml(formatDate(task.updated_at))}</small>
      </div>
      <div class="task-status-stack">
        <span class="tag">${escapeHtml(statusLabel(task.status))}</span>
        <span class="tag">${escapeHtml(task.risk_level)} risk</span>
        <span class="tag">${escapeHtml(statusLabel(task.approval_state))}</span>
      </div>
    </article>
  `;
}

async function createDashboardTask(form) {
  const data = new FormData(form);
  const title = String(data.get("title") || "").trim();
  if (!title) return;

  const button = form.querySelector("button[type='submit']");
  if (button) button.disabled = true;
  setPresence("Capturing", "Creating a planned task. Nothing is executing yet.", 0);

  try {
    await api("/api/tasks", {
      method: "POST",
      body: JSON.stringify({
        title,
        summary: String(data.get("summary") || "").trim(),
        project_slug: form.dataset.projectSlug || state.activeProjectSlug,
        agent_slug: String(data.get("agent_slug") || "").trim(),
        risk_level: String(data.get("risk_level") || "low"),
        approval_state: String(data.get("approval_state") || "required"),
      }),
    });
    form.reset();
    setPresence("Captured", "Planned task created and written into status memory.", 6500);
    await openProjectDetail(form.dataset.projectSlug || state.activeProjectSlug);
    await refreshSummary();
  } catch (error) {
    setPresence("Fractured", error.message, 9000);
  } finally {
    if (button) button.disabled = false;
  }
}

async function runLocalAction(actionKey) {
  const action = state.localActions.find((item) => item.key === actionKey);
  if (!action) return;

  if (action.approval_required) {
    showLocalApproval(action);
    return;
  }

  await executeLocalAction(action);
}

function showLocalApproval(action) {
  state.pendingLocalActionKey = action.key;
  setText(els.approvalTitle, action.title);
  setText(els.approvalDescription, action.description);
  setText(els.approvalRisk, action.risk_level);
  setText(els.approvalExpected, action.expected_output);
  if (els.localApprovalCard) {
    els.localApprovalCard.hidden = false;
    els.localApprovalCard.dataset.risk = action.risk_level;
    requestAnimationFrame(() => els.localApprovalCard.classList.add("visible"));
  }
  setPresence("Awaiting approval", `${action.title} needs your approval before it runs.`, 0);
  els.approvalRunButton?.focus();
}

function clearLocalApproval() {
  state.pendingLocalActionKey = "";
  if (!els.localApprovalCard) return;
  els.localApprovalCard.classList.remove("visible");
  window.setTimeout(() => {
    if (!state.pendingLocalActionKey && els.localApprovalCard) {
      els.localApprovalCard.hidden = true;
    }
  }, 180);
}

async function executeLocalAction(action) {
  if (!action) return;

  const payload = {};
  if (action.key === "run_latest_handoff" && state.latestHandoffId) {
    payload.handoff_id = state.latestHandoffId;
  }

  const confirmValue = action.approval_required ? action.key : null;
  clearLocalApproval();
  setText(els.localControlState, "Running");
  if (els.approvalRunButton) els.approvalRunButton.disabled = true;
  setPresence("Local Control", `${action.title} is running locally.`, 0);
  try {
    const result = await api(`/api/local-actions/${encodeURIComponent(action.key)}/run`, {
      method: "POST",
      body: JSON.stringify({ confirm: confirmValue, payload }),
    });
    const summary = result.result?.summary || result.error || `${action.title} finished.`;
    setPresence(result.ok ? "Completed" : "Fractured", summary, result.ok ? 7000 : 10000);
    await refreshAll();
  } catch (error) {
    setPresence("Fractured", error.message, 10000);
    await refreshLocalActions();
  } finally {
    if (els.approvalRunButton) els.approvalRunButton.disabled = false;
  }
}

async function sendMessage(message) {
  if (!message) return;

  els.chatInput.value = "";
  if (els.quickSearch) els.quickSearch.value = "";
  addMessage("user", message);
  setPresence("Thinking", "Separating conversation, memory, and execution.", 0);

  try {
    const response = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: state.sessionId, message }),
    });

    state.sessionId = response.session_id;
    localStorage.setItem("arceus.sessionId", state.sessionId);
    setText(els.sessionState, `Session ${state.sessionId.slice(0, 8)}`);
    addMessage("arceus", response.message);

    if (response.handoff_prompt) {
      state.latestHandoffPrompt = response.handoff_prompt;
      state.latestHandoffId = response.handoff_id;
      if (els.resultHandoffId) els.resultHandoffId.value = response.handoff_id;
      if (els.copyHandoffButton) els.copyHandoffButton.disabled = false;
      if (els.runHandoffButton) els.runHandoffButton.disabled = false;
      if (els.handoffFocus) els.handoffFocus.textContent = response.handoff_prompt;
      setPresence("Handoff drafted", "Codex packet is ready in the hidden execution ledger.", 9000);
    } else {
      setPresence("Watchful", "Conversation held. No handoff needed.", 5000);
    }
    await refreshAll();
  } catch (error) {
    addMessage("arceus", `The dashboard fractured: ${error.message}`);
    setPresence("Fractured", error.message, 9000);
  }
}

function bindEvents() {
  els.chatForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    await sendMessage(els.chatInput.value.trim());
  });

  els.resultForm?.addEventListener("submit", async (event) => {
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
      setPresence("Remembering", "Codex result recorded into local memory.", 7000);
      await refreshAll();
    } catch (error) {
      setPresence("Fractured", error.message, 9000);
    }
  });

  els.copyHandoffButton?.addEventListener("click", async () => {
    if (!state.latestHandoffPrompt) return;
    await navigator.clipboard.writeText(state.latestHandoffPrompt);
    setPresence("Copied", "Handoff packet copied. Aim before you summon.", 5000);
  });

  els.runHandoffButton?.addEventListener("click", async () => {
    const handoffId = state.latestHandoffId || els.resultHandoffId.value.trim();
    if (!handoffId) return;
    els.runHandoffButton.disabled = true;
    setPresence("Executing", "Codex is running locally with project-scoped write access.", 0);
    try {
      await api(`/api/handoffs/${handoffId}/run`, {
        method: "POST",
        body: JSON.stringify({ confirm: "run_codex" }),
      });
      setPresence("Forging", "Codex autorun started. I will refresh the ledger while it works.", 12000);
      await refreshAll();
    } catch (error) {
      els.runHandoffButton.disabled = false;
      setPresence("Fractured", error.message, 9000);
    }
  });

  els.refreshButton?.addEventListener("click", refreshAll);
  els.refreshLocalActionsButton?.addEventListener("click", refreshLocalActions);
  els.zoneCloseButton?.addEventListener("click", closeZonePanel);
  els.controlButton?.addEventListener("click", () => {
    if (!els.localControlDrawer) return;
    els.localControlDrawer.open = true;
    els.localControlDrawer.scrollIntoView({ behavior: "smooth", block: "center" });
  });
  els.wakeButton?.addEventListener("click", wakeArceus);
  els.sleepButton?.addEventListener("click", sleepArceus);

  els.avatarCore?.addEventListener("click", () => {
    showSubtitle("Arceus", "Still here. Ask the useful question, not the decorative one.", { duration: 5200 });
  });

  if (els.quickSearch) {
    els.quickSearch.addEventListener("keydown", async (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      await sendMessage(els.quickSearch.value.trim());
    });
  }

  els.zoneSearch?.addEventListener("input", () => {
    window.clearTimeout(state.zoneSearchTimer);
    state.zoneSearchTimer = window.setTimeout(() => {
      if (state.activeZone === "Chats") refreshZone("Chats");
    }, 180);
  });

  els.zoneBody?.addEventListener("click", async (event) => {
    const openButton = event.target.closest("[data-project-open]");
    if (openButton) {
      await openProjectDetail(openButton.dataset.projectOpen);
      return;
    }

    const backButton = event.target.closest("[data-project-back]");
    if (backButton) {
      if (location.hash !== "#projects") history.replaceState(null, "", "#projects");
      await refreshZone("Projects");
    }
  });

  els.zoneBody?.addEventListener("dblclick", async (event) => {
    const projectCard = event.target.closest("[data-project-slug]");
    if (!projectCard) return;
    await openProjectDetail(projectCard.dataset.projectSlug);
  });

  els.zoneBody?.addEventListener("submit", async (event) => {
    const form = event.target.closest("#taskCreateForm");
    if (!form) return;
    event.preventDefault();
    await createDashboardTask(form);
  });

  document.querySelectorAll("[data-prompt]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll(".shortcut-card").forEach((card) => card.classList.remove("selected"));
      button.classList.add("selected");
      setMode(button.dataset.mode || button.querySelector("span")?.textContent || "Chat");
      els.chatInput.value = button.dataset.prompt || "";
      els.chatInput.focus();
      showSubtitle("Arceus", `${button.dataset.mode || "Mode"} frame loaded. Replace the bracketed part with the real ask.`, { duration: 5200 });
    });
  });

  document.querySelectorAll("[data-zone]").forEach((control) => {
    control.addEventListener("click", () => activateZone(control.dataset.zone, control.dataset.zoneCopy));
    control.addEventListener("dblclick", () => {
      if (control.dataset.zone === "Projects") {
        showSubtitle("Projects", "Open a project card to drill into tasks and supervised captures.", { duration: 5200 });
      }
    });
  });

  els.localActionList?.addEventListener("click", async (event) => {
    const button = event.target.closest("[data-local-action]");
    if (!button) return;
    await runLocalAction(button.dataset.localAction);
  });

  els.approvalDeclineButton?.addEventListener("click", () => {
    const action = state.localActions.find((item) => item.key === state.pendingLocalActionKey);
    clearLocalApproval();
    setPresence("Declined", `${action?.title || "Local action"} was not run. Correct restraint, annoyingly useful.`, 5200);
  });

  els.approvalRunButton?.addEventListener("click", async () => {
    const action = state.localActions.find((item) => item.key === state.pendingLocalActionKey);
    if (!action) return;
    await executeLocalAction(action);
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && document.body.dataset.zoneOpen === "true") {
      closeZonePanel();
      return;
    }

    if (state.powerState !== "awake" && event.key === "Enter") {
      event.preventDefault();
      wakeArceus();
      return;
    }

    const isMac = navigator.platform.toLowerCase().includes("mac");
    const comboPressed = isMac ? event.metaKey : event.ctrlKey;
    if (!comboPressed || event.key.toLowerCase() !== "k" || !els.quickSearch) return;
    event.preventDefault();
    els.quickSearch.focus();
  });
}

function activateZone(zone, copy) {
  if (!zone) return;
  state.activeProjectSlug = "";
  selectZone(zone);
  setText(els.zoneTitle, zone);
  setText(els.zoneSummary, "Loading zone data.");
  if (els.zoneBody) els.zoneBody.innerHTML = `<p class="muted">Loading ${escapeHtml(zone)}...</p>`;
  showSubtitle(zone, "Opening dashboard zone.", { duration: 2200 });
  if (location.hash.toLowerCase() !== `#${zone.toLowerCase()}`) {
    history.replaceState(null, "", `#${zone.toLowerCase()}`);
  }
  openZonePanel();
  refreshZone(zone);
}

function selectZone(zone) {
  if (!zone) return;
  state.activeZone = zone;
  localStorage.setItem("arceus.activeZone", zone);
  document.querySelectorAll(".zone-item").forEach((item) => {
    item.classList.toggle("selected", item.dataset.zone === zone);
  });
}

function initialZoneFromHash() {
  const value = String(location.hash || "").replace(/^#/, "").toLowerCase();
  if (!isZoneHash(location.hash)) return "";
  const zone = value.split("/")[0];
  return zone.replace(/(^|-)([a-z])/g, (_match, _dash, char) => char.toUpperCase());
}

function initialProjectSlugFromHash() {
  const value = String(location.hash || "").replace(/^#/, "").toLowerCase();
  if (!value.startsWith("projects/")) return "";
  return value.split("/").slice(1).join("/");
}

function isZoneHash(hash) {
  const value = String(hash || "").replace(/^#/, "").toLowerCase();
  const zone = value.split("/")[0];
  return ["chats", "agents", "tasks", "workflows", "projects"].includes(zone);
}

function formatTaskCounts(taskCounts) {
  return Object.entries(taskCounts)
    .map(([key, value]) => `${key}: ${value}`)
    .join(", ");
}

function statusLabel(status) {
  return String(status || "unknown").replaceAll("_", " ");
}

function formatDate(value) {
  if (!value) return "unknown";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

function formatDay(value) {
  if (!value) return "Undated";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Undated";
  return new Intl.DateTimeFormat(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  }).format(date);
}

function setText(element, value) {
  if (element) element.textContent = value;
}

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
  setText(els.sessionState, `Session ${state.sessionId.slice(0, 8)}`);
}

bindEvents();
applyPowerState(state.powerState);
const hashedZone = initialZoneFromHash();
const hashedProject = initialProjectSlugFromHash();
if (hashedProject) {
  selectZone("Projects");
  openProjectDetail(hashedProject);
} else if (hashedZone) {
  activateZone(hashedZone);
} else {
  selectZone(state.activeZone);
  closeZonePanel();
}
refreshAll();
setInterval(refreshAll, 10000);
