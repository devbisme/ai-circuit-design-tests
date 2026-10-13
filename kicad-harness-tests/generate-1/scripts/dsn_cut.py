"""Reduce plane nets (GND, +3V3) in a DSN to their un-fanned pins plus one anchor pin."""
import re, sys
src, dst, failed = sys.argv[1], sys.argv[2], set(sys.argv[3].split(",")) if len(sys.argv) > 3 else set()
t = open(src).read()
failed = {f.replace(".", "-") for f in failed}
def cut(m):
    name, pins = m.group(1), m.group(2).split()
    keep = [p for p in pins if p in failed]
    anchor = next((p for p in pins if p not in failed), None)
    keep = ([anchor] if anchor else []) + keep
    print(f"{name}: {len(pins)} -> {len(keep)} pins")
    return f"(net {name}\n      (pins {' '.join(keep)})"
t = re.sub(r'\(net (GND|\+3V3)\s*\n\s*\(pins ([^)]*)\)', cut, t)
open(dst, "w").write(t)
