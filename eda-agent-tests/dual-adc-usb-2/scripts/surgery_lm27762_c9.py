"""Second U4 repair step (KiCad python, one process per mutation).

C9 (VIN cap) sits 0.01 mm from the relocated C10. Move C9 0.8 mm right,
redo its locked GND fanout, and rip up the local +4V/+5V copper so that
fix_unrouted.py can route +4V (pin 11) before +5V.
"""
import math
import os
import sys

import pcbnew

PCB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "kicad", "dual_adc.kicad_pcb")
mm = pcbnew.FromMM
step = sys.argv[1] if len(sys.argv) > 1 else "rip"
b = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in b.GetFootprints()}

if step == "rip":
    c9 = fps["C9"]
    gpad = [p for p in c9.Pads() if p.GetNetname() == "GND"][0].GetPosition()
    gx, gy = gpad.x / 1e6, gpad.y / 1e6
    gone = 0
    for t in list(b.Tracks()):
        n = t.GetNetname()
        if n == "GND" and t.IsLocked():
            pts = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
            if any(math.hypot(p.x / 1e6 - gx, p.y / 1e6 - gy) < 0.05 for p in pts) or \
               (t.GetClass() == "PCB_VIA" and math.hypot(t.GetPosition().x / 1e6 - gx,
                                                         t.GetPosition().y / 1e6 - (gy - 0.925)) < 0.05):
                b.Remove(t); gone += 1
            continue
        if n in ("+4V", "+5V") and not t.IsLocked():
            pts = [t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()]
            if any(61.5 < p.x / 1e6 < 66.5 and 86.0 < p.y / 1e6 < 93.0 for p in pts):
                b.Remove(t); gone += 1
    print("removed", gone)
    b.Save(PCB)
elif step == "move":
    c9 = fps["C9"]
    p = c9.GetPosition()
    c9.SetPosition(pcbnew.VECTOR2I(p.x + mm(0.8), p.y))
    gpad = [q for q in c9.Pads() if q.GetNetname() == "GND"][0].GetPosition()
    net = b.FindNet("GND")
    vx, vy = gpad.x, gpad.y - mm(0.925)
    t = pcbnew.PCB_TRACK(b); t.SetStart(gpad); t.SetEnd(pcbnew.VECTOR2I(vx, vy))
    t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(net); t.SetLocked(True); b.Add(t)
    v = pcbnew.PCB_VIA(b); v.SetPosition(pcbnew.VECTOR2I(vx, vy)); v.SetViaType(pcbnew.VIATYPE_THROUGH)
    v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetWidth(mm(0.45)); v.SetDrill(mm(0.2))
    v.SetNet(net); v.SetLocked(True); b.Add(v)
    print("C9 at", c9.GetPosition().x / 1e6, c9.GetPosition().y / 1e6, "GND via", vx / 1e6, vy / 1e6)
    b.Save(PCB)
