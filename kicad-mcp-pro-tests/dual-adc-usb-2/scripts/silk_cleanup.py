"""Hide silkscreen reference text of small passives (it stays on F.Fab via the
footprint's ${REFERENCE} fab text). Dense 0603 placement put most refs over pads."""
import sys, re
import pcbnew
b = pcbnew.LoadBoard(sys.argv[1]); n = 0
for fp in b.GetFootprints():
    if re.match(r'^(R|C|D|FB|F|RN)\d', fp.GetReference()) or fp.GetReference().startswith(('U1', 'U2', 'U3', 'U40', 'X', 'Y', 'U70')):
        if fp.Reference().IsVisible():
            fp.Reference().SetVisible(False); n += 1
b.Save(sys.argv[1]); print('hidden refs:', n)
