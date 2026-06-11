# Tier 1: Local Durable Queue

## What You Are Building

This is Arceus' first reliable task inbox.

When a future phone/cloud request needs your laptop, it will become a durable
task. The laptop worker will claim that task and run it.

## Why It Matters

If your laptop is asleep, Arceus still needs to remember the request.

The queue is the contract. Live notifications are useful later, but the saved
task row is what survives sleep, restart, and crashes.

## What Exists Now

- `remote_tasks` table migration.
- `remote_task_events` table migration.
- `enqueue` command.
- `drain` command.
- `worker` command.
- `show-task` and `list-tasks` commands.
- A Tier 1 `noop` task handler for verification.

## One-Time Setup

Run this from the project folder:

```bash
cd /Users/brianng/Documents/Arceus
./scripts/arceus setup-db
```

The first run may install Python dependencies into `.venv`.

## Verify the Queue

Create a test task:

```bash
TASK_ID=$(./scripts/arceus enqueue --role "$(hostname)" --kind noop --payload '{}')
echo "$TASK_ID"
```

Show the task before the worker runs:

```bash
./scripts/arceus show-task "$TASK_ID"
```

You should see status:

```text
pending
```

Drain pending tasks once:

```bash
./scripts/arceus drain --role "$(hostname)"
```

Show the task again:

```bash
./scripts/arceus show-task "$TASK_ID"
```

You should see:

```text
status: completed
summary: No-op task completed. The queue is alive.
```

## Verify Drain-On-Startup Behavior

This is the important test.

1. Create another task.
2. Do not run `drain`.
3. Start the worker.
4. Confirm the worker processes the already-waiting task.

Commands:

```bash
TASK_ID=$(./scripts/arceus enqueue --role "$(hostname)" --kind noop --payload '{}')
echo "$TASK_ID"
./scripts/arceus worker --role "$(hostname)"
```

The worker should say it processed a task shortly after startup.

Open a second Terminal window and run:

```bash
cd /Users/brianng/Documents/Arceus
./scripts/arceus show-task "$TASK_ID"
```

Stop the worker with `Control-C` after the test.

## What Success Means

Tier 1 is successful when:

- the database tables exist;
- a task can be queued;
- the worker claims it;
- the worker completes it;
- a task that existed before worker startup is processed on startup.

That last point proves the future cloud/laptop bridge will survive laptop
sleep.
