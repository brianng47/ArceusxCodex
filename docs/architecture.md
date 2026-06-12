# Architecture

## Strategy

Build local-first, cloud-ready.

This means Arceus starts on the laptop for speed and safety, but uses boundaries
that allow the system to split into laptop and cloud processes later.

As of 2026-06-12, the active architecture priority is Jarvis OS-first. Arceus
must become the personal operating layer above Codex, Claude Code, Claude
Cowork, Grok, and future engines. The dashboard is a later client of the OS,
not the center of the architecture.

The default workflow is:

1. understand the user's request;
2. extract the key problem statement;
3. read relevant personal memory;
4. ask only context-changing clarifying questions;
5. propose a workflow plan with dependencies, runtimes, specialists, risks,
   and approval gates;
6. request holistic approval;
7. execute approved low-risk work and pause on required gates;
8. synthesize the result;
9. write useful memory back to Obsidian and the operational ledger.

## Main Layers

### Agent Runtimes

Agent runtimes are the underlying reasoning and execution engines.

Examples:

- Codex CLI;
- Claude Code;
- Claude Cowork;
- Grok;
- future local or cloud models.

They provide language, reasoning, file edits, command execution, and tool-use
capability. They are not the whole product.

Arceus should be runtime-aware but not runtime-trapped. The system should be
able to route requests to different runtimes over time without rewriting
memory, approvals, UI, or specialist orchestration.

The runtime broker records:

- selected runtime;
- reason for selection;
- input handoff;
- output summary;
- failure state;
- quality notes;
- memory-worthy result.

### Brain and Presence

The Brain and Presence layer is Arceus itself: conversational persona,
first-pass processor, planner, reasoning journal, orchestrator, and router.

Responsibilities:

- converse with the user in real time;
- maintain avatar state such as idle, listening, thinking, speaking, waiting,
  and executing;
- understand the user's intent;
- infer from personal memory before asking repeat questions;
- ask clarifying questions when missing context changes the plan;
- decide whether a task is safe, risky, local-only, cloud-safe, or hybrid;
- maintain a task plan for substantial work;
- delegate to bounded concurrent specialists;
- ask for holistic approval before running a workflow;
- preserve important context in memory.

The queue and worker system must serve this layer. They should not define the
user experience by themselves.

### Memory

Memory has two parts:

- System ledger: structured records for tasks, runs, approvals, statuses,
  events, and memory indexes.
- Personal knowledge base: Obsidian pages that the user and Arceus can read,
  edit, and grow over time.

Recommended system ledger: Postgres.

Obsidian uses an LLM-wiki pattern:

- a map file that agents read first;
- immutable `raw/` sources;
- LLM-maintained `wiki/` pages;
- `wiki/index.md` as the routing table;
- `wiki/log.md` as the operation timeline;
- `wiki/hot.md` as a rolling fast-context cache;
- `wiki/audits/` for self-heal reports.

Postgres remains the source of truth for operational state. Obsidian is the
source of truth for human-readable personal memory and knowledge.

### Specialists

Specialists are focused agents. Each has a narrow purpose, clear permissions,
and a known risk profile.

All specialists are hybrid by default:

- cloud can plan, queue, retrieve, or run low-risk work;
- laptop executes powerful, sensitive, or local-only work.

Specialists may run concurrently only through a bounded workflow swarm. The
first limit is 2-4 concurrent tasks with dependency tracking, cancellation,
failure isolation, and one final synthesis by Arceus.

## Process Roles

### Laptop Process

Trusted local control center.

Registers:

- real local tools;
- powerful local agents;
- laptop worker;
- local UI events;
- approval UI;
- local memory sync.

### Cloud Process

Limited remote access layer.

Registers:

- safe tools;
- proxy tools for laptop-only agents;
- phone/PWA messaging;
- result notification handlers.

The cloud process must not directly execute powerful local actions.

## Durable Queue

The queue is the durable execution layer, not the soul of Arceus.

Each routed task is stored as a durable row. Push notifications are an
optimization. The worker must always drain pending work on startup so tasks
created while the laptop was asleep are not lost.

Recommended task table:

```text
remote_tasks
------------
id
owner_id
worker_role
kind
payload
status
result
error_message
claimed_by
origin_task_id
chain_depth
expires_at
created_at
claimed_at
completed_at
```

Future task payloads should align with the Jarvis OS contract: problem
statement, context references, agent role, runtime hint, approval state,
dependencies, expected artifacts, and memory writeback rules.

## Internal Statuses and UI Labels

Keep internal statuses simple and reliable. Let the UI display Arceus-themed
labels.

| Internal Status | UI Label |
| --- | --- |
| queued | Destined |
| claimed | Summoned |
| planning | Reading the Threads |
| awaiting_approval | Awaiting Your Blessing |
| executing | Forging |
| saving_memory | Inscribing the Codex |
| completed | Manifested |
| failed | Fractured |
| cancelled | Sealed Away |
| expired | Faded |

## Cross-Machine Routing

For laptop-only agents:

1. The cloud exposes a proxy tool with the same name and input shape as the
   real local tool.
2. The proxy enqueues a durable task.
3. The laptop worker claims the task.
4. The laptop runs the real local agent to completion.
5. The task result is stored.
6. The cloud sends a completion ping to the remote surface.

## No-Double-Execution Rule

The laptop registers the real powerful tool.

The cloud registers the proxy only if the real tool is absent.

This prevents one request from running both locally and remotely.

## Recommended Stack

- Brain and workers: Python/FastAPI.
- UI: Next.js/React.
- Ledger: Postgres.
- Local knowledge base: Obsidian.
- Structured shared knowledge base: Notion.
- Desktop shell later: Tauri.
- Voice: push-to-talk first, with low-latency transcription, TTS, and text
  fallback before always-listening modes.

## UI Architecture Direction

The UI should be built as a real operating surface, not a static landing page.

The UI comes after the OS contracts are reliable. It is a supervisor interface
over Arceus, not a replacement for the OS kernel.

Recommended approach:

- Next.js/React for the dashboard.
- Component library only where it accelerates reliable controls.
- Motion library for panel and status animation.
- Canvas/WebGL or generated video only for the avatar/background layer when it
  adds meaningful atmosphere.
- Asset-generation tools may be used for background plates, avatar studies, or
  animation references, but the application should still be assembled from
  maintainable UI components.

The dashboard should have three layers:

1. Ambient layer: cosmic/holographic background and subtle data flow.
2. Avatar layer: central Arceus-inspired core, jewel plates, and voice state.
3. Work layer: readable cards, queues, approvals, agent states, and memory.

## Push and Polling

Use both:

- instant wake signals when possible;
- backup polling for reliability.

Presence should affect wording only. It must never decide whether work is
queued.
