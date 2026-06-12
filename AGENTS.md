# Instructions for Agents Working on Arceus

Read this file before making changes.

## Northstar

Arceus is being built as a local-first, cloud-ready personal AI operating
system. It should become the user's day-to-day companion, business partner,
idea bouncer, second brain, and coordinated specialist-agent system.

The architecture has three major layers:

1. Brain and Presence: Arceus, the conversational persona, first-pass
   processor, planner, orchestrator, and router.
2. Memory: durable system memory plus human-facing knowledge bases.
3. Specialists: focused agents that execute tasks through safe, auditable flows.

Arceus is not an API-key chatbot. Arceus is the operating layer around local
agent runtimes such as Codex CLI and, later, Claude Code. The product value is
the combination of persona, memory, tools, approvals, specialists, UI, and
local/cloud execution.

## Current Phase

The project starts from zero. Prefer foundational clarity over speed.

Do not jump into implementation before confirming:

- which tier is being built;
- what counts as successful verification;
- whether an action is local-only, cloud-safe, or approval-required.

## Safety Rules

- Ask before any file write unless the user has explicitly authorized the
  current edit.
- Treat destructive, financial, credential, purchase, and irreversible actions
  as high-risk.
- Cloud/phone surfaces may queue or propose high-risk actions, but may not
  execute them directly.
- Laptop-side approval is required for powerful local actions unless the user
  later promotes a workflow to automation.
- Keep an audit trail for substantial decisions and actions.
- Hide sensitive error details from remote surfaces by default.
- Do not grant Documents-wide access. The repo should live at
  `/Users/brianng/Developer/Arceus`; Obsidian read/write, repo-local
  `.arceus-state`, read-only `~/.codex`, and explicit project folders are
  allowed by policy. Every future filesystem agent must check the Arceus path
  policy before reading or writing local files.

## Design Rules

The local UI should feel like a mission-control dashboard with an avatar layer.
Arceus should feel wise, strategic, ethereal, witty, and occasionally
sarcastic when challenging weak ideas.

Keep the voice practical. Mythic flavor is welcome, but it should not drown out
clear thinking or daily usefulness.

Reliability comes first. Lore should decorate dependable system states, not
replace them.

Use `docs/ui-design-rules.md` as the source of truth for visual direction.
The dashboard should take high-level inspiration from holographic command
interfaces: dark spatial depth, luminous circuitry, animated status panels, and
a central living avatar/core.

For frontend redesign, animation, UI polish, dashboard critique, decluttering,
or visual implementation work, automatically use
`skills/frontend-motion-taste/SKILL.md` even if the user does not name it. It
preserves the reusable motion and anti-generic design rules for future agents.

Private fan-project rule:

This project is currently private and non-commercial. In that mode, the user
wants Arceus to directly use Pokemon-owned Arceus visual and lore references.
Treat official/fan-reference Arceus art as acceptable private prototype
direction when designing the avatar, jewel plates, silhouette, and personality.

Future-mode warning:

If this project ever becomes public or commercial, the visual identity will need
a deliberate rebrand away from protected Pokemon-owned assets. Do not delete
this warning; it is a strategic boundary for a possible future version.

## Implementation Rules

- Build tier by tier.
- Do not let the queue/task system become the product. It is infrastructure
  beneath the real-time Arceus conversation and avatar experience.
- Verify each tier before moving to the next.
- Preserve a simple internal state model even if the UI uses Arceus-themed
  labels.
- Use durable storage as the source of truth.
- Do not rely on live push signals alone. Always support catch-up on startup.
- Avoid duplicate execution by construction: real local tools on laptop,
  proxy tools in cloud only when the real tool is absent.
