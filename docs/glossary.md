# Plain-Language Glossary

This file translates technical terms into the way we will use them in Arceus.

## Agent

A focused AI worker.

Example:

- a filesystem agent that works with files;
- a research agent that gathers information;
- a UI/UX agent that designs screens.

## Brain

Arceus itself: the planner and orchestrator.

The Brain decides what needs to happen and which specialist should help.

## Specialist

An agent with a specific job.

Specialists should be powerful in their lane, not responsible for the whole
system.

## Memory Layer

The part of Arceus that remembers useful things over time.

It includes structured system records plus human-readable notes in Obsidian and
Notion.

## Postgres

A reliable database.

For Arceus, Postgres is the system ledger: it remembers tasks, approvals,
statuses, agent runs, and important records.

## Queue

A durable task inbox.

If you ask the cloud to do something that must run on your laptop, the request
goes into the queue and waits until the laptop can handle it.

## Worker

The process that picks tasks out of the queue and runs them.

The laptop worker is the trusted runner for laptop-only actions.

## PWA

A phone-friendly web app that can feel close to a mobile app without needing an
App Store release.

This is the first remote surface for Arceus.

## Proxy Tool

A safe stand-in.

In the cloud, a proxy tool has the same name as a laptop tool, but it does not
perform the powerful action. It only queues the request for the laptop.

## Durable

Saved in a way that survives restarts, crashes, and sleep.

If something is durable, Arceus can recover it later.

## Lifecycle State

The current stage of a task.

Example:

- queued;
- running;
- awaiting approval;
- completed;
- failed.

The UI can show lore-themed names like "Forging" or "Manifested", but the
system keeps simple internal labels underneath.

## Approval Gate

A checkpoint where Arceus must ask before continuing.

Examples:

- writing files;
- deleting files;
- sending a message;
- using credentials;
- making purchases.

## Local-First, Cloud-Ready

Start by building on the laptop, but design it so cloud access can be added
without rebuilding everything.

This gives speed now and flexibility later.
