"""Route the few connections Freerouting leaves open (KiCad python).

Reads the unconnected-item pairs from a kicad-cli DRC report, then runs a
small grid A* on F.Cu/B.Cu (with through vias) between each pair, treating
other nets' pads, tracks and vias as obstacles. Zones are ignored as
obstacles (they are refilled afterwards).

usage: python3.11 fix_unrouted.py route/drcN.rpt
"""

import heapq
import math
import os
import re
import sys

import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
PCB = os.path.join(HERE, "..", "kicad", "dual_adc.kicad_pcb")
STEP = 0.1                     # grid, mm
CLR = 0.15                     # clearance (the board rule)
VIA_D, VIA_DR = 0.45, 0.2
POWER = {"+5V", "VBUS", "VBUS_F", "+1V2", "+4V", "-4V", "LM_CP", "LM_CPF", "LM_CN",
         "FT_VPHY", "VCCPLL0", "VCCPLL1", "OSC_VDD", "FT_VCCA", "FT_VCORE"}
mm = pcbnew.FromMM

rpt = open(sys.argv[1]).read()
pairs = []
for blk in re.findall(r"\[unconnected_items\].*?(?=\n\[|\Z)", rpt, re.S):
    pts = re.findall(r"@\(([\d.]+) mm, ([\d.]+) mm\): [^\n]*?\[([^\]]+)\][^\n]*? on ([^\n]*)", blk)
    if len(pts) >= 2:
        def lays(t):
            return [i for i, L in enumerate(("F.Cu", "B.Cu")) if L in t] or [0]
        (x0, y0, n0, l0), (x1, y1, n1, l1) = pts[:2]
        pairs.append((n0, (float(x0), float(y0)), (float(x1), float(y1)), lays(l0), lays(l1)))
print("pairs", pairs)

board = pcbnew.LoadBoard(PCB)
LAYERS = [pcbnew.F_Cu, pcbnew.B_Cu]


def route(net, a, b, la, lb):
    w = 0.2                    # fine-pitch escapes; short links only
    infl = CLR + w / 2
    x0, x1 = min(a[0], b[0]) - 8, max(a[0], b[0]) + 8
    y0, y1 = min(a[1], b[1]) - 8, max(a[1], b[1]) + 8
    nx, ny = int((x1 - x0) / STEP) + 1, int((y1 - y0) / STEP) + 1
    blocked = [bytearray(nx * ny) for _ in LAYERS]
    viablk = bytearray(nx * ny)

    def mark_rect(li, rx0, ry0, rx1, ry1, grow, arr=None):
        """Block cells whose centre lies within `grow` (Euclidean) of the rect."""
        arr = arr if arr is not None else blocked[li]
        i0 = max(0, int(math.floor((rx0 - grow - x0) / STEP)))
        i1 = min(nx - 1, int(math.ceil((rx1 + grow - x0) / STEP)))
        j0 = max(0, int(math.floor((ry0 - grow - y0) / STEP)))
        j1 = min(ny - 1, int(math.ceil((ry1 + grow - y0) / STEP)))
        g2 = grow * grow
        for j in range(j0, j1 + 1):
            cy = y0 + j * STEP
            dy = max(ry0 - cy, 0.0, cy - ry1)
            row = j * nx
            for i in range(i0, i1 + 1):
                cx = x0 + i * STEP
                dx = max(rx0 - cx, 0.0, cx - rx1)
                if dx * dx + dy * dy <= g2:
                    arr[row + i] = 1

    def mark_seg(li, sx, sy, ex, ey, r, arr=None):
        L = math.hypot(ex - sx, ey - sy)
        n = max(1, int(L / (STEP / 2)))
        for k in range(n + 1):
            t = k / n
            cx, cy = sx + (ex - sx) * t, sy + (ey - sy) * t
            mark_rect(li, cx, cy, cx, cy, r, arr)

    via_grow = CLR + VIA_D / 2
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.GetNetname() == net:
                continue
            bb = p.GetBoundingBox()
            r = (bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6)
            for li, L in enumerate(LAYERS):
                if p.IsOnLayer(L):
                    mark_rect(li, *r, infl)
                    mark_rect(li, *r, via_grow, viablk)
            if p.GetDrillSize().x > 0:
                mark_rect(0, *r, via_grow + 0.1, viablk)
    if os.environ.get("DBG"):
        print("after pads blocked", sum(blocked[0]), "of", nx * ny)
    for t in board.Tracks():
        if t.GetNetname() == net:
            continue
        if t.GetClass() == "PCB_VIA":
            c = t.GetPosition()
            r = t.GetWidth(pcbnew.F_Cu) / 2e6 if hasattr(t, "GetWidth") else 0.225
            for li in range(2):
                mark_rect(li, c.x / 1e6, c.y / 1e6, c.x / 1e6, c.y / 1e6, r + infl)
            mark_rect(0, c.x / 1e6, c.y / 1e6, c.x / 1e6, c.y / 1e6, r + via_grow + 0.05, viablk)
        else:
            li = LAYERS.index(t.GetLayer()) if t.GetLayer() in LAYERS else None
            if li is None:
                continue
            s, e = t.GetStart(), t.GetEnd()
            r = t.GetWidth() / 2e6
            mark_seg(li, s.x / 1e6, s.y / 1e6, e.x / 1e6, e.y / 1e6, r + infl)
            mark_seg(li, s.x / 1e6, s.y / 1e6, e.x / 1e6, e.y / 1e6, r + via_grow, viablk)
    if os.environ.get("DBG"):
        print("after tracks blocked", sum(blocked[0]), "of", nx * ny)
    # board edge
    bb = board.GetBoardEdgesBoundingBox()
    ex0, ey0, ex1, ey1 = bb.GetLeft() / 1e6 + 0.4, bb.GetTop() / 1e6 + 0.4, bb.GetRight() / 1e6 - 0.4, bb.GetBottom() / 1e6 - 0.4

    def cell(p):
        return int(round((p[0] - x0) / STEP)), int(round((p[1] - y0) / STEP))

    def ok(li, i, j):
        if not (0 <= i < nx and 0 <= j < ny):
            return False
        x, y = x0 + i * STEP, y0 + j * STEP
        if not (ex0 < x < ex1 and ey0 < y < ey1):
            return False
        return not blocked[li][j * nx + i]

    # Start/end may sit on any layer their item is on; free a small disc there.
    sa, sb = cell(a), cell(b)
    for (ci, cj) in (sa, sb):
        for li in range(2):
            for dj in range(-2, 3):
                for di in range(-2, 3):
                    ii, jj = ci + di, cj + dj
                    if 0 <= ii < nx and 0 <= jj < ny:
                        blocked[li][jj * nx + ii] = 0
    starts = [(l, sa[0], sa[1]) for l in la]
    goal = {(l, sb[0], sb[1]) for l in lb}
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1),
             (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    h = lambda i, j: math.hypot(i - sb[0], j - sb[1])
    openq, came, g = [], {}, {}
    for s in starts:
        g[s] = 0
        heapq.heappush(openq, (h(s[1], s[2]), s))
    found = None
    while openq:
        f, cur = heapq.heappop(openq)
        if cur in goal:
            found = cur
            break
        li, i, j = cur
        for di, dj, c in moves:
            nxt = (li, i + di, j + dj)
            if not ok(*nxt):
                continue
            ng = g[cur] + c
            if ng < g.get(nxt, 1e18):
                g[nxt], came[nxt] = ng, cur
                heapq.heappush(openq, (ng + h(nxt[1], nxt[2]), nxt))
        nxt = (1 - li, i, j)
        if ok(*nxt) and not viablk[j * nx + i]:
            ng = g[cur] + 25
            if ng < g.get(nxt, 1e18):
                g[nxt], came[nxt] = ng, cur
                heapq.heappush(openq, (ng + h(i, j), nxt))
    if not found:
        print("FAILED", net, a, b, "expanded", len(g), "start ok", [ok(*s) for s in starts],
              "goal ok", [ok(*q) for q in goal], "edge", (ex0, ey0, ex1, ey1), "win", (x0, y0, nx, ny))
        if os.environ.get("DBG"):
            for jj in range(sa[1] - 6, sa[1] + 7):
                print("".join("S" if (ii, jj) == sa else "#" if blocked[0][jj * nx + ii] else "."
                              for ii in range(sa[0] - 10, sa[0] + 14)))
        return False
    path = [found]
    while path[-1] in came:
        path.append(came[path[-1]])
    path.reverse()
    ni = board.FindNet(net)
    # Emit segments, merging collinear steps.
    def xy(n):
        return pcbnew.VECTOR2I(mm(x0 + n[1] * STEP), mm(y0 + n[2] * STEP))
    k = 0
    pts = [pcbnew.VECTOR2I(mm(a[0]), mm(a[1]))]
    segs = []
    seg_start = path[0]
    for idx in range(1, len(path)):
        p, q = path[idx - 1], path[idx]
        if p[0] != q[0]:
            if seg_start != p:
                segs.append((p[0], seg_start, p))
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(xy(p)); v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DR))
            v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            v.SetNet(ni); board.Add(v)
            seg_start = q
            continue
        if idx + 1 < len(path):
            r = path[idx + 1]
            if r[0] == q[0] and (r[1] - q[1], r[2] - q[2]) == (q[1] - p[1], q[2] - p[2]):
                continue
        segs.append((q[0], seg_start, q))
        seg_start = q
    for li, s, e in segs:
        if s == e:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(xy(s)); t.SetEnd(xy(e)); t.SetWidth(mm(w))
        t.SetLayer(LAYERS[li]); t.SetNet(ni); board.Add(t)
    # Join exact endpoints to the grid-snapped path ends.
    for (pt, node) in ((a, path[0]), (b, path[-1])):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(mm(pt[0]), mm(pt[1]))); t.SetEnd(xy(node))
        t.SetWidth(mm(w)); t.SetLayer(LAYERS[node[0]]); t.SetNet(ni); board.Add(t)
    print("routed", net, len(segs), "segments")
    return True


# Shortest, most constrained first (flying-cap pins before the rails around them).
FIRST = ["LM_CPF", "LM_CN", "+4V"]
pairs.sort(key=lambda p: (FIRST.index(p[0]) if p[0] in FIRST else 9, math.dist(p[1], p[2])))
for net, a, b, la, lb in pairs:
    route(net, a, b, la, lb)
pcbnew.ZONE_FILLER(board).Fill(board.Zones())
board.Save(PCB)
