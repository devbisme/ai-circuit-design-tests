# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed.
- **KiCad 10.** Konnect writes KiCad 10 files (`generator_version "10.0"`), which KiCad 9
  refuses to open. These tests used KiCad 10.0.4 at `~/bin/kicad10`, alongside the system
  KiCad 9.0.9.
- `kicad-cli` from KiCad 10 (used for ERC, DRC and exports).
- Optional: [Freerouting](https://github.com/freerouting/freerouting) 2.4.1 and a Java
  runtime on `PATH`, for autorouting.

## 1. Install the Konnect server

Download and unpack the Linux server binary
([v0.12.1](https://github.com/mixelpixx/Konnect/releases/download/v0.12.1/konnect-v0.12.1-x86_64-unknown-linux-gnu.tar.gz)):

```bash
tar xzf konnect-v0.12.1-x86_64-unknown-linux-gnu.tar.gz
cd konnect-v0.12.1-x86_64-unknown-linux-gnu
./konnect --version
```

## 2. Install the skills, agents and hooks

```bash
./konnect init
```

This writes six skills (`konnect`, `kicad-schematic`, `kicad-pcb`, `kicad-review`,
`kicad-manufacture`, `kicad-library`) to `~/.claude/skills`, two agents to `~/.claude/agents`,
and four `PreToolUse` hooks to `~/.claude/settings.json`. Check it with:

```bash
./konnect status
```

`konnect init` does **not** register the MCP server. Upgrading the binary does not update
guidance written by an older `init`; re-run `konnect init` after an upgrade (it overwrites
files you edited).

## 3. Register the MCP server with Claude Code

Use the absolute path to the binary. `-s user` makes it available in every project:

```bash
claude mcp add -s user -e RUST_LOG=info konnect -- /absolute/path/to/konnect
```

If you use Freerouting, the server needs Java on its `PATH`. Add
`-e PATH=/path/to/jre/bin:$PATH` to the command above.

Restart Claude Code, then run `/mcp`; `konnect` should show as **connected**. From the shell,
`claude mcp get konnect` shows its configuration. Inside a session, the
`get_installation_info` tool reports which binary is serving and whether it finds KiCad.

## 4. Install the KiCad plugin

PCB edits go over KiCad's live IPC API, which needs PCBNEW running with the Konnect plugin.

1. Download the
   [Konnect KiCad plugin](https://github.com/mixelpixx/Konnect/releases/download/v0.12.1/konnect-pcm-v0.12.1-linux.zip).
2. In KiCad 10, open **Plugin and Content Manager → Install from File** and select the zip.
   It installs to `~/.local/share/kicad/10.0/3rdparty/plugins/com_github_mixelpixx_konnect`.
3. Restart KiCad.
4. Make sure the IPC API is on: **Preferences → Plugins → Enable KiCad API**.

## 5. Start the plugin server (each session)

Open the board in PCBNEW and click **Tools → External Plugins → Konnect**. In the
**Konnect Settings** window, click **Start Server**. This opens the channel Claude Code uses
to talk to PCBNEW. Schematic edits don't need it; most PCB tools do.

## Known environment issues

- A stale global KiCad 10 `sym-lib-table` / `fp-lib-table` adds hundreds of spurious
  `lib_symbol_issues` ERC/DRC warnings. Point the tables at the KiCad 10 libraries before a run.
- Some steps (layer changes, closing and reopening the board) need you to act in the PCBNEW
  GUI.

Source: [Konnect README](https://github.com/mixelpixx/Konnect), `konnect --help`, and the
installation on this machine.
