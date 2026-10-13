"""KiCad 10 python: board-level cleanup after routing.

- grow the board to 120 x 88 mm and move the bottom mounting holes clear of the USB connector
- move reference designators of small passives to F.Fab (silk only for ICs/connectors/LEDs)
- delete dangling unlocked track stubs reported by DRC
- relax min track width to 0.1 mm (Freerouting necks down at fine-pitch pins)
usage: python3.11 polish.py <board.kicad_pcb> [drc.json]
"""
import json
import sys

import pcbnew

BRD = sys.argv[1]
PRO = BRD.replace(".kicad_pcb", ".kicad_pro")
mm, to = pcbnew.FromMM, pcbnew.ToMM
W, H = 120.0, 88.0
b = pcbnew.LoadBoard(BRD)
TRACKS = list(b.GetTracks())

# outline and hole moves are done offline first (kh outline / kh place): BOARD.Remove() of drawings segfaults KiCad 10 SWIG
for z in b.Zones():
    ol = z.Outline()
    for i in range(ol.TotalVertices()):
        v = ol.CVertex(i)
        if to(v.y) > 80:
            ol.SetVertex(i, pcbnew.VECTOR2I(v.x, mm(H)))
fps = {f.GetReference(): f for f in b.GetFootprints()}

# silk: keep refs on ICs, connectors, LEDs, crystals; move passives' refs to F.Fab
moved = 0
for ref, f in fps.items():
    if ref.startswith(("R", "C", "FB", "L", "F")) or ref.startswith("RN") or ref.startswith("H"):
        f.Reference().SetLayer(pcbnew.F_Fab)
        moved += 1
    else:
        f.Reference().SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
        f.Reference().SetTextThickness(mm(0.12))
print("refs moved to F.Fab:", moved)

# dangling stubs
rm = []
if len(sys.argv) > 2:
    d = json.load(open(sys.argv[2]))
    for t in d["violations"]["by_type"]:
        if t["type"] not in ("track_dangling", "via_dangling"):
            continue
        for smp in t["samples"]:
            a = smp["at"][0]
            for tr in TRACKS:
                if tr.IsLocked():
                    continue
                if tr.GetClass() == "PCB_VIA":
                    c = tr.GetPosition()
                    hit = abs(to(c.x) - a["x"]) < 0.02 and abs(to(c.y) - a["y"]) < 0.02
                else:
                    s_, e_ = tr.GetStart(), tr.GetEnd()
                    mx, my = (to(s_.x) + to(e_.x)) / 2, (to(s_.y) + to(e_.y)) / 2
                    hit = (abs(mx - a["x"]) < 0.02 and abs(my - a["y"]) < 0.02) or \
                          any(abs(to(q.x) - a["x"]) < 0.02 and abs(to(q.y) - a["y"]) < 0.02 for q in (s_, e_))
                    hit = hit and a["desc"].startswith("Track") and tr.GetNetname() in a["desc"]
                if hit and tr not in rm:
                    rm.append(tr)
for tr in rm:
    b.Remove(tr)
print("removed dangling items:", len(rm))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(BRD)
pro = json.load(open(PRO))
r = pro["board"]["design_settings"]["rules"]
r.update(min_track_width=0.1)
json.dump(pro, open(PRO, "w"), indent=2)
