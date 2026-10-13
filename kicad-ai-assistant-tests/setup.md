# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed.
- **KiCad 10.0+.** The README says it was tested on KiCad 10.0 on Linux and Windows. These tests
  used KiCad 10.0.4 at `~/bin/kicad10-root`, alongside the system KiCad 9.0.9.
- **[`uv`](https://github.com/astral-sh/uv).** The setup script uses it to create the venv
  and to install Python 3.13.
- **A running KiCad, for some tools.** The PCB-side tools that change the live board
  (`update_pcb_from_schematic`, `refill_zones`, `run_drc_check`, `save_document`,
  `reload_kicad`) talk to the KiCad GUI over its IPC API (`kicad-python`). Enable the API
  server under **Preferences → Plugins → KiCad API server**. Most schematic tools edit the
  `.kicad_sch` files directly through `kicad-skip`.
- **An LLM API key, but only for the plugin's in-KiCad chat panel.** Claude Code supplies the
  LLM when it uses the MCP server, so these tests didn't configure a key.

## What the tool is

KiCad-AI-Assistant has two parts:

- **A KiCad action plugin** (`kicad_plugin/`). It adds a wxPython chat panel to the PCB
  editor that runs its own agent loop against OpenAI, Anthropic, Bedrock or Ollama. It also
  has the Freerouting integration (`autorouter.py`).
- **An MCP server, `kcaa`** (`kcaa/`). The plugin starts it as a subprocess in a reduced
  "plugin" profile. Run on its own (the "Standalone MCP Server" section of the README), it uses
  the "full" profile, which is meant for external MCP clients. **That is how Claude Code uses
  it in these tests.** The plugin's chat panel is not used.

## Quick option: let Claude Code install it

This is how it was installed for these tests. I started `claude` in this repo and asked it to
follow `new_tool_prompt.txt`, which included:

```
Install the tool as instructed by its repository.
```

Claude read the repo's documentation and did the steps below. Some details differ from the
README:

- Claude Code's auto-mode classifier blocked the one-shot `make dist-plugin` +
  `./setup_plugin.sh` command twice, the second time after I approved it. So Claude ran each
  step by hand: copying the plugin files, creating the venv, `uv pip install`, and downloading
  the Freerouting JAR. The result is the same as the script's, except that there's no
  intermediate zip.
- It registered the standalone server with Claude Code. The README describes a `.env` file
  instead.
- It pointed the server at the KiCad 10 AppImage's libraries and `kicad-cli`, not the system
  KiCad 9.
- It set `KCAA_SKILLS_DIR` (see [Notes](#notes)).

A different session may make different choices, so check the result against the steps below.

## 1. Install the plugin and its venv

```bash
cd ~/tmp/DOWNLOADS
git clone https://github.com/paul356/KiCad-AI-Assistant
cd KiCad-AI-Assistant            # commit ce4161f, 2026-10-09, kcaa 0.2.7
make dist-plugin                 # -> dist/kicad_ai_assistant.zip (plugin files + VERSION)

P=~/.local/share/kicad/10.0/scripting/plugins
mkdir -p $P
unzip dist/kicad_ai_assistant.zip -d $P
cd $P/kicad_ai_assistant
./setup_plugin.sh
```

`setup_plugin.sh` does three things:

1. `uv venv .venv --python 3.13`
2. `uv pip install kcaa==<VERSION> pymupdf`. Note that this installs **`kcaa` from PyPI**, not
   from the clone. The clone only supplies the plugin files and the version number.
3. Downloads `freerouting-2.2.3.jar` into the plugin directory.

Instead of building from source, you can download `kicad_ai_assistant.zip` from the
[Releases page](https://github.com/paul356/KiCad-AI-Assistant/releases).

Installed versions: `kcaa` 0.2.7 and `kicad-python` 0.8.0.

## 2. Configure the MCP server

```bash
P=~/.local/share/kicad/10.0/scripting/plugins/kicad_ai_assistant
claude mcp add -s user kcaa \
  -e KICAD_VERSION=10.0 \
  -e KICAD_APP_PATH=$HOME/bin/kicad10-root/usr/share/kicad \
  -e KICAD_CLI_PATH=$HOME/bin/kicad10-root/bin/kicad-cli \
  -e KCAA_SKILLS_DIR=$P/skills \
  -- $P/.venv/bin/kcaa
```

- **`KICAD_VERSION`** is required. The server raises an error at startup if it can't find a
  version, either here or in the `KICAD10_*` variables that KiCad sets for plugins.
- **`KICAD_APP_PATH`** is where the server looks for the symbol, footprint and template
  libraries. The Linux default is `/usr/share/kicad`, which holds the KiCad 9 libraries on
  this machine.
- **`KICAD_CLI_PATH`** is used by `run_erc` and the other tools that call `kicad-cli`. If it
  isn't set, the server uses `kicad-cli` from `PATH`, which is KiCad 9 here.
- **`KCAA_SKILLS_DIR`**: see [Notes](#notes).
- **Transport** defaults to stdio (`MCP_TRANSPORT`), which is what Claude Code needs.

### Toolset

The full profile registers **129 tools**, counted with `create_server().list_tools()`. The
README's tables list about 110 and are out of date. The ones they leave out include the symbol
library/group tools and the routing tools.

| Area | Examples |
|---|---|
| Symbols / schematic | `search_symbols`, `get_symbol_pins`, `add_symbol_to_schematic`, `connect_pins_with_wire`, `add_label_to_schematic`, `add_sheet_symbol`, `add_sheet_pin`, `create_symbol` |
| Schematic analysis | `extract_schematic_netlist`, `find_component_connections`, `run_erc`, `identify_circuit_patterns`, `validate_project`, `check_reference_conflicts` |
| Footprints / PCB | `search_footprints`, `update_pcb_from_schematic`, `set_footprint_position`, `place_footprint_group`, `score_placement`, `set_board_outline_rect`, `add_zone` |
| Routing | `pcb_route_pad_to_pad` (its own push-and-shove router, `kcaa/router/`), `pcb_add_vias`, `pcb_delete_tracks`, `get_ratsnest` |
| Rules / DRC | `get_effective_design_rules`, `set_net_class_rules`, `add_custom_rule`, `run_drc_check` |
| Misc | `analyze_bom`, `export_bom_csv`, `save_project_version`, `generate_pcb_thumbnail`, `list_skills`, `get_skill` |

It has tools for creating designs (symbol placement, wiring, sheets, footprint placement,
routing) and for reviewing them (ERC, netlist and pattern analysis, validation, BOM). So it is
tested as a **hybrid**:

- `dual-adc-usb-1/`: review of the `konnect-tests/dual-adc-usb-2` project.
- `dual-adc-usb-2/`: a new design from `dual-adc-prompt.txt`.

## 3. Verify

```bash
claude mcp list | grep kcaa
# kcaa: /home/devb/.local/share/kicad/10.0/scripting/plugins/kicad_ai_assistant/.venv/bin/kcaa  - ✔ Connected
```

Inside a session, `/mcp` should list `kcaa` as **connected**. With KiCad 10 open and its API
server enabled, `check_kicad_ipc_connection` should succeed.

## Notes

- **Skills directory.** The skill tools (`list_skills`, `get_skill`) read Markdown workflow
  guides from `KCAA_SKILLS_DIR`. If it isn't set, they fall back to a path relative to the
  `kcaa` package (`kcaa/tools/skill_tools.py`). That works from the clone, but in the PyPI
  install it points to a directory that doesn't exist, so the skill list would be empty.
  `KCAA_SKILLS_DIR` points to the 12 skills shipped with the plugin (schematic wiring and
  placement, PCB placement, routing, zones, DRC rules, and so on).
- **No headless DRC.** `run_drc_check` opens KiCad's DRC dialog over IPC, and you click
  **Run DRC** yourself. It doesn't return the violations to the LLM. ERC is headless through
  `kicad-cli`.
- **Freerouting belongs to the plugin, not the MCP server.** Nothing in `kcaa/` refers to
  Freerouting. Through Claude Code, routing goes through `pcb_route_pad_to_pad`, one
  connection at a time.
- **The schematic editor doesn't refresh.** According to the README, schematic edits made
  through the tools don't show up in an open schematic editor until **File → Reload** (a
  KiCad IPC limitation).
- **Settings file.** `~/.config/kicad/kicad_ai_assistant.json` holds the plugin's LLM settings.
  The standalone server doesn't use it.

Sources: [KiCad-AI-Assistant README](https://github.com/paul356/KiCad-AI-Assistant),
`Makefile`, `pyproject.toml`, `kicad_plugin/setup_plugin.sh`,
`kicad_plugin/server_manager.py`, `kcaa/server.py`, `kcaa/utils/config.py`,
`kcaa/utils/kicad_cli.py`, `kcaa/tools/skill_tools.py`, `kcaa/tools/drc_tools.py`, and the
installation on this machine.
