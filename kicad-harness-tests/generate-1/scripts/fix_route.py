"""Run with KiCad 10 python. Repair what Freerouting left: route DRC 'unconnected_items' pairs with a
small grid A* on F.Cu/B.Cu, and delete dangling vias.

usage: python3.11 fix_route.py <board.kicad_pcb> <drc.json>
"""
import heapq
import json
import math
import sys
from pathlib import Path

import pcbnew

BOARD, DRC = Path(sys.argv[1]), Path(sys.argv[2])
PRO = BOARD.with_suffix(".kicad_pro")
pro_text = PRO.read_text()
mm, to = pcbnew.FromMM, pcbnew.ToMM
STEP, W, CLR, VIA_D, VIA_DRILL = 0.05, 0.15, 0.16, 0.45, 0.2
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]
if len(sys.argv) > 5 and sys.argv[5] == "in2":     # last resort: allow short runs inside the +3V3 plane layer
    LAYERS.append(pcbnew.In2_Cu)

b = pcbnew.LoadBoard(str(BOARD))
d = json.loads(DRC.read_text())
# KiCad 10 SWIG: BOARD.Tracks() stops being iterable after Remove(); snapshot once, mutate at the end.
TRACKS = list(b.GetTracks())


def samples(kind):
    for t in d["violations"]["by_type"] + d.get("unconnected", {}).get("by_type", []):
        if t["type"] == kind:
            yield from t["samples"]


# ---------------------------------------------------------------- dangling vias (removed at the end)
to_remove = []
for s_ in samples("via_dangling"):
    a = s_["at"][0]
    for t in TRACKS:
        if t.GetClass() == "PCB_VIA" and not t.IsLocked():
            p = t.GetPosition()
            if abs(to(p.x) - a["x"]) < 0.01 and abs(to(p.y) - a["y"]) < 0.01:
                to_remove.append(t)
TRACKS = [t for t in TRACKS if not any(t is r for r in to_remove)]


# ---------------------------------------------------------------- copper model
def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - ax - t * dx, py - ay - t * dy)


SHAPES = None


def shapes():
    global SHAPES
    if SHAPES is None:
        SHAPES = _shapes()
    return SHAPES


def _shapes():
    """(layer, netcode, kind, geom)"""
    out = []
    for f in b.GetFootprints():
        for p in f.Pads():
            bb = p.GetBoundingBox()
            box = (to(bb.GetLeft()), to(bb.GetTop()), to(bb.GetRight()), to(bb.GetBottom()))
            th = p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            for L in LAYERS:
                if th or p.IsOnLayer(L):
                    out.append((L, p.GetNetCode(), "box", box))
    for t in TRACKS:
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            for L in LAYERS:
                out.append((L, t.GetNetCode(), "circ", (to(c.x), to(c.y), to(t.GetWidth(pcbnew.F_Cu)) / 2)))
        else:
            if t.GetLayer() in LAYERS:
                s, e = t.GetStart(), t.GetEnd()
                out.append((t.GetLayer(), t.GetNetCode(), "seg", (to(s.x), to(s.y), to(e.x), to(e.y), to(t.GetWidth()) / 2)))
    return out


def dist(x, y, kind, g):
    if kind == "box":
        dx = max(g[0] - x, 0, x - g[2]); dy = max(g[1] - y, 0, y - g[3])
        return math.hypot(dx, dy)
    if kind == "circ":
        return math.hypot(x - g[0], y - g[1]) - g[2]
    return seg_dist(x, y, g[0], g[1], g[2], g[3]) - g[4]


edge = b.GetBoardEdgesBoundingBox()
EX0, EY0, EX1, EY1 = to(edge.GetLeft()) + 0.4, to(edge.GetTop()) + 0.4, to(edge.GetRight()) - 0.4, to(edge.GetBottom()) - 0.4


def route(net, ax, ay, bx, by, a_layers, b_layers):
    M = float(sys.argv[3]) if len(sys.argv) > 3 else 2.5     # search-window margin, mm
    x0, y0 = min(ax, bx) - M, min(ay, by) - M
    x1, y1 = max(ax, bx) + M, max(ay, by) + M
    nx, ny = int((x1 - x0) / STEP) + 1, int((y1 - y0) / STEP) + 1
    sh = [s for s in shapes() if s[1] != net]
    near = {L: [s for s in sh if s[0] == L and dist((x0 + x1) / 2, (y0 + y1) / 2, s[2], s[3]) <
                math.hypot(x1 - x0, y1 - y0) / 2 + 1] for L in LAYERS}
    blocked_cache = {}

    def blocked(i, j, li, r):
        key = (i, j, li, r)
        if key in blocked_cache:
            return blocked_cache[key]
        x, y = x0 + i * STEP, y0 + j * STEP
        res = not (EX0 < x < EX1 and EY0 < y < EY1) or any(dist(x, y, s[2], s[3]) < CLR + r for s in near[LAYERS[li]])
        blocked_cache[key] = res
        return res

    gi = lambda x: int(round((x - x0) / STEP))
    gj = lambda y: int(round((y - y0) / STEP))
    start = [(gi(ax), gj(ay), li) for li, L in enumerate(LAYERS) if L in a_layers]
    goal = {(gi(bx), gj(by), li) for li, L in enumerate(LAYERS) if L in b_layers}
    h = lambda i, j: math.hypot(i - gi(bx), j - gj(by))
    openq = [(h(i, j), 0.0, (i, j, li)) for i, j, li in start]
    prev = {s: None for s in start}
    gbest = {s: 0.0 for s in start}
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    # pads themselves are inside other-net clearance zones only for neighbours; allow the first/last 0.3 mm
    free_r = 0.35 / STEP
    while openq:
        f, g, cur = heapq.heappop(openq)
        if cur in goal:
            path = []
            while cur:
                path.append(cur)
                cur = prev[cur]
            return [(x0 + i * STEP, y0 + j * STEP, LAYERS[li]) for i, j, li in reversed(path)]
        if g > gbest.get(cur, 1e9):
            continue
        i, j, li = cur
        nbrs = []
        for di, dj, c in moves:
            nbrs.append(((i + di, j + dj, li), c))
        for ol in range(len(LAYERS)):
            if ol != li:
                nbrs.append(((i, j, ol), 40 if LAYERS[ol] != pcbnew.In2_Cu else 120))
        for nxt, c in nbrs:
            ni, nj, nl = nxt
            if not (0 <= ni < nx and 0 <= nj < ny):
                continue
            near_end = math.hypot(ni - gi(ax), nj - gj(ay)) < free_r or math.hypot(ni - gi(bx), nj - gj(by)) < free_r
            if nl != li:
                if near_end or any(blocked(ni, nj, k, VIA_D / 2) for k in range(len(LAYERS))):
                    continue
            elif not near_end and blocked(ni, nj, nl, W / 2):
                continue
            ng = g + c
            if ng < gbest.get(nxt, 1e9):
                gbest[nxt] = ng
                prev[nxt] = cur
                heapq.heappush(openq, (ng + h(ni, nj), ng, nxt))
    xs = [x0 + k[0] * STEP for k in prev]; ys = [y0 + k[1] * STEP for k in prev]
    print(f"  A* fail: expanded {len(prev)} nodes, x {min(xs):.2f}..{max(xs):.2f}, y {min(ys):.2f}..{max(ys):.2f}")
    return None


def emit(net, path):
    pts = [path[0]]
    for k in range(1, len(path) - 1):
        a, m, c = pts[-1], path[k], path[k + 1]
        if m[2] != a[2] or c[2] != m[2]:
            pts.append(m); continue
        if abs((m[0] - a[0]) * (c[1] - a[1]) - (m[1] - a[1]) * (c[0] - a[0])) > 1e-9:
            pts.append(m)
    pts.append(path[-1])
    for a, c in zip(pts, pts[1:]):
        if a[2] != c[2]:
            v = pcbnew.PCB_VIA(b)
            v.SetPosition(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL)); v.SetNetCode(net)
            b.Add(v)
            for L in LAYERS:
                shapes().append((L, net, "circ", (a[0], a[1], VIA_D / 2)))
        elif (a[0], a[1]) != (c[0], c[1]):
            t = pcbnew.PCB_TRACK(b)
            t.SetStart(pcbnew.VECTOR2I(mm(a[0]), mm(a[1])))
            t.SetEnd(pcbnew.VECTOR2I(mm(c[0]), mm(c[1])))
            t.SetWidth(mm(W)); t.SetLayer(a[2]); t.SetNetCode(net)
            b.Add(t)
            shapes().append((a[2], net, "seg", (a[0], a[1], c[0], c[1], W / 2)))


def item_at(desc, x, y):
    """Return (netcode, (x,y) anchor, layers) for a DRC item description."""
    best = None
    if desc.startswith("Pad"):
        for f in b.GetFootprints():
            for p in f.Pads():
                c = p.GetPosition()
                dd = math.hypot(to(c.x) - x, to(c.y) - y)
                if dd < 0.01:
                    lay = LAYERS if p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH else [L for L in LAYERS if p.IsOnLayer(L)]
                    return p.GetNetCode(), (to(c.x), to(c.y)), lay
    for t in TRACKS:
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            dd = math.hypot(to(c.x) - x, to(c.y) - y)
            if best is None or dd < best[0]:
                best = (dd, t.GetNetCode(), (to(c.x), to(c.y)), LAYERS)
        else:
            s, e = t.GetStart(), t.GetEnd()
            dd = seg_dist(x, y, to(s.x), to(s.y), to(e.x), to(e.y))
            q = min((s, e), key=lambda q: math.hypot(to(q.x) - x, to(q.y) - y))
            if best is None or dd < best[0]:
                best = (dd, t.GetNetCode(), (to(q.x), to(q.y)), [t.GetLayer()])
    return best[1:]


done, failed = 0, []
RIP = sys.argv[4].split(",") if len(sys.argv) > 4 else []
pairs = []
for netname in RIP:          # rip up a net completely and re-route it pad-to-pad (nearest-neighbour chain)
    nc = b.FindNet(netname).GetNetCode()
    for t in TRACKS:
        if t.GetNetCode() == nc and not t.IsLocked():
            to_remove.append(t)
    TRACKS = [t for t in TRACKS if not any(t is r for r in to_remove)]
    SHAPES = None
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.GetNetCode() == nc]
    pts = [(to(p.GetPosition().x), to(p.GetPosition().y), [L for L in LAYERS if p.IsOnLayer(L)]) for p in pads]
    for a_, c_ in zip(pts, pts[1:]):
        pairs.append((nc, a_, c_))
for nc, a_, c_ in pairs:
    path = route(nc, a_[0], a_[1], c_[0], c_[1], a_[2], c_[2])
    if path:
        emit(nc, path); done += 1
    else:
        failed.append((nc, a_[:2], c_[:2]))
for s in ([] if RIP else samples("unconnected_items")):
    (a, c) = s["at"][:2]
    na, pa, la = item_at(a["desc"], a["x"], a["y"])
    nb, pb, lb = item_at(c["desc"], c["x"], c["y"])
    path = route(na, pa[0], pa[1], pb[0], pb[1], la, lb)
    if path:
        emit(na, path)
        done += 1
    else:
        failed.append((a["desc"], c["desc"]))
print(f"routed {done}, failed {len(failed)}: {failed}")
for t in to_remove:
    b.Remove(t)
print("removed dangling vias:", len(to_remove))
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
b.Save(str(BOARD))
PRO.write_text(pro_text)
