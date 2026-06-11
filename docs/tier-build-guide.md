# Tier Build Guide

This guide explains how to build Arceus step by step.

The principle is simple: build the smallest useful layer, verify it, then move
to the next layer.

## Tier 0: Project Foundation

Goal:

- create the project doctrine, product requirements, architecture, agent rules,
  skill plan, memory plan, and guardrails.

Why it matters:

- Arceus is broad and ambitious. Without written constraints, the system will
  drift.

Verification:

- the user confirms the plan;
- docs exist and agree with each other;
- next implementation tier is clear.

## Track A: Presence and Conversation

This track makes Arceus feel alive and useful before it becomes a large
execution system.

Build order:

1. Local text conversation shell.
2. Avatar state model.
3. Memory-aware conversation notes.
4. Reasoning journal summaries for substantial requests.
5. Voice input/output after text is stable.

Verification:

- the user can bounce ideas in real time;
- Arceus keeps context across a session;
- the avatar state changes with conversation;
- only action-worthy items become tasks.

## Track B: Durable Execution

This track gives Arceus reliable hands.

The queue and worker belong here.

## Tier 1: Durable Local Task Queue

Plain-English goal:

- create a reliable task inbox that survives restarts.

What it does:

- stores tasks in Postgres;
- lets Arceus add tasks;
- lets the laptop worker claim one task at a time;
- marks tasks completed or failed;
- drains pending tasks when the worker starts.

Why it matters:

- cross-machine routing depends on durable work records.
- if the laptop is asleep, the task must still exist when it wakes.

Verification:

1. Create a test task.
2. Stop the worker.
3. Start the worker.
4. Confirm it picks up the old task on startup.
5. Confirm the task status becomes completed.

Decision point before building:

- choose local Postgres setup method.

Current local command:

```bash
./scripts/arceus setup-db
./scripts/arceus enqueue --role "$(hostname)" --kind noop --payload '{}'
./scripts/arceus worker --role "$(hostname)"
./scripts/arceus show-task "<task-id>"
```

## Tier 2: Remote Dispatch Task Kind

Plain-English goal:

- teach the task system to carry agent requests.

What it does:

- stores tasks like "run filesystem agent with these instructions";
- routes the task to the correct laptop-side runner;
- waits for the real work to finish;
- stores a useful result.

Verification:

1. Queue a filesystem-agent task.
2. Watch the local worker run it.
3. Confirm the task reaches completed or failed.
4. Confirm the result summary is useful.
5. Confirm an unknown agent fails cleanly.

Decision point before building:

- define the first filesystem-agent input shape.

## Tier 3: Cloud Proxy Tool

Plain-English goal:

- let the cloud ask for laptop-only work without being able to perform it.

What it does:

- cloud exposes a proxy that looks like the real tool;
- proxy creates a durable task instead of executing locally;
- laptop later runs the real agent.

Verification:

1. Call the proxy from the cloud-like process.
2. Confirm a task appears.
3. Confirm nothing powerful runs in the cloud process.
4. Confirm laptop executes the task.

Decision point before building:

- define how we simulate cloud locally before real deployment.

## Tier 4: Presence and Honest Acknowledgements

Plain-English goal:

- know whether the laptop appears online, only to word messages honestly.

What it does:

- laptop sends a heartbeat;
- cloud checks whether the heartbeat is fresh;
- if laptop is online, message says it is starting;
- if laptop is offline, message says it is queued for later.

Important:

- presence never decides whether a task is queued.

Verification:

1. Start laptop process and confirm online.
2. Stop laptop process and wait.
3. Confirm offline.
4. Queue a task anyway.

Decision point before building:

- choose heartbeat freshness window, likely around 90 seconds.

## Tier 5: Local UI Visibility and Approvals

Plain-English goal:

- see what Arceus is doing on the laptop and approve risky actions.

What it does:

- shows queued/running/completed/failed tasks;
- shows approval cards;
- shows safe summaries;
- displays lore-styled lifecycle labels.
- introduces the first mission-control dashboard shell with central avatar,
  animated task cards, and readable command panels.

Verification:

1. Open the local dashboard.
2. Queue a task.
3. Watch it appear.
4. Confirm it pauses for approval before writes.
5. Approve or reject.
6. Confirm the final task status is correct.

Decision point before building:

- choose first UI layout, avatar placeholder, and motion intensity.

## Tier 6: Remote Completion Ping

Plain-English goal:

- notify the phone/PWA when laptop work completes or fails.

What it does:

- listens for completed or failed tasks;
- sends a useful summary to the remote surface;
- hides sensitive details behind "View details";
- uses lore-styled failure messages.

Verification:

1. Queue a successful task.
2. Confirm phone/PWA receives a completion summary.
3. Force a failure.
4. Confirm phone/PWA says it fractured, not that it finished.
5. Confirm details are hidden by default.

Decision point before building:

- define first notification channel in the PWA.

## Tier 7: Memory Update Skill

Plain-English goal:

- make Arceus remember the useful parts of what happened.

What it does:

- records decisions;
- updates project context;
- saves useful summaries to Obsidian and Notion;
- links memory to tasks and agents.

Verification:

1. Complete a substantial task.
2. Confirm a memory entry is created.
3. Confirm it appears in the expected knowledge base.
4. Confirm future Arceus can retrieve it.

Decision point before building:

- choose the first Obsidian vault location and Notion workspace strategy.

## Teaching Style for Each Tier

For every tier, explain:

1. What we are building in plain English.
2. Why it matters to the northstar.
3. What choices the user needs to make.
4. What files are being added or changed.
5. How we verify it.
6. What risks or tradeoffs exist.

Do not proceed to the next tier until the current tier is verified.
