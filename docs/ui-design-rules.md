# UI Design Rules

## Purpose

This document is the visual and interaction source of truth for the Arceus
dashboard.

The goal is not to make a generic admin panel. The goal is a mission-control
surface where Arceus feels present, watchful, and useful.

## Reference Direction

The provided command-center image is a mood reference for layout, atmosphere,
and holographic interface language. It should not be copied one-for-one.

Useful traits to carry forward:

- dark cinematic command-center background;
- luminous cyan holographic circuitry;
- central glowing core;
- radial HUD rings;
- thin technical linework;
- data paths extending from the center;
- high contrast between background and active information.

Arceus adaptation:

- replace the mechanical eye with a direct Arceus fan-project avatar/core;
- use jewel plates as functional navigation and status objects;
- add divine/cosmic warmth so the interface is not only blue-on-black;
- make dashboard cards feel summoned around the avatar, not pasted on top.

## Fan-Project Identity Rule

This is a private, non-commercial fan project.

The user explicitly wants the dashboard and avatar direction to copy/use
Pokemon-owned Arceus art, lore, silhouette language, jewel plates, divine
presence, and related visual cues for private use.

Private prototype mode allows:

- direct Arceus visual references;
- official-art-derived avatar studies;
- Arceus-like silhouette, jewel plates, ring forms, and godlike presence;
- Pokemon/Arceus naming in internal docs and UI;
- fan-project lore language when it improves the experience.

Boundary:

- keep this project private and non-commercial while using protected assets;
- do not present the work as official;
- if the project ever becomes public or commercial, create a separate public
  identity pass that replaces protected Pokemon-owned assets.

Strategic note:

The private fan-project direction is accepted. The future public-mode warning
exists only so the project does not accidentally drift into a different risk
profile later.

## Core Layout

The first dashboard should contain:

1. Central avatar/core.
2. Orbiting jewel plates for projects, agents, tasks, and memory.
3. Left-side command stream or conversation panel.
4. Right-side task queue and approval cards.
5. Bottom status rail for worker presence, queue health, memory sync, and
   current mode.

The center must remain the emotional anchor. Cards should orbit or align around
it without blocking it.

## Visual Layers

### Ambient Layer

Purpose:

- create the sense of a deep, living control room.

Rules:

- near-black base;
- subtle stars, grid traces, or cosmic mist;
- slow animated data lines;
- no heavy blur that reduces legibility;
- no decorative blobs or generic gradient orbs.

### Avatar Layer

Purpose:

- make Arceus feel present.

Rules:

- central luminous core or avatar placeholder;
- slow breathing/pulsing motion;
- ring or halo motion tied to voice/listening/thinking states;
- jewel plates that represent active projects, tasks, or agents;
- animation should respond to actual system states when possible.

### Work Layer

Purpose:

- let the user act quickly.

Rules:

- cards are practical, readable, and compact;
- use transparent dark glass only when text remains sharp;
- status, approvals, and errors must be obvious;
- action buttons must be clear and easy to hit;
- no card inside another card;
- avoid oversized hero text inside dashboard panels.

## Palette

Use a multi-hue ethereal palette. Avoid a one-note blue interface.

Recommended tokens:

| Role | Color |
| --- | --- |
| Void background | `#03050A` |
| Deep space surface | `#07111F` |
| Hologram cyan | `#4BD8FF` |
| Divine gold | `#F5D36C` |
| Pearl white | `#F7F4EA` |
| Spectral violet | `#9B7CFF` |
| Celestial teal | `#37E6C1` |
| Warning amber | `#FFB84D` |
| Failure crimson | `#FF5C7A` |

Usage:

- cyan for active data and circuitry;
- gold for Arceus identity, approvals, and high-value states;
- violet for memory, mystery, and specialist intelligence;
- teal for safe completion and healthy systems;
- crimson only for true failure or danger.

## Motion Language

Motion should feel alive, not noisy.

Allowed motion:

- slow avatar breathing;
- rotating halo rings;
- data pulses along circuit lines;
- cards materializing with light edge scans;
- jewel plates gently orbiting or shifting when active;
- approval cards glowing softly when waiting.

Avoid:

- constant shaking;
- high-speed particle spam;
- animations that move text while reading;
- motion that hides system state;
- expensive effects that make the dashboard sluggish.

Every animation must respect a reduced-motion setting.

## Dashboard Cards

Cards should look like holographic instruments.

Card types:

- active task;
- approval request;
- agent status;
- memory update;
- queue health;
- worker presence;
- recent manifestation/completion.

Card behavior:

- entrance: materialize or scan in;
- active: subtle edge pulse;
- awaiting approval: gold pulse;
- completed: teal confirmation;
- failed: crimson fracture line;
- stale/offline: dimmed with clear text.

## Typography

Use readable modern type.

Rules:

- dashboard text must be practical before cinematic;
- no tiny decorative labels for critical data;
- avoid negative letter spacing;
- do not scale fonts with viewport width;
- lore labels can exist, but pair them with plain meaning where needed.

Example:

- "Forging" may be shown as the state label.
- The card should still explain "Running filesystem agent" nearby.

## Asset Strategy

Leverage existing tools where useful.

Potential asset sources:

- generated images for background concepts;
- video generation for avatar motion studies;
- Remotion for controlled interface animation;
- design tools for mockups;
- future Higgsfield or Seedance integrations if available.

Important:

- generated assets should support the UI, not replace it;
- critical controls must be implemented as real components;
- keep assets modular so they can be swapped without rebuilding the dashboard;
- preserve prompts and source notes in memory for repeatability.

Current connector note:

- No Higgsfield or Seedance connector is currently installed in this workspace.
  If one becomes available later, it should be added as a creative asset skill,
  not as a dependency for core dashboard function.

## First Dashboard Slice

The first implementation should include:

- dark ethereal background;
- central avatar/core placeholder;
- four jewel plates: Tasks, Agents, Memory, Approvals;
- animated task cards;
- worker presence card;
- approval card state;
- lifecycle labels using the Arceus vocabulary.

Do not build a marketing landing page first. Build the usable control surface.

## Verification

Before accepting a dashboard implementation:

1. Open it on desktop and phone widths.
2. Confirm text never overlaps.
3. Confirm cards remain readable over the background.
4. Confirm animations run smoothly.
5. Confirm reduced-motion mode works.
6. Confirm the avatar/core is visible in the first viewport.
7. Confirm the UI still works if generated assets fail to load.
