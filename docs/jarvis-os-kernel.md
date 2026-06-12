# Jarvis OS Kernel

This document describes the first implemented slice of the Jarvis OS roadmap.

The goal is to make Arceus operate from a stable contract before adding runtime
brokering, bounded swarms, voice, or dashboard supervisor UI.

## Implemented Slice

### Root Vault Memory

The Obsidian vault root is now the primary LLM-wiki memory layer.

Commands:

```bash
./scripts/arceus vault init
./scripts/arceus vault context
./scripts/arceus vault audit
./scripts/arceus vault write-page <path> --title "<title>" --body "<body>"
```

Behavior:

- ensures root `CLAUDE.md`, `AGENTS.md`, `raw/`, and `wiki/` exist;
- reads `CLAUDE.md`, `wiki/index.md`, `wiki/hot.md`, and generated Current
  State;
- writes pages under `wiki/`;
- updates `wiki/index.md`;
- appends to `wiki/log.md`;
- refreshes `wiki/hot.md`;
- runs audit-only self-heal.

### Jarvis OS Plan

Command:

```bash
./scripts/arceus os-plan "<request>" --project <project> --save
```

Behavior:

- extracts the problem statement;
- reads root vault context;
- states assumptions;
- asks material clarifying questions;
- builds a holistic approval gate;
- drafts agent run assignments;
- identifies memory writeback requirements;
- optionally saves the plan under `wiki/analyses/`.

## Current Contract Shape

A Jarvis OS plan contains:

- plan id;
- user request;
- problem statement;
- assumptions;
- clarifying questions;
- context pages;
- approval gates;
- agent runs;
- expected outputs;
- memory writeback;
- next action.

## Next Implementation

The next code slice should turn the plan into an executable workflow record:

1. Persist plans in Postgres.
2. Add approval packet status.
3. Add workflow run status.
4. Connect approved plans to task queue entries.
5. Add bounded concurrent specialist execution.
