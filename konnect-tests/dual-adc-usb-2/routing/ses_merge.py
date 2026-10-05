"""Merge the fixed (locked) plane fanout wires/vias from the DSN wiring into a Freerouting SES.

Freerouting omits (type fix) items from its SES output; KiCad's SES import replaces unlocked
tracks, so the fanout must be present in the SES to survive import.
usage: ses_merge.py prep.dsn route.ses merged.ses SCALE
SCALE = SES units per DSN unit (determined by comparing resolutions).
"""
import re, sys

dsn, ses, out, scale = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4])
d = open(dsn).read()
wiring = d[d.index('(wiring'):]

by_net = {}
for m in re.finditer(r'\(wire \(path (\S+) (\S+)\s+([-\d.\s]+)\)\(net ([^)]+)\)\(type fix\)\)', wiring):
    layer, width, coords, net = m.groups()
    xs = [float(v) * scale for v in coords.split()]
    pts = ' '.join('%d %d' % (xs[i], xs[i + 1]) for i in range(0, len(xs), 2))
    by_net.setdefault(net, []).append('(wire (path %s %d %s))' % (layer, float(width) * scale, pts))
for m in re.finditer(r'\(via ("[^"]+") ([-\d.]+) ([-\d.]+) \(net ([^)]+)\)\(type fix\)\)', wiring):
    ps, x, y, net = m.groups()
    by_net.setdefault(net, []).append('(via %s %d %d)' % (ps, float(x) * scale, float(y) * scale))

s = open(ses).read()
added = 0
for net, items in by_net.items():
    key = '(net %s\n' % net if '(net %s\n' % net in s else None
    block = '\n'.join('        ' + it for it in items) + '\n'
    if key:
        i = s.index(key) + len(key)
        s = s[:i] + block + s[i:]
    else:
        i = s.index('(network_out') + len('(network_out')
        s = s[:i] + '\n      (net %s\n%s      )' % (net, block) + s[i:]
    added += len(items)
open(out, 'w').write(s)
print('merged items:', added, 'nets:', len(by_net))
