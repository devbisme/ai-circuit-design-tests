"""Import Freerouting's SES into the board (locked fanout is kept), refill zones, save.
Usage (KiCad 10 python): import_ses.py board.kicad_pcb routed.ses out.kicad_pcb"""
import os, shutil, sys, pcbnew
# SaveBoard rewrites <out>.kicad_pro from the loaded board's project settings; if the input
# board has no .kicad_pro beside it, the real project rules get replaced by defaults.
# Keep a copy of the output's project file and put it back afterwards.
pro_out = sys.argv[3].replace(".kicad_pcb", ".kicad_pro")
saved = open(pro_out).read() if os.path.exists(pro_out) else None
b = pcbnew.LoadBoard(sys.argv[1])
before = sum(1 for t in b.GetTracks() if t.IsLocked())
assert pcbnew.ImportSpecctraSES(b, sys.argv[2])
locked = sum(1 for t in b.GetTracks() if t.IsLocked())
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[3], b)
if saved is not None:
    open(pro_out, "w").write(saved)
n = sum(1 for _ in b.GetTracks())
print(f"locked items before/after: {before}/{locked}; total tracks+vias {n}")
