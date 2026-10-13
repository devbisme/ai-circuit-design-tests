# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed.
- **KiCad 9 or 10.** The README says it was tested on 10.0.5. These tests used KiCad 10.0.4 at
  `~/bin/kicad10-root`, alongside the system KiCad 9.0.9.
- **`kicad-cli`, `rsvg-convert` and `python3`** on `PATH` (checked by `setup.sh`).
  `rsvg-convert` (Debian/Ubuntu package `librsvg2-bin`) turns the `kicad-cli` SVG exports into
  the PNGs that `kh view` / `kh sview` produce.
- **KiCad's `pcbnew` Python module**, seen through a venv made with `--system-site-packages`.
- **No API key.** The tool is a skill plus a CLI; Claude Code is the LLM.
- **A running KiCad, only for the live layer.** `kh live` / `kh exec` edit a board open in the
  KiCad GUI over its IPC API (kicad-python). Enable it under **Preferences → Plugins →
  Enable KiCad API**, and keep a PCB editor window open, not just the project manager. Everything
  else (library lookup, board/schematic queries, renders, DRC/ERC, netlist → board, placement)
  works on files, headless.

## What the tool is

kicad-harness has two parts:

- **An Agent Skill** (`SKILL.md` plus `docs/`). It tells the agent how to work: look up every
  symbol/footprint id, render and look at every placement, write schematics as `.kicad_sch`
  text, use the Specctra bridge for autorouting, generate missing footprints from datasheets.
- **A Python CLI, `kh`** (`kicad_harness/`). Every subcommand prints JSON:

  | Area | Commands |
  |---|---|
  | Libraries | `sym` (search, `--pins`, `--sexpr`), `fp`, `validate` |
  | Board / schematic queries | `info`, `ls`, `nets`, `netlist`, `bom` |
  | Renders | `view` (board region → PNG), `sview` (schematic sheet → PNG) |
  | Checks | `drc` (grouped, `--refill`), `erc` |
  | Generation | `board-from-netlist`, `place`, `outline` |
  | Live (IPC) | `live`, `exec <script.py>` |

  Footprint generation has no CLI. It is a documented procedure (`docs/footprints/`) plus the
  KiCad wizard templates in `templates/`.

Claude Code uses both: the skill as a user-level skill, and `kh` from Bash.

The skill also tells the agent to **edit, commit and push the skill repo itself** whenever it
finds something wrong ("You have standing permission from the repo owner to commit and push
these fixes"). See [Notes](#notes).

## Quick option: let Claude Code install it

This is how it was installed for these tests. I started `claude` in this repo and ran
`/new-tool https://github.com/zxkmm/kicad-harness`. Claude read the repo's documentation and did
the steps below. Deviations from the README:

- **The venv is built on KiCad 10's bundled Python 3.11**, not the system `python3`.
  `setup.sh` runs `python3 -m venv --system-site-packages`, which on this machine would give
  Python 3.14 with no `pcbnew` (the system `pcbnew` belongs to KiCad 9 and Python 3.12).
  KiCad 10's `pcbnew` lives in the AppImage tree and only loads in its own `python3.11`.
- **`setup.sh` was not run.** It would fail its tool check, because `rsvg-convert` isn't
  installed, and it would build the venv on the wrong Python. Its steps were done by hand,
  using `uv pip` because the bundled Python has no `pip`.
- **A `kh` wrapper in `~/.local/bin`** puts KiCad 10's `kicad-cli` ahead of the system
  KiCad 9 one. `kh` calls a bare `kicad-cli` from `PATH`, and there is no option or env var to
  change that.

A different session may make different choices, so check the result against the steps below.

## 1. Clone and build the venv

```bash
cd ~/tmp/DOWNLOADS
git clone https://github.com/zxkmm/kicad-harness
cd kicad-harness                 # commit db4bcdb, 2026-10-11, package version 0.1.0

# venv on KiCad 10's own python, so `import pcbnew` gives 10.0.4
~/bin/kicad10-root/bin/python3.11 -m venv --system-site-packages --without-pip .venv
uv pip install --python .venv/bin/python -e .
```

Installed: `kicad-harness` 0.1.0 (editable, so the skill directory *is* the code `kh` runs) and
`kicad-python` 0.8.0. The repo's notes were measured with kicad-python 0.7.1.

## 2. Point `kh` at KiCad 10's `kicad-cli`

```bash
H=~/tmp/DOWNLOADS/kicad-harness
mkdir -p $H/.venv/kicad10-bin
ln -s ~/bin/kicad10-root/bin/kicad-cli $H/.venv/kicad10-bin/kicad-cli

cat > ~/.local/bin/kh <<'EOF'
#!/bin/sh
# kicad-harness wrapper (installed for ai-circuit-design-tests/kicad-harness-tests).
# Puts KiCad 10's kicad-cli ahead of the system KiCad 9 one; the venv's python is
# KiCad 10's bundled python3.11, so pcbnew is 10.x too.
H="$HOME/tmp/DOWNLOADS/kicad-harness"
PATH="$H/.venv/kicad10-bin:$PATH" exec "$H/.venv/bin/kh" "$@"
EOF
chmod +x ~/.local/bin/kh
```

`~/.local/bin` comes before `/usr/bin` on `PATH` here, so `kh` from any directory is the wrapper.
`python -m kicad_harness` with some other Python would bypass it; the skill mentions that form
as an alternative.

## 3. Install the skill

As the README says, a symlink rather than a copy:

```bash
ln -s ~/tmp/DOWNLOADS/kicad-harness ~/.claude/skills/kicad-harness
```

This is a **user-level** skill, so it is active in every Claude Code session, not just these
run directories.

## 4. Install `rsvg-convert` (manual, needs sudo)

```bash
sudo apt install librsvg2-bin
```

Without it, `kh view` and `kh sview` fail with
`RuntimeError: required tool not found on PATH: rsvg-convert`. All other commands work.

## Files touched outside this repo

| Path | What | Uninstall |
|---|---|---|
| `~/tmp/DOWNLOADS/kicad-harness/` | clone, `.venv/` (KiCad 10 python3.11), `.venv/kicad10-bin/kicad-cli` symlink | `rm -rf` |
| `~/.local/bin/kh` | wrapper script | `rm` |
| `~/.claude/skills/kicad-harness` | symlink to the clone | `rm` |
| `librsvg2-bin` (apt) | `rsvg-convert` | `sudo apt remove librsvg2-bin` |

Nothing was added to `~/.claude.json` or any MCP config, and no KiCad config files were changed.

## Verify

On a scratch copy of `analyze-1/`'s KiCad files:

```bash
$ kh info --pcb .
{ "components": 174, "nets": 214, "copper_layers": 4, "track_segments": 2994,
  "board_box_mm": { "x": 49.975, "y": 49.975, "w": 140.05, "h": 90.05 }, ... }

$ kh drc --pcb .          # -> "clean": true
$ kh erc --sch .          # -> 203 warnings, 201 of them lib_symbol_issues (see Notes)
$ kh netlist --sch . --out n.net && grep -m1 -o '(tool "[^"]*")' n.net
(tool "Eeschema 10.0.4")  # confirms the KiCad 10 kicad-cli is used

$ kh validate --symbols "Device:R,Analog_ADC:LTC2290" --footprints "Resistor_SMD:R_0603_1608Metric"
# Device:R and the footprint valid; LTC2290 invalid with suggestion "Analog_ADC:LTC2290xUP"

$ kh live
# "connected": false, with instructions to enable the KiCad API (no KiCad running)
```

`kh view` was **not verified**, because `rsvg-convert` wasn't installed at setup time.

In a Claude Code session started in a run directory, `/skills` should list `kicad-harness`.

## Notes

- **Library lookups use the KiCad 9 libraries.** `kh sym`/`fp`/`validate` read the global
  `sym-lib-table`/`fp-lib-table` of every `~/.config/kicad/<version>/` directory, newest
  first. The KiCad 10 tables nest the default libraries through a stale `/tmp/.mount_*`
  AppImage path, so they add nothing. The 9.0 tables resolve to `/usr/share/kicad/symbols` and
  `/usr/share/kicad/footprints` (KiCad 9.0.9 libraries). Even with the KiCad 10 tables fixed,
  `kh` would find no symbols there: KiCad 10 ships symbols as `.kicad_symdir` directories, and
  `libs.py` only reads single-file `.kicad_sym` libraries. Symbol names are mostly the same
  between 9 and 10, and the skill copies each symbol's body into the schematic's
  `lib_symbols`, so this probably works. But `kh` is not looking at the libraries KiCad 10
  itself uses.
- **ERC noise.** 201 of the 203 ERC warnings on the Konnect design are `lib_symbol_issues`
  ("configuration does not include the symbol library…"), caused by the same stale global
  table. They are environment problems, not design problems. kcaa run 1 saw the same thing.
- **Self-editing skill.** `SKILL.md` and `docs/SELF_ITERATION.md` tell the agent to fix the
  skill repo when it finds a problem, then commit and **push** in the same session, and to
  log unfixed problems in `ISSUES.md`. The clone's `origin` is the upstream GitHub repo. That
  has two consequences for these tests:
  - A run may change the tool. Edits from `analyze-1` would be in effect for `generate-1`.
    Check `git -C ~/tmp/DOWNLOADS/kicad-harness status`/`log` after each run, and reset to
    `db4bcdb` between runs if you want both runs to use the same tool.
  - A run may try to push. The push would fail without write access to `zxkmm/kicad-harness`,
    but to be safe, disable it:
    `git -C ~/tmp/DOWNLOADS/kicad-harness remote set-url --push origin DISABLED`.
  The user-level CLAUDE.md requires permission for git operations, which conflicts with the
  skill's "standing permission". Either the agent asks, or it ignores one of the two rules.
  Either outcome is worth noting in the run.
- **No autorouter.** The skill documents driving an external router through
  `pcbnew.ExportSpecctraDSN` / `ImportSpecctraSES`, but doesn't ship one. Freerouting is
  already on this machine from earlier runs.
- **No schematic API.** Schematics are written and edited as `.kicad_sch` text
  (`docs/RECIPES.md`, `docs/SCHEMATIC_EDITS.md`). The live layer is PCB-only.
- **`board.save()` over IPC loses data** (locked graphics, User-layer geometry), per the skill.
  It recommends offline `kh place` and saving from the GUI.

Sources: [kicad-harness README](https://github.com/zxkmm/kicad-harness), `SKILL.md`,
`setup.sh`, `pyproject.toml`, `docs/SELF_ITERATION.md`, `ISSUES.md`, `kicad_harness/libs.py`,
`kicad_harness/checks.py`, `kicad_harness/render.py`, and the installation on this machine.
