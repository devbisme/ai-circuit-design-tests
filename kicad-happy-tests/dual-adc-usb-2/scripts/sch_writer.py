"""
Label-based KiCad 9/10 hierarchical schematic writer for a SKiDL circuit.

Each SKiDL subcircuit becomes one sheet. Symbols are placed unrotated with shelf packing;
every pin gets a short wire stub ending in:
  - a power symbol (rails),
  - a global label (net used on more than one sheet),
  - a local label (net confined to the sheet), or
  - a no-connect flag (SKiDL NC).
Electrical correctness comes from labels, so connectivity is exact by construction; the
netlist exported by kicad-cli is compared against SKiDL's (scripts/compare_netlists.py).

Usage (from the SKiDL design, after the circuit is built):
    from sch_writer import write_schematic
    write_schematic(default_circuit, outdir, project="dual_adc_usb", libdir="lib")
"""
import math
import os
import re
import uuid
from collections import defaultdict

GRID = 1.27
NS = uuid.UUID("6f1d6c3e-1d1a-4b55-9a77-3f3f2a6a0c11")

# Rail net -> (power lib symbol, is_ground)
POWER_SYMS = {
    "GND": ("GND", True),
    "+3V3": ("+3V3", False),
    "+5V": ("+5V", False),
    "+1V2": ("+1V2", False),
    "VBUS": ("VBUS", False),
    "+3V3_ADC": ("+3V3", False),
    "+3V3A": ("+3.3VA", False),
    "-3V3A": ("-3V3", True),  # graphic points down like GND
}

PAPERS = [("A4", 297, 210), ("A3", 420, 297), ("A2", 594, 420), ("A1", 841, 594), ("A0", 1189, 841)]


def uid(*names):
    return str(uuid.uuid5(NS, "/".join(str(n) for n in names)))


def snap(v):
    return round(round(v / GRID) * GRID, 4)


def q(s):
    return '"' + str(s).replace("\\", "\\\\").replace('"', '\\"') + '"'


# ------------------------------------------------------------------ s-expression utilities
def tokenize(text):
    return re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)


def parse(text):
    stack, cur = [], []
    for t in tokenize(text):
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t)
    return cur[0]


def unq(t):
    return t[1:-1].replace('\\"', '"').replace("\\\\", "\\") if isinstance(t, str) and t.startswith('"') else t


def dump(node, ind=1):
    if not isinstance(node, list):
        return node
    simple = all(not isinstance(x, list) for x in node)
    if simple:
        return "(" + " ".join(node) + ")"
    pad = "\t" * ind
    parts = []
    head = []
    for x in node:
        if isinstance(x, list):
            parts.append(pad + dump(x, ind + 1))
        else:
            head.append(x)
    return "(" + " ".join(head) + "\n" + "\n".join(parts) + "\n" + "\t" * (ind - 1) + ")"


def kids(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]


# ------------------------------------------------------------------ symbol library access
class SymLib:
    def __init__(self, libdir):
        self.libdir = libdir
        self.cache = {}

    def _lib(self, lib):
        if lib not in self.cache:
            root = parse(open(os.path.join(self.libdir, lib + ".kicad_sym")).read())
            self.cache[lib] = {unq(s[1]): s for s in kids(root, "symbol")}
        return self.cache[lib]

    def flat(self, lib, name):
        """Return a flattened symbol (no 'extends') named 'lib:name' (recursive for chains)."""
        sym = self._lib(lib)[name]
        ext = kids(sym, "extends")
        if not ext:
            node = list(sym)
            node[1] = q(f"{lib}:{name}")
            return node
        pname = unq(ext[0][1])
        parent = self.flat(lib, pname)
        child_props = {unq(p[1]): p for p in kids(sym, "property")}
        new = []
        for x in parent:
            if isinstance(x, list) and x and x[0] == "property" and unq(x[1]) in child_props:
                new.append(child_props.pop(unq(x[1])))
            elif isinstance(x, list) and x and x[0] == "symbol":
                sub = list(x)
                sub[1] = q(name + unq(sub[1])[len(pname):])
                new.append(sub)
            else:
                new.append(x)
        idx = next(i for i, x in enumerate(new) if isinstance(x, list) and x and x[0] == "symbol")
        new[idx:idx] = list(child_props.values())
        new[1] = q(f"{lib}:{name}")
        return new


def symbol_pins(sym):
    """{pin_number: (unit, x, y, angle, length, etype)} from a flattened symbol (symbol coords, y up)."""
    name = unq(sym[1]).split(":")[1]
    pins = {}
    for sub in kids(sym, "symbol"):
        m = re.match(r"^" + re.escape(name) + r"_(\d+)_(\d+)$", unq(sub[1]))
        unit = int(m.group(1)) if m else 1
        style = int(m.group(2)) if m else 1
        if style not in (0, 1):
            continue
        for p in kids(sub, "pin"):
            at = kids(p, "at")[0]
            ln = float(kids(p, "length")[0][1])
            num = unq(kids(p, "number")[0][1])
            pins.setdefault(num, (unit, float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0.0, ln, p[1]))
    return pins


def symbol_bbox(sym, unit):
    """Body bbox (symbol coords) from graphics and pin ends for one unit (unit 0 = common)."""
    name = unq(sym[1]).split(":")[1]
    xs, ys = [], []
    for sub in kids(sym, "symbol"):
        m = re.match(r"^" + re.escape(name) + r"_(\d+)_(\d+)$", unq(sub[1]))
        if not m or int(m.group(1)) not in (0, unit) or int(m.group(2)) not in (0, 1):
            continue
        for g in sub:
            if not isinstance(g, list):
                continue
            if g[0] == "rectangle":
                for k in ("start", "end"):
                    v = kids(g, k)[0]
                    xs.append(float(v[1]))
                    ys.append(float(v[2]))
            elif g[0] in ("polyline", "bezier"):
                for pts in kids(g, "pts"):
                    for xy in kids(pts, "xy"):
                        xs.append(float(xy[1]))
                        ys.append(float(xy[2]))
            elif g[0] in ("circle", "arc"):
                for k in ("center", "start", "end", "mid"):
                    for v in kids(g, k):
                        xs.append(float(v[1]))
                        ys.append(float(v[2]))
            elif g[0] == "pin":
                at = kids(g, "at")[0]
                xs.append(float(at[1]))
                ys.append(float(at[2]))
    if not xs:
        return (-2.54, -2.54, 2.54, 2.54)
    return (min(xs), min(ys), max(xs), max(ys))


# ------------------------------------------------------------------ main writer
def outward(angle):
    """Pin 'at' angle (direction from connection point into the body) -> outward unit vector in
    sheet coordinates (y down)."""
    a = int(round(angle)) % 360
    return {0: (-1, 0), 180: (1, 0), 90: (0, 1), 270: (0, -1)}[a]


def label_angle(out):
    return {(-1, 0): 180, (1, 0): 0, (0, 1): 270, (0, -1): 90}[out]


def power_rot(out, ground):
    up = {(0, -1): 0, (0, 1): 180, (-1, 0): 90, (1, 0): 270}
    down = {(0, 1): 0, (0, -1): 180, (-1, 0): 270, (1, 0): 90}
    return (down if ground else up)[out]


def text_len(s):
    return 1.0 * len(s) + 2.0


def write_schematic(circuit, outdir, project, libdir, title=""):
    os.makedirs(outdir, exist_ok=True)
    lib = SymLib(libdir)
    root_uuid = uid(project, "root")

    # Collect parts per sheet.
    sheets = defaultdict(list)
    for p in circuit.parts:
        sheet = p.hiertuple[-1] if getattr(p, "hiertuple", None) and len(p.hiertuple) > 1 else "top"
        sheets[sheet].append(p)

    # Net -> set of sheets (for global vs local labels).
    def netname(pin):
        n = pin.net
        if n is None or n.name.startswith("__NOCONNECT"):
            return None
        return n.name

    net_sheets = defaultdict(set)
    for sheet, parts in sheets.items():
        for p in parts:
            for pin in p.pins:
                n = netname(pin)
                if n:
                    net_sheets[n].add(sheet)

    pwr_count = [0]
    pwr_syms_used = set()
    sheet_files = []
    sheet_order = ["power1", "usb_interface1", "front_end1", "front_end2", "adc1", "clocks1", "sdram1", "fpga1"]
    names = sorted(sheets, key=lambda s: sheet_order.index(s) if s in sheet_order else 99)

    for page, sheet in enumerate(names, start=2):
        sheet_uuid = uid(project, "sheet", sheet)
        inst_path = f"/{root_uuid}/{sheet_uuid}"
        fname = f"{sheet}.kicad_sch"
        sheet_files.append((sheet, fname, sheet_uuid, page))
        lib_syms = {}
        items = []  # placed unit records

        # Build unit records: (part, unit, sym, pins in unit, bbox)
        for p in sorted(sheets[sheet], key=lambda x: (-len(x.pins), x.ref)):
            libname = str(p.lib.filename if hasattr(p.lib, "filename") else p.lib)
            libname = os.path.splitext(os.path.basename(libname))[0]
            sym = lib.flat(libname, p.name)
            lib_id = f"{libname}:{p.name}"
            lib_syms[lib_id] = sym
            spins = symbol_pins(sym)
            units = sorted({u for (u, *_r) in spins.values() if u != 0}) or [1]
            for u in units:
                upins = {n: v for n, v in spins.items() if v[0] in (0, u)}
                bb = symbol_bbox(sym, u)
                items.append(dict(part=p, unit=u, sym=sym, lib_id=lib_id, pins=upins, bb=bb,
                                  nunits=len(units)))

        # Margins for stubs + labels per side.
        pinnet = {}
        for it in items:
            p = it["part"]
            for pin in p.pins:
                pinnet[(p.ref, str(pin.num))] = netname(pin)
        for it in items:
            m = {"L": 3.0, "R": 3.0, "T": 3.0, "B": 3.0}
            for num, (_u, x, y, a, ln, et) in it["pins"].items():
                n = pinnet.get((it["part"].ref, num))
                o = outward(a)
                lab = 2.54 + (text_len(n) if n and n not in POWER_SYMS else 6.0)
                side = {(-1, 0): "L", (1, 0): "R", (0, 1): "B", (0, -1): "T"}[o]
                m[side] = max(m[side], lab)
            x0, y0, x1, y1 = it["bb"]
            # sheet-coord extents relative to symbol origin (y flips)
            it["ext"] = (x0 - m["L"], -y1 - m["T"] - 2.54, x1 + m["R"], -y0 + m["B"] + 2.54)
            it["w"] = it["ext"][2] - it["ext"][0]
            it["h"] = it["ext"][3] - it["ext"][1]

        # Choose paper and shelf-pack.
        area = sum(it["w"] * it["h"] for it in items)
        for pname, pw, ph in PAPERS:
            if area * 1.6 < (pw - 40) * (ph - 50) and max(it["w"] for it in items) < pw - 40:
                break
        while True:
            x, y, shelf_h = 20.0, 25.0, 0.0
            ok = True
            for it in items:
                if x + it["w"] > pw - 20:
                    x, y = 20.0, y + shelf_h
                    shelf_h = 0.0
                it["origin"] = (snap(x - it["ext"][0]), snap(y - it["ext"][1]))
                x += it["w"]
                shelf_h = max(shelf_h, it["h"])
            if y + shelf_h > ph - 30:
                idx = [pp[0] for pp in PAPERS].index(pname)
                if idx + 1 >= len(PAPERS):
                    break
                pname, pw, ph = PAPERS[idx + 1]
                continue
            break

        out = []
        for it in items:
            p = it["part"]
            X, Y = it["origin"]
            u = it["unit"]
            fields = [("Reference", p.ref, (X, Y + it["ext"][1] + 1.5), False),
                      ("Value", str(p.value), (X, Y + it["ext"][3] - 1.0), False),
                      ("Footprint", p.footprint or "", (X, Y), True),
                      ("Datasheet", "", (X, Y), True)]
            for k in ("MPN", "Tolerance", "Dielectric"):
                v = getattr(p, k, None) if k in vars(p) else None
                if v:
                    fields.append((k, str(v), (X, Y), True))
            props = []
            for k, v, (fx, fy), hide in fields:
                props.append(f'\t\t(property {q(k)} {q(v)}\n\t\t\t(at {snap(fx)} {snap(fy)} 0)\n'
                             + ("\t\t\t(hide yes)\n" if hide else "")
                             + "\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)")
            pin_lines = "".join(f'\t\t(pin {q(n)}\n\t\t\t(uuid {q(uid(project, p.ref, "pin", n))})\n\t\t)\n'
                                for n in it["pins"])
            is_pwr = p.ref.startswith("#")
            out.append(
                f"\t(symbol\n\t\t(lib_id {q(it['lib_id'])})\n\t\t(at {X} {Y} 0)\n\t\t(unit {u})\n"
                f"\t\t(exclude_from_sim no)\n\t\t(in_bom {'no' if is_pwr else 'yes'})\n"
                f"\t\t(on_board {'no' if is_pwr else 'yes'})\n\t\t(dnp no)\n"
                f"\t\t(uuid {q(uid(project, p.ref, 'unit', u))})\n" + "\n".join(props) + "\n" + pin_lines
                + f"\t\t(instances\n\t\t\t(project {q(project)}\n\t\t\t\t(path {q(inst_path)}\n"
                f"\t\t\t\t\t(reference {q(p.ref)})\n\t\t\t\t\t(unit {u})\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)")

            # Pin stubs and terminations.
            for num, (_u, px, py, a, ln, et) in sorted(it["pins"].items()):
                sx, sy = snap(X + px), snap(Y - py)
                o = outward(a)
                ex, ey = snap(sx + 2.54 * o[0]), snap(sy + 2.54 * o[1])
                n = pinnet.get((p.ref, num))
                key = (p.ref, num)
                if n is None:
                    out.append(f"\t(no_connect\n\t\t(at {sx} {sy})\n\t\t(uuid {q(uid(project, sheet, 'nc', *key))})\n\t)")
                    continue
                out.append(f"\t(wire\n\t\t(pts\n\t\t\t(xy {sx} {sy}) (xy {ex} {ey})\n\t\t)\n\t\t(stroke\n\t\t\t(width 0)\n"
                           f"\t\t\t(type default)\n\t\t)\n\t\t(uuid {q(uid(project, sheet, 'w', *key))})\n\t)")
                if n in POWER_SYMS:
                    symname, ground = POWER_SYMS[n]
                    pwr_syms_used.add(symname)
                    pwr_count[0] += 1
                    ref = f"#PWR{pwr_count[0]:04d}"
                    rot = power_rot(o, ground)
                    vx, vy = snap(ex + 3.81 * o[0]), snap(ey + 3.81 * o[1])
                    out.append(
                        f"\t(symbol\n\t\t(lib_id {q('power:' + symname)})\n\t\t(at {ex} {ey} {rot})\n\t\t(unit 1)\n"
                        f"\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n\t\t(on_board yes)\n\t\t(dnp no)\n"
                        f"\t\t(uuid {q(uid(project, sheet, 'pwr', *key))})\n"
                        f"\t\t(property \"Reference\" {q(ref)}\n\t\t\t(at {ex} {ey} 0)\n\t\t\t(hide yes)\n"
                        f"\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
                        f"\t\t(property \"Value\" {q(n)}\n\t\t\t(at {vx} {vy} 0)\n"
                        f"\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.0 1.0)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
                        f"\t\t(property \"Footprint\" \"\"\n\t\t\t(at {ex} {ey} 0)\n\t\t\t(hide yes)\n"
                        f"\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
                        f"\t\t(property \"Datasheet\" \"\"\n\t\t\t(at {ex} {ey} 0)\n\t\t\t(hide yes)\n"
                        f"\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n"
                        f"\t\t(pin \"1\"\n\t\t\t(uuid {q(uid(project, sheet, 'pwrpin', *key))})\n\t\t)\n"
                        f"\t\t(instances\n\t\t\t(project {q(project)}\n\t\t\t\t(path {q(inst_path)}\n"
                        f"\t\t\t\t\t(reference {q(ref)})\n\t\t\t\t\t(unit 1)\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)")
                    continue
                ang = label_angle(o)
                just = "left" if ang in (0, 90) else "right"
                if len(net_sheets[n]) > 1:
                    out.append(
                        f"\t(global_label {q(n)}\n\t\t(shape bidirectional)\n\t\t(at {ex} {ey} {ang})\n"
                        f"\t\t(fields_autoplaced yes)\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.0 1.0)\n\t\t\t)\n"
                        f"\t\t\t(justify {just})\n\t\t)\n\t\t(uuid {q(uid(project, sheet, 'gl', *key))})\n"
                        f"\t\t(property \"Intersheetrefs\" \"${{INTERSHEET_REFS}}\"\n\t\t\t(at {ex} {ey} 0)\n"
                        f"\t\t\t(effects\n\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(hide yes)\n\t\t\t)\n\t\t)\n\t)")
                else:
                    out.append(
                        f"\t(label {q(n)}\n\t\t(at {ex} {ey} {ang})\n\t\t(effects\n\t\t\t(font\n\t\t\t\t(size 1.0 1.0)\n"
                        f"\t\t\t)\n\t\t\t(justify {just} bottom)\n\t\t)\n\t\t(uuid {q(uid(project, sheet, 'l', *key))})\n\t)")

        for s in sorted(pwr_syms_used):
            lib_syms["power:" + s] = lib.flat("power", s)
        pwr_syms_used.clear()

        text = (f"(kicad_sch\n\t(version 20250114)\n\t(generator \"eeschema\")\n\t(generator_version \"9.0\")\n"
                f"\t(uuid {q(sheet_uuid)})\n\t(paper {q(pname)})\n"
                f"\t(title_block\n\t\t(title {q(title + ' - ' + sheet)})\n\t\t(comment 1 \"Generated from dual_adc_usb.py (SKiDL) by scripts/sch_writer.py\")\n\t)\n"
                "\t(lib_symbols\n" + "\n".join("\t\t" + dump(s, 3) for _k, s in sorted(lib_syms.items())) + "\n\t)\n"
                + "\n".join(out) + "\n\t(embedded_fonts no)\n)\n")
        open(os.path.join(outdir, fname), "w").write(text)

    # Root sheet with one sheet symbol per subcircuit.
    blocks = []
    for i, (sheet, fname, suuid, page) in enumerate(sheet_files):
        x, y = 25.4 + (i % 4) * 63.5, 38.1 + (i // 4) * 38.1
        blocks.append(
            f"\t(sheet\n\t\t(at {x} {y})\n\t\t(size 50.8 25.4)\n\t\t(exclude_from_sim no)\n\t\t(in_bom yes)\n"
            f"\t\t(on_board yes)\n\t\t(dnp no)\n\t\t(fields_autoplaced yes)\n\t\t(stroke\n\t\t\t(width 0.1524)\n"
            f"\t\t\t(type solid)\n\t\t)\n\t\t(fill\n\t\t\t(color 0 0 0 0.0000)\n\t\t)\n\t\t(uuid {q(suuid)})\n"
            f"\t\t(property \"Sheetname\" {q(sheet)}\n\t\t\t(at {x} {round(y - 0.7, 4)} 0)\n\t\t\t(effects\n"
            f"\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left bottom)\n\t\t\t)\n\t\t)\n"
            f"\t\t(property \"Sheetfile\" {q(fname)}\n\t\t\t(at {x} {round(y + 26.0, 4)} 0)\n\t\t\t(effects\n"
            f"\t\t\t\t(font\n\t\t\t\t\t(size 1.27 1.27)\n\t\t\t\t)\n\t\t\t\t(justify left top)\n\t\t\t)\n\t\t)\n"
            f"\t\t(instances\n\t\t\t(project {q(project)}\n\t\t\t\t(path {q('/' + root_uuid)}\n"
            f"\t\t\t\t\t(page {q(str(page))})\n\t\t\t\t)\n\t\t\t)\n\t\t)\n\t)")
    root = (f"(kicad_sch\n\t(version 20250114)\n\t(generator \"eeschema\")\n\t(generator_version \"9.0\")\n"
            f"\t(uuid {q(root_uuid)})\n\t(paper \"A4\")\n\t(title_block\n\t\t(title {q(title)})\n"
            f"\t\t(comment 1 \"Generated from dual_adc_usb.py (SKiDL) by scripts/sch_writer.py\")\n\t)\n"
            "\t(lib_symbols)\n" + "\n".join(blocks)
            + "\n\t(sheet_instances\n\t\t(path \"/\"\n\t\t\t(page \"1\")\n\t\t)\n\t)\n\t(embedded_fonts no)\n)\n")
    open(os.path.join(outdir, project + ".kicad_sch"), "w").write(root)
    return [f for _s, f, _u, _p in sheet_files]
