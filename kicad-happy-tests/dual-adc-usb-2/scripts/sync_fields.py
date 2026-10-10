"""Copy Value/MPN/Tolerance/Dielectric from the schematic netlist onto PCB footprints (by ref).
usage: python3.11 sync_fields.py board.kicad_pcb netlist.net"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_pcb_netlist import parse_netlist  # noqa: E402

b = pcbnew.LoadBoard(sys.argv[1])
comps, _ = parse_netlist(sys.argv[2])
n = 0
for fp in b.GetFootprints():
    c = comps.get(fp.GetReference())
    if not c:
        continue
    fp.SetValue(c["value"])
    for k in ("MPN", "Tolerance", "Dielectric"):
        if k in c["fields"] and fp.GetFieldText(k) != c["fields"][k]:
            fp.SetField(k, c["fields"][k])
            n += 1
b.Save(sys.argv[1])
print("fields updated:", n)
