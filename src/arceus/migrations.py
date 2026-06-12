from __future__ import annotations

from psycopg.types.json import Jsonb

from arceus.config import Settings
from arceus.db import connect


MIGRATION_SQL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS remote_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    worker_role text NOT NULL,
    kind text NOT NULL,
    payload jsonb NOT NULL DEFAULT '{}'::jsonb,
    status text NOT NULL DEFAULT 'pending',
    result jsonb,
    error_message text,
    claimed_by text,
    origin_task_id uuid REFERENCES remote_tasks(id),
    chain_depth integer NOT NULL DEFAULT 0,
    expires_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    claimed_at timestamptz,
    completed_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT remote_tasks_status_check CHECK (
        status IN (
            'pending',
            'claimed',
            'completed',
            'failed',
            'cancelled',
            'expired'
        )
    ),
    CONSTRAINT remote_tasks_chain_depth_check CHECK (chain_depth >= 0)
);

CREATE INDEX IF NOT EXISTS idx_remote_tasks_claim
    ON remote_tasks (worker_role, status, created_at)
    WHERE status = 'pending';

CREATE INDEX IF NOT EXISTS idx_remote_tasks_owner_created
    ON remote_tasks (owner_id, created_at DESC);

CREATE TABLE IF NOT EXISTS remote_task_events (
    id bigserial PRIMARY KEY,
    task_id uuid NOT NULL REFERENCES remote_tasks(id) ON DELETE CASCADE,
    event_type text NOT NULL,
    message text,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_remote_task_events_task
    ON remote_task_events (task_id, created_at);

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'conversation_sessions'
          AND column_name = 'provider'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'conversation_sessions'
          AND column_name = 'runtime'
    ) THEN
        ALTER TABLE conversation_sessions RENAME COLUMN provider TO runtime;
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'conversation_messages'
          AND column_name = 'provider'
    ) AND NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'conversation_messages'
          AND column_name = 'runtime'
    ) THEN
        ALTER TABLE conversation_messages RENAME COLUMN provider TO runtime;
    END IF;
END
$$;

CREATE TABLE IF NOT EXISTS conversation_sessions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    title text NOT NULL DEFAULT 'Arceus Conversation',
    runtime text NOT NULL DEFAULT 'offline',
    status text NOT NULL DEFAULT 'active',
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT conversation_sessions_status_check CHECK (
        status IN ('active', 'archived')
    )
);

CREATE INDEX IF NOT EXISTS idx_conversation_sessions_owner_created
    ON conversation_sessions (owner_id, created_at DESC);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id bigserial PRIMARY KEY,
    session_id uuid NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    role text NOT NULL,
    content text NOT NULL,
    runtime text,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT conversation_messages_role_check CHECK (
        role IN ('system', 'user', 'assistant')
    )
);

CREATE INDEX IF NOT EXISTS idx_conversation_messages_session_created
    ON conversation_messages (session_id, created_at);

CREATE TABLE IF NOT EXISTS avatar_events (
    id bigserial PRIMARY KEY,
    session_id uuid REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    state text NOT NULL,
    message text,
    data jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT avatar_events_state_check CHECK (
        state IN (
            'idle',
            'listening',
            'thinking',
            'speaking',
            'planning',
            'awaiting_approval',
            'executing',
            'remembering',
            'fractured'
        )
    )
);

CREATE INDEX IF NOT EXISTS idx_avatar_events_session_created
    ON avatar_events (session_id, created_at);

CREATE TABLE IF NOT EXISTS runtime_handoffs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    session_id uuid REFERENCES conversation_sessions(id) ON DELETE SET NULL,
    runtime text NOT NULL,
    status text NOT NULL DEFAULT 'drafted',
    user_intent text NOT NULL,
    handoff_prompt text NOT NULL,
    result_summary text,
    result_text text,
    memory_summary text,
    created_at timestamptz NOT NULL DEFAULT now(),
    completed_at timestamptz,
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT runtime_handoffs_status_check CHECK (
        status IN ('drafted', 'result_recorded', 'archived')
    )
);

CREATE INDEX IF NOT EXISTS idx_runtime_handoffs_owner_created
    ON runtime_handoffs (owner_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_runtime_handoffs_session_created
    ON runtime_handoffs (session_id, created_at DESC);

ALTER TABLE runtime_handoffs
    DROP CONSTRAINT IF EXISTS runtime_handoffs_status_check;

ALTER TABLE runtime_handoffs
    ADD CONSTRAINT runtime_handoffs_status_check CHECK (
        status IN ('drafted', 'running', 'result_recorded', 'failed', 'archived')
    );

CREATE TABLE IF NOT EXISTS status_updates (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    actor text NOT NULL,
    runtime text NOT NULL,
    workstream text NOT NULL,
    status text NOT NULL,
    summary text NOT NULL,
    decisions jsonb NOT NULL DEFAULT '[]'::jsonb,
    files_changed jsonb NOT NULL DEFAULT '[]'::jsonb,
    blockers jsonb NOT NULL DEFAULT '[]'::jsonb,
    next_actions jsonb NOT NULL DEFAULT '[]'::jsonb,
    memory_notes text,
    linked_project text,
    linked_task text,
    linked_agent text,
    source_type text,
    source_id text,
    obsidian_path text,
    obsidian_error text,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_status_updates_owner_created
    ON status_updates (owner_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_status_updates_source
    ON status_updates (source_type, source_id);

CREATE INDEX IF NOT EXISTS idx_status_updates_workstream_status
    ON status_updates (owner_id, workstream, status, created_at DESC);

CREATE TABLE IF NOT EXISTS local_action_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    action_key text NOT NULL,
    title text NOT NULL,
    risk_level text NOT NULL,
    approval_required boolean NOT NULL DEFAULT true,
    status text NOT NULL DEFAULT 'requested',
    output_summary text,
    output_data jsonb NOT NULL DEFAULT '{}'::jsonb,
    error_message text,
    approved_at timestamptz,
    started_at timestamptz,
    completed_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT local_action_runs_status_check CHECK (
        status IN ('requested', 'approved', 'running', 'completed', 'failed')
    ),
    CONSTRAINT local_action_runs_risk_check CHECK (
        risk_level IN ('low', 'medium', 'high')
    )
);

CREATE INDEX IF NOT EXISTS idx_local_action_runs_owner_created
    ON local_action_runs (owner_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_local_action_runs_action_status
    ON local_action_runs (owner_id, action_key, status, created_at DESC);

CREATE TABLE IF NOT EXISTS dashboard_projects (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    slug text NOT NULL,
    name text NOT NULL,
    status text NOT NULL DEFAULT 'active',
    summary text NOT NULL,
    focus text NOT NULL DEFAULT '',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (owner_id, slug),
    CONSTRAINT dashboard_projects_status_check CHECK (
        status IN ('active', 'paused', 'completed', 'archived')
    )
);

CREATE INDEX IF NOT EXISTS idx_dashboard_projects_owner_status
    ON dashboard_projects (owner_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS dashboard_agents (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    slug text NOT NULL,
    name text NOT NULL,
    role text NOT NULL,
    category text NOT NULL,
    lore_identity text NOT NULL DEFAULT '',
    status text NOT NULL DEFAULT 'planned',
    trust_level text NOT NULL DEFAULT 'supervised',
    summary text NOT NULL,
    can_run_local boolean NOT NULL DEFAULT false,
    approval_policy text NOT NULL DEFAULT 'ask_before_action',
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (owner_id, slug),
    CONSTRAINT dashboard_agents_status_check CHECK (
        status IN ('active', 'available', 'planned', 'paused', 'retired')
    ),
    CONSTRAINT dashboard_agents_trust_level_check CHECK (
        trust_level IN ('advisory', 'supervised', 'trusted', 'automated')
    )
);

CREATE INDEX IF NOT EXISTS idx_dashboard_agents_owner_category
    ON dashboard_agents (owner_id, category, status);

CREATE TABLE IF NOT EXISTS dashboard_tasks (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    slug text NOT NULL,
    project_id uuid REFERENCES dashboard_projects(id) ON DELETE SET NULL,
    agent_id uuid REFERENCES dashboard_agents(id) ON DELETE SET NULL,
    title text NOT NULL,
    status text NOT NULL DEFAULT 'planned',
    risk_level text NOT NULL DEFAULT 'low',
    approval_state text NOT NULL DEFAULT 'not_required',
    due_at timestamptz,
    summary text NOT NULL,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (owner_id, slug),
    CONSTRAINT dashboard_tasks_status_check CHECK (
        status IN ('planned', 'queued', 'awaiting_approval', 'running', 'completed', 'failed', 'paused')
    ),
    CONSTRAINT dashboard_tasks_risk_level_check CHECK (
        risk_level IN ('low', 'medium', 'high')
    ),
    CONSTRAINT dashboard_tasks_approval_state_check CHECK (
        approval_state IN ('not_required', 'required', 'approved', 'declined')
    )
);

CREATE INDEX IF NOT EXISTS idx_dashboard_tasks_owner_status
    ON dashboard_tasks (owner_id, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_dashboard_tasks_project
    ON dashboard_tasks (project_id, status);

CREATE TABLE IF NOT EXISTS dashboard_workflows (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    slug text NOT NULL,
    name text NOT NULL,
    status text NOT NULL DEFAULT 'draft',
    summary text NOT NULL,
    graph jsonb NOT NULL DEFAULT '{"nodes":[],"edges":[]}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (owner_id, slug),
    CONSTRAINT dashboard_workflows_status_check CHECK (
        status IN ('draft', 'active', 'paused', 'retired')
    )
);

CREATE INDEX IF NOT EXISTS idx_dashboard_workflows_owner_status
    ON dashboard_workflows (owner_id, status, updated_at DESC);

CREATE TABLE IF NOT EXISTS dashboard_tags (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    name text NOT NULL,
    color text NOT NULL DEFAULT 'cyan',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (owner_id, name)
);

CREATE TABLE IF NOT EXISTS conversation_session_tags (
    session_id uuid NOT NULL REFERENCES conversation_sessions(id) ON DELETE CASCADE,
    tag_id uuid NOT NULL REFERENCES dashboard_tags(id) ON DELETE CASCADE,
    linked_project_id uuid REFERENCES dashboard_projects(id) ON DELETE SET NULL,
    linked_task_id uuid REFERENCES dashboard_tasks(id) ON DELETE SET NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (session_id, tag_id)
);

CREATE TABLE IF NOT EXISTS dashboard_memory_links (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id text NOT NULL,
    entity_type text NOT NULL,
    entity_id text NOT NULL,
    title text NOT NULL,
    obsidian_path text NOT NULL,
    summary text NOT NULL DEFAULT '',
    created_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (owner_id, entity_type, entity_id, obsidian_path)
);

CREATE INDEX IF NOT EXISTS idx_dashboard_memory_links_entity
    ON dashboard_memory_links (owner_id, entity_type, entity_id);
"""


def migrate(settings: Settings) -> None:
    with connect(settings) as conn:
        with conn.transaction():
            conn.execute(MIGRATION_SQL)
            _seed_dashboard_backbone(conn, settings)


def _seed_dashboard_backbone(conn, settings: Settings) -> None:
    owner_id = settings.owner_id

    projects = [
        {
            "slug": "riprocket-tcg-instagram-growth",
            "name": "riprocket_tcg Instagram Growth",
            "status": "active",
            "summary": "Grow riprocket_tcg into a sharper Instagram engine for TCG trust, content cadence, audience growth, and sales support.",
            "focus": "Pokemon TCG content, collector trust, social proof, offer testing.",
            "metadata": {
                "priority": "high",
                "channels": ["Instagram"],
                "northstar": "Turn content into a repeatable audience and sales system.",
            },
        },
        {
            "slug": "ugc-influencer-content-creation",
            "name": "UGC Influencer Content Creation",
            "status": "active",
            "summary": "Build a UGC content workflow that studies real influencer formats, adapts them safely, and produces reusable creative briefs.",
            "focus": "Influencer modeling, creative direction, scripts, video references, asset pipeline.",
            "metadata": {
                "priority": "high",
                "channels": ["Instagram", "TikTok", "Short-form video"],
                "northstar": "Create repeatable UGC concepts without becoming a generic copy machine.",
            },
        },
    ]

    project_ids: dict[str, str] = {}
    for project in projects:
        row = conn.execute(
            """
            INSERT INTO dashboard_projects (
                owner_id, slug, name, status, summary, focus, metadata
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (owner_id, slug) DO UPDATE
            SET name = EXCLUDED.name,
                status = EXCLUDED.status,
                summary = EXCLUDED.summary,
                focus = EXCLUDED.focus,
                metadata = EXCLUDED.metadata,
                updated_at = now()
            RETURNING id
            """,
            (
                owner_id,
                project["slug"],
                project["name"],
                project["status"],
                project["summary"],
                project["focus"],
                Jsonb(project["metadata"]),
            ),
        ).fetchone()
        project_ids[project["slug"]] = str(row["id"])

    agents = [
        {
            "slug": "arceus",
            "name": "Arceus",
            "role": "Orchestrator",
            "category": "Brain",
            "lore_identity": "Origin strategist",
            "status": "active",
            "trust_level": "supervised",
            "summary": "First-pass processor, planning partner, routing layer, and approval-aware command presence.",
            "can_run_local": False,
            "approval_policy": "route_before_action",
        },
        {
            "slug": "memory-scribe",
            "name": "Memory Scribe",
            "role": "Knowledge steward",
            "category": "Memory",
            "lore_identity": "Lake guardian of continuity",
            "status": "available",
            "trust_level": "supervised",
            "summary": "Maintains status summaries, Obsidian links, decisions, preferences, and task memory.",
            "can_run_local": True,
            "approval_policy": "ask_before_write",
        },
        {
            "slug": "filesystem-code-agent",
            "name": "Filesystem/Code Agent",
            "role": "Local builder",
            "category": "Engineering",
            "lore_identity": "Steel-type forge operator",
            "status": "available",
            "trust_level": "supervised",
            "summary": "Uses local project files and Codex runtime to implement scoped changes after approval.",
            "can_run_local": True,
            "approval_policy": "ask_before_write",
        },
        {
            "slug": "research-agent",
            "name": "Research Agent",
            "role": "Evidence scout",
            "category": "Research",
            "lore_identity": "Psychic-type signal finder",
            "status": "planned",
            "trust_level": "advisory",
            "summary": "Collects sources, separates facts from inference, and prepares decision-grade briefs.",
            "can_run_local": False,
            "approval_policy": "safe_read_only",
        },
        {
            "slug": "ui-ux-agent",
            "name": "UI/UX Agent",
            "role": "Interface designer",
            "category": "Design",
            "lore_identity": "Fairy-light interface artisan",
            "status": "available",
            "trust_level": "supervised",
            "summary": "Improves dashboard flow, motion, interaction clarity, and product taste.",
            "can_run_local": True,
            "approval_policy": "ask_before_write",
        },
        {
            "slug": "tcg-growth-strategist",
            "name": "TCG Growth Strategist",
            "role": "Commerce strategist",
            "category": "Growth",
            "lore_identity": "Battle tower tactician",
            "status": "planned",
            "trust_level": "advisory",
            "summary": "Designs content pillars, launch calendars, offer tests, and audience-building loops for TCG sales.",
            "can_run_local": False,
            "approval_policy": "proposal_only",
        },
        {
            "slug": "ugc-creative-director",
            "name": "UGC Creative Director",
            "role": "Creative operator",
            "category": "Creative",
            "lore_identity": "Contest hall director",
            "status": "planned",
            "trust_level": "advisory",
            "summary": "Turns influencer references into ethical briefs, scripts, shot lists, and production workflows.",
            "can_run_local": False,
            "approval_policy": "proposal_only",
        },
    ]

    agent_ids: dict[str, str] = {}
    for agent in agents:
        row = conn.execute(
            """
            INSERT INTO dashboard_agents (
                owner_id, slug, name, role, category, lore_identity, status,
                trust_level, summary, can_run_local, approval_policy
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (owner_id, slug) DO UPDATE
            SET name = EXCLUDED.name,
                role = EXCLUDED.role,
                category = EXCLUDED.category,
                lore_identity = EXCLUDED.lore_identity,
                status = EXCLUDED.status,
                trust_level = EXCLUDED.trust_level,
                summary = EXCLUDED.summary,
                can_run_local = EXCLUDED.can_run_local,
                approval_policy = EXCLUDED.approval_policy,
                updated_at = now()
            RETURNING id
            """,
            (
                owner_id,
                agent["slug"],
                agent["name"],
                agent["role"],
                agent["category"],
                agent["lore_identity"],
                agent["status"],
                agent["trust_level"],
                agent["summary"],
                agent["can_run_local"],
                agent["approval_policy"],
            ),
        ).fetchone()
        agent_ids[agent["slug"]] = str(row["id"])

    tasks = [
        {
            "slug": "riprocket-content-pillars",
            "project": "riprocket-tcg-instagram-growth",
            "agent": "tcg-growth-strategist",
            "title": "Define riprocket_tcg content pillars",
            "status": "planned",
            "risk_level": "low",
            "approval_state": "not_required",
            "summary": "Map recurring content pillars for trust, education, inventory storytelling, and sales conversion.",
        },
        {
            "slug": "riprocket-weekly-brief-template",
            "project": "riprocket-tcg-instagram-growth",
            "agent": "memory-scribe",
            "title": "Create weekly Instagram growth brief template",
            "status": "planned",
            "risk_level": "low",
            "approval_state": "required",
            "summary": "Create an Obsidian-backed brief template that Arceus can reuse for weekly review.",
        },
        {
            "slug": "ugc-reference-map",
            "project": "ugc-influencer-content-creation",
            "agent": "ugc-creative-director",
            "title": "Map influencer reference patterns",
            "status": "planned",
            "risk_level": "medium",
            "approval_state": "required",
            "summary": "Study influencer structures and extract reusable principles without blindly copying identity or protected material.",
        },
        {
            "slug": "dashboard-zone-backbone",
            "project": "riprocket-tcg-instagram-growth",
            "agent": "filesystem-code-agent",
            "title": "Wire dashboard zones to durable data",
            "status": "completed",
            "risk_level": "low",
            "approval_state": "approved",
            "summary": "Turn sidebar zones into read-only dashboard views backed by Postgres records.",
        },
    ]

    for task in tasks:
        conn.execute(
            """
            INSERT INTO dashboard_tasks (
                owner_id, slug, project_id, agent_id, title, status,
                risk_level, approval_state, summary
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (owner_id, slug) DO UPDATE
            SET project_id = EXCLUDED.project_id,
                agent_id = EXCLUDED.agent_id,
                title = EXCLUDED.title,
                status = EXCLUDED.status,
                risk_level = EXCLUDED.risk_level,
                approval_state = EXCLUDED.approval_state,
                summary = EXCLUDED.summary,
                updated_at = now()
            """,
            (
                owner_id,
                task["slug"],
                project_ids.get(task["project"]),
                agent_ids.get(task["agent"]),
                task["title"],
                task["status"],
                task["risk_level"],
                task["approval_state"],
                task["summary"],
            ),
        )

    workflow_graph = {
        "nodes": [
            {"id": "user", "label": "Brian", "kind": "input"},
            {"id": "arceus", "label": "Arceus", "kind": "brain"},
            {"id": "specialist", "label": "Specialist Agent", "kind": "agent"},
            {"id": "approval", "label": "Approval Gate", "kind": "approval"},
            {"id": "codex", "label": "Codex Runtime", "kind": "local"},
            {"id": "memory", "label": "Obsidian Memory", "kind": "memory"},
        ],
        "edges": [
            {"from": "user", "to": "arceus", "label": "ask"},
            {"from": "arceus", "to": "specialist", "label": "route"},
            {"from": "specialist", "to": "approval", "label": "plan"},
            {"from": "approval", "to": "codex", "label": "approved"},
            {"from": "codex", "to": "memory", "label": "status"},
            {"from": "memory", "to": "arceus", "label": "context"},
        ],
    }
    conn.execute(
        """
        INSERT INTO dashboard_workflows (owner_id, slug, name, status, summary, graph)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (owner_id, slug) DO UPDATE
        SET name = EXCLUDED.name,
            status = EXCLUDED.status,
            summary = EXCLUDED.summary,
            graph = EXCLUDED.graph,
            updated_at = now()
        """,
        (
            owner_id,
            "supervised-local-agent-loop",
            "Supervised Local Agent Loop",
            "draft",
            "Conversation routes into a specialist, approval gate, local Codex execution, and Obsidian status memory.",
            Jsonb(workflow_graph),
        ),
    )

    tags = [
        ("strategy", "gold"),
        ("execution", "teal"),
        ("memory", "violet"),
        ("tcg", "cyan"),
        ("ugc", "rose"),
    ]
    for name, color in tags:
        conn.execute(
            """
            INSERT INTO dashboard_tags (owner_id, name, color)
            VALUES (%s, %s, %s)
            ON CONFLICT (owner_id, name) DO UPDATE
            SET color = EXCLUDED.color
            """,
            (owner_id, name, color),
        )
