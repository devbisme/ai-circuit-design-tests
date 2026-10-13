"""Run with KiCad 10 python: import a Freerouting SES (keeps locked fanout), add GND pours, refill, save.

usage: python3.11 import_ses.py <board.kicad_pcb> <routes.ses>
"""
import json
import sys
from pathlib import Path

import pcbnew

BOARD, SES = Path(sys.argv[1]), Path(sys.argv[2])
PRO = BOARD.with_suffix(".kicad_pro")
pro_text = PRO.read_text()
mm = pcbnew.FromMM

b = pcbnew.LoadBoard(str(BOARD))
ok = pcbnew.ImportSpecctraSES(b, str(SES))
print("SES import:", ok)
edge = b.GetBoardEdgesBoundingBox()
x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (edge.GetLeft(), edge.GetTop(), edge.GetRight(), edge.GetBottom()))
have = {(z.GetLayer(), z.GetNetname()) for z in b.Zones()}
for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
    if (layer, "GND") in have:
        continue
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet("GND"))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(mm(x), mm(y))
    z.SetMinThickness(mm(0.2))
    z.SetLocalClearance(mm(0.25))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    b.Add(z)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BOARD))
PRO.write_text(pro_text)      # Save() rewrites the project file; restore net classes/rules
print("saved", BOARD)
