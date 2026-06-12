# Agent System

## Agent Philosophy

Agents are not random scripts. Each specialist should have:

- a clear purpose;
- explicit permissions;
- known inputs and outputs;
- a risk profile;
- an approval policy;
- memory logging rules.

The Brain remains responsible for orchestration and reasoning. Specialists do
focused work.

The user should not need to manually decide that a new agent is required. The
normal interaction should be outcome-first: Brian asks for a result, Arceus
checks its component catalog, uses what exists, and drafts any missing skill,
tool adapter, agent, or workflow only when the task exposes a real capability
gap.

For the TCG business target ecosystem, see
[TCG Business Agent Ecosystem](tcg-business-agent-ecosystem.md).

## Agent Classes

### Brain Agent: Arceus

Purpose:

- interpret requests;
- maintain reasoning journal and task plans;
- route tasks;
- decide when to ask for approval;
- create or summon specialists;
- update memory.

Risk profile:

- high influence, but should not directly execute high-risk operations without
  approval.

### Filesystem/Code Specialist

Purpose:

- inspect files and projects;
- explain code;
- propose edits;
- apply approved file changes;
- run approved local checks.

Execution location:

- laptop-first.

Why laptop-bound:

- local filesystem;
- local development tools;
- possible private files;
- write operations.

Approval policy:

- read allowed where configured;
- every write requires approval;
- destructive actions require explicit high-risk approval.

Path boundary:

- all filesystem access must pass through the Arceus path policy;
- default read roots are the Arceus repo, Obsidian vault, repo-local
  `.arceus-state`, and read-only `~/.codex`;
- default write roots are the Arceus repo, Obsidian vault, and repo-local
  `.arceus-state`;
- Documents-wide access is intentionally not part of the default policy;
- add external project folders explicitly through `ARCEUS_EXTRA_READ_PATHS` and
  `ARCEUS_EXTRA_WRITE_PATHS` only after the project needs them.

### Research Specialist

Purpose:

- gather information;
- summarize sources;
- distinguish fact from inference;
- save durable research notes.

Execution location:

- hybrid.

Approval policy:

- low-risk research can run remotely;
- private memory retrieval should follow remote-surface disclosure rules.

### UI/UX Specialist

Purpose:

- design Arceus flows and screens;
- create mockups and visual concepts;
- recommend interaction patterns;
- eventually integrate with creative tools.

Execution location:

- hybrid.

Potential integrations:

- Higgsfield;
- Remotion;
- Seedance;
- image generation systems;
- design tools.

Approval policy:

- may propose freely;
- may create mockups after approval;
- may not publish or modify production surfaces without approval.

## Agent Chaining

Agents may create downstream tasks. This is required for workflows like:

- marketing strategy -> image generation -> copywriting -> ad variants;
- product plan -> UI mockups -> implementation tasks -> QA;
- research -> synthesis -> memory update -> action plan.

Guardrails:

- track origin task;
- track chain depth;
- require approval when crossing into high-risk categories;
- prevent unbounded cascades;
- preserve an audit trail.

## Tool Registration Rule

Laptop:

- real local tools;
- real local agents.

Cloud:

- safe tools;
- proxy tools only when real tools are absent.

Never register both the real powerful tool and its proxy in the same process.

## First Agent Slice

Build the filesystem/code specialist first.

Initial capability:

1. Read a selected folder.
2. Summarize its structure.
3. Propose a file change.
4. Ask for approval.
5. Apply the approved change.
6. Log the action to memory.
