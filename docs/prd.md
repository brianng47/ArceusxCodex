# Product Requirements Document

## Product Name

Arceus

## Vision

Arceus is a personal AI command system that acts as the user's day-to-day
companion, business partner, idea bouncer, second brain, and specialist-agent
orchestrator.

Arceus may use local agent runtimes such as Codex CLI, Claude Code, or future
providers as reasoning and execution engines. The product is not the model
alone. The product is the complete operating layer: real-time persona, avatar,
memory, knowledge base, skills, local tools, specialists, approvals, and
cloud/laptop routing.

The experience should feel like a mission-control dashboard with a central
avatar. The avatar represents Arceus: wise, strategic, ethereal, and witty,
with enough sarcasm to challenge weak thinking without becoming hostile.

The visual direction should blend a dark holographic command center with a
private fan-project Arceus aesthetic: luminous circuitry, divine jewel plates,
animated dashboard cards, direct Arceus visual/lore references, and a cosmic
background that feels alive without overpowering the work.

## Problem

The user wants more than a chatbot. They want a trusted operating layer that can
understand goals, remember context, break large objectives into smaller tasks,
delegate to specialist agents, run work safely across local and remote
surfaces, and preserve knowledge over time.

The system must eventually support both:

- an always-on cloud/phone-accessible assistant; and
- a trusted laptop control center with access to local files, tools, UI,
  credentials, and approvals.

## Goals

- Make Arceus useful as a real-time conversational partner before it becomes a
  large execution machine.
- Build a strong local-first foundation that can later become cloud-ready.
- Create a durable task and memory ledger.
- Preserve decisions, project context, and useful outputs in a growing
  knowledge base.
- Make the laptop the trusted execution center for powerful actions.
- Make the phone/cloud surface safe for queuing, status, low-risk tasks, and
  selected approvals.
- Support specialist agents that can chain work while preserving guardrails.
- Provide interactive local visibility for queued, running, approval, and
  completed work.

## Non-Goals for the First Phase

- No full cloud deployment yet.
- No native mobile app yet.
- No direct financial, purchase, credential, or destructive execution from the
  phone/cloud surface.
- No unapproved file writes.
- No fully autonomous high-risk workflows.

## Target Users

Single-user for now: Brian.

The data model should still include ownership fields so future multi-user
support can be added without rewriting the foundation.

## Product Surfaces

### Laptop Control Center

The laptop is the trusted command center. It should host the richest UI and the
most powerful capabilities.

Expected responsibilities:

- project and filesystem work;
- local code execution;
- local credentials and desktop tools;
- approval cards;
- run visibility;
- voice/avatar experience;
- access to the full memory layer.

Visual requirements:

- central avatar/core visible in the first viewport;
- animated jewel plates for projects, tasks, or specialists;
- dashboard cards for queue, agents, approvals, memory, and system health;
- holographic linework and subtle data-flow animation;
- readable, practical panels over cinematic background layers;
- no purely decorative effects that make controls harder to use.

### Phone PWA

The first remote surface should be a phone-friendly web app.

Expected responsibilities:

- text-first interaction;
- queueing work for the laptop;
- checking status;
- receiving completion summaries;
- displaying full results only when explicitly requested;
- supporting tagged low-risk approvals.

Voice should be planned soon after text is stable.

## First Specialist Agents

### Filesystem/Code Agent

The first laptop-bound specialist.

Initial rules:

- may inspect broadly;
- must ask before any write;
- must preview proposed changes;
- must avoid destructive operations unless explicitly approved;
- must log substantial actions to memory.

### Research Agent

Hybrid specialist for gathering, summarizing, and preserving external
information. It should distinguish sourced facts from inference.

### UI/UX Agent

Hybrid specialist for designing the Arceus dashboard, avatar experience,
interaction flows, and eventually mockups/content using creative tools.

## Completion Ping Preferences

Default remote completion ping: useful summary.

Full results are shown only when asked, especially if they may contain private
files, code, or memory snippets.

Failure messages should be lore-styled but honest.

Example:

> The forging fractured. No changes were applied.

Details should be hidden behind a "View details" action.

## Offline Laptop Behavior

If the laptop is offline or asleep, the cloud/phone surface should still queue
the task and acknowledge that it will run later.

When the laptop wakes, it should show a reminder/pop-up asking whether the user
still wants to run queued tasks. Future tasks may set expiry times.
