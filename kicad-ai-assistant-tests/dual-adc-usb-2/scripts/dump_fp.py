"""Dump footprint geometry (rotation 0, front side) to JSON.  Run with KiCad 10 python."""
import json, sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
out = {}
for f in b.GetFootprints():
    ref = f.GetReference()
    f.SetOrientationDegrees(0)
    pos = f.GetPosition()
    pads = [dict(num=p.GetNumber(), x=(p.GetPosition().x - pos.x) / 1e6,
                 y=(p.GetPosition().y - pos.y) / 1e6, net=p.GetNetname())
            for p in f.Pads()]
    cy = f.GetCourtyard(pcbnew.F_CrtYd)
    if cy.OutlineCount():
        bb = cy.BBox()
    else:
        bb = f.GetBoundingBox(False)
    out[ref] = dict(fpid=str(f.GetFPID().GetLibItemName()), pads=pads,
                    bbox=[(bb.GetLeft() - pos.x) / 1e6, (bb.GetTop() - pos.y) / 1e6,
                          (bb.GetRight() - pos.x) / 1e6, (bb.GetBottom() - pos.y) / 1e6])
json.dump(out, open(sys.argv[2], "w"), indent=0)
print(len(out))
