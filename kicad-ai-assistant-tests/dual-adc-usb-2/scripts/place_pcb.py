"""Plan footprint placement and apply it with kcaa tools (move_footprints_by_delta,
flip_footprint, set_footprint_position).

Board: 128 x 85 mm, origin (100, 100).  Signal flow left -> right:
BNC -> front end -> ADC -> FPGA -> SDRAM; FT232H + USB-B below the FPGA; power bottom-left.
Decoupling caps of the four big ICs go on B.Cu under/around their IC; everything else on
F.Cu, kept out of a 2.5 mm escape band around the big ICs (lesson from earlier runs).
"""
import json, math, os, sys
import kcaa_call
from design import PARTS, POWER_NETS

PROJ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PCB = os.path.join(PROJ, "dual_adc.kicad_pcb")
G = json.load(open(os.path.join(os.path.dirname(__file__), "fpgeom.json")))
BX0, BY0, BW, BH = 100.0, 100.0, 128.0, 85.0
BIG = {"U20": 1.0, "U30": 4.0, "U40": 2.5, "U50": 2.0}   # IC -> inward offset for B.Cu caps
ESCAPE = 2.5
CLR = 0.3

ANCHORS = {   # ref: (x, y, rot)
    "J2": (112.7, 117.0, 90), "J3": (112.7, 152.0, 90),
    "U20": (168.0, 134.5, 0), "U30": (194.0, 134.5, 0), "U40": (220.0, 134.5, 0),
    "U50": (194.0, 163.0, 180), "J1": (209.0, 170.0, 270), "J4": (222.0, 152.0, 0),
    "X1": (163.5, 146.5, 0), "X2": (207.0, 118.0, 0), "U51": (184.0, 166.0, 0),
    "H1": (103.5, 103.5, 0), "H2": (224.5, 103.5, 0), "H3": (103.5, 181.5, 0),
    "H4": (224.5, 181.5, 0),
}
# front-end template, channel origin (119, yc); roles keyed by channel-A refs
FE = {"R10": (3, -2.2, 0), "C100": (3, 1.0, 0), "R11": (8, 4.5, 90), "C101": (10, 4.5, 90),
      "C102": (9, 9, 0), "D2": (9, -4.5, 0), "R12": (13, 0, 0), "U10": (18, 0, 0),
      "C103": (18, -3.6, 0), "C104": (18, 3.6, 0), "R13": (22.5, 0, 0), "C107": (25.5, 2.5, 90),
      "R14": (28, -4.2, 0), "R15": (27.5, -1.6, 0), "R18": (27.5, 1.6, 0), "R17": (28, 4.2, 0),
      "R16": (22.5, 4.5, 0), "U12": (33, 0, 0), "C105": (32.5, -4.2, 0), "C106": (32.5, 4.2, 0),
      "C108": (36.5, -4.2, 0), "C109": (36.5, 4.2, 0), "R19": (38, -1.2, 0),
      "R20": (38, 1.2, 0), "C110": (41, 0, 90)}


def chB(ref):
    """map a channel-A front-end ref to channel B"""
    p, n = ref[0], int(ref[1:])
    if p == "R":
        return f"R{n + 20}"
    if p == "C":
        return f"C{n + 20}"
    return {"D2": "D3", "U10": "U11", "U12": "U13"}[ref]


def rot_pt(x, y, rot):
    """rotate a footprint-local point; KiCad CCW-positive with +Y down"""
    r = math.radians(rot)
    return (x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r))


def rect(ref, x, y, rot, side):
    x0, y0, x1, y1 = G[ref]["bbox"]
    if side == "B":
        x0, x1 = -x1, -x0
    pts = [rot_pt(a, b, rot) for a in (x0, x1) for b in (y0, y1)]
    return (x + min(p[0] for p in pts), y + min(p[1] for p in pts),
            x + max(p[0] for p in pts), y + max(p[1] for p in pts))


def overlap(a, b, c=CLR):
    return not (a[2] + c <= b[0] or b[2] + c <= a[0] or a[3] + c <= b[1] or b[3] + c <= a[1])


PLACED = {}            # ref -> (x, y, rot, side)
OCC = {"F": [], "B": []}


def put(ref, x, y, rot=0, side="F"):
    PLACED[ref] = (round(x, 2), round(y, 2), rot, side)
    OCC[side].append((ref, rect(ref, x, y, rot, side)))
    if side == "F" and ref in BIG:   # escape band for top-side parts
        r = rect(ref, x, y, rot, side)
        OCC["F"].append((ref + "_esc", (r[0] - ESCAPE, r[1] - ESCAPE, r[2] + ESCAPE,
                                        r[3] + ESCAPE)))


def pad_world(ref, num):
    x, y, rot, side = PLACED[ref]
    for p in G[ref]["pads"]:
        if p["num"] == num:
            px = -p["x"] if side == "B" else p["x"]
            dx, dy = rot_pt(px, p["y"], rot)
            return x + dx, y + dy
    return None


def free(ref, tx, ty, side, rot=0, inside=None):
    """spiral search for a non-overlapping spot near (tx, ty)"""
    for rad in [i * 0.25 for i in range(0, 160)]:
        n = max(1, int(2 * math.pi * rad / 0.5))
        for k in range(n):
            a = 2 * math.pi * k / n
            x, y = round(tx + rad * math.cos(a), 2), round(ty + rad * math.sin(a), 2)
            r = rect(ref, x, y, rot, side)
            if r[0] < BX0 + 0.5 or r[2] > BX0 + BW - 0.5 or r[1] < BY0 + 0.5 or \
                    r[3] > BY0 + BH - 0.5:
                continue
            if inside and not (inside[0] <= x <= inside[2] and inside[1] <= y <= inside[3]):
                continue
            if any(overlap(r, o) for _, o in OCC[side]):
                continue
            return x, y
    raise RuntimeError(f"no room for {ref}")


def main_plan():
    for ref, (x, y, rot) in ANCHORS.items():
        put(ref, x, y, rot)
    for yc, mapper in ((117.0, lambda r: r), (152.0, chB)):
        for ref, (dx, dy, rot) in FE.items():
            put(mapper(ref), 119 + dx, yc + dy, rot)
    rest = [r for r in PARTS if r not in PLACED]
    sheet_order = {"adc": 0, "fpga": 1, "sdram": 2, "usb": 3, "power": 4, "frontend": 5}
    rest.sort(key=lambda r: (sheet_order[PARTS[r]["sheet"]], -len(PARTS[r]["pins"]), r))
    parent = {"adc": "U20", "fpga": "U30", "sdram": "U40", "usb": "U50"}
    big_power = {n for n, v in POWER_NETS.items()}
    for ref in rest:
        p = PARTS[ref]
        nets = set(p["pins"].values()) - {"NC"}
        par = parent.get(p["sheet"])
        side = "F"
        target = None
        if par and p["sym"] == "C" and (nets - {"GND"}) and all(
                n == "GND" or n in PARTS[par]["pins"].values() for n in nets):
            # decoupling/bypass cap -> B.Cu at its IC pin, pulled toward the IC centre
            side = "B"
            sig = sorted(nets - {"GND"})[0]
            cands = [k for k, v in PARTS[par]["pins"].items() if v == sig]
            used = USED_PINS.setdefault((par, sig), [])
            pin = next((c for c in cands if c not in used), cands[len(used) % len(cands)])
            used.append(pin)
            px, py = pad_world(par, pin)
            cx, cy = PLACED[par][0], PLACED[par][1]
            d = math.hypot(px - cx, py - cy) or 1
            k = BIG[par]
            target = (px + (cx - px) / d * k, py + (cy - py) / d * k)
        else:
            pts = []
            for n in nets:
                if len(NETS.get(n, [])) > 6:
                    continue
                for (r2, pin2) in NETS.get(n, []):
                    if r2 in PLACED and r2 != ref:
                        pts.append(pad_world(r2, pin2))
            pts = [q for q in pts if q]
            if not pts:
                pts = [ZONE.get(p["sheet"], (140.0, 175.0))]
            target = (sum(q[0] for q in pts) / len(pts), sum(q[1] for q in pts) / len(pts))
        x, y = free(ref, target[0], target[1], side)
        put(ref, x, y, 0, side)
    return PLACED


USED_PINS = {}
ZONE = {"power": (160.0, 177.0)}
from design import nets as _nets
NETS = _nets()


def apply():
    call = kcaa_call.call
    refs = list(PARTS)
    print(call("move_footprints_by_delta", pcb_path=PCB, references=refs, dx=400.0, dy=0.0)
          .get("success"))
    flips = [r for r, v in PLACED.items() if v[3] == "B"]
    for r in flips:
        res = call("flip_footprint", pcb_path=PCB, reference=r)
        if not res.get("success"):
            print("flip fail", r, res)
    items = [{"reference": r, "x": v[0], "y": v[1], "rotation": float(v[2])}
             for r, v in PLACED.items()]
    res = call("set_footprint_position", pcb_path=PCB, items=items)
    adj = [x for x in res.get("results", []) if x.get("position_adjusted") or x.get("error")]
    print("placed", len(items), "flipped", len(flips), "adjusted/errors", len(adj))
    for a in adj[:20]:
        print("  ", json.dumps(a)[:200])
    json.dump(PLACED, open(os.path.join(os.path.dirname(__file__), "placement.json"), "w"),
              indent=0)


if __name__ == "__main__":
    main_plan()
    print(f"planned {len(PLACED)} parts, B side: {sum(1 for v in PLACED.values() if v[3]=='B')}")
    if "--apply" in sys.argv:
        apply()
