from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, Optional

from psycopg.types.json import Jsonb

from arceus.config import Settings
from arceus.db import connect
from arceus.status import StatusTracker, StatusUpdate, truncate


MessageRow = Dict[str, Any]


@dataclass(frozen=True)
class ConversationTurn:
    session_id: str
    user_message: str
    assistant_message: str
    runtime: str


class ConversationStore:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.status_tracker = StatusTracker(settings)

    def create_session(self, title: str = "Arceus Conversation") -> str:
        with connect(self.settings) as conn:
            with conn.transaction():
                row = conn.execute(
                """
                INSERT INTO conversation_sessions (owner_id, title, runtime)
                VALUES (%s, %s, %s)
                RETURNING id
                """,
                    (self.settings.owner_id, title, self.settings.runtime_mode),
                ).fetchone()
                session_id = str(row["id"])
                self._add_avatar_event(conn, session_id, "idle", "Arceus is awake.")
                return session_id

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        runtime: Optional[str] = None,
    ) -> None:
        with connect(self.settings) as conn:
            with conn.transaction():
                conn.execute(
                    """
                    INSERT INTO conversation_messages (
                        session_id,
                        role,
                        content,
                        runtime
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    (session_id, role, content, runtime),
                )
                conn.execute(
                    """
                    UPDATE conversation_sessions
                    SET updated_at = now()
                    WHERE id = %s
                    """,
                    (session_id,),
                )

    def list_messages(self, session_id: str, limit: int = 20) -> Iterable[MessageRow]:
        with connect(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT role, content, runtime, created_at
                FROM conversation_messages
                WHERE session_id = %s
                ORDER BY created_at DESC, id DESC
                LIMIT %s
                """,
                (session_id, limit),
            ).fetchall()
            return list(reversed([dict(row) for row in rows]))

    def add_avatar_event(
        self,
        session_id: Optional[str],
        state: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        with connect(self.settings) as conn:
            self._add_avatar_event(conn, session_id, state, message, data)

    def _add_avatar_event(
        self,
        conn: Any,
        session_id: Optional[str],
        state: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        conn.execute(
            """
            INSERT INTO avatar_events (session_id, state, message, data)
            VALUES (%s, %s, %s, %s)
            """,
            (session_id, state, message, Jsonb(data or {})),
        )

    def record_turn(self, turn: ConversationTurn) -> None:
        self.add_avatar_event(turn.session_id, "listening", "User message received.")
        self.add_message(turn.session_id, "user", turn.user_message)
        self.add_avatar_event(turn.session_id, "thinking", "Arceus is shaping a response.")
        self.add_message(
            turn.session_id,
            "assistant",
            turn.assistant_message,
            runtime=turn.runtime,
        )
        self.add_avatar_event(turn.session_id, "speaking", "Arceus responded.")
        self.add_avatar_event(turn.session_id, "idle", "Arceus returned to watchful idle.")
        if _is_meaningful_chat(turn.user_message, turn.assistant_message):
            self._record_status_update(
                StatusUpdate(
                    actor="arceus",
                    runtime=turn.runtime,
                    workstream="Conversation",
                    status="captured",
                    summary=f"Conversation checkpoint: {truncate(turn.user_message)}",
                    next_actions=_extract_next_actions(turn.assistant_message),
                    memory_notes=truncate(turn.assistant_message, 420),
                    source_type="conversation_session",
                    source_id=turn.session_id,
                )
            )

    def create_runtime_handoff(
        self,
        session_id: str,
        runtime: str,
        user_intent: str,
        handoff_prompt: str,
    ) -> str:
        with connect(self.settings) as conn:
            with conn.transaction():
                row = conn.execute(
                    """
                    INSERT INTO runtime_handoffs (
                        owner_id,
                        session_id,
                        runtime,
                        user_intent,
                        handoff_prompt
                    )
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        self.settings.owner_id,
                        session_id,
                        runtime,
                        user_intent,
                        handoff_prompt,
                    ),
                ).fetchone()
                handoff_id = str(row["id"])
                self._add_avatar_event(
                    conn,
                    session_id,
                    "planning",
                    "Codex handoff packet drafted.",
                    {"handoff_id": handoff_id, "runtime": runtime},
                )
                self._record_status_update(
                    StatusUpdate(
                        actor="arceus",
                        runtime=runtime,
                        workstream="Execution Runtime",
                        status="drafted",
                        summary=f"Codex handoff drafted: {truncate(user_intent)}",
                        next_actions=[
                            f"Run or record a result for handoff {handoff_id}.",
                        ],
                        memory_notes="A supervised Codex handoff was created and is awaiting execution or manual result recording.",
                        linked_task=handoff_id,
                        source_type="runtime_handoff",
                        source_id=handoff_id,
                    )
                )
                return handoff_id

    def record_handoff_result(
        self,
        handoff_id: str,
        result_text: str,
        result_summary: Optional[str] = None,
        memory_summary: Optional[str] = None,
    ) -> bool:
        with connect(self.settings) as conn:
            with conn.transaction():
                row = conn.execute(
                    """
                    UPDATE runtime_handoffs
                    SET status = 'result_recorded',
                        result_text = %s,
                        result_summary = %s,
                        memory_summary = %s,
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = %s
                    RETURNING session_id, runtime, user_intent
                    """,
                    (result_text, result_summary, memory_summary, handoff_id),
                ).fetchone()

                if row is None:
                    return False

                session_id = row["session_id"]
                if session_id:
                    self._add_avatar_event(
                        conn,
                        str(session_id),
                        "remembering",
                        "Codex handoff result recorded.",
                        {"handoff_id": handoff_id},
                    )
                self._record_status_update(
                    StatusUpdate(
                        actor="codex",
                        runtime=str(row["runtime"]),
                        workstream="Execution Runtime",
                        status="completed",
                        summary=result_summary or f"Codex handoff result recorded: {truncate(str(row['user_intent']))}",
                        next_actions=[],
                        memory_notes=memory_summary or truncate(result_text, 420),
                        linked_task=handoff_id,
                        source_type="runtime_handoff",
                        source_id=handoff_id,
                    )
                )
                return True

    def mark_handoff_running(self, handoff_id: str) -> bool:
        with connect(self.settings) as conn:
            with conn.transaction():
                row = conn.execute(
                    """
                    UPDATE runtime_handoffs
                    SET status = 'running',
                        updated_at = now()
                    WHERE id = %s
                      AND status IN ('drafted', 'failed')
                    RETURNING session_id, runtime, user_intent
                    """,
                    (handoff_id,),
                ).fetchone()

                if row is None:
                    return False

                session_id = row["session_id"]
                if session_id:
                    self._add_avatar_event(
                        conn,
                        str(session_id),
                        "executing",
                        "Codex autorun started.",
                        {"handoff_id": handoff_id},
                    )
                self._record_status_update(
                    StatusUpdate(
                        actor="codex",
                        runtime=str(row["runtime"]),
                        workstream="Execution Runtime",
                        status="running",
                        summary=f"Codex autorun started: {truncate(str(row['user_intent']))}",
                        next_actions=[f"Wait for handoff {handoff_id} to complete or fail."],
                        linked_task=handoff_id,
                        source_type="runtime_handoff",
                        source_id=handoff_id,
                    )
                )
                return True

    def mark_handoff_failed(
        self,
        handoff_id: str,
        result_text: str,
        result_summary: Optional[str] = None,
        memory_summary: Optional[str] = None,
    ) -> bool:
        with connect(self.settings) as conn:
            with conn.transaction():
                row = conn.execute(
                    """
                    UPDATE runtime_handoffs
                    SET status = 'failed',
                        result_text = %s,
                        result_summary = %s,
                        memory_summary = %s,
                        completed_at = now(),
                        updated_at = now()
                    WHERE id = %s
                    RETURNING session_id, runtime, user_intent
                    """,
                    (result_text, result_summary, memory_summary, handoff_id),
                ).fetchone()

                if row is None:
                    return False

                session_id = row["session_id"]
                if session_id:
                    self._add_avatar_event(
                        conn,
                        str(session_id),
                        "fractured",
                        "Codex autorun failed.",
                        {"handoff_id": handoff_id},
                    )
                self._record_status_update(
                    StatusUpdate(
                        actor="codex",
                        runtime=str(row["runtime"]),
                        workstream="Execution Runtime",
                        status="failed",
                        summary=result_summary or f"Codex handoff failed: {truncate(str(row['user_intent']))}",
                        blockers=[result_summary or truncate(result_text, 260)],
                        next_actions=[f"Inspect failed handoff {handoff_id} before retrying."],
                        memory_notes=memory_summary or truncate(result_text, 420),
                        linked_task=handoff_id,
                        source_type="runtime_handoff",
                        source_id=handoff_id,
                    )
                )
                return True

    def get_handoff(self, handoff_id: str) -> Optional[dict[str, Any]]:
        with connect(self.settings) as conn:
            row = conn.execute(
                """
                SELECT *
                FROM runtime_handoffs
                WHERE id = %s
                """,
                (handoff_id,),
            ).fetchone()
            return dict(row) if row else None

    def list_handoffs(self, limit: int = 20) -> list[dict[str, Any]]:
        with connect(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM runtime_handoffs
                WHERE owner_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (self.settings.owner_id, limit),
            ).fetchall()
            return [dict(row) for row in rows]

    def build_memory_summary(self, limit: int = 5) -> dict[str, Any]:
        with connect(self.settings) as conn:
            session_rows = conn.execute(
                """
                SELECT
                    session.id,
                    session.title,
                    session.runtime,
                    session.created_at,
                    session.updated_at,
                    COUNT(message.id) AS message_count,
                    MAX(message.created_at) AS last_message_at
                FROM conversation_sessions AS session
                LEFT JOIN conversation_messages AS message
                  ON message.session_id = session.id
                WHERE session.owner_id = %s
                GROUP BY session.id
                ORDER BY session.updated_at DESC
                LIMIT %s
                """,
                (self.settings.owner_id, limit),
            ).fetchall()

            handoff_rows = conn.execute(
                """
                SELECT
                    id,
                    runtime,
                    status,
                    user_intent,
                    result_summary,
                    memory_summary,
                    created_at,
                    completed_at
                FROM runtime_handoffs
                WHERE owner_id = %s
                ORDER BY created_at DESC
                LIMIT %s
                """,
                (self.settings.owner_id, limit),
            ).fetchall()

            task_rows = conn.execute(
                """
                SELECT status, COUNT(*) AS count
                FROM remote_tasks
                WHERE owner_id = %s
                GROUP BY status
                ORDER BY status
                """,
                (self.settings.owner_id,),
            ).fetchall()

        try:
            current_status = self.status_tracker.current_state(limit=limit)
        except Exception:
            current_status = {
                "owner_id": self.settings.owner_id,
                "obsidian_vault_path": str(self.settings.obsidian_vault_path) if self.settings.obsidian_vault_path else None,
                "obsidian_current_state_path": None,
                "latest_update": None,
                "recent_updates": [],
                "next_actions": ["Run ./scripts/arceus setup-db to create the status tracker tables."],
                "blockers": ["Status tracker is not initialized yet."],
            }

        return {
            "owner_id": self.settings.owner_id,
            "runtime_mode": self.settings.runtime_mode,
            "recent_sessions": [dict(row) for row in session_rows],
            "recent_handoffs": [dict(row) for row in handoff_rows],
            "task_counts": {row["status"]: row["count"] for row in task_rows},
            "current_status": current_status,
        }

    def _record_status_update(self, update: StatusUpdate) -> None:
        try:
            self.status_tracker.record(update)
        except Exception:
            return


def _is_meaningful_chat(user_message: str, assistant_message: str) -> bool:
    text = f"{user_message}\n{assistant_message}".lower()
    keywords = {
        "plan",
        "implement",
        "build",
        "decision",
        "roadmap",
        "status",
        "agent",
        "task",
        "project",
        "memory",
        "approval",
        "dashboard",
        "workflow",
        "obsidian",
        "codex",
    }
    return len(user_message.strip()) > 140 or any(keyword in text for keyword in keywords)


def _extract_next_actions(assistant_message: str) -> list[str]:
    actions = []
    for line in assistant_message.splitlines():
        cleaned = line.strip().strip("-").strip()
        if not cleaned:
            continue
        lower = cleaned.lower()
        if lower.startswith(("next ", "run ", "open ", "review ", "record ", "implement ", "create ")):
            actions.append(cleaned[:220])
    return actions[:5]
