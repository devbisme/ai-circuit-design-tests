"""KiCad 10 python: iteratively remove unlocked dead-end track spurs and orphan vias.

A track end is 'free' if no pad (HitTest on that layer), via, or other track end/body of the same
net touches it. Works on a snapshot (KiCad 10 SWIG breaks iteration after Remove()); removes at the end.
usage: python3.11 prune.py <board.kicad_pcb>
"""
import sys

import pcbnew

BRD = sys.argv[1]
PRO = BRD.replace(".kicad_pcb", ".kicad_pro")
pro_text = open(PRO).read()
b = pcbnew.LoadBoard(BRD)
TR = list(b.GetTracks())
PADS = [p for f in b.GetFootprints() for p in f.Pads()]
TOL = 2000   # nm


def seg_touch(t, pt):
    s, e = t.GetStart(), t.GetEnd()
    dx, dy = e.x - s.x, e.y - s.y
    L2 = dx * dx + dy * dy
    u = 0 if L2 == 0 else max(0, min(1, ((pt.x - s.x) * dx + (pt.y - s.y) * dy) / L2))
    cx, cy = s.x + u * dx, s.y + u * dy
    return ((pt.x - cx) ** 2 + (pt.y - cy) ** 2) ** 0.5 <= t.GetWidth() / 2 + TOL


def connected(item, pt, layer, alive):
    net = item.GetNetCode()
    for p in PADS:
        if p.GetNetCode() == net and p.IsOnLayer(layer) and p.HitTest(pt):
            return True
    for o in alive:
        if o is item or o.GetNetCode() != net:
            continue
        if o.GetClass() == "PCB_VIA":
            c = o.GetPosition()
            if ((c.x - pt.x) ** 2 + (c.y - pt.y) ** 2) ** 0.5 <= o.GetWidth(pcbnew.F_Cu) / 2 + TOL:
                return True
        elif o.GetLayer() == layer and seg_touch(o, pt):
            return True
    return False


alive = list(TR)
removed = []
while True:
    dead = []
    for t in alive:
        if t.IsLocked():
            continue
        if t.GetClass() == "PCB_VIA":
            pt = t.GetPosition()
            n = sum(1 for o in alive if o is not t and o.GetClass() != "PCB_VIA" and o.GetNetCode() == t.GetNetCode()
                    and seg_touch(o, pt))
            pads = any(p.GetNetCode() == t.GetNetCode() and p.HitTest(pt) for p in PADS)
            zones = t.GetNetname() in ("GND", "+3V3")
            if n == 0 and not pads and not zones:
                dead.append(t)
            continue
        L = t.GetLayer()
        if not connected(t, t.GetStart(), L, alive) or not connected(t, t.GetEnd(), L, alive):
            dead.append(t)
    if not dead:
        break
    removed += dead
    alive = [t for t in alive if not any(t is d for d in dead)]
for t in removed:
    b.Remove(t)
print("pruned", len(removed), "items:", sorted({t.GetNetname() for t in removed}))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(BRD)
open(PRO, "w").write(pro_text)
