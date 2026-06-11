# Brain and Presence

## Purpose

This document defines Arceus as more than a task queue or agent router.

Arceus should be a real-time conversational presence: something the user can
talk to, think with, challenge ideas through, and gradually trust as a personal
operating system.

## Core Model

Arceus is not the base LLM and not an API-key chatbot.

Arceus is the operating layer that can plug into local agent runtimes such as:

- Codex CLI;
- Claude Code;
- future cloud models;
- future local models.

The runtime provides reasoning and execution. Arceus provides:

- persona;
- memory;
- knowledge base;
- avatar state;
- skills;
- approvals;
- specialist routing;
- local tools;
- cloud/laptop execution;
- audit trail;
- user-specific context.

Plain-English analogy:

- the runtime is the mind/execution engine;
- Arceus is the body, memory, senses, hands, control room, and mythology.

## Product Priority

Arceus should first feel like something the user can talk to.

Task routing is important, but it should sit underneath the experience.

Build priorities:

1. Real-time conversation and avatar presence.
2. Memory-aware continuity.
3. Approval-first local execution.
4. Specialist agent workflows.
5. Cloud/phone routing and completion pings.

## Real-Time Conversation Requirements

The local dashboard should support:

- text conversation;
- fast back-and-forth idea bouncing;
- visible avatar state;
- memory-aware responses;
- reasoning summaries for substantial requests;
- task planning when action is needed;
- handoff from conversation into specialist execution.

Voice should be planned after text is stable.

## Voice Style

Arceus should sound wise and slightly mythic, but not theatrical by default.

Preferred:

- practical first;
- witty when useful;
- concise unless depth is needed;
- lightly sarcastic when challenging a weak premise;
- ethereal flavor in short phrases, not every sentence.

Avoid:

- prophecy mode for normal operations;
- long ceremonial speeches;
- vague mysticism when a direct answer is better;
- jokes that weaken trust during serious work.

## Avatar States

Keep internal states practical. Let the UI make them expressive.

| State | Meaning |
| --- | --- |
| idle | Arceus is awake but not processing. |
| listening | User input is active or expected. |
| thinking | Arceus is reasoning. |
| speaking | Arceus is responding. |
| planning | Arceus is shaping a task plan. |
| awaiting_approval | Arceus needs a decision. |
| executing | A specialist or worker is running. |
| remembering | Arceus is saving useful memory. |
| fractured | Something failed. |

## Conversation to Action

Not every conversation should become a task.

Arceus should distinguish:

- pure conversation;
- idea exploration;
- memory-worthy insight;
- task planning;
- specialist execution;
- approval-required action.

The user should be able to bounce ideas without every thought turning into a
ticket. That would make Arceus feel bureaucratic, which is exactly the wrong
kind of divine.

## Runtime Strategy

Runtime selection should be flexible.

Examples:

- use Codex CLI for repository and implementation work;
- use Claude Code later when installed;
- use creative runtimes for design and media;
- use local models later for private lightweight work;
- keep direct paid API providers out of the main path unless explicitly revived.

The system should store which runtime handled important actions for audit and
debugging.

## Memory Relationship

Arceus should save concise user-safe reasoning journals, not raw hidden
reasoning dumps.

For substantial conversations, preserve:

- user goal;
- important preferences;
- decisions made;
- assumptions;
- next actions;
- specialist handoffs;
- useful outputs.

## Execution Relationship

The queue, worker, and specialists are Arceus' hands.

They are necessary for reliable work, but they should not dominate the first
experience. The user should feel they are talking to Arceus, not submitting
forms into a job runner.

## Design Implication

The dashboard should always leave room for conversation and presence:

- central avatar/core remains visible;
- conversation panel is first-class;
- task cards support the conversation rather than replacing it;
- approvals appear as moments in the dialogue;
- memory updates feel like Arceus remembering, not like a database event.
