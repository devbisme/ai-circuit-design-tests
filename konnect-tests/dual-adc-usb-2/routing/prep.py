"""Scratch-copy routing prep: 4-layer stackup, plane zones, locked plane fanout, DSN export."""
import math, sys
import pcbnew
from pcbnew import FromMM, ToMM, VECTOR2I

SRC, OUT, DSN = sys.argv[1], sys.argv[2], sys.argv[3]
PLANES = {'GND': pcbnew.In1_Cu, '+3V3': pcbnew.In2_Cu}
VIA_D, VIA_DRILL, CLR, STUB_W = 0.6, 0.3, 0.15, 0.2
BX0, BY0, BX1, BY1 = 50, 50, 190, 140

b = pcbnew.LoadBoard(SRC)
b.SetCopperLayerCount(4)
for lay in (pcbnew.In1_Cu, pcbnew.In2_Cu):
    b.SetLayerType(lay, pcbnew.LT_POWER)

MOVES = {'R605': (142, 108.5, 0), 'C624': (139.2, 109, 90), 'C625': (144.3, 109, 90),
         'R606': (142, 75.5, 0), 'C626': (139, 75.6, 90), 'C627': (145.5, 75.6, 90),
         'R502': (143.5, 62.3, 90), 'U503': (156, 54.4, 0),
         'C311': (112, 81, 0), 'C312': (114, 81, 0), 'C313': (116, 81, 0), 'C314': (118, 81, 0), 'C316': (120, 81, 0), 'C317': (122, 81, 0), 'C315': (124.8, 81, 0),
         'C511': (145.8, 58.4, 0), 'C512': (148.4, 58.4, 0), 'C513': (151.0, 58.4, 0), 'C514': (153.6, 58.4, 0),
         'C505': (163, 61.5, 0), 'C506': (163, 63.5, 0), 'C507': (163, 65.5, 0), 'C508': (163, 67.5, 0),
         'C509': (163, 69.5, 0), 'C510': (163, 71.5, 0)}
for fp in b.GetFootprints():
    if fp.GetReference() in MOVES:
        x, y, r = MOVES[fp.GetReference()]
        fp.SetPosition(VECTOR2I(FromMM(x), FromMM(y))); fp.SetOrientationDegrees(r)

def zone(netname, layer, inset=0.5, prio=0):
    z = pcbnew.ZONE(b)
    z.SetLayer(layer)
    z.SetNet(b.FindNet(netname))
    z.SetLocalClearance(FromMM(0.3))
    z.SetMinThickness(FromMM(0.2))
    z.SetAssignedPriority(prio)
    z.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
    o = z.Outline(); o.NewOutline()
    for x, y in ((BX0+inset, BY0+inset), (BX1-inset, BY0+inset), (BX1-inset, BY1-inset), (BX0+inset, BY1-inset)):
        o.Append(FromMM(x), FromMM(y))
    b.Add(z)
for n, l in PLANES.items():
    zone(n, l)

# Obstacles: every copper pad (rect bbox, mm) with its net.
pads = []
for fp in b.GetFootprints():
    for p in fp.Pads():
        if not p.IsOnCopperLayer(): continue
        bb = p.GetBoundingBox()
        pads.append((ToMM(bb.GetLeft()), ToMM(bb.GetTop()), ToMM(bb.GetRight()), ToMM(bb.GetBottom()),
                     p.GetNetname(), p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD))
vias = []  # (x, y, net)
stubs = []  # (x0, y0, x1, y1, net)

def seg_dist(px, py, s):
    x0, y0, x1, y1 = s[:4]; dx, dy = x1 - x0, y1 - y0; L = dx*dx + dy*dy
    t = 0 if L == 0 else max(0, min(1, ((px-x0)*dx + (py-y0)*dy) / L))
    return math.hypot(px - x0 - t*dx, py - y0 - t*dy)


def rect_dist(x, y, r):
    dx = max(r[0] - x, 0, x - r[2]); dy = max(r[1] - y, 0, y - r[3])
    return math.hypot(dx, dy)

def via_ok(x, y, net):
    if not (BX0 + 1.0 < x < BX1 - 1.0 and BY0 + 1.0 < y < BY1 - 1.0):
        return False
    for r in pads:
        d = rect_dist(x, y, r)
        if r[4] == net and r[5]:
            continue  # same-net SMD pad: via may touch/sit in it
        if d < VIA_D / 2 + CLR + 0.02:
            return False
    for vx, vy, vn in vias:
        if math.hypot(vx - x, vy - y) < VIA_D + CLR + 0.02:
            return False
    for st in stubs:
        if st[4] != net and seg_dist(x, y, st) < VIA_D / 2 + STUB_W / 2 + CLR + 0.02:
            return False
    for h in ((54, 54), (186, 54), (54, 136), (186, 136)):
        if math.hypot(h[0] - x, h[1] - y) < 3.2 / 2 + 0.5 + VIA_D / 2:
            return False
    return True

def stub_ok(x0, y0, x1, y1, net, own):
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 0.1))
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n; y = y0 + (y1 - y0) * i / n
        for r in pads:
            if r is own or (r[4] == net):
                continue
            if rect_dist(x, y, r) < STUB_W / 2 + CLR + 0.02:
                return False
        for vx, vy, vn in vias:
            if vn != net and math.hypot(vx - x, vy - y) < VIA_D / 2 + STUB_W / 2 + CLR + 0.02:
                return False
        for st in stubs:
            if st[4] != net and seg_dist(x, y, st) < STUB_W + CLR + 0.02:
                return False
    return True

placed = failed = 0
fails = []
PRIORITY = {('U601','6'), ('U601','132'), ('U502','5'), ('U502','51')}
work = [(fp, p) for fp in b.GetFootprints() for p in fp.Pads() if p.IsOnCopperLayer()]
work.sort(key=lambda fpp: (fpp[0].GetReference(), fpp[1].GetNumber()) not in PRIORITY)
for fp, p in work:
    c = fp.GetPosition(); cx, cy = ToMM(c.x), ToMM(c.y)
    if True:
        net = p.GetNetname()
        if net not in PLANES or p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
            continue
        own = next(r for r in pads if abs(r[0] - ToMM(p.GetBoundingBox().GetLeft())) < 1e-6 and
                   abs(r[1] - ToMM(p.GetBoundingBox().GetTop())) < 1e-6)
        px, py = ToMM(p.GetPosition().x), ToMM(p.GetPosition().y)
        w, h = own[2] - own[0], own[3] - own[1]
        netobj = b.FindNet(net)
        if (w > 1.8 and h > 1.8) or (w * h > 2.0 and math.hypot(px - cx, py - cy) < 0.6):  # exposed pad
            nx, ny = min(3, max(1, int(w // 1.2))), min(3, max(1, int(h // 1.2)))
            for i in range(nx):
                for j in range(ny):
                    vx = own[0] + w * (i + 0.5) / nx; vy = own[1] + h * (j + 0.5) / ny
                    if via_ok(vx, vy, net):
                        vias.append((vx, vy, net)); placed += 1
                        v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(FromMM(vx), FromMM(vy)))
                        v.SetDrill(FromMM(VIA_DRILL)); v.SetWidth(FromMM(VIA_D)); v.SetNet(netobj); v.SetLocked(True); b.Add(v)
            continue
        # escape direction: away from footprint centre along dominant axis
        dx, dy = px - cx, py - cy
        if abs(dx) >= abs(dy):
            ux, uy = (1 if dx >= 0 else -1), 0
        else:
            ux, uy = 0, (1 if dy >= 0 else -1)
        if abs(dx) < 1e-3 and abs(dy) < 1e-3:
            ux, uy = 0, -1
        half = (w if ux else h) / 2
        ep = [q for q in fp.Pads() if q.GetNetname() == net and q.GetNumber() != p.GetNumber() and pcbnew.ToMM(q.GetSize(pcbnew.F_Cu).x) * pcbnew.ToMM(q.GetSize(pcbnew.F_Cu).y) > 2.0 and
              math.hypot(ToMM(q.GetPosition().x) - cx, ToMM(q.GetPosition().y) - cy) < 0.6]
        if ep:
            eb = ep[0].GetBoundingBox()
            el, et, er, ebm = ToMM(eb.GetLeft()), ToMM(eb.GetTop()), ToMM(eb.GetRight()), ToMM(eb.GetBottom())
            if ux:   # pad on left/right side: go horizontally inward
                ok = et + 0.15 < py < ebm - 0.15; tx, ty = (er - 0.3 if ux > 0 else el + 0.3), py
            else:
                ok = el + 0.15 < px < er - 0.15; tx, ty = px, (ebm - 0.3 if uy > 0 else et + 0.3)
            if ok and stub_ok(px, py, tx, ty, net, own):
                stubs.append((px, py, tx, ty, net))
                t = pcbnew.PCB_TRACK(b); t.SetStart(p.GetPosition()); t.SetEnd(VECTOR2I(FromMM(tx), FromMM(ty)))
                t.SetWidth(FromMM(STUB_W)); t.SetLayer(pcbnew.F_Cu); t.SetNet(netobj); t.SetLocked(True); b.Add(t)
                placed += 1
                continue
        cands = []
        for d in (0.7, 1.0, 1.3, 1.7, 2.2, 2.7, 3.2, 3.8, 4.5):
            for lat in (0, 0.5, -0.5, 1.0, -1.0, 1.5, -1.5, 2.0, -2.0, 2.5, -2.5):
                cands.append((px + ux * (half + d) - uy * lat, py + uy * (half + d) + ux * lat))
        for d in (0.8, 1.2):  # perpendicular fallbacks (two-pin parts)
            for s in (1, -1):
                hp = (h if ux else w) / 2
                cands.append((px - uy * s * (hp + d), py + ux * s * (hp + d)))
        done = False
        trials = []
        for vx, vy in cands:
            kx, ky = (px + ux * (half + 0.45), py + uy * (half + 0.45))
            trials.append((vx, vy, [(px, py), (vx, vy)]))
            if abs((vx - px) * uy - (vy - py) * ux) > 1e-6:
                trials.append((vx, vy, [(px, py), (kx, ky), ((vx if ux == 0 else kx), (ky if ux == 0 else vy)), (vx, vy)]))
        for vx, vy, path in trials:
            if via_ok(vx, vy, net) and all(stub_ok(a[0], a[1], c[0], c[1], net, own) for a, c in zip(path, path[1:])):
                vias.append((vx, vy, net)); placed += 1
                v = pcbnew.PCB_VIA(b); v.SetPosition(VECTOR2I(FromMM(vx), FromMM(vy)))
                v.SetDrill(FromMM(VIA_DRILL)); v.SetWidth(FromMM(VIA_D)); v.SetNet(netobj); v.SetLocked(True); b.Add(v)
                for a, c in zip(path, path[1:]):
                    if math.hypot(c[0] - a[0], c[1] - a[1]) < 1e-6: continue
                    stubs.append((a[0], a[1], c[0], c[1], net))
                    t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(FromMM(a[0]), FromMM(a[1]))); t.SetEnd(VECTOR2I(FromMM(c[0]), FromMM(c[1])))
                    t.SetWidth(FromMM(STUB_W)); t.SetLayer(pcbnew.F_Cu); t.SetNet(netobj); t.SetLocked(True); b.Add(t)
                done = True
                break
        if not done:  # share an existing same-net via
            for vx, vy, vn in sorted((v for v in vias if v[2] == net), key=lambda v: math.hypot(v[0]-px, v[1]-py)):
                if math.hypot(vx - px, vy - py) > 3.5: break
                kx, ky = (px + ux * (half + 0.45), py + uy * (half + 0.45))
                for path in ([(px, py), (vx, vy)], [(px, py), (kx, ky), ((vx if ux == 0 else kx), (ky if ux == 0 else vy)), (vx, vy)]):
                    if all(stub_ok(a[0], a[1], c[0], c[1], net, own) for a, c in zip(path, path[1:])):
                        for a, c in zip(path, path[1:]):
                            if math.hypot(c[0] - a[0], c[1] - a[1]) < 1e-6: continue
                            stubs.append((a[0], a[1], c[0], c[1], net))
                            t = pcbnew.PCB_TRACK(b); t.SetStart(VECTOR2I(FromMM(a[0]), FromMM(a[1]))); t.SetEnd(VECTOR2I(FromMM(c[0]), FromMM(c[1])))
                            t.SetWidth(FromMM(STUB_W)); t.SetLayer(pcbnew.F_Cu); t.SetNet(netobj); t.SetLocked(True); b.Add(t)
                        done = True; placed += 1
                        break
                if done: break
        if not done:
            # debug: why
            def why(x, y):
                r=[]
                for q in pads:
                    if not (q[4]==net and q[5]) and rect_dist(x,y,q) < VIA_D/2+CLR+0.02: r.append(('pad',q[4],round(q[0],2),round(q[1],2)))
                for vx_,vy_,vn in vias:
                    if math.hypot(vx_-x,vy_-y) < VIA_D+CLR+0.02: r.append(('via',vn,round(vx_,2),round(vy_,2)))
                for st in stubs:
                    if st[4]!=net and seg_dist(x,y,st) < VIA_D/2+STUB_W/2+CLR+0.02: r.append(('stub',st[4]))
                return r[:3]
            print('FAIL', fp.GetReference(), p.GetNumber(), (round(px,2),round(py,2)), (ux,uy), 'half', round(half,2))
            for c in cands[:6]: print('   ', [round(v,2) for v in c], why(*c))
            failed += 1; fails.append(f'{fp.GetReference()}.{p.GetNumber()}({net})')

print('fanout vias placed:', placed, 'failed pads:', failed, fails)
filler = pcbnew.ZONE_FILLER(b); filler.Fill(b.Zones())
pcbnew.SaveBoard(OUT, b)
print('DSN export:', pcbnew.ExportSpecctraDSN(b, DSN))
