from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable, Optional
from uuid import UUID

from psycopg.types.json import Jsonb

from arceus.codex_runner import CodexRunError, start_handoff_codex_run
from arceus.config import Settings
from arceus.conversation import ConversationStore
from arceus.dashboard_launcher import dashboard_status, install_mac_launcher, open_dashboard
from arceus.db import connect
from arceus.migrations import migrate
from arceus.path_policy import describe_path_policy
from arceus.runtimes import inspect_codex_runtime
from arceus.status import StatusTracker, StatusUpdate, initialize_status_tracker, truncate


@dataclass(frozen=True)
class LocalAction:
    key: str
    title: str
    description: str
    risk_level: str
    approval_required: bool
    expected_output: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


ActionRunner = Callable[["LocalControlService", dict[str, Any]], dict[str, Any]]


ACTION_CATALOG: dict[str, LocalAction] = {
    "system_check": LocalAction(
        key="system_check",
        title="Check System",
        description="Check database reachability, runtime mode, Codex availability, and current status health.",
        risk_level="low",
        approval_required=False,
        expected_output="A compact health report; if the ledger is available, the run is audited.",
    ),
    "codex_doctor": LocalAction(
        key="codex_doctor",
        title="Check Codex",
        description="Inspect the configured local Codex runtime and report whether Arceus can find it.",
        risk_level="low",
        approval_required=False,
        expected_output="Codex path, version, and availability.",
    ),
    "status_summary": LocalAction(
        key="status_summary",
        title="Read Current State",
        description="Read the compact status tracker summary used to reduce token waste between sessions.",
        risk_level="low",
        approval_required=False,
        expected_output="Latest update, next actions, and blockers.",
    ),
    "dashboard_status": LocalAction(
        key="dashboard_status",
        title="Check Dashboard",
        description="Check whether the local dashboard server is reachable and where its logs are stored.",
        risk_level="low",
        approval_required=False,
        expected_output="Dashboard URL, running state, pid, and log path.",
    ),
    "path_policy_status": LocalAction(
        key="path_policy_status",
        title="Check Path Access",
        description="Show the folders Arceus is allowed to read and write through its application-level policy.",
        risk_level="low",
        approval_required=False,
        expected_output="Read roots and write roots; Documents-wide access should not appear.",
    ),
    "open_dashboard": LocalAction(
        key="open_dashboard",
        title="Open Dashboard",
        description="Open the local Arceus dashboard in the default browser.",
        risk_level="low",
        approval_required=False,
        expected_output="The dashboard opens locally if the server is reachable.",
    ),
    "setup_database": LocalAction(
        key="setup_database",
        title="Initialize Database",
        description="Create or update local Arceus database tables. This changes local Postgres schema.",
        risk_level="medium",
        approval_required=True,
        expected_output="Database migration result and action ledger entry.",
    ),
    "init_status_tracker": LocalAction(
        key="init_status_tracker",
        title="Initialize Status Tracker",
        description="Seed the automatic status tracker and write the Obsidian Current State note.",
        risk_level="medium",
        approval_required=True,
        expected_output="A status update in Postgres and a Current State note in Obsidian.",
    ),
    "install_mac_launcher": LocalAction(
        key="install_mac_launcher",
        title="Install Mac Launcher",
        description="Create a double-click macOS app that starts Arceus without opening a Terminal window.",
        risk_level="medium",
        approval_required=True,
        expected_output="An Arceus Dashboard app in your user Applications folder.",
    ),
    "run_latest_handoff": LocalAction(
        key="run_latest_handoff",
        title="Run Latest Codex Handoff",
        description="Start the latest drafted or failed Codex handoff through the local Codex runtime.",
        risk_level="medium",
        approval_required=True,
        expected_output="A background Codex run linked to the execution ledger.",
    ),
}


class LocalControlService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.status_tracker = StatusTracker(settings)

    def catalog(self) -> list[dict[str, Any]]:
        return [action.to_dict() for action in ACTION_CATALOG.values()]

    def recent_runs(self, limit: int = 8) -> list[dict[str, Any]]:
        try:
            with connect(self.settings) as conn:
                rows = conn.execute(
                    """
                    SELECT *
                    FROM local_action_runs
                    WHERE owner_id = %s
                    ORDER BY created_at DESC
                    LIMIT %s
                    """,
                    (self.settings.owner_id, limit),
                ).fetchall()
                return [dict(row) for row in rows]
        except Exception:
            return []

    def run(self, action_key: str, confirm: Optional[str] = None, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        action = ACTION_CATALOG.get(action_key)
        if action is None:
            raise ValueError(f"Unknown local action: {action_key}")
        if action.approval_required and confirm != action.key:
            raise ValueError(f"{action.title} requires approval before it can run.")

        payload = payload or {}
        if action.key == "setup_database":
            return self._run_setup_database(action, payload)

        run_id = self._create_run(action, "running")
        try:
            result = self._dispatch(action, payload)
            summary = str(result.get("summary") or f"{action.title} completed.")
            run = self._finish_run(run_id, "completed", summary, result, None) if run_id else None
            self._record_status(action, "completed", summary, result=result)
            return {"ok": True, "action": action.to_dict(), "run": run, "result": result}
        except Exception as exc:
            summary = f"{action.title} failed."
            error = str(exc)
            run = self._finish_run(run_id, "failed", summary, {}, error) if run_id else None
            self._record_status(
                action,
                "failed",
                summary,
                blockers=[error],
                next_actions=[f"Review the failed {action.title} action before retrying."],
            )
            return {"ok": False, "action": action.to_dict(), "run": run, "error": error}

    def _run_setup_database(self, action: LocalAction, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            migrate(self.settings)
            result = {"summary": "Arceus database is ready.", "database_ready": True}
            run_id = self._create_run(action, "running")
            run = self._finish_run(run_id, "completed", result["summary"], result, None) if run_id else None
            self._record_status(action, "completed", result["summary"], result=result)
            return {"ok": True, "action": action.to_dict(), "run": run, "result": result}
        except Exception as exc:
            error = str(exc)
            self._record_status(
                action,
                "failed",
                "Database initialization failed.",
                blockers=[error],
                next_actions=["Run the database check again after confirming local Postgres is running."],
            )
            return {"ok": False, "action": action.to_dict(), "run": None, "error": error}

    def _dispatch(self, action: LocalAction, payload: dict[str, Any]) -> dict[str, Any]:
        runners: dict[str, ActionRunner] = {
            "system_check": _run_system_check,
            "codex_doctor": _run_codex_doctor,
            "status_summary": _run_status_summary,
            "dashboard_status": _run_dashboard_status,
            "path_policy_status": _run_path_policy_status,
            "open_dashboard": _run_open_dashboard,
            "init_status_tracker": _run_init_status_tracker,
            "install_mac_launcher": _run_install_mac_launcher,
            "run_latest_handoff": _run_latest_handoff,
        }
        runner = runners.get(action.key)
        if runner is None:
            raise ValueError(f"No runner registered for {action.key}")
        return runner(self, payload)

    def _create_run(self, action: LocalAction, status: str) -> str | None:
        try:
            with connect(self.settings) as conn:
                with conn.transaction():
                    row = conn.execute(
                        """
                        INSERT INTO local_action_runs (
                            owner_id,
                            action_key,
                            title,
                            risk_level,
                            approval_required,
                            status,
                            approved_at,
                            started_at
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, now(), now())
                        RETURNING id
                        """,
                        (
                            self.settings.owner_id,
                            action.key,
                            action.title,
                            action.risk_level,
                            action.approval_required,
                            status,
                        ),
                    ).fetchone()
                    return str(row["id"])
        except Exception:
            return None

    def _finish_run(
        self,
        run_id: str,
        status: str,
        summary: str,
        output_data: dict[str, Any],
        error: str | None,
    ) -> dict[str, Any] | None:
        try:
            with connect(self.settings) as conn:
                with conn.transaction():
                    row = conn.execute(
                        """
                        UPDATE local_action_runs
                        SET status = %s,
                            output_summary = %s,
                            output_data = %s,
                            error_message = %s,
                            completed_at = now(),
                            updated_at = now()
                        WHERE id = %s
                        RETURNING *
                        """,
                        (status, summary, Jsonb(_json_safe(output_data)), error, run_id),
                    ).fetchone()
                    return dict(row) if row else None
        except Exception:
            return None

    def _record_status(
        self,
        action: LocalAction,
        status: str,
        summary: str,
        result: Optional[dict[str, Any]] = None,
        blockers: Optional[list[str]] = None,
        next_actions: Optional[list[str]] = None,
    ) -> None:
        try:
            self.status_tracker.record(
                StatusUpdate(
                    actor="arceus_dashboard",
                    runtime="local_control",
                    workstream="Local Control",
                    status=status,
                    summary=summary,
                    decisions=[f"{action.title} was run from the dashboard."],
                    blockers=blockers or [],
                    next_actions=next_actions or [],
                    memory_notes=truncate(_memory_note(result or summary), 420),
                    linked_agent="Arceus",
                    source_type="local_action",
                    source_id=action.key,
                    metadata={"action": action.to_dict()},
                )
            )
        except Exception:
            return


def _run_system_check(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    db_ok = False
    db_error = None
    try:
        with connect(service.settings) as conn:
            conn.execute("SELECT 1").fetchone()
            db_ok = True
    except Exception as exc:
        db_error = str(exc)

    codex = inspect_codex_runtime(service.settings)
    status_ready = True
    status_error = None
    try:
        current = service.status_tracker.current_state(limit=3)
    except Exception as exc:
        current = None
        status_ready = False
        status_error = str(exc)

    return {
        "summary": "System check completed.",
        "database_ok": db_ok,
        "database_error": db_error,
        "runtime_mode": service.settings.runtime_mode,
        "codex_available": bool(codex.get("available")),
        "status_tracker_ready": status_ready,
        "status_tracker_error": status_error,
        "path_policy": describe_path_policy(service.settings),
        "current_state": current,
    }


def _run_codex_doctor(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    report = inspect_codex_runtime(service.settings)
    return {
        "summary": "Codex check completed." if report.get("available") else "Codex check completed; Codex is not available.",
        "report": report,
    }


def _run_status_summary(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    current = service.status_tracker.current_state(limit=5)
    latest = current.get("latest_update") or {}
    return {
        "summary": "Current state read.",
        "latest_summary": latest.get("summary") or "No status updates recorded yet.",
        "current_state": current,
    }


def _run_dashboard_status(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    host = str(payload.get("host") or "127.0.0.1")
    port = int(payload.get("port") or 8787)
    status = dashboard_status(host, port, settings=service.settings)
    return {
        "summary": status["summary"],
        "dashboard": status,
    }


def _run_path_policy_status(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    policy = describe_path_policy(service.settings)
    return {
        "summary": "Path policy loaded.",
        "path_policy": policy,
    }


def _run_open_dashboard(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    host = str(payload.get("host") or "127.0.0.1")
    port = int(payload.get("port") or 8787)
    return open_dashboard(host, port, settings=service.settings)


def _run_init_status_tracker(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    record = initialize_status_tracker(service.settings, actor="arceus_dashboard")
    return {
        "summary": "Status tracker initialized.",
        "status_update": record,
    }


def _run_install_mac_launcher(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    app_path = str(payload.get("app_path") or "").strip() or None
    return install_mac_launcher(service.settings, app_path=app_path)


def _run_latest_handoff(service: LocalControlService, payload: dict[str, Any]) -> dict[str, Any]:
    handoff_id = str(payload.get("handoff_id") or "").strip()
    store = ConversationStore(service.settings)
    if not handoff_id:
        handoffs = store.list_handoffs(limit=20)
        runnable = next((handoff for handoff in handoffs if handoff.get("status") in {"drafted", "failed"}), None)
        if runnable:
            handoff_id = str(runnable["id"])

    if not handoff_id:
        raise ValueError("No drafted or failed Codex handoff is available to run.")

    try:
        result = start_handoff_codex_run(service.settings, handoff_id)
    except CodexRunError as exc:
        raise ValueError(str(exc)) from exc

    return {
        "summary": str(result.get("message") or "Codex handoff run requested."),
        "handoff_id": handoff_id,
        "codex_result": result,
    }


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, (UUID, Path)):
        return str(value)
    return value


def _memory_note(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(_json_safe(value), ensure_ascii=True)
    except TypeError:
        return str(value)
