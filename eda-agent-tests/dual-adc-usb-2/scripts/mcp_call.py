"""Call an eda-agent MCP tool in-process (same registered tool code as the
stdio server), so large DesignPlan payloads can be passed from files instead
of being pasted into MCP calls.

usage: <eda-agent venv python> mcp_call.py TOOL [key=value | key=@file] ...
"""
import asyncio, json, os, sys

os.environ.setdefault("EDA_AGENT_BACKEND", "kicad")
os.environ.setdefault("EDA_AGENT_HEADLESS", "1")
W = os.path.expanduser("~/.local/share/eda-agent")
os.environ.setdefault("EDA_AGENT_WORKSPACE", W + "/workspace")
os.environ.setdefault("EDA_AGENT_POINTER_FILE", W + "/workspace-path.txt")
from eda_agent.server import mcp  # noqa: E402


def main():
    tool = sys.argv[1]
    args = {}
    for a in sys.argv[2:]:
        k, v = a.split("=", 1)
        if v.startswith("@"):
            v = open(v[1:], encoding="utf-8").read()
        else:
            try:
                v = json.loads(v)
            except ValueError:
                pass
        args[k] = v
    res = asyncio.run(mcp.call_tool(tool, args))
    # FastMCP returns (content, structured) or a content list depending on version.
    if isinstance(res, tuple):
        res = res[1] if res[1] is not None else res[0]
    if isinstance(res, list):
        out = [getattr(c, "text", str(c)) for c in res]
        print("\n".join(out))
    else:
        print(json.dumps(res, indent=1, default=str))


main()
