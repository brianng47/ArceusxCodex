from __future__ import annotations

import subprocess
import threading
from pathlib import Path
from typing import Any, Optional

from arceus.config import Settings
from arceus.conversation import ConversationStore
from arceus.path_policy import ensure_write_allowed


class CodexRunError(RuntimeError):
    pass


def run_handoff_with_codex(settings: Settings, handoff_id: str) -> dict[str, Any]:
    store = ConversationStore(settings)
    handoff = store.get_handoff(handoff_id)
    if handoff is None:
        raise CodexRunError(f"No handoff found with id {handoff_id}.")

    status = str(handoff["status"])
    if status == "result_recorded":
        return {
            "ok": True,
            "handoff_id": handoff_id,
            "status": status,
            "message": "Handoff already has a recorded result.",
        }

    if not store.mark_handoff_running(handoff_id):
        refreshed = store.get_handoff(handoff_id)
        return {
            "ok": False,
            "handoff_id": handoff_id,
            "status": refreshed["status"] if refreshed else "unknown",
            "message": "Handoff is not runnable in its current state.",
        }

    return _execute_handoff_with_codex(settings, handoff_id, handoff)


def start_handoff_codex_run(settings: Settings, handoff_id: str) -> dict[str, Any]:
    store = ConversationStore(settings)
    handoff = store.get_handoff(handoff_id)
    if handoff is None:
        raise CodexRunError(f"No handoff found with id {handoff_id}.")

    status = str(handoff["status"])
    if status == "result_recorded":
        return {
            "ok": True,
            "handoff_id": handoff_id,
            "status": status,
            "message": "Handoff already has a recorded result.",
        }
    if status == "running":
        return {
            "ok": True,
            "handoff_id": handoff_id,
            "status": status,
            "message": "Codex autorun is already running.",
        }
    if not store.mark_handoff_running(handoff_id):
        refreshed = store.get_handoff(handoff_id)
        return {
            "ok": False,
            "handoff_id": handoff_id,
            "status": refreshed["status"] if refreshed else "unknown",
            "message": "Handoff is not runnable in its current state.",
        }

    thread = threading.Thread(
        target=_run_background,
        args=(settings, handoff_id, handoff),
        daemon=True,
        name=f"arceus-codex-run-{handoff_id[:8]}",
    )
    thread.start()
    return {
        "ok": True,
        "handoff_id": handoff_id,
        "status": "running",
        "message": "Codex autorun started.",
    }


def _execute_handoff_with_codex(
    settings: Settings,
    handoff_id: str,
    handoff: dict[str, Any],
) -> dict[str, Any]:
    store = ConversationStore(settings)
    run_dir = ensure_write_allowed(settings, settings.root / "outputs" / "codex-runs" / handoff_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    prompt_path = ensure_write_allowed(settings, run_dir / "prompt.md")
    result_path = ensure_write_allowed(settings, run_dir / "result.md")
    stdout_path = ensure_write_allowed(settings, run_dir / "stdout.txt")
    stderr_path = ensure_write_allowed(settings, run_dir / "stderr.txt")

    prompt = str(handoff["handoff_prompt"])
    prompt_path.write_text(prompt, encoding="utf-8")

    command = _build_codex_exec_command(settings, result_path)

    try:
        completed = subprocess.run(
            command,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=settings.codex_timeout_seconds,
            check=False,
        )
    except Exception as exc:
        message = f"Codex autorun could not start: {exc}"
        store.mark_handoff_failed(
            handoff_id,
            result_text=message,
            result_summary="Codex autorun failed to start.",
            memory_summary="A Codex autorun attempt failed before execution.",
        )
        raise CodexRunError(message) from exc

    stdout_path.write_text(completed.stdout or "", encoding="utf-8")
    stderr_path.write_text(completed.stderr or "", encoding="utf-8")

    result_text = _read_text(result_path) or _fallback_output(completed.stdout, completed.stderr)
    result_summary = _summarize_result(result_text, completed.returncode)
    memory_summary = _build_memory_summary(handoff, result_summary)

    if completed.returncode == 0:
        store.record_handoff_result(
            handoff_id,
            result_text=result_text,
            result_summary=result_summary,
            memory_summary=memory_summary,
        )
        return {
            "ok": True,
            "handoff_id": handoff_id,
            "status": "result_recorded",
            "result_summary": result_summary,
            "run_dir": str(run_dir),
        }

    store.mark_handoff_failed(
        handoff_id,
        result_text=result_text,
        result_summary=result_summary,
        memory_summary=memory_summary,
    )
    return {
        "ok": False,
        "handoff_id": handoff_id,
        "status": "failed",
        "result_summary": result_summary,
        "run_dir": str(run_dir),
    }


def _run_background(settings: Settings, handoff_id: str, handoff: dict[str, Any]) -> None:
    try:
        _execute_handoff_with_codex(settings, handoff_id, handoff)
    except Exception:
        # The foreground request already returned; failure details are persisted by
        # _execute_handoff_with_codex where possible. Keep this thread from killing the server.
        return


def _build_codex_exec_command(settings: Settings, result_path: Path) -> list[str]:
    ensure_write_allowed(settings, settings.root)
    ensure_write_allowed(settings, result_path)
    command = [settings.codex_bin]
    command.extend(
        [
            "exec",
        ]
    )
    if settings.codex_skip_git_repo_check:
        command.append("--skip-git-repo-check")
    command.extend(
        [
            "--cd",
            str(settings.root),
            "--sandbox",
            settings.codex_sandbox,
            "--output-last-message",
            str(result_path),
            "-",
        ]
    )
    return command


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _fallback_output(stdout: str, stderr: str) -> str:
    combined = "\n".join(part for part in (stdout, stderr) if part).strip()
    return combined or "Codex produced no final message."


def _summarize_result(result_text: str, returncode: int) -> str:
    prefix = "Codex autorun completed." if returncode == 0 else "Codex autorun failed."
    for line in result_text.splitlines():
        cleaned = line.strip().strip("-").strip()
        if cleaned:
            return f"{prefix} {cleaned[:220]}"
    return prefix


def _build_memory_summary(handoff: dict[str, Any], result_summary: str) -> str:
    intent = str(handoff.get("user_intent") or "unspecified task").strip()
    return f"Automated Codex run for '{intent[:160]}': {result_summary}"
