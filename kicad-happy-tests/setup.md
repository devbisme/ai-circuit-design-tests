# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed and logged in. These
  tests used Claude Code 2.1.293.
- **Python ≥ 3.10.** The analysis scripts use only the standard library, so there is nothing
  to `pip install`. These tests used Python 3.14.7.
- **KiCad is not needed at runtime.** The scripts parse saved `.kicad_sch` / `.kicad_pcb`
  files directly (KiCad 5–10 are supported).
- Optional:
  - A SPICE simulator for the `spice` skill: `ngspice`, LTspice or Xyce (auto-detected).
    These tests used ngspice 44.2. Without one, simulation is skipped and the rest of the
    analysis still runs.
  - Python packages `requests` (better HTTP) and `playwright` (datasheet sites that need
    JavaScript), and the `pdftotext` command for PDF text extraction. These tests had
    `requests` 2.34.2 and `pdftotext`, but not `playwright`.
  - Distributor API keys. Without them, the sourcing skills use web search instead:

    | Service   | Environment variable(s)                      |
    |-----------|----------------------------------------------|
    | DigiKey   | `DIGIKEY_CLIENT_ID`, `DIGIKEY_CLIENT_SECRET` |
    | Mouser    | `MOUSER_SEARCH_API_KEY`                      |
    | element14 | `ELEMENT14_API_KEY`                          |
    | LCSC      | none (free community API)                    |

    None were set for these tests.
 - Copy the KiCad project files from /home/devb/projects/AI/ai-circuit-design-tests/konnect-tests/dual-adc-usb-2
   so that kicad-happy will have something to work with.

## 1. Install the plugin

Inside a Claude Code session:

```
/plugin marketplace add aklofas/kicad-happy
/plugin install kicad-happy@kicad-happy
/reload-plugins
```

Or from the shell (this is how it was installed for these tests):

```bash
claude plugin marketplace add aklofas/kicad-happy
claude plugin install kicad-happy@kicad-happy      # user scope by default
```

This installs version 2.3.1 into `~/.claude/plugins/cache/kicad-happy/kicad-happy/2.3.1/`. It
adds 11 skills, namespaced as `kicad-happy:<skill>`: `kicad`, `spice`, `emc`, `datasheets`,
`bom`, `digikey`, `mouser`, `lcsc`, `element14`, `jlcpcb`, `pcbway`. There are no agents,
hooks or MCP servers. `claude plugin details` estimates ~3.2k tokens of always-on context per
session. Each skill call costs more; the `kicad` skill alone costs ~31k.

A manual install that symlinks `skills/*` into `~/.claude/skills/` is also available. See
[install-guidance.md](https://github.com/aklofas/kicad-happy/blob/main/install-guidance.md#install-manual-symlinks).

## 2. Verify

```bash
claude plugin list               # kicad-happy@kicad-happy  Version: 2.3.1  Status: enabled
claude plugin details kicad-happy@kicad-happy
```

Smoke test: run the schematic analyzer directly on an existing design:

```bash
P=~/.claude/plugins/cache/kicad-happy/kicad-happy/2.3.1/skills/kicad/scripts
python3 $P/analyze_schematic.py ../konnect-tests/dual-adc-usb-2/power.kicad_sch > sch.json
```

When given a sub-sheet, the analyzer finds the root sheet and analyzes the whole project. On
this machine it exited 0 and wrote JSON with 80 findings (7 errors, 3 warnings, 70 info).

## 3. Upgrade

The README warns that `/plugin update` may not find new versions
([anthropics/claude-code#36317](https://github.com/anthropics/claude-code/issues/36317)).
To upgrade, delete the cache and reinstall:

```bash
rm -rf ~/.claude/plugins/cache/kicad-happy ~/.claude/plugins/marketplaces/kicad-happy
claude plugin marketplace add aklofas/kicad-happy
claude plugin install kicad-happy@kicad-happy
```

## Notes

- **Overlap with Konnect.** The Konnect skills (`kicad-review`, `kicad-schematic`, …) are also
  installed in `~/.claude/skills` on this machine, and their triggers overlap with
  `kicad-happy:kicad` ("review my design", "check my schematic"). Disable one of them while
  testing the other so you know which tool did the work:
  `claude plugin disable kicad-happy@kicad-happy`.
- kicad-happy reviews and analyzes designs that already exist. It does not create
  schematics or layouts.
- It can also run as a GitHub Action that reviews PRs. See
  [github-action.md](https://github.com/aklofas/kicad-happy/blob/main/github-action.md).
  That was not used here.

Source: [kicad-happy README](https://github.com/aklofas/kicad-happy),
[install-guidance.md](https://github.com/aklofas/kicad-happy/blob/main/install-guidance.md)
(commit `0684046`, 2026-10-05), and the installation on this machine.
