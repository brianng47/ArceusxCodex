# Decision Log

This file records important project decisions so future work does not repeat
the same debates.

## 2026-06-10: Project Northstar

Decision:

Arceus will be built as a local-first, cloud-ready personal AI command system.

Rationale:

The user wants a durable companion, business partner, second brain, and
specialist-agent army. The architecture needs to support local power and remote
access without making the cloud surface too dangerous.

## 2026-06-10: Main Architecture Layers

Decision:

Use three conceptual layers:

- Brain;
- Memory;
- Specialists.

Rationale:

This keeps orchestration, durable context, and task execution separate enough
to evolve over time.

## 2026-06-10: Local-First, Cloud-Ready

Decision:

Start locally, but use architecture that can later split into laptop and cloud
processes.

Rationale:

The project has no code yet. Local-first reduces startup complexity while
cloud-ready boundaries prevent a painful migration later.

## 2026-06-10: Recommended Stack

Decision:

- Python/FastAPI for Brain, workers, and agent orchestration.
- Next.js/React for mission-control UI.
- Postgres for durable ledger and queue.
- Obsidian and Notion for human-facing memory.
- Tauri later for desktop polish.

Rationale:

This combines strong AI workflow ergonomics, rich UI capability, and durable
storage.

## 2026-06-10: First Specialist

Decision:

Build the filesystem/code agent first.

Rationale:

It is concrete, useful, local-bound, and ideal for proving approval-first local
execution.

## 2026-06-10: Approval Defaults

Decision:

Any file write requires approval. High-risk actions require laptop-side
approval.

Rationale:

The system should become powerful without going rogue.

## 2026-06-10: Remote Surface

Decision:

Start with a phone-friendly PWA. Text-first, voice planned soon after.

Rationale:

A PWA is easier to test and keeps early experiments separate from personal
phone data.

## 2026-06-10: Dashboard Visual Direction

Decision:

Use a dark holographic mission-control dashboard inspired by the provided image,
adapted into a private fan-project Arceus interface that directly uses
Pokemon-owned Arceus visual and lore references for personal, non-commercial
use.

The dashboard should center on a living avatar/core, with jewel plates for
projects, tasks, agents, and memory. Cards should be animated, readable, and
state-driven.

Rationale:

The visual system should make Arceus feel present and powerful while preserving
practical control-center usability.

Guardrail:

Do not copy the provided command-center reference one-for-one. It is a mood and
composition reference.

Direct Arceus/Pokemon-owned visual references are permitted for the private fan
project. If the project becomes public or commercial, create a separate public
identity that replaces protected Pokemon-owned assets.

## 2026-06-10: Arceus Is the Operating Layer, Not the Base LLM

Decision:

Arceus may use Codex CLI, Claude Code, or future runtimes as reasoning and
execution engines, but Arceus itself is the durable operating layer around
those runtimes.

That layer includes persona, avatar, memory, knowledge base, skills,
approvals, specialists, local tools, cloud/laptop routing, and audit trails.

Rationale:

The user does not want a task sorter. The goal is a real-time companion and
all-encompassing personal OS that can converse, reason, remember, and execute.

Consequence:

The roadmap should not let queue plumbing dominate the product. Build presence
and conversation as a first-class track alongside durable execution.

## 2026-06-10: First Real Runtime Path

Decision:

Use Codex CLI as the first real runtime target and remove the OpenAI API-key
provider from the main path.

Rationale:

The user wants Arceus to wrap local agent runtimes like Codex/Claude Code, not
incur per-call API costs as a chatbot.

Implementation note:

The active fallback is `codex_manual`: Arceus generates a structured handoff
packet, the user runs it through Codex manually, and Arceus records the result.
`codex_app_server` remains the future direct bridge once the experimental
protocol is stable enough.

## 2026-06-11: Codex App-Server Feasibility Gate

Decision:

Add tooling to inspect Codex app-server protocol shape, but do not enable direct
Codex control yet.

Rationale:

Codex app-server exposes thread, turn, filesystem, command, remote-control, and
approval request surfaces. That is enough to explore direct integration, but it
is too powerful to route through Arceus before Arceus can display and enforce
approval gates.

Implementation note:

Use `./scripts/arceus app-server-doctor` to generate and inspect protocol
schemas. Keep `codex_manual` as the active runtime until a minimal JSON-RPC path,
approval UI, constrained execution profile, and lifecycle visibility are proven.

## 2026-06-11: Supervised Codex Autorun

Decision:

Allow Arceus to run one stored Codex handoff automatically through `codex exec`
and record the final result back into memory.

Rationale:

Manual copy/paste is useful for early proof, but it becomes friction quickly.
The next safe step is project-scoped autorun, not unrestricted machine-wide
control.

Implementation note:

`./scripts/arceus run-handoff <handoff-id>` and the dashboard **Run with Codex**
button use `workspace-write` sandboxing by default. Run artifacts are stored
under `outputs/codex-runs/<handoff-id>/`. Full laptop-wide access remains gated
behind future approval UI work.
