"""Build the hierarchical KiCad schematic from design.py using kcaa MCP tools (in-process).

kcaa tools used: add_sheet_symbol, get_symbol, add_symbol_to_schematic, rename_symbol,
move_component, extract_schematic_netlist, set_symbol_property, connect_points_with_wire,
add_label_to_schematic, add_no_connect.

Style: every connected pin gets a 2.54 mm stub ending in a power symbol (power nets) or a
net label (local if the net stays on one sheet, global otherwise).  Unused pins get NC flags.

Ordering matters: kcaa's add_symbol_to_schematic shifts a symbol whose pin would land on an
existing wire, so all symbols (incl. power symbols) are placed before any wire is drawn.
"""
import math, os, shutil, sys, time
import kcaa_call
from design import PARTS, LIB, POWER_NETS, PWR_FLAG_NETS, SHEETS, SHEET_TITLES, nets

call = kcaa_call.call
PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ROOT = os.path.join(PROJ, "dual_adc.kicad_sch")
GRID = 1.27
STUB = 2.54
PAPER = {}
DEFAULT_PAPER = ("A3", 420, 297)
DIRV = {"left": (-1, 0), "right": (1, 0), "up": (0, -1), "down": (0, 1)}   # screen Y-down
LABEL_ANGLE = {"right": 0, "up": 90, "left": 180, "down": 270}
UP_ROT = {"up": 0, "left": 90, "down": 180, "right": 270}      # body-up power symbols
DOWN_ROT = {"down": 0, "right": 90, "up": 180, "left": 270}    # GND
LOG = []


def log(*a):
    s = " ".join(str(x) for x in a)
    LOG.append(s)
    print(s, flush=True)


def snap(v):
    return round(round(v / GRID) * GRID, 2)


def ok(r, what):
    if not isinstance(r, dict) or r.get("error") or r.get("success") is False:
        log("FAIL", what, str(r)[:300])
        return False
    return True


def net_sheets():
    out = {}
    for ref, p in PARTS.items():
        for net in p["pins"].values():
            out.setdefault(net, set()).add(p["sheet"])
    return out


def label_len(net):
    return STUB + 1.1 * len(net) + 4.0


def sym_geometry(sym):
    """Pin sides + per-unit bboxes from kcaa (library coords, Y-up)."""
    g = call("get_symbol", library_name=LIB, symbol_name=sym, project_path=PROJ)
    pins = call("get_symbol_pins", library_name=LIB, symbol_name=sym, project_path=PROJ)
    return g, pins


def item_boxes(ref, p, geo):
    """Return list of (unit, w, h, dx, dy) where dx/dy = anchor offset from box top-left.
    kcaa's get_symbol_pins has no per-pin unit, so label margins use all pins of the part."""
    g, pins = geo
    m = {"left": 3.0, "right": 3.0, "up": 3.0, "down": 3.0}
    for pin in pins.get("pins", []):
        net = p["pins"].get(str(pin["number"]), "NC")
        d = pin.get("direction", "left")
        length = 2.0 if net == "NC" else (7.0 if net in POWER_NETS else label_len(net))
        m[d] = max(m[d], length + 1.27)
    ub = g.get("unit_bboxes") or {"1": g["body_bbox"]}
    out = []
    for u in sorted(ub, key=int):
        bb = ub[u]
        x0, y0, x1, y1 = bb["min_x"], bb["min_y"], bb["max_x"], bb["max_y"]
        w = (x1 - x0) + m["left"] + m["right"]
        h = (y1 - y0) + m["up"] + m["down"]
        out.append((int(u), w, h, m["left"] - x0, m["up"] + y1))   # screen y = -lib y
    return out


def uuid_of(sheet_file, ref):
    from sexp import parse, find, find1
    t = parse(open(sheet_file).read())
    for sym in find(t, "symbol"):
        for prop in find(sym, "property"):
            if prop[1] == "Reference" and prop[2] == ref:
                return str(find1(sym, "uuid")[1])
    return None


def snap_units(sheet_file, ref):
    """kcaa stacks extra units at +10 mm (off the 1.27 mm grid) and move_component only
    moves by grid-snapped deltas, so snap each unit's anchor (and its fields) in the file."""
    from sexp import parse, dump, find, find1
    t = parse(open(sheet_file).read())
    n = 0
    for sym in find(t, "symbol"):
        if not any(p[1] == "Reference" and p[2] == ref for p in find(sym, "property")):
            continue
        at = find1(sym, "at")
        x, y = float(at[1]), float(at[2])
        dx, dy = snap(x) - x, snap(y) - y
        if abs(dx) < 1e-6 and abs(dy) < 1e-6:
            continue
        at[1], at[2] = str(snap(x)), str(snap(y))
        for prop in find(sym, "property"):
            pa = find1(prop, "at")
            pa[1], pa[2] = str(round(float(pa[1]) + dx, 3)), str(round(float(pa[2]) + dy, 3))
        n += 1
    open(sheet_file, "w").write(dump(t) + "\n")
    log(f"snapped {n} off-grid units of {ref}")


def two_pin(p):
    return len(p["pins"]) == 2


def build_sheet(sheet, sheet_file, NS):
    paper, PW, PH = PAPER.get(sheet, DEFAULT_PAPER)
    refs = [r for r, p in PARTS.items() if p["sheet"] == sheet]
    big = [r for r in refs if len(PARTS[r]["pins"]) > 6]
    small = [r for r in refs if r not in big]
    order = big + sorted(small, key=lambda r: (PARTS[r]["sym"], r))
    # ---------- geometry and shelf packing
    geo_cache = {}
    items = []
    for r in order:
        p = PARTS[r]
        rot = 90 if two_pin(p) and p["sym"] not in ("Conn_Coaxial",) else 0
        if p["sym"] not in geo_cache:
            geo_cache[p["sym"]] = sym_geometry(p["sym"])
        g, pins = geo_cache[p["sym"]]
        if rot == 90:   # 2-pin vertical symbol rotated: pins left/right, labels horizontal
            nl = [p["pins"][k] for k in sorted(p["pins"])]
            w = 7.62 + sum((7.0 if n in POWER_NETS else label_len(n)) + 1 for n in nl)
            boxes = [(1, w, 12.7, w / 2, 6.35)]
        elif not p["pins"]:
            boxes = [(1, 10.16, 10.16, 5.08, 5.08)]
        else:
            boxes = item_boxes(r, p, (g, pins))
        for (u, w, h, dx, dy) in boxes:
            items.append(dict(ref=r, unit=u, w=w, h=h, dx=dx, dy=dy, rot=rot,
                              nunits=len(boxes)))
    # shelf packing, then spread the shelves over the page height
    shelves, cur, x = [], [], 20.0
    for it in items:
        if cur and x + it["w"] > PW - 15:
            shelves.append(cur); cur, x = [], 20.0
        it["x0"] = x
        cur.append(it)
        x += it["w"] + 5.08
    shelves.append(cur)
    used = sum(max(i["h"] for i in sh) for sh in shelves)
    gap = max(2.54, min(20.0, (PH - 70 - used) / max(1, len(shelves))))
    y = 20.0
    for sh in shelves:
        for it in sh:
            it["ax"], it["ay"] = snap(it["x0"] + it["dx"]), snap(y + it["dy"])
        y += max(i["h"] for i in sh) + gap
    if y > PH - 30:
        log(f"WARNING {sheet}: content height {y:.0f} mm exceeds paper {PH} mm")
    # ---------- place symbols
    placed = {}
    for it in items:
        r, p = it["ref"], PARTS[it["ref"]]
        if it["unit"] == 1:
            res = call("add_symbol_to_schematic", schematic_path=sheet_file, library_name=LIB,
                       symbol_name=p["sym"], x=it["ax"], y=it["ay"], rotation=it["rot"],
                       value=p["value"])
            if not ok(res, f"place {r}"):
                continue
            if res.get("position_adjusted"):
                log(f"note: {r} position adjusted to {res['position']}")
            placed[r] = res
            # rename to the design reference
            if res["reference_assigned"] != r:
                # kcaa gap: extract_schematic_netlist returns no uuid, which rename_symbol
                # needs, so read it from the sheet file
                uid = uuid_of(sheet_file, res["reference_assigned"])
                rr = call("rename_symbol", schematic_path=sheet_file, symbol_uuid=uid,
                          target_reference=r)
                ok(rr, f"rename {res['reference_assigned']}->{r}")
        else:
            # move this unit (kcaa stacks units at +10 mm) to its packed slot
            cur = placed.get(r)
            if not cur:
                continue
            ux, uy = cur["position"]["x"], cur["position"]["y"] + (it["unit"] - 1) * 10.0
            mv = call("move_component", schematic_path=sheet_file, reference=r,
                      x=round(it["ax"] - ux, 2), y=round(it["ay"] - uy, 2), unit=it["unit"])
            ok(mv, f"move {r} unit {it['unit']}")
    for r in {it["ref"] for it in items if it["nunits"] > 1}:
        snap_units(sheet_file, r)
    # footprints in one batch
    fpi = [{"reference": r, "property_name": "Footprint", "property_value": PARTS[r]["fp"]}
           for r in refs if PARTS[r]["fp"]]
    if fpi:
        ok(call("set_symbol_property", schematic_path=sheet_file, items=fpi), "footprints")
    desc = [{"reference": r, "property_name": "Description", "property_value": PARTS[r]["desc"]}
            for r in refs if PARTS[r]["desc"]]
    if desc:
        ok(call("set_symbol_property", schematic_path=sheet_file, items=desc), "descriptions")
    # ---------- pin coordinates from kcaa netlist extraction
    nl = call("extract_schematic_netlist", schematic_path=sheet_file)["analysis"]["components"]
    stubs = []   # (ref, pin, net, px, py, dir)
    for r in refs:
        comp = nl.get(r)
        if comp is None:
            log(f"FAIL {r} not found after placement"); continue
        for unit in comp["units"].values():
            for pin in unit["pins"]:
                net = PARTS[r]["pins"].get(str(pin["num"]))
                if net is None:
                    log(f"FAIL {r} pin {pin['num']} has no design net"); continue
                stubs.append((r, str(pin["num"]), net, float(pin["x"]), float(pin["y"]),
                              pin["direction"]))
    # ---------- power symbols first (before any wire exists)
    nwires = 0
    for (r, pin, net, px, py, d) in stubs:
        if net in POWER_NETS:
            vx, vy = DIRV[d]
            ex, ey = round(px + vx * STUB, 2), round(py + vy * STUB, 2)
            rot = (DOWN_ROT if net == "GND" else UP_ROT)[d]
            ps = POWER_NETS[net]
            res = call("add_symbol_to_schematic", schematic_path=sheet_file,
                       library_name=f"power/{ps}", symbol_name=ps, x=ex, y=ey, rotation=rot)
            if ok(res, f"power {net} at {r}.{pin}") and res.get("position_adjusted"):
                log(f"FAIL power symbol for {r}.{pin} moved to {res['position']}")
    # PWR_FLAGs: flag + power symbol joined by a short wire, top-right corner area
    fx = snap(PW - 60.0)
    fy = snap(PH - 60.0)
    flags = [n for n in PWR_FLAG_NETS if sheet in NS.get(n, set())
             and FLAG_HOME.get(n) == sheet]
    flag_wires = []
    for n in flags:
        res = call("add_symbol_to_schematic", schematic_path=sheet_file,
                   library_name="power/PWR_FLAG", symbol_name="PWR_FLAG", x=fx, y=fy)
        ok(res, f"PWR_FLAG {n}")
        if n in POWER_NETS:
            ps = POWER_NETS[n]
            rot = 0 if n == "GND" else 180
            call("add_symbol_to_schematic", schematic_path=sheet_file,
                 library_name=f"power/{ps}", symbol_name=ps, x=fx, y=fy + 5.08, rotation=rot)
            flag_wires.append((fx, fy, fx, fy + 5.08, None))
        else:
            flag_wires.append((fx, fy, fx, fy + 5.08, n))
        fx += 12.7
    # ---------- wires and labels
    for (r, pin, net, px, py, d) in stubs:
        if net == "NC":
            ok(call("add_no_connect", schematic_path=sheet_file, x=px, y=py), f"nc {r}.{pin}")
            continue
        vx, vy = DIRV[d]
        ex, ey = round(px + vx * STUB, 2), round(py + vy * STUB, 2)
        ok(call("connect_points_with_wire", schematic_path=sheet_file, start_x=px, start_y=py,
                end_x=ex, end_y=ey), f"wire {r}.{pin}")
        nwires += 1
        if net not in POWER_NETS:
            glob = len(NS[net]) > 1
            ok(call("add_label_to_schematic", schematic_path=sheet_file, text=net, x=ex, y=ey,
                    angle=LABEL_ANGLE[d], label_type="global" if glob else "local",
                    shape="bidirectional"), f"label {net} at {r}.{pin}")
    for (x1, y1, x2, y2, lab) in flag_wires:
        ok(call("connect_points_with_wire", schematic_path=sheet_file, start_x=x1, start_y=y1,
                end_x=x2, end_y=y2), "flag wire")
        if lab:
            glob = len(NS[lab]) > 1
            ok(call("add_label_to_schematic", schematic_path=sheet_file, text=lab, x=x2, y=y2,
                    angle=270, label_type="global" if glob else "local",
                    shape="bidirectional"), f"flag label {lab}")
    log(f"{sheet}: {len(refs)} parts, {len(stubs)} pins, {nwires} stubs")


def fix_label_justify():
    """kcaa writes every local label with (justify left bottom); KiCad uses (justify right
    bottom) for 180/270 degree labels, otherwise the text runs back over the pin."""
    import re
    for s in SHEETS:
        f = os.path.join(PROJ, f"{s}.kicad_sch")
        t = open(f).read()
        t, n = re.subn(r'(\(label "[^"]*" \(at [-\d.]+ [-\d.]+ (?:180|270)\)[^\n]*?)'
                       r'\(justify left bottom\)', r'\1(justify right bottom)', t)
        open(f, "w").write(t)
        log(f"{s}: fixed justification of {n} local labels")


# each PWR_FLAG lives on exactly one sheet
FLAG_HOME = {"GND": "power", "VBUS": "power", "+5V": "power", "+3V3": "power",
             "+5VA": "power", "-5VA": "power", "+1V2": "power", "+3.3VA": "power",
             "-5V": "power", "FT_VCCD": "usb", "FT_VCORE": "usb", "FT_VCCA": "usb",
             "VCCPLL0": "fpga", "VCCPLL1": "fpga"}


def main():
    t0 = time.time()
    # start from the blank root saved at project creation
    for f in os.listdir(PROJ):
        if f.endswith(".kicad_sch") or f.endswith(".kicad_sch.bak"):
            os.remove(os.path.join(PROJ, f))
    shutil.copy(os.path.join(PROJ, "scripts", "root_blank.kicad_sch"), ROOT)
    NS = net_sheets()
    x = 30.0
    for i, s in enumerate(SHEETS):
        res = call("add_sheet_symbol", schematic_path=ROOT, sheet_name=SHEET_TITLES[s],
                   sheet_file=f"{s}.kicad_sch", x=30 + (i % 3) * 120, y=40 + (i // 3) * 90,
                   width=90, height=60, create_child=True,
                   child_paper=PAPER.get(s, DEFAULT_PAPER)[0], child_title=SHEET_TITLES[s])
        ok(res, f"sheet {s}")
    for s in SHEETS:
        build_sheet(s, os.path.join(PROJ, f"{s}.kicad_sch"), NS)
    import fix_hierarchy   # noqa: F401  (rewrites instance paths on import)
    fix_label_justify()
    log(f"done in {time.time() - t0:.0f} s")
    open(os.path.join(PROJ, "scripts", "build_schematic.log"), "w").write("\n".join(LOG) + "\n")


if __name__ == "__main__":
    main()
