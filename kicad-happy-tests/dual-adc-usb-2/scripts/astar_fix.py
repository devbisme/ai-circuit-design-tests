"""
Finish the last unrouted connections with a small 2-layer grid A* router.

  python3.11 scripts/astar_fix.py board.kicad_pcb drc.json out.kicad_pcb

For each unconnected pair in a kicad-cli DRC JSON report, route a 0.15 mm track
(F.Cu / B.Cu, vias allowed) between the two items with 0.15 mm clearance to all foreign
copper. Zone fills are ignored (outer pours are refilled afterwards; inner planes are never
routed on). For a pad on a plane net (GND, +3V3) whose partner is unreachable, the goal is
any legal via site (the via lands on the plane).
"""
import heapq
import json
import math
import sys

import pcbnew

MM = pcbnew.FromMM
TOMM = pcbnew.ToMM
RES = 0.05
RIP_COST = int(__import__("os").environ.get("ASTAR_RIP_COST", "1000"))
RIPUP = __import__("os").environ.get("ASTAR_RIPUP", "0") == "1"
MAX_EXP = int(__import__("os").environ.get("ASTAR_MAX_EXP", "400000"))
W = 0.15
CLR = 0.175  # 0.15 rule + margin for 0.05 mm grid rounding
VIA_D, VIA_DRILL = 0.45, 0.2
PLANE_NETS = {"GND", "+3V3"}
LAYERS = (pcbnew.F_Cu, pcbnew.B_Cu)


def seg_dist(px, py, ax, ay, bx, by):
    vx, vy = bx - ax, by - ay
    L = vx * vx + vy * vy
    t = 0 if L == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L))
    return math.hypot(px - ax - t * vx, py - ay - t * vy)


class Item:
    def __init__(self, kind, net, layers, geom):
        self.kind, self.net, self.layers, self.geom = kind, net, layers, geom

    def dist(self, x, y):
        k, g = self.kind, self.geom
        if k == "pad":
            poly = g
            # distance to polygon (0 inside)
            inside = False
            n = len(poly)
            d = 1e9
            for i in range(n):
                ax, ay = poly[i]
                bx, by = poly[(i + 1) % n]
                d = min(d, seg_dist(x, y, ax, ay, bx, by))
                if (ay > y) != (by > y) and x < (bx - ax) * (y - ay) / (by - ay + 1e-12) + ax:
                    inside = not inside
            return 0.0 if inside else d
        if k == "track":
            ax, ay, bx, by, w = g
            return max(0.0, seg_dist(x, y, ax, ay, bx, by) - w / 2)
        if k == "via":
            cx, cy, d = g
            return max(0.0, math.hypot(x - cx, y - cy) - d / 2)

    def bbox(self):
        k, g = self.kind, self.geom
        if k == "pad":
            xs = [p[0] for p in g]
            ys = [p[1] for p in g]
            return min(xs), min(ys), max(xs), max(ys)
        if k == "track":
            ax, ay, bx, by, w = g
            return min(ax, bx) - w / 2, min(ay, by) - w / 2, max(ax, bx) + w / 2, max(ay, by) + w / 2
        cx, cy, d = g
        return cx - d / 2, cy - d / 2, cx + d / 2, cy + d / 2


def collect(board):
    items = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if not pad.IsOnCopperLayer():
                continue
            lays = tuple(l for l in LAYERS if pad.IsOnLayer(l))
            if not lays:
                continue
            ps = pad.GetEffectivePolygon(lays[0], pcbnew.ERROR_OUTSIDE)
            ol = ps.Outline(0)
            poly = [(TOMM(ol.CPoint(i).x), TOMM(ol.CPoint(i).y)) for i in range(ol.PointCount())]
            it = Item("pad", pad.GetNetname(), lays, poly)
            it.obj = pad
            items.append(it)
            if pad.GetDrillSize().x > 0:  # holes block both layers
                it.layers = LAYERS
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            it = Item("via", t.GetNetname(), LAYERS, (TOMM(t.GetPosition().x), TOMM(t.GetPosition().y),
                                                      TOMM(t.GetWidth(pcbnew.F_Cu))))
        else:
            if t.GetLayer() not in LAYERS:
                continue
            it = Item("track", t.GetNetname(), (t.GetLayer(),),
                      (TOMM(t.GetStart().x), TOMM(t.GetStart().y), TOMM(t.GetEnd().x), TOMM(t.GetEnd().y),
                       TOMM(t.GetWidth())))
        it.obj = t
        items.append(it)
    return items


def find_item(items, desc, pos):
    x, y = pos["x"], pos["y"]
    net = desc[desc.index("[") + 1: desc.index("]")]
    best = None
    for it in items:
        if it.net != net:
            continue
        if desc.startswith("Pad") and it.kind != "pad":
            continue
        if desc.startswith("Track") and it.kind != "track":
            continue
        if desc.startswith("Via") and it.kind != "via":
            continue
        d = it.dist(x, y)
        if best is None or d < best[0]:
            best = (d, it)
    return best[1] if best and best[0] < 0.05 else None


def route(board, items, a, b, net, edge, soft_ok=False, usb=False):
    global W, CLR
    fine = net.startswith(("DA", "DB")) or net in ("OFA", "OFB")
    W, CLR = (0.1, 0.12) if fine else ((0.2, 0.175) if usb else (0.15, 0.175))
    """A* from item a to item b (b may be None -> any via site for plane nets)."""
    pts = [a.bbox()] + ([b.bbox()] if b else [])
    for margin in (3.0, 6.0, 10.0):
        x0 = min(p[0] for p in pts) - margin
        y0 = min(p[1] for p in pts) - margin
        x1 = max(p[2] for p in pts) + margin
        y1 = max(p[3] for p in pts) + margin
        x0, y0 = max(x0, edge[0] + 0.4), max(y0, edge[1] + 0.4)
        x1, y1 = min(x1, edge[2] - 0.4), min(y1, edge[3] - 0.4)
        nx, ny = int((x1 - x0) / RES) + 1, int((y1 - y0) / RES) + 1
        local = [it for it in items if not (it.bbox()[2] < x0 - 1 or it.bbox()[0] > x1 + 1 or
                                            it.bbox()[3] < y0 - 1 or it.bbox()[1] > y1 + 1)]
        foreign = [it for it in local if it.net != net]
        own = [it for it in local if it.net == net]

        # Obstacle rasters: blocked[(li, rad)] is a bytearray over the window, 1 = blocked.
        rasters = {}
        SOFT = soft_ok

        def rippable(it):
            return SOFT and it.kind in ("track", "via") and it.net not in PLANE_NETS

        def raster(li, rad):
            key = (li, rad)
            if key in rasters:
                return rasters[key]
            grid = bytearray(nx * ny)
            soft = {}
            reach = rad + CLR
            for it in foreign:
                if LAYERS[li] not in it.layers:
                    continue
                rip = rippable(it)
                bb = it.bbox()
                i0 = max(0, int((bb[0] - reach - x0) / RES))
                i1 = min(nx - 1, int((bb[2] + reach - x0) / RES) + 1)
                j0 = max(0, int((bb[1] - reach - y0) / RES))
                j1 = min(ny - 1, int((bb[3] + reach - y0) / RES) + 1)
                for j in range(j0, j1 + 1):
                    y = y0 + j * RES
                    row = j * nx
                    for i in range(i0, i1 + 1):
                        c = row + i
                        if grid[c] == 1:
                            continue
                        if it.dist(x0 + i * RES, y) < reach:
                            if rip:
                                grid[c] = 2
                                soft.setdefault(c, []).append(it)
                            else:
                                grid[c] = 1
                                soft.pop(c, None)
            rasters[key] = (grid, soft)
            return rasters[key]

        def free(i, j, li, rad):
            return not raster(li, rad)[0][j * nx + i]

        def cell_cost(i, j, li, rad):
            """None = hard blocked, else extra cost (soft = crossing a rippable foreign track)."""
            v = raster(li, rad)[0][j * nx + i]
            return None if v == 1 else (RIP_COST if v == 2 else 0)

        def on(it, i, j, li):
            return LAYERS[li] in it.layers and it.dist(x0 + i * RES, y0 + j * RES) < 1e-6

        def via_ok(i, j):
            return free(i, j, 0, VIA_D / 2) and free(i, j, 1, VIA_D / 2)

        # start cells: grid cells inside item a on its layers
        def cells_of(it):
            bb = it.bbox()
            out = []
            for i in range(max(0, int((bb[0] - x0) / RES)), min(nx, int((bb[2] - x0) / RES) + 2)):
                for j in range(max(0, int((bb[1] - y0) / RES)), min(ny, int((bb[3] - y0) / RES) + 2)):
                    for li in range(2):
                        if on(it, i, j, li):
                            out.append((i, j, li))
            return out

        starts = cells_of(a)
        if b is not None:
            goals = set(cells_of(b))
            gx = sum(c[0] for c in goals) / max(1, len(goals))
            gy = sum(c[1] for c in goals) / max(1, len(goals))
        else:
            goals = None
            gx = gy = None
        if not starts or (b is not None and not goals):
            return None

        def h(i, j):
            return 0 if gx is None else math.hypot(i - gx, j - gy)

        openq = []
        came = {}
        g = {}
        for s in starts:
            g[s] = 0
            heapq.heappush(openq, (h(s[0], s[1]), 0, s))
        steps = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414),
                 (-1, -1, 1.414)]
        found = None
        n_exp = 0
        while openq and n_exp < MAX_EXP:
            f, gc, cur = heapq.heappop(openq)
            if gc > g.get(cur, 1e18):
                continue
            n_exp += 1
            i, j, li = cur
            if goals is not None and cur in goals:
                found = cur
                break
            if goals is None and cur not in starts and via_ok(i, j):
                found = (i, j, li, "via")
                break
            for di, dj, c in steps:
                ni, nj = i + di, j + dj
                if not (0 <= ni < nx and 0 <= nj < ny):
                    continue
                nxt = (ni, nj, li)
                inside_own = (goals is not None and nxt in goals) or any(on(it, ni, nj, li) for it in (a,))
                extra = 0
                if not inside_own:
                    extra = cell_cost(ni, nj, li, W / 2)
                    if extra is None:
                        continue
                ng = gc + c + extra
                if ng < g.get(nxt, 1e18):
                    g[nxt] = ng
                    came[nxt] = cur
                    heapq.heappush(openq, (ng + h(ni, nj), ng, nxt))
            # layer change via
            if goals is not None and via_ok(i, j):
                nxt = (i, j, 1 - li)
                ng = gc + 40
                if ng < g.get(nxt, 1e18):
                    g[nxt] = ng
                    came[nxt] = cur
                    heapq.heappush(openq, (ng + h(i, j), ng, nxt))
        print(f"   window {x1 - x0:.1f}x{y1 - y0:.1f} mm, expanded {n_exp}, found={bool(found)}")
        if found:
            end_via = len(found) == 4
            cur = found[:3]
            path = [cur]
            while cur in came:
                cur = came[cur]
                path.append(cur)
            path.reverse()
            # Line-of-sight smoothing per layer run: drop intermediate points when the straight
            # segment between kept points is clear.
            def clear_line(p, q):
                (i1, j1, l1), (i2, j2, _l) = p, q
                n = int(max(abs(i2 - i1), abs(j2 - j1))) + 1
                for k in range(n + 1):
                    i = round(i1 + (i2 - i1) * k / n)
                    j = round(j1 + (j2 - j1) * k / n)
                    if (i, j, l1) in starts_set or (goals is not None and (i, j, l1) in goals):
                        continue
                    if not free(i, j, l1, W / 2):
                        return False
                return True
            starts_set = set(starts)
            out = [path[0]]
            k = 0
            while k < len(path) - 1:
                # furthest reachable point on the same layer
                best = k + 1
                m = k + 2
                while m < len(path) and path[m][2] == path[k][2] and clear_line(path[k], path[m]):
                    best = m
                    m += 1
                out.append(path[best])
                k = best
            crossed = set()
            for i, j, li in path:
                crossed.update(raster(li, W / 2)[1].get(j * nx + i, []))
            for t in range(len(out) - 1):  # smoothed segments may cut through other soft cells
                (i1, j1, l1), (i2, j2, _l) = out[t], out[t + 1]
                n = int(max(abs(i2 - i1), abs(j2 - j1))) + 1
                for k in range(n + 1):
                    i = round(i1 + (i2 - i1) * k / n)
                    j = round(j1 + (j2 - j1) * k / n)
                    crossed.update(raster(l1, W / 2)[1].get(j * nx + i, []))
            for i, j, li in path:
                if li != path[0][2]:
                    pass
            route.crossed = crossed
            return [(x0 + i * RES, y0 + j * RES, li) for i, j, li in out], end_via
    return None


def emit(board, net, path, end_via):
    ni = board.FindNet(net)
    # compress collinear runs
    pts = [path[0]]
    for p in path[1:]:
        pts.append(p)
        if len(pts) >= 3:
            (ax, ay, al), (bx, by, bl), (cx, cy, cl) = pts[-3:]
            if al == bl == cl and abs((bx - ax) * (cy - by) - (by - ay) * (cx - bx)) < 1e-9:
                pts.pop(-2)
    n_t = n_v = 0
    for (ax, ay, al), (bx, by, bl) in zip(pts, pts[1:]):
        if al != bl:
            v = pcbnew.PCB_VIA(board)
            v.SetPosition(pcbnew.VECTOR2I(MM(ax), MM(ay)))
            v.SetWidth(MM(VIA_D))
            v.SetDrill(MM(VIA_DRILL))
            v.SetNet(ni)
            board.Add(v)
            n_v += 1
            continue
        if math.hypot(bx - ax, by - ay) < 1e-6:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(ax), MM(ay)))
        t.SetEnd(pcbnew.VECTOR2I(MM(bx), MM(by)))
        t.SetWidth(MM(W))
        t.SetLayer(LAYERS[al])
        t.SetNet(ni)
        board.Add(t)
        n_t += 1
    if end_via:
        x, y, _l = pts[-1]
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(VIA_D))
        v.SetDrill(MM(VIA_DRILL))
        v.SetNet(ni)
        board.Add(v)
        n_v += 1
    return n_t, n_v


def main(src, drc, dst):
    board = pcbnew.LoadBoard(src)
    bb = board.GetBoardEdgesBoundingBox()
    edge = (TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom()))
    report = json.load(open(drc))
    for u in report.get("unconnected_items", []):
        (da, pa), (db, pb) = [(i["description"], i["pos"]) for i in u["items"]]
        if da.startswith("Zone") or db.startswith("Zone"):
            print("skip zone pair:", da[:40], db[:40])
            continue
        items = collect(board)
        a = find_item(items, da, pa)
        b = find_item(items, db, pb)
        if a is None or b is None:
            print("item not found", da, db)
            continue
        net = a.net
        # Prefer starting from the pad (smaller start set).
        if b.kind == "pad" and a.kind != "pad":
            a, b = b, a
        res = route(board, items, a, b, net, edge)
        if res is None and net in PLANE_NETS and a.kind == "pad":
            res = route(board, items, a, None, net, edge)
        if res is None and RIPUP:
            route.crossed = set()
            res = route(board, items, a, b, net, edge, soft_ok=True)
            if res is not None and route.crossed:
                nets = sorted({it.net for it in route.crossed})
                for it in route.crossed:
                    board.Remove(it.obj)
                print(f"   ripped {len(route.crossed)} segments of {nets}")
        if res is None:
            print("FAILED", net, da[:50], "<->", db[:50])
            continue
        path, end_via = res
        nt, nv = emit(board, net, path, end_via)
        print(f"routed {net}: {nt} tracks, {nv} vias")
        if getattr(route, "crossed", None):
            # One rip-up per process: SWIG proxies get unreliable after Remove()+Add() churn.
            board.Save(dst)
            return
    board.Save(dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3])
