from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from arceus.config import Settings
from arceus.path_policy import describe_path_policy, ensure_read_allowed, ensure_write_allowed


SKIP_DIRS = {
    ".arceus-state",
    ".codex",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".pycache",
    ".ruff_cache",
    ".venv",
    "Arceus Dashboard.app",
    "__pycache__",
    "artifacts",
    "exports",
    "local-data",
    "node_modules",
    "output",
    "outputs",
    "test-results",
    "tmp",
}
SKIP_FILES = {".DS_Store"}
PROPOSAL_DIR = Path(".arceus-state") / "filesystem-agent" / "proposals"


@dataclass(frozen=True)
class FilesystemAgent:
    settings: Settings

    def inspect(self, path: str = ".", max_depth: int = 3, max_entries: int = 120) -> dict[str, Any]:
        root = ensure_read_allowed(self.settings, _resolve_user_path(self.settings, path))
        max_depth = max(0, min(int(max_depth), 8))
        max_entries = max(1, min(int(max_entries), 500))

        if root.is_file():
            file_summary = self.read_file(path, max_bytes=2400)
            return {
                "summary": f"Inspected file {root.name}.",
                "kind": "file",
                "root": str(root),
                "file": file_summary,
                "path_policy": describe_path_policy(self.settings),
            }

        if not root.exists():
            raise FileNotFoundError(f"Path does not exist: {root}")
        if not root.is_dir():
            raise ValueError(f"Path is neither a file nor directory: {root}")

        entries: list[dict[str, Any]] = []
        counts = {"files": 0, "dirs": 0, "skipped": 0}
        truncated = False

        def walk(directory: Path, depth: int) -> None:
            nonlocal truncated
            if truncated:
                return
            try:
                children = sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
            except OSError:
                counts["skipped"] += 1
                return

            for child in children:
                if len(entries) >= max_entries:
                    truncated = True
                    return
                if child.name in SKIP_FILES or (child.is_dir() and child.name in SKIP_DIRS):
                    counts["skipped"] += 1
                    continue

                try:
                    resolved = ensure_read_allowed(self.settings, child)
                except PermissionError:
                    counts["skipped"] += 1
                    continue

                try:
                    is_dir = resolved.is_dir()
                    stat = resolved.stat()
                except OSError:
                    counts["skipped"] += 1
                    continue

                entry = {
                    "path": _display_path(self.settings, resolved),
                    "name": resolved.name,
                    "kind": "dir" if is_dir else "file",
                    "depth": depth,
                    "size_bytes": None if is_dir else stat.st_size,
                }
                entries.append(entry)
                counts["dirs" if is_dir else "files"] += 1

                if is_dir and depth < max_depth:
                    walk(resolved, depth + 1)

        walk(root, 0)
        return {
            "summary": f"Inspected {counts['files']} file(s) and {counts['dirs']} folder(s) under {_display_path(self.settings, root)}.",
            "kind": "directory",
            "root": str(root),
            "display_root": _display_path(self.settings, root),
            "counts": counts,
            "truncated": truncated,
            "max_depth": max_depth,
            "max_entries": max_entries,
            "entries": entries,
            "path_policy": describe_path_policy(self.settings),
        }

    def read_file(self, path: str, max_bytes: int = 12000) -> dict[str, Any]:
        target = ensure_read_allowed(self.settings, _resolve_user_path(self.settings, path))
        max_bytes = max(1, min(int(max_bytes), 50000))
        if not target.exists():
            raise FileNotFoundError(f"File does not exist: {target}")
        if not target.is_file():
            raise ValueError(f"Path is not a file: {target}")

        data = target.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        binary = _looks_binary(data[:4096])
        preview = ""
        truncated = len(data) > max_bytes
        if not binary:
            preview = data[:max_bytes].decode("utf-8", errors="replace")

        return {
            "summary": f"Read {_display_path(self.settings, target)}.",
            "path": str(target),
            "display_path": _display_path(self.settings, target),
            "size_bytes": len(data),
            "sha256": digest,
            "binary": binary,
            "truncated": truncated,
            "preview": preview,
        }

    def draft_change(
        self,
        path: str,
        intent: str,
        proposed_content: str | None = None,
        mode: str = "replace",
    ) -> dict[str, Any]:
        if mode != "replace":
            raise ValueError("Filesystem Agent v0 only supports full-file replacement proposals.")
        if not intent.strip():
            raise ValueError("Change intent is required.")

        target = ensure_write_allowed(self.settings, _resolve_user_path(self.settings, path))
        current_sha = None
        if target.exists() and target.is_file():
            current_sha = hashlib.sha256(target.read_bytes()).hexdigest()
        elif target.exists():
            raise ValueError(f"Target exists but is not a file: {target}")

        proposal_id = str(uuid4())
        created_at = datetime.now(timezone.utc).astimezone().isoformat()
        proposal = {
            "id": proposal_id,
            "status": "drafted",
            "agent": "filesystem_code",
            "mode": mode,
            "target_path": str(target),
            "display_target_path": _display_path(self.settings, target),
            "intent": intent.strip(),
            "current_sha256": current_sha,
            "proposed_content": proposed_content,
            "created_at": created_at,
            "updated_at": created_at,
            "requires_approval": True,
            "approval_token": "apply_filesystem_proposal",
        }
        proposal_path = _proposal_json_path(self.settings, proposal_id)
        proposal_note_path = _proposal_note_path(self.settings, proposal_id)
        proposal_path.parent.mkdir(parents=True, exist_ok=True)
        proposal_path.write_text(json.dumps(proposal, indent=2, sort_keys=True), encoding="utf-8")
        proposal_note_path.write_text(_render_proposal_note(proposal), encoding="utf-8")

        return {
            "summary": f"Drafted file change proposal for {_display_path(self.settings, target)}.",
            "proposal": _without_large_content(proposal),
            "proposal_path": str(proposal_path),
            "proposal_note_path": str(proposal_note_path),
        }

    def list_proposals(self, limit: int = 20) -> dict[str, Any]:
        proposal_dir = _proposal_dir(self.settings)
        proposals: list[dict[str, Any]] = []
        if proposal_dir.exists():
            for path in sorted(proposal_dir.glob("*.json"), reverse=True)[: max(1, min(limit, 100))]:
                try:
                    proposal = json.loads(path.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                proposals.append(_without_large_content(proposal))
        return {
            "summary": f"Found {len(proposals)} filesystem proposal(s).",
            "proposals": proposals,
        }

    def get_proposal(self, proposal_id: str, include_content: bool = False) -> dict[str, Any]:
        proposal = _load_proposal(self.settings, proposal_id)
        return proposal if include_content else _without_large_content(proposal)

    def apply_proposal(self, proposal_id: str) -> dict[str, Any]:
        proposal = _load_proposal(self.settings, proposal_id)
        if proposal.get("status") != "drafted":
            raise ValueError(f"Proposal is not drafted: {proposal.get('status')}")

        target = ensure_write_allowed(self.settings, proposal["target_path"])
        ensure_write_allowed(self.settings, target.parent)
        proposed_content = proposal.get("proposed_content")
        if proposed_content is None:
            raise ValueError("Proposal has no proposed content to apply.")

        expected_sha = proposal.get("current_sha256")
        if target.exists():
            if not target.is_file():
                raise ValueError(f"Target exists but is not a file: {target}")
            current_sha = hashlib.sha256(target.read_bytes()).hexdigest()
            if expected_sha and current_sha != expected_sha:
                raise ValueError("Target file changed since proposal was drafted. Reinspect before applying.")

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(proposed_content), encoding="utf-8")
        new_sha = hashlib.sha256(target.read_bytes()).hexdigest()

        applied_at = datetime.now(timezone.utc).astimezone().isoformat()
        proposal["status"] = "applied"
        proposal["updated_at"] = applied_at
        proposal["applied_at"] = applied_at
        proposal["new_sha256"] = new_sha
        proposal_path = _proposal_json_path(self.settings, proposal_id)
        proposal_path.write_text(json.dumps(proposal, indent=2, sort_keys=True), encoding="utf-8")
        _proposal_note_path(self.settings, proposal_id).write_text(_render_proposal_note(proposal), encoding="utf-8")

        return {
            "summary": f"Applied file change proposal to {_display_path(self.settings, target)}.",
            "proposal": _without_large_content(proposal),
            "target_path": str(target),
            "new_sha256": new_sha,
        }


def _resolve_user_path(settings: Settings, path: str | Path) -> Path:
    raw = Path(path or ".").expanduser()
    if raw.is_absolute():
        return raw.resolve(strict=False)
    return (settings.root / raw).resolve(strict=False)


def _display_path(settings: Settings, path: Path) -> str:
    try:
        return str(path.relative_to(settings.root))
    except ValueError:
        return str(path)


def _proposal_dir(settings: Settings) -> Path:
    return ensure_write_allowed(settings, settings.root / PROPOSAL_DIR)


def _proposal_json_path(settings: Settings, proposal_id: str) -> Path:
    safe_id = str(UUID(str(proposal_id)))
    return ensure_write_allowed(settings, _proposal_dir(settings) / f"{safe_id}.json")


def _proposal_note_path(settings: Settings, proposal_id: str) -> Path:
    safe_id = str(UUID(str(proposal_id)))
    return ensure_write_allowed(settings, _proposal_dir(settings) / f"{safe_id}.md")


def _load_proposal(settings: Settings, proposal_id: str) -> dict[str, Any]:
    path = _proposal_json_path(settings, proposal_id)
    if not path.exists():
        raise FileNotFoundError(f"No filesystem proposal found with id {proposal_id}.")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Proposal file is malformed.")
    return data


def _looks_binary(data: bytes) -> bool:
    return b"\x00" in data


def _without_large_content(proposal: dict[str, Any]) -> dict[str, Any]:
    safe = dict(proposal)
    content = safe.pop("proposed_content", None)
    safe["has_proposed_content"] = content is not None
    if isinstance(content, str):
        safe["proposed_content_chars"] = len(content)
    return safe


def _render_proposal_note(proposal: dict[str, Any]) -> str:
    return "\n".join(
        [
            "---",
            "type: arceus_filesystem_proposal",
            f"id: {proposal.get('id')}",
            f"status: {proposal.get('status')}",
            f"target_path: {proposal.get('target_path')}",
            f"created_at: {proposal.get('created_at')}",
            f"updated_at: {proposal.get('updated_at')}",
            "---",
            "",
            f"# Filesystem Proposal: {proposal.get('display_target_path')}",
            "",
            f"- Status: {proposal.get('status')}",
            f"- Mode: {proposal.get('mode')}",
            f"- Requires approval: {proposal.get('requires_approval')}",
            f"- Approval token: `{proposal.get('approval_token')}`",
            f"- Current SHA-256: `{proposal.get('current_sha256') or 'new file'}`",
            f"- New SHA-256: `{proposal.get('new_sha256') or ''}`",
            "",
            "## Intent",
            "",
            str(proposal.get("intent") or ""),
            "",
        ]
    )
