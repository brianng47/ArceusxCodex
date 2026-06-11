# Codex Runtime Bridge

## What This Adds

Arceus is now aimed at local agent runtimes, not paid API-key chat providers.

The first runtime target is Codex CLI.

Discovered local binary:

```text
/Applications/Codex.app/Contents/Resources/codex
```

## Runtime Modes

### `offline`

Local placeholder conversation. Useful for testing the shell.

### `codex_manual`

The active supervised bridge.

Arceus:

1. listens to your request;
2. decides whether it is Codex-worthy;
3. creates a structured Codex handoff packet;
4. stores the packet in Postgres;
5. gives you the packet to run in Codex manually;
6. records the pasted result afterward.

This avoids API-key billing while keeping Arceus as the front door.

The local dashboard can now run a stored handoff through Codex automatically via
the **Run with Codex** button. This uses `codex exec`, writes run artifacts to
`outputs/codex-runs/<handoff-id>/`, and records the final Codex message back
into Arceus memory.

The autorun still belongs to the `codex_manual` lane because Arceus is launching
one explicit handoff at a time. It is not yet a free-running app-server bridge.

### `codex_app_server`

Reserved for future direct integration with Codex app-server/MCP-style control.

Codex exposes experimental app-server and MCP-server surfaces. Arceus should
not depend on them until a stable request/response path is proven.

Use the feasibility track before enabling this mode:

```bash
./scripts/arceus app-server-doctor
```

See [Codex App-Server Feasibility](codex-app-server-feasibility.md).

## Local Setup

In `.env`, use:

```text
ARCEUS_RUNTIME_MODE=codex_manual
ARCEUS_CODEX_BIN=/Applications/Codex.app/Contents/Resources/codex
ARCEUS_CODEX_SANDBOX=workspace-write
ARCEUS_CODEX_APPROVAL_POLICY=never
ARCEUS_CODEX_SKIP_GIT_REPO_CHECK=false
```

Do not type those lines directly into Terminal unless you also export them or
prefix the command. The simplest path is editing `.env`.

Then run:

```bash
./scripts/arceus setup-db
./scripts/arceus chat
```

Ask for implementation-style work, for example:

```text
Help me implement a small memory summary command.
```

Arceus should create a handoff packet and show a handoff id.

## Record a Result

After running the handoff in Codex, save or paste the result back:

```bash
./scripts/arceus record-handoff-result <handoff-id> --result-file result.txt
```

For a short result, inline summary and memory are enough:

```bash
./scripts/arceus record-handoff-result <handoff-id> \
  --summary "Implemented the requested command." \
  --memory "Arceus learned that this workflow is useful."
```

Or pipe/paste through stdin:

```bash
pbpaste | ./scripts/arceus record-handoff-result <handoff-id> --result-file -
```

Show a handoff:

```bash
./scripts/arceus show-handoff <handoff-id>
```

List handoffs:

```bash
./scripts/arceus list-handoffs
```

Run a stored handoff through local Codex and record the result automatically:

```bash
./scripts/arceus run-handoff <handoff-id>
```

Review the local memory pulse after recording a result:

```bash
./scripts/arceus memory-summary
```

## Runtime Doctor

Check local runtime availability:

```bash
./scripts/arceus runtime-doctor
```

Expected for now:

- Codex available;
- Codex app-server help visible;
- Codex MCP-server help visible;
- Claude Code unavailable unless installed later.

For the deeper app-server protocol check:

```bash
./scripts/arceus app-server-doctor
```
