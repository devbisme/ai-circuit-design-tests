# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed.
- **Python ≥ 3.11.** `pyproject.toml` lists 3.11 and 3.12. These tests used 3.12.14 from pyenv.
- **An EDA tool the server can drive.** eda-agent has three backends:
  - `altium` (the default and most complete): Altium Designer AD20+. **Windows only.**
  - `kicad`: KiCad 9+ with the IPC API server enabled. **Used for these tests**, because
    this machine runs Linux. These tests used KiCad 10.0.4 at `~/bin/kicad10-root`,
    alongside the system KiCad 9.0.9.
  - `easyeda`: EasyEDA Pro with a browser extension.
- **A running KiCad** for most tools. Every KiCad-backend tool is labelled `live_only` in
  `docs/TOOL_REFERENCE.md`. The server talks to the KiCad GUI over its protobuf IPC socket,
  and it even finds `kicad-cli` by asking the running KiCad for its path. Enable the API
  server in KiCad under **Preferences → Plugins → KiCad API server**. The exception is the
  `kicad_generate_*` tools: despite the label, they write files directly from the design plan
  without using the IPC connection (`src/eda_agent/tools/kicad.py`).

`pyproject.toml` lists only `Operating System :: Microsoft :: Windows`, and neither the
README nor `docs/BACKENDS.md` says whether the KiCad backend works on Linux. The Windows-only
dependencies (`pywin32`, `comtypes`) are skipped off Windows. The install and MCP connection
work on Linux. Whether the tools themselves work is tested by the runs.

## Quick option: let Claude Code install it

This is how it was installed for these tests. I started `claude` in this repo and asked it to
follow `new_tool_prompt.txt`, which included:

```
Install the tool as instructed at https://github.com/salitronic/eda-agent.
```

Claude read the repo's documentation and did the steps below on its own. It made several
choices that the repo's instructions don't specify:

- It cloned the repo to `~/tmp/DOWNLOADS/`.
- It installed into a venv inside the clone, not into a global Python.
- It added the `render` extra along with `kicad`.
- It registered the server as `eda-kicad`, because the Seeed kicad-mcp-server already uses
  `kicad`.
- It set two environment variables to stop the server writing a Windows-path file on Linux
  (see [Notes](#notes)).

A different session may make different choices, so check the result against the steps below.

## 1. Install the server

```bash
cd ~/tmp/DOWNLOADS
git clone https://github.com/salitronic/eda-agent
cd eda-agent                    # commit 8e659a2, 2026-10-07, version 0.6.1 (Alpha)
~/.pyenv/versions/3.12.14/bin/python -m venv .venv
.venv/bin/python -m pip install -e '.[kicad,render]'
.venv/bin/eda-agent --help
```

The README's install is `python -m pip install -e .`, plus `pip install -e .[kicad]` for the
KiCad backend. The `kicad` extra pulls in `kicad-python` (0.8.0 here), KiCad's official IPC
client. The `render` extra adds matplotlib for PNG previews of design plans.

There are no GitHub releases. The tags stop at `v0.6.0`, so this install is from `main`.

## 2. Configure the MCP server

```bash
W=$HOME/.local/share/eda-agent
mkdir -p $W/workspace
claude mcp add -s user eda-kicad \
  -e EDA_AGENT_BACKEND=kicad \
  -e EDA_AGENT_HEADLESS=1 \
  -e EDA_AGENT_WORKSPACE=$W/workspace \
  -e EDA_AGENT_POINTER_FILE=$W/workspace-path.txt \
  -- $HOME/tmp/DOWNLOADS/eda-agent/.venv/bin/eda-agent --backend kicad --headless
```

The README's suggested command is `claude mcp add -s user kicad -e EDA_AGENT_BACKEND=kicad
eda-agent`. The differences:

- **Name `eda-kicad`.** The Seeed kicad-mcp-server already uses `kicad`. The tools are named
  `mcp__eda-kicad__*`.
- **Full path to the venv's `eda-agent`**, since the venv isn't on `PATH`.
- **`--headless` / `EDA_AGENT_HEADLESS=1`** skips the web dashboard at `127.0.0.1:8766`.
  Claude Code doesn't need it.
- **`EDA_AGENT_WORKSPACE` and `EDA_AGENT_POINTER_FILE`**: see [Notes](#notes).

### Toolset

On the KiCad backend the server exposes 109 tools (from a `tools/list` call), compared with
about 450 on the Altium backend:

| Group | Count | Examples |
|---|---:|---|
| `kicad_*` | 85 | `kicad_generate_project`, `kicad_full_review`, `kicad_review_schematic`, `kicad_compare_sch_pcb`, `kicad_add_track`, `kicad_export_gerbers`, `kicad_run_spice`, `kicad_cli` |
| `pcb_*` | 7 | |
| `design_*` | 6 | `design_validate_plan`, `design_review_plan`, `design_datasheet_checklist` |
| others | 11 | `review_design`, `run_erc`, `run_drc`, `part_search`, `tool_catalog` |

- **Design creation** goes through a JSON `DesignPlan` that the LLM writes.
  `kicad_generate_project` turns it into `.kicad_pro`, `.kicad_sch` and `.kicad_pcb`.
- **The autonomous spec-to-board harness is not available on KiCad.** The `autodesign` skill
  and the `design_autonomy_guide` tool need it, and `skills/README.md` says only the Altium
  and EasyEDA backends register it. So the skill was **not** installed.
- `EDA_AGENT_TOOLSET=minimal` advertises only `tool_catalog` and `tool_invoke`, for clients
  that cap the number of tools. These tests used the full toolset.

## 3. Verify

```bash
claude mcp list | grep eda-kicad
# eda-kicad: /home/devb/tmp/DOWNLOADS/eda-agent/.venv/bin/eda-agent --backend kicad --headless - ✔ Connected
```

Inside a session, `/mcp` should list `eda-kicad` as **connected**. With KiCad 10 open and its
API server enabled, the `kicad_ping` tool should return the KiCad and API versions.

`eda-agent health` and `eda-agent doctor` check the Altium bridge (workspace, DelphiScript
files, canary IPC calls), so they say nothing useful about the KiCad backend.

## Notes

- **Windows-path pointer file.** At startup the server writes the workspace path to a pointer
  file that the Altium DelphiScript reads. Its default location is hard-coded as
  `C:\ProgramData\eda-agent\workspace-path.txt` (`src/eda_agent/config.py`). On Linux that's
  a relative filename, so the server would create a file with that literal name in whatever
  directory Claude Code was started from. `EDA_AGENT_POINTER_FILE` moves it. Without
  `USERPROFILE`, the workspace defaults to `~/EDA Agent/workspace`, and
  `EDA_AGENT_WORKSPACE` moves that out of the home directory.
- **KiCad IPC.** On KiCad 10 the IPC API needs the GUI open with the project loaded. If KiCad
  isn't running, the tools that use the IPC connection return a "KiCad not reachable" error
  instead of falling back to reading the files. The `kicad_generate_*` tools still work.
- **Maturity.** The README labels the project "⚠ Experimental" and says "queries are safer
  than edits". Most of its testing and documentation is on the Altium backend.
- **Offline CLI.** `eda-agent review --offline`, `bom --offline` and `netlist --offline`
  read Altium files (`.SchDoc`/`.PrjPcb`), not KiCad files.

Sources: [eda-agent README](https://github.com/salitronic/eda-agent), `docs/BACKENDS.md`,
`docs/TOOL_REFERENCE.md`, `skills/README.md`, `pyproject.toml`, `src/eda_agent/config.py`,
`src/eda_agent/bridge/kicad_bridge.py`, and the installation on this machine.
