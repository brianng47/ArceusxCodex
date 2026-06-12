from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

from psycopg.types.json import Jsonb

from arceus.config import Settings
from arceus.db import connect
from arceus.path_policy import ensure_write_allowed


STATUS_ROOT = Path("Arceus") / "00_System"
STATUS_TRACKER_DIR = STATUS_ROOT / "Status Tracker"
CURRENT_STATE_PATH = STATUS_ROOT / "Current State.md"
FALLBACK_STATUS_DIR = Path("status-fallback")
FALLBACK_CURRENT_STATE_PATH = FALLBACK_STATUS_DIR / "Current State.md"


@dataclass(frozen=True)
class StatusUpdate:
    actor: str
    runtime: str
    workstream: str
    status: str
    summary: str
    decisions: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)
    memory_notes: Optional[str] = None
    linked_project: Optional[str] = None
    linked_task: Optional[str] = None
    linked_agent: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class StatusTracker:
    def __init__(self, settings: Settings):
        self.settings = settings

    def record(self, update: StatusUpdate) -> dict[str, Any]:
        try:
            with connect(self.settings) as conn:
                with conn.transaction():
                    row = conn.execute(
                        """
                        INSERT INTO status_updates (
                            owner_id,
                            actor,
                            runtime,
                            workstream,
                            status,
                            summary,
                            decisions,
                            files_changed,
                            blockers,
                            next_actions,
                            memory_notes,
                            linked_project,
                            linked_task,
                            linked_agent,
                            source_type,
                            source_id,
                            metadata
                        )
                        VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                            %s, %s, %s, %s, %s, %s, %s
                        )
                        RETURNING *
                        """,
                        (
                            self.settings.owner_id,
                            update.actor,
                            update.runtime,
                            update.workstream,
                            update.status,
                            update.summary,
                            Jsonb(update.decisions),
                            Jsonb(update.files_changed),
                            Jsonb(update.blockers),
                            Jsonb(update.next_actions),
                            update.memory_notes,
                            update.linked_project,
                            update.linked_task,
                            update.linked_agent,
                            update.source_type,
                            update.source_id,
                            Jsonb(update.metadata),
                        ),
                    ).fetchone()
        except Exception as exc:
            return self._record_fallback(update, exc)

        record = dict(row)
        obsidian_path = None
        obsidian_error = None
        try:
            obsidian_path = self._write_obsidian_status(record)
            self._write_current_state()
        except Exception as exc:
            obsidian_error = str(exc)

        if obsidian_path or obsidian_error:
            with connect(self.settings) as conn:
                with conn.transaction():
                    updated = conn.execute(
                        """
                        UPDATE status_updates
                        SET obsidian_path = %s,
                            obsidian_error = %s
                        WHERE id = %s
                        RETURNING *
                        """,
                        (obsidian_path, obsidian_error, record["id"]),
                    ).fetchone()
                    record = dict(updated)

        return record

    def latest(self, limit: int = 10) -> list[dict[str, Any]]:
        try:
            with connect(self.settings) as conn:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM status_updates
                    WHERE owner_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (self.settings.owner_id, limit),
                ).fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return self._fallback_latest(limit)

    def current_state(self, limit: int = 5) -> dict[str, Any]:
        recent = self.latest(limit)
        latest = recent[0] if recent else None
        next_actions: list[str] = []
        blockers: list[str] = []

        for update in recent:
            next_actions.extend(_as_list(update.get("next_actions")))
            blockers.extend(_as_list(update.get("blockers")))

        return {
            "owner_id": self.settings.owner_id,
            "obsidian_vault_path": str(self.settings.obsidian_vault_path) if self.settings.obsidian_vault_path else None,
            "obsidian_current_state_path": self._display_path(CURRENT_STATE_PATH),
            "latest_update": latest,
            "recent_updates": recent,
            "next_actions": _dedupe(next_actions)[:8],
            "blockers": _dedupe(blockers)[:8],
        }

    def _write_obsidian_status(self, record: dict[str, Any]) -> str | None:
        vault = self.settings.obsidian_vault_path
        if vault is None:
            return None
        ensure_write_allowed(self.settings, vault)

        tracker_dir = vault / STATUS_TRACKER_DIR
        ensure_write_allowed(self.settings, tracker_dir)
        tracker_dir.mkdir(parents=True, exist_ok=True)

        created_at = record["created_at"]
        if not isinstance(created_at, datetime):
            created_at = datetime.now(timezone.utc)
        stamp = created_at.astimezone().strftime("%Y-%m-%d %H%M%S")
        slug = _slugify(str(record["summary"]))
        note_path = tracker_dir / f"{stamp} - {slug}.md"
        ensure_write_allowed(self.settings, note_path)
        note_path.write_text(_render_status_note(record), encoding="utf-8")
        return str(note_path.relative_to(vault))

    def _write_current_state(self) -> None:
        vault = self.settings.obsidian_vault_path
        if vault is None:
            return
        ensure_write_allowed(self.settings, vault)

        current_path = vault / CURRENT_STATE_PATH
        ensure_write_allowed(self.settings, current_path)
        current_path.parent.mkdir(parents=True, exist_ok=True)
        current_path.write_text(_render_current_state(self.current_state(limit=8)), encoding="utf-8")

    def _display_path(self, relative_path: Path) -> str | None:
        vault = self.settings.obsidian_vault_path
        if vault is None:
            return None
        return str(vault / relative_path)

    def _record_fallback(self, update: StatusUpdate, db_error: Exception) -> dict[str, Any]:
        created_at = datetime.now(timezone.utc).astimezone()
        record = {
            "id": f"local-{uuid4()}",
            "owner_id": self.settings.owner_id,
            "actor": update.actor,
            "runtime": update.runtime,
            "workstream": update.workstream,
            "status": update.status,
            "summary": update.summary,
            "decisions": update.decisions,
            "files_changed": update.files_changed,
            "blockers": update.blockers,
            "next_actions": update.next_actions,
            "memory_notes": update.memory_notes,
            "linked_project": update.linked_project,
            "linked_task": update.linked_task,
            "linked_agent": update.linked_agent,
            "source_type": update.source_type,
            "source_id": update.source_id,
            "metadata": update.metadata,
            "created_at": created_at.isoformat(),
            "storage": "local_fallback",
            "db_error": str(db_error),
            "obsidian_path": None,
            "obsidian_error": "Skipped because the primary status database was unavailable.",
        }

        fallback_dir = ensure_write_allowed(self.settings, self.settings.arceus_state_path / FALLBACK_STATUS_DIR)
        fallback_dir.mkdir(parents=True, exist_ok=True)
        stamp = created_at.strftime("%Y-%m-%d %H%M%S")
        slug = _slugify(update.summary)
        json_path = ensure_write_allowed(self.settings, fallback_dir / f"{stamp} - {slug}.json")
        note_path = ensure_write_allowed(self.settings, fallback_dir / f"{stamp} - {slug}.md")
        json_path.write_text(json.dumps(_json_safe(record), indent=2, sort_keys=True), encoding="utf-8")
        note_path.write_text(_render_status_note(record), encoding="utf-8")
        record["fallback_json_path"] = str(json_path)
        record["fallback_note_path"] = str(note_path)
        self._write_fallback_current_state()
        return record

    def _fallback_latest(self, limit: int = 10) -> list[dict[str, Any]]:
        fallback_dir = self.settings.arceus_state_path / FALLBACK_STATUS_DIR
        if not fallback_dir.exists():
            return []

        records: list[dict[str, Any]] = []
        for path in sorted(fallback_dir.glob("*.json"), reverse=True)[:limit]:
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except (OSError, json.JSONDecodeError):
                continue
        return records

    def _write_fallback_current_state(self) -> None:
        fallback_path = ensure_write_allowed(self.settings, self.settings.arceus_state_path / FALLBACK_CURRENT_STATE_PATH)
        fallback_path.parent.mkdir(parents=True, exist_ok=True)
        state = self.current_state(limit=8)
        fallback_path.write_text(_render_current_state(state), encoding="utf-8")


def initial_dashboard_roadmap_update(settings: Settings, actor: str = "arceus_cli") -> StatusUpdate:
    return StatusUpdate(
        actor=actor,
        runtime=settings.runtime_mode,
        workstream="Dashboard Roadmap",
        status="initialized",
        summary="Arceus dashboard roadmap and automatic status tracker initialized.",
        decisions=[
            "Use Postgres as the operational ledger.",
            "Use the iCloud Obsidian vault as the canonical long-term memory.",
            "Read the compact Current State before loading long histories.",
        ],
        next_actions=[
            "Build the data backbone for dashboard zones.",
            "Wire Chats, Agents, Tasks, Workflows, and Projects to real records.",
            "Keep status updates automatic after meaningful work.",
        ],
        memory_notes=(
            "The status tracker is the token-saving spine of Arceus. "
            "Future agents should read Current State first."
        ),
        source_type="roadmap",
        source_id="dashboard-roadmap-status-tracker",
    )


def initialize_status_tracker(settings: Settings, actor: str = "arceus_cli") -> dict[str, Any]:
    return StatusTracker(settings).record(initial_dashboard_roadmap_update(settings, actor=actor))


def _render_status_note(record: dict[str, Any]) -> str:
    created_at = record.get("created_at")
    return "\n".join(
        [
            "---",
            "type: arceus_status_update",
            f"id: {record.get('id')}",
            f"created_at: {created_at.isoformat() if isinstance(created_at, datetime) else created_at}",
            f"workstream: {record.get('workstream')}",
            f"status: {record.get('status')}",
            f"source_type: {record.get('source_type') or ''}",
            f"source_id: {record.get('source_id') or ''}",
            f"linked_project: {record.get('linked_project') or ''}",
            f"linked_task: {record.get('linked_task') or ''}",
            f"linked_agent: {record.get('linked_agent') or ''}",
            "---",
            "",
            f"# {record.get('summary')}",
            "",
            f"- Actor: {record.get('actor')}",
            f"- Runtime: {record.get('runtime')}",
            f"- Workstream: {record.get('workstream')}",
            f"- Status: {record.get('status')}",
            "",
            _section("Decisions", _as_list(record.get("decisions"))),
            _section("Files Changed", _as_list(record.get("files_changed"))),
            _section("Blockers", _as_list(record.get("blockers"))),
            _section("Next Actions", _as_list(record.get("next_actions"))),
            "## Memory Notes",
            "",
            str(record.get("memory_notes") or "No durable note captured."),
            "",
        ]
    )


def _render_current_state(state: dict[str, Any]) -> str:
    latest = state.get("latest_update") or {}
    recent = state.get("recent_updates") or []
    lines = [
        "# Arceus Current State",
        "",
        "This file is generated by Arceus after meaningful sessions, handoffs, and task lifecycle events.",
        "Read this first before loading long chat history.",
        "",
        "## Latest Update",
        "",
    ]

    if latest:
        created_at = latest.get("created_at")
        created_text = created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
        lines.extend(
            [
                f"- Time: {created_text}",
                f"- Workstream: {latest.get('workstream')}",
                f"- Status: {latest.get('status')}",
                f"- Summary: {latest.get('summary')}",
                "",
            ]
        )
    else:
        lines.extend(["No status updates recorded yet.", ""])

    lines.extend([_section("Current Blockers", state.get("blockers") or []), _section("Next Actions", state.get("next_actions") or [])])
    lines.extend(["## Recent Updates", ""])
    if recent:
        for update in recent:
            lines.append(f"- {update.get('status')} / {update.get('workstream')}: {update.get('summary')}")
    else:
        lines.append("No recent updates.")
    lines.append("")
    return "\n".join(lines)


def _section(title: str, items: list[str]) -> str:
    lines = [f"## {title}", ""]
    if not items:
        lines.append("None.")
    else:
        lines.extend(f"- {item}" for item in items)
    lines.append("")
    return "\n".join(lines)


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return (cleaned or "status-update")[:70]


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        deduped.append(item)
    return deduped


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Path):
        return str(value)
    return value


def truncate(value: str, limit: int = 180) -> str:
    text = " ".join(str(value).split())
    if len(text) <= limit:
        return text
    return f"{text[: limit - 1].rstrip()}..."
