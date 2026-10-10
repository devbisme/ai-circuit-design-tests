"""Floorplan placement for dual_adc_usb (run with KiCad 10's python3.11).

kicad-mcp-pro's pcb_sync_from_schematic imported the footprints and nets, but its
force-directed placement scored 1/100 (overlaps, connectors off the edges). This script:
  * sets 4 copper layers and a W x H board outline,
  * puts connectors / ICs at hand-chosen floorplan positions,
  * places every remaining part greedily next to the IC pad it connects to.
Usage: place_board.py board.kicad_pcb
"""
import math, sys
import pcbnew

W, H = 115.0, 85.0
MM = pcbnew.FromMM
POWER = {'GND', '+3V3', '+5V', '+1V2', '+3.3VA', '+4V5A', '-4V5A', 'VBUS'}

# ref: (x, y, rotation_deg)
FIXED = {
    'J201': (12.7, 22.0, 90), 'J301': (12.7, 63.0, 90),          # BNC, mouth to the left edge
    'U201': (26.0, 16.0, 0), 'U202': (36.0, 22.0, 0),            # AFE A
    'U301': (26.0, 69.0, 0), 'U302': (36.0, 63.0, 0),            # AFE B
    'U104': (24.0, 42.5, 0),                                     # +/-4.5 V
    'U103': (36.0, 42.5, 0),                                     # +3.3VA LDO
    'U401': (48.0, 42.5, 0),                                     # ADC
    'X401': (41.0, 33.0, 0), 'U402': (53.0, 31.0, 0),            # 10 MHz clock + buffer
    'U501': (78.0, 40.0, 0),                                     # FPGA
    'X501': (90.0, 25.0, 0), 'J501': (66.0, 6.0, 90),            # 50 MHz, GPIO header
    'U601': (78.0, 70.0, 90),                                    # SDRAM
    'U502': (97.0, 60.0, 0),                                     # config flash
    'U702': (101.0, 27.0, 180), 'U703': (97.0, 13.0, 0), 'Y701': (110.0, 20.0, 0),
    'J701': (100.5, 47.0, 0), 'U701': (108.0, 38.0, 0),          # USB-B, ESD
    'U101': (104.0, 70.0, 0), 'U102': (104.0, 78.0, 0),          # 3V3, 1V2 LDOs
}
# preferred anchor for parts whose only links are power rails
ANCHOR_BY_HUNDREDS = {'1': 'U101', '2': 'U202', '3': 'U302', '4': 'U401', '5': 'U501', '6': 'U601', '7': 'U702'}


def bbox(fp, margin=0.25):
    cy = fp.GetCourtyard(pcbnew.F_CrtYd)
    bb = cy.BBox() if cy.OutlineCount() else fp.GetBoundingBox(False)
    return (bb.GetLeft() / 1e6 - margin, bb.GetTop() / 1e6 - margin,
            bb.GetRight() / 1e6 + margin, bb.GetBottom() / 1e6 + margin)


def overlap(a, b):
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def main(path):
    board = pcbnew.LoadBoard(path)
    board.SetCopperLayerCount(4)
    # outline
    for d in list(board.GetDrawings()):
        if d.GetLayer() == pcbnew.Edge_Cuts:
            board.Remove(d)
    rect = pcbnew.PCB_SHAPE(board, pcbnew.SHAPE_T_RECT)
    rect.SetStart(pcbnew.VECTOR2I(0, 0)); rect.SetEnd(pcbnew.VECTOR2I(MM(W), MM(H)))
    rect.SetLayer(pcbnew.Edge_Cuts); rect.SetWidth(MM(0.1)); board.Add(rect)

    fps = {fp.GetReference(): fp for fp in board.GetFootprints()}
    placed = []
    for ref, (x, y, rot) in FIXED.items():
        fp = fps[ref]
        fp.SetOrientationDegrees(rot)
        fp.SetPosition(pcbnew.VECTOR2I(MM(x), MM(y)))
        # ICs get a wider keep-clear band so pins can escape (fine pitch needs room)
        placed.append(bbox(fp, 1.2 if ref.startswith('U') and len(list(fp.Pads())) > 8 else 0.3))

    majors = [r for r in FIXED]
    nets_of = {r: {p.GetNetname() for p in fp.Pads() if p.GetNetname()} for r, fp in fps.items()}
    used_pads = set()

    def anchor_pad(ref):
        sig = nets_of[ref] - POWER
        best, best_score = None, -1
        for m in majors:
            s = 10 * len(sig & nets_of[m]) + (5 if m == ANCHOR_BY_HUNDREDS.get(ref.lstrip('ACDFJLNRUXY')[:1]) else 0)
            if s > best_score:
                best, best_score = m, s
        fp = fps[best]
        cands = [p for p in fp.Pads() if p.GetNetname() in (sig or (nets_of[ref] - {'GND'}) or nets_of[ref])]
        fresh = [p for p in cands if (best, p.GetNumber()) not in used_pads] or cands or list(fp.Pads())
        pad = fresh[0]
        used_pads.add((best, pad.GetNumber()))
        return pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6

    others = sorted((r for r in fps if r not in FIXED), key=lambda r: (r[0] not in 'RC', r))
    for ref in others:
        fp = fps[ref]
        ax, ay = anchor_pad(ref)
        done = False
        for radius in [i * 0.5 for i in range(1, 80)]:
            n = max(8, int(2 * math.pi * radius / 0.8))
            for k in range(n):
                t = 2 * math.pi * k / n
                x, y = ax + radius * math.cos(t), ay + radius * math.sin(t)
                for rot in (0, 90):
                    fp.SetOrientationDegrees(rot)
                    fp.SetPosition(pcbnew.VECTOR2I(MM(round(x / 0.25) * 0.25), MM(round(y / 0.25) * 0.25)))
                    bb = bbox(fp)
                    if bb[0] < 1 or bb[1] < 1 or bb[2] > W - 1 or bb[3] > H - 1:
                        continue
                    if any(overlap(bb, o) for o in placed):
                        continue
                    placed.append(bb); done = True
                    break
                if done: break
            if done: break
        if not done:
            print('could not place', ref)
    board.Save(path)
    print('placed', len(fps))


if __name__ == '__main__':
    main(sys.argv[1])
