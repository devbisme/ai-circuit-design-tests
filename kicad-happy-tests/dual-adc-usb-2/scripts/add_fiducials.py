"""Add 3 board-only fiducials per assembled side (F.Cu and B.Cu) near three board corners,
each at the nearest free spot. usage: python3.11 add_fiducials.py board.kicad_pcb"""
import math
import sys

import pcbnew

MM = pcbnew.FromMM
LIB = "/home/devb/bin/kicad10-root/share/kicad/footprints/Fiducial.pretty"
b = pcbnew.LoadBoard(sys.argv[1])
for fp in list(b.GetFootprints()):
    if fp.GetReference().startswith("FID"):
        b.Remove(fp)
bb = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = [pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom())]


def rect(r):
    return (pcbnew.ToMM(r.GetLeft()), pcbnew.ToMM(r.GetTop()), pcbnew.ToMM(r.GetRight()), pcbnew.ToMM(r.GetBottom()))


def obstacles(layer, crtyd):
    obs = []
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(layer):
                obs.append(rect(p.GetBoundingBox()))
        # (GetCourtyard(B_CrtYd) segfaults in KiCad 10 python; use the footprint bbox per side)
        if fp.IsFlipped() == (layer == pcbnew.B_Cu):
            obs.append(rect(fp.GetBoundingBox(False)))
    for t in b.GetTracks():
        if t.IsOnLayer(layer):
            obs.append(rect(t.GetBoundingBox()))
    return obs


n = 0
for layer, crtyd, flip in ((pcbnew.F_Cu, pcbnew.F_CrtYd, False), (pcbnew.B_Cu, pcbnew.B_CrtYd, True)):
    obs = obstacles(layer, crtyd)

    def free(x, y, r=1.6):
        if x - r < x0 + 1 or x + r > x1 - 1 or y - r < y0 + 1 or y + r > y1 - 1:
            return False
        return all(x + r < a or x - r > c or y + r < d0 or y - r > d1 for a, d0, c, d1 in obs)

    for cx, cy in ((x0 + 9, y0 + 4), (x1 - 9, y0 + 4), (x0 + 9, y1 - 4)):
        spot = None
        for rad in [k * 0.25 for k in range(0, 80)]:
            for a in range(0, 360, 15):
                x, y = cx + rad * math.cos(math.radians(a)), cy + rad * math.sin(math.radians(a))
                if free(x, y):
                    spot = (x, y)
                    break
            if spot:
                break
        n += 1
        fp = pcbnew.FootprintLoad(LIB, "Fiducial_1mm_Mask2mm")
        fp.SetFPID(pcbnew.LIB_ID("Fiducial", "Fiducial_1mm_Mask2mm"))
        fp.SetReference(f"FID{n}")
        fp.SetValue("Fiducial")
        fp.SetBoardOnly(True)
        fp.SetPosition(pcbnew.VECTOR2I(MM(spot[0]), MM(spot[1])))
        b.Add(fp)  # must be on the board before Flip() (segfaults otherwise)
        if flip:
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        obs.append((spot[0] - 1.6, spot[1] - 1.6, spot[0] + 1.6, spot[1] + 1.6))
        print(f"FID{n} {'B' if flip else 'F'} at {spot[0]:.2f},{spot[1]:.2f}")
b.Save(sys.argv[1])
