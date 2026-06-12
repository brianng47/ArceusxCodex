# Dashboard Roadmap And Status Tracker

## Purpose

This document now defines the dashboard as a later supervisor surface over the
Jarvis OS core. It is not the primary roadmap.

The active product priority is:

1. personal memory;
2. clarification and planning;
3. holistic approvals;
4. runtime brokering;
5. bounded concurrent specialists;
6. reliable local execution;
7. push-to-talk voice;
8. dashboard/front interface.

The dashboard should never become a parallel state model. It must consume the
same OS contracts used by CLI, local API, workers, and future remote surfaces.

## Status Tracker First

The automatic status tracker remains the first handoff surface for future
agents. It reduces token waste by giving future runs a compact current-state
record before they inspect long chats, handoff logs, or scattered docs.

Each status update stores:

- date and time;
- actor and runtime;
- workstream;
- current status;
- summary;
- decisions;
- files changed;
- blockers;
- next actions;
- memory-worthy notes;
- linked project, task, or agent;
- source type and source id.

Postgres is the operational ledger. Obsidian is the personal knowledge and
memory layer.

Configured Obsidian vault:

```text
/Users/brianng/Library/Mobile Documents/iCloud~md~obsidian/Documents
```

Generated status notes:

```text
Arceus/00_System/Status Tracker/
Arceus/00_System/Current State.md
```

Before starting substantial work, future agents should read:

```bash
./scripts/arceus status-summary
```

## Dashboard Role

The dashboard should become a supervisor view for:

- current problem statement;
- clarification state;
- holistic approval packet;
- running workflow plan;
- concurrent sub-agent progress;
- runtime choices and why they were made;
- dependencies and blockers;
- safe failure details;
- final synthesis;
- memory writes and Obsidian links.

It should not be the only way to operate Arceus. The same flows must remain
available through CLI/local API so the OS can be tested and recovered without a
browser.

## Current v0 Implementation

Already implemented:

- local dashboard at `http://127.0.0.1:8787`;
- terminal-free macOS launcher;
- conversation panel;
- runtime status;
- handoff list and Codex autorun button;
- Local Control drawer with fixed allowed actions;
- dashboard-native approval card for state-changing Local Control actions;
- status tracker panel;
- read-only zone APIs under `/api/zones/<zone>`;
- seed projects for `riprocket_tcg Instagram Growth` and
  `UGC Influencer Content Creation`;
- seed agent roster for Arceus, Memory Scribe, Filesystem/Code Agent, Research
  Agent, UI/UX Agent, TCG Growth Strategist, and UGC Creative Director.

These pieces are useful, but they are not the finished OS.

## Workstreams In The New Order

### 1. OS API Consumer

Dashboard controls should call stable OS endpoints for intent, plans,
approvals, agent runs, memory links, and status. Avoid dashboard-only business
logic.

### 2. Supervisor View

Show the workflow plan before execution:

- problem statement;
- assumptions;
- clarifying questions;
- dependencies;
- agent assignments;
- runtime choices;
- risk levels;
- approval gates.

### 3. Approval Center

Show holistic approval bundles first. Step-level approvals remain available for
writes, destructive operations, publishing, credentials, purchases, financial
actions, and irreversible actions.

### 4. Agent Swarm Progress

Show bounded concurrent specialists as a supervised swarm:

- queued;
- running;
- blocked;
- failed;
- completed;
- synthesized.

### 5. Memory Visibility

Show which Obsidian pages are read or written:

- `wiki/index.md`;
- `wiki/log.md`;
- `wiki/hot.md`;
- project pages;
- preference pages;
- workflow pages;
- audit pages.

### 6. Voice And Avatar

Voice and avatar should reflect the OS state rather than decorate an unstable
workflow. First target is push-to-talk voice with transcript fallback and a
stateful 2D/avatar core. Spline or richer 3D can come after the OS loop is
stable.

## Cost Guardrail

Lean local prototype: roughly `$0-$15/month`.

Useful voice plus lightweight avatar prototype: roughly `$25-$60/month`.

Creative-heavy 3D/video month: roughly `$60-$150/month`, depending on
Meshy/Higgsfield usage.

Cloud/PWA always-on later: add roughly `$0-$40/month` at early scale.

Heavy production/business workflow: `$150+/month`.
