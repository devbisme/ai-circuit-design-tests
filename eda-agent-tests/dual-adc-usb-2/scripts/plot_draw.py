"""Companion to plot_area.py (system python with PIL)."""
import json, sys
from PIL import Image, ImageDraw
d = json.load(open("/tmp/_plot.json")); x0, y0, x1, y1 = d["win"]; S = 60
W, H = int((x1-x0)*S), int((y1-y0)*S)
im = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(im, "RGBA")
P = lambda x, y: ((x-x0)*S, (y-y0)*S)
for it in d["items"]:
    if it[0] == "trk":
        x, y, ex, ey, w = it[1]
        col = (200, 0, 0, 160) if it[3] == "F.Cu" else (0, 0, 200, 120)
        dr.line([P(x, y), P(ex, ey)], fill=col, width=max(1, int(w*S)))
for it in d["items"]:
    if it[0] == "pad":
        r = it[1]; dr.rectangle([P(r[0], r[1]), P(r[2], r[3])], outline="black", fill=(255, 200, 0, 120))
        dr.text(P(r[0], r[1]), it[3] + " " + it[2], fill="black")
    elif it[0] == "via":
        x, y = it[1]; dr.ellipse([P(x-.225, y-.225), P(x+.225, y+.225)], fill=(0, 150, 0, 200)); dr.text(P(x+.25, y), it[2], fill=(0,100,0))
for it in d["items"]:
    if it[0] == "trk" and it[2] in sys.argv[2:]:
        x, y, ex, ey, w = it[1]; dr.text(P((x+ex)/2, (y+ey)/2), it[2], fill="purple")
im.save(sys.argv[1])
