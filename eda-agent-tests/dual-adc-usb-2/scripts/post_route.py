"""Import the Freerouting session, add outer GND pours, fill zones (KiCad python).

usage: python3.11 post_route.py [route/dual_adc.ses]
Then run patch_project.py (board.Save rewrites the .kicad_pro).
"""

import os
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
PCB = os.path.join(ROOT, "kicad", "dual_adc.kicad_pcb")
SES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "route", "dual_adc.ses")
mm = pcbnew.FromMM
OX, OY, BW, BH = 40.0, 40.0, 125.0, 95.0

board = pcbnew.LoadBoard(PCB)
n_locked = sum(1 for t in board.Tracks() if t.IsLocked())
ok = pcbnew.ImportSpecctraSES(board, SES)
n_after = sum(1 for t in board.Tracks() if t.IsLocked())
print("SES import", ok, "locked items before/after", n_locked, n_after,
      "total tracks+vias", len(board.Tracks()))

gnd = board.FindNet("GND")
for layer, name in ((pcbnew.F_Cu, "GND_top"), (pcbnew.B_Cu, "GND_bottom")):
    if any(z.GetZoneName() == name for z in board.Zones()):
        continue
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(gnd)
    z.SetZoneName(name)
    o = z.Outline()
    o.NewOutline()
    for x, y in ((0.3, 0.3), (BW - 0.3, 0.3), (BW - 0.3, BH - 0.3), (0.3, BH - 0.3)):
        o.Append(mm(OX + x), mm(OY + y))
    z.SetAssignedPriority(0)
    z.SetLocalClearance(mm(0.25))
    z.SetMinThickness(mm(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(mm(0.25))
    z.SetThermalReliefSpokeWidth(mm(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    board.Add(z)

pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(PCB)
print("saved", PCB)
