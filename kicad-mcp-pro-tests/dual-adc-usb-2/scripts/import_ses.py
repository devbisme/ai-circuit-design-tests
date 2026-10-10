"""Import a Freerouting session into the board, add GND pours, fill zones, save.

KiCad's SES import keeps locked items (the GND fanout) and replaces unlocked routing.
F.Cu/B.Cu GND pours are added here (after routing) so the router never saw them.
Usage: import_ses.py board.kicad_pcb session.ses
"""
import sys
import pcbnew

MM = pcbnew.FromMM


def add_pour(board, layer, name):
    gnd = board.FindNet('GND')
    bb = board.GetBoardEdgesBoundingBox()
    z = pcbnew.ZONE(board)
    z.SetLayer(layer); z.SetNet(gnd); z.SetZoneName(name)
    z.SetLocalClearance(MM(0.25)); z.SetMinThickness(MM(0.2))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    z.SetThermalReliefGap(MM(0.25)); z.SetThermalReliefSpokeWidth(MM(0.3))
    z.SetAssignedPriority(0)
    ol = z.Outline(); ol.NewOutline()
    x0, y0, x1, y1 = bb.GetLeft() + MM(0.3), bb.GetTop() + MM(0.3), bb.GetRight() - MM(0.3), bb.GetBottom() - MM(0.3)
    for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
        ol.Append(x, y)
    board.Add(z)


def main(pcb, ses):
    board = pcbnew.LoadBoard(pcb)
    if not pcbnew.ImportSpecctraSES(board, ses):
        sys.exit('SES import failed')
    names = {z.GetZoneName() for z in board.Zones()}
    if 'GND_TOP' not in names:
        add_pour(board, pcbnew.F_Cu, 'GND_TOP')
    if 'GND_BOT' not in names:
        add_pour(board, pcbnew.B_Cu, 'GND_BOT')
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(pcb)
    tracks = [t for t in board.GetTracks()]
    print('tracks+vias:', len(tracks), 'vias:', sum(isinstance(t, pcbnew.PCB_VIA) for t in tracks))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
