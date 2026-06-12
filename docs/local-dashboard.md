# Local Dashboard

## Purpose

The local dashboard is the first visual front door for Arceus.

It wraps the current Codex manual bridge with:

- conversation panel;
- runtime status;
- animated Arceus-inspired core;
- recent Codex handoffs;
- supervised Codex autorun for stored handoffs;
- Local Control v0 for approved laptop actions without Terminal copy/paste;
- memory pulse;
- compact current-state status tracker;
- result recording form.

## Terminal-Free Launch

Install the double-click launcher:

```bash
cd /Users/brianng/Developer/Arceus
./scripts/install-mac-launcher
```

This creates:

```text
/Users/brianng/Developer/Arceus/Arceus Dashboard.app
```

After that, double-click **Arceus Dashboard.app** in the Arceus folder to start
the local dashboard and open it in the browser without keeping Terminal open.

The launcher writes runtime state to:

```text
/Users/brianng/Developer/Arceus/.arceus-state/runtime/dashboard.pid
/Users/brianng/Developer/Arceus/.arceus-state/logs/dashboard.log
/Users/brianng/Developer/Arceus/.arceus-state/logs/mac-launcher.log
```

Mac privacy note: the repo now lives at `~/Developer/Arceus` instead of
`Documents`. This avoids the broad Documents permission problem and gives future
login/startup services a cleaner path. Do not move it back under Documents
unless you are willing to handle macOS privacy prompts again.

Useful dashboard service commands:

```bash
./scripts/arceus dashboard status
./scripts/arceus dashboard start
./scripts/arceus dashboard open
```

## Manual Run

```bash
cd /Users/brianng/Developer/Arceus
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
5. Watch the memory pulse and daily brief update after the run records its
   result.

## Local Control

The dashboard includes a collapsed **Local Control** drawer.

This is the first step away from Terminal copy/paste. It exposes a fixed catalog
of allowed local actions:

- Check System;
- Check Codex;
- Read Current State;
- Check Dashboard;
- Check Path Access;
- Inspect Files;
- Open Dashboard;
- Initialize Database;
- Initialize Status Tracker;
- Install Mac Launcher;
- Run Latest Codex Handoff.

Read-only actions can run directly. State-changing actions require approval in
the dashboard before they run. Approval happens through an in-dashboard approval
card that shows the action, risk level, and expected output. Do not route this
through a generic browser confirmation popup.

Local Control is intentionally not an arbitrary shell. New actions should be
added to the catalog only after their risk level, expected output, and approval
rules are clear.

## Status Tracker

The dashboard reads the compact current-state tracker so future work does not
need to reload full chat history.

Useful command:

```bash
./scripts/arceus status-summary
```

To seed the tracker and create the Obsidian current-state files:

```bash
./scripts/arceus init-status-tracker
```

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

Current Codex versions no longer accept the older `--ask-for-approval` exec
flag. Arceus keeps approval at the dashboard layer and passes sandboxing to
Codex through `--sandbox`.

`ARCEUS_CODEX_SKIP_GIT_REPO_CHECK=false` keeps Codex's Git trust check active.
Only set it to `true` temporarily if you are testing in a folder that has not
been initialized as a Git repository.

## Design Notes

This is intentionally lightweight and dependency-free. It uses Python's local
HTTP server plus static HTML/CSS/JavaScript so Arceus gets a usable control
surface before we commit to a heavier frontend stack.

The UI follows `docs/ui-design-rules.md`: dark holographic command surface,
animated central avatar/core, readable cards, and practical controls.
