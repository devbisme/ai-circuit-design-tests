# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and logged in.
- **Node.js ≥ 20.** These tests used Node 22.23.3 installed with `nvm`.
- **KiCad ≥ 8** with `kicad-cli` on `PATH`. These tests used the system KiCad 9.0.9.
  To use a different binary, set `COPPERHEAD_KICAD_CLI=/path/to/kicad-cli`.
- `git`.
- [OpenSpec](https://github.com/Fission-AI/OpenSpec) (`openspec` on `PATH`). `copperhead doctor`
  checks for it, and the pipeline writes its change proposals under `openspec/`:

  ```bash
  npm install -g @fission-ai/openspec
  ```

## Quick option: let Claude Code install it

Start `claude` in the project directory and type:

```
Install copperhead for this repo using https://raw.githubusercontent.com/copperheadhq/copperhead/main/agent-install-prompt.md
```

The prompt asks three questions (model backend, existing or new project, npm or source
install), then installs copperhead, runs `copperhead doctor` and `copperhead check`, and adds
`.env` and `.copperhead/runs/` to `.gitignore`. It does not run `create` or `do`. The manual
steps below do the same thing.

## 1. Install copperhead

```bash
npm install -g copperhead
copperhead --version          # these tests used 0.11.0
```

To build from source instead, run `npm ci && npm run build && npm link` inside a clone of
[copperheadhq/copperhead](https://github.com/copperheadhq/copperhead).

## 2. Choose the Claude Code backend

copperhead needs a model backend. These tests used `claude-code`, which runs Claude Code
through the Claude Agent SDK on your Claude subscription, so no `ANTHROPIC_API_KEY` is needed.
The SDK is an optional dependency, and a normal `npm install -g` includes it.

Set the backend in the project's `.env` file (or export it in your shell):

```bash
COPPERHEAD_MODEL=claude-code
```

You can also pass `--model claude-code` on each `do` or `create` command.

The README says the backend reuses the token from `claude setup-token`:

```bash
claude setup-token                    # prints a long-lived OAuth token
export CLAUDE_CODE_OAUTH_TOKEN=...    # or put it in .env
```

Not confirmed: in this test, `.env` held the token as `CLAUDE_CODE_TOKEN` (not
`CLAUDE_CODE_OAUTH_TOKEN`), and the run still worked. So the backend may use the existing
`claude` login without the token. Use the variable name the README gives.

Other backends (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, Codex CLI, Cursor Agent CLI) are
listed in the [README](https://github.com/copperheadhq/copperhead#requirements).

## 3. Keep secrets and run logs out of git

Make sure the project's `.gitignore` contains:

```gitignore
.env
.copperhead/runs/
```

## 4. Verify

```bash
copperhead doctor     # checks node, kicad-cli, git, openspec, provider; no LLM, no network
copperhead check      # ERC + DRC + doc drift; no LLM
```

Expected `doctor` output on this machine:

```
  [ok]   node      v22.23.3 (>= 20)
  [ok]   kicad-cli 9.0.9
  [ok]   git       2.43.0
  [ok]   openspec  1.14.0
  [info] provider  claude-code -> claude-code: uses Claude Code login (not verified offline)
ready
```

`doctor` cannot check the Claude Code login offline. A bad login shows up only on the first
`do` or `create`. In an empty directory, `check` exits 0 and skips ERC and DRC.

## 5. Run it

- New project from a brief (what these tests do):

  ```bash
  copperhead create --brief brief.md
  ```

  `--brief` expects a markdown file. The pipeline has 8 stages and commits to git once per
  stage, **in whatever repo contains the project directory** (here, `master` of
  `ai-circuit-design-tests`). Branch first if you don't want that. If a run stops (for example
  at a usage limit), re-running it skips completed stages and replays cached LLM turns.
- Existing KiCad project: run `copperhead init` once to scaffold `docs/` from the schematic,
  then `copperhead do "<change>"`.

Each stage is limited to `maxTurns` (default 40) in `.copperhead/config.json`. In this test,
stage 3 ran out of turns.

Source: [copperhead README](https://github.com/copperheadhq/copperhead),
[agent-install-prompt.md](https://raw.githubusercontent.com/copperheadhq/copperhead/main/agent-install-prompt.md),
the `dual-adc-usb-1` transcript, and the installation on this machine.
