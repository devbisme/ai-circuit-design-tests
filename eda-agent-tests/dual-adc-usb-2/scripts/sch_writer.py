"""Write a connected, hierarchical KiCad schematic from the DesignPlan.

Fills the gap left by eda-agent's kicad_generate_project. Its schematic places
global labels on a grid that touch no pin, so the result has no connectivity,
and it places only unit 1 of multi-unit parts.

Approach (label-based):
  * the root sheet holds one sheet symbol per plan sheet;
  * each part (every unit) is placed unrotated, shelf-packed in plan order
    (plan order already groups each IC with its support parts);
  * every pin gets a 2.54 mm wire stub that ends in a power symbol (power
    nets; the symbol's Value names the net), a global label (other nets), or
    a no-connect flag;
  * PWR_FLAGs mark nets fed through passives (ferrites, PLL filter resistors).
"""

import json
import os
import uuid as _uuid

import symlib
from symlib import Q, dump, find, find1

HERE = os.path.dirname(os.path.abspath(__file__))
PROJ = os.path.join(HERE, "..", "kicad")
NAME = "dual_adc"
G = 1.27            # grid
STUB = 2.54

plan = json.load(open(os.path.join(HERE, "..", "plan", "dual_adc_plan.json")))
no_connects = {(r, p) for r, p in json.load(
    open(os.path.join(HERE, "..", "plan", "no_connects.json")))}

pin_net = {}
power_nets = set()
for n in plan["nets"]:
    if n.get("is_power") or n.get("is_ground"):
        power_nets.add(n["name"])
    for p in n["pins"]:
        pin_net[(p["refdes"], p["pin"])] = n["name"]
PWR_FLAG_NETS = ["+5V", "FT_VPHY", "OSC_VDD", "VCCPLL0", "VCCPLL1", "VBUS_F"]

ROOT_UUID = str(_uuid.uuid4())


def uid():
    return str(_uuid.uuid4())


def snap(v):
    return round(round(v / G) * G, 4)


def fmt(v):
    v = round(v, 4)
    return str(int(v)) if v == int(v) else str(v)


# ---------------------------------------------------------------- symbols --
sym_cache = {}


def get_sym(lib_ref):
    if lib_ref not in sym_cache:
        lib, name = lib_ref.split(":")
        s = symlib.load_symbol(lib, name)
        sym_cache[lib_ref] = (s, symlib.pins(s))
    return sym_cache[lib_ref]


def lib_symbol_block(lib_ref):
    s, _ = get_sym(lib_ref)
    s = list(s)
    s[1] = Q(lib_ref)
    return dump(s, 2)


def unit_list(pins):
    units = sorted({p["unit"] for p in pins if p["unit"] > 0})
    return units or [1]


def unit_pins(pins, u):
    return [p for p in pins if p["unit"] in (u, 0)]


def body_bbox(sym, u):
    """Bounding box of the unit's graphics and pins, in library coords (y up)."""
    xs, ys = [], []
    for sub in find(sym, "symbol"):
        tail = sub[1].rsplit("_", 2)
        if int(tail[-2]) not in (0, u) or int(tail[-1]) > 1:
            continue
        for g in sub:
            if not isinstance(g, list):
                continue
            if g[0] == "rectangle":
                for k in ("start", "end"):
                    e = find1(g, k)
                    xs.append(float(e[1])); ys.append(float(e[2]))
            elif g[0] in ("polyline", "bezier"):
                for xy in find(find1(g, "pts"), "xy"):
                    xs.append(float(xy[1])); ys.append(float(xy[2]))
            elif g[0] == "circle":
                c = find1(g, "center"); r = float(find1(g, "radius")[1])
                xs += [float(c[1]) - r, float(c[1]) + r]
                ys += [float(c[2]) - r, float(c[2]) + r]
    _, pins = get_sym_by_obj(sym)
    for p in unit_pins(pins, u):
        xs.append(p["x"]); ys.append(p["y"])
    if not xs:
        return (-2.54, -2.54, 2.54, 2.54)
    return min(xs), min(ys), max(xs), max(ys)


def get_sym_by_obj(sym):
    for v in sym_cache.values():
        if v[0] is sym:
            return v
    raise KeyError


DIRS = {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}   # stub dir, sch coords


def stub_dir(p):
    """Direction (schematic coords, y down) pointing away from the body."""
    a = int(p["angle"]) % 360
    # Library pin angle = direction from connection point toward body (y up).
    # 0 → body to the right → stub goes left. 90 → body above (lib y up) →
    # stub goes down in lib coords → +y in schematic coords.
    return DIRS[a]


def label_len(text):
    return len(text) * 1.0 + 3.0


# ------------------------------------------------------------- emitters ---
def prop(name, value, x, y, hide=False, angle=0, justify=None):
    j = f" (justify {justify})" if justify else ""
    h = " (hide yes)" if hide else ""
    return (f'\t\t(property "{name}" "{esc(value)}" (at {fmt(x)} {fmt(y)} {angle})'
            f'{h} (effects (font (size 1.27 1.27)){j}))')


def esc(s):
    return str(s).replace("\\", "\\\\").replace('"', '\\"')


def in_bom(lib_ref):
    if lib_ref.startswith("power:"):
        return "yes"
    e = find1(get_sym(lib_ref)[0], "in_bom")
    return str(e[1]) if e else "yes"


def symbol_instance(lib_ref, ref, value, x, y, unit, pins, sheet_path, fields,
                    rot=0, hide_ref=False, hide_val=False, bbox=None):
    out = [f'\t(symbol (lib_id "{esc(lib_ref)}") (at {fmt(x)} {fmt(y)} {rot}) (unit {unit})',
           f'\t\t(exclude_from_sim no) (in_bom {in_bom(lib_ref)}) (on_board yes) (dnp no)',
           f'\t\t(uuid "{uid()}")']
    if bbox:
        x0, y0, x1, y1 = bbox
        out.append(prop("Reference", ref, x + (x0 + x1) / 2, y - y1 - 1.6, hide_ref))
        out.append(prop("Value", value, x + (x0 + x1) / 2, y - y0 + 1.6, hide_val))
    else:
        out.append(prop("Reference", ref, x, y - 3, hide_ref))
        out.append(prop("Value", value, x, y + 3, hide_val))
    for k, v in fields.items():
        out.append(prop(k, v, x, y, hide=True))
    for p in pins:
        out.append(f'\t\t(pin "{esc(p)}" (uuid "{uid()}"))')
    out.append(f'\t\t(instances (project "{NAME}" (path "{sheet_path}" '
               f'(reference "{esc(ref)}") (unit {unit}))))')
    out.append("\t)")
    return "\n".join(out)


def wire(x0, y0, x1, y1):
    return (f'\t(wire (pts (xy {fmt(x0)} {fmt(y0)}) (xy {fmt(x1)} {fmt(y1)}))'
            f' (stroke (width 0) (type default)) (uuid "{uid()}"))')


def glabel(name, x, y, d):
    ang = {(-1, 0): 180, (1, 0): 0, (0, -1): 90, (0, 1): 270}[d]
    just = "right" if ang in (180, 90) else "left"
    return (f'\t(global_label "{esc(name)}" (shape bidirectional) (at {fmt(x)} {fmt(y)} {ang})'
            f' (fields_autoplaced yes) (effects (font (size 1.27 1.27)) (justify {just}))'
            f' (uuid "{uid()}"))')


def noconn(x, y):
    return f'\t(no_connect (at {fmt(x)} {fmt(y)}) (uuid "{uid()}"))'


pwr_counter = [0]


def power_symbol(net, x, y, d, sheet_path):
    """Power symbol whose pin sits at (x, y), graphic pointing along d."""
    pwr_counter[0] += 1
    ref = f"#PWR{pwr_counter[0]:04d}"
    if net == "GND":
        lib, rot = "power:GND", {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[d]
    elif net.startswith("-"):
        lib, rot = "power:VEE", {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}[d]
    else:
        lib, rot = "power:VCC", {(0, -1): 0, (-1, 0): 90, (0, 1): 180, (1, 0): 270}[d]
    used_libs.add(lib)
    return symbol_instance(lib, ref, net, x, y, 1, ["1"], sheet_path, {}, rot=rot,
                           hide_ref=True)


def pwr_flag(x, y, sheet_path):
    pwr_counter[0] += 1
    used_libs.add("power:PWR_FLAG")
    return symbol_instance("power:PWR_FLAG", f"#FLG{pwr_counter[0]:04d}", "PWR_FLAG",
                           x, y, 1, ["1"], sheet_path, {}, hide_ref=True)


used_libs = set()

# --------------------------------------------------------------- layout ---
PAPERS = [("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594), ("A0", 1189, 841)]


def layout_sheet(items, width):
    """Shelf-pack items [(key, w, h)] left→right, top→bottom; returns pos map."""
    x, y, shelf_h = 20.0, 25.0, 0.0
    pos = {}
    for key, w, h in items:
        if x + w > width - 15 and x > 20:
            x, y, shelf_h = 20.0, y + shelf_h + 6, 0.0
        pos[key] = (x, y)
        x += w + 6
        shelf_h = max(shelf_h, h)
    return pos, y + shelf_h


def build_sheet(sheet_name, sheet_path):
    parts = [p for p in plan["parts"] if p.get("sheet", "main") == sheet_name]
    items, info = [], {}
    for p in parts:
        sym, pins = get_sym(p["lib_ref"])
        for u in unit_list(pins):
            x0, y0, x1, y1 = body_bbox(sym, u)
            up = unit_pins(pins, u)
            # Margins for stubs + labels on each side.
            ml = mr = mt = mb = 2.0
            for pin in up:
                net = pin_net.get((p["refdes"], pin["number"]))
                ll = STUB + (label_len(net) if net and net not in power_nets else 6)
                d = stub_dir(pin)
                if d == (-1, 0): ml = max(ml, ll)
                if d == (1, 0): mr = max(mr, ll)
                if d == (0, -1): mt = max(mt, ll)
                if d == (0, 1): mb = max(mb, ll)
            mt = max(mt, 4.5); mb = max(mb, 4.5)   # ref / value text
            w = (x1 - x0) + ml + mr
            h = (y1 - y0) + mt + mb
            key = (p["refdes"], u)
            items.append((key, w, h))
            info[key] = (p, sym, up, (x0, y0, x1, y1), ml, mt)
    for paper, W, H in PAPERS:
        pos, bottom = layout_sheet(items, W)
        if bottom < H - 40:
            break
    out_items = []
    flags = []
    for key, (px, py) in pos.items():
        p, sym, up, (x0, y0, x1, y1), ml, mt = info[key]
        # Symbol origin so the bbox's top-left lands at (px+ml, py+mt); y flips.
        sx = snap(px + ml - x0)
        sy = snap(py + mt + y1)
        fields = {"Footprint": p.get("footprint", ""),
                  "Datasheet": p.get("datasheet_url", "") or symlib.prop(sym, "Datasheet") or "",
                  "Description": symlib.prop(sym, "Description") or ""}
        if p.get("mpn"):
            fields["MPN"] = p["mpn"]
        if p.get("manufacturer"):
            fields["Manufacturer"] = p["manufacturer"]
        if p.get("role", "").startswith("tolerance"):
            fields["Tolerance"] = p["role"].split()[-1]
        all_pins = [q["number"] for q in up]
        out_items.append(symbol_instance(
            p["lib_ref"], p["refdes"], p.get("value", ""), sx, sy, key[1],
            all_pins, sheet_path, fields, bbox=(x0, y0, x1, y1),
            hide_val=p["lib_ref"].startswith("Mechanical:")))
        done = {}
        for pin in up:
            k = (p["refdes"], pin["number"])
            ex, ey = sx + pin["x"], sy - pin["y"]
            net = pin_net.get(k)
            where = (round(ex, 3), round(ey, 3))
            if where in done:          # stacked pins: one stub serves all
                if done[where] != net:
                    raise SystemExit(f"stacked pins with different nets at {k}")
                continue
            done[where] = net
            if k in no_connects:
                out_items.append(noconn(ex, ey))
                continue
            if net is None:
                raise SystemExit(f"pin {k} has no net and is not NC")
            d = stub_dir(pin)
            tx, ty = ex + d[0] * STUB, ey + d[1] * STUB
            out_items.append(wire(ex, ey, tx, ty))
            if net in power_nets:
                out_items.append(power_symbol(net, tx, ty, d, sheet_path))
            else:
                out_items.append(glabel(net, tx, ty, d))
            if net in PWR_FLAG_NETS and net not in placed_flags:
                placed_flags.add(net)
                flags.append(net)
    # PWR_FLAGs in their own row under the packed parts.
    fx, fy = 30.48, snap(bottom + 12)
    for net in flags:
        out_items.append(wire(fx, fy, fx, fy + 5.08))
        if net in power_nets:
            out_items.append(power_symbol(net, fx, fy + 5.08, (0, 1) if net == "GND" else (0, -1), sheet_path))
            # power symbol drawn at the lower end; flag at the upper end
        else:
            out_items.append(glabel(net, fx, fy + 5.08, (0, 1)))
        out_items.append(pwr_flag(fx, fy, sheet_path))
        fx += 25.4
    return paper, out_items


placed_flags = set()


def write_sheet_file(path, paper, body, title, file_uuid):
    libs = sorted({l for l in used_libs_sheet})
    lines = ["(kicad_sch", "\t(version 20250114)", '\t(generator "eeschema")',
             '\t(generator_version "9.0")', f'\t(uuid "{file_uuid}")',
             f'\t(paper "{paper}")',
             f'\t(title_block (title "{esc(title)}") (company "eda-agent-tests / dual-adc-usb-2"))',
             "\t(lib_symbols"]
    for l in libs:
        lines.append("\t\t" + lib_symbol_block(l))
    lines.append("\t)")
    lines += body
    return lines


os.makedirs(PROJ, exist_ok=True)
sheets = [s["name"] for s in plan["sheets"]]
root_body = []
for i, sname in enumerate(sheets):
    sheet_uuid = uid()
    used_libs = set()
    sheet_path = f"/{ROOT_UUID}/{sheet_uuid}"
    paper, body = build_sheet(sname, sheet_path)
    used_libs_sheet = used_libs | {p["lib_ref"] for p in plan["parts"]
                                   if p.get("sheet") == sname}
    lines = write_sheet_file(None, paper, body, f"Dual ADC - {sname}", uid())
    lines += ["\t(embedded_fonts no)", ")"]
    with open(os.path.join(PROJ, f"{sname}.kicad_sch"), "w") as fh:
        fh.write("\n".join(lines) + "\n")
    x, y = 30 + (i % 3) * 70, 40 + (i // 3) * 50
    root_body.append(
        f'\t(sheet (at {x} {y}) (size 50 30) (fields_autoplaced yes)\n'
        f'\t\t(stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000))\n'
        f'\t\t(uuid "{sheet_uuid}")\n'
        f'\t\t(property "Sheetname" "{sname}" (at {x} {y - 0.7} 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n'
        f'\t\t(property "Sheetfile" "{sname}.kicad_sch" (at {x} {y + 30.6} 0) (effects (font (size 1.27 1.27)) (justify left top)))\n'
        f'\t\t(instances (project "{NAME}" (path "/{ROOT_UUID}" (page "{i + 2}"))))\n\t)')
    print(f"{sname}: {paper}, {len(body)} items")

notes = ("Dual-channel ±10 V, 10 MS/s, 12-bit USB ADC.\\n"
         "Plan: plan/dual_adc_plan.json (eda-agent DesignPlan). "
         "See design_decisions.md for part choices and open items.")
root = ["(kicad_sch", "\t(version 20250114)", '\t(generator "eeschema")',
        '\t(generator_version "9.0")', f'\t(uuid "{ROOT_UUID}")', '\t(paper "A4")',
        '\t(title_block (title "Dual-channel USB ADC") (company "eda-agent-tests / dual-adc-usb-2"))',
        "\t(lib_symbols)"]
root += root_body
root.append(f'\t(text "{notes}" (exclude_from_sim no) (at 30 150 0) '
            f'(effects (font (size 2 2)) (justify left)) (uuid "{uid()}"))')
root += ['\t(sheet_instances (path "/" (page "1")))', "\t(embedded_fonts no)", ")"]
with open(os.path.join(PROJ, f"{NAME}.kicad_sch"), "w") as fh:
    fh.write("\n".join(root) + "\n")
print("written to", os.path.abspath(PROJ))
