from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, unquote, urlparse

from arceus.codex_runner import start_handoff_codex_run
from arceus.config import Settings
from arceus.conversation import ConversationStore, ConversationTurn
from arceus.dashboard_backbone import DashboardBackbone
from arceus.local_control import LocalControlService
from arceus.queue import json_default
from arceus.runtimes import get_runtime, inspect_codex_app_server, inspect_codex_runtime
from arceus.status import StatusTracker, StatusUpdate


WEB_ROOT = Path(__file__).resolve().parents[2] / "web"


class ArceusWebApp:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.store = ConversationStore(settings)
        self.status_tracker = StatusTracker(settings)
        self.local_control = LocalControlService(settings)
        self.backbone = DashboardBackbone(settings)

    def create_handler(self) -> type[BaseHTTPRequestHandler]:
        app = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "ArceusWeb/0.1"

            def log_message(self, format: str, *args: Any) -> None:
                return

            def do_GET(self) -> None:
                app.handle_get(self)

            def do_POST(self) -> None:
                app.handle_post(self)

        return Handler

    def handle_get(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        path = parsed.path

        if path == "/":
            self._send_file(handler, WEB_ROOT / "index.html")
            return

        if path == "/api/summary":
            params = parse_qs(parsed.query)
            limit = _int_param(params.get("limit"), 5)
            self._send_json(handler, self.store.build_memory_summary(limit))
            return

        if path == "/api/runtime-doctor":
            self._send_json(handler, inspect_codex_runtime(self.settings))
            return

        if path == "/api/app-server-doctor":
            self._send_json(handler, inspect_codex_app_server(self.settings))
            return

        if path == "/api/handoffs":
            params = parse_qs(parsed.query)
            limit = _int_param(params.get("limit"), 20)
            self._send_json(handler, self.store.list_handoffs(limit))
            return

        if path == "/api/status":
            params = parse_qs(parsed.query)
            limit = _int_param(params.get("limit"), 10)
            try:
                self._send_json(handler, self.status_tracker.latest(limit))
            except Exception:
                self._send_json(handler, [])
            return

        if path == "/api/status/current":
            params = parse_qs(parsed.query)
            limit = _int_param(params.get("limit"), 5)
            try:
                self._send_json(handler, self.status_tracker.current_state(limit))
            except Exception:
                self._send_json(
                    handler,
                    {
                        "owner_id": self.settings.owner_id,
                        "obsidian_vault_path": str(self.settings.obsidian_vault_path)
                        if self.settings.obsidian_vault_path
                        else None,
                        "obsidian_current_state_path": None,
                        "latest_update": None,
                        "recent_updates": [],
                        "next_actions": ["Run ./scripts/arceus setup-db to initialize status tracking."],
                        "blockers": ["Status tracker tables are not ready."],
                    },
                )
            return

        if path == "/api/local-actions":
            params = parse_qs(parsed.query)
            limit = _int_param(params.get("limit"), 8)
            self._send_json(
                handler,
                {
                    "actions": self.local_control.catalog(),
                    "recent_runs": self.local_control.recent_runs(limit),
                },
            )
            return

        if path.startswith("/api/zones/"):
            params = parse_qs(parsed.query)
            zone = path.rsplit("/", 1)[-1]
            query = _optional_str((params.get("q") or [""])[0]) or ""
            self._send_json(handler, self.backbone.zone(zone, query=query))
            return

        if path.startswith("/api/projects/"):
            project_slug = unquote(path.rsplit("/", 1)[-1])
            try:
                self._send_json(handler, self.backbone.project_detail(project_slug))
            except KeyError as exc:
                self._send_error(handler, HTTPStatus.NOT_FOUND, str(exc))
            except ValueError as exc:
                self._send_error(handler, HTTPStatus.BAD_REQUEST, str(exc))
            return

        if path.startswith("/api/handoffs/"):
            handoff_id = path.rsplit("/", 1)[-1]
            handoff = self.store.get_handoff(handoff_id)
            if handoff is None:
                self._send_error(handler, HTTPStatus.NOT_FOUND, "No handoff found.")
                return
            self._send_json(handler, handoff)
            return

        safe_path = path.lstrip("/")
        if safe_path.startswith("assets/"):
            self._send_file(handler, WEB_ROOT / safe_path)
            return

        self._send_error(handler, HTTPStatus.NOT_FOUND, "Not found.")

    def handle_post(self, handler: BaseHTTPRequestHandler) -> None:
        parsed = urlparse(handler.path)
        path = parsed.path

        if path == "/api/chat":
            self._with_json_body(handler, self._handle_chat)
            return

        if path == "/api/tasks":
            self._with_json_body(handler, self._handle_create_task)
            return

        if path.startswith("/api/handoffs/") and path.endswith("/result"):
            handoff_id = path.split("/")[-2]
            self._with_json_body(handler, lambda body: self._handle_handoff_result(handoff_id, body))
            return

        if path.startswith("/api/handoffs/") and path.endswith("/run"):
            handoff_id = path.split("/")[-2]
            self._with_json_body(handler, lambda body: self._handle_handoff_run(handoff_id, body))
            return

        if path.startswith("/api/local-actions/") and path.endswith("/run"):
            action_key = path.split("/")[-2]
            self._with_json_body(handler, lambda body: self._handle_local_action_run(action_key, body))
            return

        self._send_error(handler, HTTPStatus.NOT_FOUND, "Not found.")

    def _handle_chat(self, body: dict[str, Any]) -> dict[str, Any]:
        message = str(body.get("message", "")).strip()
        if not message:
            raise ValueError("Message is required.")

        session_id = str(body.get("session_id") or "").strip()
        if not session_id:
            session_id = self.store.create_session("Arceus Dashboard")

        runtime = get_runtime(self.settings)
        history = list(self.store.list_messages(session_id))
        response = runtime.respond(message, history)

        handoff_id = None
        handoff_prompt = response.handoff_prompt
        assistant_message = response.content

        if handoff_prompt:
            handoff_id = self.store.create_runtime_handoff(
                session_id=session_id,
                runtime=response.runtime,
                user_intent=message,
                handoff_prompt=handoff_prompt,
            )
            assistant_message = (
                f"{assistant_message}\n\n"
                f"Handoff ID: {handoff_id}\n\n"
                f"{handoff_prompt}"
            )

        self.store.record_turn(
            ConversationTurn(
                session_id=session_id,
                user_message=message,
                assistant_message=assistant_message,
                runtime=response.runtime,
            )
        )

        return {
            "session_id": session_id,
            "runtime": response.runtime,
            "message": assistant_message,
            "handoff_id": handoff_id,
            "handoff_prompt": handoff_prompt,
        }

    def _handle_handoff_result(self, handoff_id: str, body: dict[str, Any]) -> dict[str, Any]:
        summary = _optional_str(body.get("summary"))
        memory = _optional_str(body.get("memory"))
        result = _optional_str(body.get("result"))

        if not result:
            parts = []
            if summary:
                parts.append(f"Summary: {summary}")
            if memory:
                parts.append(f"Memory: {memory}")
            result = "\n".join(parts)

        if not result:
            raise ValueError("Provide a result, summary, or memory note.")

        recorded = self.store.record_handoff_result(
            handoff_id,
            result_text=result,
            result_summary=summary,
            memory_summary=memory,
        )
        if not recorded:
            raise KeyError("No handoff found.")

        return {"ok": True, "handoff_id": handoff_id}

    def _handle_handoff_run(self, handoff_id: str, body: dict[str, Any]) -> dict[str, Any]:
        confirm = str(body.get("confirm") or "").strip()
        if confirm != "run_codex":
            raise ValueError("Codex autorun requires explicit confirmation.")
        return start_handoff_codex_run(self.settings, handoff_id)

    def _handle_local_action_run(self, action_key: str, body: dict[str, Any]) -> dict[str, Any]:
        confirm = _optional_str(body.get("confirm"))
        payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
        return self.local_control.run(action_key, confirm=confirm, payload=payload)

    def _handle_create_task(self, body: dict[str, Any]) -> dict[str, Any]:
        task = self.backbone.create_task(body)
        project_slug = _optional_str(body.get("project_slug"))
        agent_slug = _optional_str(body.get("agent_slug"))
        try:
            status_update = self.status_tracker.record(
                StatusUpdate(
                    actor="arceus_dashboard",
                    runtime=self.settings.runtime_mode,
                    workstream="Dashboard Tasks",
                    status="created",
                    summary=f"Dashboard task created: {task['title']}",
                    decisions=[
                        "Task was captured in the dashboard as planned work.",
                        "Execution remains approval-gated; creating the task did not run local tools.",
                    ],
                    next_actions=[
                        "Review the task, confirm risk level, and approve execution before local runtime launch.",
                    ],
                    memory_notes=task["summary"],
                    linked_project=project_slug,
                    linked_task=task["slug"],
                    linked_agent=agent_slug,
                    source_type="dashboard_task",
                    source_id=str(task["id"]),
                    metadata={"risk_level": task["risk_level"], "approval_state": task["approval_state"]},
                )
            )
        except Exception as exc:
            status_update = {"error": str(exc)}

        return {"ok": True, "task": task, "status_update": status_update}

    def _with_json_body(
        self,
        handler: BaseHTTPRequestHandler,
        action: Callable[[dict[str, Any]], dict[str, Any]],
    ) -> None:
        try:
            body = self._read_json_body(handler)
            payload = action(body)
        except KeyError as exc:
            self._send_error(handler, HTTPStatus.NOT_FOUND, str(exc))
            return
        except ValueError as exc:
            self._send_error(handler, HTTPStatus.BAD_REQUEST, str(exc))
            return
        except Exception as exc:
            self._send_error(handler, HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return

        self._send_json(handler, payload)

    def _read_json_body(self, handler: BaseHTTPRequestHandler) -> dict[str, Any]:
        length = int(handler.headers.get("Content-Length", "0"))
        raw_body = handler.rfile.read(length).decode("utf-8") if length else "{}"
        data = json.loads(raw_body)
        if not isinstance(data, dict):
            raise ValueError("JSON body must be an object.")
        return data

    def _send_json(
        self,
        handler: BaseHTTPRequestHandler,
        payload: Any,
        status: HTTPStatus = HTTPStatus.OK,
    ) -> None:
        data = json.dumps(payload, default=json_default).encode("utf-8")
        handler.send_response(status)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)

    def _send_error(
        self,
        handler: BaseHTTPRequestHandler,
        status: HTTPStatus,
        message: str,
    ) -> None:
        self._send_json(handler, {"error": message}, status=status)

    def _send_file(self, handler: BaseHTTPRequestHandler, path: Path) -> None:
        try:
            resolved = path.resolve()
            resolved.relative_to(WEB_ROOT.resolve())
        except ValueError:
            self._send_error(handler, HTTPStatus.FORBIDDEN, "Forbidden.")
            return

        if not resolved.exists() or not resolved.is_file():
            self._send_error(handler, HTTPStatus.NOT_FOUND, "Not found.")
            return

        data = resolved.read_bytes()
        content_type = mimetypes.guess_type(str(resolved))[0] or "application/octet-stream"
        handler.send_response(HTTPStatus.OK)
        handler.send_header("Content-Type", content_type)
        handler.send_header("Content-Length", str(len(data)))
        handler.end_headers()
        handler.wfile.write(data)


def serve(settings: Settings, host: str, port: int) -> None:
    app = ArceusWebApp(settings)
    server = ThreadingHTTPServer((host, port), app.create_handler())
    print(f"Arceus dashboard listening at http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nArceus dashboard sealed.")
    finally:
        server.server_close()


def _int_param(value: list[str] | None, default: int) -> int:
    if not value:
        return default
    try:
        return int(value[0])
    except ValueError:
        return default


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
