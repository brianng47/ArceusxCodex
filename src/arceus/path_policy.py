from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from arceus.config import Settings


class PathPolicyError(PermissionError):
    pass


@dataclass(frozen=True)
class PathPolicy:
    read_roots: tuple[Path, ...]
    write_roots: tuple[Path, ...]

    @classmethod
    def from_settings(cls, settings: Settings) -> "PathPolicy":
        return cls(
            read_roots=_normalize_many(settings.allowed_read_paths),
            write_roots=_normalize_many(settings.allowed_write_paths),
        )

    def can_read(self, path: str | Path) -> bool:
        return _is_within_any(_normalize(path), self.read_roots)

    def can_write(self, path: str | Path) -> bool:
        return _is_within_any(_normalize(path), self.write_roots)

    def require_read(self, path: str | Path) -> Path:
        resolved = _normalize(path)
        if not _is_within_any(resolved, self.read_roots):
            raise PathPolicyError(f"Read access denied outside Arceus allowlist: {resolved}")
        return resolved

    def require_write(self, path: str | Path) -> Path:
        resolved = _normalize(path)
        if not _is_within_any(resolved, self.write_roots):
            raise PathPolicyError(f"Write access denied outside Arceus allowlist: {resolved}")
        return resolved

    def describe(self) -> dict[str, Any]:
        return {
            "read_roots": [str(path) for path in self.read_roots],
            "write_roots": [str(path) for path in self.write_roots],
            "summary": "Path policy loaded. Documents-wide access is not in the default allowlist.",
        }


def describe_path_policy(settings: Settings) -> dict[str, Any]:
    return PathPolicy.from_settings(settings).describe()


def ensure_read_allowed(settings: Settings, path: str | Path) -> Path:
    return PathPolicy.from_settings(settings).require_read(path)


def ensure_write_allowed(settings: Settings, path: str | Path) -> Path:
    return PathPolicy.from_settings(settings).require_write(path)


def _normalize(path: str | Path) -> Path:
    return Path(path).expanduser().resolve(strict=False)


def _normalize_many(paths: Iterable[Path]) -> tuple[Path, ...]:
    return tuple(_normalize(path) for path in paths)


def _is_within_any(path: Path, roots: tuple[Path, ...]) -> bool:
    for root in roots:
        if path == root or root in path.parents:
            return True
    return False
