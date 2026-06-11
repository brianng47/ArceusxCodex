# Skills and Integrations

## Purpose

Skills are reusable capabilities that Arceus and specialists can call. Some
will be built in this project. Others may come from MCP servers, local tools,
or external creative systems.

## Skill Categories

### Memory Skills

Purpose:

- save important decisions;
- update project context;
- summarize completed tasks;
- avoid repeating discovery work;
- keep Obsidian and Notion coherent.

Initial skill to build:

- `update_memory`

Expected behavior:

1. Detect what should be preserved.
2. Write a concise structured memory entry.
3. Link it to a project, task, or decision.
4. Sync or prepare sync to Obsidian and Notion.

### Filesystem Skills

Purpose:

- list files;
- inspect content;
- propose changes;
- apply approved changes.

Initial safety rule:

- ask before any write.

### Research Skills

Purpose:

- search;
- read;
- summarize;
- cite sources;
- save useful findings to memory.

Rule:

- distinguish sourced facts from Arceus' inference.

### UI/UX Skills

Purpose:

- create flows, screens, and mockups;
- inspect screenshots;
- propose design changes;
- generate visual assets when appropriate.

Potential integrations:

- image generation;
- Higgsfield;
- Remotion;
- Seedance;
- Canva or other design surfaces;
- browser-based UI verification.

Rules:

- leverage existing high-quality creative tools when available instead of
  hand-building every asset;
- use generated assets for atmosphere, avatar studies, and motion references;
- keep core dashboard controls as maintainable UI components;
- do not rely on external asset tools for critical app behavior;
- avoid direct copies of protected character art or reference imagery.

### Voice and Avatar Skills

Purpose:

- speech input;
- speech output;
- avatar animation;
- emotional state display;
- interaction-aware movement.

Initial priority:

- plan for voice soon after text is stable.

## Skill Quality Bar

Every skill should define:

- what it does;
- where it can run;
- what permissions it requires;
- what approval gates it needs;
- what it logs to memory;
- what failure looks like.

## First Skills to Implement

1. Queue task.
2. Claim task.
3. Update lifecycle status.
4. Ask for approval.
5. Update memory.
6. Inspect filesystem.
7. Propose file edit.
8. Apply approved file edit.
