# Architecture

## Strategy

Build local-first, cloud-ready.

This means Arceus starts on the laptop for speed and safety, but uses boundaries
that allow the system to split into laptop and cloud processes later.

## Main Layers

### Agent Runtimes

Agent runtimes are the underlying reasoning and execution engines.

Examples:

- Codex CLI;
- Claude Code;
- future local or cloud models.

They provide language, reasoning, file edits, command execution, and tool-use
capability. They are not the whole product.

Arceus should be runtime-aware but not runtime-trapped. The system should be
able to route requests to different runtimes over time without rewriting
memory, approvals, UI, or specialist orchestration.

### Brain and Presence

The Brain and Presence layer is Arceus itself: conversational persona,
first-pass processor, planner, reasoning journal, orchestrator, and router.

Responsibilities:

- converse with the user in real time;
- maintain avatar state such as idle, listening, thinking, speaking, waiting,
  and executing;
- understand the user's intent;
- decide whether a task is safe, risky, local-only, cloud-safe, or hybrid;
- maintain a task plan for substantial work;
- delegate to specialists;
- ask for approval when required;
- preserve important context in memory.

The queue and worker system must serve this layer. They should not define the
user experience by themselves.

### Memory

Memory has two parts:

- System ledger: structured records for tasks, runs, approvals, statuses,
  events, and memory indexes.
- Human knowledge base: Obsidian and Notion pages that the user can read,
  edit, and grow over time.

Recommended system ledger: Postgres.

### Specialists

Specialists are focused agents. Each has a narrow purpose, clear permissions,
and a known risk profile.

All specialists are hybrid by default:

- cloud can plan, queue, retrieve, or run low-risk work;
- laptop executes powerful, sensitive, or local-only work.

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

The queue is the contract between machines, not the soul of Arceus.

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

## UI Architecture Direction

The UI should be built as a real operating surface, not a static landing page.

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
