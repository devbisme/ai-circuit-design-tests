"""
Plane fanout: give every SMD pad on a plane net (GND -> In1, +3V3 -> In2) its own via plus a
short stub, locked, so Freerouting never has to route plane nets.

Run with KiCad 10's python:  python3.11 scripts/fanout.py in.kicad_pcb out.kicad_pcb
"""
import math
import sys

import pcbnew

MM = pcbnew.FromMM
TOMM = pcbnew.ToMM

PLANE_NETS = ("GND", "+3V3")
VIA_D, VIA_DRILL = 0.45, 0.2
CLR = 0.15  # copper clearance
STUB_W = 0.2
EDGE_CLR = 0.5


def pad_rect(pad):
    bb = pad.GetBoundingBox()
    return (TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom()))


def dist_pt_rect(x, y, r):
    dx = max(r[0] - x, 0, x - r[2])
    dy = max(r[1] - y, 0, y - r[3])
    return math.hypot(dx, dy)


def dist_seg_rect(x1, y1, x2, y2, r, n=12):
    return min(dist_pt_rect(x1 + (x2 - x1) * t / n, y1 + (y2 - y1) * t / n, r) for t in range(n + 1))


def seg_seg_dist(a, b):
    (x1, y1, x2, y2), (x3, y3, x4, y4) = a, b
    def pt_seg(px, py, ax, ay, bx, by):
        vx, vy = bx - ax, by - ay
        L = vx * vx + vy * vy
        t = 0 if L == 0 else max(0, min(1, ((px - ax) * vx + (py - ay) * vy) / L))
        return math.hypot(px - ax - t * vx, py - ay - t * vy)
    def ccw(ax, ay, bx, by, cx, cy):
        return (cy - ay) * (bx - ax) - (by - ay) * (cx - ax)
    d1, d2 = ccw(x1, y1, x2, y2, x3, y3), ccw(x1, y1, x2, y2, x4, y4)
    d3, d4 = ccw(x3, y3, x4, y4, x1, y1), ccw(x3, y3, x4, y4, x2, y2)
    if (d1 > 0) != (d2 > 0) and (d3 > 0) != (d4 > 0) and d1 * d2 != 0 and d3 * d4 != 0:
        return 0.0  # proper crossing
    return min(pt_seg(x1, y1, x3, y3, x4, y4), pt_seg(x2, y2, x3, y3, x4, y4),
               pt_seg(x3, y3, x1, y1, x2, y2), pt_seg(x4, y4, x1, y1, x2, y2))


def main(src, dst):
    board = pcbnew.LoadBoard(src)
    bb = board.GetBoardEdgesBoundingBox()
    ex0, ey0, ex1, ey1 = TOMM(bb.GetLeft()), TOMM(bb.GetTop()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())

    # Obstacles: all copper pads (per layer side), with net.
    pads = []
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if not pad.IsOnCopperLayer():
                continue
            th = pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)
            side = "both" if th else ("B" if pad.IsOnLayer(pcbnew.B_Cu) else "F")
            pads.append(dict(pad=pad, fp=fp, rect=pad_rect(pad), net=pad.GetNetname(), side=side,
                             th=th, num=pad.GetNumber()))

    vias = []  # (x, y, net)
    stubs = []  # (x1,y1,x2,y2, side, net)
    added = 0
    failed = []
    # Existing copper (re-run on a routed board): obstacles, and pads already served.
    old_vias, old_stubs = [], []
    served = set()
    for t in board.GetTracks():
        if t.GetClass() == "PCB_VIA":
            old_vias.append((TOMM(t.GetPosition().x), TOMM(t.GetPosition().y), t.GetNetname(),
                             TOMM(t.GetWidth(pcbnew.F_Cu)) if hasattr(t, "GetWidth") else VIA_D))
        else:
            side = "F" if t.GetLayer() == pcbnew.F_Cu else ("B" if t.GetLayer() == pcbnew.B_Cu else "I")
            old_stubs.append((TOMM(t.GetStart().x), TOMM(t.GetStart().y), TOMM(t.GetEnd().x),
                              TOMM(t.GetEnd().y), side, t.GetNetname(), TOMM(t.GetWidth())))
    for p in pads:
        if p["net"] not in PLANE_NETS:
            continue
        for x1, y1, x2, y2, side, net, w in old_stubs:
            if net == p["net"] and side == p["side"] and (dist_pt_rect(x1, y1, p["rect"]) == 0 or
                                                           dist_pt_rect(x2, y2, p["rect"]) == 0):
                served.add(id(p))
        for vx, vy, vn, vd in old_vias:
            if vn == p["net"] and dist_pt_rect(vx, vy, p["rect"]) == 0:
                served.add(id(p))

    def via_ok(x, y, net, side):
        r = VIA_D / 2
        if x - r < ex0 + EDGE_CLR or x + r > ex1 - EDGE_CLR or y - r < ey0 + EDGE_CLR or y + r > ey1 - EDGE_CLR:
            return False
        for p in pads:
            # Vias are through: they clash with pads on every layer.
            need = r + CLR if p["net"] != net else r + 0.05
            if p["net"] == net and not p["th"]:
                need = r + 0.05  # may touch own-net SMD pads lightly but not sit on them
            if dist_pt_rect(x, y, p["rect"]) < need:
                return False
        for vx, vy, vn in vias:
            if math.hypot(x - vx, y - vy) < VIA_D + (CLR if vn != net else 0.1):
                return False
        for s in stubs:
            if s[5] != net and seg_seg_dist((x, y, x, y), s[:4]) < r + STUB_W / 2 + CLR:
                return False
        for vx, vy, vn, vd in old_vias:
            if math.hypot(x - vx, y - vy) < r + vd / 2 + (CLR if vn != net else 0.1):
                return False
        for x1, y1, x2, y2, sd, sn, w in old_stubs:
            if sn != net and seg_seg_dist((x, y, x, y), (x1, y1, x2, y2)) < r + w / 2 + CLR:
                return False
        return True

    def stub_ok(x1, y1, x2, y2, net, side, own):
        for p in pads:
            if p is own or p["net"] == net:
                continue
            if p["side"] not in (side, "both"):
                continue
            if dist_seg_rect(x1, y1, x2, y2, p["rect"]) < STUB_W / 2 + CLR:
                return False
        for s in stubs:
            if s[4] == side and s[5] != net and seg_seg_dist((x1, y1, x2, y2), s[:4]) < STUB_W + CLR:
                return False
        for vx, vy, vn in vias:
            if vn != net and seg_seg_dist((x1, y1, x2, y2), (vx, vy, vx, vy)) < VIA_D / 2 + STUB_W / 2 + CLR:
                return False
        for vx, vy, vn, vd in old_vias:
            if vn != net and seg_seg_dist((x1, y1, x2, y2), (vx, vy, vx, vy)) < vd / 2 + STUB_W / 2 + CLR:
                return False
        for a1, b1, a2, b2, sd, sn, w in old_stubs:
            if sn != net and sd == side and seg_seg_dist((x1, y1, x2, y2), (a1, b1, a2, b2)) < w / 2 + STUB_W / 2 + CLR:
                return False
        return True

    # Biggest parts first: fine-pitch pins get first pick of space.
    order = sorted([p for p in pads if p["net"] in PLANE_NETS and not p["th"]],
                   key=lambda p: -p["fp"].GetPadCount())
    for p in order:
        if id(p) in served:
            continue
        pad, fp, net = p["pad"], p["fp"], p["net"]
        side = p["side"]
        px, py = TOMM(pad.GetPosition().x), TOMM(pad.GetPosition().y)
        cx, cy = TOMM(fp.GetPosition().x), TOMM(fp.GetPosition().y)
        w = p["rect"][2] - p["rect"][0]
        h = p["rect"][3] - p["rect"][1]
        big_pad = w > 2.0 and h > 2.0  # exposed pads
        # Reuse an existing same-net via close by.
        if not big_pad:
            near = [v for v in vias if v[2] == net and math.hypot(v[0] - px, v[1] - py) < 1.2]
            if near:
                vx, vy, _ = min(near, key=lambda v: math.hypot(v[0] - px, v[1] - py))
                if stub_ok(px, py, vx, vy, net, side, p):
                    stubs.append((px, py, vx, vy, side, net))
                    added += 1
                    continue
        if big_pad:
            # Grid of vias inside the exposed pad (max 3x3).
            nx = min(3, max(1, int(w / 1.2)))
            ny = min(3, max(1, int(h / 1.2)))
            for i in range(nx):
                for j in range(ny):
                    x = p["rect"][0] + w * (i + 0.5) / nx
                    y = p["rect"][1] + h * (j + 0.5) / ny
                    vias.append((x, y, net))
            added += 1
            continue
        # Outward direction.
        if fp.GetPadCount() <= 4:
            others = [q for q in fp.Pads() if q.GetNumber() != pad.GetNumber()]
            ox = sum(TOMM(q.GetPosition().x) for q in others) / max(1, len(others))
            oy = sum(TOMM(q.GetPosition().y) for q in others) / max(1, len(others))
            dx, dy = px - ox, py - oy
        else:
            dx, dy = px - cx, py - cy
            # snap to the dominant axis of the pin row
            if abs(dx) > abs(dy):
                dy = 0
            else:
                dx = 0
        d = math.hypot(dx, dy) or 1.0
        ux, uy = dx / d, dy / d
        vx_, vy_ = -uy, ux  # lateral
        half = max(w, h) / 2 if fp.GetPadCount() > 4 else (abs(ux) * w + abs(uy) * h) / 2
        done = False
        for along in [half + VIA_D / 2 + 0.1 + k * 0.15 for k in range(12)]:
            for lat in (0, 0.25, -0.25, 0.5, -0.5, 0.75, -0.75, 1.0, -1.0):
                x = px + ux * along + vx_ * lat
                y = py + uy * along + vy_ * lat
                if via_ok(x, y, net, side) and stub_ok(px, py, x, y, net, side, p):
                    vias.append((x, y, net))
                    stubs.append((px, py, x, y, side, net))
                    added += 1
                    done = True
                    break
            if done:
                break
        if not done:
            # Try all directions as a last resort.
            for along in [half + VIA_D / 2 + 0.1 + k * 0.2 for k in range(10)]:
                for a in range(0, 360, 20):
                    x = px + along * math.cos(math.radians(a))
                    y = py + along * math.sin(math.radians(a))
                    if via_ok(x, y, net, side) and stub_ok(px, py, x, y, net, side, p):
                        vias.append((x, y, net))
                        stubs.append((px, py, x, y, side, net))
                        added += 1
                        done = True
                        break
                if done:
                    break
        if not done:
            failed.append(f"{fp.GetReference()}.{pad.GetNumber()} ({net})")

    netinfo = {n: board.FindNet(n) for n in PLANE_NETS}
    for x, y, net in vias:
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(VIA_D))
        v.SetDrill(MM(VIA_DRILL))
        v.SetNet(netinfo[net])
        v.SetLocked(True)
        board.Add(v)
    for x1, y1, x2, y2, side, net in stubs:
        if math.hypot(x2 - x1, y2 - y1) < 1e-3:
            continue
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        t.SetEnd(pcbnew.VECTOR2I(MM(x2), MM(y2)))
        t.SetWidth(MM(STUB_W))
        t.SetLayer(pcbnew.B_Cu if side == "B" else pcbnew.F_Cu)
        t.SetNet(netinfo[net])
        t.SetLocked(True)
        board.Add(t)
    board.Save(dst)
    print(f"fanout: {added} pads, {len(vias)} vias, {len(failed)} failed")
    for f in failed:
        print("  failed", f)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
