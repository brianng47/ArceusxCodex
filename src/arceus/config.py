from __future__ import annotations

import os
import socket
from dataclasses import dataclass
from pathlib import Path


DEFAULT_DATABASE_URL = "postgresql://arceus:arceus@localhost:5432/arceus"
DEFAULT_OWNER_ID = "local-user"


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


def get_settings() -> Settings:
    root = Path(__file__).resolve().parents[2]
    load_dotenv(root / ".env")

    hostname = socket.gethostname()
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
    )


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}
