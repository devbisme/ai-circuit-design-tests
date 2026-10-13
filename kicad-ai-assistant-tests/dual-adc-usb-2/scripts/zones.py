"""(Re)create the inner-layer plane zones with KiCad's API (kcaa add_zone output loads as
F.Cu in KiCad 10).  Usage: zones.py in.kicad_pcb out.kicad_pcb [--fill]"""
import sys, pcbnew
MM = 1e6
ZONES = [
    ("In1.Cu", "GND", [(100.3, 100.3), (227.7, 100.3), (227.7, 184.7), (100.3, 184.7)]),
    ("In2.Cu", "+3V3", [(166.0, 100.3), (227.7, 100.3), (227.7, 184.7), (147.0, 184.7),
                        (147.0, 165.0), (166.0, 165.0)]),
    ("In2.Cu", "GND", [(100.3, 100.3), (165.4, 100.3), (165.4, 164.4), (146.4, 164.4),
                       (146.4, 184.7), (100.3, 184.7)]),
]
import subprocess
if "--strip" in sys.argv:          # separate process: KiCad 10 SWIG wrappers break after Remove()
    b = pcbnew.LoadBoard(sys.argv[1])
    for z in list(b.Zones()):
        b.Remove(z)
    pcbnew.SaveBoard(sys.argv[2], b)
    sys.exit(0)
subprocess.run([sys.executable, __file__, sys.argv[1], sys.argv[2], "--strip"], check=True)
b = pcbnew.LoadBoard(sys.argv[2])
for layer, net, pts in ZONES:
    z = pcbnew.ZONE(b)
    z.SetLayer(b.GetLayerID(layer))
    z.SetNet(b.FindNet(net))
    ol = z.Outline()
    ol.NewOutline()
    for x, y in pts:
        ol.Append(int(x * MM), int(y * MM))
    z.SetLocalClearance(int(0.3 * MM))
    z.SetMinThickness(int(0.2 * MM))
    z.SetThermalReliefGap(int(0.3 * MM))
    z.SetThermalReliefSpokeWidth(int(0.4 * MM))
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    b.Add(z)
    z.thisown = 0
if "--fill" in sys.argv:
    pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)
print([(z.GetLayerName(), z.GetNetname()) for z in b.Zones()])
