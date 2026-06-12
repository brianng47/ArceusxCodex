# Arceus Local Access Policy

Arceus is now located at:

```text
/Users/brianng/Developer/Arceus
```

Do not use `/Users/brianng/Documents/Arceus` as the project location. Keeping
the repo outside Documents avoids broad macOS privacy permissions and keeps
future background launch more reliable.

## Default Allowlist

Arceus application-level file access is intentionally narrow.

Read roots:

- `/Users/brianng/Developer/Arceus`
- `/Users/brianng/Library/Mobile Documents/iCloud~md~obsidian/Documents`
- `/Users/brianng/Developer/Arceus/.arceus-state`
- `/Users/brianng/.codex`

Write roots:

- `/Users/brianng/Developer/Arceus`
- `/Users/brianng/Library/Mobile Documents/iCloud~md~obsidian/Documents`
- `/Users/brianng/Developer/Arceus/.arceus-state`
- `/Users/brianng/Developer/Arceus/Arceus Dashboard.app`

Documents-wide access is not allowed by default.

## Why Obsidian Is Allowed

Obsidian is the current long-term brain vault. Arceus needs read and write
access so it can:

- preserve decisions;
- update the current state;
- grow the knowledge base;
- link tasks, projects, agents, and research notes.

## Adding Project Folders Later

If Arceus needs to work on another project, add that exact folder instead of
granting all of Documents.

Use:

```text
ARCEUS_EXTRA_READ_PATHS=/path/to/project
ARCEUS_EXTRA_WRITE_PATHS=/path/to/project
```

Use multiple paths with `:` on macOS:

```text
ARCEUS_EXTRA_READ_PATHS=/path/one:/path/two
```

Every future filesystem-capable agent must check this policy before reading or
writing local files.
