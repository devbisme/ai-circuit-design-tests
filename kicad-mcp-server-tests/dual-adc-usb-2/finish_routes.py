"""Route the connections Freerouting left open, with a simple grid A* maze router.

    ~/bin/kicad10-root/bin/python3.11 finish_routes.py <in.kicad_pcb> <drc.rpt> <out.kicad_pcb>

<drc.rpt> is a kicad-cli DRC report of <in.kicad_pcb>; each [unconnected_items] entry
is routed between the two items it names. Grid 0.1 mm; layers F.Cu, In2.Cu, B.Cu
(In1.Cu is the GND plane, crossed only by vias). Pure Python (no numpy in KiCad's Python).
"""

import heapq
import math
import re
import sys

import pcbnew

MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
G = 0.1                      # grid pitch, mm
import os
CLR = float(os.environ.get("ROUTE_CLR", "0.16"))  # blocking clearance (board rule 0.15 + margin)
VIA_D, VIA_DRILL = 0.45, 0.2
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
ALL_CU = [pcbnew.F_Cu, pcbnew.In1_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]
VIA_COST = 25
POWER = {"VBUS", "+5V", "+3V3", "+3V3A", "+3V0A", "-3V3A", "+1V2", "+1V8_FT", "SW_3V3",
         "CPOUT", "CP_P", "CP_N", "VPHY", "VPLL", "VCCPLL0", "VCCPLL1", "OSC_VDD", "GND"}


class Grid:
    def __init__(self, board):
        bb = board.GetBoardEdgesBoundingBox()
        self.x0, self.y0 = TOMM(bb.GetX()), TOMM(bb.GetY())
        self.nx = int(TOMM(bb.GetWidth()) / G) + 1
        self.ny = int(TOMM(bb.GetHeight()) / G) + 1
        n = self.nx * self.ny
        # owner net code per cell for track-blocking and via-blocking (0 = free, -1 = hard block)
        self.trk = {l: [0] * n for l in ALL_CU}
        self.via = {l: [0] * n for l in ALL_CU}
        m = int(0.5 / G) + 1  # board-edge margin
        for l in ALL_CU:
            for iy in range(self.ny):
                for ix in range(self.nx):
                    if ix < m or iy < m or ix >= self.nx - m or iy >= self.ny - m:
                        self.trk[l][iy * self.nx + ix] = -1
                        self.via[l][iy * self.nx + ix] = -1

    def cell(self, x, y):
        return int(round((x - self.x0) / G)), int(round((y - self.y0) / G))

    def xy(self, ix, iy):
        return self.x0 + ix * G, self.y0 + iy * G

    def mark_shape(self, layer, net, dist_fn, bbox, half_w):
        """Mark cells whose distance to the shape is below the track/via keep-out radius."""
        x0, y0, x1, y1 = bbox
        for grid, r in ((self.trk[layer], half_w + CLR), (self.via[layer], VIA_D / 2 + CLR)):
            ix0, iy0 = self.cell(x0 - r, y0 - r)
            ix1, iy1 = self.cell(x1 + r, y1 + r)
            for iy in range(max(iy0, 0), min(iy1 + 1, self.ny)):
                for ix in range(max(ix0, 0), min(ix1 + 1, self.nx)):
                    x, y = self.xy(ix, iy)
                    if dist_fn(x, y) < r:
                        k = iy * self.nx + ix
                        if grid[k] == 0:
                            grid[k] = net
                        elif grid[k] != net:
                            grid[k] = -1


def seg_dist(ax, ay, bx, by, px, py):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)


def rect_dist(x0, y0, x1, y1):
    def f(x, y):
        return math.hypot(max(x0 - x, 0, x - x1), max(y0 - y, 0, y - y1))
    return f


def pad_shape(pad, layer):
    """(dist_fn, bbox) of a pad's copper on layer, from its effective polygon."""
    poly = pad.GetEffectivePolygon(layer, pcbnew.ERROR_INSIDE)
    pts = []
    for i in range(poly.OutlineCount()):
        o = poly.Outline(i)
        pts += [(TOMM(o.CPoint(j).x), TOMM(o.CPoint(j).y)) for j in range(o.PointCount())]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    bbox = (min(xs), min(ys), max(xs), max(ys))
    segs = list(zip(pts, pts[1:] + pts[:1]))

    def inside(x, y):
        c = False
        for (ax, ay), (bx, by) in segs:
            if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay) + ax:
                c = not c
        return c

    def f(x, y):
        if inside(x, y):
            return 0.0
        return min(seg_dist(ax, ay, bx, by, x, y) for (ax, ay), (bx, by) in segs)
    return f, bbox


def build_grid(board):
    g = Grid(board)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            net = pad.GetNetCode() or -1
            for layer in ALL_CU:
                if pad.IsOnLayer(layer):
                    f, bb = pad_shape(pad, layer)
                    g.mark_shape(layer, net, f, bb, 0.075)
            if pad.HasHole():
                hx, hy = TOMM(pad.GetPosition().x), TOMM(pad.GetPosition().y)
                hr = TOMM(max(pad.GetDrillSize().x, pad.GetDrillSize().y)) / 2
                for layer in ALL_CU:
                    g.mark_shape(layer, net, lambda x, y: math.hypot(x - hx, y - hy) - hr,
                                 (hx - hr, hy - hr, hx + hr, hy + hr), 0.075)
    for t in board.GetTracks():
        add_item_to_grid(g, t)
    return g


def add_item_to_grid(g, t):
    net = t.GetNetCode()
    if t.Type() == pcbnew.PCB_VIA_T:
        cx, cy, r = TOMM(t.GetPosition().x), TOMM(t.GetPosition().y), TOMM(t.GetWidth(pcbnew.F_Cu)) / 2
        for layer in ALL_CU:
            g.mark_shape(layer, net, lambda x, y: math.hypot(x - cx, y - cy) - r, (cx - r, cy - r, cx + r, cy + r), 0.075)
    else:
        ax, ay, bx, by = TOMM(t.GetStart().x), TOMM(t.GetStart().y), TOMM(t.GetEnd().x), TOMM(t.GetEnd().y)
        w = TOMM(t.GetWidth()) / 2
        g.mark_shape(t.GetLayer(), net, lambda x, y: seg_dist(ax, ay, bx, by, x, y) - w,
                     (min(ax, bx) - w, min(ay, by) - w, max(ax, bx) + w, max(ay, by) + w), 0.075)


def item_cells(g, item):
    """(layer, ix, iy) cells covered by a pad / track / via (any copper layer it is on)."""
    cells = set()
    if isinstance(item, pcbnew.PAD):
        for layer in LAYERS:
            if item.IsOnLayer(layer):
                f, (x0, y0, x1, y1) = pad_shape(item, layer)
                ix0, iy0 = g.cell(x0, y0)
                ix1, iy1 = g.cell(x1, y1)
                for iy in range(iy0, iy1 + 1):
                    for ix in range(ix0, ix1 + 1):
                        if f(*g.xy(ix, iy)) < -0.0 + 0.02:
                            cells.add((layer, ix, iy))
                if not any(c[0] == layer for c in cells):
                    ix, iy = g.cell(TOMM(item.GetPosition().x), TOMM(item.GetPosition().y))
                    cells.add((layer, ix, iy))
    elif item.Type() == pcbnew.PCB_VIA_T:
        ix, iy = g.cell(TOMM(item.GetPosition().x), TOMM(item.GetPosition().y))
        cells |= {(l, ix, iy) for l in LAYERS}
    else:
        ax, ay, bx, by = TOMM(item.GetStart().x), TOMM(item.GetStart().y), TOMM(item.GetEnd().x), TOMM(item.GetEnd().y)
        n = max(1, int(math.hypot(bx - ax, by - ay) / G))
        if item.GetLayer() in LAYERS:
            for k in range(n + 1):
                cells.add((item.GetLayer(), *g.cell(ax + (bx - ax) * k / n, ay + (by - ay) * k / n)))
    return cells


def free(g, layer, ix, iy, net):
    if not (0 <= ix < g.nx and 0 <= iy < g.ny):
        return False
    v = g.trk[layer][iy * g.nx + ix]
    return v == 0 or v == net


def via_free(g, ix, iy, net):
    k = iy * g.nx + ix
    return all(g.via[l][k] in (0, net) for l in ALL_CU)


DIRS = [(1, 0, 1.0), (-1, 0, 1.0), (0, 1, 1.0), (0, -1, 1.0),
        (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]


def astar(g, net, src, dst, max_expand=3_000_000):
    dst_set = set(dst)
    tx = [c[1] for c in dst]
    ty = [c[2] for c in dst]
    bx0, bx1, by0, by1 = min(tx), max(tx), min(ty), max(ty)

    def h(ix, iy):
        return math.hypot(max(bx0 - ix, 0, ix - bx1), max(by0 - iy, 0, iy - by1))
    openq, came, cost = [], {}, {}
    for c in src:
        cost[c] = 0
        heapq.heappush(openq, (h(c[1], c[2]), 0, c))
    n = 0
    while openq:
        f, gc, c = heapq.heappop(openq)
        if gc > cost.get(c, 1e18):
            continue
        if c in dst_set:
            path = [c]
            while path[-1] in came:
                path.append(came[path[-1]])
            return path[::-1]
        n += 1
        if n > max_expand:
            return None
        layer, ix, iy = c
        nbrs = []
        for dx, dy, w in DIRS:
            jx, jy = ix + dx, iy + dy
            if free(g, layer, jx, jy, net) or (layer, jx, jy) in dst_set:
                # diagonal moves must not cut a blocked corner
                if dx and dy and not (free(g, layer, ix + dx, iy, net) and free(g, layer, ix, iy + dy, net)):
                    continue
                nbrs.append(((layer, jx, jy), w))
        if via_free(g, ix, iy, net):
            for l2 in LAYERS:
                if l2 != layer and free(g, l2, ix, iy, net):
                    nbrs.append(((l2, ix, iy), VIA_COST))
        for nc, w in nbrs:
            ng = gc + w
            if ng < cost.get(nc, 1e18):
                cost[nc] = ng
                came[nc] = c
                heapq.heappush(openq, (ng + h(nc[1], nc[2]), ng, nc))
    return None


def emit(board, g, net_item, path, width):
    """Turn a cell path into tracks and vias; return the new items."""
    items = []
    pts = [path[0]]
    for a, b, c in zip(path, path[1:], path[2:]):
        if a[0] != b[0] or b[0] != c[0]:
            pts.append(b)
            continue
        if (b[1] - a[1], b[2] - a[2]) != (c[1] - b[1], c[2] - b[2]):
            pts.append(b)
    pts.append(path[-1])
    # dedupe consecutive identical
    clean = [pts[0]]
    for p in pts[1:]:
        if p != clean[-1]:
            clean.append(p)
    for a, b in zip(clean, clean[1:]):
        xa, ya = g.xy(a[1], a[2])
        xb, yb = g.xy(b[1], b[2])
        if a[0] != b[0]:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(MM(xa), MM(ya)))
            v.SetWidth(MM(VIA_D))
            v.SetDrill(MM(VIA_DRILL))
            v.SetNet(net_item)
            board.Add(v)
            items.append(v)
        else:
            t = pcbnew.PCB_TRACK(board)
            t.SetStart(pcbnew.VECTOR2I(MM(xa), MM(ya)))
            t.SetEnd(pcbnew.VECTOR2I(MM(xb), MM(yb)))
            t.SetWidth(MM(width))
            t.SetLayer(a[0])
            t.SetNet(net_item)
            board.Add(t)
            items.append(t)
    return items


ITEM_RE = re.compile(r"@\(([-\d.]+) mm, ([-\d.]+) mm\): ((?:PTH |SMD |NPTH )?[Pp]ad (\S+) \[([^\]]*)\] of (\S+)|Track \[([^\]]*)\]|Via \[([^\]]*)\])")


def find_item(board, x, y, desc):
    m = ITEM_RE.match(desc)
    if m[4]:
        fp = board.FindFootprintByReference(m[6])
        cands = [p for p in fp.Pads() if p.GetNumber() == m[4]]
        return min(cands, key=lambda p: math.hypot(TOMM(p.GetPosition().x) - x, TOMM(p.GetPosition().y) - y))
    want = pcbnew.PCB_VIA_T if m[8] is not None else pcbnew.PCB_TRACE_T
    net = m[7] if m[7] is not None else m[8]
    best, bd = None, 1e9
    for t in board.GetTracks():
        if t.Type() != want or t.GetNetname() != net:
            continue
        if want == pcbnew.PCB_VIA_T:
            d = math.hypot(TOMM(t.GetPosition().x) - x, TOMM(t.GetPosition().y) - y)
        else:
            d = seg_dist(TOMM(t.GetStart().x), TOMM(t.GetStart().y), TOMM(t.GetEnd().x), TOMM(t.GetEnd().y), x, y)
        if d < bd:
            best, bd = t, d
    return best


def parse_unconnected(rpt):
    text = open(rpt).read()
    out = []
    for blk in text.split("[unconnected_items]")[1:]:
        locs = re.findall(r"(@\([-\d.]+ mm, [-\d.]+ mm\): [^\n]+)", blk)[:2]
        if len(locs) == 2:
            out.append(locs)
    return out


def main():
    src_pcb, rpt, out_pcb = sys.argv[1:4]
    board = pcbnew.LoadBoard(src_pcb)
    pairs = parse_unconnected(rpt)
    print(f"{len(pairs)} unconnected pairs")
    g = build_grid(board)
    failed = []
    first = os.environ.get("ROUTE_FIRST", "").split(",")
    def prio(p):
        return (0 if any(f and f"[{f}]" in p[0] for f in first) else 1, p[0])
    for a, b in sorted(pairs, key=prio):
        ma, mb = ITEM_RE.match(a.strip()), ITEM_RE.match(b.strip())
        ia = find_item(board, float(ma[1]), float(ma[2]), a.strip())
        ib = find_item(board, float(mb[1]), float(mb[2]), b.strip())
        if ia is None or ib is None:
            failed.append((a, b, "item not found"))
            continue
        net = ia.GetNetCode()
        name = ia.GetNetname()
        path = astar(g, net, list(item_cells(g, ia)), list(item_cells(g, ib)))
        if path is None:
            # retry: from the isolated end (ia) to anything in the other end's connected cluster
            net_items = [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetCode() == net]
            net_items += [tr for tr in board.GetTracks() if tr.GetNetCode() == net]
            cells = {id(it): item_cells(g, it) for it in net_items}
            def cluster(seed):
                seen, todo, acc = set(), [seed], set(item_cells(g, seed))
                while todo:
                    cur = todo.pop()
                    cc = item_cells(g, cur) if id(cur) not in cells else cells[id(cur)]
                    for it in net_items:
                        if id(it) in seen or it is cur:
                            continue
                        if cells[id(it)] & cc:
                            seen.add(id(it))
                            todo.append(it)
                            acc |= cells[id(it)]
                return acc
            for s, o in ((ia, ib), (ib, ia)):
                src_cl = cluster(s)
                dst = cluster(o) - src_cl
                if dst:
                    path = astar(g, net, list(src_cl), list(dst), max_expand=6_000_000)
                if path:
                    break
        if path is None:
            failed.append((a, b, "no path"))
            print("  FAIL", name, a[:60], "->", b[:60])
            continue
        width = 0.15  # grid keep-outs assume 0.15 mm; TODO wider power tracks need a second grid
        for it in emit(board, g, ia.GetNet(), path, width):
            add_item_to_grid(g, it)
            if os.environ.get("ROUTE_DEBUG"):
                if it.Type() == pcbnew.PCB_VIA_T:
                    print("    via", TOMM(it.GetPosition().x), TOMM(it.GetPosition().y))
                else:
                    print("    trk", board.GetLayerName(it.GetLayer()), TOMM(it.GetStart().x), TOMM(it.GetStart().y),
                          TOMM(it.GetEnd().x), TOMM(it.GetEnd().y))
        print(f"  routed {name}: {len(path)} cells")
    board.Save(out_pcb)
    print(f"failed: {len(failed)}")


if __name__ == "__main__":
    main()
