"""Locked plane fanout: stub + via for every SMD pad on the plane nets (GND -> In1/In2-left,
+3V3 -> In2-right), plus a via grid in the ADC exposed pad.  Run with KiCad 10 python.

Freerouting does not treat inner-layer zones as connecting a net, so plane-net pads are
connected here and the plane nets are cut down to one pin in the DSN (see route.py).
"""
import math, sys
import pcbnew

PLANE_NETS = ("GND", "+3V3")
VIA_D, VIA_DRILL, STUB_W, CLR = 0.5, 0.25, 0.25, 0.17
MM = 1e6

board = pcbnew.LoadBoard(sys.argv[1])
edge = board.GetBoardEdgesBoundingBox()
EX0, EY0, EX1, EY1 = edge.GetLeft() / MM, edge.GetTop() / MM, edge.GetRight() / MM, edge.GetBottom() / MM

pads = []          # (x0, y0, x1, y1, net, is_th, cx, cy, drill)
for fp in board.GetFootprints():
    for p in fp.Pads():
        bb = p.GetBoundingBox()
        pads.append((bb.GetLeft() / MM, bb.GetTop() / MM, bb.GetRight() / MM, bb.GetBottom() / MM,
                     p.GetNetname(), p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH,
                     p.GetPosition().x / MM, p.GetPosition().y / MM,
                     max(p.GetDrillSize().x, p.GetDrillSize().y) / MM,
                     bool(p.IsOnLayer(pcbnew.F_Cu)), bool(p.IsOnLayer(pcbnew.B_Cu)), id(p)))
vias = []          # (x, y, net)
segs = []          # (x0, y0, x1, y1, net, front)


def rect_dist(x, y, r):
    dx = max(r[0] - x, 0, x - r[2])
    dy = max(r[1] - y, 0, y - r[3])
    return math.hypot(dx, dy)


def via_ok(x, y, net, own):
    if x < EX0 + 0.6 or x > EX1 - 0.6 or y < EY0 + 0.6 or y > EY1 - 0.6:
        return False
    for r in pads:
        if r[11] == own:
            continue
        d = rect_dist(x, y, r)
        if r[4] == net and not r[5]:
            if d < 0.05:            # don't drop a via onto another same-net SMD pad
                return False
            continue
        if d < VIA_D / 2 + CLR:
            return False
        if r[5] and math.hypot(x - r[6], y - r[7]) < VIA_DRILL / 2 + r[8] / 2 + 0.3:
            return False
    for (vx, vy, vn) in vias:
        if math.hypot(x - vx, y - vy) < VIA_D + CLR:
            return False
    for (a, b, c, d, sn, sf) in segs:
        if sn != net and seg_pt_dist(a, b, c, d, x, y) < VIA_D / 2 + STUB_W / 2 + CLR:
            return False
    return True


def seg_pt_dist(x0, y0, x1, y1, x, y):
    L2 = (x1 - x0) ** 2 + (y1 - y0) ** 2
    t = 0 if L2 == 0 else max(0, min(1, ((x - x0) * (x1 - x0) + (y - y0) * (y1 - y0)) / L2))
    return math.hypot(x - (x0 + t * (x1 - x0)), y - (y0 + t * (y1 - y0)))


def stub_ok(x0, y0, x1, y1, net, own, front):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.1))
    for i in range(n + 1):
        x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
        for r in pads:
            if r[11] == own or r[4] == net:
                continue
            if (front and not r[9]) or (not front and not r[10]):
                continue
            if rect_dist(x, y, r) < STUB_W / 2 + CLR:
                return False
        for (vx, vy, vn) in vias:
            if vn != net and math.hypot(x - vx, y - vy) < VIA_D / 2 + STUB_W / 2 + CLR:
                return False
        for (a, b, c, d, sn, sf) in segs:
            if sn != net and sf == front and seg_pt_dist(a, b, c, d, x, y) < STUB_W + CLR:
                return False
    return True


def add_via(x, y, net):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(int(x * MM), int(y * MM)))
    v.SetWidth(int(VIA_D * MM)); v.SetDrill(int(VIA_DRILL * MM))
    v.SetNet(net); v.SetLocked(True)
    board.Add(v); v.thisown = 0
    vias.append((x, y, net.GetNetname()))


def add_track(x0, y0, x1, y1, layer, net, w=STUB_W):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(int(x0 * MM), int(y0 * MM)))
    t.SetEnd(pcbnew.VECTOR2I(int(x1 * MM), int(y1 * MM)))
    t.SetWidth(int(w * MM)); t.SetLayer(layer); t.SetNet(net); t.SetLocked(True)
    board.Add(t); t.thisown = 0
    segs.append((x0, y0, x1, y1, net.GetNetname(), layer == pcbnew.F_Cu))


done = fail = 0
failed = []
for fp in board.GetFootprints():
    fc = fp.GetPosition()
    fcx, fcy = fc.x / MM, fc.y / MM
    npads = len(list(fp.Pads()))
    ref = fp.GetReference()
    for p in fp.Pads():
        net = p.GetNetname()
        if net not in PLANE_NETS or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        ni = p.GetNet()
        px, py = p.GetPosition().x / MM, p.GetPosition().y / MM
        front = p.IsOnLayer(pcbnew.F_Cu)
        layer = pcbnew.F_Cu if front else pcbnew.B_Cu
        own = id(p)
        sz = p.GetBoundingBox()
        half = max(sz.GetWidth(), sz.GetHeight()) / MM / 2
        # exposed pad: via grid
        if ref == "U20" and p.GetNumber() == "65":
            for gx in (-2.2, 0, 2.2):
                for gy in (-2.2, 0, 2.2):
                    add_via(px + gx, py + gy, ni)
            done += 1
            continue
        # ADC GND pins: short stub in to the (GND) exposed pad (diagonal from corner pins)
        if ref == "U20" and net == "GND":
            ix, iy = fcx - px, fcy - py
            if abs(abs(ix) - abs(iy)) < 2.5 or min(abs(ix), abs(iy)) > 2.5:   # near a corner
                # straight in past the pad row, then diagonal onto the exposed pad
                if abs(iy) > abs(ix):
                    mx, my = px, py + math.copysign(0.55, iy)
                else:
                    mx, my = px + math.copysign(0.55, ix), py
                add_track(px, py, mx, my, layer, ni, 0.2)
                add_track(mx, my, mx + math.copysign(0.55, ix), my + math.copysign(0.55, iy),
                          layer, ni, 0.2)
                done += 1
                continue
            elif abs(ix) > abs(iy):
                ex, ey = px + math.copysign(1.3, ix), py
            else:
                ex, ey = px, py + math.copysign(1.3, iy)
            add_track(px, py, ex, ey, layer, ni)
            done += 1
            continue
        # preferred direction
        ux, uy = px - fcx, py - fcy
        if npads > 8 and ref != "U20":        # QFP/TSOP: go inward under the body
            ux, uy = -ux, -uy
        if abs(ux) > abs(uy):
            ux, uy = math.copysign(1, ux), 0.0
        else:
            ux, uy = 0.0, math.copysign(1, uy) if uy else 1.0
        dirs = [(ux, uy), (-uy, ux), (uy, -ux), (-ux, -uy)]
        dirs += [((a + b) / math.sqrt(2), (c + d) / math.sqrt(2))
                 for (a, c), (b, d) in [(dirs[0], dirs[1]), (dirs[0], dirs[2])]]
        placed = False
        for (dx, dy) in dirs:
            for dist in (half + 0.45, half + 0.75, half + 1.1, half + 1.6, half + 2.2, half + 3.0):
                vx, vy = round(px + dx * dist, 3), round(py + dy * dist, 3)
                if via_ok(vx, vy, net, own) and stub_ok(px, py, vx, vy, net, own, front):
                    add_track(px, py, vx, vy, layer, ni)
                    add_via(vx, vy, ni)
                    placed = True
                    break
            if placed:
                break
        if placed:
            done += 1
        else:
            fail += 1
            failed.append(f"{ref}.{p.GetNumber()}")
pcbnew.SaveBoard(sys.argv[2], board)
print(f"fanned out {done} pads, {fail} failed: {failed}")
