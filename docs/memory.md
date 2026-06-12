# Memory Layer

## Purpose

Memory is what lets Arceus become Brian's Jarvis instead of another vanilla
LLM front end.

It should preserve:

- user preferences;
- project context;
- decisions;
- plans;
- important outputs;
- lessons learned;
- agent behavior changes;
- recurring workflows;
- approval policies;
- personal operating context that prevents repeated clarification.

## Memory Split

### Postgres

Postgres is the operational ledger.

It stores:

- tasks;
- agent runs;
- approvals;
- lifecycle events;
- memory indexes;
- audit logs;
- routing decisions;
- crash-recovery state.

Postgres answers "what is happening, what happened, and what can safely run?"

### Obsidian

Obsidian is the personal knowledge and second-brain layer.

It stores:

- personal notes;
- project context;
- long-running knowledge;
- linked thinking;
- decision records;
- reusable workflow context;
- human-readable memories that Arceus should use later.

For the current build, Arceus uses the iCloud Obsidian vault:

```text
/Users/brianng/Library/Mobile Documents/iCloud~md~obsidian/Documents
```

Obsidian answers "what does Arceus know about Brian, his projects, and the
world he is operating in?"

## LLM-Wiki Pattern

Arceus adopts the LLM-wiki pattern described by:

```text
https://github.com/NulightJens/ai-second-brain-skills
```

The important idea is that the folder becomes the app. Arceus compiles raw
inputs into a maintained wiki instead of repeatedly re-reading scattered raw
sources or relying only on vector retrieval.

Initial vault-level memory structure:

```text
<Obsidian vault>/
  AGENTS.md
  CLAUDE.md
  raw/
  wiki/
    index.md
    log.md
    hot.md
    audits/
    people/
    projects/
    preferences/
    workflows/
    sources/
    analyses/
    system/
  Arceus/
    00_System/
```

Rules:

- read the map file before memory work;
- read `wiki/index.md` before answering memory-backed questions;
- write every durable operation to `wiki/log.md`;
- keep `wiki/hot.md` as a compact rolling cache for current user context,
  active projects, recent decisions, and voice-speed lookup;
- use `[[wikilinks]]` for internal navigation;
- keep frontmatter on wiki pages;
- preserve source metadata;
- never fabricate citations;
- never silently resolve contradictions;
- never modify `raw/` sources;
- use audits to find stale claims, contradictions, orphan pages, missing pages,
  missing cross-references, and data gaps.

The existing `Arceus/00_System/` folder is retained as the generated status
tracker area because current Arceus code writes Current State and Status
Tracker notes there. Do not move it until the status tracker path is migrated.

## Whole-Vault Policy

Brian chose whole-vault memory with free wiki edits.

Practical interpretation:

- Arceus may read the whole Obsidian vault for context within the configured
  path policy.
- Arceus may autonomously maintain wiki-style memory pages, indexes, logs, hot
  cache, and audits.
- `raw/` is immutable source material. Arceus reads it but does not modify it.
- Existing personal notes outside the Arceus wiki should be treated as context
  or source material unless a workflow explicitly promotes them into
  Arceus-maintained wiki pages.
- The root-level `wiki/` folder is the primary LLM-wiki memory layer.
- The nested `Arceus/wiki/` folder is a legacy/subproject scaffold and should
  not be treated as the vault-wide source of truth.
- Destructive edits still require explicit approval.

This keeps the vault flexible without letting memory lose provenance.

## Memory Workflows

### Clarify And Remember

When Brian gives a vague or high-impact request:

1. Extract the key problem statement.
2. Read relevant memory.
3. Draft assumptions.
4. Ask only questions that materially change the workflow.
5. Save useful answers into the appropriate wiki pages.
6. Update `wiki/index.md`, `wiki/log.md`, and `wiki/hot.md`.

### Query

When answering from memory:

1. Read the map file.
2. Read `wiki/index.md`.
3. Select relevant pages.
4. Follow `[[wikilinks]]` only as needed.
5. Answer with clear source references to wiki pages.
6. Offer to file novel synthesis back into the wiki when useful.

### Ingest

When new source material is added:

1. Read the source completely.
2. Identify affected entities, concepts, projects, preferences, workflows, or
   analyses.
3. Update existing pages where possible.
4. Create new pages only when justified.
5. Add bidirectional `[[wikilinks]]`.
6. Update the index.
7. Append exactly one log entry.

### Self-Heal

Memory self-heal should start in audit-only mode on the first run.

The audit scans for:

- contradictions;
- stale claims;
- orphan pages;
- missing pages;
- missing cross-references;
- data gaps.

Full self-heal runs should use quality-gated research and leave changes
reviewable. It is better to skip a weak source than poison the wiki.

## Reasoning Journal

For substantial requests, Arceus should preserve a user-safe reasoning journal
or task plan. It must not dump raw hidden chain-of-thought.

Record:

- what Brian asked;
- the key problem statement;
- assumptions;
- clarifying questions and answers;
- which agents or runtimes were used;
- approvals granted or denied;
- what was completed;
- what remains open;
- what should be remembered.

## Automatic Status Tracker

The status tracker remains the compact handoff layer for future agents.

Arceus records status updates after:

- meaningful chat sessions;
- roadmap decisions;
- Codex handoff creation, start, completion, or failure;
- worker task completion or failure;
- local action runs;
- future agent and workflow lifecycle events.

Each update is stored in Postgres and written to Obsidian when the vault is
available.

Generated status locations:

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
- remember Brian's preferences;
- preserve important project state;
- explain why something was built a certain way;
- improve recurring workflows.

Avoid saving:

- transient chatter;
- secrets;
- raw credentials;
- sensitive details without explicit approval;
- large unprocessed dumps;
- unsourced factual claims presented as certain.

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
