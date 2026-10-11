"""Turn eda-agent's generated board into a placed 4-layer board (KiCad python).

eda-agent's kicad_generate_project gives a 2-layer board with the right pad
nets, but its footprints sit on a grid, the FPIDs have no library nickname,
and nothing links them to schematic symbols. This script keeps its footprints
and nets and:
  * sets 4 copper layers and the board outline,
  * gives every footprint a full lib:name FPID plus the schematic symbol path
    (so DRC schematic parity works),
  * places ICs/connectors from a hand table, then places every other part by
    spiral search around the pads it connects to.

usage: python3.11 build_pcb.py
"""

import json
import math
import os
import re
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import board_sync  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
SRC = os.path.join(ROOT, "eda_agent_raw", "dual_adc.kicad_pcb")
DST = os.path.join(ROOT, "kicad", "dual_adc.kicad_pcb")
plan = json.load(open(os.path.join(ROOT, "plan", "dual_adc_plan.json")))
parts = {p["refdes"]: p for p in plan["parts"]}

OX, OY = 40.0, 40.0          # board origin on the page, mm
BW, BH = 125.0, 95.0         # board size, mm
mm = pcbnew.FromMM


def V(x, y):
    return pcbnew.VECTOR2I(mm(OX + x), mm(OY + y))


board = pcbnew.LoadBoard(SRC)
board.SetCopperLayerCount(4)
ds = board.GetDesignSettings()
ds.SetCopperLayerCount(4)
for lid, name in ((pcbnew.In1_Cu, "In1.GND"), (pcbnew.In2_Cu, "In2.PWR")):
    board.SetLayerName(lid, name)
    board.SetLayerType(lid, pcbnew.LT_POWER)
# Remove eda-agent's outline.
for d in list(board.GetDrawings()):
    if d.GetLayer() == pcbnew.Edge_Cuts:
        board.Remove(d)
rect = pcbnew.PCB_SHAPE(board)
rect.SetShape(pcbnew.SHAPE_T_RECT)
rect.SetStart(V(0, 0))
rect.SetEnd(V(BW, BH))
rect.SetLayer(pcbnew.Edge_Cuts)
rect.SetWidth(mm(0.1))
board.Add(rect)

fps, resync = board_sync.sync(board, force_replace=("J1",))

# --------------------------------------------------------------- placement --
FIXED = {   # ref: (x, y, rotation°)
    "J2": (14, 20, 90), "J3": (14, 72, 90),            # BNCs, mating face left
    "J1": (111, 77, 0),                                  # USB-B, mating face right
    "U8": (30, 46, 0), "U4": (21, 50, 0),
    "U9": (39, 27, 0), "U10": (39, 64, 0),
    "U11": (54, 46, 0), "X1": (44.5, 46, 0),
    "U12": (85, 45, 0), "U14": (111, 40, 0),
    "U6": (89, 77, 0), "U13": (70, 16, 0), "J4": (52, 5, 90),
    "U1": (62, 86, 0), "U2": (72, 86, 0), "U3": (52, 64, 0),
    "H1": (4, 4, 0), "H2": (121, 4, 0), "H3": (4, 91, 0), "H4": (121, 91, 0),
}
CLEAR = 0.4
ESCAPE = {"U11": 2.2, "U12": 2.6, "U14": 2.2, "U6": 2.0}   # ref: band width, mm


def crt_box(fp):
    bb = fp.GetCourtyard(pcbnew.F_CrtYd).BBox()
    if bb.GetWidth() == 0:
        bb = fp.GetBoundingBox(False)
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6)


occupied = []


def overlaps(b):
    for o in occupied:
        if b[0] < o[2] + CLEAR and b[2] > o[0] - CLEAR and b[1] < o[3] + CLEAR and b[3] > o[1] - CLEAR:
            return True
    return False


def on_board(b, margin=0.6):
    return (b[0] >= OX + margin and b[1] >= OY + margin and
            b[2] <= OX + BW - margin and b[3] <= OY + BH - margin)


for ref, (x, y, r) in FIXED.items():
    fp = fps[ref]
    fp.SetOrientationDegrees(r)
    fp.SetPosition(V(x, y))
    b = crt_box(fp)
    if ref.startswith("J") and ref != "J4":
        # Connector bodies overhang the edge; only the on-board part blocks.
        b = (max(b[0], OX), max(b[1], OY), min(b[2], OX + BW), min(b[3], OY + BH))
    occupied.append(b)
    if ref in ESCAPE:
        # Keep passives out of the fine-pitch escape-routing band.
        pb = fp.GetBoundingBox(False)
        m = ESCAPE[ref]
        occupied.append((pb.GetLeft() / 1e6 - m, pb.GetTop() / 1e6 - m,
                         pb.GetRight() / 1e6 + m, pb.GetBottom() / 1e6 + m))

net_pins = {}
for n in plan["nets"]:
    net_pins[n["name"]] = [(p["refdes"], p["pin"]) for p in n["pins"]]
power = {n["name"] for n in plan["nets"] if n.get("is_power") or n.get("is_ground")}


def pad_pos(ref, pin):
    for pad in fps[ref].Pads():
        if pad.GetNumber() == pin:
            p = pad.GetPosition()
            return p.x / 1e6, p.y / 1e6
    return None


placed = set(FIXED)
rail_use = {}          # (ic, pin) -> caps assigned
order = [p["refdes"] for p in plan["parts"]]


def anchor_points(ref):
    p = parts[ref]
    my_nets = [n for n, pins in net_pins.items() if any(r == ref for r, _ in pins)]
    pts = []
    for n in my_nets:
        if n in power:
            continue
        for r, pin in net_pins[n]:
            if r != ref and r in placed:
                pts.append(pad_pos(r, pin))
    if pts:
        return pts
    # Rail-only part (decoupling cap): pick the most recent preceding IC in plan
    # order with a pin on the rail, then its least-used rail pin.
    rails = [n for n in my_nets if n in power and n != "GND"]
    if not rails:
        return []
    rail = rails[0]
    idx = order.index(ref)
    ics = [r for r in order[:idx] if r[0] in "UX" and
           any(rr == r for rr, _ in net_pins[rail])]
    if not ics:
        ics = [r for r, _ in net_pins[rail] if r[0] in "UX" and r in placed] or \
              [r for r, _ in net_pins[rail] if r in placed and r != ref]
    if not ics:
        return []
    ic = ics[-1]
    cands = [pin for rr, pin in net_pins[rail] if rr == ic]
    pin = min(cands, key=lambda q: rail_use.get((ic, q), 0))
    rail_use[(ic, pin)] = rail_use.get((ic, pin), 0) + 1
    return [pad_pos(ic, pin)]


def place_free(fp, tx, ty):
    for radius in [i * 0.5 for i in range(0, 120)]:
        steps = max(1, int(2 * math.pi * radius / 0.5))
        for k in range(steps):
            a = 2 * math.pi * k / steps
            x, y = tx + radius * math.cos(a), ty + radius * math.sin(a)
            for rot in (0, 90):
                fp.SetOrientationDegrees(rot)
                fp.SetPosition(pcbnew.VECTOR2I(mm(round(x * 4) / 4), mm(round(y * 4) / 4)))
                b = crt_box(fp)
                if on_board(b) and not overlaps(b):
                    occupied.append(b)
                    return True
    return False


for ref in order:
    if ref in placed:
        continue
    pts = [p for p in anchor_points(ref) if p]
    if pts:
        tx = sum(p[0] for p in pts) / len(pts)
        ty = sum(p[1] for p in pts) / len(pts)
    else:
        tx, ty = OX + BW / 2, OY + BH / 2
    if not place_free(fps[ref], tx, ty):
        print("could not place", ref)
    placed.add(ref)

# Reference designators: small, on silkscreen.
for fp in fps.values():
    t = fp.Reference()
    t.SetTextSize(pcbnew.VECTOR2I(mm(0.8), mm(0.8)))
    t.SetTextThickness(mm(0.12))
    fp.Value().SetVisible(False)

board.Save(DST)
os.makedirs(os.path.join(ROOT, "route"), exist_ok=True)
if resync:
    board_sync.resync(DST)
    board = pcbnew.LoadBoard(DST)
board.Save(os.path.join(ROOT, "route", "placed.kicad_pcb"))
print("saved", DST)
