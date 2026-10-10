"""Prepare the placed board for Freerouting.

1. GND fanout: every SMD GND pad gets a locked via (plus a short stub) to the In1.Cu
   GND plane; exposed pads get a small via array.
2. Export Specctra DSN, then edit it: In1.Cu becomes a plane layer (not routed), and the
   GND net is cut to one pin so Freerouting does not try to route it with tracks.
   (Freerouting does not treat KiCad zones as connecting a net.)

    ~/bin/kicad10-root/bin/python3.11 route_prep.py <work_dir>
"""

import math
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
WORK = Path(sys.argv[1])
MM, TOMM = pcbnew.FromMM, pcbnew.ToMM
CLR = 0.17           # mm, a little over the 0.15 board clearance
KEEP = {}            # plane net -> DSN pins left in the net (failed fanouts + a partner)
VIA_SIZES = [(0.5, 0.25), (0.45, 0.2)]


def seg_point_dist(ax, ay, bx, by, px, py):
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)


class Obstacles:
    """Copper of other nets as circles/rects (mm) for coarse clearance checks."""

    def __init__(self, board):
        self.items = []  # (net, kind, geom)
        self.segs = []   # (net, x0, y0, x1, y1, w) fanout stubs
        for fp in board.GetFootprints():
            for p in fp.Pads():
                bb = p.GetBoundingBox()
                self.items.append((p.GetNetname(), "rect",
                                   (TOMM(bb.GetX()), TOMM(bb.GetY()), TOMM(bb.GetRight()), TOMM(bb.GetBottom())),
                                   p.IsOnCopperLayer() and p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH)))
        edge = board.GetBoardEdgesBoundingBox()
        self.edge = (TOMM(edge.GetX()), TOMM(edge.GetY()), TOMM(edge.GetRight()), TOMM(edge.GetBottom()))

    def add_via(self, net, x, y, r):
        self.items.append((net, "circle", (x, y, r), True))

    def add_seg(self, net, x0, y0, x1, y1, w):
        self.segs.append((net, x0, y0, x1, y1, w))

    def via_ok(self, net, x, y, r):
        for n, ax, ay, bx, by, w in self.segs:
            if n != net and seg_point_dist(ax, ay, bx, by, x, y) < r + w / 2 + CLR:
                return False
        ex0, ey0, ex1, ey1 = self.edge
        if not (ex0 + 0.6 + r < x < ex1 - 0.6 - r and ey0 + 0.6 + r < y < ey1 - 0.6 - r):
            return False
        for n, kind, g, _ in self.items:
            if kind == "rect":
                x0, y0, x1, y1 = g
                dx = max(x0 - x, 0, x - x1)
                dy = max(y0 - y, 0, y - y1)
                d = math.hypot(dx, dy)
                need = r + CLR if n != net or n == "" else r + 0.05
                # a via must not sit on a same-net pad of another part either (solder wicking)
                if d < need:
                    return False
            else:
                cx, cy, cr = g
                if math.hypot(cx - x, cy - y) < cr + r + CLR:
                    return False
        return True

    def stub_ok(self, net, pad, x0, y0, x1, y1, w):
        for n, ax, ay, bx, by, sw in self.segs:
            if n == net:
                continue
            for k in range(11):
                px, py = x0 + (x1 - x0) * k / 10, y0 + (y1 - y0) * k / 10
                if seg_point_dist(ax, ay, bx, by, px, py) < (w + sw) / 2 + CLR:
                    return False
        for n, kind, g, _ in self.items:
            if kind == "circle" and n != net:
                cx, cy, cr = g
                if seg_point_dist(x0, y0, x1, y1, cx, cy) < cr + w / 2 + CLR:
                    return False
        for n, kind, g, _ in self.items:
            if kind != "rect" or n == net:
                continue
            rx0, ry0, rx1, ry1 = g
            # sample the stub against the rect
            for k in range(11):
                t = k / 10
                px, py = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                dx = max(rx0 - px, 0, px - rx1)
                dy = max(ry0 - py, 0, py - ry1)
                if math.hypot(dx, dy) < w / 2 + CLR:
                    return False
        return True


def add_via(board, net, x, y, size, drill):
    v = pcbnew.PCB_VIA(board)
    v.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
    v.SetWidth(MM(size))
    v.SetDrill(MM(drill))
    v.SetNet(net)
    v.SetLocked(True)
    board.Add(v)


def add_track(board, net, layer, x0, y0, x1, y1, w):
    t = pcbnew.PCB_TRACK(board)
    t.SetStart(pcbnew.VECTOR2I(MM(x0), MM(y0)))
    t.SetEnd(pcbnew.VECTOR2I(MM(x1), MM(y1)))
    t.SetWidth(MM(w))
    t.SetLayer(layer)
    t.SetNet(net)
    t.SetLocked(True)
    board.Add(t)


def fanout(board, netname="GND", obs=None):
    obs = obs or Obstacles(board)
    gnd = board.FindNet(netname)
    done, failed = 0, []
    for fp in board.GetFootprints():
        fc = fp.GetPosition()
        fcx, fcy = TOMM(fc.x), TOMM(fc.y)
        for pad in fp.Pads():
            if pad.GetNetname() != netname or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            if not pad.IsOnCopperLayer():
                continue
            px, py = TOMM(pad.GetPosition().x), TOMM(pad.GetPosition().y)
            sx, sy = TOMM(pad.GetBoundingBox().GetWidth()), TOMM(pad.GetBoundingBox().GetHeight())
            if sx > 1.8 and sy > 1.8:  # exposed/thermal pad: via array inside it
                nx, ny = min(3, int(sx / 1.1)), min(3, int(sy / 1.1))
                for i in range(nx):
                    for j in range(ny):
                        x = px + (i - (nx - 1) / 2) * 1.1
                        y = py + (j - (ny - 1) / 2) * 1.1
                        add_via(board, gnd, x, y, 0.5, 0.25)
                        obs.add_via(netname, x, y, 0.25)
                done += 1
                continue
            if fp.GetPadCount() > 4 and sx * sy > 1.2 and min(sx, sy) >= 0.85:  # small exposed pad: one via in its centre
                add_via(board, gnd, px, py, 0.45, 0.2)
                obs.add_via(netname, px, py, 0.225)
                done += 1
                continue
            # candidate directions: outward from the footprint centre first
            ox, oy = px - fcx, py - fcy
            dirs = []
            if abs(ox) >= abs(oy):
                dirs = [(math.copysign(1, ox or 1), 0), (0, 1), (0, -1), (-math.copysign(1, ox or 1), 0)]
            else:
                dirs = [(0, math.copysign(1, oy or 1)), (1, 0), (-1, 0), (0, -math.copysign(1, oy or 1))]
            ok = False
            for size, drill in VIA_SIZES:
                for dx, dy in dirs:
                    half = (sx if dx else sy) / 2
                    for extra in (0.15, 0.35, 0.6, 0.9, 1.3):
                        d = half + size / 2 + extra
                        x, y = px + dx * d, py + dy * d
                        if obs.via_ok(netname, x, y, size / 2) and obs.stub_ok(netname, pad, px, py, x, y, 0.3):
                            add_via(board, gnd, x, y, size, drill)
                            add_track(board, gnd, pad.GetLayer() if pad.GetLayer() >= 0 else pcbnew.F_Cu,
                                      px, py, x, y, 0.3)
                            obs.add_via(netname, x, y, size / 2)
                            obs.add_seg(netname, px, py, x, y, 0.3)
                            ok = True
                            break
                    if ok:
                        break
                if ok:
                    break
            if ok:
                done += 1
            else:
                failed.append(f"{fp.GetReference()}.{pad.GetNumber()}")
    print(f"{netname} fanout: {done} pads, {len(failed)} failed: {failed}")
    # failed pads stay routable: keep each one plus its nearest fanned-out pad in the DSN net
    pads = {f"{fp.GetReference()}-{p.GetNumber()}": p for fp in board.GetFootprints() for p in fp.Pads()
            if p.GetNetname() == netname and p.GetNumber()}
    keep = set()
    for f in failed:
        fp_pad = pads[f.replace(".", "-")]
        keep.add(f.replace(".", "-"))
        others = [(k, (p.GetPosition() - fp_pad.GetPosition()).EuclideanNorm()) for k, p in pads.items()
                  if k.replace("-", ".") not in failed]
        keep.add(min(others, key=lambda kv: kv[1])[0])
    KEEP[netname] = keep
    return obs


# plane net -> inner layer it lives on (set PLANES=GND only for the GND-only variant)
PLANES = {"GND": "In1.Cu"}  # "+3V3": "In2.Cu" was tried as a variant


def patch_dsn(src, dst):
    t = src.read_text()
    for net, layer in PLANES.items():
        # plane layer: not used for routing
        t, n = re.subn(r'\(layer ' + re.escape(layer) + r'\s*\(type signal\)', f"(layer {layer} (type power)", t)
        assert n == 1, f"{layer} not found in DSN"
        # plane net: keep a single pin so the router leaves it alone
        m = re.search(r'\(net "?' + re.escape(net) + r'"?\s*\(pins ([^)]*)\)', t)
        pins = m.group(1).split()
        kept = [p for p in pins if p in KEEP.get(net, ())] or pins[:1]
        t = t[:m.start(1)] + " ".join(kept) + t[m.end(1):]
        print(f"DSN: {net} cut from {len(pins)} pins to {kept}, {layer} made a plane")
    dst.write_text(t)


def main():
    board = pcbnew.LoadBoard(str(HERE / "dual_adc_usb.kicad_pcb"))
    obs = None
    for net in PLANES:
        obs = fanout(board, net, obs)
    out = WORK / "fanout.kicad_pcb"
    board.Save(str(out))
    dsn = WORK / "board.dsn"
    pcbnew.ExportSpecctraDSN(board, str(dsn))
    patch_dsn(dsn, WORK / "route.dsn")


if __name__ == "__main__":
    main()
