"""Build the KiCad schematic for design.py with kicad-mcp-server's editing tools.

Run with KiCad 10's bundled Python (the MCP server's environment):
    ~/bin/kicad10-root/bin/python3.11 build_schematic.py

Parts are placed with the server's add_component_from_library and connected
with add_global_label (labels anchored on pins, no wires). The server has no
tools for sheets, no-connect flags, paper size or text, and its pin lookup
fails for derived ("extends") symbols and for multi-unit symbols, so this
script fills those gaps itself (marked WORKAROUND below).
"""

import asyncio
import re
import shutil
import site
import sys
import uuid
from pathlib import Path

MCP_DIR = Path.home() / "tmp/DOWNLOADS/kicad-mcp-server"
site.addsitedir(str(MCP_DIR / ".kicad10-deps"))
sys.path.insert(0, str(MCP_DIR / "src"))
from kicad_mcp_server.tools import schematic_editor as se  # noqa: E402
from kicad_mcp_server.utils.kicad_version import get_kicad_symbol_dir  # noqa: E402

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import design  # noqa: E402

PROJECT = "dual_adc_usb"
ROOT_SCH = HERE / f"{PROJECT}.kicad_sch"
TEMPLATE = Path(sys.argv[1]) if len(sys.argv) > 1 else None
LIBDIR = get_kicad_symbol_dir()
GRID = 2.54


# ---------------------------------------------------------------------------
# Library access (same .kicad_sym files the MCP server reads)
# ---------------------------------------------------------------------------
_lib_cache = {}


def lib_text(lib):
    if lib not in _lib_cache:
        _lib_cache[lib] = (LIBDIR / f"{lib}.kicad_sym").read_text()
    return _lib_cache[lib]


def resolve_base(lib, sym):
    """WORKAROUND: the server copies a derived symbol without its parent, giving a
    pinless symbol. Use the root parent (identical pins); the value keeps the real part."""
    while True:
        blk = se._extract_symbol_from_kicad_sym(LIBDIR / f"{lib}.kicad_sym", sym)
        if blk is None:
            raise KeyError(f"{lib}:{sym} not found")
        m = re.search(r'\(extends "([^"]+)"', blk)
        if not m:
            return sym, blk
        sym = m.group(1)


PIN_RE = re.compile(
    r'\(pin (?P<etype>\w+) \w+\s+\(at (?P<x>[-\d.]+) (?P<y>[-\d.]+) (?P<a>[-\d.]+)\)'
    r'[\s\S]*?\(number "(?P<num>[^"]*)"')


def sym_geometry(blk, base):
    """{unit: {pin: (dx_sheet, dy_sheet, etype)}} and body extents per unit."""
    units = {}
    body = {}
    for m in re.finditer(r'\(symbol "' + re.escape(base) + r'_(\d+)_(\d+)"', blk):
        u = int(m.group(1))
        start, depth = m.start(), 0
        for i in range(start, len(blk)):
            if blk[i] == "(":
                depth += 1
            elif blk[i] == ")":
                depth -= 1
                if depth == 0:
                    break
        sub = blk[start:i + 1]
        pins = units.setdefault(u, {})
        for pm in PIN_RE.finditer(sub):
            pins[pm["num"]] = (float(pm["x"]), -float(pm["y"]), pm["etype"], OUTWARD[int(float(pm["a"])) % 360])
        pts = [(float(a), -float(b)) for a, b in re.findall(r'\((?:xy|start|end|center) ([-\d.]+) ([-\d.]+)\)', sub)]
        body.setdefault(u, []).extend(pts)
    common = units.pop(0, {})
    cbody = body.pop(0, [])
    if not units:
        units = {1: {}}
        body.setdefault(1, [])
    for u in units:
        units[u].update(common)
        body[u] = body.get(u, []) + cbody
    return units, body


# Lib pin angle points from the connection point toward the body; labels go the other way
# (sheet Y is flipped, so lib 90 = pin pointing up = label below = sheet angle 270).
OUTWARD = {0: 180, 180: 0, 90: 270, 270: 90}


def pin_angle(dx, dy):
    """Outward label direction, same rule as the server's _pin_anchor."""
    if abs(dx) >= abs(dy):
        return 0 if dx >= 0 else 180
    return 90 if dy < 0 else 270


def label_len(text):
    return 1.0 * len(text) + 4.0


# ---------------------------------------------------------------------------
# Instances: one per (part, unit) with the pins that unit carries
# ---------------------------------------------------------------------------
def make_instances():
    insts = []
    for p in design.PARTS:
        base, blk = resolve_base(p["lib"], p["sym"])
        p["base"] = base
        units, body = sym_geometry(blk, base)
        p["etypes"] = {n: g[2] for u in units.values() for n, g in u.items()}
        allpins = set(p["etypes"])
        given = set(p["conns"]) | set(p["nc"])
        missing, extra = allpins - given, given - allpins
        if missing:
            print(f"!! {p['ref']}: pins not assigned: {sorted(missing)}")
        if extra:
            print(f"!! {p['ref']}: pins not in symbol: {sorted(extra)}")
        for u in sorted(units):
            insts.append(dict(part=p, unit=u, pins=units[u], body=body[u],
                              multi=len(units) > 1))
    return insts


def inst_bbox(inst):
    xs, ys = [0.0], [0.0]
    for x, y in inst["body"]:
        xs.append(x)
        ys.append(y)
    for num, (dx, dy, _, a) in inst["pins"].items():
        net = inst["part"]["conns"].get(num)
        L = label_len(net) if net else 1.0
        ex = {0: (dx, dx + L), 180: (dx - L, dx)}.get(a, (dx - 1.5, dx + 1.5))
        ey = {90: (dy - L, dy), 270: (dy, dy + L)}.get(a, (dy - 1.5, dy + 1.5))
        xs += ex
        ys += ey
    if len(inst["pins"]) <= 3 and max(xs) - min(xs) < 8:  # fields sit to the right (place_fields)
        p = inst["part"]
        xs.append(max(x for x, _ in inst["body"] or [(0, 0)]) + 2.5 + 1.0 * max(len(p["ref"]), len(p["value"])))
    ys += [-6.5, 4.0]  # reference / value fields
    return min(xs), min(ys), max(xs), max(ys)


def snap(v):
    return round(v / GRID) * GRID


PAPERS = [("A4", 297, 210), ("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594), ("A0", 1189, 841)]


def layout(insts):
    """Shelf-pack instances left-to-right, top-to-bottom; choose the smallest paper."""
    for name, W, H in PAPERS:
        x0, y0, margin, gap = 20.0, 25.0, 20.0, 5.08
        x, y, row_h, placed = x0, y0, 0.0, []
        ok = True
        for inst in insts:
            bx0, by0, bx1, by1 = inst_bbox(inst)
            w, h = bx1 - bx0, by1 - by0
            if (x + w > W - margin or inst["part"].get("newrow") and inst["unit"] == 1) and x > x0:
                x, y, row_h = x0, y + row_h + gap, 0.0
            placed.append((snap(x - bx0), snap(y - by0)))
            x += w + gap
            row_h = max(row_h, h)
        if y + row_h <= H - margin - 30:  # leave room for the title block
            for inst, pos in zip(insts, placed):
                inst["pos"] = pos
            return name
    raise RuntimeError("does not fit on A0")


# ---------------------------------------------------------------------------
# File helpers
# ---------------------------------------------------------------------------
def append_entry(path, entry):
    text = path.read_text()
    path.write_text(se._append_top_level(text, entry))


def global_label_entry(name, shape, x, y, angle):
    """Same text the server's add_global_label writes (used where its pin lookup fails)."""
    justify = se._JUSTIFY.get(angle, "left")
    return (
        f'\t(global_label "{name}" (shape {shape}) (at {round(x, 3)} {round(y, 3)} {angle})\n'
        f"\t\t(effects (font (size 1.27 1.27)) (justify {justify}))\n"
        f'\t\t(uuid "{uuid.uuid4()}")\n'
        f'\t\t(property "Intersheetrefs" "${{INTERSHEET_REFS}}" (at 0 0 0)\n'
        f"\t\t\t(effects (font (size 1.27 1.27)) hide)\n"
        f"\t\t)\n"
        f"\t)\n"
    )


def no_connect_entry(x, y):
    return f'\t(no_connect (at {round(x, 3)} {round(y, 3)}) (uuid "{uuid.uuid4()}"))\n'


SHAPE = {"input": "input", "output": "output", "bidirectional": "bidirectional",
         "tri_state": "tri_state", "open_collector": "output"}


def run(coro):
    res = asyncio.run(coro)
    if not res.startswith("✅"):
        raise RuntimeError(res)
    return res


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------
def new_sheet_file(path, title):
    path.write_text(
        "(kicad_sch\n\t(version 20260306)\n\t(generator \"eeschema\")\n\t(generator_version \"10.0\")\n"
        f"\t(uuid \"{uuid.uuid4()}\")\n\t(paper \"A3\")\n\t(title_block\n\t\t(title \"{title}\")\n"
        "\t\t(date \"2026-10-09\")\n\t)\n\t(lib_symbols)\n)\n")


def set_paper(path, paper):
    t = path.read_text()
    path.write_text(re.sub(r'\(paper "[^"]+"\)', f'(paper "{paper}")', t, count=1))


def place_fields(path, sheet_insts):
    """WORKAROUND (cosmetic): the server puts Value on the symbol centre. Move Reference/Value
    beside small parts and above/below the body of ICs."""
    where = {(i["part"]["ref"], i["unit"]): i for i in sheet_insts}
    text = path.read_text()

    def fix(m):
        blk = m.group(0)
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk)[1]
        inst = where.get((ref, int(m.group(4))))
        if inst is None:
            return blk
        x, y = float(m.group(2)), float(m.group(3))
        pts = inst["body"] or [(0, 0)]
        bx0, bx1 = min(p[0] for p in pts), max(p[0] for p in pts)
        by0, by1 = min(p[1] for p in pts), max(p[1] for p in pts)
        if len(inst["pins"]) <= 3 and bx1 - bx0 < 8:
            rpos, vpos, just = (x + bx1 + 1.27, y - 1.27), (x + bx1 + 1.27, y + 1.27), "left"
        else:
            rpos, vpos, just = (x + bx0, y + by0 - 1.27), (x + bx0, y + by1 + 2.54), "left"
        for prop, (px, py) in (("Reference", rpos), ("Value", vpos)):
            blk = re.sub(r'(\(property "%s" "[^"]*") \(at [-\d.]+ [-\d.]+ 0\)\s*\(effects \(font \(size 1.27 1.27\)\)\)' % prop,
                         lambda mm: f'{mm.group(1)} (at {round(px, 3)} {round(py, 3)} 0)\n    '
                                    f'(effects (font (size 1.27 1.27)) (justify {just}))', blk)
        return blk

    text = re.sub(r'\(symbol \(lib_id "([^"]+)"\) \(at ([-\d.]+) ([-\d.]+) 0\) \(unit (\d+)\).*?\n\)',
                  fix, text, flags=re.S)
    path.write_text(text)


def build():
    insts = make_instances()
    # Power flags for supply nets that no power_out pin drives
    drivers, sinks = set(), set()
    for p in design.PARTS:
        for num, net in p["conns"].items():
            if net is None:
                continue
            et = p["etypes"].get(num)
            if et == "power_out":
                drivers.add(net)
            elif et == "power_in":
                sinks.add(net)
    flag_nets = sorted(sinks - drivers)
    for i, net in enumerate(flag_nets, 1):
        design.part(f"#FLG{i:02d}", "power", "PWR_FLAG", "PWR_FLAG", "", "power", {1: net})
    insts = make_instances()
    print("PWR_FLAG on:", flag_nets)

    # Fresh root (from the server's empty project) and sub-sheets
    if TEMPLATE:
        shutil.copy(TEMPLATE, ROOT_SCH)
    for name, title in design.SHEETS:
        new_sheet_file(HERE / f"{name}.kicad_sch", title)

    for name, _ in design.SHEETS:
        path = HERE / f"{name}.kicad_sch"
        sheet_insts = [i for i in insts if i["part"]["sheet"] == name]
        paper = layout(sheet_insts)
        set_paper(path, paper)
        fp = str(path)
        for inst in sheet_insts:
            p = inst["part"]
            x, y = inst["pos"]
            run(se.add_component_from_library(fp, p["lib"], p["base"], p["ref"], p["value"],
                                              p["fp"], x, y, inst["unit"]))
        for inst in sheet_insts:
            p = inst["part"]
            x, y = inst["pos"]
            for num, (dx, dy, et, ang) in inst["pins"].items():
                net = p["conns"].get(num)
                if net is None:
                    append_entry(path, no_connect_entry(x + dx, y + dy))
                    continue
                shape = SHAPE.get(et, "passive")
                if inst["multi"] or ang != pin_angle(dx, dy):
                    # WORKAROUND: server's _pin_anchor stops at the first unit with this ref, and
                    # its position-based direction rule turns labels sideways on tall symbols
                    append_entry(path, global_label_entry(net, shape, x + dx, y + dy, ang))
                else:
                    res = run(se.add_global_label(fp, p["ref"], num, net, shape))
                    m = re.search(r"at \(([-\d.]+), ([-\d.]+)\)", res)
                    assert abs(float(m[1]) - (x + dx)) < 1e-3 and abs(float(m[2]) - (y + dy)) < 1e-3, \
                        (p["ref"], num, res)
        place_fields(path, sheet_insts)
        print(f"{name}: {len(sheet_insts)} symbols, paper {paper}")

    # WORKAROUND: no sheet tool in the server; write sheet symbols into the root
    root = ROOT_SCH.read_text()
    root_uuid = re.search(r'\(uuid "([^"]+)"\)', root).group(1)
    entries = ""
    for k, (name, title) in enumerate(design.SHEETS):
        x, y, w, h = round(30.48 + k * 50.8, 2), 50.8, 43.18, 25.4
        entries += (
            f"\t(sheet (at {x} {y}) (size {w} {h})\n"
            "\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)\n"
            "\t\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000))\n"
            f'\t\t(uuid "{uuid.uuid4()}")\n'
            f'\t\t(property "Sheetname" "{name}" (at {x} {round(y - 0.7, 2)} 0)\n'
            "\t\t\t(effects (font (size 1.27 1.27)) (justify left bottom)))\n"
            f'\t\t(property "Sheetfile" "{name}.kicad_sch" (at {x} {round(y + h + 0.6, 2)} 0)\n'
            "\t\t\t(effects (font (size 1.27 1.27)) (justify left top)))\n"
            f'\t\t(instances (project "{PROJECT}" (path "/{root_uuid}" (page "{k + 2}"))))\n'
            "\t)\n"
            f'\t(text "{title}" (at {round(x + 1.27, 2)} {y + 12.7} 0)\n'
            f"\t\t(effects (font (size 1.27 1.27)) (justify left))\n"
            f'\t\t(uuid "{uuid.uuid4()}"))\n'
        )
    notes = (HERE / "design_notes.txt").read_text().strip().replace('"', "'").replace("\n", "\\n")
    entries += (f'\t(text "{notes}" (at 30.48 95.25 0)\n'
                "\t\t(effects (font (size 1.27 1.27)) (justify left top))\n"
                f'\t\t(uuid "{uuid.uuid4()}"))\n')
    ROOT_SCH.write_text(se._append_top_level(root, entries))
    set_paper(ROOT_SCH, "A3")


if __name__ == "__main__":
    build()
