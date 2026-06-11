# Guardrails

## Core Principle

Arceus should become powerful through trust, not shortcuts.

Default behavior:

- propose before acting;
- ask before writes;
- log substantial decisions;
- expose errors honestly;
- keep sensitive details local unless requested.

## Risk Categories

### Low Risk

Examples:

- summarize public information;
- read approved project files;
- create plans;
- draft text;
- queue tasks.

Default:

- can usually run without approval.

### Medium Risk

Examples:

- modify project files;
- run local commands;
- update knowledge bases;
- create design assets;
- trigger downstream agent chains.

Default:

- approval required until promoted.

Current implementation:

- Codex autorun may run one stored handoff at a time when Brian explicitly
  clicks **Run with Codex** or runs `./scripts/arceus run-handoff <id>`.
- The default sandbox is `workspace-write`, scoped to the Arceus project.
- Unrestricted laptop-wide access is not enabled by default.

### High Risk

Examples:

- delete files;
- overwrite large folders;
- use credentials;
- send emails or messages;
- publish content;
- purchase anything;
- financial actions;
- irreversible operations.

Default:

- laptop-side approval required.
- cloud/phone may queue or propose, but not execute.

## Filesystem Guardrails

- Read access can be broad.
- Write access requires approval.
- Destructive operations require explicit high-risk approval.
- Show proposed changes before applying.
- Avoid secrets, credentials, SSH keys, browser profiles, and financial files
  unless explicitly authorized.

## Remote Surface Guardrails

The phone/PWA can:

- queue work;
- check status;
- receive summaries;
- approve tagged low-risk decisions;
- ask for full results.

The phone/PWA cannot directly:

- execute destructive filesystem actions;
- perform purchases or financial actions;
- use credentials;
- publish externally;
- run untagged powerful local actions.

## Failure Handling

Failures should be honest and lore-styled.

Default message:

> The forging fractured. No changes were applied.

Error details should be hidden behind "View details".

## Agent Chaining Guardrails

Agents may create downstream tasks, but the system must track:

- origin task;
- chain depth;
- agent that spawned the task;
- risk category;
- approval state.

Require approval when:

- chain depth exceeds the configured limit;
- a task crosses into high risk;
- a task would publish, spend, delete, or use credentials.

## Sleeping Laptop Guardrail

Queued work must survive laptop sleep.

When the laptop wakes:

- show pending tasks;
- ask whether expired or stale tasks should still run;
- continue valid tasks after confirmation where required.
