import sys
from pathlib import Path
from sexp import parse, find, find1
FPDIR = Path.home() / "bin/kicad10-root/share/kicad/footprints"
def info(fid):
    lib, name = fid.split(":")
    t = parse((FPDIR / f"{lib}.pretty" / f"{name}.kicad_mod").read_text())
    pads = [(str(p[1]), float(find1(p, "at")[1]), float(find1(p, "at")[2])) for p in find(t, "pad")]
    xs, ys = [], []
    for g in find(t, "fp_line") + find(t, "fp_rect") + find(t, "fp_poly"):
        lay = str(find1(g, "layer")[1])
        if "CrtYd" in lay:
            for k in ("start", "end"):
                e = find1(g, k)
                if e: xs.append(float(e[1])); ys.append(float(e[2]))
            pts = find1(g, "pts")
            if pts:
                for xy in find(pts, "xy"): xs.append(float(xy[1])); ys.append(float(xy[2]))
    return pads, (min(xs), min(ys), max(xs), max(ys)) if xs else None
if __name__ == "__main__":
    for f in sys.argv[1:]:
        pads, cy = info(f)
        print(f, "courtyard", cy)
        print("  ", sorted(set((p, round(x, 2), round(y, 2)) for p, x, y in pads))[:20])
