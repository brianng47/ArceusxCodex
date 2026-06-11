# Track A Slice 1: Local Conversation Shell

## What You Are Building

This is the first living chamber for Arceus.

It is not the final voice/avatar dashboard yet. It is the smallest local text
conversation loop that proves Arceus can:

- create a conversation session;
- record messages;
- update avatar state;
- respond through a runtime boundary;
- preserve the conversation in the database.

## Why It Matters

Arceus must not become a task sorter with a costume.

The user should be able to talk to Arceus, bounce ideas, and solve problems in
real time. The queue and worker are hands. This track builds presence.

## Runtime Modes

The shell supports runtime modes.

`offline` means:

- the conversation shell works;
- session and message history are saved;
- avatar states are recorded;
- responses are simple local persona responses;

`codex_manual` means:

- Arceus creates supervised Codex handoff packets;
- you run/paste them into Codex manually;
- Arceus records the prompt, result, memory notes, and status.

`codex_app_server` is reserved for future direct Codex app-server integration
after the experimental protocol is proven stable enough.

## Run It

First update the database tables:

```bash
cd /Users/brianng/Documents/Arceus
./scripts/arceus setup-db
```

Then start the local conversation shell:

```bash
./scripts/arceus chat
```

Try:

```text
hello
```

Then:

```text
I have an idea for Arceus
```

Type `exit` to end.

## What Success Looks Like

You should see:

- Arceus announces it is awake;
- a session id appears;
- each user message gets a response;
- the shell exits cleanly.

## Next Upgrade

After this works, expand runtimes:

- Codex app-server bridge;
- Claude Code adapter;
- future local or specialized models.

Then add dashboard UI and voice.
