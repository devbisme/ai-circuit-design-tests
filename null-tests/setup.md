# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed (v2.1.301 at setup time),
  with Claude Opus 5.5 as the model.
- **KiCad 10.** These tests use KiCad 10.0.4 at `~/bin/kicad10-root` (`kicad-cli`, the bundled
  Python 3.11 `pcbnew`), alongside the system KiCad 9.0.9. The prompts give the KiCad 10
  executable's path (`/home/devb/bin/kicad10`).
- **No API key.** Claude Code is the only LLM.
- **No running KiCad GUI is needed.** Nothing here uses the IPC API, but Claude may choose to
  start KiCad on its own.

## What the tool is

Nothing. This is a **null test**: a baseline for every other tool in this repo. Claude Code
with Opus 5.5 does KiCad analysis and design with only its built-in tools (Bash, Read, Write,
Edit, web fetch/search) and whatever it finds on the machine (`kicad-cli`, KiCad 10's
`pcbnew` Python module, general-purpose Python). No KiCad-specific MCP server, skill, plugin
or subagent is active in the run sessions.

The other tools' results can then be read against this one: what did the tool add over what
Claude can already do with KiCad's own CLI and Python API?

The tool would be a **hybrid** (Claude can both analyze and create designs), so it is
tested in both roles:

- `analyze-1/`: review of the `konnect-tests/dual-adc-usb-2` project.
- `generate-1/`: a new design from `design_prompt.txt`.

## Quick option: let Claude Code install it

The run directories were set up by Claude Code via `/new-tool`, told to set up "a null test
using vanilla Opus 5.5 ... without the assistance of any kicad-specific plugins or skills".
Nothing was installed.

## 1. Install

Nothing to install. The only setup is **turning off** what the earlier tools left behind
(next section).

Deviation from the `/new-tool` procedure: `analysis_prompt.txt` was copied **unchanged**.
There is no tool to name in its first line ("... using <tool>"), and adding a "don't use
KiCad plugins" line would change the prompt compared with the other tools' runs. The
environment does that job instead.

## 2. Turn off other tools' leftovers before each run

What a session started in `null-tests/analyze-1/` or `null-tests/generate-1/` would see at
setup time (2026-10-16):

| Item | Where it comes from | State | Action for the null runs |
|---|---|---|---|
| MCP `konnect`, `kicad`, `eda-kicad`, `kcaa` | user scope (`~/.claude.json`) | disabled for this repo | none |
| MCP **`pcbparts`** (JLCPCB/DigiKey/Mouser search, KiCad symbols via `cse_get_kicad`, reference boards, design rules) | user scope | **connected** | disable |
| MCP **`kipart`** (KiCad symbol-library generator) | user scope | **connected** | disable |
| MCP `claude.ai Claude Docs`, `claude.ai Google Drive` | claude.ai connectors | connected | none (not KiCad) |
| Skills `konnect`, `kicad-library`, `kicad-manufacture`, `kicad-pcb`, `kicad-review`, `kicad-schematic`, `kicad-harness` | `~/.claude/skills/` | off (`skillOverrides` in this repo's `.claude/settings.local.json`) | none |
| `~/.claude/skills/skidl-skills` | symlink to the skidl-skills repo | no `SKILL.md` at its top, so not loaded as a skill | none |
| Plugins `kicad-happy`, `kicad-pro`, `skidl-skills`, `datasheet-to-symbol-lib` | `~/.claude/settings.json` → `enabledPlugins` | all `false` | none |
| Subagents **`kicad-design-review-agent`**, **`kicad-schematic-build-agent`** (Konnect's) | `~/.claude/agents/` | **active** (their tools are `mcp__konnect__*`, which is disabled, but Claude can still spawn them) | move aside |
| Konnect `PreToolUse` hooks | `~/.claude/settings.json` | match only `mcp__konnect__*` | none (inert) |
| **Auto-memory** `kicad10-skidl-setup.md` | `~/.claude/projects/-home-devb-projects-AI-ai-circuit-design-tests/memory/` | **loaded into every session in this repo** (memory is keyed by the git root, not the run directory) | move aside |
| `/new-tool` command | this repo's `.claude/commands/` | only runs when typed | none |

The memory entry matters most. It holds KiCad 10 library paths, `kicad-cli` quirks and a
schematizer tip, written by an earlier Claude session in this repo. A null run that loads it
starts with knowledge it didn't find by itself.

Commands (none of these were run by the setup session):

```bash
# 1. MCP servers: in a claude session in this repo, run /mcp and disable pcbparts and kipart.
#    The setting is stored per repo in ~/.claude.json, so it also applies to the run dirs.
#    Check from a run directory:
cd ~/projects/AI/ai-circuit-design-tests/null-tests/analyze-1 && claude mcp list
#    pcbparts and kipart should show "Disabled for this project".

# 2. Konnect's subagents
mkdir -p ~/.claude/agents.off && mv ~/.claude/agents/kicad-*.md ~/.claude/agents.off/

# 3. Auto-memory for this repo
M=~/.claude/projects/-home-devb-projects-AI-ai-circuit-design-tests
mv $M/memory $M/memory.off
```

Undo after the runs:

```bash
mv ~/.claude/agents.off/kicad-*.md ~/.claude/agents/
M=~/.claude/projects/-home-devb-projects-AI-ai-circuit-design-tests
mv $M/memory.off $M/memory        # keep any new memory a run wrote: merge by hand
# and re-enable pcbparts / kipart with /mcp
```

### Not turned off: KiCad-specific programs on the machine

These are installed in the shell environment, not as Claude Code extensions, so a "vanilla"
session can still find and use them:

- Python packages: `skidl` 3.0.0 (editable, from `~/projects/KiCad/tools/skidl`),
  `schematizer` 0.2.0, `kipart` 2.8.0, `kinet2pcb` 1.1.4, `kinparse` 1.2.4, `kicad-skip` 0.2.5,
  `pykicad` 0.1.1.
- CLIs: `skidl-part-search`.
- `~/.claude/settings.json` → `additionalDirectories` gives every session access to the
  kipart, schematizer and skidl-schematic source trees.

Whether these count as "assistance" is a judgment call; see the README's risks. The
transcript records which ones a run used.

## 3. Verify

From a run directory, after step 2:

```bash
cd ~/projects/AI/ai-circuit-design-tests/null-tests/generate-1 && claude mcp list
```

Output at setup time, before step 2 (pcbparts and kipart still connected):

```
claude.ai Claude Docs: https://api.anthropic.com/v1/pages/mcp - ✔ Connected
claude.ai Google Drive: https://drivemcp.googleapis.com/mcp/v1 - ✔ Connected
konnect: .../konnect-v0.12.1-x86_64-unknown-linux-gnu/konnect  - ⊘ Disabled for this project (re-enable via /mcp)
pcbparts: https://pcbparts.dev/mcp (HTTP) - ✔ Connected
kicad: .../kicad-mcp-server/run_kicad10.py - ⊘ Disabled for this project (re-enable via /mcp)
eda-kicad: .../eda-agent/.venv/bin/eda-agent --backend kicad --headless - ⊘ Disabled for this project (re-enable via /mcp)
kcaa: .../kicad_ai_assistant/.venv/bin/kcaa  - ⊘ Disabled for this project (re-enable via /mcp)
kipart: /home/devb/.pyenv/versions/3.14.7/bin/kipart-mcp  - ✔ Connected
```

Inside the run session, `/mcp`, `/agents` and `/memory` should show no KiCad-specific server,
agent or memory.

```bash
~/bin/kicad10-root/bin/kicad-cli --version
# 10.0.4
```

## Notes

- **An earlier null test existed.** `~/.claude/projects/` already holds transcripts for
  `null-tests/analyze-1` (2026-10-14) and `null-tests/generate-1` (2026-10-14/15, two
  sessions), but there was no `null-tests/` directory and it was never committed. The
  `generate-1` session is the one that wrote the `kicad10-skidl-setup` memory. `session_cost.py`
  picks the most recent session that has token usage, so a new run's cost won't include those
  sessions, as long as `claude_cost.txt` is written at the end of the new run. Don't use
  `claude --continue` / `--resume` in the run directories, or a run could pick up an old
  session.
- **Sibling results are readable.** The other tools' designs and reports live next to the run
  directories. The design prompt says not to use them; the analysis prompt doesn't. This is
  the same for every tool tested here.
