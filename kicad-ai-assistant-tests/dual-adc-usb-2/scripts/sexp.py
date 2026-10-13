"""Minimal S-expression reader/writer for KiCad files."""
import re
_tok = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')

class Q(str):
    """Quoted string atom."""

def parse(text):
    stack, cur = [], []
    pos = 0
    while True:
        m = _tok.match(text, pos)
        if not m or m.end() == pos:
            break
        pos = m.end()
        o, c, q, a = m.groups()
        if o:
            stack.append(cur); cur = []
        elif c:
            done = cur; cur = stack.pop(); cur.append(done)
        elif q is not None:
            cur.append(Q(q[1:-1].replace('\\"', '"').replace('\\\\', '\\')))
        else:
            cur.append(a)
    return cur[0]

def dump(x, ind=0):
    if isinstance(x, list):
        simple = all(not isinstance(e, list) for e in x)
        if simple:
            return "(" + " ".join(dump(e) for e in x) + ")"
        out = "(" + " ".join(dump(e) for e in x if not isinstance(e, list))
        for e in x:
            if isinstance(e, list):
                out += "\n" + "\t" * (ind + 1) + dump(e, ind + 1)
        return out + "\n" + "\t" * ind + ")"
    if isinstance(x, Q):
        return '"' + x.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return str(x)

def find(x, key):
    return [e for e in x if isinstance(e, list) and e and e[0] == key]

def find1(x, key):
    r = find(x, key); return r[0] if r else None
