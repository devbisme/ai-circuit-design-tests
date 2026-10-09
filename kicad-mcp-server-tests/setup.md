# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed.
- **KiCad with its bundled Python.** The server imports KiCad's `pcbnew` module for full PCB
  analysis. These tests used KiCad 10.0.4 at `~/bin/kicad10-root` (bundled Python 3.11.2),
  alongside the system KiCad 9.0.9.
- `kicad-cli` from the same KiCad (used for ERC, DRC, netlists and exports).
- `git`.

## Quick option: let Claude Code install it

This is how it was installed for these tests. I did the simplest thing possible: I started
`claude` and gave it the prompt:

```
Install the kicad-mcp-server using the instructions at https://github.com/Seeed-Studio/kicad-mcp-server.
```

It worked! The steps below describe what that produced on this machine.

## 1. Get the server

```bash
git clone https://github.com/Seeed-Studio/kicad-mcp-server.git
cd kicad-mcp-server           # these tests used commit 4085d3f (2026-09-28), version 0.1.0
```

## 2. Install into KiCad's Python

The README recommends installing into KiCad's bundled Python so the server can use `pcbnew`.
Without it, the server falls back to text parsing of `.kicad_pcb` files and loses precise
track lengths, design rules and signal/power-integrity analysis.

The KiCad 10 bundled Python ignores `PYTHONPATH`, so on this machine the dependencies went
into a local `.kicad10-deps/` directory (fastmcp 3.4.8, mcp 1.30.0, and the rest of
`requirements.txt`), and a small launcher, `run_kicad10.py`, adds that directory and `src/`
to the path before starting the server:

```python
# Launch kicad_mcp_server under KiCad 10's bundled Python (which ignores PYTHONPATH).
import os, runpy, site, sys
here = os.path.dirname(os.path.abspath(__file__))
site.addsitedir(os.path.join(here, ".kicad10-deps"))
sys.path.insert(0, os.path.join(here, "src"))
runpy.run_module("kicad_mcp_server", run_name="__main__", alter_sys=True)
```

`requirements.txt` pins `mcp<2` and `fastmcp>=3.2,<4`. Its comments say that without these
bounds pip resolves a combination that fails on import (`No module named 'pydantic_settings'`).

## 3. Register the MCP server with Claude Code

`-s user` makes it available in every project:

```bash
claude mcp add -s user kicad -- ~/bin/kicad10-root/bin/python3.11 \
    /path/to/kicad-mcp-server/run_kicad10.py
```

## 4. Verify

```bash
claude mcp get kicad          # Scope: User config ... Status: ✔ Connected
~/bin/kicad10-root/bin/python3.11 -c 'import pcbnew; print(pcbnew.Version())'   # 10.0.4
```

Inside a session, `/mcp` should list `kicad` as **connected**, with tools named
`mcp__kicad__*`. To confirm `pcbnew` is active, ask for `get_pcb_statistics` on a board: the
output includes a **Design Rules** section only when `pcbnew` is in use (it did here).

## Notes

- **Use the KiCad 10 `kicad-cli`.** The test boards are KiCad 10 files. The system KiCad 9
  `kicad-cli` fails on them with `Failed to load board`. The server itself runs under the
  KiCad 10 Python, so its tools work; direct shell calls need
  `~/bin/kicad10-root/bin/kicad-cli`.
- The server analyzes and exports existing designs. It has a few schematic-editing tools
  (`add_component_from_library`, `add_wire`, labels), but those were not used here.

Source: [kicad-mcp-server README](https://github.com/Seeed-Studio/kicad-mcp-server),
`requirements.txt`, and the installation on this machine.
