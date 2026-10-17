"""
Final touches after routing:
  - pads that DRC reports as 'starved_thermal' get a solid zone connection,
  - mounting holes are marked board-only / excluded from BOM,
  - zones are refilled.
Saving the board makes pcbnew rewrite dual_adc.kicad_pro with default rules,
so run write_project.py afterwards.

    ~/bin/kicad10-root/bin/python3.11 finish_board.py dual_adc.kicad_pcb drc.rpt
"""
import re
import sys
import pcbnew as pn

pcb, rpt = sys.argv[1:3]
b = pn.LoadBoard(pcb)

starved = set()
for blk in open(rpt).read().split("\n["):
    if blk.startswith("starved_thermal"):
        starved.update(re.findall(r"Pad (\S+) \[GND\] of (\S+) on", blk))
for pad, ref in sorted(starved):
    for p in b.FindFootprintByReference(ref).Pads():
        if p.GetNumber() == pad:
            p.SetLocalZoneConnection(pn.ZONE_CONNECTION_FULL)
            print(f"solid zone connection: {ref} pad {pad}")

for fp in b.GetFootprints():
    if fp.GetReference().startswith("H"):
        fp.SetBoardOnly(True)
        fp.SetExcludedFromBOM(True)

pn.ZONE_FILLER(b).Fill(b.Zones())
b.Save(pcb)
print("saved", pcb)
