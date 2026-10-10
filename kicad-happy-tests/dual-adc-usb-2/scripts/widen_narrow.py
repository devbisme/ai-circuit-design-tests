"""Widen track segments below the board minimum (Freerouting neck-downs) to 0.1 mm.
usage: python3.11 widen_narrow.py board.kicad_pcb"""
import sys

import pcbnew

b = pcbnew.LoadBoard(sys.argv[1])
n = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_TRACK" and t.GetWidth() < pcbnew.FromMM(0.1):
        t.SetWidth(pcbnew.FromMM(0.1))
        n += 1
b.Save(sys.argv[1])
print("widened", n)
