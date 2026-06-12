from __future__ import annotations

import re
import uuid
from typing import Any

from psycopg.types.json import Jsonb

from arceus.config import Settings
from arceus.db import connect


class DashboardBackbone:
    def __init__(self, settings: Settings):
        self.settings = settings

    def zone(self, zone: str, query: str = "") -> dict[str, Any]:
        key = zone.strip().lower()
        if key == "chats":
            return self.chats(query=query)
        if key == "agents":
            return self.agents()
        if key == "tasks":
            return self.tasks()
        if key == "workflows":
            return self.workflows()
        if key == "projects":
            return self.projects()
        return {
            "zone": zone,
            "title": "Unknown zone",
            "summary": "This dashboard zone has not been wired yet.",
            "items": [],
        }

    def chats(self, query: str = "", limit: int = 18) -> dict[str, Any]:
        pattern = f"%{query.strip()}%" if query.strip() else None
        where = "session.owner_id = %s"
        params: list[Any] = [self.settings.owner_id]
        if pattern:
            where += """
              AND (
                session.title ILIKE %s
                OR EXISTS (
                    SELECT 1
                    FROM conversation_messages AS search_message
                    WHERE search_message.session_id = session.id
                      AND search_message.content ILIKE %s
                )
              )
            """
            params.extend([pattern, pattern])
        params.append(limit)

        with connect(self.settings) as conn:
            rows = conn.execute(
                f"""
                SELECT
                    session.id,
                    session.title,
                    session.runtime,
                    session.status,
                    session.created_at,
                    session.updated_at,
                    COUNT(DISTINCT message.id) AS message_count,
                    MAX(message.created_at) AS last_message_at,
                    COALESCE(
                        jsonb_agg(
                            DISTINCT jsonb_build_object(
                                'name', tag.name,
                                'color', tag.color
                            )
                        ) FILTER (WHERE tag.id IS NOT NULL),
                        '[]'::jsonb
                    ) AS tags,
                    COALESCE(
                        jsonb_agg(
                            DISTINCT jsonb_build_object(
                                'project', project.name,
                                'task', task.title
                            )
                        ) FILTER (WHERE project.id IS NOT NULL OR task.id IS NOT NULL),
                        '[]'::jsonb
                    ) AS links
                FROM conversation_sessions AS session
                LEFT JOIN conversation_messages AS message
                  ON message.session_id = session.id
                LEFT JOIN conversation_session_tags AS session_tag
                  ON session_tag.session_id = session.id
                LEFT JOIN dashboard_tags AS tag
                  ON tag.id = session_tag.tag_id
                LEFT JOIN dashboard_projects AS project
                  ON project.id = session_tag.linked_project_id
                LEFT JOIN dashboard_tasks AS task
                  ON task.id = session_tag.linked_task_id
                WHERE {where}
                GROUP BY session.id
                ORDER BY session.updated_at DESC
                LIMIT %s
                """,
                tuple(params),
            ).fetchall()

        return {
            "zone": "chats",
            "title": "Chats",
            "summary": "Conversations grouped by recency, with search and tagging hooks ready for project links.",
            "query": query,
            "items": _rows(rows),
        }

    def agents(self) -> dict[str, Any]:
        with connect(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT
                    agent.*,
                    COUNT(task.id) AS task_count,
                    COUNT(task.id) FILTER (
                        WHERE task.status IN ('queued', 'awaiting_approval', 'running')
                    ) AS active_task_count
                FROM dashboard_agents AS agent
                LEFT JOIN dashboard_tasks AS task
                  ON task.agent_id = agent.id
                WHERE agent.owner_id = %s
                GROUP BY agent.id
                ORDER BY
                    CASE agent.status
                        WHEN 'active' THEN 0
                        WHEN 'available' THEN 1
                        WHEN 'planned' THEN 2
                        ELSE 3
                    END,
                    agent.category,
                    agent.name
                """,
                (self.settings.owner_id,),
            ).fetchall()

        return {
            "zone": "agents",
            "title": "Agents",
            "summary": "Specialists are treated as team members: role, trust level, local power, and current load.",
            "items": _rows(rows),
        }

    def tasks(self) -> dict[str, Any]:
        with connect(self.settings) as conn:
            task_rows = conn.execute(
                """
                SELECT
                    task.*,
                    project.name AS project_name,
                    project.slug AS project_slug,
                    agent.name AS agent_name,
                    agent.category AS agent_category
                FROM dashboard_tasks AS task
                LEFT JOIN dashboard_projects AS project
                  ON project.id = task.project_id
                LEFT JOIN dashboard_agents AS agent
                  ON agent.id = task.agent_id
                WHERE task.owner_id = %s
                ORDER BY
                    CASE task.status
                        WHEN 'running' THEN 0
                        WHEN 'awaiting_approval' THEN 1
                        WHEN 'queued' THEN 2
                        WHEN 'planned' THEN 3
                        WHEN 'failed' THEN 4
                        ELSE 5
                    END,
                    task.updated_at DESC
                LIMIT 30
                """,
                (self.settings.owner_id,),
            ).fetchall()
            remote_rows = conn.execute(
                """
                SELECT id, kind, status, worker_role, error_message, created_at, updated_at
                FROM remote_tasks
                WHERE owner_id = %s
                ORDER BY created_at DESC
                LIMIT 8
                """,
                (self.settings.owner_id,),
            ).fetchall()
            local_rows = conn.execute(
                """
                SELECT id, action_key, title, risk_level, status, output_summary, error_message, created_at
                FROM local_action_runs
                WHERE owner_id = %s
                ORDER BY created_at DESC
                LIMIT 8
                """,
                (self.settings.owner_id,),
            ).fetchall()

        return {
            "zone": "tasks",
            "title": "Tasks",
            "summary": "Planned work, approval states, local action runs, and remote queue activity in one view.",
            "items": _rows(task_rows),
            "remote_tasks": _rows(remote_rows),
            "local_runs": _rows(local_rows),
        }

    def workflows(self) -> dict[str, Any]:
        with connect(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT *
                FROM dashboard_workflows
                WHERE owner_id = %s
                ORDER BY
                    CASE status
                        WHEN 'active' THEN 0
                        WHEN 'draft' THEN 1
                        ELSE 2
                    END,
                    updated_at DESC
                """,
                (self.settings.owner_id,),
            ).fetchall()

        return {
            "zone": "workflows",
            "title": "Workflows",
            "summary": "Read-only maps first. Editing comes after the routes are proven and safe.",
            "items": _rows(rows),
        }

    def projects(self) -> dict[str, Any]:
        with connect(self.settings) as conn:
            rows = conn.execute(
                """
                SELECT
                    project.*,
                    COUNT(task.id) AS task_count,
                    COUNT(task.id) FILTER (
                        WHERE task.status IN ('queued', 'awaiting_approval', 'running')
                    ) AS active_task_count,
                    COUNT(task.id) FILTER (WHERE task.status = 'completed') AS completed_task_count
                FROM dashboard_projects AS project
                LEFT JOIN dashboard_tasks AS task
                  ON task.project_id = project.id
                WHERE project.owner_id = %s
                GROUP BY project.id
                ORDER BY
                    CASE project.status
                        WHEN 'active' THEN 0
                        WHEN 'paused' THEN 1
                        ELSE 2
                    END,
                    project.updated_at DESC
                """,
                (self.settings.owner_id,),
            ).fetchall()

        return {
            "zone": "projects",
            "title": "Projects",
            "summary": "Project folders show status, focus, and work currently attached to them.",
            "items": _rows(rows),
        }

    def project_detail(self, slug: str) -> dict[str, Any]:
        safe_slug = slug.strip().lower()
        if not safe_slug:
            raise ValueError("Project slug is required.")

        with connect(self.settings) as conn:
            project = conn.execute(
                """
                SELECT
                    project.*,
                    COUNT(task.id) AS task_count,
                    COUNT(task.id) FILTER (
                        WHERE task.status IN ('queued', 'awaiting_approval', 'running')
                    ) AS active_task_count,
                    COUNT(task.id) FILTER (WHERE task.status = 'completed') AS completed_task_count
                FROM dashboard_projects AS project
                LEFT JOIN dashboard_tasks AS task
                  ON task.project_id = project.id
                WHERE project.owner_id = %s
                  AND project.slug = %s
                GROUP BY project.id
                """,
                (self.settings.owner_id, safe_slug),
            ).fetchone()
            if project is None:
                raise KeyError("No project found.")

            tasks = conn.execute(
                """
                SELECT
                    task.*,
                    agent.name AS agent_name,
                    agent.slug AS agent_slug,
                    agent.category AS agent_category
                FROM dashboard_tasks AS task
                LEFT JOIN dashboard_agents AS agent
                  ON agent.id = task.agent_id
                WHERE task.owner_id = %s
                  AND task.project_id = %s
                ORDER BY
                    CASE task.status
                        WHEN 'running' THEN 0
                        WHEN 'awaiting_approval' THEN 1
                        WHEN 'queued' THEN 2
                        WHEN 'planned' THEN 3
                        WHEN 'failed' THEN 4
                        ELSE 5
                    END,
                    task.updated_at DESC
                """,
                (self.settings.owner_id, project["id"]),
            ).fetchall()
            agents = conn.execute(
                """
                SELECT id, slug, name, role, category, status, trust_level, can_run_local
                FROM dashboard_agents
                WHERE owner_id = %s
                ORDER BY
                    CASE status
                        WHEN 'active' THEN 0
                        WHEN 'available' THEN 1
                        WHEN 'planned' THEN 2
                        ELSE 3
                    END,
                    category,
                    name
                """,
                (self.settings.owner_id,),
            ).fetchall()

        return {
            "project": dict(project),
            "tasks": _rows(tasks),
            "agents": _rows(agents),
        }

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        title = _required_str(data.get("title"), "Task title is required.")
        summary = _optional_str(data.get("summary")) or "No summary provided yet."
        project_slug = _optional_str(data.get("project_slug"))
        agent_slug = _optional_str(data.get("agent_slug"))
        risk_level = _choice(data.get("risk_level"), {"low", "medium", "high"}, "low")
        approval_state = _choice(
            data.get("approval_state"),
            {"not_required", "required", "approved", "declined"},
            "required",
        )
        status = _choice(
            data.get("status"),
            {"planned", "queued", "awaiting_approval", "running", "completed", "failed", "paused"},
            "planned",
        )
        slug = f"{_slugify(title)}-{uuid.uuid4().hex[:8]}"

        with connect(self.settings) as conn:
            with conn.transaction():
                project_id = None
                if project_slug:
                    row = conn.execute(
                        """
                        SELECT id
                        FROM dashboard_projects
                        WHERE owner_id = %s
                          AND slug = %s
                        """,
                        (self.settings.owner_id, project_slug),
                    ).fetchone()
                    if row is None:
                        raise ValueError("Selected project does not exist.")
                    project_id = row["id"]

                agent_id = None
                if agent_slug:
                    row = conn.execute(
                        """
                        SELECT id
                        FROM dashboard_agents
                        WHERE owner_id = %s
                          AND slug = %s
                        """,
                        (self.settings.owner_id, agent_slug),
                    ).fetchone()
                    if row is None:
                        raise ValueError("Selected agent does not exist.")
                    agent_id = row["id"]

                row = conn.execute(
                    """
                    INSERT INTO dashboard_tasks (
                        owner_id,
                        slug,
                        project_id,
                        agent_id,
                        title,
                        status,
                        risk_level,
                        approval_state,
                        summary,
                        metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        self.settings.owner_id,
                        slug,
                        project_id,
                        agent_id,
                        title,
                        status,
                        risk_level,
                        approval_state,
                        summary,
                        Jsonb({"created_from": "dashboard_project_overlay"}),
                    ),
                ).fetchone()

        return dict(row)


def _rows(rows: list[Any]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_str(value: Any, message: str) -> str:
    text = _optional_str(value)
    if text is None:
        raise ValueError(message)
    return text


def _choice(value: Any, allowed: set[str], default: str) -> str:
    text = _optional_str(value) or default
    if text not in allowed:
        allowed_text = ", ".join(sorted(allowed))
        raise ValueError(f"Expected one of: {allowed_text}.")
    return text


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:64].strip("-") or "dashboard-task"
