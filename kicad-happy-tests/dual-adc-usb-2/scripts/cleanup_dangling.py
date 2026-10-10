"""Remove dangling tracks/vias (left by rip-up) — non-plane nets only, repeated until stable.
usage: python3.11 cleanup_dangling.py in.kicad_pcb out.kicad_pcb"""
import sys

import pcbnew

PLANE_NETS = {"GND", "+3V3"}
TOL = pcbnew.FromMM(0.01)


def d(a, b):
    try:
        return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5
    except AttributeError:  # untyped SWIG proxy (KiCad 10 quirk): treat as connected
        return 0


def main(src, dst):
    b = pcbnew.LoadBoard(src)
    total = 0
    while True:
        tracks = [t for t in b.GetTracks() if t.GetNetname() not in PLANE_NETS and not t.IsLocked()]
        pads = [p for fp in b.GetFootprints() for p in fp.Pads()]
        removed = []
        for t in tracks:
            net = t.GetNetname()
            if t.GetClass() == "PCB_VIA":
                pos = t.GetPosition()
                n = 0
                for u in tracks:
                    if u is t or u.GetClass() == "PCB_VIA" or u.GetNetname() != net:
                        continue
                    if d(u.GetStart(), pos) < TOL or d(u.GetEnd(), pos) < TOL:
                        n += 1
                if any(p.GetNetname() == net and p.HitTest(pos) for p in pads):
                    n += 1
                if n <= 1:
                    removed.append(t)
                continue
            for end in (t.GetStart(), t.GetEnd()):
                ok = False
                for u in tracks:
                    if u is t or u.GetNetname() != net:
                        continue
                    if u.GetClass() == "PCB_VIA":
                        if d(u.GetPosition(), end) < u.GetWidth(pcbnew.F_Cu) // 2:
                            ok = True
                            break
                    elif u.GetLayer() == t.GetLayer() and (
                            d(u.GetStart(), end) < TOL or d(u.GetEnd(), end) < TOL
                            or u.HitTest(end)):
                        ok = True
                        break
                if not ok:
                    ok = any(p.GetNetname() == net and p.IsOnLayer(t.GetLayer()) and p.HitTest(end) for p in pads)
                if not ok:
                    removed.append(t)
                    break
        if not removed:
            break
        for t in removed:
            b.Remove(t)
        total += len(removed)
    b.Save(dst)
    print("removed dangling items:", total)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
