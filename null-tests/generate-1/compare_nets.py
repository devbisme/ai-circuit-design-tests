"""Compare connectivity of two KiCad netlists (e.g. SKiDL vs schematic export).

    python3 compare_nets.py dual_adc.net dual_adc_sch.net
"""
import re
import sys


def sexp(text):
    tokens = re.findall(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+', text)
    stack, cur = [], []
    for t in tokens:
        if t == "(":
            stack.append(cur)
            cur = []
        elif t == ")":
            done = cur
            cur = stack.pop()
            cur.append(done)
        else:
            cur.append(t[1:-1] if t.startswith('"') else t)
    return cur[0]


def find(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]


def get(node, key):
    r = find(node, key)
    return r[0][1] if r else None


def groups(path):
    root = sexp(open(path).read())
    out = {}
    for n in find(find(root, "nets")[0], "net"):
        nodes = frozenset((get(x, "ref"), get(x, "pin")) for x in find(n, "node")
                          if not get(x, "ref").startswith("#"))  # skip PWR_FLAGs
        out[nodes] = get(n, "name")
    return out


if __name__ == "__main__":
    a, b = groups(sys.argv[1]), groups(sys.argv[2])
    pa = {p: k for k in a for p in k}
    pb = {p: k for k in b for p in k}
    bad = 0
    for k in a:
        if k not in b:
            bad += 1
            print("A net", a[k], "differs:")
            for p in sorted(k):
                kb = pb.get(p)
                print("    ", p, "->", b.get(kb) if kb else "UNCONNECTED",
                      len(kb) if kb else "")
    for k in b:
        if k not in a and len(k) > 1:
            extra = [p for p in k if p not in pa]
            if extra:
                print("B net", b[k], "has pins not in A:", extra)
    print("differing nets:", bad)
