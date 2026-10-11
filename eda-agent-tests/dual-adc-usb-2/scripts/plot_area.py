"""Plot copper (pads/tracks/vias) in a board window to PNG for inspection.
usage: python3.11 plot_area.py x0 y0 x1 y1 out.png   (page mm)"""
import json, subprocess, sys, os
import pcbnew
x0, y0, x1, y1 = map(float, sys.argv[1:5])
b = pcbnew.LoadBoard(os.path.join(os.path.dirname(__file__), "..", "kicad", "dual_adc.kicad_pcb"))
items = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        r = [bb.GetLeft()/1e6, bb.GetTop()/1e6, bb.GetRight()/1e6, bb.GetBottom()/1e6]
        if r[2] > x0 and r[0] < x1 and r[3] > y0 and r[1] < y1:
            items.append(["pad", r, p.GetNetname(), fp.GetReference() + "." + p.GetNumber(), p.IsOnLayer(pcbnew.F_Cu)])
for t in b.Tracks():
    if t.GetClass() == "PCB_VIA":
        c = t.GetPosition(); items.append(["via", [c.x/1e6, c.y/1e6], t.GetNetname()])
    else:
        s, e = t.GetStart(), t.GetEnd()
        items.append(["trk", [s.x/1e6, s.y/1e6, e.x/1e6, e.y/1e6, t.GetWidth()/1e6], t.GetNetname(), t.GetLayerName()])
json.dump({"win": [x0, y0, x1, y1], "items": items}, open("/tmp/_plot.json", "w"))
