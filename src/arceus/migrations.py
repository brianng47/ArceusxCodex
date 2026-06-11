from __future__ import annotations

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
"""


def migrate(settings: Settings) -> None:
    with connect(settings) as conn:
        conn.execute(MIGRATION_SQL)
