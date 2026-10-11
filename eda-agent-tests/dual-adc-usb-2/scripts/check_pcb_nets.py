"""Compare a board's pad->net assignment with the DesignPlan (run with KiCad python)."""
import json, sys
import pcbnew
board = pcbnew.LoadBoard(sys.argv[1])
plan = json.load(open(sys.argv[2]))
want = {}
for n in plan["nets"]:
    for p in n["pins"]:
        want[(p["refdes"], p["pin"])] = n["name"]
got = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNumber() and pad.IsOnCopperLayer():
            k = (fp.GetReference(), pad.GetNumber())
            nm = pad.GetNetname()
            if k in got and got[k] != nm:
                print("PAD SPLIT", k, got[k], nm)
            got[k] = nm
bad = 0
for k, v in want.items():
    if got.get(k) != v:
        bad += 1
        if bad < 15: print("MISMATCH", k, "want", v, "got", got.get(k))
extra = [k for k, v in got.items() if v and k not in want]
print("plan pins", len(want), "mismatches", bad, "extra netted pads", len(extra), extra[:10])
print("layers", board.GetCopperLayerCount(), "fps", len(board.GetFootprints()),
      "fpid sample", [str(f.GetFPID().GetUniStringLibId()) for f in list(board.GetFootprints())[:3]])
