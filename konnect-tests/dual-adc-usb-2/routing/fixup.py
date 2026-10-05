"""Route the connections KiCad DRC reports as unconnected, using a small 2-layer A* grid router.
usage: fixup.py in.kicad_pcb drc.json out.kicad_pcb
Obstacles: every copper item of another net (pads by bbox, tracks as segments, vias as circles),
inflated by clearance + half the new track width (or via radius for via cells)."""
import heapq, json, math, sys
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

SRC, DRC, OUT = sys.argv[1:4]
G = 0.1; CLR = 0.16; W = 0.2; VIA_D, VIA_DR = 0.6, 0.3; VIA_COST = 25; MARGIN = float(sys.argv[4]) if len(sys.argv) > 4 else 6.0
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]

b = pcbnew.LoadBoard(SRC)
byuuid = {}
for t in b.GetTracks(): byuuid[t.m_Uuid.AsString()] = t
for fp in b.GetFootprints():
    for p in fp.Pads(): byuuid[p.m_Uuid.AsString()] = p

def items():
    for fp in b.GetFootprints():
        for p in fp.Pads():
            if not p.IsOnCopperLayer(): continue
            bb = p.GetBoundingBox()
            lay = [l for l in LAYERS if p.IsOnLayer(l)]
            yield ('rect', p.GetNetname(), lay, (ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom())))
    for t in b.GetTracks():
        if t.GetClass() == 'PCB_VIA':
            yield ('circ', t.GetNetname(), LAYERS, (ToMM(t.GetPosition().x), ToMM(t.GetPosition().y), ToMM(t.GetWidth(pcbnew.F_Cu)) / 2))
        else:
            if t.GetLayer() in LAYERS:
                yield ('seg', t.GetNetname(), [t.GetLayer()], (ToMM(t.GetStart().x), ToMM(t.GetStart().y), ToMM(t.GetEnd().x), ToMM(t.GetEnd().y), ToMM(t.GetWidth()) / 2))
ALL = list(items())

def dist(kind, g, x, y):
    if kind == 'rect':
        return math.hypot(max(g[0] - x, 0, x - g[2]), max(g[1] - y, 0, y - g[3]))
    if kind == 'circ':
        return max(0.0, math.hypot(x - g[0], y - g[1]) - g[2])
    x0, y0, x1, y1, hw = g; dx, dy = x1 - x0, y1 - y0; L = dx * dx + dy * dy
    t = 0 if L == 0 else max(0, min(1, ((x - x0) * dx + (y - y0) * dy) / L))
    return max(0.0, math.hypot(x - x0 - t * dx, y - y0 - t * dy) - hw)

def bbox(kind, g):
    if kind == 'rect': return g
    if kind == 'circ': return (g[0] - g[2], g[1] - g[2], g[0] + g[2], g[1] + g[2])
    return (min(g[0], g[2]) - g[4], min(g[1], g[3]) - g[4], max(g[0], g[2]) + g[4], max(g[1], g[3]) + g[4])

def route(net, a, b_, la, lb):
    x0 = min(a[0], b_[0]) - MARGIN; y0 = min(a[1], b_[1]) - MARGIN
    nx = int((abs(a[0] - b_[0]) + 2 * MARGIN) / G) + 1; ny = int((abs(a[1] - b_[1]) + 2 * MARGIN) / G) + 1
    blocked = [set(), set()]; viablk = set()
    tr = CLR + W / 2; vr = CLR + VIA_D / 2
    for kind, n, lays, g in ALL:
        if n == net: continue
        bx = bbox(kind, g)
        for li, L in enumerate(LAYERS):
            if L not in lays: continue
            for r, tgt in ((tr, blocked[li]), (vr, viablk)):
                i0 = max(0, int((bx[0] - r - x0) / G)); i1 = min(nx - 1, int((bx[2] + r - x0) / G) + 1)
                j0 = max(0, int((bx[1] - r - y0) / G)); j1 = min(ny - 1, int((bx[3] + r - y0) / G) + 1)
                for i in range(i0, i1 + 1):
                    for j in range(j0, j1 + 1):
                        if (i, j) not in tgt and dist(kind, g, x0 + i * G, y0 + j * G) < r:
                            tgt.add((i, j))
    # board edge keepout
    def inside(i, j):
        x, y = x0 + i * G, y0 + j * G
        return 50.6 < x < 189.4 and 50.6 < y < 139.4
    S = (round((a[0] - x0) / G), round((a[1] - y0) / G)); T = (round((b_[0] - x0) / G), round((b_[1] - y0) / G))
    starts = [(S[0], S[1], li) for li, L in enumerate(LAYERS) if L in la]
    goals = {(T[0], T[1], li) for li, L in enumerate(LAYERS) if L in lb}
    # free the immediate neighbourhood of the endpoints (they sit on own-net copper whose
    # inflated neighbours may already be blocked by adjacent-pin clearance)
    def free(c, li):
        return 0 <= c[0] < nx and 0 <= c[1] < ny and inside(*c) and (c not in blocked[li] or
               (abs(c[0]-S[0]) <= 1 and abs(c[1]-S[1]) <= 1) or (abs(c[0]-T[0]) <= 1 and abs(c[1]-T[1]) <= 1))
    h = lambda c: math.hypot(c[0] - T[0], c[1] - T[1])
    pq = [(h(s), 0.0, s, None) for s in starts]; came = {}; gbest = {s: 0.0 for s in starts}
    while pq:
        f, gc, c, par = heapq.heappop(pq)
        if c in came: continue
        came[c] = par
        if c in goals:
            path = [c]
            while came[path[-1]] is not None: path.append(came[path[-1]])
            return path[::-1], x0, y0
        i, j, li = c
        for di, dj in ((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
            n_ = (i + di, j + dj, li)
            if not free(n_[:2], li): continue
            ng = gc + math.hypot(di, dj)
            if ng < gbest.get(n_, 1e18):
                gbest[n_] = ng; heapq.heappush(pq, (ng + h(n_), ng, n_, c))
        if (i, j) not in viablk and math.hypot(i - S[0], j - S[1]) > 6 and math.hypot(i - T[0], j - T[1]) > 6:
            n_ = (i, j, 1 - li); ng = gc + VIA_COST
            if free((i, j), 1 - li) and ng < gbest.get(n_, 1e18):
                gbest[n_] = ng; heapq.heappush(pq, (ng + h(n_), ng, n_, c))
    return None, x0, y0

def emit(net, path, x0, y0, a, b_):
    no = b.FindNet(net); pts = [(x0 + c[0] * G, y0 + c[1] * G, c[2]) for c in path]
    pts[0] = (a[0], a[1], pts[0][2]); pts[-1] = (b_[0], b_[1], pts[-1][2])
    # compress collinear runs per layer, insert vias on layer changes
    segs = []; start = pts[0]; prev = pts[0]; d = None
    for p in pts[1:]:
        if p[2] != prev[2]:
            if (start[0], start[1]) != (prev[0], prev[1]): segs.append((start, prev))
            v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(FromMM(prev[0]), FromMM(prev[1])))
            v.SetWidth(FromMM(VIA_D)); v.SetDrill(FromMM(VIA_DR)); v.SetNet(no); b.Add(v)
            ALL.append(('circ', net, LAYERS, (prev[0], prev[1], VIA_D / 2)))
            start = (prev[0], prev[1], p[2]); prev = start; d = None
        nd = (round((p[0] - prev[0]) / G), round((p[1] - prev[1]) / G))
        if d is not None and nd != d:
            segs.append((start, prev)); start = prev
        d = nd; prev = p
    segs.append((start, prev))
    for s, e in segs:
        t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(FromMM(s[0]), FromMM(s[1]))); t.SetEnd(VECTOR2I(FromMM(e[0]), FromMM(e[1])))
        t.SetWidth(FromMM(W)); t.SetLayer(LAYERS[s[2]]); t.SetNet(no); b.Add(t)
        ALL.append(('seg', net, [LAYERS[s[2]]], (s[0], s[1], e[0], e[1], W / 2)))
    return len(segs)

def anchor(it, other):
    o = byuuid[it['uuid']]; ox, oy = other
    if o.GetClass() == 'PAD':
        P = o.GetPosition(); return (ToMM(P.x), ToMM(P.y)), [l for l in LAYERS if o.IsOnLayer(l)], o.GetNetname()
    if o.GetClass() == 'PCB_VIA':
        P = o.GetPosition(); return (ToMM(P.x), ToMM(P.y)), LAYERS, o.GetNetname()
    ends = [(ToMM(o.GetStart().x), ToMM(o.GetStart().y)), (ToMM(o.GetEnd().x), ToMM(o.GetEnd().y))]
    e = min(ends, key=lambda q: math.hypot(q[0] - ox, q[1] - oy)); return e, [o.GetLayer()], o.GetNetname()

d = json.load(open(DRC))
for u in d['unconnected_items']:
    A, B = u['items']
    pa = (A['pos']['x'] * 100, A['pos']['y'] * 100); pb = (B['pos']['x'] * 100, B['pos']['y'] * 100)
    a, la, net = anchor(A, pb); b_, lb, _ = anchor(B, a)
    path, x0, y0 = route(net, a, b_, la, lb)
    if path is None:
        print('FAILED', net, a, b_); continue
    n = emit(net, path, x0, y0, a, b_)
    vias = sum(1 for p, q in zip(path, path[1:]) if p[2] != q[2])
    print('routed', net, a, '->', b_, 'segs', n, 'vias', vias)
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(OUT, b)
