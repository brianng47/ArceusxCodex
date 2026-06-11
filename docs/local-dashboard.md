# Local Dashboard

## Purpose

The local dashboard is the first visual front door for Arceus.

It wraps the current Codex manual bridge with:

- conversation panel;
- runtime status;
- animated Arceus-inspired core;
- recent Codex handoffs;
- supervised Codex autorun for stored handoffs;
- memory pulse;
- result recording form.

## Run It

```bash
cd /Users/brianng/Documents/Arceus
./scripts/arceus setup-db
./scripts/arceus web
```

Open:

```text
http://127.0.0.1:8787
```

## First Flow

1. Ask Arceus for implementation work.
2. Review the generated Codex handoff packet.
3. Click **Run with Codex** to start a local Codex autorun, or copy the packet
   if you want to run it manually.
4. Wait for the handoff ledger to refresh.
5. Watch the memory pulse update after the run records its result.

## Autorun Guardrail

The dashboard autorun uses Codex non-interactive mode with project-scoped write
access:

```text
ARCEUS_CODEX_SANDBOX=workspace-write
ARCEUS_CODEX_APPROVAL_POLICY=never
ARCEUS_CODEX_SKIP_GIT_REPO_CHECK=false
```

This lets Codex edit the Arceus project without giving it unrestricted access to
the whole laptop. Full machine-wide access is intentionally not the default.
That step needs a stronger approval UI first.

`ARCEUS_CODEX_SKIP_GIT_REPO_CHECK=false` keeps Codex's Git trust check active.
Only set it to `true` temporarily if you are testing in a folder that has not
been initialized as a Git repository.

## Design Notes

This is intentionally lightweight and dependency-free. It uses Python's local
HTTP server plus static HTML/CSS/JavaScript so Arceus gets a usable control
surface before we commit to a heavier frontend stack.

The UI follows `docs/ui-design-rules.md`: dark holographic command surface,
animated central avatar/core, readable cards, and practical controls.
