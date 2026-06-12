# Anti-Generic Frontend Guidance

Source grounding:

- Taste Skill: https://www.tasteskill.dev/
- Impeccable repository: https://github.com/pbakaus/impeccable

## Taste Filter

Before editing, state the product lane:

- operational dashboard;
- command center;
- creative tool;
- marketplace/ecommerce;
- content studio;
- personal OS;
- marketing site.

Do not use the same layout grammar for all lanes.

## Generic Tells To Avoid

- Purple-blue gradient as the main visual idea.
- One-note monochrome or one-hue palette.
- Cards inside cards.
- A wall of equal-weight cards with no real hierarchy.
- Oversized hero typography inside operational tools.
- Rounded-square icon tile above every heading.
- Gray text on colored or dark backgrounds with poor contrast.
- Default Inter/system typography without deliberate scale, weight, and spacing choices.
- Decorative blobs, bokeh orbs, and unrelated gradient clouds.
- Placeholder assets where a real product, avatar, state, or object should appear.
- Feature-description copy inside the app explaining what obvious controls do.

## Dashboard Quality Rules

1. Make the first viewport answer:
   - What is happening now?
   - What needs my attention?
   - What can I ask or approve next?

2. Use cards only when they frame a real object:
   - task;
   - approval;
   - alert;
   - message;
   - handoff;
   - repeated record.

3. Hide logs and ledger details behind "View details".

4. Show urgent stats only by default.
   - Pending approval.
   - Failed run.
   - Running task.
   - Stale queued task.
   - Memory update needed.
   - Security or permission issue.

5. Use domain-shaped labels.
   - Prefer "Awaiting approval" over "Pending".
   - Prefer "Codex handoff ready" over "Task created".
   - Keep lore labels secondary to plain status.

6. Keep controls familiar.
   - Use text buttons for major actions.
   - Use icon buttons only when the symbol is obvious or tooltip-backed.
   - Do not invent interaction patterns when a standard control is clearer.

## Pre-Handoff Checklist

- The main action is visually obvious.
- Non-urgent information is collapsed or lower priority.
- Text fits on mobile and desktop.
- Hover/focus states are present.
- Empty, loading, success, failure, and awaiting-approval states exist.
- Motion has a purpose and respects reduced-motion.
- The design would still make sense if the decorative background were removed.
- The UI does not look like a generic AI dashboard template.

