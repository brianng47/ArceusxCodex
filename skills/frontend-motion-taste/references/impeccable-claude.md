# Impeccable And Claude Setup

Source grounding:

- Impeccable GitHub repository: https://github.com/pbakaus/impeccable

## Current Recommended Install Paths

From the project root, Impeccable currently documents:

```bash
npx impeccable skills install
```

Then reload the AI coding tool. Inside Claude Code, initialize the project context:

```text
/impeccable init
```

Claude Code users can also use Claude's plugin marketplace command:

```text
/plugin marketplace add pbakaus/impeccable
```

The repository also documents a general-purpose skills install path:

```bash
npx skills add pbakaus/impeccable
```

## About `claudepluginhub`

If a user specifically provides:

```bash
npx claudepluginhub pbakaus/impeccable --plugin impeccable
```

do not assume it is the current recommended path unless the user's Claude setup requires it. Prefer Impeccable's own install docs above, then use the user-provided installer only if they confirm that Claude Plugin Hub is already part of their workflow.

## Local Sandbox Note

Codex may be unable to install this automatically when:

- npm network access is blocked;
- writing to `~/.claude` is outside the current filesystem sandbox;
- Claude Code is not available on PATH.

When blocked, give the user the exact command to run in their normal Terminal and ask them to paste the output back.

## Suggested Impeccable Commands For Arceus UI

After installation and `/impeccable init`, use:

```text
/impeccable critique dashboard
/impeccable distill dashboard
/impeccable animate dashboard
/impeccable polish dashboard
```

Use `distill` when the dashboard is cluttered, `animate` when the UI is too static, and `polish` before considering a UI pass complete.
