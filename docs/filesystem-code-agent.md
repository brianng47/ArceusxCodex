# Filesystem/Code Agent

The Filesystem/Code Agent is the first laptop-bound specialist.

Its job is to inspect allowed project files, explain structure, draft file
change proposals, and apply approved proposals. It is not an arbitrary shell.

## Access Boundary

All file access goes through `src/arceus/path_policy.py`.

Default read roots:

- `/Users/brianng/Developer/Arceus`
- Obsidian vault
- `/Users/brianng/Developer/Arceus/.arceus-state`
- read-only `~/.codex`

Default write roots:

- `/Users/brianng/Developer/Arceus`
- Obsidian vault
- `/Users/brianng/Developer/Arceus/.arceus-state`

Documents-wide access is denied by default.

## V0 Capabilities

- Inspect an allowed folder without changing anything.
- Read an allowed text file with size limits.
- Draft a full-file replacement proposal.
- Apply a proposal only with explicit approval.
- Store proposals under `.arceus-state/filesystem-agent/proposals/`.

V0 intentionally does not support arbitrary shell commands or patch hunks. Full
file replacement is blunt, but auditable. Patch-level editing can come after the
dashboard has a proper proposal review screen.

## Commands

Inspect the repo:

```bash
./scripts/arceus fs-inspect . --max-depth 2
```

Read a file:

```bash
./scripts/arceus fs-read README.md
```

Draft a proposal:

```bash
./scripts/arceus fs-draft tmp/example.txt \
  --intent "Create a tiny verification file." \
  --content "hello"
```

Apply a proposal:

```bash
./scripts/arceus fs-apply-proposal <proposal-id> \
  --confirm apply_filesystem_proposal
```

## Dashboard Exposure

The dashboard Local Control catalog exposes **Inspect Files** as a safe read-only
action. Drafting and applying proposals remain CLI-backed until the dashboard
has a dedicated proposal review surface that shows target path, diff, risk, and
approval token clearly.

## Approval Rule

Every target file write must come from an approved proposal. If the target file
changed after the proposal was drafted, apply fails and the agent must reinspect
before drafting again.
