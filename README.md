# Arceus

Arceus is a local-first, cloud-ready personal agent system.

The long-term goal is to build a day-to-day AI companion, business partner,
idea bouncer, second brain, and coordinated army of specialist agents. Arceus
is the brain and orchestrator. It should understand intent, preserve memory,
route work to specialists, ask for approval before risky action, and keep the
user informed through a mission-control dashboard with an avatar layer.

This repository starts from a blank slate. The first priority is a strong
foundation:

- A clear product charter and PRD.
- A durable memory and task ledger.
- A local-first architecture that can later split into cloud and laptop roles.
- Approval-first specialist agents.
- A tier-by-tier implementation path with verification at every step.

## Current Status

Planning and foundation docs are in place. The local foundation is now running:

- durable Postgres task queue;
- local conversation shell;
- supervised Codex manual handoff runtime;
- supervised Codex autorun for stored handoffs;
- memory summary command;
- local dashboard at `http://127.0.0.1:8787`;
- Codex app-server feasibility tooling.

## Key Documents

- [Product Requirements](docs/prd.md)
- [Founding Charter](docs/founding-charter.md)
- [Architecture](docs/architecture.md)
- [Brain and Presence](docs/brain-and-presence.md)
- [Codex Runtime Bridge](docs/codex-runtime-bridge.md)
- [Codex App-Server Feasibility](docs/codex-app-server-feasibility.md)
- [Local Dashboard](docs/local-dashboard.md)
- [UI Design Rules](docs/ui-design-rules.md)
- [Agent System](docs/agents.md)
- [TCG Business Agent Ecosystem](docs/tcg-business-agent-ecosystem.md)
- [Skills and Integrations](docs/skills.md)
- [Memory Layer](docs/memory.md)
- [Tier Build Guide](docs/tier-build-guide.md)
- [Tier 1 Local Queue Guide](docs/tier-1-local-queue.md)
- [Track A Conversation Shell](docs/track-a-conversation-shell.md)
- [Guardrails](docs/guardrails.md)
- [Plain-Language Glossary](docs/glossary.md)
- [Decision Log](docs/decision-log.md)

## Operating Principle

Arceus should be powerful, but never reckless.

Cloud and phone access are limited by default. The laptop is the trusted control
center. High-risk actions require explicit approval until the user promotes a
workflow to automation.
