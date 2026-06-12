# Motion Principles

Source grounding:

- Emil Kowalski, "Great Animations": https://emilkowal.ski/ui/great-animations

## Core Rules

1. Motion should explain state, continuity, or attention.
   - Use it when an element appears, disappears, changes status, expands, completes, fails, or needs temporary attention.
   - Do not animate every decorative element just because the page feels static.

2. Interaction motion should feel fast.
   - Most user-triggered UI transitions should stay under 300ms.
   - Favor ease-out curves for responsive actions because they start quickly and settle smoothly.

3. Ambient motion should stay quiet.
   - Use slow breathing, glow, orbit, or parallax only for non-essential presence.
   - Keep it subtle enough that the user can read, think, and work without distraction.

4. Animate compositor-friendly properties.
   - Prefer `transform` and `opacity`.
   - Avoid animating `width`, `height`, `top`, `left`, `margin`, `padding`, and expensive filters for repeated UI motion.

5. Make motion interruptible.
   - Hover, focus, expanded panels, tabs, and overlays should transition smoothly even if the user reverses direction mid-animation.
   - Prefer transitions for interactive states unless keyframes are necessary.

6. Respect reduced motion.
   - Provide `@media (prefers-reduced-motion: reduce)`.
   - Replace large movement with short fades or remove non-essential animation.

7. Do not slow down repeated work.
   - Avoid animation on keyboard-initiated flows, repeated list navigation, or frequent command entry.
   - A command center should feel responsive before it feels cinematic.

## Recommended Timing Tokens

```css
:root {
  --motion-fast: 160ms cubic-bezier(0.16, 1, 0.3, 1);
  --motion-base: 220ms cubic-bezier(0.16, 1, 0.3, 1);
  --motion-soft: 360ms ease;
  --motion-ambient: 8s ease-in-out;
}
```

Use faster tokens for direct manipulation. Use slower tokens only for background or avatar presence.

## Arceus-Specific Motion Roles

- Listening: subtle avatar brightening, waveform activity, command input focus.
- Thinking: one restrained orbit or pulse, not a screen-wide loading spectacle.
- Planning: step list or plan card enters once, then stabilizes.
- Awaiting approval: approval control becomes visually dominant.
- Executing: progress line or lifecycle card updates; avoid fake completion theatrics.
- Remembering: short memory confirmation, then quiet state.

