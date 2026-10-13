"""Repair kcaa flip_footprint artifacts on B.Cu footprints: courtyard left on F.CrtYd and
texts not mirrored.  (Pad positions are left as-is: the flipped parts are symmetric 2-pad
caps, and moving pads would detach routed copper.)  KiCad 10 python: fix_flips.py in out"""
import sys, pcbnew
b = pcbnew.LoadBoard(sys.argv[1])
nc = nt = 0
for f in b.GetFootprints():
    if f.GetLayer() != pcbnew.B_Cu:
        continue
    for g in f.GraphicalItems():
        if g.GetLayer() == pcbnew.F_CrtYd:
            g.SetLayer(pcbnew.B_CrtYd); nc += 1
        if isinstance(g, pcbnew.PCB_TEXT) and g.GetLayer() in (pcbnew.B_SilkS, pcbnew.B_Fab) \
                and not g.IsMirrored():
            g.SetMirrored(True); nt += 1
    for fld in f.GetFields():
        if fld.GetLayer() in (pcbnew.B_SilkS, pcbnew.B_Fab) and not fld.IsMirrored():
            fld.SetMirrored(True); nt += 1
pcbnew.SaveBoard(sys.argv[2], b)
print(f"courtyards moved {nc}, texts mirrored {nt}")
