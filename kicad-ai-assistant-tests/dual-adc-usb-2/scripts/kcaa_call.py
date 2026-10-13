"""Call kcaa MCP tools in-process (same code the MCP server runs).

Usage as module:  from kcaa_call import call;  call("get_symbol_pins", library_name=..., symbol_name=...)
"""
import asyncio, json, os, sys, logging

os.environ.setdefault("KICAD_VERSION", "10.0")
os.environ.setdefault("KICAD_APP_PATH", "/home/devb/bin/kicad10-root/usr/share/kicad")
os.environ.setdefault("KICAD_CLI_PATH", "/home/devb/bin/kicad10-root/bin/kicad-cli")
os.environ.setdefault("KCAA_SKILLS_DIR",
    "/home/devb/.local/share/kicad/10.0/scripting/plugins/kicad_ai_assistant/skills")
# ~/.profile exports the KiCad-5 era KICAD_SYMBOL_DIR=/usr/share/kicad/library, which kcaa
# treats as an override for KICAD10_SYMBOL_DIR. Force the KiCad 10 location.
os.environ["KICAD_SYMBOL_DIR"] = "/home/devb/bin/kicad10-root/usr/share/kicad/symbols"
os.environ["KICAD_FOOTPRINT_DIR"] = "/home/devb/bin/kicad10-root/usr/share/kicad/footprints"
logging.disable(logging.WARNING)

from kcaa.server import create_server
import fastmcp.server.context as _fctx


async def _quiet_log(self, *a, **k):  # no MCP session in-process: drop ctx.info/ctx.log
    return None

_fctx.Context.log = _quiet_log
for _n in ("report_progress",):
    setattr(_fctx.Context, _n, _quiet_log)

_mcp = None
_loop = asyncio.new_event_loop()


def call(name, **kw):
    global _mcp
    if _mcp is None:
        _mcp = create_server("full")
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):   # kcaa parsers print progress to stdout
        try:
            res = _loop.run_until_complete(_mcp.call_tool(name, kw))
        except Exception as e:  # return tool errors as data, like the MCP client sees them
            return {"success": False, "error": f"{type(e).__name__}: {str(e)[:500]}"}
    if getattr(res, "structured_content", None) is None and not res.content:
        return None
    # fastmcp ToolResult -> structured content or text
    sc = getattr(res, "structured_content", None)
    if sc is not None:
        return sc.get("result", sc) if isinstance(sc, dict) else sc
    txt = "".join(getattr(c, "text", "") for c in res.content)
    try:
        return json.loads(txt)
    except Exception:
        return txt


if __name__ == "__main__":
    print(json.dumps(call(sys.argv[1], **json.loads(sys.argv[2])), indent=1))
