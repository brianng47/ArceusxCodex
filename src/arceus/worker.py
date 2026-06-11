from __future__ import annotations

import time
from typing import Any, Dict

from arceus.queue import RemoteTaskQueue, TaskRow


def handle_task(task: TaskRow) -> Dict[str, Any]:
    kind = task["kind"]

    if kind == "noop":
        return {
            "status": "success",
            "summary": "No-op task completed. The queue is alive.",
        }

    return {
        "status": "error",
        "summary": f"No Tier 1 handler exists for task kind '{kind}'.",
    }


def drain_once(queue: RemoteTaskQueue, worker_role: str, worker_id: str) -> int:
    completed = 0

    while True:
        task = queue.claim(worker_role=worker_role, claimed_by=worker_id)
        if task is None:
            return completed

        task_id = str(task["id"])
        result = handle_task(task)
        if result.get("status") == "error":
            queue.fail(task_id, result["summary"], result)
        else:
            queue.complete(task_id, result)
        completed += 1


def run_polling_worker(
    queue: RemoteTaskQueue,
    worker_role: str,
    worker_id: str,
    poll_interval_seconds: float,
) -> None:
    print(f"Arceus worker online as {worker_id} for role {worker_role}.")
    print("Draining pending tasks on startup.")

    while True:
        completed = drain_once(queue, worker_role, worker_id)
        if completed:
            print(f"Processed {completed} task(s).")
        time.sleep(poll_interval_seconds)
