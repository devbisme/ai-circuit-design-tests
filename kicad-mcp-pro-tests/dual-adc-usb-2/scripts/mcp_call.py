"""Call kicad-mcp-pro tools in-process (same code path as the MCP server).

Used for tools the running Claude Code session could not see because the server gated
them at startup (no KiCad IPC then).
Usage: mcp_call.py TOOL '{json args}' [TOOL2 '{...}' ...]
"""
import asyncio, json, os, sys
os.environ.setdefault('KICAD_MCP_PROFILE', 'full')
os.environ.setdefault('KICAD_MCP_OPERATING_MODE', 'write')
os.environ.setdefault('KICAD_MCP_KICAD_CLI', '/home/devb/bin/kicad10-root/bin/kicad-cli')
os.environ.setdefault('KICAD_MCP_FREEROUTING_JAR', '/home/devb/bin/freerouting/freerouting-2.4.1.jar')
from kicad_mcp.server import build_server


async def main(pairs):
    mcp = build_server('full')
    for name, args in pairs:
        try:
            res = await mcp.call_tool(name, json.loads(args))
        except Exception as exc:  # report and keep going
            print(f'=== {name}: EXCEPTION {exc!r}')
            continue
        print(f'=== {name}')
        items = res[0] if isinstance(res, tuple) else getattr(res, 'content', res)
        for it in items if isinstance(items, list) else [items]:
            print(getattr(it, 'text', it))


argv = sys.argv[1:]
asyncio.run(main(list(zip(argv[0::2], argv[1::2]))))
