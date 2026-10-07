# Setup

## Prerequisites

- [Claude Code](https://docs.claude.com/en/docs/claude-code) installed.
- [SKiDL](https://github.com/devbisme/skidl):

  ```bash
  pip install skidl
  ```

- KiCad installed, with `KICAD_SYMBOL_DIR` pointing at its symbol libraries
  (put this line in your shell profile, e.g. `~/.bashrc`):

  ```bash
  export KICAD_SYMBOL_DIR=/usr/share/kicad/symbols
  ```

## 1. Install skidl-skills

`skidl-skills` is published through the
[devbisme-skills](https://github.com/devbisme/devbisme-skills) plugin marketplace.
That marketplace is an index: its entry for `skidl-skills` points at the
[devbisme/skidl-skills](https://github.com/devbisme/skidl-skills) repo.

Add the marketplace, then install the plugin from it:

```bash
claude plugin marketplace add https://github.com/devbisme/devbisme-skills
claude plugin install skidl-skills@devbisme-skills
```

You can run the same steps inside a Claude Code session:

```
/plugin marketplace add https://github.com/devbisme/devbisme-skills
/plugin install skidl-skills@devbisme-skills
```

If the marketplace was added before, refresh it to get the latest plugin
versions:

```bash
claude plugin marketplace update devbisme-skills
```

Restart Claude Code so it loads the plugin. To check that it worked, run
`/plugin` and look for `skidl-skills` under installed plugins. The
`/new-circuit` command should also be available. It starts the workflow that
architects a circuit, sources in-stock parts, gathers datasheets, writes the
SKiDL code, and checks it with ERC.

## 2. Install and activate the pcbparts MCP server

[pcbparts-mcp](https://github.com/Averyy/pcbparts-mcp) provides component search
(stock, pricing, and parametric data). `skidl-skills` uses it for part sourcing.
A hosted instance is available, so nothing has to be installed locally. Register
it with Claude Code over the HTTP transport:

```bash
claude mcp add --transport http pcbparts https://pcbparts.dev/mcp
```

This registers the server in local scope, so it is active only in the current
project directory. To make it available in every project, add `-s user`:

```bash
claude mcp add -s user --transport http pcbparts https://pcbparts.dev/mcp
```

To share it with everyone who uses this repo, add `-s project`. That writes it to
`.mcp.json`, and each user approves it the first time Claude Code starts in the
repo:

```json
{
  "mcpServers": {
    "pcbparts": {
      "type": "http",
      "url": "https://pcbparts.dev/mcp"
    }
  }
}
```

### Activate and verify

1. Restart Claude Code, or start a new session, so it connects to the server.
2. Run `/mcp`. `pcbparts` should show as **connected**, and its tools will be
   listed as `mcp__pcbparts__*`.
3. From the shell, `claude mcp list` shows the connection status.
   `claude mcp get pcbparts` shows its configuration.

If it shows as failed, check that `https://pcbparts.dev/mcp` is reachable from
your network. To remove it, run `claude mcp remove pcbparts`. For self-hosting
options, see the [pcbparts-mcp README](https://github.com/Averyy/pcbparts-mcp).
