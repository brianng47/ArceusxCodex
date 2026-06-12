# Memory Layer

## Purpose

Memory is what allows Arceus to improve over time.

It should preserve:

- user preferences;
- project context;
- decisions;
- plans;
- important outputs;
- lessons learned;
- agent behavior changes;
- recurring workflows;
- approval policies.

## Memory Targets

### Postgres

System-facing memory and ledger.

Stores:

- tasks;
- agent runs;
- approvals;
- lifecycle events;
- memory indexes;
- audit logs;
- routing decisions.

### Obsidian

Human-facing knowledge base.

Best for:

- personal notes;
- project context;
- long-running knowledge;
- linked thinking;
- decision records.

For the current build, Obsidian is the only long-term brain vault. Arceus uses
the iCloud Obsidian vault:

```text
/Users/brianng/Library/Mobile Documents/iCloud~md~obsidian/Documents
```

### Notion

Structured workspace and database-style knowledge.

Best for:

- dashboards;
- task views;
- structured project records;
- shared future workflows.

## Foundational Memory Documents

Create these early:

- Arceus Founding Charter.
- User Preferences.
- Project Map.
- Agent Registry.
- Decision Log.
- Approval Policies.
- Memory Update Rules.

## Reasoning Journal

For substantial requests, Arceus should maintain a reasoning journal or task
plan. This is not a place to dump raw hidden chain-of-thought. It is a concise,
user-safe record of:

- what the user asked;
- what Arceus decided to do;
- which agents were used;
- what assumptions were made;
- what was completed;
- what remains open.

## Memory Update Skill

The first memory skill should:

1. Decide whether a task produced durable knowledge.
2. Write a short memory entry.
3. Attach project, agent, and source metadata.
4. Update Obsidian.
5. Queue or prepare a Notion update.
6. Record the update in Postgres.

## Automatic Status Tracker

The status tracker is the first memory automation because it reduces repeated
context loading.

Arceus records compact status updates after:

- meaningful chat sessions;
- Codex handoff creation, start, completion, or failure;
- worker task completion or failure;
- future agent and workflow lifecycle events.

Each update is stored in Postgres and written to Obsidian when the vault is
available.

Generated Obsidian locations:

```text
Arceus/00_System/Status Tracker/
Arceus/00_System/Current State.md
```

Future agents should inspect this first:

```bash
./scripts/arceus status-summary
```

## Memory Hygiene

Do not save everything.

Save things that help future Arceus:

- make better decisions;
- avoid repeated setup;
- remember the user's preferences;
- preserve important project state;
- explain why something was built a certain way.

Avoid saving:

- transient chatter;
- secrets;
- raw credentials;
- sensitive details without explicit approval;
- large unprocessed dumps.

## Local Summary Command

Use this command to inspect what Arceus has remembered locally so far:

```bash
./scripts/arceus memory-summary
```

For machine-readable output:

```bash
./scripts/arceus memory-summary --json
```

The summary includes recent conversation sessions, Codex handoffs, and remote
task counts. It is intentionally small: this is a local memory pulse check, not
the full future memory system.
