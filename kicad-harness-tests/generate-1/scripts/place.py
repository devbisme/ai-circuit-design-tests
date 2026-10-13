"""Placement: hand-placed anchors + FPGA pin swapping + greedy passive placement.

Writes scripts/pinmap.json (FPGA bus pin assignment) and work/placement.json ({ref: [x, y, rot, side]}).
Re-run gen_sch.py after this so the schematic follows the new pin map.
"""
import json
import math
import sys
from pathlib import Path

import design
from fpinfo import info

HERE = Path(__file__).resolve().parent
WORK = HERE.parent / "work"
BOARD = (0.0, 0.0, 120.0, 85.0)
BIGNETS = {"GND"}

ANCHORS = {   # ref: (x, y, rot)  -- footprint origin
    "J2": (12.7, 20, 90), "J3": (12.7, 63, 90),
    "U6": (25.5, 20, 0), "U7": (35, 20, 0),
    "U8": (25.5, 63, 0), "U9": (35, 63, 0),
    "U10": (50, 41, 0),
    "U11": (82, 40, 0),
    "U13": (106.5, 40, 0),
    "U14": (84, 71, 0),
    "U12": (97, 59.5, 0),
    "J1": (102.5, 70, 0),
    "J4": (60, 4, 90),
    "Y1": (44, 54, 0),
    "U2": (50, 70, 0), "U3": (64, 66, 0), "U4": (57, 76, 0), "U5": (24, 78, 0),
    "H1": (4, 4, 0), "H2": (116, 4, 0), "H3": (4, 81, 0), "H4": (116, 81, 0),
}
REGIONS = {   # group: (x0, y0, x1, y1) where its free parts may go
    "FEA": (14, 6, 44, 33), "FEB": (14, 49, 44, 76),
    "ADC": (39, 30, 61, 53), "RN": (55, 28, 70, 55), "OSC": (38, 50, 58, 60),
    "FPGA": (58, 16, 98, 60), "SDRAM": (94, 14, 120, 60), "FLASH": (88, 52, 102, 66),
    "FT": (70, 56, 100, 85), "USBIN": (90, 56, 120, 85),
    "BUCK": (40, 60, 70, 85), "LDO12": (55, 58, 75, 72), "LDO3VA": (48, 70, 68, 85),
    "NEG5": (14, 72, 44, 85), "PWRLED": (80, 2, 110, 12), "LEDS": (80, 2, 110, 14), "PROG": (0, 0, 120, 85),
}


def xf(x, y, rot):
    r = math.radians(rot)
    return x * math.cos(r) + y * math.sin(r), -x * math.sin(r) + y * math.cos(r)


class Fp:
    def __init__(self, part):
        self.part = part
        self.pads, cy = info(part.footprint)
        if cy is None:
            xs = [p[1] for p in self.pads] or [0]
            ys = [p[2] for p in self.pads] or [0]
            cy = (min(xs) - 1, min(ys) - 1, max(xs) + 1, max(ys) + 1)
        self.cy = cy

    def rect(self, x, y, rot, m=0.15):
        pts = [xf(a, b, rot) for a in (self.cy[0], self.cy[2]) for b in (self.cy[1], self.cy[3])]
        return (x + min(p[0] for p in pts) - m, y + min(p[1] for p in pts) - m,
                x + max(p[0] for p in pts) + m, y + max(p[1] for p in pts) + m)

    def padpos(self, x, y, rot):
        out = []
        for num, px, py in self.pads:
            dx, dy = xf(px, py, rot)
            out.append((num, x + dx, y + dy))
        return out


def overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def inside(r, box):
    return r[0] >= box[0] and r[1] >= box[1] and r[2] <= box[2] and r[3] <= box[3]


def assign_fpga_pins(fps, pos):
    """Match each FPGA bus to a contiguous arc of FPGA pins in angular order."""
    from sexp import load_symbol, symbol_pins
    fl = symbol_pins(load_symbol("FPGA_Lattice:ICE40HX4K-TQ144"))
    io = design.fpga_io_pins(fl)
    free = [n for s in "LBRT" for n in io[s]]
    fx, fy, frot = pos["U11"]
    fpga_pad = {n: (x, y) for n, x, y in fps["U11"].padpos(fx, fy, frot)}
    ang = lambda x, y: math.atan2(y - fy, x - fx)

    c = design.build()
    netpads = {}
    for p in c.parts:
        if p.ref in pos and p.ref != "U11":
            pp = {n: (x, y) for n, x, y in fps[p.ref].padpos(*pos[p.ref])}
            for n, net in p.pins.items():
                if net and n in pp:
                    netpads.setdefault(net, []).append(pp[n])

    def far_end(sig):
        # FPGA-side net -> counterpart pad (through the series resistor packs / SD_CLK resistor)
        for cand in (sig, sig + "_S", sig.replace("_S", "")):
            if cand in netpads:
                return netpads[cand][0]
        return None

    pm = {}
    groups = [("ADC", design.ADC_SIGS), ("SD", design.SD_SIGS), ("FT", design.FT_SIGS[:-2])]
    for gname, sigs in groups:
        pts = [(s, far_end(s)) for s in sigs]
        miss = [s for s, p in pts if p is None]
        if miss:
            raise RuntimeError(f"no counterpart for {miss}")
        cx = sum(p[0] for _, p in pts) / len(pts)
        cy_ = sum(p[1] for _, p in pts) / len(pts)
        phi = ang(cx, cy_)
        rel = lambda x, y: (ang(x, y) - phi + math.pi) % (2 * math.pi)   # cut opposite the bus
        pts.sort(key=lambda sp: rel(*sp[1]))
        fr = sorted(free, key=lambda n: rel(*fpga_pad[n]))
        n, best = len(pts), None
        for start in range(len(fr) - n + 1):
            sel = fr[start:start + n]
            cost = 0.0
            for (s, p), pin in zip(pts, sel):
                d = abs(ang(*p) - ang(*fpga_pad[pin]))
                cost += min(d, 2 * math.pi - d)
            if best is None or cost < best[0]:
                best = (cost, sel)
        for (s, p), pin in zip(pts, best[1]):
            pm[s] = pin
            free.remove(pin)
    # LEDs: any pins nearest the top edge (LED region)
    free.sort(key=lambda n: fpga_pad[n][1])
    pm["LED0"], pm["LED1"] = free[0], free[1]
    return pm


def main():
    c = design.build()
    fps = {p.ref: Fp(p) for p in c.parts if p.footprint}
    pos = {r: v for r, v in ANCHORS.items()}
    pm = assign_fpga_pins(fps, pos)
    (HERE / "pinmap.json").write_text(json.dumps(pm, indent=1))
    c = design.build()          # rebuild with the new pin map
    parts = {p.ref: p for p in c.parts if p.footprint}
    rects = [fps[r].rect(*pos[r]) for r in pos]
    padxy = {}               # net -> list of (x, y) of placed pads

    def add_pads(ref):
        for n, x, y in fps[ref].padpos(*pos[ref]):
            net = parts[ref].pins.get(n)
            if net and net not in BIGNETS:
                padxy.setdefault(net, []).append((x, y, ref))
    for r in pos:
        add_pads(r)

    claimed = set()
    todo = [r for r in parts if r not in pos]
    anchors_by_group = {}
    for r in pos:
        anchors_by_group.setdefault(parts[r].group, []).append(r)

    def nconn(ref):
        return sum(1 for net in parts[ref].pins.values() if net in padxy)

    while todo:
        todo.sort(key=lambda r: -nconn(r))
        ref = todo.pop(0)
        p, fp = parts[ref], fps[ref]
        region = REGIONS.get(p.group, BOARD)
        nets = {n: net for n, net in p.pins.items() if net and net not in BIGNETS}
        # decap-like part: one non-GND net that is a power rail -> claim a nearby IC pin of that rail
        targets = {}
        for n, net in nets.items():
            cands = [(x, y, r) for x, y, r in padxy.get(net, []) if r != ref]
            if net.startswith(("+", "-", "VCC", "FT_V", "OSC_VDD")) and len(nets) == 1:
                own = [(x, y, r) for x, y, r in cands if r in anchors_by_group.get(p.group, []) and (x, y) not in claimed]
                if own:
                    cands = own
            targets[n] = cands
        allc = [xy for v in targets.values() for xy in v]
        if allc:
            tx = sum(a[0] for a in allc) / len(allc)
            ty = sum(a[1] for a in allc) / len(allc)
        else:
            tx, ty = (region[0] + region[2]) / 2, (region[1] + region[3]) / 2
        best = None
        for radius_lim in (8, 16, 40, 200):
            step = 0.5
            k = int(radius_lim / step)
            for i in range(-k, k + 1):
                for j in range(-k, k + 1):
                    x, y = round(tx + i * step, 2), round(ty + j * step, 2)
                    if (x - tx) ** 2 + (y - ty) ** 2 > radius_lim ** 2:
                        continue
                    for rot in (0, 90, 180, 270):
                        rr = fp.rect(x, y, rot)
                        if not inside(rr, region) or not inside(rr, BOARD):
                            continue
                        if any(overlap(rr, o) for o in rects):
                            continue
                        cost = 0.0
                        for n, px, py in fp.padpos(x, y, rot):
                            cs = targets.get(n)
                            if cs:
                                cost += min(math.hypot(px - a[0], py - a[1]) for a in cs)
                        cost += 0.05 * math.hypot(x - tx, y - ty)
                        if best is None or cost < best[0]:
                            best = (cost, x, y, rot)
            if best:
                break
            if radius_lim == 40:
                region = BOARD
        if not best:
            print("COULD NOT PLACE", ref)
            continue
        _, x, y, rot = best
        pos[ref] = (x, y, rot)
        rects.append(fp.rect(x, y, rot))
        # mark claimed IC pad for decaps
        for n, px, py in fp.padpos(x, y, rot):
            cs = targets.get(n)
            if cs and len(nets) == 1:
                a = min(cs, key=lambda a: math.hypot(px - a[0], py - a[1]))
                claimed.add((a[0], a[1]))
        add_pads(ref)
    out = {r: [v[0], v[1], v[2], "F"] for r, v in pos.items()}
    (WORK / "placement.json").write_text(json.dumps(out, indent=0))
    print("placed", len(out), "parts")


if __name__ == "__main__":
    main()
