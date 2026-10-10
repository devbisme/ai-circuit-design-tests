"""
Build dual_adc_usb.kicad_pcb from a KiCad (kicadsexpr) netlist exported from the schematic.

Run with KiCad 10's python:
  ~/bin/kicad10-root/bin/python3.11 scripts/build_pcb.py dual_adc_usb.net dual_adc_usb.kicad_pcb

- 4-layer stackup: F.Cu / In1.Cu (GND plane) / In2.Cu (+3V3 plane) / B.Cu
- Main parts placed at fixed anchors (see ANCHORS); passives auto-placed next to the
  IC pad they serve (shared signal net, else least-used pad of the shared power net).
"""
import math
import re
import sys

import os

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

FPLIB = "/home/devb/bin/kicad10-root/share/kicad/footprints"
MM = pcbnew.FromMM

BOARD_W, BOARD_H = 130.0, 90.0  # mm
OX, OY = 50.0, 50.0  # board origin offset in KiCad coordinates


from build_pcb_netlist import parse_netlist  # noqa: E402


# ---------------------------------------------------------------- placement plan
# Anchor positions (mm, board-relative) and rotation for the main parts, matched by value
# and, for duplicated front-end parts, by sheet name.
ANCHORS = [
    # (match value regex, sheet regex, x, y, rot)
    # BNC: footprint body front face is 12.7 mm from pad 1 -> flush with the left edge at rot 90.
    (r"^IN_A$", "", 12.7, 20.0, 90),
    (r"^IN_B$", "", 12.7, 66.0, 90),
    (r"^OPA810", r"front_end1", 27.0, 21.0, 0),
    (r"^OPA810", r"front_end2", 27.0, 67.0, 0),
    (r"^THS4521", r"front_end1", 39.0, 27.0, 0),
    (r"^THS4521", r"front_end2", 39.0, 61.0, 0),
    (r"^LM27762", "", 22.0, 44.0, 0),
    (r"^LP5907", "", 38.0, 44.0, 0),
    (r"^LTC2291", "", 55.0, 44.0, 0),
    (r"^10MHz$", "", 48.0, 33.0, 0),
    (r"^ICE40", "", 82.0, 42.0, 0),
    (r"^25MHz$", "", 73.0, 59.0, 0),
    (r"^W25Q32", "", 92.0, 62.0, 0),
    (r"^AP2112", "", 82.0, 21.5, 0),
    (r"^IS42S16400", "", 112.0, 40.0, 0),
    # rot 180: DM/DP (pins 7/8) face the USB connector.
    (r"^FT2232HL", "", 99.0, 74.0, 180),
    (r"^93LC56B", "", 88.0, 83.0, 0),
    (r"^12MHz$", "", 107.95, 79.5, 0),  # next to OSCI/OSCO (right side after rot 180)
    # USB-B: shell extends +15.5 mm in x from pad 1; front face at the right edge.
    (r"^USB_B$", "", 115.0, 71.0, 0),
    (r"^USBLC6", "", 109.5, 74.5, 0),  # flow-through between FT2232H DM/DP and J1
    (r"^TLV62569", "", 121.0, 57.0, 0),
    (r"^GPIO$", "", 76.0, 6.0, 90),
]

# Rails that are planes: passives on these nets anchor to signal nets first.
PLANE_NETS = {"GND", "+3V3"}
# Decoupling caps of these parts go on B.Cu, under the pin rows.
BOTTOM_DECAP_OWNERS = r"^(ICE40|IS42S16400|FT2232HL)"
RAILS = {"GND", "+3V3", "+1V2", "+3V3_ADC", "+3V3A", "-3V3A", "+5V", "FT_VCORE", "FT_VPHY"}
BIG_NETS = {"GND"}


def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(f"{FPLIB}/{lib}.pretty", name)
    if fp is None:
        raise RuntimeError(f"footprint {fpid} not found")
    return fp


def bbox_mm(fp, margin=0.25):
    # Courtyard bbox if present, else full bbox.
    try:
        cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
        bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    except Exception:
        bb = fp.GetBoundingBox(False)
    return (pcbnew.ToMM(bb.GetLeft()) - margin, pcbnew.ToMM(bb.GetTop()) - margin,
            pcbnew.ToMM(bb.GetRight()) + margin, pcbnew.ToMM(bb.GetBottom()) + margin)


def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def main(netfile, pcbfile):
    comps, nets = parse_netlist(netfile)
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    ds = board.GetDesignSettings()
    ds.SetBoardThickness(MM(1.6))
    ds.m_TrackMinWidth = MM(0.1)  # Freerouting necks down to ~0.11 mm at fine-pitch pins
    ds.m_ViasMinSize = MM(0.45)
    ds.m_MinThroughDrill = MM(0.2)
    ds.m_MinClearance = MM(0.1)  # Fine net class (ADC bus) uses 0.1 mm
    ds.m_HoleClearance = MM(0.2)
    ds.m_CopperEdgeClearance = MM(0.3)
    ds.SetCustomTrackWidth(MM(0.15))
    nc = ds.m_NetSettings.GetDefaultNetclass()
    nc.SetClearance(MM(0.15))
    nc.SetTrackWidth(MM(0.15))
    nc.SetViaDiameter(MM(0.45))
    nc.SetViaDrill(MM(0.2))
    board.SetLayerName(pcbnew.In1_Cu, "In1.Cu")
    board.SetLayerName(pcbnew.In2_Cu, "In2.Cu")

    # Outline.
    def seg(x1, y1, x2, y2):
        s = pcbnew.PCB_SHAPE(board)
        s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(pcbnew.VECTOR2I(MM(OX + x1), MM(OY + y1)))
        s.SetEnd(pcbnew.VECTOR2I(MM(OX + x2), MM(OY + y2)))
        s.SetLayer(pcbnew.Edge_Cuts)
        s.SetWidth(MM(0.1))
        board.Add(s)

    seg(0, 0, BOARD_W, 0)
    seg(BOARD_W, 0, BOARD_W, BOARD_H)
    seg(BOARD_W, BOARD_H, 0, BOARD_H)
    seg(0, BOARD_H, 0, 0)

    # Nets.
    netinfo = {}
    for name in nets:
        ni = pcbnew.NETINFO_ITEM(board, name)
        board.Add(ni)
        netinfo[name] = ni
    pad_net = {}
    for name, nodes in nets.items():
        for ref, pin in nodes:
            pad_net[(ref, pin)] = name

    # Footprints.
    fps = {}
    for ref, c in sorted(comps.items()):
        if not c["footprint"] or ref.startswith("#"):
            continue
        fp = load_fp(c["footprint"])
        lib_nick, fp_name = c["footprint"].split(":")
        fp.SetFPID(pcbnew.LIB_ID(lib_nick, fp_name))
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        path = c["sheettstamps"] + c["tstamp"]
        fp.SetPath(pcbnew.KIID_PATH(path))
        fp.SetSheetname(c["sheetnames"])
        fp.SetSheetfile(c["fields"].get("Sheetfile", ""))
        for k in ("MPN", "Tolerance", "Dielectric"):
            if k in c["fields"]:
                fp.SetField(k, c["fields"][k])
                for fld in fp.GetFields():
                    if fld.GetName() == k:
                        fld.SetVisible(False)
        for pad in fp.Pads():
            n = pad_net.get((ref, pad.GetNumber()))
            if n:
                pad.SetNet(netinfo[n])
        board.Add(fp)
        fps[ref] = fp

    # ---- place anchors
    placed = {}
    occupied = []
    occupied_bot = []
    for rx, sx, x, y, rot in ANCHORS:
        hits = [r for r, c in comps.items() if r in fps and re.search(rx, c["value"])
                and re.search(sx, c["sheetnames"] or "")]
        if len(hits) != 1:
            print("anchor match problem", rx, sx, hits)
            continue
        fp = fps[hits[0]]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)))
        placed[hits[0]] = fp
        occupied.append(bbox_mm(fp))

    # Mounting holes.
    for i, (x, y) in enumerate(((3.5, 3.5), (BOARD_W - 3.5, 3.5), (3.5, BOARD_H - 3.5),
                                (BOARD_W - 3.5, BOARD_H - 3.5))):
        mh = load_fp("MountingHole:MountingHole_3.2mm_M3_Pad_Via")
        mh.SetFPID(pcbnew.LIB_ID("MountingHole", "MountingHole_3.2mm_M3_Pad_Via"))
        mh.SetBoardOnly(True)  # not in the schematic
        mh.SetReference(f"H{i + 1}")
        mh.SetValue("MountingHole")
        mh.SetPosition(pcbnew.VECTOR2I(MM(OX + x), MM(OY + y)))
        for pad in mh.Pads():
            pad.SetNet(netinfo["GND"])
        board.Add(mh)
        occupied.append(bbox_mm(mh, 0.5))

    def inside(b):
        return b[0] >= 0.5 + OX and b[1] >= 0.5 + OY and b[2] <= OX + BOARD_W - 0.5 and b[3] <= OY + BOARD_H - 0.5

    def try_place(fp, tx, ty, rot, max_r=25.0, step=0.25, bottom=False):
        occ = occupied_bot if bottom else occupied
        if bottom and not fp.IsFlipped():
            fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        fp.SetOrientationDegrees(rot)
        r = 0.0
        while r <= max_r:
            n = max(1, int(2 * math.pi * r / step)) if r > 0 else 1
            best = None
            for k in range(n):
                a = 2 * math.pi * k / n
                x, y = tx + r * math.cos(a), ty + r * math.sin(a)
                fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
                b = bbox_mm(fp)
                if inside(b) and not any(overlap(b, o) for o in occ):
                    best = (x, y)
                    break
            if best:
                fp.SetPosition(pcbnew.VECTOR2I(MM(best[0]), MM(best[1])))
                occ.append(bbox_mm(fp))
                return True
            r += step
        print("could not place", fp.GetReference())
        return False

    # ---- place everything else near the pad it serves
    pad_use = {}

    def ic_pads(net):
        out = []
        for ref, fp in placed.items():
            for pad in fp.Pads():
                if pad.GetNetname() == net:
                    out.append((ref, pad))
        return out

    remaining = [r for r in fps if r not in placed]

    # Process passives tied to signal nets of placed parts first; repeat until all placed
    # so chains (e.g. R -> C -> IC) resolve.
    for _ in range(6):
        progress = False
        for ref in list(remaining):
            fp = fps[ref]
            my_nets = [p.GetNetname() for p in fp.Pads() if p.GetNetname()]
            sig = [n for n in my_nets if n not in PLANE_NETS]
            cand = []
            sheet = comps[ref]["sheetnames"]
            for n in sig:
                for r2, pad in ic_pads(n):
                    same = comps.get(r2, {}).get("sheetnames") == sheet
                    w = (0 if same else 1, len(nets[n]))
                    cand.append((w, r2, pad))
            if not cand:
                for n in my_nets:
                    if n in BIG_NETS:
                        continue
                    for r2, pad in ic_pads(n):
                        same = comps.get(r2, {}).get("sheetnames") == sheet
                        cand.append(((0 if same else 1, -placed[r2].GetPadCount(),
                                      pad_use.get((r2, pad.GetNumber()), 0)), r2, pad))
            if not cand:
                continue
            cand.sort(key=lambda t: (t[0], t[1]))
            _, r2, pad = cand[0]
            pad_use[(r2, pad.GetNumber())] = pad_use.get((r2, pad.GetNumber()), 0) + 1
            owner = placed[r2]
            cx, cy = pcbnew.ToMM(owner.GetPosition().x), pcbnew.ToMM(owner.GetPosition().y)
            px, py = pcbnew.ToMM(pad.GetPosition().x), pcbnew.ToMM(pad.GetPosition().y)
            dx, dy = px - cx, py - cy
            d = math.hypot(dx, dy) or 1.0
            is_decap = {n.split("/")[-1] for n in my_nets} <= RAILS and len(my_nets) == 2
            bottom = is_decap and re.search(BOTTOM_DECAP_OWNERS, owner.GetValue()) is not None
            if bottom:
                dist = -1.8  # under the package, just inside the pin row
            elif owner.GetPadCount() <= 3:
                dist = 1.5
            elif owner.GetPadCount() <= 16:
                dist = 2.6  # small fine-pitch ICs: leave an escape ring
            else:
                dist = 3.5  # big fine-pitch ICs: keep a fan-out ring clear for the buses
            tx, ty = px + dist * dx / d, py + dist * dy / d
            if bottom:
                # radial direction of the pad row: use the dominant axis from the IC centre
                rot = 90 if abs(dx) > abs(dy) else 0
            else:
                rot = 0 if abs(dx) > abs(dy) else 90
            # Both pads land on pins of the same IC (e.g. a flying cap): lie parallel to those pins,
            # pad order matching, so the two connections don't cross.
            if fp.GetPadCount() == 2:
                p1, p2 = list(fp.Pads())
                o1 = [q for q in owner.Pads() if q.GetNetname() == p1.GetNetname() and p1.GetNetname() not in PLANE_NETS]
                o2 = [q for q in owner.Pads() if q.GetNetname() == p2.GetNetname() and p2.GetNetname() not in PLANE_NETS]
                if o1 and o2:
                    ax, ay = pcbnew.ToMM(o1[0].GetPosition().x), pcbnew.ToMM(o1[0].GetPosition().y)
                    bx, by = pcbnew.ToMM(o2[0].GetPosition().x), pcbnew.ToMM(o2[0].GetPosition().y)
                    # footprint pad 1 -> pad 2 runs +x at rot 0; at rot 90 it runs -y (KiCad CCW)
                    if abs(bx - ax) >= abs(by - ay):
                        rot = 0 if bx > ax else 180
                    else:
                        rot = 90 if by < ay else 270
                    mx, my = (ax + bx) / 2, (ay + by) / 2
                    ux, uy = mx - cx, my - cy
                    du = math.hypot(ux, uy) or 1.0
                    tx, ty = mx + 2.2 * ux / du, my + 2.2 * uy / du
            if try_place(fp, tx, ty, rot, bottom=bottom):
                placed[ref] = fp
                remaining.remove(ref)
                progress = True
        if not progress:
            break
    for ref in remaining:
        print("unplaced (no anchor):", ref, comps[ref]["value"])
        try_place(fps[ref], OX + BOARD_W / 2, OY + BOARD_H / 2, 0, max_r=80)

    # ---- zones: In1 GND, In2 +3V3, GND pour on F/B
    def zone(layer, net, prio=0):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(netinfo[net])
        ol = z.Outline()
        ol.NewOutline()
        for x, y in ((0.3, 0.3), (BOARD_W - 0.3, 0.3), (BOARD_W - 0.3, BOARD_H - 0.3), (0.3, BOARD_H - 0.3)):
            ol.Append(MM(OX + x), MM(OY + y))
        z.SetAssignedPriority(prio)
        z.SetLocalClearance(MM(0.2))
        z.SetMinThickness(MM(0.2))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(MM(0.25))
        z.SetThermalReliefSpokeWidth(MM(0.3))
        board.Add(z)
        return z

    zone(pcbnew.In1_Cu, "GND")
    zone(pcbnew.In2_Cu, "+3V3")
    # Outer-layer GND pours are added after routing (scripts/finish_pcb.py): Freerouting would
    # treat them as obstacles covering F.Cu/B.Cu.

    board.Save(pcbfile)
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    import netclasses
    netclasses.patch(os.path.splitext(pcbfile)[0] + ".kicad_pro")
    print("saved", pcbfile, "footprints", len(fps))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
