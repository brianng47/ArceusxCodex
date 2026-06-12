from __future__ import annotations

import os
import shlex
import signal
import shutil
import socket
import subprocess
import sys
import time
import webbrowser
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from arceus.config import Settings
from arceus.path_policy import ensure_write_allowed


DEFAULT_STATE_DIR = Path.home() / ".arceus"
DEFAULT_MAC_APP_NAME = "Arceus Dashboard.app"


@dataclass(frozen=True)
class DashboardStatus:
    url: str
    host: str
    port: int
    running: bool
    pid: int | None
    pid_running: bool
    port_open: bool
    log_path: str
    pid_path: str
    summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def dashboard_url(host: str = "127.0.0.1", port: int = 8787) -> str:
    return f"http://{host}:{port}/"


def dashboard_status(
    host: str = "127.0.0.1",
    port: int = 8787,
    settings: Settings | None = None,
) -> dict[str, Any]:
    pid_path = _pid_path(settings)
    log_path = _dashboard_log_path(settings)
    pid = _read_pid(pid_path)
    pid_running = _pid_running(pid) if pid else False
    port_open = _port_open(host, port)
    running = port_open or pid_running
    summary = "Dashboard is running." if running else "Dashboard is not running."
    return DashboardStatus(
        url=dashboard_url(host, port),
        host=host,
        port=port,
        running=running,
        pid=pid,
        pid_running=pid_running,
        port_open=port_open,
        log_path=str(log_path),
        pid_path=str(pid_path),
        summary=summary,
    ).to_dict()


def open_dashboard(
    host: str = "127.0.0.1",
    port: int = 8787,
    settings: Settings | None = None,
) -> dict[str, Any]:
    url = dashboard_url(host, port)
    webbrowser.open(url)
    status = dashboard_status(host, port, settings=settings)
    return {
        "summary": f"Dashboard opened at {url}.",
        "url": url,
        "status": status,
    }


def start_dashboard(
    settings: Settings,
    host: str = "127.0.0.1",
    port: int = 8787,
    open_browser: bool = True,
    timeout_seconds: float = 8.0,
) -> dict[str, Any]:
    before = dashboard_status(host, port, settings=settings)
    if before["running"]:
        if open_browser:
            webbrowser.open(before["url"])
        return {
            "summary": f"Dashboard is already running at {before['url']}.",
            "started": False,
            "status": before,
        }

    _ensure_runtime_dirs(settings)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(settings.root / "src")
    pid_path = _pid_path(settings)
    log_path = _dashboard_log_path(settings)

    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write("\n--- starting Arceus dashboard ---\n")
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "arceus.cli",
                "web",
                "--host",
                host,
                "--port",
                str(port),
            ],
            cwd=str(settings.root),
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            close_fds=True,
            start_new_session=True,
        )

    pid_path.write_text(str(process.pid), encoding="utf-8")

    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        if _port_open(host, port):
            if open_browser:
                webbrowser.open(dashboard_url(host, port))
            status = dashboard_status(host, port, settings=settings)
            return {
                "summary": f"Dashboard started at {status['url']}.",
                "started": True,
                "status": status,
            }
        if process.poll() is not None:
            break
        time.sleep(0.2)

    status = dashboard_status(host, port, settings=settings)
    return {
        "summary": "Dashboard start was requested, but the server did not become reachable in time.",
        "started": False,
        "status": status,
        "log_tail": _tail_log(settings=settings),
    }


def stop_dashboard(
    host: str = "127.0.0.1",
    port: int = 8787,
    settings: Settings | None = None,
) -> dict[str, Any]:
    pid_path = _pid_path(settings)
    pid = _read_pid(pid_path)
    if not pid:
        return {
            "summary": "No dashboard pid file exists. If the dashboard is open, it was started outside the Arceus launcher.",
            "stopped": False,
            "status": dashboard_status(host, port, settings=settings),
        }

    if not _pid_running(pid):
        _clear_pid(pid_path)
        return {
            "summary": "Dashboard pid file was stale and has been cleared.",
            "stopped": False,
            "status": dashboard_status(host, port, settings=settings),
        }

    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if not _pid_running(pid):
            _clear_pid(pid_path)
            return {
                "summary": "Dashboard stopped.",
                "stopped": True,
                "status": dashboard_status(host, port, settings=settings),
            }
        time.sleep(0.2)

    return {
        "summary": "Dashboard stop was requested, but the process is still running.",
        "stopped": False,
        "status": dashboard_status(host, port, settings=settings),
    }


def install_mac_launcher(settings: Settings, app_path: str | None = None) -> dict[str, Any]:
    target = Path(app_path).expanduser() if app_path else settings.root / DEFAULT_MAC_APP_NAME
    target = ensure_write_allowed(settings, target)
    ensure_write_allowed(settings, target.parent)
    target.parent.mkdir(parents=True, exist_ok=True)
    _ensure_runtime_dirs(settings)
    launcher_log_path = _mac_launcher_log_path(settings)

    command = " ".join(
        [
            "cd",
            shlex.quote(str(settings.root)),
            "&&",
            "./scripts/arceus",
            "dashboard",
            "start",
            ">",
            shlex.quote(str(launcher_log_path)),
            "2>&1",
        ]
    )
    raw_shell_event = "\u00abevent sysoexec\u00bb"
    script = f'{raw_shell_event} "{_applescript_string(command)}"'

    if target.exists():
        shutil.rmtree(target)

    completed = subprocess.run(
        ["osacompile", "-o", str(target), "-e", script],
        cwd=str(settings.root),
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout or "osacompile failed.").strip())

    return {
        "summary": f"Arceus Dashboard launcher installed at {target}.",
        "app_path": str(target),
        "launcher_log_path": str(launcher_log_path),
        "opens_terminal": False,
        "next_action": "Double-click the app to start Arceus and open the dashboard without a Terminal window.",
    }


def _ensure_runtime_dirs(settings: Settings | None = None) -> None:
    runtime_dir = _runtime_dir(settings)
    log_dir = _log_dir(settings)
    if settings is not None:
        ensure_write_allowed(settings, runtime_dir)
        ensure_write_allowed(settings, log_dir)
    runtime_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)


def _read_pid(pid_path: Path) -> int | None:
    try:
        raw = pid_path.read_text(encoding="utf-8").strip()
        return int(raw) if raw else None
    except (FileNotFoundError, ValueError):
        return None


def _clear_pid(pid_path: Path) -> None:
    try:
        pid_path.unlink()
    except FileNotFoundError:
        return


def _pid_running(pid: int | None) -> bool:
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def _port_open(host: str, port: int) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.35):
            return True
    except OSError:
        return False


def _tail_log(max_chars: int = 2000, settings: Settings | None = None) -> str:
    try:
        text = _dashboard_log_path(settings).read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        return ""
    return text[-max_chars:]


def _applescript_string(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def _state_dir(settings: Settings | None = None) -> Path:
    if settings is None:
        return DEFAULT_STATE_DIR
    return settings.arceus_state_path


def _runtime_dir(settings: Settings | None = None) -> Path:
    return _state_dir(settings) / "runtime"


def _log_dir(settings: Settings | None = None) -> Path:
    return _state_dir(settings) / "logs"


def _pid_path(settings: Settings | None = None) -> Path:
    return _runtime_dir(settings) / "dashboard.pid"


def _dashboard_log_path(settings: Settings | None = None) -> Path:
    return _log_dir(settings) / "dashboard.log"


def _mac_launcher_log_path(settings: Settings | None = None) -> Path:
    return _log_dir(settings) / "mac-launcher.log"
