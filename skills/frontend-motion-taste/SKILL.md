---
name: frontend-motion-taste
description: Apply restrained, purposeful frontend motion and anti-generic visual design judgment to dashboards, app UI, landing pages, prototypes, HTML/CSS/JS/React work, design audits, polish passes, and Arceus UI changes. Use automatically when Codex is asked to redesign, build, animate, simplify, declutter, polish, critique, or improve frontend interfaces, especially dark dashboards, command centers, agent UIs, or screens that risk looking generic, static, overbuilt, cluttered, or visually weak.
---

# Frontend Motion Taste

## Overview

Use this skill to make frontend work feel deliberate, alive, and non-generic without turning the interface into decoration. It combines motion discipline inspired by Emil Kowalski, anti-slop frontend judgment inspired by Taste Skill, and an Impeccable-compatible quality gate for future Claude/Codex workflows.

Invoke this skill even when the user does not name it if the task involves frontend design, dashboard UI, animation, visual polish, decluttering, design critique, or a UI implementation pass.

## Operating Standard

Start by deciding what the screen is actually for. Remove panels, stats, labels, and animation that do not support that job.

For Arceus dashboards, prioritize:

- a clear command/conversation surface;
- Arceus presence that feels alive but does not obstruct work;
- urgent matters and approvals only;
- visible plan, risk, and next action when execution is relevant;
- durable memory and handoff details hidden until requested.

## Workflow

1. Audit the existing UI before editing.
   - Name the primary user job.
   - Identify clutter, duplicate controls, weak hierarchy, and generic AI/SaaS tells.
   - Preserve useful existing behavior and data wiring.

2. Define a small visual system.
   - Choose layout hierarchy, spacing rhythm, color roles, type scale, and motion roles.
   - Avoid one-note palettes. Dark UI needs hue, contrast, and depth, not pure black plus neon.
   - Use real assets for meaningful visual elements. Do not fake important visuals with div art or placeholder boxes.

3. Map motion to information.
   - Use motion to show state change, attention, continuity, or system presence.
   - Keep interaction animations fast and responsive.
   - Keep ambient motion subtle, slow, and optional.
   - Animate only `transform` and `opacity` unless there is a strong reason.

4. Implement with restraint.
   - Prefer CSS transitions/keyframes for simple UI motion.
   - Keep controls functional and text readable on mobile and desktop.
   - Avoid nested cards, decorative excess, cramped panels, and repeated badge clutter.

5. Verify before handoff.
   - Check layout at desktop and mobile widths.
   - Check text overflow and button label fit.
   - Check reduced-motion behavior.
   - Check that the screen still works with real current data, empty states, and error states.
   - Check the anti-generic checklist in `references/anti-generic-frontend.md`.

## Motion Defaults

Use these as defaults, then tune to the product mood:

```css
:root {
  --motion-fast: 160ms cubic-bezier(0.16, 1, 0.3, 1);
  --motion-base: 220ms cubic-bezier(0.16, 1, 0.3, 1);
  --motion-soft: 360ms ease;
  --motion-ambient: 8s ease-in-out;
}
```

Apply `--motion-fast` to button hover, focus, pressed, tabs, and small state changes. Apply `--motion-base` to panels entering, expanding details, and meaningful state transitions. Apply `--motion-ambient` only to non-essential presence effects such as breathing, subtle orbit, or background drift.

Do not animate keyboard-heavy workflows. Do not use bounce or elastic easing unless the product deliberately needs playful toy-like behavior.

## References

Read only the reference needed for the task:

- `references/motion-principles.md`: use when adding, revising, or critiquing animation.
- `references/anti-generic-frontend.md`: use when redesigning, polishing, or critiquing frontend visuals.
- `references/impeccable-claude.md`: use when installing or aligning Claude/Codex with Impeccable.

## Failure Modes

Push back when a request would make the interface worse:

- more panels without a clear job;
- animation added only to make the page feel busy;
- generic SaaS layout pasted over a domain-specific tool;
- dark mode with poor hierarchy or gray-on-gray text;
- protected/public brand risk ignored for non-private use;
- implementation that looks polished but loses approval, safety, or memory clarity.
