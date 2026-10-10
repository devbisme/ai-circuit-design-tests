"""Remove PWR_FLAGs that sch_build_circuit auto-adds on every sheet.

Each flag sits on a same-position global label. Keep one flag per net listed in KEEP;
drop the rest (flag symbol + its label). Nets with real power-output drivers need none.
"""
import re, sys, pathlib
KEEP = set(sys.argv[2:])
proj = pathlib.Path(sys.argv[1]); kept = set()

def block_at(t, i):
    """Return (start, end) of the balanced block whose '(' is at index i (tab-indented)."""
    d = 0
    i = t.index('(', i)
    for j in range(i, len(t)):
        d += {'(': 1, ')': -1}.get(t[j], 0)
        if d == 0: return i, j + 1

for f in sorted(proj.glob('*.kicad_sch')):
    t = f.read_text(); cuts = []
    labels = {(m.group(2), m.group(3)): (m.group(1), t.rfind('\n\t(global_label', 0, m.end()) + 1)
              for m in re.finditer(r'\(global_label "([^"]+)"\s*\(shape \w+\)\s*\(at ([-\d.]+) ([-\d.]+)', t)}
    for m in re.finditer(r'\(lib_id "power:PWR_FLAG"\)\s*\(at ([-\d.]+) ([-\d.]+)', t):
        net, lstart = labels.get(m.groups(), (None, None))
        if net in KEEP and net not in kept:
            kept.add(net); continue
        cuts.append(block_at(t, t.rfind('\n\t(symbol', 0, m.start()) + 1))
        if lstart is not None: cuts.append(block_at(t, lstart))
        print(f.name, 'drop flag on', net)
    for s, e in sorted(cuts, reverse=True):
        t = t[:s] + t[e:].lstrip('\n')
    f.write_text(t)
print('kept', kept)
