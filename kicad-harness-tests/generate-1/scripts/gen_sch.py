"""Write a hierarchical, label-based KiCad 10 schematic project from design.build().

Every pin gets a 2.54 mm wire stub ending in a net label (local if the net stays on
one sheet, global otherwise) or a no-connect flag. Connectivity is carried entirely
by label names, so placement only has to avoid overlaps.
"""
import json
import sys
import uuid as _uuid
from pathlib import Path

from sexp import Q, SYMDIR, dump, symbol_bbox, symbol_units
import design

PROJ = "dual_adc"
OUT = Path(__file__).resolve().parent.parent / "dual_adc"
GRID = 1.27
SHEETS = ["Power", "FrontEnd", "ADC", "FPGA", "Memory", "USB"]
PAPERS = [("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594), ("A0", 1189, 841)]


def uid(*key):
    return Q(str(_uuid.uuid5(_uuid.NAMESPACE_URL, "dual_adc/" + "/".join(map(str, key)))))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def font(size=1.27):
    return ["effects", ["font", ["size", size, size]]]


def label_len(name):
    return 1.0 * len(name) + 4.0


OUTWARD = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}     # sheet coords, y down
LABEL_ANGLE = {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}


def unit_geometry(part, unit):
    """Pins of this unit with sheet-relative endpoints (symbol at 0,0) and the footprint box incl. labels."""
    pins = [p for p in part.libpins if p["unit"] in (0, unit)]
    x0, y0, x1, y1 = symbol_bbox(part.sym, unit)
    # sheet coords: y flipped
    bx0, by0, bx1, by1 = x0, -y1, x1, -y0
    m = {"l": 0.0, "r": 0.0, "t": 0.0, "b": 0.0}
    for p in pins:
        net = part.pins.get(p["number"])
        d = OUTWARD[int(p["rot"]) % 360]
        ext = 2.54 + (label_len(net) if net else 1.0)
        key = {(-1, 0): "l", (1, 0): "r", (0, 1): "b", (0, -1): "t"}[d]
        m[key] = max(m[key], ext)
    return pins, (bx0 - m["l"] - 3, by0 - m["t"] - 5, bx1 + m["r"] + 3, by1 + m["b"] + 5)


def place_units(units, paper_w, paper_h):
    """Shelf packing; returns {(ref,unit): (x,y)} or None if it does not fit."""
    x, y, shelf_h = 15.0, 15.0, 0.0
    pos = {}
    for key, (bx0, by0, bx1, by1) in units:
        w, h = bx1 - bx0, by1 - by0
        if x + w > paper_w - 15:
            x, y, shelf_h = 15.0, y + shelf_h, 0.0
        pos[key] = (snap(x - bx0), snap(y - by0))
        x += w
        shelf_h = max(shelf_h, h)
    if y + shelf_h > paper_h - 40:
        return None
    return pos


def lib_symbols(parts):
    seen, out = set(), []
    for p in parts:
        if p.lib_id not in seen:
            seen.add(p.lib_id)
            out.append(p.sym)
    return ["lib_symbols"] + out


def prop(name, value, x, y, hide=False, size=1.27):
    e = ["property", Q(name), Q(value), ["at", x, y, 0], font(size)]
    if hide:
        e[-1] = font(size) + [["hide", "yes"]]
    return e


def symbol_inst(part, unit, x, y, root_uuid, sheet_uuid, pins):
    is_pwr = part.ref.startswith("#")
    bx0, by0, bx1, by1 = symbol_bbox(part.sym, unit)
    node = ["symbol", ["lib_id", Q(part.lib_id)], ["at", x, y, 0], ["unit", unit],
            ["exclude_from_sim", "no"], ["in_bom", "no" if is_pwr else "yes"],
            ["on_board", "no" if is_pwr else "yes"], ["dnp", "no"],
            ["uuid", uid(part.ref, unit)],
            prop("Reference", part.ref, x, snap(y - by1 - 1.5), hide=is_pwr),
            prop("Value", part.value, x, snap(y - by0 + 1.5)),
            prop("Footprint", part.footprint, x, y, hide=True),
            prop("Datasheet", "", x, y, hide=True)]
    for k, v in part.fields.items():
        node.append(prop(k, v, x, y, hide=True))
    for pn in sorted({p["number"] for p in pins}, key=lambda s: (len(s), s)):
        node.append(["pin", Q(pn), ["uuid", uid(part.ref, "pin", pn)]])
    node.append(["instances", ["project", Q(PROJ),
                               ["path", Q(f"/{root_uuid}/{sheet_uuid}"), ["reference", Q(part.ref)], ["unit", unit]]]])
    return node


def write_sheet(name, parts, global_nets, root_uuid, sheet_uuid, page):
    units = []
    geo = {}
    for p in parts:
        for u in (symbol_units(p.sym) if p.libpins else [1]):
            pins, box = unit_geometry(p, u)
            if not pins and p.libpins:
                continue
            geo[(p.ref, u)] = (p, u, pins)
            units.append(((p.ref, u), box))
    for paper, w, h in PAPERS:
        pos = place_units(units, w, h)
        if pos:
            break
    else:
        raise RuntimeError(f"sheet {name} does not fit A0")
    items = []
    stubs = {}
    for key, (x, y) in pos.items():
        p, u, pins = geo[key]
        items.append(symbol_inst(p, u, x, y, root_uuid, sheet_uuid, pins))
        for pin in pins:
            net = p.pins.get(pin["number"])
            ex, ey = snap(x + pin["x"]), snap(y - pin["y"])
            k = (ex, ey)
            if k in stubs:
                if stubs[k] != net:
                    raise RuntimeError(f"{p.ref} pin {pin['number']} stacked on different net")
                continue
            stubs[k] = net
            if net is None:
                items.append(["no_connect", ["at", ex, ey], ["uuid", uid(name, "nc", ex, ey)]])
                continue
            dx, dy = OUTWARD[int(pin["rot"]) % 360]
            lx, ly = snap(ex + 2.54 * dx), snap(ey + 2.54 * dy)
            items.append(["wire", ["pts", ["xy", ex, ey], ["xy", lx, ly]],
                          ["stroke", ["width", 0], ["type", "default"]], ["uuid", uid(name, "w", ex, ey)]])
            ang = LABEL_ANGLE[(dx, dy)]
            just = "left" if ang in (0, 90) else "right"
            if net in global_nets:
                items.append(["global_label", Q(net), ["shape", "passive"], ["at", lx, ly, ang],
                              ["fields_autoplaced", "yes"], font() + [["justify", just]],
                              ["uuid", uid(name, "gl", lx, ly)],
                              ["property", Q("Intersheetrefs"), Q("${INTERSHEET_REFS}"), ["at", lx, ly, 0],
                               font() + [["justify", just], ["hide", "yes"]]]])
            else:
                items.append(["label", Q(net), ["at", lx, ly, ang], font() + [["justify", just, "bottom"]],
                              ["uuid", uid(name, "l", lx, ly)]])
    sch = ["kicad_sch", ["version", 20260101], ["generator", Q("eeschema")], ["generator_version", Q("10.0")],
           ["uuid", sheet_uuid], ["paper", Q(paper)],
           ["title_block", ["title", Q(f"Dual 12-bit 10 MSPS USB ADC - {name}")], ["rev", Q("A")]],
           lib_symbols(parts)] + items + [["embedded_fonts", "no"]]
    (OUT / f"{name}.kicad_sch").write_text(dump(sch) + "\n")
    return paper, len(pos)


def main():
    OUT.mkdir(exist_ok=True)
    c = design.build()
    by_sheet = {s: [p for p in c.parts if p.sheet == s] for s in SHEETS}
    net_sheets = {}
    for p in c.parts:
        for net in p.pins.values():
            if net:
                net_sheets.setdefault(net, set()).add(p.sheet)
    global_nets = {n for n, s in net_sheets.items() if len(s) > 1 or n.startswith(("+", "-", "GND", "VBUS"))}
    root_uuid = uid("root")
    sheet_nodes = []
    for i, s in enumerate(SHEETS):
        su = uid("sheet", s)
        paper, n = write_sheet(s, by_sheet[s], global_nets, root_uuid, su, str(i + 2))
        print(f"{s}: {n} units on {paper}")
        x, y = 30 + (i % 3) * 70, 40 + (i // 3) * 50
        sheet_nodes.append(["sheet", ["at", x, y], ["size", 50, 30], ["exclude_from_sim", "no"], ["in_bom", "yes"],
                            ["on_board", "yes"], ["dnp", "no"], ["stroke", ["width", 0], ["type", "solid"]],
                            ["fill", ["color", 0, 0, 0, 0]], ["uuid", su],
                            ["property", Q("Sheetname"), Q(s), ["at", x, y - 0.8, 0],
                             font(1.524) + [["justify", "left", "bottom"]]],
                            ["property", Q("Sheetfile"), Q(f"{s}.kicad_sch"), ["at", x, y + 30.6, 0],
                             font(1.524) + [["justify", "left", "top"]]],
                            ["instances", ["project", Q(PROJ), ["path", Q(f"/{root_uuid}"), ["page", Q(str(i + 2))]]]]])
    root = ["kicad_sch", ["version", 20260101], ["generator", Q("eeschema")], ["generator_version", Q("10.0")],
            ["uuid", root_uuid], ["paper", Q("A4")],
            ["title_block", ["title", Q("Dual 12-bit 10 MSPS USB ADC")], ["rev", Q("A")]],
            ["lib_symbols"]] + sheet_nodes + [["sheet_instances", ["path", Q("/"), ["page", Q("1")]]],
                                              ["embedded_fonts", "no"]]
    (OUT / f"{PROJ}.kicad_sch").write_text(dump(root) + "\n")
    libs = sorted({p.lib_id.split(":")[0] for p in c.parts})
    (OUT / "sym-lib-table").write_text(
        "(sym_lib_table\n  (version 7)\n" +
        "".join(f'  (lib (name "{l}")(type "KiCad")(uri "{SYMDIR}/{l}.kicad_symdir")(options "")(descr ""))\n'
                for l in libs) + ")\n")
    fplibs = sorted({p.footprint.split(":")[0] for p in c.parts if p.footprint})
    fpdir = SYMDIR.parent / "footprints"
    (OUT / "fp-lib-table").write_text(
        "(fp_lib_table\n  (version 7)\n" +
        "".join(f'  (lib (name "{l}")(type "KiCad")(uri "{fpdir}/{l}.pretty")(options "")(descr ""))\n'
                for l in fplibs) + ")\n")
    pro = OUT / f"{PROJ}.kicad_pro"
    if not pro.exists():
        pro.write_text(json.dumps({"meta": {"filename": f"{PROJ}.kicad_pro", "version": 3},
                                   "sheets": [[str(root_uuid), "Root"]] + [[str(uid("sheet", s)), s] for s in SHEETS]},
                                  indent=2))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
