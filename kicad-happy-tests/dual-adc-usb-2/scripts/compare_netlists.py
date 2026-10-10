"""Compare connectivity of two KiCad netlists (net = set of ref.pin). Prints differences."""
import re
import sys


def load(path):
    import os
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from build_pcb_netlist import parse_netlist
    _, nets = parse_netlist(path)
    return {k: frozenset(f"{r}.{p}" for r, p in v if not r.startswith("#")) for k, v in nets.items()}


def main(a, b):
    na, nb = load(a), load(b)
    sa = {v: k for k, v in na.items() if not k.startswith("unconnected") and len(v) > 1}
    sb = {v: k for k, v in nb.items() if not k.startswith("unconnected") and len(v) > 1}
    only_a = [sa[s] for s in sa if s not in sb]
    only_b = [sb[s] for s in sb if s not in sa]
    print(f"{a}: {len(sa)} multi-pin nets; {b}: {len(sb)}")
    # map pin -> net for diagnostics
    pa = {p: k for k, v in na.items() for p in v}
    pb = {p: k for k, v in nb.items() for p in v}
    for n in sorted(only_a):
        pins = na[n]
        others = sorted({pb.get(p, "<none>") for p in pins})
        print(f"A-only {n} ({len(pins)} pins) -> in B as {others[:6]}")
    for n in sorted(only_b):
        pins = nb[n]
        others = sorted({pa.get(p, "<none>") for p in pins})
        print(f"B-only {n} ({len(pins)} pins) <- from A {others[:6]}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
