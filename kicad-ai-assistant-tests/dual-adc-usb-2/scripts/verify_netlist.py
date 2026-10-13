"""Compare kicad-cli netlist of the schematic against design.py (pin-set per net)."""
import subprocess, sys
from sexp import parse, find, find1
import design
CLI = "/home/devb/bin/kicad10-root/bin/kicad-cli"
out = "/tmp/claude-1000/dual_adc.net"
subprocess.run([CLI, "sch", "export", "netlist", "../dual_adc.kicad_sch", "-o", out],
               check=True, capture_output=True)
t = parse(open(out).read())
got = {}
for n in find(find1(t, "nets"), "net"):
    pins = frozenset((find1(x, "ref")[1], find1(x, "pin")[1]) for x in find(n, "node"))
    got[find1(n, "name")[1]] = pins
want = {k: frozenset(v) for k, v in design.nets().items()}
gs = {v: k for k, v in got.items()}
bad = 0
for net, pins in sorted(want.items()):
    if pins in gs:
        continue
    bad += 1
    # find nets in got that overlap
    ov = [(k, len(v & pins), len(v)) for k, v in got.items() if v & pins]
    print(f"MISMATCH {net} ({len(pins)} pins): overlaps {ov[:5]}")
comps = {find1(c, "ref")[1] for c in find(find1(t, "components"), "comp")}
missing = set(design.PARTS) - comps
extra = comps - set(design.PARTS)
print(f"design nets {len(want)}, schematic nets {len(got)}, mismatched {bad}, "
      f"missing parts {sorted(missing)}, extra parts {sorted(extra)}")
