"""Run with KiCad 10 python. Net classes, inner planes, locked GND/+3V3 fanout, DSN export.

usage: python3.11 route_prep.py <board.kicad_pcb> <out.dsn>
"""
import json
import math
import sys
from pathlib import Path

import pcbnew

BOARD, DSN = Path(sys.argv[1]), Path(sys.argv[2])
PRO = BOARD.with_suffix(".kicad_pro")
PLANES = {"GND": pcbnew.In1_Cu, "+3V3": pcbnew.In2_Cu}
POWER_NETS = ["VBUS", "+5V", "+5VA", "-5VA", "+3VA", "+1V2", "/Power/BUCK_SW", "/Power/CP_FLYP",
              "/Power/CP_FLYN", "/ADC/OSC_VDD", "/FPGA/VCCPLL0", "/FPGA/VCCPLL1", "/USB/FT_VPHY",
              "/USB/FT_VCORE", "/USB/FT_VCCA"]
VIA_D, VIA_DRILL = 0.45, 0.2
CLR = 0.16
mm = pcbnew.FromMM


def patch_pro():
    d = json.loads(PRO.read_text())
    ns = d["net_settings"]
    base = dict(ns["classes"][0])
    base.update(name="Default", clearance=0.15, track_width=0.2, via_diameter=VIA_D, via_drill=VIA_DRILL)
    pwr = dict(base)
    pwr.update(name="Power", track_width=0.4, via_diameter=0.6, via_drill=0.3, priority=0)
    ns["classes"] = [base, pwr]
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER_NETS]
    r = d["board"]["design_settings"]["rules"]
    r.update(min_through_hole_diameter=0.2, min_via_diameter=0.45, min_track_width=0.127,
             min_hole_clearance=0.2, min_copper_edge_clearance=0.3, min_via_annular_width=0.1)
    PRO.write_text(json.dumps(d, indent=2))


def main():
    patch_pro()
    b = pcbnew.LoadBoard(str(BOARD))
    # inner layers as planes
    b.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)
    b.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_POWER)
    # remove old zones / fanout
    for z in list(b.Zones()):
        b.Remove(z)
    for t in list(b.GetTracks()):
        if t.IsLocked():
            b.Remove(t)
    edge = b.GetBoardEdgesBoundingBox()
    x0, y0, x1, y1 = (pcbnew.ToMM(v) for v in (edge.GetLeft(), edge.GetTop(), edge.GetRight(), edge.GetBottom()))
    for net, layer in PLANES.items():
        z = pcbnew.ZONE(b)
        z.SetLayer(layer)
        z.SetNet(b.FindNet(net))
        z.SetIsRuleArea(False)
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
            ol.Append(mm(x), mm(y))
        z.SetMinThickness(mm(0.2))
        z.SetLocalClearance(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        z.SetAssignedPriority(0)
        b.Add(z)

    # ---------------------------------------------------------------- fanout
    pads = [p for f in b.GetFootprints() for p in f.Pads() if p.IsOnCopperLayer()]
    obst = []      # (x0,y0,x1,y1,netname) in mm
    for p in pads:
        bb = p.GetBoundingBox()
        obst.append((pcbnew.ToMM(bb.GetLeft()), pcbnew.ToMM(bb.GetTop()), pcbnew.ToMM(bb.GetRight()),
                     pcbnew.ToMM(bb.GetBottom()), p.GetNetname()))
    vias = []      # (x, y, net)
    hole_obst = [] # non-plated / TH holes
    for p in pads:
        if p.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH, pcbnew.PAD_ATTRIB_NPTH):
            c = p.GetPosition()
            hole_obst.append((pcbnew.ToMM(c.x), pcbnew.ToMM(c.y), pcbnew.ToMM(max(p.GetSize().x, p.GetSize().y)) / 2))

    def box_dist(x, y, o):
        dx = max(o[0] - x, 0, x - o[2])
        dy = max(o[1] - y, 0, y - o[3])
        return math.hypot(dx, dy)

    def ok_via(x, y, net, own):
        r = VIA_D / 2
        if not (x0 + 0.6 < x < x1 - 0.6 and y0 + 0.6 < y < y1 - 0.6):
            return False
        for o in obst:
            if o is own:
                continue
            need = r + (0.0 if o[4] == net else CLR)
            if o[4] == net and box_dist(x, y, o) < 0.01 and False:
                continue
            if box_dist(x, y, o) < need:
                return False
        for vx, vy, vn in vias:
            if math.hypot(vx - x, vy - y) < VIA_D + (0.25 if vn != net else 0.25):
                return False
        for hx, hy, hr in hole_obst:
            if math.hypot(hx - x, hy - y) < hr + r + 0.25:
                return False
        return True

    def ok_stub(ax, ay, bx, by, net, own):
        n = 8
        for k in range(1, n + 1):
            x, y = ax + (bx - ax) * k / n, ay + (by - ay) * k / n
            for o in obst:
                if o is own or o[4] == net:
                    continue
                if box_dist(x, y, o) < 0.125 + CLR:
                    return False
        return True

    placed, failed = 0, []
    for p in pads:
        net = p.GetNetname()
        if net not in PLANES or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD or not p.IsOnLayer(pcbnew.F_Cu):
            continue
        f = p.GetParentFootprint()
        own = next(o for o in obst if abs(o[0] - pcbnew.ToMM(p.GetBoundingBox().GetLeft())) < 1e-6
                   and abs(o[1] - pcbnew.ToMM(p.GetBoundingBox().GetTop())) < 1e-6 and o[4] == net)
        px, py = pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)
        sx, sy = pcbnew.ToMM(p.GetBoundingBox().GetWidth()) / 2, pcbnew.ToMM(p.GetBoundingBox().GetHeight()) / 2
        # big pads (exposed pads): vias inside the pad
        if sx > 1.5 and sy > 1.5:
            n = 3
            for i in range(n):
                for j in range(n):
                    vx = px + (i - (n - 1) / 2) * min(sx, 3) * 0.6
                    vy = py + (j - (n - 1) / 2) * min(sy, 3) * 0.6
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
                    v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL))
                    v.SetNet(p.GetNet()); v.SetLocked(True)
                    b.Add(v); vias.append((vx, vy, net))
            placed += 1
            continue
        fc = f.GetPosition()
        fx, fy = pcbnew.ToMM(fc.x), pcbnew.ToMM(fc.y)
        dirs = []
        if f.GetPadCount() <= 3:
            # two/three-terminal part: away from footprint centre
            dx, dy = px - fx, py - fy
        else:
            dx, dy = px - fx, py - fy
            # snap to the pad's long axis for IC pins
            if sx > sy:
                dx, dy = (1 if dx > 0 else -1), 0
            else:
                dx, dy = 0, (1 if dy > 0 else -1)
        L = math.hypot(dx, dy) or 1
        dx, dy = dx / L, dy / L
        base = [(dx, dy), (-dy, dx), (dy, -dx), (dx * 0.7 - dy * 0.7, dy * 0.7 + dx * 0.7),
                (dx * 0.7 + dy * 0.7, dy * 0.7 - dx * 0.7)]
        done = False
        for ddx, ddy in base:
            ext = abs(ddx) * sx + abs(ddy) * sy
            for extra in (0.35, 0.55, 0.8, 1.1, 1.5, 2.0):
                vx, vy = px + ddx * (ext + extra), py + ddy * (ext + extra)
                if ok_via(vx, vy, net, own) and ok_stub(px, py, vx, vy, net, own):
                    t = pcbnew.PCB_TRACK(b)
                    t.SetStart(pcbnew.VECTOR2I(mm(px), mm(py)))
                    t.SetEnd(pcbnew.VECTOR2I(mm(vx), mm(vy)))
                    t.SetWidth(mm(0.25)); t.SetLayer(pcbnew.F_Cu)
                    t.SetNet(p.GetNet()); t.SetLocked(True)
                    b.Add(t)
                    v = pcbnew.PCB_VIA(b)
                    v.SetPosition(pcbnew.VECTOR2I(mm(vx), mm(vy)))
                    v.SetWidth(mm(VIA_D)); v.SetDrill(mm(VIA_DRILL))
                    v.SetNet(p.GetNet()); v.SetLocked(True)
                    b.Add(v)
                    vias.append((vx, vy, net))
                    obst.append((vx - VIA_D / 2, vy - VIA_D / 2, vx + VIA_D / 2, vy + VIA_D / 2, net))
                    placed += 1
                    done = True
                    break
            if done:
                break
        if not done:
            failed.append(f"{f.GetReference()}.{p.GetNumber()}")
    print(f"fanout: {placed} pads, failed {len(failed)}: {failed}")
    filler = pcbnew.ZONE_FILLER(b)
    filler.Fill(b.Zones())
    b.Save(str(BOARD))
    patch_pro()   # Save() rewrites the project file
    pcbnew.ExportSpecctraDSN(b, str(DSN))
    print("wrote", DSN)


main()
