# Codex App-Server Feasibility

## Purpose

This track investigates whether Arceus can talk to Codex directly through the
local Codex app-server instead of relying only on manual handoff packets.

The goal is not to give Arceus full laptop control immediately. The goal is to
prove the bridge shape, then wrap it with approvals, memory, and UI state before
it becomes an active runtime.

## Current Recommendation

Keep this setting active:

```text
ARCEUS_RUNTIME_MODE=codex_manual
```

`codex_manual` remains the safe default because Brian stays in the loop:

1. Arceus creates the Codex handoff.
2. Brian runs or pastes it into Codex.
3. Brian records the result back into Arceus.
4. Arceus preserves the outcome in memory.

Direct app-server mode is feasible to explore, but it is not approved as the
main runtime until the gates below are met.

## Doctor Command

Run:

```bash
./scripts/arceus app-server-doctor
```

This command:

- checks the configured Codex binary;
- asks Codex for app-server daemon status;
- generates local app-server protocol schemas into a temporary folder;
- counts client/server methods exposed by the protocol;
- highlights approval requests and high-power methods;
- explains whether direct mode should remain disabled.

For raw machine-readable output:

```bash
./scripts/arceus app-server-doctor --json
```

To save generated schemas somewhere specific:

```bash
./scripts/arceus app-server-doctor --schema-dir /tmp/arceus-codex-schema
```

## What The Schema Shows

The protocol exposes enough pieces to attempt a direct bridge:

- thread start and resume;
- turn start and steering;
- filesystem and process operations;
- dynamic tool calls;
- approval requests from Codex back to the client;
- realtime and remote-control related surfaces.

That is powerful, which is exactly why it cannot be wired in casually.

## Required Gates Before Direct Mode

Direct `codex_app_server` mode must stay disabled until all gates pass:

1. A minimal JSON-RPC request/response path through the app-server proxy is
   proven on this laptop.
2. Arceus can receive and display every approval request from Codex.
3. Arceus can block writes, commands, credentials, publishing, financial
   actions, and irreversible operations until Brian approves.
4. Direct runs can start in a constrained profile first, preferably read-only or
   sandboxed.
5. The dashboard can show direct-run lifecycle states, not just final results.
6. `codex_manual` remains available as the fallback when app-server behavior
   changes.

## Safety Doctrine

The app-server is not the brain. It is a power adapter.

Arceus remains responsible for:

- persona and conversation;
- routing judgment;
- memory capture;
- approval discipline;
- explaining what is happening;
- choosing when a task should stay manual.

Codex remains responsible for:

- implementation reasoning;
- repository edits when approved;
- test execution when approved;
- tool-driven local work.

## Decision

Until the gates pass, Arceus should say:

```text
Direct Codex control is not active yet. I can prepare a supervised Codex handoff.
```

This is less flashy than claiming full autonomy, but it keeps the system honest.
Small inconvenience, large reduction in chaos. A reasonable trade.
