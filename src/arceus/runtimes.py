from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional, Protocol

from arceus.config import Settings
from arceus.conversation import MessageRow
from arceus.path_policy import ensure_write_allowed
from arceus.prompts import ARCEUS_RUNTIME_INSTRUCTIONS


CODEX_WORTHY_TERMS = (
    "implement",
    "build",
    "code",
    "edit",
    "fix",
    "bug",
    "refactor",
    "test",
    "ui",
    "dashboard",
    "database",
    "migration",
    "script",
    "agent",
    "runtime",
    "codex",
    "file",
    "repo",
)


@dataclass(frozen=True)
class RuntimeResponse:
    runtime: str
    content: str
    handoff_prompt: Optional[str] = None


class ArceusRuntime(Protocol):
    name: str

    def respond(self, user_message: str, history: Iterable[MessageRow]) -> RuntimeResponse:
        ...


class OfflineRuntime:
    name = "offline"

    def respond(self, user_message: str, history: Iterable[MessageRow]) -> RuntimeResponse:
        history_count = len(list(history))
        lowered = user_message.lower()

        if _looks_codex_worthy(user_message):
            return RuntimeResponse(
                runtime=self.name,
                content=(
                    "This is Codex-worthy, but Arceus is currently in `offline` mode. Set "
                    "`ARCEUS_RUNTIME_MODE=codex_manual` in `.env`, restart chat, and I will "
                    "draft the handoff packet. Tiny config altar, large consequence."
                ),
            )

        if any(word in lowered for word in ("hello", "hi", "hey")):
            content = (
                "I am awake. Still local, still young, but functional enough to be useful. "
                "Bring me a thought and I will help sharpen it."
            )
        elif "queue" in lowered or "task" in lowered:
            content = (
                "The queue is plumbing, not personality. Useful plumbing, admittedly. We will "
                "keep it under the floorboards where it belongs."
            )
        elif "idea" in lowered or "think" in lowered or "strategy" in lowered:
            content = (
                "Good. Give me the idea. I will test the premise, find the weak joints, and "
                "try not to be too smug if one snaps."
            )
        else:
            content = (
                "I can hold the conversation shell now, but no live agent runtime is driving "
                "this reply. Use `codex_manual` when you want me to prepare supervised Codex "
                f"handoffs. For now, this is recorded as turn {history_count + 1}."
            )

        return RuntimeResponse(runtime=self.name, content=content)


class CodexManualRuntime:
    name = "codex_manual"

    def __init__(self, settings: Settings):
        self.settings = settings

    def respond(self, user_message: str, history: Iterable[MessageRow]) -> RuntimeResponse:
        if not self._looks_codex_worthy(user_message):
            return RuntimeResponse(
                runtime=self.name,
                content=(
                    "This feels like conversation, not a Codex handoff. Good. Not every thought "
                    "needs to become a ticket with delusions of grandeur. Keep talking, or ask me "
                    "to build/fix/inspect something and I will prepare the handoff."
                ),
            )

        handoff_prompt = self._build_handoff_prompt(user_message, history)
        return RuntimeResponse(
            runtime=self.name,
            content=(
                "I drafted a Codex handoff packet. Run it in Codex manually, then record the "
                "result back here. Supervised first; divine rampage later."
            ),
            handoff_prompt=handoff_prompt,
        )

    def _looks_codex_worthy(self, user_message: str) -> bool:
        return _looks_codex_worthy(user_message)

    def _build_handoff_prompt(
        self,
        user_message: str,
        history: Iterable[MessageRow],
    ) -> str:
        recent_context = []
        for row in list(history)[-6:]:
            role = row["role"]
            content = row["content"].strip()
            if not content:
                continue
            recent_context.append(f"{role}: {content}")

        context_block = "\n".join(recent_context) if recent_context else "No prior session context."

        return f"""# Codex Handoff: Arceus Supervised Runtime

You are Codex working inside the Arceus repository.

## User Intent

{user_message}

## Recent Arceus Context

{context_block}

## Operating Rules

{ARCEUS_RUNTIME_INSTRUCTIONS}

- Follow the repository `AGENTS.md`.
- Keep changes scoped to the user's request.
- Prefer docs and architecture consistency over clever shortcuts.
- Ask before destructive, credential, financial, publishing, or irreversible actions.
- Preserve Arceus' current doctrine: local-first, private fan project, supervised execution first.
- If implementation is unsafe or unclear, explain the blocker instead of forcing it.

## Expected Output Back To Arceus

Return:

- summary of what you did or recommend;
- files changed, if any;
- verification performed;
- unresolved risks or decisions;
- memory-worthy notes Arceus should preserve.
""".strip()


class CodexAppServerRuntime:
    name = "codex_app_server"

    def __init__(self, settings: Settings):
        self.settings = settings

    def respond(self, user_message: str, history: Iterable[MessageRow]) -> RuntimeResponse:
        return RuntimeResponse(
            runtime=self.name,
            content=(
                "Codex app-server mode is reserved but not enabled yet. The protocol is "
                "experimental, so Arceus will use the manual bridge until we prove a stable "
                "request/response path. Sensible, I know. Deeply inconvenient to the drama."
            ),
        )


def get_runtime(settings: Settings) -> ArceusRuntime:
    mode = settings.runtime_mode.lower()

    if mode == "codex_manual":
        return CodexManualRuntime(settings)

    if mode == "codex_app_server":
        return CodexAppServerRuntime(settings)

    return OfflineRuntime()


def _looks_codex_worthy(user_message: str) -> bool:
    lowered = user_message.lower()
    return any(term in lowered for term in CODEX_WORTHY_TERMS)


def inspect_codex_runtime(settings: Settings) -> dict[str, object]:
    configured_path = Path(settings.codex_bin)
    resolved = str(configured_path) if configured_path.exists() else shutil.which("codex")

    report: dict[str, object] = {
        "configured_path": settings.codex_bin,
        "resolved_path": resolved,
        "available": bool(resolved),
        "version": None,
        "app_server_help": None,
        "mcp_server_help": None,
        "claude_code_available": bool(shutil.which("claude")),
    }

    if not resolved:
        return report

    report["version"] = _run_short([resolved, "--version"])
    report["app_server_help"] = _run_short([resolved, "app-server", "--help"])
    report["mcp_server_help"] = _run_short([resolved, "mcp-server", "--help"])
    return report


def inspect_codex_app_server(
    settings: Settings,
    schema_dir: Optional[str] = None,
    include_experimental: bool = True,
) -> dict[str, object]:
    configured_path = Path(settings.codex_bin)
    resolved = str(configured_path) if configured_path.exists() else shutil.which("codex")

    report: dict[str, object] = {
        "configured_path": settings.codex_bin,
        "resolved_path": resolved,
        "available": bool(resolved),
        "direct_bridge_ready": False,
        "active_recommendation": "Keep ARCEUS_RUNTIME_MODE=codex_manual.",
        "status": "codex_missing",
        "cli_version": None,
        "daemon_version": None,
        "daemon_online": False,
        "schema_generation": None,
        "schema_dir": None,
        "schema_file_count": 0,
        "client_methods": [],
        "server_request_methods": [],
        "server_notification_methods": [],
        "approval_request_methods": [],
        "high_power_client_methods": [],
        "readiness_notes": [
            "Direct app-server control stays disabled until Arceus has an approval UI wrapper.",
            "Manual handoff remains the safe runtime because it keeps the human in the loop.",
        ],
        "next_gates": [
            "Prove a minimal JSON-RPC request/response path through the Codex app-server proxy.",
            "Route every Codex approval request into Arceus before allowing writes or commands.",
            "Start with sandboxed or read-only turns before any full laptop-power execution.",
            "Keep codex_manual as a fallback even after direct mode exists.",
        ],
    }

    if not resolved:
        return report

    report["status"] = "schema_not_checked"
    report["cli_version"] = _run_short([resolved, "--version"])
    daemon_version = _run_short([resolved, "app-server", "daemon", "version"])
    report["daemon_version"] = daemon_version
    report["daemon_online"] = bool(daemon_version.get("ok"))

    output_dir = Path(schema_dir) if schema_dir else settings.arceus_state_path / "codex-app-schema"
    output_dir = ensure_write_allowed(settings, output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    command = [resolved, "app-server", "generate-json-schema", "--out", str(output_dir)]
    if include_experimental:
        command.append("--experimental")

    generation = _run_short(command, timeout_seconds=20)
    report["schema_generation"] = generation
    report["schema_dir"] = str(output_dir)

    schema_files = sorted(output_dir.rglob("*.json"))
    report["schema_file_count"] = len(schema_files)

    if not generation["ok"]:
        report["status"] = "schema_generation_failed"
        return report

    client_methods = _extract_request_methods(output_dir / "ClientRequest.json")
    server_request_methods = _extract_request_methods(output_dir / "ServerRequest.json")
    server_notification_methods = _extract_request_methods(output_dir / "ServerNotification.json")

    report["client_methods"] = client_methods
    report["server_request_methods"] = server_request_methods
    report["server_notification_methods"] = server_notification_methods
    report["approval_request_methods"] = [
        method
        for method in server_request_methods
        if "approval" in method.lower() or "elicitation" in method.lower() or "requestuserinput" in method.lower()
    ]
    report["high_power_client_methods"] = [
        method
        for method in client_methods
        if method.startswith(("fs/", "command", "process", "thread/start", "turn/start", "remoteControl"))
    ]

    if client_methods and server_request_methods:
        report["status"] = "protocol_shape_discovered"
        report["readiness_notes"] = [
            "Codex app-server schema generation works on this machine.",
            "The protocol exposes thread and turn control, plus filesystem/command surfaces.",
            "The server can ask the client for approvals, so Arceus must become the approval gate before direct mode.",
            "Direct bridge is feasible to explore, but not safe to activate as the main runtime yet.",
        ]
    else:
        report["status"] = "schema_incomplete"

    return report


def _extract_request_methods(schema_path: Path) -> list[str]:
    if not schema_path.exists():
        return []

    try:
        data = json.loads(schema_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    methods: set[str] = set()
    for option in data.get("oneOf", []):
        if not isinstance(option, dict):
            continue
        properties = option.get("properties", {})
        if not isinstance(properties, dict):
            continue
        method_property = properties.get("method", {})
        if not isinstance(method_property, dict):
            continue
        for value in method_property.get("enum", []):
            if isinstance(value, str):
                methods.add(value)

    return sorted(methods)


def _run_short(command: list[str], timeout_seconds: int = 10) -> dict[str, object]:
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except Exception as exc:
        return {"ok": False, "output": str(exc)}

    output = "\n".join(part for part in (result.stdout, result.stderr) if part).strip()
    return {
        "ok": result.returncode == 0,
        "returncode": result.returncode,
        "output": output[:4000],
    }
