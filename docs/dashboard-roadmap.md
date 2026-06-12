# Dashboard Roadmap And Status Tracker

## Purpose

The dashboard roadmap defines the remaining build work for Arceus as a
full-fledged local-first operating surface.

The first priority is the automatic status tracker. It reduces token waste by
giving future agents a compact current-state record to read before they inspect
long chats, handoff logs, or scattered docs.

## Status Tracker First

Arceus records compact status updates after meaningful sessions and lifecycle
events.

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

Postgres is the operational ledger. Obsidian is the canonical long-term memory.

Configured Obsidian vault:

```text
/Users/brianng/Library/Mobile Documents/iCloud~md~obsidian/Documents
```

Generated Obsidian notes:

```text
Arceus/00_System/Status Tracker/
Arceus/00_System/Current State.md
```

Before starting substantial work, future agents should read:

```bash
./scripts/arceus status-summary
```

## Workstreams

### 1. Data Backbone

Build durable records and APIs for:

- chats;
- tags;
- agents;
- projects;
- workflows;
- approvals;
- memory links;
- status updates.

Current v0 implementation:

- Postgres tables exist for projects, agents, dashboard tasks, workflows, tags,
  memory links, and chat tags.
- Seed data creates the first two project folders:
  `riprocket_tcg Instagram Growth` and
  `UGC Influencer Content Creation`.
- Seed data creates the first agent roster: Arceus, Memory Scribe,
  Filesystem/Code Agent, Research Agent, UI/UX Agent, TCG Growth Strategist,
  and UGC Creative Director.
- The dashboard exposes read-only zone APIs under `/api/zones/<zone>`.
- Editing, double-click project drill-down, and workflow promotion remain future
  work.

### 2. Dashboard Zones

Make the sidebar zones real views:

- Chats: date organization, keyword search, tags to tasks and projects.
- Agents: team-member cards with Pokemon-lore-inspired identities.
- Tasks: scheduled, queued, running, completed, failed, and awaiting approval.
- Workflows: visual read-only graph first, editable later.
- Projects: start with `riprocket_tcg Instagram Growth` and
  `UGC Influencer Content Creation`.

### 3. Obsidian Memory

Obsidian is the only long-term brain vault for now.

Arceus should write linked Markdown for:

- decisions;
- projects;
- task results;
- agent behavior;
- user preferences;
- daily brief sources.

### 4. Tasks And Approvals

Low-risk batches can use grouped approval.

High-risk actions always need explicit approval:

- destructive changes;
- credential access;
- financial actions;
- publishing;
- irreversible actions.

Automation without approval is only allowed after a workflow is defined, tested,
and promoted.

### 5. Agents

Agents should feel like team members, not generic tools.

Initial roster:

- Arceus: orchestrator;
- Memory Scribe;
- Filesystem/Code Agent;
- Research Agent;
- UI/UX Agent;
- TCG Growth Strategist;
- UGC Creative Director.

### 6. Voice And Avatar

Voice should prioritize fast conversational response using ElevenLabs.

The avatar path starts with Spline for interactive 3D. Meshy can supply assets
later. Higgsfield is for cinematic references and video studies, not a core
dashboard dependency.

## Cost Guardrail

Lean local prototype: roughly `$0-$15/month`.

Useful voice plus Spline prototype: roughly `$25-$60/month`.

Creative-heavy 3D/video month: roughly `$60-$150/month`, depending on
Meshy/Higgsfield usage.

Cloud/PWA always-on later: add roughly `$0-$40/month` at early scale.

Heavy production/business workflow: `$150+/month`.
