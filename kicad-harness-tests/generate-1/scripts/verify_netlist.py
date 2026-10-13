"""Compare kicad-cli's netlist of the generated schematic against design.build()."""
import subprocess, sys, re
from pathlib import Path
from sexp import parse, find, find1
import design
root = Path(__file__).resolve().parent.parent / "dual_adc"
out = root.parent / "work" / "dual_adc.net"
subprocess.run(["kh", "netlist", "--sch", str(root), "--out", str(out)], check=True, capture_output=True)
t = parse(out.read_text())
got = {}
for n in find(find1(t, "nets"), "net"):
    name = str(find1(n, "name")[1]).lstrip("/")
    pins = frozenset((str(find1(x, "ref")[1]), str(find1(x, "pin")[1])) for x in find(n, "node")
                     if not str(find1(x, "ref")[1]).startswith("#"))
    if pins:
        got[pins] = name
want = {frozenset(p): n for n, p in design.build().nets().items()}
want = {frozenset(x for x in k if not x[0].startswith("#")): v for k, v in want.items()}
want = {k: v for k, v in want.items() if k}
miss = [v for k, v in want.items() if k not in got]
extra = [v for k, v in got.items() if k not in want and len(k) > 1]
print(f"design nets {len(want)}, kicad nets {len(got)}, missing/different {len(miss)}, extra {len(extra)}")
for m in miss[:20]: print("  MISSING", m)
for m in extra[:20]: print("  EXTRA", m)
sys.exit(1 if miss or extra else 0)
