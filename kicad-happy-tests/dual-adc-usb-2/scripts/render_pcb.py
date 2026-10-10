"""Render a window of a board (F.Cu+B.Cu+pads+fab refs) to PNG via kicad-cli + inkscape.
usage: render_pcb.py board.kicad_pcb out.png [x0 y0 x1 y1 (mm, KiCad coords)] [dpi]"""
import os
import subprocess
import sys

K = os.path.expanduser("~/bin/kicad10-root/bin/kicad-cli")
b, out = sys.argv[1], sys.argv[2]
svg = out[:-4] + ".svg"
subprocess.run([K, "pcb", "export", "svg", "--layers", "F.Cu,B.Cu,F.Fab,Edge.Cuts", "--mode-single",
                "--exclude-drawing-sheet", "--page-size-mode", "2", "-o", svg, b],
               capture_output=True)
args = ["inkscape", svg, "--export-type=png", f"--export-filename={out}", "--export-background=white",
        "--export-background-opacity=1"]
if len(sys.argv) >= 7:
    x0, y0, x1, y1 = map(float, sys.argv[3:7])
    dpi = sys.argv[7] if len(sys.argv) > 7 else "600"
    # SVG user units are mm when page = board; export-area in px at 96 dpi -> mm*96/25.4
    s = 96 / 25.4
    args += [f"--export-area={x0 * s}:{y0 * s}:{x1 * s}:{y1 * s}", f"--export-dpi={dpi}"]
else:
    args += ["--export-dpi=100"]
subprocess.run(args, capture_output=True)
print(out)
