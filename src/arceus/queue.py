from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Iterable, Optional

from psycopg.types.json import Jsonb

from arceus.config import Settings
from arceus.db import connect
from arceus.status import StatusTracker, StatusUpdate, truncate


TaskRow = Dict[str, Any]


@dataclass(frozen=True)
class EnqueueRequest:
    worker_role: str
    kind: str
    payload: Dict[str, Any]
    owner_id: str
    origin_task_id: Optional[str] = None
    chain_depth: int = 0
    expires_at: Optional[str] = None


class RemoteTaskQueue:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.status_tracker = StatusTracker(settings)

    def enqueue(self, request: EnqueueRequest) -> str:
        with connect(self.settings) as conn:
            with conn.transaction():
                row = conn.execute(
                    """
                    INSERT INTO remote_tasks (
                        owner_id,
                        worker_role,
                        kind,
                        payload,
                        origin_task_id,
                        chain_depth,
                        expires_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        request.owner_id,
                        request.worker_role,
                        request.kind,
                        Jsonb(request.payload),
                        request.origin_task_id,
                        request.chain_depth,
                        request.expires_at,
                    ),
                ).fetchone()
                task_id = str(row["id"])
                self._add_event(conn, task_id, "queued", "Task entered the queue.")
                conn.execute("SELECT pg_notify('remote_tasks', %s)", (task_id,))
                return task_id

    def claim(self, worker_role: str, claimed_by: str) -> Optional[TaskRow]:
        with connect(self.settings) as conn:
            with conn.transaction():
                row = conn.execute(
                    """
                    WITH next_task AS (
                        SELECT id
                        FROM remote_tasks
                        WHERE worker_role = %s
                          AND status = 'pending'
                          AND (expires_at IS NULL OR expires_at > now())
                        ORDER BY created_at ASC
                        FOR UPDATE SKIP LOCKED
                        LIMIT 1
                    )
                    UPDATE remote_tasks AS task
                    SET status = 'claimed',
                        claimed_by = %s,
                        claimed_at = now(),
                        updated_at = now()
                    FROM next_task
                    WHERE task.id = next_task.id
                    RETURNING task.*
                    """,
                    (worker_role, claimed_by),
                ).fetchone()

                if row is None:
                    return None

                task_id = str(row["id"])
                self._add_event(
                    conn,
                    task_id,
                    "claimed",
                    f"Task claimed by {claimed_by}.",
                    {"claimed_by": claimed_by},
                )
                return dict(row)

    def complete(self, task_id: str, result: Dict[str, Any]) -> None:
        task = self.get_task(task_id)
        with connect(self.settings) as conn:
            with conn.transaction():
                conn.execute(
                    """
                    UPDATE remote_tasks
                    SET status = 'completed',
                        result = %s,
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (Jsonb(result), task_id),
                )
                self._add_event(conn, task_id, "completed", "Task completed.", result)
                conn.execute("SELECT pg_notify('remote_task_results', %s)", (task_id,))
        self._record_task_status(task_id, task, "completed", result)

    def fail(self, task_id: str, error_message: str, result: Optional[Dict[str, Any]] = None) -> None:
        safe_result = result or {"status": "error", "message": error_message}
        task = self.get_task(task_id)
        with connect(self.settings) as conn:
            with conn.transaction():
                conn.execute(
                    """
                    UPDATE remote_tasks
                    SET status = 'failed',
                        result = %s,
                        error_message = %s,
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (Jsonb(safe_result), error_message, task_id),
                )
                self._add_event(conn, task_id, "failed", error_message, safe_result)
                conn.execute("SELECT pg_notify('remote_task_results', %s)", (task_id,))
        self._record_task_status(task_id, task, "failed", safe_result, error_message)

    def get_task(self, task_id: str) -> Optional[TaskRow]:
        with connect(self.settings) as conn:
            row = conn.execute(
                "SELECT * FROM remote_tasks WHERE id = %s",
                (task_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_tasks(self, limit: int = 20) -> Iterable[TaskRow]:
        with connect(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM remote_tasks
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]

    def _add_event(
        self,
        conn: Any,
        task_id: str,
        event_type: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO remote_task_events (task_id, event_type, message, data)
            VALUES (%s, %s, %s, %s)
            """,
            (task_id, event_type, message, Jsonb(data or {})),
        )

    def _record_task_status(
        self,
        task_id: str,
        task: Optional[TaskRow],
        status: str,
        result: Dict[str, Any],
        error_message: str | None = None,
    ) -> None:
        try:
            kind = str(task.get("kind") if task else "unknown")
            payload = task.get("payload") if task else {}
            summary = str(result.get("summary") or result.get("message") or f"Task {status}.")
            blockers = [error_message or summary] if status == "failed" else []
            actor = str((task.get("claimed_by") if task else None) or self.settings.worker_id)
            self.status_tracker.record(
                StatusUpdate(
                    actor=actor,
                    runtime="local_worker",
                    workstream="Task Queue",
                    status=status,
                    summary=f"{kind} task {status}: {truncate(summary)}",
                    blockers=blockers,
                    next_actions=[f"Review task {task_id} before retrying."] if status == "failed" else [],
                    memory_notes=truncate(str(result), 420),
                    linked_task=task_id,
                    source_type="remote_task",
                    source_id=task_id,
                    metadata={"kind": kind, "payload": payload},
                )
            )
        except Exception:
            return


def json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def to_pretty_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, default=json_default)
