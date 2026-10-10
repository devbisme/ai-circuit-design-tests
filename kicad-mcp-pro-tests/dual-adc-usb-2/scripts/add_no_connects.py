"""Add no_connect markers to every pin KiCad reports as unconnected.

Reads 'unconnected-(REF-NAME-PadN)' nets from a kicad-cli netlist, locates each pin
in the sheet files (symbol placement + embedded lib_symbols pin coordinates), and
inserts (no_connect ...) items. The sch_build_circuit tool has no NC support.
"""
import re, sys, uuid, math, pathlib

def blocks(text, head):
    """Yield (start, end) of balanced s-expr blocks starting with head."""
    i = 0
    while (i := text.find(head, i)) >= 0:
        d = 0
        i = text.index('(', i)
        for j in range(i, len(text)):
            d += {'(': 1, ')': -1}.get(text[j], 0)
            if d == 0:
                yield i, j + 1
                break
        i = j + 1

proj = pathlib.Path(sys.argv[1]); netfile = sys.argv[2]
want = {}
for ref, pad in re.findall(r'unconnected-\((\w+?)[A-E]?-.*?-Pad(\w+)\)', open(netfile).read()):
    want.setdefault(ref, set()).add(pad)
# fix refs like U501A -> U501 (unit letter); ambiguous ones are also tried verbatim
for f in sorted(proj.glob('*.kicad_sch')):
    t = f.read_text()
    libs = {}
    ls = t.find('(lib_symbols')
    for s, e in blocks(t[ls:], '(symbol "'):
        blk = t[ls + s:ls + e]
        name = re.match(r'\(symbol "([^"]+)"', blk).group(1)
        if ':' not in name: continue
        pins = {}
        for us, ue in blocks(blk[1:], '(symbol "'):   # skip the block itself
            sub = blk[1 + us:1 + ue]
            m = re.match(r'\(symbol "[^"]+_(\d+)_(\d+)"', sub)
            if not m: continue
            for px, py, num in re.findall(r'\(pin \w+ \w+\s*\(at ([-\d.]+) ([-\d.]+) \d+\).*?\(number "([^"]+)"', sub, re.S):
                pins[(int(m.group(1)), num)] = (float(px), float(py))
        libs[name] = pins
    adds = []
    body = t[t.find(')', t.find('(lib_symbols')):]
    for s, e in blocks(t, '\n\t(symbol\n'):
        blk = t[s:e]
        lib = re.search(r'\(lib_id "([^"]+)"', blk).group(1)
        x, y, rot = map(float, re.search(r'\(at ([-\d.]+) ([-\d.]+) ([-\d.]+)\)', blk).groups())
        unit = int(re.search(r'\(unit (\d+)\)', blk).group(1))
        ref = re.search(r'\(property "Reference" "([^"]+)"', blk).group(1)
        for pad in want.get(ref, ()):
            p = libs[lib].get((unit, pad)) or libs[lib].get((0, pad))
            if p is None: continue
            a = math.radians(rot); px, py = p[0], -p[1]
            adds.append((round(x + px*math.cos(a) + py*math.sin(a), 2),
                         round(y - px*math.sin(a) + py*math.cos(a), 2), ref, pad))
    if adds:
        nc = ''.join(f'\t(no_connect\n\t\t(at {ax} {ay})\n\t\t(uuid "{uuid.uuid4()}")\n\t)\n' for ax, ay, *_ in adds)
        k = t.rfind('\t(sheet_instances') if '(sheet_instances' in t else t.rfind(')')
        t = t[:k] + nc + t[k:]
        f.write_text(t)
        print(f.name, [(r, p) for *_, r, p in adds])
