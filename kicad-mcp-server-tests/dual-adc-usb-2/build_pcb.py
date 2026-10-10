"""Populate the board outline (made by kicad-mcp-server's setup_pcb_layout) from the
schematic netlist and place the footprints. kicad-mcp-server has no tool to import a
netlist or place footprints, so this uses KiCad 10's pcbnew API directly.

    ~/bin/kicad10-root/bin/kicad-cli sch export netlist --format kicadsexpr -o dual_adc_usb.net dual_adc_usb.kicad_sch
    ~/bin/kicad10-root/bin/python3.11 build_pcb.py <outline.kicad_pcb>
"""

import copy
import json
import re
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
FPLIB = Path.home() / "bin/kicad10-root/share/kicad/footprints"
OUTLINE = Path(sys.argv[1])
BOARD = HERE / "dual_adc_usb.kicad_pcb"
MM = pcbnew.FromMM

# ---------------------------------------------------------------------------
# Netlist
# ---------------------------------------------------------------------------
net_text = re.sub(r"\s+", " ", (HERE / "dual_adc_usb.net").read_text())
comps = {}
for m in re.finditer(r'\(comp \(ref "([^"]+)"\) \(value "([^"]*)"\) \(footprint "([^"]*)"\)', net_text):
    comps[m[1]] = dict(value=m[2], fp=m[3], nets={})
for m in re.finditer(r'\(net \(code "\d+"\) \(name "([^"]+)"\)(.*?)(?=\(net \(code|$)', net_text):
    name = m[1].lstrip("/")
    for ref, pin in re.findall(r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', m[2]):
        if ref in comps:
            comps[ref]["nets"][pin] = name

# ---------------------------------------------------------------------------
# Placement: fixed parts, then clusters shelf-packed into regions (board mm, origin top-left)
# ---------------------------------------------------------------------------
FIXED = {  # ref: (x, y, rotation_deg)
    "J101": (34.2, 22, 90), "J201": (34.2, 68, 90),          # BNC faces off the left edge
    "U301": (80, 45, 0),                                      # ADC: inputs left, data right/top/bottom
    "U401": (116, 48, 0),                                     # FPGA, bank 3 faces the ADC
    "U402": (116, 12, 90),                                    # SDRAM above the FPGA, clear channel between
    "U501": (140, 50, 0),                                     # FT2232H, faces FPGA bank 1
    "J1": (146.6, 74, 90),                                    # USB-C faces off the right edge
    "J401": (147, 5, 0),                                      # GPIO header along the right edge
    "H1": (4, 4, 0), "H2": (146, 86, 0), "H3": (4, 86, 0), "H4": (100, 4, 0),
}


def rng(prefix, a, b):
    return [f"{prefix}{i}" for i in range(a, b + 1)]


def afe(n):
    b = n * 100
    return ([f"C{b+1}", f"R{b+1}", f"R{b+2}", f"C{b+2}", f"R{b+3}", f"C{b+3}", f"C{b+4}", f"D{b+1}",
             f"R{b+4}", f"U{b+1}", f"C{b+5}", f"C{b+6}", f"R{b+5}", f"R{b+6}", f"U{b+2}", f"R{b+7}",
             f"C{b+7}", f"R{b+8}", f"C{b+8}", f"C{b+10}", f"R{b+9}", f"R{b+10}", f"C{b+9}"])


TOP, BOT = "top", "bottom"
CLUSTERS = [  # (x0, y0, x1, y1), side, rotation, refs in packing order
    ((39, 4, 66, 33), TOP, 0, afe(1)),
    ((39, 57, 66, 87), TOP, 0, afe(2)),
    ((39, 35, 66, 55), TOP, 0, ["U4", "C7", "C8", "U5", "C9", "C10", "U6", "C11", "C12", "C13", "R4", "R5"]),
    ((67, 30, 80, 39), TOP, 0, ["C316", "C308", "C309", "C310", "C311", "C301", "C302", "R301", "R302"]),
    ((67, 51, 80, 60), TOP, 0, ["C317", "C312", "C313", "C314", "C315", "C303", "C304", "C305"]),
    ((86, 33, 91, 60), TOP, 90, rng("RN", 301, 307)),
    ((80.5, 51.5, 85.5, 56), TOP, 0, ["C306", "C307"]),
    ((68, 62, 98, 72), TOP, 0, ["Y301", "FB301", "C318", "C319", "R303", "R304", "R305"]),
    ((107, 39, 126, 57), BOT, 0, rng("C", 405, 419)),                       # FPGA decoupling, under it
    ((106, 8.3, 126, 15.7), BOT, 0, rng("C", 421, 428)),                     # SDRAM decoupling, under it
    ((135.6, 45.6, 144.4, 54.4), BOT, 0, ["C505", "C507", "C509", "C510", "C511", "C513", "C514", "C515"]),                      # FT2232H decoupling, under it
    ((100, 62, 132, 72), TOP, 0, ["R408", "R401", "C401", "C402", "R402", "C403", "C404", "U403", "R406",
                                  "R407", "C420", "R403", "R404", "R405"]),
    ((100, 73, 128, 80), TOP, 0, ["R409", "D401", "R410", "D402"]),
    ((128, 26, 144, 42), TOP, 0, ["Y501", "C502", "C503", "U502", "R503", "R504", "R505", "R506", "C501"]),
    ((133, 58, 149, 66), TOP, 0, ["R501", "R502", "FB501", "C504", "FB502", "C506", "C508", "C512", "C516"]),
    ((68, 73, 99, 88), TOP, 0, ["U2", "L1", "C2", "C3", "C4", "U3", "C5", "C6", "R6", "D1"]),
    ((112, 81.5, 141, 89), TOP, 0, ["U1", "F1", "R1", "R2", "R3", "C1"]),
]


def load_fp(fpid):
    lib, name = fpid.split(":")
    fp = pcbnew.FootprintLoad(str(FPLIB / f"{lib}.pretty"), name)
    if fp is None:
        raise RuntimeError(f"footprint {fpid} not found")
    fp.SetFPID(pcbnew.LIB_ID(lib, name))
    return fp


def courtyard(fp):
    cy = fp.GetCourtyard(pcbnew.B_CrtYd if fp.IsFlipped() else pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return bb.GetX(), bb.GetY(), bb.GetRight(), bb.GetBottom()


POWER_NETS = ["GND", "VBUS", "+5V", "+3V3", "+3V3A", "+3V0A", "-3V3A", "+1V2", "+1V8_FT", "SW_3V3",
              "CPOUT", "CP_P", "CP_N", "VPHY", "VPLL", "VCCPLL0", "VCCPLL1", "OSC_VDD"]


def set_rules():
    """Net classes and rules live in the .kicad_pro, which board.Save() rewrites; patch it after."""
    p = HERE / "dual_adc_usb.kicad_pro"
    d = json.loads(p.read_text())
    ns = d["net_settings"]
    dflt = next(c for c in ns["classes"] if c["name"] == "Default")
    dflt.update(clearance=0.15, track_width=0.15, via_diameter=0.45, via_drill=0.2)
    pwr = copy.deepcopy(dflt)
    pwr.update(name="Power", track_width=0.3, priority=0)
    ns["classes"] = [dflt, pwr]
    ns["netclass_patterns"] = [{"netclass": "Power", "pattern": n} for n in POWER_NETS]
    r = d["board"]["design_settings"]["rules"]
    r.update(min_track_width=0.15, min_clearance=0.15, min_through_hole_diameter=0.2, min_via_diameter=0.45)
    p.write_text(json.dumps(d, indent=2))


def main():
    board = pcbnew.LoadBoard(str(OUTLINE))
    board.SetCopperLayerCount(4)
    netinfo = {}
    for c in comps.values():
        for n in c["nets"].values():
            if n not in netinfo:
                ni = pcbnew.NETINFO_ITEM(board, n)
                board.Add(ni)
                netinfo[n] = ni
    fps = {}
    for ref, c in comps.items():
        fp = load_fp(c["fp"])
        fp.SetReference(ref)
        fp.SetValue(c["value"])
        if ref == "J1":  # library footprint numbers the USB-C shell "SH"; the symbol's pin is "S1"
            for pad in fp.Pads():
                if pad.GetNumber() == "SH":
                    pad.SetNumber("S1")
        for pad in fp.Pads():
            n = c["nets"].get(pad.GetNumber())
            if n and not n.startswith("unconnected-"):  # no-connect pins stay netless, as KiCad does
                pad.SetNet(netinfo[n])
        board.Add(fp)
        fps[ref] = fp

    placed = set()
    for ref, (x, y, rot) in FIXED.items():
        fps[ref].SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        fps[ref].SetOrientationDegrees(rot)
        placed.add(ref)

    gap = MM(0.6)
    for (x0, y0, x1, y1), side, rot, refs in CLUSTERS:
        cx, cy, row_h = MM(x0), MM(y0), 0
        for ref in refs:
            fp = fps[ref]
            fp.SetPosition(pcbnew.VECTOR2I(0, 0))
            fp.SetOrientationDegrees(rot)
            if side == BOT and not fp.IsFlipped():
                fp.Flip(fp.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
            bx0, by0, bx1, by1 = courtyard(fp)
            w, h = bx1 - bx0, by1 - by0
            if cx + w > MM(x1) and cx > MM(x0):
                cx, cy, row_h = MM(x0), cy + row_h + gap, 0
            if cy + h > MM(y1):
                print(f"!! cluster at ({x0},{y0}) overflows at {ref}")
            fp.SetPosition(pcbnew.VECTOR2I(cx - bx0, cy - by0))
            cx += w + gap
            row_h = max(row_h, h)
            placed.add(ref)
    missing = set(fps) - placed
    if missing:
        print("!! unplaced:", sorted(missing))
    board.Save(str(BOARD))
    set_rules()
    print(f"{len(fps)} footprints, {len(netinfo)} nets -> {BOARD.name}")


if __name__ == "__main__":
    main()
