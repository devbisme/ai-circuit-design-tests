"""Final copper cleanup (KiCad python): zero-length tracks, dangling vias,
the duplicate CLK10 via left by fix_unrouted.py, and nudging R5 clear of C9
(dragging the track ends attached to its pads)."""
import math
import os

import pcbnew

PCB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad", "dual_adc.kicad_pcb")
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in b.GetFootprints()}


def near(v, x, y, tol=0.02):
    return math.hypot(v.x / 1e6 - x, v.y / 1e6 - y) < tol


# R5 vs C9 courtyard overlap.
cy = lambda f: f.GetCourtyard(pcbnew.F_CrtYd).BBox()
ov = cy(fps["C9"]).GetRight() - cy(fps["R5"]).GetLeft()
if ov > -mm(0.05):
    d = ov + mm(0.1)
    centers = [p.GetPosition() for p in fps["R5"].Pads()]
    for t in b.Tracks():
        if t.GetClass() == "PCB_VIA":
            continue
        for get, put in ((t.GetStart, t.SetStart), (t.GetEnd, t.SetEnd)):
            v = get()
            if any(v.x == c.x and v.y == c.y for c in centers):
                put(pcbnew.VECTOR2I(v.x + d, v.y))
    p = fps["R5"].GetPosition()
    fps["R5"].SetPosition(pcbnew.VECTOR2I(p.x + d, p.y))
    print("moved R5 by", d / 1e6)

drop = []
for t in b.Tracks():
    if t.GetClass() != "PCB_VIA" and t.GetLength() == 0:
        drop.append(t)
    elif t.GetNetname() == "+5V" and (
            (t.GetClass() == "PCB_VIA" and near(t.GetPosition(), 64.0467, 111.2187)) or
            (t.GetClass() != "PCB_VIA" and (near(t.GetStart(), 64.0467, 111.2187) or
                                             near(t.GetEnd(), 64.0467, 111.2187)))):
        drop.append(t)      # rip-up leftover: via + 26.8 mm stub to nowhere
    elif t.GetClass() == "PCB_VIA" and t.GetNetname() == "CLK10" and near(t.GetPosition(), 81.7134, 80.9033):
        drop.append(t)
        # keep continuity on both layers to the Freerouting via beside it
        for L in (pcbnew.F_Cu, pcbnew.B_Cu):
            s = pcbnew.PCB_TRACK(b)
            s.SetStart(t.GetPosition()); s.SetEnd(pcbnew.VECTOR2I(mm(81.6134), mm(80.8033)))
            s.SetWidth(mm(0.2)); s.SetLayer(L); s.SetNet(t.GetNet()); b.Add(s)
for t in drop:
    b.Remove(t)
print("removed", len(drop))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(PCB)
