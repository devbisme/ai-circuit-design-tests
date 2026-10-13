"""Export a Specctra DSN for Freerouting from a zone-free copy of the board, then:
 - mark In1/In2 as power layers (signals stay on F.Cu/B.Cu; inner layers are planes),
 - cut the plane nets (GND, +3V3) down to one pin: their pads are already connected to the
   planes by the locked fanout, and Freerouting would otherwise route them pad-to-pad.
Usage (KiCad 10 python): export_dsn.py board.kicad_pcb out.dsn"""
import re, subprocess, sys, os, pcbnew
src, dsn = sys.argv[1], sys.argv[2]
tmp = dsn.replace(".dsn", "_nozones.kicad_pcb")
subprocess.run([sys.executable, os.path.join(os.path.dirname(__file__), "zones.py"), src, tmp,
                "--strip"], check=True)
import shutil   # net classes live in the .kicad_pro, which must sit next to the board
shutil.copy(src.replace(".kicad_pcb", ".kicad_pro"), tmp.replace(".kicad_pcb", ".kicad_pro"))
b = pcbnew.LoadBoard(tmp)
assert pcbnew.ExportSpecctraDSN(b, dsn)
t = open(dsn).read()
t, n = re.subn(r'\(layer (In[12]\.Cu)\s*\(type signal\)', r'(layer \1 (type power)', t)
print("inner layers set to power:", n)
for net in ("GND", "+3V3"):
    pat = re.compile(r'\(net "?' + re.escape(net) + r'"?\s*\(pins ([^)]*)\)')
    m = pat.search(t)
    pins = m.group(1).split()
    t = t[:m.start(1)] + pins[0] + t[m.end(1):]
    print(f"{net}: {len(pins)} pins -> 1 ({pins[0]})")
open(dsn, "w").write(t)
