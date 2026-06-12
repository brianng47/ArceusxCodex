# Tier Build Guide

This guide explains the active build order for Arceus.

As of 2026-06-12, the roadmap is Jarvis OS-first. The dashboard is important,
but it is no longer the lead workstream. Arceus must first become a personal
operating layer that knows Brian, reasons over context, plans workflows, asks
for holistic approval, delegates to bounded concurrent specialists, executes
through local-safe runtimes, and writes useful memory back to Obsidian.

The principle is still simple: build the smallest useful layer, verify it, then
move to the next layer. The difference is that the layers now follow operating
system dependencies, not dashboard screens.

## Current Completed Foundation

These pieces already exist as v0 foundations:

- project doctrine, PRD, architecture, guardrails, agent rules, and design
  direction;
- Postgres-backed durable task queue with a `noop` worker path;
- local conversation shell and dashboard chat;
- supervised Codex handoff drafting, manual result recording, and scoped
  Codex autorun;
- automatic status tracker with Postgres records and Obsidian Current State
  notes;
- local dashboard v0 and macOS launcher;
- Local Control v0 with a fixed allowed-action catalog and dashboard approval
  card;
- Filesystem/Code Agent v0 for inspect, read, draft full-file proposals, and
  apply proposals with explicit confirmation.

These are foundations, not the finished OS.

## Active Build Order

### Segment 1: Jarvis OS Contract

Goal:

- define one operating contract for intent, context, plans, approvals, agent
  runs, artifacts, synthesis, and memory writeback.

Why it comes first:

- Arceus must not grow separate models for dashboard tasks, Codex handoffs,
  local actions, memory notes, and specialist work. One contract reduces
  rework and prevents hidden state mismatches.

Verification:

1. A non-trivial request can be represented as a problem statement, context
   bundle, plan, risk profile, approval bundle, agent assignments, and final
   synthesis.
2. CLI, local API, future dashboard, and future phone/PWA can all use the same
   contract.
3. Every run records runtime, reason for runtime choice, result, failure state,
   artifacts, and memory notes.

### Segment 2: Personal Memory Vault

Goal:

- make Obsidian the personal knowledge layer that lets Arceus know Brian better
  than vanilla Codex, Claude, Grok, or any single LLM.

Build direction:

- use the whole Obsidian vault as Arceus' personal memory surface;
- apply a nested LLM-wiki pattern with a map file, `raw/`, `wiki/`,
  `wiki/index.md`, `wiki/log.md`, `wiki/hot.md`, and `wiki/audits/`;
- use Obsidian links, frontmatter, and indexes as the routing layer;
- keep Postgres as the operational ledger for tasks, approvals, events, and
  crash recovery.

Verification:

1. Arceus reads the map and index before answering memory-backed questions.
2. Clarifying answers from Brian are saved into the wiki and reused later.
3. New durable knowledge updates the correct wiki page, index, log, and hot
   cache.
4. Source-backed factual claims keep source metadata.

### Segment 3: Clarification Engine

Goal:

- let Arceus extract the real problem statement, infer from memory, draft a
  plan, and ask only the questions that materially change the workflow.

Default behavior:

- plan then confirm;
- ask clarifying questions when missing context changes scope, success
  criteria, risk, dependencies, or runtime choice;
- save useful answers to Obsidian so the same context is not requested again.

Verification:

1. A vague request produces a concise problem statement and assumptions.
2. Arceus asks targeted follow-up questions instead of guessing blindly.
3. The answers become structured memory entries.

### Segment 4: Runtime Broker

Goal:

- make Arceus the layer above Codex, Claude Code, Claude Cowork, Grok, and
  future engines.

Why it matters:

- the product value is not any one model. The value is knowing when to use each
  runtime, preserving context across them, and auditing the result.

Verification:

1. Arceus can choose a runtime per subtask and record why.
2. Runtime selection does not change the memory, approval, or task contract.
3. Codex remains preferred for local repo/code execution until another runtime
   is explicitly integrated and verified.

### Segment 5: Bounded Workflow Swarm

Goal:

- support concurrent specialist agents without unbounded cascades.

First target:

- 2-4 concurrent specialist tasks with dependency tracking, status updates,
  cancellation, failure recording, and one final synthesis.

Verification:

1. Arceus decomposes a complex request into specialist subtasks.
2. Independent subtasks can run concurrently.
3. Dependent subtasks wait for prerequisites.
4. Failures are isolated and reflected in the synthesis.
5. No duplicate execution occurs after restart.

### Segment 6: Holistic Approval Bundle

Goal:

- replace one-action-at-a-time approval friction with a workflow-level approval
  packet.

What the approval bundle shows:

- problem statement;
- planned steps;
- specialists and runtimes;
- dependencies;
- files, folders, tools, services, or memory areas touched;
- risk level per step;
- which low-risk actions can run automatically;
- which medium or high-risk actions still require explicit approval;
- expected outputs and rollback or recovery notes.

Verification:

1. Arceus can request one holistic approval before execution.
2. Whitelisted low-risk actions may run automatically after the plan is
   approved.
3. Writes, destructive actions, publishing, credentials, purchases, financial
   actions, and irreversible operations still require explicit approval.

### Segment 7: First Capability Trio

Goal:

- prove Arceus is useful across the three non-optional working-OS loops.

Required loops:

- File/code agent loop: inspect, read, draft, approve, apply, verify, remember.
- Project memory loop: capture context, update wiki pages, maintain index/log,
  and reuse memory later.
- TCG Instagram growth loop: plan and track `riprocket_tcg` Instagram growth
  work as real business operations.

Verification:

1. One natural-language request can produce useful work across all three loops.
2. The result includes a final synthesis, saved memory, and clear next actions.
3. TCG work attaches to the existing `riprocket_tcg Instagram Growth` project.

### Segment 8: Push-To-Talk Voice

Goal:

- add fast voice control without making always-listening reliability and
  privacy problems the first voice milestone.

First target:

- push-to-talk speech input;
- low-latency transcript;
- TTS response;
- visible text fallback;
- voice state reflected in avatar/core state.

Verification:

1. A voice command can trigger the same OS workflow as typed input.
2. The transcript is visible and correctable.
3. Failed speech or TTS does not block the text workflow.

### Segment 9: Production-Like Local Hardening

Goal:

- make the local OS reliable before adding a polished dashboard or remote phone
  surface.

Verification:

1. Migrations are idempotent.
2. Queued tasks survive restart.
3. Claimed tasks recover after worker death.
4. Failed tasks preserve safe error details.
5. Approval decisions are audited.
6. Filesystem proposal application detects changed targets.
7. Memory writes fail safely without corrupting operational state.
8. Core flows have automated checks or repeatable smoke commands.

### Segment 10: Dashboard And Front Interface

Goal:

- build the dashboard as a supervisor view over stable OS APIs.

Important:

- the dashboard must not become a separate task, approval, or memory model.
- it should show the plan, agents, dependencies, approvals, progress, blockers,
  and final synthesis.
- the full visual avatar layer comes after the OS contract and memory loop are
  reliable.

Verification:

1. Dashboard reads from and writes to the OS API contract.
2. Dashboard can display pending approvals and concurrent sub-agent progress.
3. The same workflow remains executable through CLI/local API.

### Segment 11: Remote And Phone Layer

Goal:

- add cloud/phone access after the local Jarvis loop is stable.

Build order:

1. Simulated remote proxy.
2. Laptop heartbeat and honest online/offline wording.
3. Phone/PWA queue and status.
4. Completion pings.
5. Low-risk remote approvals.

Verification:

1. Remote surfaces can queue work even when the laptop is asleep.
2. Presence affects wording only, not whether tasks are queued.
3. Cloud/phone cannot directly execute high-risk local actions.

## Standing Rules For Every Segment

For every segment, explain:

1. what we are building in plain English;
2. why it matters to the Jarvis OS northstar;
3. what choices Brian needs to make;
4. what files or interfaces change;
5. how we verify it;
6. what risks or tradeoffs exist.

Do not move to later surface polish while the OS contract, memory loop,
approval model, and crash-recovery behavior are still unstable.
