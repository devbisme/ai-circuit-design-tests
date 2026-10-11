"""Minimal KiCad symbol-library access for KiCad 10 .kicad_symdir libraries.

eda-agent's symbol resolver only reads single-file <lib>.kicad_sym libraries,
so it cannot see KiCad 10's symdir libraries. This module fills that gap:
parse a symbol, flatten `extends`, and list its pins.
"""

import os
import re

SYMDIR = os.path.expanduser("~/bin/kicad10-root/share/kicad/symbols")


class Q(str):
    """A quoted string atom (kept distinct from bare symbols for re-emission)."""


_tok = re.compile(r'\s*(?:(\()|(\))|"((?:[^"\\]|\\.)*)"|([^\s()"]+))')


def parse(text):
    stack, cur = [], []
    pos = 0
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError(f"parse error at {pos}: {text[pos:pos+40]!r}")
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            cur.append(Q(m.group(3).replace('\\"', '"').replace("\\\\", "\\")))
        else:
            cur.append(m.group(4))
    return cur[0] if len(cur) == 1 else cur


def dump(x, indent=0):
    """Serialize an s-expression tree back to KiCad text."""
    if isinstance(x, Q):
        return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(x, str):
        return x
    if all(not isinstance(e, list) for e in x):
        return "(" + " ".join(dump(e) for e in x) + ")"
    pad = "\t" * (indent + 1)
    out = "(" + " ".join(dump(e) for e in x if not isinstance(e, list))
    for e in x:
        if isinstance(e, list):
            out += "\n" + pad + dump(e, indent + 1)
    return out + "\n" + "\t" * indent + ")"


def find(x, key):
    return [e for e in x if isinstance(e, list) and e and e[0] == key]


def find1(x, key):
    r = find(x, key)
    return r[0] if r else None


def _load_raw(lib, name):
    path = os.path.join(SYMDIR, lib + ".kicad_symdir", name + ".kicad_sym")
    tree = parse(open(path, encoding="utf-8").read())
    return find1(tree, "symbol")


def load_symbol(lib, name):
    """Return a flattened symbol tree (extends resolved) named lib:name."""
    sym = _load_raw(lib, name)
    ext = find1(sym, "extends")
    if ext:
        parent = load_symbol(lib, ext[1])
        child_props = {p[1]: p for p in find(sym, "property")}
        body = []
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == "property" and e[1] in child_props:
                body.append(child_props.pop(e[1]))
            elif isinstance(e, list) and e[0] == "symbol":
                # Sub-unit names carry the symbol name as prefix.
                sub = list(e)
                sub[1] = Q(re.sub(r"^.*?(_\d+_\d+)$", name + r"\1", sub[1]))
                body.append(sub)
            else:
                body.append(e)
        body += list(child_props.values())
        sym = ["symbol", Q(name)] + body
    else:
        sym = list(sym)
    sym[1] = Q(name)
    return sym


def pins(sym):
    """List pins: dicts with number, name, type, unit, x, y, angle, length."""
    out = []
    for sub in find(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", sub[1])
        unit, style = int(m.group(1)), int(m.group(2))
        if style > 1:
            continue  # skip De Morgan alternates
        for p in find(sub, "pin"):
            at = find1(p, "at")
            out.append(dict(
                number=find1(p, "number")[1], name=find1(p, "name")[1],
                type=p[1], unit=unit, x=float(at[1]), y=float(at[2]),
                angle=float(at[3]) if len(at) > 3 else 0.0,
                length=float(find1(p, "length")[1]),
                hidden=any(e == "hide" or (isinstance(e, list) and e[0] == "hide" and e[1] == "yes") for e in p)))
    return out


def prop(sym, key):
    for p in find(sym, "property"):
        if p[1] == key:
            return str(p[2])
    return None


if __name__ == "__main__":
    import sys
    for arg in sys.argv[1:]:
        lib, name = arg.split(":")
        s = load_symbol(lib, name)
        print(f"== {arg}  fp={prop(s, 'Footprint')}")
        for p in sorted(pins(s), key=lambda p: (p["unit"], p["number"].zfill(4))):
            print(f"  u{p['unit']} {p['number']:>4} {p['name']:<14} {p['type']}")
