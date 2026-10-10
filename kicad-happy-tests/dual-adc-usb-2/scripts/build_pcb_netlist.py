"""KiCad kicadsexpr netlist parser (no pcbnew dependency)."""
import re


# ---------------------------------------------------------------- netlist parse
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
            cur.append(t[1:-1].replace('\\"', '"') if t.startswith('"') else t)
    return cur[0]


def find(node, key):
    return [n for n in node if isinstance(n, list) and n and n[0] == key]


def val(node, key, default=None):
    f = find(node, key)
    return f[0][1] if f and len(f[0]) > 1 else default


def parse_netlist(path):
    root = sexp(open(path).read())
    comps = {}
    for c in find(find(root, "components")[0], "comp"):
        ref = val(c, "ref")
        sp = find(c, "sheetpath")[0]
        fields = {}
        for fl in find(c, "fields"):
            for f in find(fl, "field"):
                name = val(f, "name")
                fields[name] = f[2] if len(f) > 2 else ""
        props = {val(p, "name"): val(p, "value") for p in find(c, "property")}
        comps[ref] = dict(
            ref=ref, value=val(c, "value", ""), footprint=val(c, "footprint", ""),
            sheetnames=val(sp, "names"), sheettstamps=val(sp, "tstamps"),
            tstamp=(val(c, "tstamps") or ""), fields=fields, props=props,
        )
    nets = {}
    for n in find(find(root, "nets")[0], "net"):
        name = val(n, "name")
        nets[name] = [(val(nd, "ref"), val(nd, "pin")) for nd in find(n, "node")]
    return comps, nets


