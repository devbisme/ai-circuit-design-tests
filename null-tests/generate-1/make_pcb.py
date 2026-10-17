"""
Build dual_adc.kicad_pcb from a KiCad netlist: load footprints, assign nets,
place parts, draw the board outline and ground plane.

Run with KiCad 10's bundled Python:
    ~/bin/kicad10-root/bin/python3.11 make_pcb.py dual_adc_sch.net dual_adc.kicad_pcb
"""

import math
import re
import sys

import pcbnew as pn

FP_ROOT = "/home/devb/bin/kicad10-root/share/kicad/footprints/"
W, H = 140.0, 95.0  # board size, mm
MM = pn.FromMM


# ---------------------------------------------------------------------------
# Minimal s-expression reader for the KiCad netlist.
# ---------------------------------------------------------------------------
def sexp(text):
    tokens = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return cur[0]


def find(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]


def get(node, key, default=None):
    r = find(node, key)
    return r[0][1] if r and len(r[0]) > 1 else default


def read_netlist(path):
    root = sexp(open(path).read())
    comps = {}
    for c in find(find(root, "components")[0], "comp"):
        ref = get(c, "ref")
        fpid = get(c, "footprint") or ""
        if ref.startswith("#") or ":" not in fpid or fpid.endswith(":"):
            continue  # power flags and other non-physical symbols
        sp = find(c, "sheetpath")[0]
        comps[ref] = dict(
            value=get(c, "value"),
            footprint=get(c, "footprint"),
            sheet=get(sp, "names"),
            sheet_ts=get(sp, "tstamps"),
            ts=get(c, "tstamps") or get(c, "tstamp"),
        )
    nets = {}
    for n in find(find(root, "nets")[0], "net"):
        name = get(n, "name")
        nets[name] = [(get(x, "ref"), get(x, "pin")) for x in find(n, "node")
                      if get(x, "ref") in comps]
    return comps, nets


# ---------------------------------------------------------------------------
# Placement data.
# ---------------------------------------------------------------------------
# Fixed placement of major parts, identified by (value or footprint fragment,
# sheet fragment): (x, y, rotation).
FIXED = [
    (("BNC CHA", None), (14.0, 22.0, 90)),
    (("BNC CHB", None), (14.0, 72.0, 90)),
    (("USB_B_OST", None), (123.5, 45.0, 0)),
    (("LTC2290CUP", None), (57.0, 47.0, 0)),
    (("ICE40HX4K-TQ144", None), (90.0, 47.0, 0)),
    (("IS42S16400J-7TL", None), (90.0, 15.5, 90)),
    (("FT232HL", None), (112.0, 54.0, 270)),
    (("BAV199DW", None), (25.0, 47.0, 0)),
    # Front end A (top) and B (bottom).
    (("OPA356xxDBV", "front_end1"), [(29.0, 12.0, 0), (29.0, 32.0, 0)]),
    (("THS4521ID", "front_end1"), (42.0, 30.0, 0)),
    (("OPA356xxDBV", "front_end2"), [(29.0, 62.0, 0), (29.0, 82.0, 0)]),
    (("THS4521ID", "front_end2"), (42.0, 64.0, 0)),
    # Clock.
    (("ASE-10.000MHz", None), (45.0, 47.0, 0)),
    # Power.
    (("TPS62160DSG", None), (126.0, 80.0, 0)),
    (("AP2112K-1.2", None), (104.0, 74.0, 0)),
    (("LP5907MFX-4.5", None), (14.0, 47.0, 90)),
    (("LP5907MFX-3.0", None), (60.0, 66.0, 0)),
    (("REF3020", None), (19.0, 54.0, 0)),
    # Config flash, headers.
    (("W25Q32JVSS", None), (97.0, 66.0, 0)),
    (("FPGA_PROG", None), (110.0, 86.0, 90)),
    (("GPIO/TRIG", None), (70.0, 89.0, 90)),
]

# Region (x0, y0, x1, y1) where the remaining parts of each sheet may go.
REGIONS = {
    "front_end1": (2, 2, 50, 45),
    "front_end2": (2, 49, 50, 93),
    "adc1": (40, 30, 72, 66),
    "sample_clock1": (38, 38, 56, 62),
    "fpga1": (62, 22, 120, 93),
    "sdram1": (66, 2, 116, 30),
    "usb_bridge1": (98, 22, 138, 72),
    "usb_input1": (108, 25, 138, 70),
    "power1": (2, 40, 138, 93),
}
DEFAULT_REGION = (2, 2, 138, 93)
MOUNT_HOLES = [(4, 4), (W - 4, 4), (4, H - 4), (W - 4, H - 4)]


def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pn.FootprintLoad(FP_ROOT + lib + ".pretty", name)
    if fp is None:
        raise RuntimeError(f"footprint {fpid} not found")
    return fp


def courtyard(fp, margin=0.5):
    """Footprint courtyard bbox in mm (x0, y0, x1, y1), with margin."""
    cy = fp.GetCourtyard(pn.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (pn.ToMM(bb.GetLeft()) - margin, pn.ToMM(bb.GetTop()) - margin,
            pn.ToMM(bb.GetRight()) + margin, pn.ToMM(bb.GetBottom()) + margin)


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def main(net_path, pcb_path):
    comps, nets = read_netlist(net_path)

    board = pn.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(4)
    ds.SetBoardThickness(MM(1.6))
    # NOTE: marking In1 as a power layer (pn.LT_POWER) keeps Freerouting off
    # the GND plane, but in this run it then left 4 signals and ~19 GND pads
    # unconnected, so In1 stays a signal layer and the plane gets cut.

    # Nets.
    netinfo = {}
    for name in nets:
        ni = pn.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    pin_net = {(r, p): n for n, nodes in nets.items() for (r, p) in nodes}

    # Footprints.
    fps = {}
    for ref, c in sorted(comps.items()):
        fp = load_fp(c["footprint"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        fp.SetFPID(pn.LIB_ID(*c["footprint"].split(":")))
        # Link to schematic symbol: path = sheet tstamps + symbol tstamp.
        if c["ts"]:
            fp.SetPath(pn.KIID_PATH(c["sheet_ts"] + c["ts"]))
        board.Add(fp)
        for pad in fp.Pads():
            n = pin_net.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])
        fps[ref] = fp

    sheet_of = {r: c["sheet"].strip("/").split("/")[-1] if c["sheet"] else ""
                for r, c in comps.items()}

    placed = {}  # ref -> courtyard rect (mm, absolute)
    keepouts = []  # mounting holes etc.
    for x, y in MOUNT_HOLES:
        keepouts.append((x - 3.5, y - 3.5, x + 3.5, y + 3.5))

    def put(ref, x, y, rot):
        fp = fps[ref]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pn.VECTOR2I(MM(x), MM(y)))
        placed[ref] = courtyard(fp)

    # 1. Fixed parts.
    for (key, sheet), spots in FIXED:
        refs = sorted(
            (r for r, c in comps.items()
             if (c["value"] == key or key in c["footprint"])
             and (sheet is None or sheet_of[r] == sheet)),
            key=lambda r: int(re.sub(r"\D", "", r) or 0))
        if not isinstance(spots, list):
            spots = [spots]
        if len(refs) != len(spots):
            print(f"WARNING: {key}/{sheet}: {len(refs)} parts for {len(spots)} spots")
        for r, s in zip(refs, spots):
            put(r, *s)

    # Op-amp roles: the first OPA356 in each front end should be the signal
    # buffer (input on ATT_x); swap if needed.
    for ch, sheet in (("A", "front_end1"), ("B", "front_end2")):
        ops = sorted((r for r in comps if comps[r]["value"] == "OPA356xxDBV"
                      and sheet_of[r] == sheet), key=lambda r: int(r[1:]))
        if len(ops) == 2 and pin_net.get((ops[0], "3")) != f"ATT_{ch}":
            p0, p1 = fps[ops[0]].GetPosition(), fps[ops[1]].GetPosition()
            put(ops[0], pn.ToMM(p1.x), pn.ToMM(p1.y), 0)
            put(ops[1], pn.ToMM(p0.x), pn.ToMM(p0.y), 0)

    big = {r for r in placed if len(fps[r].Pads()) >= 3}
    adc_ref = next(r for r, c in comps.items() if c["value"] == "LTC2290CUP")
    a = placed[adc_ref]
    adc_zone = (a[0] - 3, a[1] - 3, a[2] + 3, a[3] + 3)

    def pads_of_net(net, refs):
        out = []
        for r, p in nets.get(net, []):
            if r in refs:
                for pad in fps[r].Pads():
                    if pad.GetNumber() == p:
                        out.append((r, pad))
        return out

    claimed = {}  # (ref, padnum) -> count, spreads decaps over power pins

    def target_for(ref):
        """Choose the point a free part should sit next to."""
        my_nets = [pin_net.get((ref, pad.GetNumber())) for pad in fps[ref].Pads()]
        my_nets = [n for n in my_nets if n and n != "GND"]
        sheet = sheet_of[ref]
        best = None
        # Prefer the most specific net (fewest nodes) touching a placed part,
        # preferring placed parts in the same sheet.
        for n in sorted(set(my_nets), key=lambda n: len(nets[n])):
            cands = pads_of_net(n, placed.keys())
            if not cands:
                continue
            same = [c for c in cands if sheet_of[c[0]] == sheet]
            cands = same or cands
            cands.sort(key=lambda c: claimed.get((c[0], c[1].GetNumber()), 0))
            r, pad = cands[0]
            claimed[(r, pad.GetNumber())] = claimed.get((r, pad.GetNumber()), 0) + 1
            pp = pad.GetPosition()
            cc = fps[r].GetPosition()
            px, py = pn.ToMM(pp.x), pn.ToMM(pp.y)
            cx, cy = pn.ToMM(cc.x), pn.ToMM(cc.y)
            d = math.hypot(px - cx, py - cy) or 1.0
            push = 2.0 if r in big else 1.0
            best = (px + (px - cx) / d * push, py + (py - cy) / d * push)
            break
        if best is None:
            reg = REGIONS.get(sheet, DEFAULT_REGION)
            best = ((reg[0] + reg[2]) / 2, (reg[1] + reg[3]) / 2)
        return best

    def free_spot(ref, tx, ty):
        fp = fps[ref]
        reg = REGIONS.get(sheet_of[ref], DEFAULT_REGION)
        for region in (reg, DEFAULT_REGION):
            for radius in [i * 0.25 for i in range(0, 240)]:
                n = max(1, int(2 * math.pi * radius / 0.25))
                for k in range(n):
                    a = 2 * math.pi * k / n
                    x = round((tx + radius * math.cos(a)) * 4) / 4
                    y = round((ty + radius * math.sin(a)) * 4) / 4
                    for rot in (0, 90):
                        fp.SetOrientationDegrees(rot)
                        fp.SetPosition(pn.VECTOR2I(MM(x), MM(y)))
                        cr = courtyard(fp)
                        if (cr[0] < region[0] or cr[1] < region[1] or
                                cr[2] > region[2] or cr[3] > region[3]):
                            continue
                        if any(overlaps(cr, o) for o in placed.values()):
                            continue
                        if any(overlaps(cr, o) for o in keepouts):
                            continue
                        # Keep the ADC-output resistor packs back from the
                        # ADC so its 0.5 mm-pitch data pins have escape room.
                        if ref.startswith("RN") and overlaps(cr, adc_zone):
                            continue
                        return x, y, rot
        raise RuntimeError(f"no room for {ref}")

    # 2. Free parts: those touching placed parts first (breadth-first).
    remaining = [r for r in comps if r not in placed]
    while remaining:
        def score(r):
            ns = {pin_net.get((r, p.GetNumber())) for p in fps[r].Pads()} - {"GND", None}
            touching = [n for n in ns if pads_of_net(n, placed.keys())]
            # Specific (small) nets first, then by count of placed neighbours.
            spec = min((len(nets[n]) for n in touching), default=999)
            return (0 if touching else 1, spec, r)
        remaining.sort(key=score)
        ref = remaining.pop(0)
        tx, ty = target_for(ref)
        put(ref, *free_spot(ref, tx, ty))

    # Board outline.
    rect = pn.PCB_SHAPE(board)
    rect.SetShape(pn.SHAPE_T_RECT)
    rect.SetStart(pn.VECTOR2I(0, 0))
    rect.SetEnd(pn.VECTOR2I(MM(W), MM(H)))
    rect.SetLayer(pn.Edge_Cuts)
    rect.SetWidth(MM(0.1))
    board.Add(rect)

    # Mounting holes.
    for i, (x, y) in enumerate(MOUNT_HOLES):
        mh = load_fp("MountingHole:MountingHole_3.2mm_M3")
        mh.SetReference(f"H{i+1}")
        mh.SetValue("MountingHole")
        mh.SetBoardOnly(True)  # not in the schematic
        mh.SetExcludedFromBOM(True)
        mh.SetPosition(pn.VECTOR2I(MM(x), MM(y)))
        board.Add(mh)

    # Solid GND plane on In1.Cu.
    add_zone(board, netinfo["GND"], pn.In1_Cu, 0)

    # Hide fab-irrelevant value text to reduce silkscreen clutter; keep refs
    # small.
    for fp in fps.values():
        fp.Value().SetVisible(False)
        ref = fp.Reference()
        ref.SetTextSize(pn.VECTOR2I(MM(0.8), MM(0.8)))
        ref.SetTextThickness(MM(0.12))

    board.Save(pcb_path)
    print(f"placed {len(fps)} footprints; saved {pcb_path}")


def add_zone(board, net, layer, priority, margin=0.5):
    z = pn.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(net)
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(MM(0.25))
    z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pn.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.3))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((margin, margin), (W - margin, margin), (W - margin, H - margin),
                 (margin, H - margin)):
        ol.Append(MM(x), MM(y))
    board.Add(z)
    return z


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
