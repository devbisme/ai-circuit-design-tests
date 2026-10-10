"""Pre-route USB D+/D- (J1 -> USBLC6 flow-through -> FT2232H) with the A* router, 0.2 mm tracks,
locked, before Freerouting runs. usage: python3.11 preroute_usb.py board.kicad_pcb"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import astar_fix as A  # noqa: E402

b = pcbnew.LoadBoard(sys.argv[1])
fps = {fp.GetValue(): fp for fp in b.GetFootprints()}
J, E, U = fps["USB_B"], fps["USBLC6-2SC6"], fps["FT2232HL"]
bb = b.GetBoardEdgesBoundingBox()
edge = tuple(pcbnew.ToMM(v) for v in (bb.GetLeft(), bb.GetTop(), bb.GetRight(), bb.GetBottom()))


def pad(fp, num):
    return [p for p in fp.Pads() if p.GetNumber() == num][0]


# (from pad, to pad) chains; USBLC6 I/O1 = pins 1/6 (D+), I/O2 = pins 3/4 (D-)
links = [((J, "3"), (E, "6")), ((E, "1"), (U, "8")), ((J, "2"), (E, "4")), ((E, "3"), (U, "7"))]
A.PLANE_NETS = A.PLANE_NETS
for (fa, na), (fb, nb) in links:
    items = A.collect(b)
    pa, pb = pad(fa, na), pad(fb, nb)
    ia = [it for it in items if it.kind == "pad" and it.obj.GetParentFootprint().GetReference() == fa.GetReference()
          and it.obj.GetNumber() == na][0]
    ib = [it for it in items if it.kind == "pad" and it.obj.GetParentFootprint().GetReference() == fb.GetReference()
          and it.obj.GetNumber() == nb][0]
    A.W, A.CLR = 0.2, 0.175
    res = A.route(b, items, ia, ib, pa.GetNetname(), edge, usb=True)
    if res is None:
        print("USB preroute FAILED", pa.GetNetname(), fa.GetReference(), na, "->", fb.GetReference(), nb)
        continue
    path, end_via = res
    before = {id(t) for t in b.GetTracks()}
    nt, nv = A.emit(b, pa.GetNetname(), path, end_via)
    for t in b.GetTracks():
        if t.GetNetname() == pa.GetNetname():
            t.SetLocked(True)
    print(f"USB {pa.GetNetname()}: {nt} tracks, {nv} vias")
b.Save(sys.argv[1])
