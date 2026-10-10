"""Finish the last unrouted connections with a small grid A* (run with KiCad 10's python3.11).

Reads the unconnected-item pairs from a kicad-cli DRC JSON report and routes each one on
F.Cu / In2.Cu / B.Cu (In1 is the GND plane) with 0.15 mm tracks and 0.45/0.2 vias.
GND pours are ignored as obstacles (they are refilled afterwards).
Also fixes footprint LIB_IDs written without a library nickname (pcb_sync_from_schematic).
Usage: finish_routes.py board.kicad_pcb drc.json
"""
import heapq, json, math, re, sys
import pcbnew

MM = pcbnew.FromMM
STEP = 0.05
TW, CLR, VIA_D, VIA_H = 0.15, 0.16, 0.45, 0.2
LAYERS = [pcbnew.F_Cu, pcbnew.In2_Cu, pcbnew.B_Cu]


def fix_fpids(board):
    """Give footprints the library nickname that pcb_sync_from_schematic left out."""
    import glob, os
    root = '/home/devb/bin/kicad10-root/share/kicad/footprints'
    n = 0
    for fp in board.GetFootprints():
        fpid = fp.GetFPID()
        if str(fpid.GetLibNickname()):
            continue
        name = str(fpid.GetLibItemName())
        hits = glob.glob(f'{root}/*.pretty/{name}.kicad_mod')
        if hits:
            nick = os.path.basename(os.path.dirname(hits[0]))[:-len('.pretty')]
            fp.SetFPID(pcbnew.LIB_ID(nick, name)); n += 1
    return n


def items_of(board):
    out = []
    for fp in board.GetFootprints():
        for p in fp.Pads():
            out.append(p)
    for t in board.GetTracks():
        out.append(t)
    return out


def route(board, a, b, net):
    """a, b: (x_mm, y_mm, layer_set) endpoints."""
    x0, x1 = min(a[0], b[0]) - 3, max(a[0], b[0]) + 3
    y0, y1 = min(a[1], b[1]) - 3, max(a[1], b[1]) + 3
    nx, ny = int((x1 - x0) / STEP) + 1, int((y1 - y0) / STEP) + 1
    region = pcbnew.BOX2I(pcbnew.VECTOR2I(MM(x0 - 1), MM(y0 - 1)), pcbnew.VECTOR2I(MM(x1 - x0 + 2), MM(y1 - y0 + 2)))
    obst = {L: [] for L in LAYERS}
    for it in items_of(board):
        if it.GetNetCode() == net.GetNetCode() or not it.GetBoundingBox().Intersects(region):
            continue
        for L in LAYERS:
            if it.IsOnLayer(L):
                obst[L].append(it.GetEffectiveShape(L))
    # holes block every layer
    blocked = {}

    def free(i, j, L, r):
        key = (i, j, L, r)
        if key in blocked:
            return blocked[key]
        pt = pcbnew.VECTOR2I(MM(x0 + i * STEP), MM(y0 + j * STEP))
        ok = not any(s.Collide(pt, MM(r)) for s in obst[L])
        blocked[key] = ok
        return ok

    def via_free(i, j):
        return all(free(i, j, L, VIA_D / 2 + CLR) for L in LAYERS)

    def cell(p):
        return int(round((p[0] - x0) / STEP)), int(round((p[1] - y0) / STEP))

    si, sj = cell(a); ti, tj = cell(b)
    starts = [(si, sj, L) for L in LAYERS if L in a[2]]
    goals = {(ti, tj, L) for L in LAYERS if L in b[2]}
    h = lambda i, j: math.hypot(i - ti, j - tj)
    pq = [(h(si, sj), 0.0, s, None) for s in starts]
    came, cost = {}, {s: 0.0 for s in starts}
    moves = [(1, 0, 1), (-1, 0, 1), (0, 1, 1), (0, -1, 1), (1, 1, 1.414), (1, -1, 1.414), (-1, 1, 1.414), (-1, -1, 1.414)]
    while pq:
        f, g, s, prev = heapq.heappop(pq)
        if s in came:
            continue
        came[s] = prev
        if s in goals:
            path = [s]
            while came[path[-1]] is not None:
                path.append(came[path[-1]])
            return path[::-1], (x0, y0)
        i, j, L = s
        for di, dj, c in moves:
            n = (i + di, j + dj, L)
            if not (0 <= n[0] < nx and 0 <= n[1] < ny) or n in came:
                continue
            near_end = (abs(n[0] - si) + abs(n[1] - sj) < 6) or (abs(n[0] - ti) + abs(n[1] - tj) < 6)
            if not free(n[0], n[1], L, TW / 2 + (0.151 if near_end else CLR)):
                continue
            ng = g + c
            if ng < cost.get(n, 1e18):
                cost[n] = ng; heapq.heappush(pq, (ng + h(n[0], n[1]), ng, n, s))
        for L2 in LAYERS:
            if L2 != L:
                n = (i, j, L2)
                if n not in came and via_free(i, j):
                    ng = g + 40
                    if ng < cost.get(n, 1e18):
                        cost[n] = ng; heapq.heappush(pq, (ng + h(i, j), ng, n, s))
    return None, None


def emit(board, path, origin, net):
    x0, y0 = origin
    pts = [(x0 + i * STEP, y0 + j * STEP, L) for i, j, L in path]
    # compress collinear runs
    segs, start = [], pts[0]
    for k in range(1, len(pts)):
        p, q = pts[k - 1], pts[k]
        if q[2] != p[2]:
            if (start[0], start[1]) != (p[0], p[1]):
                segs.append((start, p))
            v = pcbnew.PCB_VIA(board); v.SetPosition(pcbnew.VECTOR2I(MM(p[0]), MM(p[1])))
            v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_H)); v.SetNet(net); board.Add(v)
            start = q
            continue
        if k + 1 < len(pts):
            r = pts[k + 1]
            if r[2] == q[2] and round((q[0] - p[0]) * (r[1] - q[1]) - (q[1] - p[1]) * (r[0] - q[0]), 6) == 0:
                continue
        segs.append((start, q)); start = q
    for s, e in segs:
        if (s[0], s[1]) == (e[0], e[1]):
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(s[0]), MM(s[1]))); t.SetEnd(pcbnew.VECTOR2I(MM(e[0]), MM(e[1])))
        t.SetWidth(MM(TW)); t.SetLayer(s[2]); t.SetNet(net); board.Add(t)


def endpoint(board, uuid, other_pos):
    it = UUIDS.get(uuid)
    if isinstance(it, pcbnew.PAD):
        p = it.GetPosition()
        return (p.x / 1e6, p.y / 1e6, {L for L in LAYERS if it.IsOnLayer(L)}), it.GetNet()
    if isinstance(it, pcbnew.PCB_TRACK):
        cands = [it.GetStart(), it.GetEnd()]
        p = min(cands, key=lambda c: math.hypot(c.x / 1e6 - other_pos[0], c.y / 1e6 - other_pos[1]))
        lay = {L for L in LAYERS if it.IsOnLayer(L)} if isinstance(it, pcbnew.PCB_VIA) else {it.GetLayer()}
        return (p.x / 1e6, p.y / 1e6, lay), it.GetNet()
    return None, None


def main(pcb, drc):
    board = pcbnew.LoadBoard(pcb)
    print('fixed FPIDs:', fix_fpids(board))
    rep = json.load(open(drc))
    global UUIDS
    UUIDS = {it.m_Uuid.AsString(): it for it in items_of(board)}
    failed = []
    for v in rep['unconnected_items']:
        ia, ib = v['items'][0], v['items'][1]
        pa, pb = (ia['pos']['x'], ia['pos']['y']), (ib['pos']['x'], ib['pos']['y'])
        a, net = endpoint(board, ia['uuid'], pb)
        b, _ = endpoint(board, ib['uuid'], pa)
        if a is None or b is None:
            print('skip', ia['description'], ib['description']); continue
        path, origin = route(board, a, b, net)
        print(net.GetNetname(), 'routed' if path else 'FAILED', len(path or []))
        if path:
            emit(board, path, origin, net)
        elif RIP:
            failed.append((a, b, net.GetNetCode()))
    rip = {}
    for a, b, code in failed:      # rip up unlocked other-net copper near failed ends
        for e in (a, b):
            for t in board.GetTracks():
                if t.IsLocked() or t.GetNetCode() == code:
                    continue
                pts = [t.GetPosition()] if isinstance(t, pcbnew.PCB_VIA) else [t.GetStart(), t.GetEnd()]
                if any(math.hypot(q.x / 1e6 - e[0], q.y / 1e6 - e[1]) < RIP for q in pts):
                    rip[t.m_Uuid.AsString()] = t
    for t in rip.values():
        print('   rip', t.GetNetname())
        board.Remove(t)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    board.Save(pcb)


RIP = float(sys.argv[3]) if len(sys.argv) > 3 else 0.0

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
