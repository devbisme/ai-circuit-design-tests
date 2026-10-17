# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed (v2.1.301 at setup
  time).
- **Python 3.11 or later** and [`uv`](https://github.com/astral-sh/uv) for the CLI.
- **KiCad 10.0.** The README says it was tested with 10.0.4. These tests use KiCad 10.0.4 at
  `~/bin/kicad10-root` (`kicad-cli`, the bundled Python 3.11 `pcbnew`), alongside the system
  KiCad 9.0.9. `boardforge doctor` found the KiCad 10 install by itself.
- **Freerouting 2.4 or later** (optional; the built-in A* router handles small boards).
  Found at `~/bin/freerouting/linux-x64/freerouting-2.4.1-linux-x64/bin/freerouting`.
- **ngspice 44 or later** (optional, for the review gate's SPICE checks): 44.2 at
  `/usr/local/bin/ngspice`.
- **pdftotext** (optional, to check that a downloaded datasheet names the part):
  `/usr/bin/pdftotext`.
- **No API key.** Claude Code is the only LLM.
- **No running KiCad GUI.** Everything is headless; KiCad is only for viewing results.

## What the tool is

boardforge has two parts:

- **A Python CLI, `boardforge`.** It takes a directory with a SKiDL file and a
  `boardforge.toml` and runs the physical pipeline: C1 SKiDL → netlist → labels-only KiCad
  schematic (via schematizer) with SKiDL and KiCad ERC and netlist parity; C2 board; C3
  placement; C4 routing (Freerouting, then A*); C5 checks (DRC, geometry, vendored
  kicad-happy 2.3.1 analyzers); C6 fab outputs (JLCPCB Gerbers, BOM, CPL). It also has the
  B4 review gate (`boardforge review`: `constraints.json`, ngspice path testbenches,
  datasheet, package and BOM checks), a datasheet cache (`boardforge datasheets ...`),
  `render`, `status` and `doctor`.
- **A Claude Code plugin** (`plugin/`, adapted from skidl-skills). It has 4 skills
  (`new-circuit`, `design-review`, `erc-rules`, `find-part`), 7 agents (`circuit-architect`,
  `part-sourcer`, `datasheet-librarian`, `skidl-coder`, `skidl-block-coder`,
  `skidl-assembler`, `erc-reviewer`), rules files, and 4 hooks (SessionStart status banner,
  PreToolUse Bash guard, PostToolUse check after Write/Edit, Stop check). `/new-circuit`
  drives the phases: requirements → architecture → sourcing → datasheets → SKiDL code →
  review → board. `claude plugin details` estimates ~1.3k tokens of always-on context.

Claude Code uses both: the plugin's agents and skills decide, and they call the CLI for every
deterministic step. The plugin's `find-part` skill prefers the **pcbparts** MCP server (live
JLCPCB stock, KiCad symbols) and falls back to `skidl-part-search` if it isn't connected.

## Quick option: let Claude Code install it

It was installed for these tests by Claude Code via `/new-tool`, given the repo URL. The
steps below are what that session did, including where it departed from the README.

## 1. Install the CLI

```bash
uv tool install --force "boardforge[analysis]"   # PyPI 0.1.0; also installs skidl 3.0.0, schematizer 0.2.0
boardforge --version                             # 0.1.0
```

Deviation: `--force`. A `boardforge` uv tool already existed, installed editable from
`~/projects/AI/boardsmith` with editable `skidl` and `schematizer`. That directory was renamed
to `~/projects/AI/boardforge`, so the old install failed with
`ModuleNotFoundError: No module named 'boardforge'`. `--force` replaced it with the PyPI
release, which also means **PyPI `skidl` 3.0.0 and `schematizer` 0.2.0** inside the tool's
venv instead of the editable development copies. PyPI 0.1.0 corresponds to the repo's
`master` at 437b70d (2026-10-16).

No `~/.config/boardforge/config.toml` was needed; `boardforge doctor` found KiCad 10,
Freerouting and ngspice on its own.

## 2. Install the plugin

The README says:

```bash
claude plugin marketplace add devbisme/boardforge
claude plugin install boardforge@boardforge
```

Deviation: **not done.** The same plugin was already installed at user scope as
`boardforge@devbisme-skills` (marketplace `devbisme/devbisme-skills`, which points at
`boardforge.git`, `plugin/`, ref `0.1.0`), at commit 437b70d, the same commit as the PyPI
release. It is disabled in `~/.claude/settings.json`. Adding the `boardforge` marketplace
would install a second copy under another name; if both were enabled, the agents and hooks
would load twice.

Instead, the plugin is enabled **only in the run directory**, by
`generate-1/.claude/settings.local.json`:

```json
{
  "enabledPlugins": { "boardforge@devbisme-skills": true },
  "permissions": { "allow": ["Bash(boardforge *)"] },
  "skillOverrides": { "konnect": "off", "kicad-library": "off", "kicad-manufacture": "off",
                      "kicad-pcb": "off", "kicad-review": "off", "kicad-schematic": "off",
                      "kicad-harness": "off" }
}
```

The `skillOverrides` are copied from the repo root's `.claude/settings.local.json`. Project
settings are read from the directory `claude` starts in, so the root copy may not apply in a
run directory.

## 3. Configure

Nothing else. The plugin has no MCP server of its own. **pcbparts** is the one external
dependency the plugin recommends; see [Contamination](#contamination).

## Files and config touched outside this repo

| What | Where | Undo |
|---|---|---|
| boardforge uv tool (replaced the broken editable install) | `~/.local/share/uv/tools/boardforge/`, `~/.local/bin/boardforge` | `uv tool uninstall boardforge`, or go back to an editable dev install (untested): `uv tool install --force -e ~/projects/AI/boardforge --with jsonschema --with referencing --with-editable ~/projects/KiCad/tools/skidl --with-editable ~/projects/KiCad/tools/schematizer` |
| Plugin | already installed: `~/.claude/plugins/cache/devbisme-skills/boardforge/0.1.0/` | nothing changed |
| Datasheet cache (created by runs, empty at setup) | `~/.cache/boardforge/datasheets/` | `rm -rf` |
| Plugin hook state | `${TMPDIR:-/tmp}/boardforge-plugin/` | `rm -rf` |

Inside this repo: `boardforge-tests/generate-1/.claude/settings.local.json`.

## 4. Verify

```bash
boardforge doctor
```
```
kicad-cli: /home/devb/bin/kicad10-root/bin/kicad-cli (10.0.4)
KiCad python: /home/devb/bin/kicad10-root/bin/python3.11
symbols: /home/devb/bin/kicad10-root/share/kicad/symbols
footprints: /home/devb/bin/kicad10-root/share/kicad/footprints
router freerouting: ok /home/devb/bin/freerouting/linux-x64/freerouting-2.4.1-linux-x64/bin/freerouting
router astar: ok
ngspice: /usr/local/bin/ngspice
fab: jlcpcb tier multilayer
skidl 3.0.0
schematizer 0.2.0
datasheet cache: /home/devb/.cache/boardforge/datasheets
pdftotext: /usr/bin/pdftotext
```

(It also printed a config warning because it was run from the repo root, which has no
`boardforge.toml`; it then checks machine settings only.)

```bash
cd ~/projects/AI/ai-circuit-design-tests/boardforge-tests/generate-1 && claude plugin list
```
```
  ❯ boardforge@devbisme-skills
    Version: 0.1.0
    Scope: user
    Status: ✔ enabled
    Note: Disabled in ~/.claude/settings.json but still loads — project, gitignored settings enable it, ...
```

From `boardforge-tests/` (one level up) the same plugin shows `✘ disabled`, so the setting
applies only to the run directory. Inside the run session, the SessionStart hook should
print `=== boardforge plugin ===` and `✓ KiCad libraries: ...`.

## Contamination

State at setup time (2026-10-16), from `generate-1/`:

| Item | State | Recommendation |
|---|---|---|
| MCP `konnect`, `kicad`, `eda-kicad`, `kcaa`, `kipart` | disabled for this repo | keep disabled |
| MCP **`pcbparts`** | **disabled for this repo** (left that way after the null tests) | **re-enable for this run**: the plugin's `find-part` skill is written around it, and it was connected for the other tools' runs. Without it the run falls back to `skidl-part-search` |
| MCP `claude.ai Claude Docs`, `claude.ai Google Drive` | connected | none (not KiCad) |
| Skills `konnect`, `kicad-library`, `kicad-manufacture`, `kicad-pcb`, `kicad-review`, `kicad-schematic`, `kicad-harness` (`~/.claude/skills/`) | off via `skillOverrides` (repo root and `generate-1/`) | none |
| `~/.claude/skills/skidl-skills` | symlink, no top-level `SKILL.md`, not loaded | none |
| Plugins `kicad-happy`, `kicad-pro`, `skidl-skills`, `datasheet-to-symbol-lib` | disabled | keep disabled; the boardforge plugin says not to enable skidl-skills with it |
| Subagents `kicad-design-review-agent`, `kicad-schematic-build-agent` | moved to `~/.claude/agents.off/` for the null tests | keep them there for this run |
| Repo auto-memory | moved to `memory.off/` for the null tests; `memory/` is empty | keep it aside for this run: `kicad10-skidl-setup.md` holds SKiDL/KiCad 10 tips |

Commands (not run by the setup session):

```bash
# pcbparts: in a claude session in this repo, /mcp → pcbparts → Enable. Then check:
cd ~/projects/AI/ai-circuit-design-tests/boardforge-tests/generate-1 && claude mcp list | grep pcbparts
# After the run, disable it again with /mcp if later runs should not have it.

# After all runs, restore what the null tests moved aside:
mv ~/.claude/agents.off/kicad-*.md ~/.claude/agents/
M=~/.claude/projects/-home-devb-projects-AI-ai-circuit-design-tests
mv $M/memory.off $M/memory    # merge by hand if a run wrote new memory
```

## Notes

- **No analysis mode for an existing KiCad project.** Every CLI command except `doctor` needs
  a `boardforge.toml` and a SKiDL design, and the `design-review` skill reviews a SKiDL
  circuit and its handoffs. So boardforge is tested only as a generator.
- **`/new-circuit` interviews the user and asks for approval between phases.** The design
  prompt says not to wait for input. Expect the run to need "approved, continue" style
  replies, and record them in the README.
- **Routing is slow.** The plugin's rules say `boardforge run --from c4` takes 10–45 min.
