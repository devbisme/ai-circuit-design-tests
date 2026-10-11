"""Plane zones + locked plane fanout + Specctra DSN for Freerouting (KiCad python).

Freerouting does not connect pads through inner-layer planes, so every SMD pad
on a plane net (GND on In1; +3V3 / +3V3A on In2) gets a locked via + stub here.
The DSN handed to Freerouting keeps only the plane-net pads that could not be
fanned out (plus one fanned-out anchor), and marks the inner layers as power
layers so signals stay on F.Cu/B.Cu.

usage: python3.11 route_prep.py   (reads/writes kicad/dual_adc.kicad_pcb,
                                    writes route/dual_adc.dsn)
"""

import math
import os
import re
from collections import defaultdict

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PCB = os.path.join(ROOT, "kicad", "dual_adc.kicad_pcb")
RDIR = os.path.join(ROOT, "route")
os.makedirs(RDIR, exist_ok=True)
mm = pcbnew.FromMM
OX, OY, BW, BH = 40.0, 40.0, 125.0, 95.0

VIA_D, VIA_DRILL, STUB_W, CLR = 0.45, 0.2, 0.2, 0.15
POWER_CLASS = ["+5V", "VBUS", "VBUS_F", "+1V2", "+4V", "-4V", "LM_CP",
               "LM_CPF", "LM_CN", "FT_VPHY", "VCCPLL0", "VCCPLL1", "OSC_VDD",
               "FT_VCCA", "FT_VCORE"]
# Plane regions (board-relative mm): +3V3A island on In2; the rest of In2 is +3V3.
A_RECT = (17.0, 8.0, 54.5, 78.0)

board = pcbnew.LoadBoard(os.path.join(RDIR, "placed.kicad_pcb"))
nets = board.GetNetsByName()


def N(name):
    return nets[pcbnew.wxString(name)] if hasattr(pcbnew, "wxString") else nets[name]


def get_net(name):
    for k, v in board.GetNetsByName().items():
        if str(k) == name:
            return v
    raise KeyError(name)


def V(x, y):
    return pcbnew.VECTOR2I(mm(x), mm(y))


# ---------------------------------------------------------------- zones ----


def add_zone(net, layer, rect, priority, name):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(get_net(net))
    z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    x0, y0, x1, y1 = rect
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        o.Append(mm(OX + x), mm(OY + y))
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    board.Add(z)
    return z


FULL = (0.3, 0.3, BW - 0.3, BH - 0.3)
add_zone("GND", pcbnew.In1_Cu, FULL, 0, "GND_plane")
add_zone("+3V3", pcbnew.In2_Cu, FULL, 0, "3V3_plane")
add_zone("+3V3A", pcbnew.In2_Cu, A_RECT, 1, "3V3A_island")


def in_region(net, x, y, m=0.6):
    rx, ry = x - OX, y - OY
    inside_a = A_RECT[0] + m < rx < A_RECT[2] - m and A_RECT[1] + m < ry < A_RECT[3] - m
    near_a = A_RECT[0] - 1.0 < rx < A_RECT[2] + 1.0 and A_RECT[1] - 1.0 < ry < A_RECT[3] + 1.0
    on_board = 1.0 < rx < BW - 1.0 and 1.0 < ry < BH - 1.0
    if net == "GND":
        return on_board
    if net == "+3V3A":
        return inside_a
    if net == "+3V3":
        return on_board and not near_a
    return False


# ------------------------------------------------------------ obstacles ----
pads = []                 # (x0, y0, x1, y1, netname, layers_set, pad)
for fp in board.GetFootprints():
    for p in fp.Pads():
        if not p.IsOnCopperLayer():
            continue
        bb = p.GetBoundingBox()
        pads.append((bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6,
                     bb.GetBottom() / 1e6, p.GetNetname(), p.GetAttribute(), p))
BUCKET = 2.0
grid = defaultdict(list)
for rec in pads:
    for i in range(int(rec[0] // BUCKET) - 1, int(rec[2] // BUCKET) + 2):
        for j in range(int(rec[1] // BUCKET) - 1, int(rec[3] // BUCKET) + 2):
            grid[(i, j)].append(rec)
vias = []                 # (x, y, net)
stubs = []                # (x0, y0, x1, y1, net)


def rect_dist(x, y, r):
    dx = max(r[0] - x, 0, x - r[2])
    dy = max(r[1] - y, 0, y - r[3])
    return math.hypot(dx, dy)


def seg_pt_dist(px, py, x0, y0, x1, y1):
    vx, vy = x1 - x0, y1 - y0
    L = vx * vx + vy * vy
    t = 0 if L == 0 else max(0, min(1, ((px - x0) * vx + (py - y0) * vy) / L))
    return math.hypot(px - (x0 + t * vx), py - (y0 + t * vy))


def clear(points, radius, net, own_pad, via_xy=None):
    """points: samples along the stub/via; radius: copper half-width."""
    for (x, y) in points:
        for rec in grid[(int(x // BUCKET), int(y // BUCKET))]:
            if rec[6] is own_pad:
                continue
            same = rec[4] == net and net != ""
            d = rect_dist(x, y, rec)
            if not same and d < radius + CLR:
                return False
            if same and via_xy is not None and (x, y) == via_xy and d < radius + 0.05:
                return False      # no via in a neighbouring same-net pad
    vx, vy = via_xy
    for (x, y, n) in vias:
        if math.hypot(x - vx, y - vy) < VIA_D + 0.2:
            return False
    for (x0, y0, x1, y1, n) in stubs:
        if n != net:
            for (x, y) in points:
                if seg_pt_dist(x, y, x0, y0, x1, y1) < radius + STUB_W / 2 + CLR:
                    return False
    return True


def add_via(x, y, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(V(x, y))
    v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    v.SetWidth(mm(VIA_D))
    v.SetDrill(mm(VIA_DRILL))
    v.SetNet(get_net(net))
    v.SetLocked(True)
    board.Add(v)
    vias.append((x, y, net))


def add_stub(x0, y0, x1, y1, net):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(V(x0, y0))
    t.SetEnd(V(x1, y1))
    t.SetWidth(mm(STUB_W))
    t.SetLayer(pcbnew.F_Cu)
    t.SetNet(get_net(net))
    t.SetLocked(True)
    board.Add(t)
    stubs.append((x0, y0, x1, y1, net))


PLANE = ("GND", "+3V3", "+3V3A")
fanned = defaultdict(set)     # net -> {(ref, pad)}
failed = defaultdict(list)

# Through-hole pads on plane nets reach the planes directly.
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() in ("GND", "+3V3", "+3V3A") and \
           p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH and \
           in_region(p.GetNetname(), p.GetPosition().x / 1e6, p.GetPosition().y / 1e6, m=0.0):
            fanned[p.GetNetname()].add((fp.GetReference(), p.GetNumber()))

# Exposed pads: 3x3 via array in the pad.
for fp in board.GetFootprints():
    for p in fp.Pads():
        if p.GetNetname() == "GND" and p.IsOnCopperLayer() and \
           p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD and p.GetSize().x > mm(2.0) and \
           p.GetSize().y > mm(1.0):
            c = p.GetPosition()
            sx, sy = p.GetSize().x / 1e6, p.GetSize().y / 1e6
            nx, ny = (3 if sx > 2.5 else 1), (3 if sy > 2.5 else 2)
            for i in range(nx):
                for j in range(ny):
                    x = c.x / 1e6 + (i - (nx - 1) / 2) * min(1.6, sx / (nx + 0.5))
                    y = c.y / 1e6 + (j - (ny - 1) / 2) * min(1.6, sy / (ny + 0.5))
                    add_via(x, y, "GND")
            fanned["GND"].add((fp.GetReference(), p.GetNumber()))

for fp in board.GetFootprints():
    fc = fp.GetPosition()
    fcx, fcy = fc.x / 1e6, fc.y / 1e6
    for p in fp.Pads():
        net = p.GetNetname()
        if net not in PLANE or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or \
           not p.IsOnLayer(pcbnew.F_Cu) or not p.GetNumber():
            continue
        key = (fp.GetReference(), p.GetNumber())
        if key in fanned[net]:
            continue
        c = p.GetPosition()
        px, py = c.x / 1e6, c.y / 1e6
        bb = p.GetBoundingBox()
        hw, hh = bb.GetWidth() / 2e6, bb.GetHeight() / 2e6
        dx, dy = px - fcx, py - fcy
        dirs = []
        if abs(dx) >= abs(dy) and dx != 0:
            dirs.append((math.copysign(1, dx), 0))
        if abs(dy) >= abs(dx) and dy != 0:
            dirs.append((0, math.copysign(1, dy)))
        dirs += [d for d in ((1, 0), (-1, 0), (0, 1), (0, -1)) if d not in dirs]
        done = False
        for d in dirs:
            ext = hw if d[0] else hh
            for k in range(6):
                dist = ext + CLR + VIA_D / 2 + 0.05 + k * 0.3
                for lat in (0, 0.5, -0.5, 1.0, -1.0):
                    vx = px + d[0] * dist + (lat if d[1] else 0)
                    vy = py + d[1] * dist + (lat if d[0] else 0)
                    if not in_region(net, vx, vy):
                        continue
                    pts = [(vx, vy)]
                    # Stub from pad centre to via, sampled.
                    for s in range(1, 6):
                        f = s / 6
                        pts.append((px + (vx - px) * f, py + (vy - py) * f))
                    if clear(pts[:1], VIA_D / 2, net, p, via_xy=(vx, vy)) and \
                       clear(pts[1:], STUB_W / 2, net, p, via_xy=(vx, vy)):
                        add_stub(px, py, vx, vy, net)
                        add_via(vx, vy, net)
                        fanned[net].add(key)
                        done = True
                        break
                if done:
                    break
            if done:
                break
        if not done:
            failed[net].append(key)

for n in PLANE:
    print(f"{n}: fanned {len(fanned[n])}, left for router {len(failed[n])} {failed[n][:12]}")

board.Save(PCB)

# ---------------------------------------------------------- DSN export ----
dsn = os.path.join(RDIR, "dual_adc_full.dsn")
scratch = os.path.join(RDIR, "scratch.kicad_pcb")
board.Save(scratch)
b2 = pcbnew.LoadBoard(scratch)
ok = pcbnew.ExportSpecctraDSN(b2, dsn)
print("DSN export", ok)
txt = open(dsn).read()

# Inner layers are already LT_POWER (exported as (type power)), so signals stay
# on F.Cu / B.Cu. Use only the small via, and 0.15 mm clearance.
txt = txt.replace('(via "Via[0-3]_600:300_um" "Via[0-3]_450:200_um")', '(via "Via[0-3]_450:200_um")')
txt = txt.replace('(use_via "Via[0-3]_600:300_um")', '(use_via "Via[0-3]_450:200_um")')
txt = re.sub(r"\(clearance 200\)", "(clearance 150)", txt)
# Plane polygons crash Freerouting 2.4.1 (NPE in ConductionArea) and it does not
# use them for connectivity anyway: drop them.
txt = re.sub(r"\n\s*\(plane [^\n]*\n[^\n]*\)\)", "", txt)


# Plane nets: drop fanned-out pins (keep one anchor if unfanned pins remain).
def fix_net(m):
    name = m.group(1).strip('"')
    if name not in PLANE:
        return m.group(0)
    pins = m.group(2).split()
    keep = [q for q in pins if tuple(q.split("@")[0].rsplit("-", 1)) not in fanned[name]]
    anchors = [q for q in pins if q not in keep]
    if keep and anchors:
        keep.append(anchors[0])
    if not keep:
        keep = anchors[:1]
    return f'(net {m.group(1)}\n      (pins {" ".join(keep)})'


txt = re.sub(r'\(net ("[^"]*"|\S+)\s*\(pins ([^)]*)\)', fix_net, txt)

# Power class: wider tracks. Move those nets out of kicad_default.
m = re.search(r"\(class kicad_default(.*?)\(circuit", txt, re.S)
names = [n for n in m.group(1).split() if n.strip('"') not in POWER_CLASS]
default = "(class kicad_default " + " ".join(names) + "\n      (circuit"
plist = " ".join(f'"{n}"' if re.search(r"[^\w]", n) else n for n in POWER_CLASS)
power_class = (f'(class Power {plist}\n      (circuit\n        (use_via "Via[0-3]_450:200_um")\n      )\n'
               f'      (rule\n        (width 400)\n        (clearance 150)\n      )\n    )\n    ')
txt = txt[:m.start()] + power_class + default + txt[m.end():]
out = os.path.join(RDIR, "dual_adc.dsn")
open(out, "w").write(txt)
print("wrote", out)
