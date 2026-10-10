"""
Post-route finishing (KiCad 10 python):  python3.11 scripts/finish_pcb.py in.kicad_pcb out.kicad_pcb
- adds F.Cu / B.Cu GND pours (deferred from build_pcb so Freerouting could use the outer layers)
- unlocks fanout so the board is editable normally
- moves reference designators of 2-/3-pin passives to the Fab layers (silkscreen too dense
  for them); IC/connector references stay on silkscreen at 0.8 mm
- fills all zones
"""
import sys

import pcbnew

MM = pcbnew.FromMM


def main(src, dst):
    board = pcbnew.LoadBoard(src)
    gnd = board.FindNet("GND")
    bb = board.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()
    have = {(z.GetLayer(), z.GetNetname()) for z in board.Zones()}
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        if (layer, "GND") in have:
            continue
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        ol = z.Outline()
        ol.NewOutline()
        m = MM(0.3)
        for x, y in ((x0 + m, y0 + m), (x1 - m, y0 + m), (x1 - m, y1 - m), (x0 + m, y1 - m)):
            ol.Append(x, y)
        z.SetLocalClearance(MM(0.25))
        z.SetMinThickness(MM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.25))
        z.SetThermalReliefSpokeWidth(MM(0.3))
        z.SetAssignedPriority(0)
        board.Add(z)

    for t in board.GetTracks():
        t.SetLocked(False)

    for fp in board.GetFootprints():
        ref = fp.Reference()
        if fp.GetPadCount() <= 3 and fp.GetReference()[0] in "RCLDF" and not fp.GetReference().startswith("H"):
            ref.SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
            ref.SetTextSize(pcbnew.VECTOR2I(MM(0.4), MM(0.4)))
            ref.SetTextThickness(MM(0.06))
        else:
            ref.SetTextSize(pcbnew.VECTOR2I(MM(0.8), MM(0.8)))
            ref.SetTextThickness(MM(0.12))

    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    board.Save(dst)
    print("finished", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
