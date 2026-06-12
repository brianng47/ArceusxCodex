from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any

from arceus.config import Settings
from arceus.path_policy import ensure_read_allowed, ensure_write_allowed


WIKI_DIR = Path("wiki")
RAW_DIR = Path("raw")
INDEX_PATH = WIKI_DIR / "index.md"
LOG_PATH = WIKI_DIR / "log.md"
HOT_PATH = WIKI_DIR / "hot.md"
AUDITS_DIR = WIKI_DIR / "audits"

REQUIRED_DIRECTORIES = (
    RAW_DIR,
    WIKI_DIR,
    AUDITS_DIR,
    WIKI_DIR / "people",
    WIKI_DIR / "projects",
    WIKI_DIR / "preferences",
    WIKI_DIR / "workflows",
    WIKI_DIR / "sources",
    WIKI_DIR / "analyses",
    WIKI_DIR / "system",
)


@dataclass(frozen=True)
class WikiPageSpec:
    path: str
    title: str
    body: str
    tags: tuple[str, ...] = ()
    sources: tuple[str, ...] = ()
    related: tuple[str, ...] = ()


class VaultMemoryError(RuntimeError):
    pass


class VaultMemory:
    def __init__(self, settings: Settings):
        if settings.obsidian_vault_path is None:
            raise VaultMemoryError("Obsidian vault path is not configured.")
        self.settings = settings
        self.vault = settings.obsidian_vault_path

    def ensure_structure(self) -> dict[str, Any]:
        ensure_write_allowed(self.settings, self.vault)
        created_dirs: list[str] = []
        created_files: list[str] = []

        for relative_dir in REQUIRED_DIRECTORIES:
            directory = ensure_write_allowed(self.settings, self.vault / relative_dir)
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(relative_dir))

        default_files = {
            Path("CLAUDE.md"): _root_claude(),
            Path("AGENTS.md"): _root_agents(),
            INDEX_PATH: _default_index(),
            LOG_PATH: _default_log(),
            HOT_PATH: _default_hot(),
        }
        for relative_path, content in default_files.items():
            path = ensure_write_allowed(self.settings, self.vault / relative_path)
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                created_files.append(str(relative_path))

        return {
            "ok": True,
            "summary": "Vault LLM-wiki structure is ready.",
            "vault_path": str(self.vault),
            "created_dirs": created_dirs,
            "created_files": created_files,
            "index_path": str(self.vault / INDEX_PATH),
            "hot_path": str(self.vault / HOT_PATH),
            "log_path": str(self.vault / LOG_PATH),
        }

    def read_context(self) -> dict[str, Any]:
        map_path = ensure_read_allowed(self.settings, self.vault / "CLAUDE.md")
        index_path = ensure_read_allowed(self.settings, self.vault / INDEX_PATH)
        hot_path = ensure_read_allowed(self.settings, self.vault / HOT_PATH)
        current_state_path = self.vault / "Arceus" / "00_System" / "Current State.md"
        current_state = ""
        if current_state_path.exists():
            current_state = ensure_read_allowed(self.settings, current_state_path).read_text(encoding="utf-8")

        return {
            "summary": "Vault memory context loaded.",
            "vault_path": str(self.vault),
            "map_path": str(map_path),
            "index_path": str(index_path),
            "hot_path": str(hot_path),
            "map": map_path.read_text(encoding="utf-8"),
            "index": index_path.read_text(encoding="utf-8"),
            "hot": hot_path.read_text(encoding="utf-8"),
            "current_state": current_state,
        }

    def upsert_page(self, spec: WikiPageSpec, operation: str = "update") -> dict[str, Any]:
        relative_path = _normalize_wiki_path(spec.path)
        path = ensure_write_allowed(self.settings, self.vault / relative_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        previous = path.read_text(encoding="utf-8") if path.exists() else None
        content = _render_page(spec)
        path.write_text(content, encoding="utf-8")

        self._ensure_index_entry(relative_path, spec.title)
        self.append_log(operation, f"{spec.title}: {relative_path}")

        return {
            "ok": True,
            "summary": "Vault wiki page updated.",
            "path": str(path),
            "relative_path": str(relative_path),
            "created": previous is None,
        }

    def append_log(self, operation: str, summary: str) -> dict[str, Any]:
        log_path = ensure_write_allowed(self.settings, self.vault / LOG_PATH)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.write_text(_default_log(), encoding="utf-8")

        entry = f"\n## [{date.today().isoformat()}] {operation} | {summary.strip()}\n"
        with log_path.open("a", encoding="utf-8") as handle:
            handle.write(entry)
        return {"ok": True, "summary": "Vault log updated.", "path": str(log_path)}

    def refresh_hot(self, sections: dict[str, str]) -> dict[str, Any]:
        hot_path = ensure_write_allowed(self.settings, self.vault / HOT_PATH)
        hot_path.parent.mkdir(parents=True, exist_ok=True)
        existing = hot_path.read_text(encoding="utf-8") if hot_path.exists() else _default_hot()
        updated = existing
        for heading, body in sections.items():
            updated = _replace_or_append_section(updated, heading, body.strip())
        updated = _replace_or_append_section(updated, "Last updated", date.today().isoformat())
        hot_path.write_text(updated, encoding="utf-8")
        self.append_log("update", "Refreshed hot context")
        return {"ok": True, "summary": "Hot context refreshed.", "path": str(hot_path)}

    def audit(self) -> dict[str, Any]:
        self.ensure_structure()
        markdown_files = []
        for path in (self.vault / WIKI_DIR).rglob("*.md"):
            if not path.is_file():
                continue
            relative = path.relative_to(self.vault)
            if relative == LOG_PATH or relative.parts[:2] == AUDITS_DIR.parts:
                continue
            markdown_files.append(path)
        index_links = _wiki_links((self.vault / INDEX_PATH).read_text(encoding="utf-8"))
        page_targets = {_link_target(path.relative_to(self.vault)) for path in markdown_files}

        orphan_pages: list[str] = []
        missing_index_entries: list[str] = []
        missing_links: list[str] = []
        stale_claims: list[str] = []

        for path in markdown_files:
            relative = path.relative_to(self.vault)
            target = _link_target(relative)
            if relative not in {INDEX_PATH, HOT_PATH} and target not in index_links:
                missing_index_entries.append(str(relative))
            text = path.read_text(encoding="utf-8")
            for link in _wiki_links(text):
                if link not in page_targets and link not in index_links:
                    missing_links.append(f"{relative}: [[{link}]]")
            if relative not in {INDEX_PATH, HOT_PATH} and not _has_backlink(target, markdown_files, self.vault):
                orphan_pages.append(str(relative))
            if re.search(r"\bTODO\b|\bTBD\b|\bstale\b", text, flags=re.IGNORECASE):
                stale_claims.append(str(relative))

        issues = {
            "missing_index_entries": sorted(set(missing_index_entries)),
            "missing_links": sorted(set(missing_links)),
            "orphan_pages": sorted(set(orphan_pages)),
            "stale_claims": sorted(set(stale_claims)),
            "contradictions": [],
            "data_gaps": [],
        }
        issue_count = sum(len(value) for value in issues.values())
        report = _render_audit_report(issues, issue_count)
        stamp = datetime.now().strftime("%Y-%m-%d-%H%M%S")
        report_path = ensure_write_allowed(self.settings, self.vault / AUDITS_DIR / f"{stamp}-audit.md")
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")
        self.append_log("audit", f"Audit-only self-heal found {issue_count} issue(s)")

        return {
            "ok": True,
            "summary": f"Audit-only self-heal completed with {issue_count} issue(s).",
            "issue_count": issue_count,
            "issues": issues,
            "report_path": str(report_path),
        }

    def _ensure_index_entry(self, relative_path: Path, title: str) -> None:
        index_path = ensure_write_allowed(self.settings, self.vault / INDEX_PATH)
        if not index_path.exists():
            index_path.write_text(_default_index(), encoding="utf-8")
        text = index_path.read_text(encoding="utf-8")
        link = _link_target(relative_path)
        if f"[[{link}]]" in text:
            return
        section = _section_for(relative_path)
        entry = f"- [[{link}]] - {title}"
        text = _append_to_section(text, section, entry)
        index_path.write_text(text, encoding="utf-8")


def _normalize_wiki_path(path: str) -> Path:
    relative = Path(path)
    if relative.is_absolute():
        raise VaultMemoryError("Wiki page path must be relative.")
    if relative.parts and relative.parts[0] == "wiki":
        normalized = relative
    else:
        normalized = WIKI_DIR / relative
    if normalized.suffix != ".md":
        normalized = normalized.with_suffix(".md")
    if ".." in normalized.parts:
        raise VaultMemoryError("Wiki page path cannot contain '..'.")
    return normalized


def _render_page(spec: WikiPageSpec) -> str:
    sources = "\n".join(f"  - {source}" for source in spec.sources)
    related = ", ".join(f"[[{link}]]" for link in spec.related)
    tags = ", ".join(spec.tags)
    return "\n".join(
        [
            "---",
            f"title: {spec.title}",
            f"tags: [{tags}]",
            "sources:",
            sources or "  []",
            f"related: {related}" if related else "related: []",
            f"last_updated: {date.today().isoformat()}",
            "---",
            "",
            f"# {spec.title}",
            "",
            spec.body.strip(),
            "",
        ]
    )


def _replace_or_append_section(text: str, heading: str, body: str) -> str:
    title = heading.strip().lstrip("#").strip()
    pattern = re.compile(rf"(^## {re.escape(title)}\n)(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    replacement = f"## {title}\n\n{body}\n\n"
    if pattern.search(text):
        return pattern.sub(replacement, text, count=1)
    return text.rstrip() + "\n\n" + replacement


def _append_to_section(text: str, heading: str, entry: str) -> str:
    pattern = re.compile(rf"(^## {re.escape(heading)}\n)(.*?)(?=^## |\Z)", re.MULTILINE | re.DOTALL)
    match = pattern.search(text)
    if not match:
        return text.rstrip() + f"\n\n## {heading}\n\n{entry}\n"
    section = match.group(2).rstrip()
    if "- No pages yet." in section:
        section = section.replace("- No pages yet.", "").strip()
    updated = (section + "\n" + entry).strip() + "\n\n"
    return text[: match.start(2)] + updated + text[match.end(2) :]


def _section_for(relative_path: Path) -> str:
    parts = relative_path.parts
    if len(parts) > 1 and parts[0] == "wiki":
        folder = parts[1]
        return {
            "people": "People",
            "projects": "Projects",
            "preferences": "Preferences",
            "workflows": "Workflows",
            "sources": "Sources",
            "analyses": "Analyses",
            "system": "System",
            "audits": "Audits",
        }.get(folder, "System")
    return "System"


def _wiki_links(text: str) -> set[str]:
    return {_normalize_link(match.split("|", 1)[0].strip()) for match in re.findall(r"\[\[([^\]]+)\]\]", text)}


def _normalize_link(link: str) -> str:
    while link.startswith("../"):
        link = link[3:]
    return link.strip("/")


def _link_target(relative_path: Path) -> str:
    path = relative_path.with_suffix("")
    parts = path.parts
    if parts and parts[0] == "wiki":
        return "/".join(parts[1:])
    return "/".join(parts)


def _has_backlink(target: str, markdown_files: list[Path], vault: Path) -> bool:
    needle = f"[[{target}]]"
    basename_needle = f"[[{target.rsplit('/', 1)[-1]}]]"
    for path in markdown_files:
        if _link_target(path.relative_to(vault)) == target:
            continue
        text = path.read_text(encoding="utf-8")
        if needle in text or basename_needle in text:
            return True
    return False


def _render_audit_report(issues: dict[str, list[str]], issue_count: int) -> str:
    lines = [
        "---",
        "title: Vault Audit",
        "tags: [audit, arceus, memory]",
        f"last_updated: {date.today().isoformat()}",
        "---",
        "",
        "# Vault Audit",
        "",
        f"Audit-only self-heal found {issue_count} issue(s).",
        "",
    ]
    for label, values in issues.items():
        lines.extend([f"## {label.replace('_', ' ').title()}", ""])
        if not values:
            lines.append("- None")
        else:
            lines.extend(f"- {value}" for value in values)
        lines.append("")
    return "\n".join(lines)


def _root_claude() -> str:
    return """# Vault LLM-Wiki Map

This Obsidian vault is Brian's personal memory layer for Arceus.

Read `wiki/index.md`, then `wiki/hot.md`, then the specific linked pages needed
for the task. Do not modify `raw/` sources. Destructive edits require explicit
approval.
"""


def _root_agents() -> str:
    return """# Vault Agent Instructions

Read `CLAUDE.md` first for vault-wide memory work.

Use `wiki/index.md` as the routing table, `wiki/hot.md` as fast current
context, and `wiki/log.md` as the operation timeline.
"""


def _default_index() -> str:
    return """# Vault Wiki Index

## Start Here

- [[hot]] - Rolling current context.

## People

- No pages yet.

## Projects

- No pages yet.

## Preferences

- No pages yet.

## Workflows

- No pages yet.

## Sources

- No pages yet.

## Analyses

- No pages yet.

## System

- No pages yet.

## Audits

- No audits yet.
"""


def _default_log() -> str:
    return f"""# Vault Wiki Log

Every durable memory operation appends exactly one dated entry.

## [{date.today().isoformat()}] init | Vault log initialized
"""


def _default_hot() -> str:
    return f"""# Hot Context

Purpose: compact rolling context for fast Arceus responses.

## Last updated

{date.today().isoformat()}

## Active Roadmap

Arceus is Jarvis OS-first.
"""
