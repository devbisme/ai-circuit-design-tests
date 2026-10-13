"""KiCad 10 python: remove one bad fanout (track+via) and tie U10 pin 59 to pin 58 (both GND)."""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); pro = sys.argv[1].replace(".kicad_pcb", ".kicad_pro"); pt = open(pro).read()
to, mm = pcbnew.ToMM, pcbnew.FromMM
rm = []
for t in list(b.GetTracks()):
    if t.GetNetname() != "GND":
        continue
    if t.GetClass() == "PCB_VIA":
        c = t.GetPosition()
        if abs(to(c.x) - 50.08) < 0.02 and abs(to(c.y) - 35.24) < 0.02: rm.append(t)
    else:
        s, e = t.GetStart(), t.GetEnd()
        if abs(to(s.x) - 48.75) < 0.02 and abs(to(s.y) - 36.5625) < 0.02 and abs(to(e.x) - 50.08) < 0.05: rm.append(t)
print("removing", len(rm))
gnd = b.FindNet("GND")
t = pcbnew.PCB_TRACK(b); t.SetStart(pcbnew.VECTOR2I(mm(48.75), mm(36.5625))); t.SetEnd(pcbnew.VECTOR2I(mm(49.25), mm(36.5625)))
t.SetWidth(mm(0.2)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); t.SetLocked(True); b.Add(t)
for r in rm: b.Remove(r)
b.Save(sys.argv[1]); open(pro, "w").write(pt)
