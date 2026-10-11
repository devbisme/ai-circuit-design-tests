"""One-off layout repair around U4 (LM27762) after autorouting (KiCad python).

Freerouting boxed in the flying-cap pins 9/10 between the +4V (pin 11) and +5V
(pin 8) traces, with C10 placed above the part. Rip up the copper on those
four nets beside U4, swap C10 to its new 0402 footprint, and move it tight to
pins 9/10. fix_unrouted.py then re-routes the open connections.

Each step runs in its own process: in KiCad 10's python, after board items
are removed or a library footprint is loaded, later SWIG wrappers in that
process can come back as bare SwigPyObjects.
"""
import os
import subprocess
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import board_sync  # noqa: E402

PCB = os.path.join(HERE, "..", "kicad", "dual_adc.kicad_pcb")
mm = pcbnew.FromMM
b = pcbnew.LoadBoard(PCB)
fps = {f.GetReference(): f for f in b.GetFootprints()}
u4 = fps["U4"]
ux, uy = u4.GetPosition().x / 1e6, u4.GetPosition().y / 1e6

if len(sys.argv) > 1 and sys.argv[1] == "--place":
    c10 = fps["C10"]
    c10.SetOrientationDegrees(270)
    c10.SetPosition(pcbnew.VECTOR2I(mm(ux + 1.95), mm(uy - 0.05)))
    print("C10 pads", [(p.GetNumber(), p.GetNetname(), p.GetPosition().x / 1e6,
                        p.GetPosition().y / 1e6) for p in c10.Pads()])
    b.Save(PCB)
    sys.exit(0)

box = (ux + 0.5, uy - 2.2, ux + 3.6, uy + 2.0)


def inside(v):
    return box[0] < v.x / 1e6 < box[2] and box[1] < v.y / 1e6 < box[3]


gone = 0
for t in list(b.Tracks()):
    if t.IsLocked():
        continue
    n = t.GetNetname()
    hit = n in ("LM_CPF", "LM_CN")
    if n in ("+4V", "+5V"):
        hit = inside(t.GetPosition()) if t.GetClass() == "PCB_VIA" else \
            inside(t.GetStart()) or inside(t.GetEnd())
    if hit:
        b.Remove(t)
        gone += 1
print("removed", gone)
b.Save(PCB)
board_sync.resync(PCB)          # swaps C10 to 0402 (fresh process)
board_sync.resync(PCB)          # fields/paths on the swapped board
subprocess.run([sys.executable, os.path.abspath(__file__), "--place"], check=True)
