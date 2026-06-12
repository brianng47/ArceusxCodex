from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_DATABASE_URL = "postgresql://arceus:arceus@localhost:5432/arceus"
DEFAULT_OWNER_ID = "local-user"
DEFAULT_OBSIDIAN_VAULT_PATH = "/Users/brianng/Library/Mobile Documents/iCloud~md~obsidian/Documents"
DEFAULT_ARCEUS_STATE_PATH = ".arceus-state"
DEFAULT_CODEX_HOME_PATH = "~/.codex"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


@dataclass(frozen=True)
class Settings:
    root: Path
    database_url: str
    owner_id: str
    worker_role: str
    worker_id: str
    runtime_mode: str
    codex_bin: str
    codex_sandbox: str
    codex_approval_policy: str
    codex_skip_git_repo_check: bool
    codex_timeout_seconds: int
    obsidian_vault_path: Path | None
    arceus_state_path: Path
    codex_home_path: Path
    allowed_read_paths: tuple[Path, ...]
    allowed_write_paths: tuple[Path, ...]


def get_settings() -> Settings:
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")

    hostname = socket.gethostname()
    obsidian_vault_path = _env_path("OBSIDIAN_VAULT_PATH", DEFAULT_OBSIDIAN_VAULT_PATH)
    arceus_state_path = _state_path(root)
    codex_home_path = _env_path("CODEX_HOME", DEFAULT_CODEX_HOME_PATH) or Path.home() / ".codex"
    allowed_read_paths = _default_read_paths(root, obsidian_vault_path, arceus_state_path, codex_home_path)
    allowed_write_paths = _default_write_paths(root, obsidian_vault_path, arceus_state_path)
    return Settings(
        root=root,
        database_url=os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL),
        owner_id=os.getenv("ARCEUS_OWNER_ID", DEFAULT_OWNER_ID),
        worker_role=os.getenv("ARCEUS_WORKER_ROLE", hostname),
        worker_id=os.getenv("ARCEUS_WORKER_ID", hostname),
        runtime_mode=os.getenv("ARCEUS_RUNTIME_MODE", "offline"),
        codex_bin=os.getenv("ARCEUS_CODEX_BIN", "/Applications/Codex.app/Contents/Resources/codex"),
        codex_sandbox=os.getenv("ARCEUS_CODEX_SANDBOX", "workspace-write"),
        codex_approval_policy=os.getenv("ARCEUS_CODEX_APPROVAL_POLICY", "never"),
        codex_skip_git_repo_check=_env_bool("ARCEUS_CODEX_SKIP_GIT_REPO_CHECK", default=False),
        codex_timeout_seconds=int(os.getenv("ARCEUS_CODEX_TIMEOUT_SECONDS", "1800")),
        obsidian_vault_path=obsidian_vault_path,
        arceus_state_path=arceus_state_path,
        codex_home_path=codex_home_path,
        allowed_read_paths=_append_env_paths(allowed_read_paths, "ARCEUS_EXTRA_READ_PATHS"),
        allowed_write_paths=_append_env_paths(allowed_write_paths, "ARCEUS_EXTRA_WRITE_PATHS"),
    )


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_path(name: str, default: str | None = None) -> Path | None:
    value = os.getenv(name)
    if value is None or not value.strip():
        value = default
    if value is None or not value.strip():
        return None
    return Path(value).expanduser()


def _state_path(root: Path) -> Path:
    value = os.getenv("ARCEUS_STATE_PATH", "").strip()
    if not value:
        return root / DEFAULT_ARCEUS_STATE_PATH
    path = Path(value).expanduser()
    if not path.is_absolute():
        return root / path
    return path


def _default_read_paths(
    root: Path,
    obsidian_vault_path: Path | None,
    arceus_state_path: Path,
    codex_home_path: Path,
) -> tuple[Path, ...]:
    paths: list[Path | None] = [
        root,
        obsidian_vault_path,
        arceus_state_path,
        codex_home_path,
    ]
    return _dedupe_paths(path for path in paths if path is not None)


def _default_write_paths(
    root: Path,
    obsidian_vault_path: Path | None,
    arceus_state_path: Path,
) -> tuple[Path, ...]:
    paths: list[Path | None] = [
        root,
        obsidian_vault_path,
        arceus_state_path,
    ]
    return _dedupe_paths(path for path in paths if path is not None)


def _append_env_paths(base_paths: tuple[Path, ...], env_name: str) -> tuple[Path, ...]:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return base_paths
    extra_paths = [Path(part).expanduser() for part in raw.split(os.pathsep) if part.strip()]
    return _dedupe_paths([*base_paths, *extra_paths])


def _dedupe_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    seen: set[str] = set()
    normalized: list[Path] = []
    for path in paths:
        resolved = path.expanduser().resolve(strict=False)
        key = str(resolved)
        if key in seen:
            continue
        seen.add(key)
        normalized.append(resolved)
    return tuple(normalized)
