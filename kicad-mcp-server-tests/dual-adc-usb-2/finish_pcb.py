"""Import Freerouting's session into the fanout board, add GND pours, fill, save.

    ~/bin/kicad10-root/bin/python3.11 finish_pcb.py <work_dir> [in2_net]
in2_net (default GND) is the net poured on In2.Cu; "+3V3" for the +3V3-plane variant.
Reads <work_dir>/fanout.kicad_pcb and <work_dir>/route.ses; writes dual_adc_usb.kicad_pcb.
The locked GND fanout survives the SES import (KiCad replaces only unlocked tracks).
"""

import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
WORK = Path(sys.argv[1])
IN2_NET = sys.argv[2] if len(sys.argv) > 2 else "GND"
MM = pcbnew.FromMM


def add_zone(board, layer, net="GND", inset=0.3, priority=0):
    edge = board.GetBoardEdgesBoundingBox()
    x0, y0 = edge.GetX() + MM(inset), edge.GetY() + MM(inset)
    x1, y1 = edge.GetRight() - MM(inset), edge.GetBottom() - MM(inset)
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(board.FindNet(net))
    z.SetAssignedPriority(priority)
    z.SetLocalClearance(MM(0.25))
    z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.3))
    z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
    ol = z.Outline()
    ol.NewOutline()
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(x, y)
    board.Add(z)


def main():
    board = pcbnew.LoadBoard(str(WORK / "fanout.kicad_pcb"))
    if not pcbnew.ImportSpecctraSES(board, str(WORK / "route.ses")):
        raise RuntimeError("SES import failed")
    for layer in (pcbnew.In1_Cu, pcbnew.F_Cu, pcbnew.B_Cu):
        add_zone(board, layer)
    add_zone(board, pcbnew.In2_Cu, IN2_NET)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    out = HERE / "dual_adc_usb.kicad_pcb"
    pro = (HERE / "dual_adc_usb.kicad_pro").read_text()
    board.Save(str(out))
    (HERE / "dual_adc_usb.kicad_pro").write_text(pro)  # keep net classes/rules (Save rewrites it)
    print("saved", out)


if __name__ == "__main__":
    main()
