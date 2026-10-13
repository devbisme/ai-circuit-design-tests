"""Minimal s-expression reader/writer and KiCad symbol-library loader."""
import re
from pathlib import Path

SYMDIR = Path.home() / "bin/kicad10-root/share/kicad/symbols"   # KiCad 10 .kicad_symdir libraries

_tok = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')


class Q(str):
    """A string that must be written quoted."""


def parse(text):
    stack, cur = [], []
    pos = 0
    while True:
        m = _tok.match(text, pos)
        if not m:
            break
        pos = m.end()
        lp, rp, qs, atom = m.groups()
        if lp:
            stack.append(cur)
            cur = []
        elif rp:
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif qs is not None:
            cur.append(Q(qs[1:-1].replace('\\"', '"').replace("\\\\", "\\")))
        else:
            cur.append(atom)
    return cur[0]


def dump(x, ind=0):
    if isinstance(x, list):
        simple = all(not isinstance(e, list) for e in x)
        if simple:
            return "(" + " ".join(dump(e) for e in x) + ")"
        out = "(" + dump(x[0])
        for e in x[1:]:
            if isinstance(e, list):
                out += "\n" + "\t" * (ind + 1) + dump(e, ind + 1)
            else:
                out += " " + dump(e)
        return out + "\n" + "\t" * ind + ")"
    if isinstance(x, Q):
        return '"' + x.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(x, float):
        s = f"{x:.4f}".rstrip("0").rstrip(".")
        return "0" if s in ("-0", "") else s
    return str(x)


def find(node, key):
    return [e for e in node if isinstance(e, list) and e and e[0] == key]


def find1(node, key):
    r = find(node, key)
    return r[0] if r else None


_libcache = {}


class _SymDir(dict):
    """Lazily parsed KiCad 10 symbol directory: one .kicad_sym file per symbol."""
    def __init__(self, lib):
        super().__init__()
        self.dir = SYMDIR / f"{lib}.kicad_symdir"

    def __missing__(self, name):
        tree = parse((self.dir / f"{name}.kicad_sym").read_text())
        for e in find(tree, "symbol"):
            self[e[1]] = e
        return dict.__getitem__(self, name)


def _lib(lib):
    if lib not in _libcache:
        _libcache[lib] = _SymDir(lib)
    return _libcache[lib]


def load_symbol(lib_id):
    """Return a flattened (no `extends`) symbol node named lib_id."""
    lib, name = lib_id.split(":")
    syms = _lib(lib)
    node = syms[name]
    ext = find1(node, "extends")
    if ext:
        parent = load_symbol(f"{lib}:{ext[1]}")
        pname = ext[1]
        child_props = {p[1]: p for p in find(node, "property")}
        new = [Q("symbol"), Q(lib_id)]
        new[0] = "symbol"
        for e in parent[2:]:
            if isinstance(e, list) and e[0] == "property" and e[1] in child_props:
                new.append(child_props.pop(e[1]))
            elif isinstance(e, list) and e[0] == "symbol":
                sub = [e[0], Q(e[1].replace(pname.split(":")[-1], name, 1))] + e[2:]
                new.append(sub)
            else:
                new.append(e)
        # child-only properties go before sub-symbols
        idx = max(i for i, e in enumerate(new) if isinstance(e, list) and e[0] == "property") + 1
        for p in child_props.values():
            new.insert(idx, p)
            idx += 1
        return new
    new = ["symbol", Q(lib_id)] + node[2:]
    return new


def symbol_pins(sym):
    """List of dicts: number, name, type, x, y, rot, unit (0 = all units)."""
    name = sym[1].split(":")[-1]
    pins = []
    for sub in find(sym, "symbol"):
        m = re.match(re.escape(name) + r"_(\d+)_(\d+)$", sub[1])
        if not m:
            continue
        unit, style = int(m.group(1)), int(m.group(2))
        if style > 1:
            continue
        for p in find(sub, "pin"):
            at = find1(p, "at")
            pins.append(dict(number=str(find1(p, "number")[1]), name=str(find1(p, "name")[1]),
                             type=p[1], x=float(at[1]), y=float(at[2]),
                             rot=float(at[3]) if len(at) > 3 else 0.0,
                             length=float(find1(p, "length")[1]), unit=unit))
    return pins


def symbol_units(sym):
    us = {p["unit"] for p in symbol_pins(sym)}
    us.discard(0)
    return sorted(us) or [1]


def symbol_bbox(sym, unit):
    """Rough bbox in lib coords (y up) of graphics + pins for a unit."""
    name = sym[1].split(":")[-1]
    xs, ys = [0.0], [0.0]

    def walk(n):
        if isinstance(n, list):
            if n and n[0] in ("xy", "start", "end", "center"):
                try:
                    xs.append(float(n[1])); ys.append(float(n[2]))
                except (ValueError, IndexError):
                    pass
            for e in n:
                walk(e)
    for sub in find(sym, "symbol"):
        m = re.match(re.escape(name) + r"_(\d+)_(\d+)$", sub[1])
        if m and int(m.group(1)) in (0, unit) and int(m.group(2)) <= 1:
            for e in sub:
                if isinstance(e, list) and e[0] in ("rectangle", "polyline", "circle", "arc"):
                    walk(e)
    for p in symbol_pins(sym):
        if p["unit"] in (0, unit):
            xs.append(p["x"]); ys.append(p["y"])
    return min(xs), min(ys), max(xs), max(ys)
