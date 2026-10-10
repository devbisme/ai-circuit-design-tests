"""Locked GND fanout + GND plane on In1 (run with KiCad 10's python3.11).

Freerouting does not treat an inner plane as connecting a net, so every GND SMD pad
gets its own via (+ short stub) to the In1.Cu GND plane here, and the GND net is then
removed from the router's job (see prep_dsn.py). Large exposed pads get a via grid.
Usage: gnd_fanout.py board.kicad_pcb
"""
import math, sys
import pcbnew

MM = pcbnew.FromMM
VIA_D, VIA_H, CLR = 0.45, 0.2, 0.17


def main(path):
    board = pcbnew.LoadBoard(path)
    gnd = board.FindNet('GND')
    obstacles = []   # (net, x0, y0, x1, y1) copper on F.Cu
    for fp in board.GetFootprints():
        for p in fp.Pads():
            if p.IsOnLayer(pcbnew.F_Cu):
                bb = p.GetBoundingBox()
                obstacles.append((p.GetNetname(), bb.GetLeft() / 1e6, bb.GetTop() / 1e6,
                                  bb.GetRight() / 1e6, bb.GetBottom() / 1e6))
    vias = []        # (x, y)
    W = board.GetBoardEdgesBoundingBox()
    bx0, by0, bx1, by1 = W.GetLeft() / 1e6, W.GetTop() / 1e6, W.GetRight() / 1e6, W.GetBottom() / 1e6

    def dist_box(x, y, b):
        dx = max(b[1] - x, 0, x - b[3]); dy = max(b[2] - y, 0, y - b[4])
        return math.hypot(dx, dy)

    def via_ok(x, y, own_box):
        if not (bx0 + 0.5 < x < bx1 - 0.5 and by0 + 0.5 < y < by1 - 0.5):
            return False
        for b in obstacles:
            if b[0] != 'GND' and dist_box(x, y, b) < VIA_D / 2 + CLR:
                return False
        return all(math.hypot(x - vx, y - vy) >= VIA_D + CLR for vx, vy in vias)

    def stub_ok(x0, y0, x1, y1, width):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.1))
        for i in range(n + 1):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            for b in obstacles:
                if b[0] != 'GND' and dist_box(x, y, b) < width / 2 + CLR:
                    return False
        return True

    def add_via(x, y):
        v = pcbnew.PCB_VIA(board)
        v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        v.SetWidth(MM(VIA_D)); v.SetDrill(MM(VIA_H)); v.SetNet(gnd); v.SetLocked(True)
        board.Add(v); vias.append((x, y))

    def add_track(x0, y0, x1, y1, w):
        t = pcbnew.PCB_TRACK(board)
        t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0))); t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
        t.SetWidth(MM(w)); t.SetLayer(pcbnew.F_Cu); t.SetNet(gnd); t.SetLocked(True)
        board.Add(t)

    done = failed = 0
    for fp in board.GetFootprints():
        has_th_gnd = any(p.GetNetname() == 'GND' and p.GetAttribute() == pcbnew.PAD_ATTRIB_PTH for p in fp.Pads())
        cx, cy = fp.GetPosition().x / 1e6, fp.GetPosition().y / 1e6
        for p in fp.Pads():
            if p.GetNetname() != 'GND' or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not p.IsOnLayer(pcbnew.F_Cu):
                continue
            px, py = p.GetPosition().x / 1e6, p.GetPosition().y / 1e6
            bb = p.GetBoundingBox()
            sx, sy = bb.GetWidth() / 1e6, bb.GetHeight() / 1e6
            if sx * sy > 4.0:                      # exposed pad
                if has_th_gnd:                     # footprint already has thermal vias
                    continue
                n = 3
                for i in range(n):
                    for j in range(n):
                        add_via(px + (i - 1) * sx / 3.5, py + (j - 1) * sy / 3.5)
                done += 1
                continue
            # outward direction: dominant axis of (pad - footprint centre)
            dx, dy = px - cx, py - cy
            dirs = []
            prim = (math.copysign(1, dx), 0) if abs(dx) >= abs(dy) else (0, math.copysign(1, dy))
            dirs = [prim, (prim[1], prim[0]), (-prim[1], -prim[0]), (-prim[0], -prim[1])]
            w = 0.2 if min(sx, sy) < 0.5 else 0.3
            ok = False
            for ux, uy in dirs:
                half = (sx if ux else sy) / 2
                for extra in (0.15, 0.35, 0.6, 0.9, 1.3):
                    for lat in (0, 0.45, -0.45, 0.8, -0.8):
                        d = half + VIA_D / 2 + extra
                        vx, vy = px + ux * d + uy * lat, py + uy * d + ux * lat
                        if via_ok(vx, vy, None) and stub_ok(px, py, vx, vy, w):
                            add_via(vx, vy); add_track(px, py, vx, vy, w)
                            ok = True; break
                    if ok: break
                if ok: break
            done += ok
            if not ok:
                failed += 1
                print('no fanout for', fp.GetReference(), p.GetNumber())
    # GND plane on In1 covering the whole board
    z = pcbnew.ZONE(board)
    z.SetLayer(pcbnew.In1_Cu); z.SetNet(gnd); z.SetLocalClearance(MM(0.2))
    z.SetMinThickness(MM(0.2)); z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    ol = z.Outline(); ol.NewOutline()
    for x, y in ((bx0, by0), (bx1, by0), (bx1, by1), (bx0, by1)):
        ol.Append(MM(x + 0.3) if x == bx0 else MM(x - 0.3), MM(y + 0.3) if y == by0 else MM(y - 0.3))
    z.SetZoneName('GND_PLANE'); board.Add(z)
    board.Save(path)
    print(f'fanout pads: {done}, failed: {failed}, vias: {len(vias)}')


if __name__ == '__main__':
    main(sys.argv[1])
