# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed.
- **Python ≥ 3.13.** The server needs 3.13 or 3.14 (`compatibility.yaml`). These tests used
  3.13.15 from pyenv.
- [uv](https://docs.astral.sh/uv/). These tests used uv 0.12.19.
- **KiCad 10.0.x.** It is the primary target. KiCad 9 support was dropped in v3.9.0, and
  KiCad 8 files are read-only. These tests used KiCad 10.0.4 at `~/bin/kicad10-root`,
  alongside the system KiCad 9.0.9.
- `kicad-cli` from the same KiCad. The server runs ERC, DRC and exports through it. Unlike
  the Seeed kicad-mcp-server, it does not use the `pcbnew` Python module.
- Optional:
  - A running KiCad with its IPC API server enabled, for live PCB edits.
  - [Freerouting](https://github.com/freerouting/freerouting) 2.4.1, for autorouting.
  - ngspice, for simulation. These tests used ngspice at `/usr/local/bin/ngspice`.

## Quick option: let Claude Code install it

This is how it was installed for these tests. I started `claude` in this repo and gave it
the prompt:

```
install https://github.com/oaslananka/kicad-mcp-pro.
```

Claude read the repo's documentation and did all of the steps below on its own.
It made several choices that the repo's instructions don't specify:

- It pinned the version with `uv tool install` instead of using `uvx`.
- It installed the skills as a local plugin.
- It replaced the plugin's `.mcp.json`.
- It chose the `full`/`write` profile.
- It named the plugin `kicad-pro`, because the already-installed Seeed server uses `kicad`.

A different session may make different choices, so check the result against the steps
below.

## 1. Install the server

```bash
uv tool install --python 3.13 kicad-mcp-pro==4.1.0
kicad-mcp-pro version          # 4.1.0
```

This puts the server in its own environment under `~/.local/share/uv/tools/kicad-mcp-pro`
and links `~/.local/bin/kicad-mcp-pro`. The README recommends `uvx kicad-mcp-pro`. I didn't
use it because it is unpinned and pulls the latest release from PyPI each time the server
starts.

## 2. Install the skills (Claude Code plugin)

The PyPI package contains only the server. The skills are in the GitHub repo:
`kicad-design-review`, `schematic-review`, `pcb-design`, `drc-check`,
`fabrication-output`, `visual-excellence` and `wired-subcircuit-design`. The repo has a
`.claude-plugin/plugin.json`, but no marketplace file. To install it as a plugin, I cloned
the repo at the release tag and added a local marketplace file to the clone:

```bash
git clone https://github.com/oaslananka/kicad-mcp-pro.git
cd kicad-mcp-pro
git checkout mcp-server-v4.1.0          # commit 7611c20, 2026-10-09
cat > .claude-plugin/marketplace.json <<'EOF'
{
  "name": "kicad-mcp-pro-local",
  "owner": {"name": "devbisme"},
  "plugins": [
    {"name": "kicad-pro", "source": "./",
     "description": "Skills shipped with kicad-mcp-pro 4.1.0"}
  ]
}
EOF
claude plugin marketplace add "$PWD"
claude plugin install kicad-pro@kicad-mcp-pro-local
```

## 3. Configure the MCP server

The plugin also loads the repo's own `.mcp.json`. That file starts an unpinned
`uvx kicad-mcp-pro` in the read-only `default` profile. I replaced it in the clone with a
configuration that uses the pinned install and the KiCad 10 tools:

```json
{
  "mcpServers": {
    "kicad-mcp-pro": {
      "command": "/home/devb/.local/bin/kicad-mcp-pro",
      "args": ["--transport", "stdio"],
      "env": {
        "KICAD_MCP_TRANSPORT": "stdio",
        "KICAD_MCP_PROFILE": "full",
        "KICAD_MCP_OPERATING_MODE": "write",
        "KICAD_MCP_KICAD_CLI": "/home/devb/bin/kicad10-root/bin/kicad-cli",
        "KICAD_MCP_FREEROUTING_JAR": "/home/devb/bin/freerouting/freerouting-2.4.1.jar",
        "KICAD_MCP_NGSPICE_CLI": "/usr/local/bin/ngspice"
      }
    }
  }
}
```

So the server is registered through the plugin, not with `claude mcp add`. Its tools are
named `mcp__plugin_kicad-pro_kicad-mcp-pro__*`. I avoided the README's suggested name
`kicad` because the Seeed kicad-mcp-server already uses it.

### Profile and mode

The server's tool set depends on two settings: the profile and the operating mode. Both are
fixed when the server starts. To change either one, edit `.mcp.json` and restart Claude Code.
Tool counts per setting, from `kicad-mcp-pro tools list`:

| Profile | Mode | Tools | Notes |
|---|---|---:|---|
| `default` / `review` | `readonly` | 24 | The README's recommended default |
| `full` | `readonly` | 135 | All inspection, checking and export tools |
| `full` | `write` | 289 | Adds schematic authoring (`sch_add_*`, `sch_build_circuit`, `sch_create_sheet`) and PCB edits. **Used for these tests.** |
| `full` / `expert` | `experimental` | 332 | Adds experimental tools |

`full`/`write` lets one configuration serve both test classes: analysis (run 1) and
design from scratch (run 2). For a pure analysis run, the `review` profile in `readonly`
mode would prevent the design from being modified by accident.

## 4. Verify

```bash
claude mcp list | grep kicad-mcp-pro
# plugin:kicad-pro:kicad-mcp-pro: /home/devb/.local/bin/kicad-mcp-pro --transport stdio - ✔ Connected
KICAD_MCP_KICAD_CLI=~/bin/kicad10-root/bin/kicad-cli kicad-mcp-pro doctor
```

`doctor` reported `Status: degraded`:

- `kicad_cli: ok` (10.0.4).
- `kicad_ipc: warn`. KiCad wasn't running. The IPC connection is needed only for live
  edits in an open KiCad, not for file-based reads, ERC, DRC or exports.

Inside a session, `/mcp` should list `plugin:kicad-pro:kicad-mcp-pro` as **connected**, and
`/plugin` should list `kicad-pro` with its 7 skills.

## Notes

- **KiCad IPC.** Live PCB edits go through KiCad's IPC API, which on KiCad 10 needs the
  KiCad GUI open with the API server enabled. The project's compatibility notes say KiCad 11
  adds a headless `kicad-cli api-server` that removes this requirement.
- **Doctor's other warnings.** `doctor` also checks config files for other agents (Codex,
  OpenCode, Cursor and others). Its warnings about `~/.codex` and `~/.config/opencode` don't
  affect Claude Code.
- The README calls the tool a "first-pass design and review assistant" rather than a sign-off
  authority, and says its SI/PI/EMC/thermal tools are closed-form estimates with "~5–10%
  accuracy".

Sources: [kicad-mcp-pro README](https://github.com/oaslananka/kicad-mcp-pro),
`docs/installation.md`, `docs/client-configuration.md`,
`docs/agents/progressive-disclosure.md`, `compatibility.yaml`, and the installation on
this machine.
