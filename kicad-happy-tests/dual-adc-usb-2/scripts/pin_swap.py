"""
FPGA pin-swap optimizer: reassign FPGA I/O within each group so the order of FPGA pins around
the package matches the order of the partner pads (ADC / SDRAM / FT2232H) seen from the FPGA
centre. That removes most bus crossings before routing.

  python3.11 scripts/pin_swap.py board.kicad_pcb fpga_pinmap.json

Writes {net_name: fpga_pin_number}; dual_adc_usb.py reads it if present.
"""
import json
import math
import sys

import pcbnew

FPGA_REF_VALUE = "ICE40HX4K-TQ144"
# Groups: (pins available, partner footprint value prefix). Clock pins (21, 49) and config pins
# are fixed and not listed.
GROUPS = {
    "adc": ([1, 2, 3, 4, 7, 8, 9, 10, 11, 12, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 28, 29, 31, 32,
             33, 34], "LTC2291"),
    "sdram": ([73, 74, 75, 76, 78, 79, 80, 81, 82, 83, 84, 85, 87, 88, 90, 91, 93, 94, 95, 96, 97, 98, 99,
               101, 102, 104, 105, 106, 107, 110, 112, 113, 114, 115, 116, 117, 118, 119], "IS42S16400"),
    "ft": ([37, 38, 39, 41, 42, 43, 44, 45, 47, 48, 52, 55, 56, 60, 61, 62, 63, 64], "FT2232HL"),
}


def main(pcb, out):
    b = pcbnew.LoadBoard(pcb)
    fps = list(b.GetFootprints())
    fpga = [f for f in fps if f.GetValue() == FPGA_REF_VALUE][0]
    cx, cy = pcbnew.ToMM(fpga.GetPosition().x), pcbnew.ToMM(fpga.GetPosition().y)
    fpad = {p.GetNumber(): p for p in fpga.Pads()}

    def ang(x, y):
        return math.atan2(y - cy, x - cx)

    result = {}
    for gname, (pins, partner) in GROUPS.items():
        part = [f for f in fps if f.GetValue().startswith(partner)][0]
        # signals: nets on the listed FPGA pins that also touch the partner (others keep their pin
        # unless they are part of the group, e.g. ADC_SHDN goes with the ADC group)
        sigs = []
        for n in pins:
            net = fpad[str(n)].GetNetname()
            if not net or net.startswith("unconnected"):
                continue
            pp = [p for p in part.Pads() if p.GetNetname() == net]
            if pp:
                x, y = pcbnew.ToMM(pp[0].GetPosition().x), pcbnew.ToMM(pp[0].GetPosition().y)
            else:
                # net not on partner (e.g. control lines to other parts): use its farthest pad
                pads = [p for f in fps for p in f.Pads() if p.GetNetname() == net and f is not fpga]
                if not pads:
                    continue
                x = sum(pcbnew.ToMM(p.GetPosition().x) for p in pads) / len(pads)
                y = sum(pcbnew.ToMM(p.GetPosition().y) for p in pads) / len(pads)
            sigs.append((ang(x, y), net))
        pin_ang = [(ang(pcbnew.ToMM(fpad[str(n)].GetPosition().x), pcbnew.ToMM(fpad[str(n)].GetPosition().y)), n)
                   for n in pins]

        def unwrap(lst):
            # start the angular sweep in the largest gap so the order has no wrap-around
            lst = sorted(lst)
            gaps = [(lst[(i + 1) % len(lst)][0] - lst[i][0]) % (2 * math.pi) for i in range(len(lst))]
            k = max(range(len(lst)), key=lambda i: gaps[i])
            return lst[k + 1:] + lst[:k + 1]

        s_sorted = unwrap(sigs)
        p_sorted = unwrap(pin_ang)
        # The FPGA pins face the partner, so ordering seen from the centre runs the same way for
        # both lists; spread signals evenly over the available pins.
        npins, nsig = len(p_sorted), len(s_sorted)
        for i, (_a, net) in enumerate(s_sorted):
            j = round(i * (npins - 1) / max(1, nsig - 1)) if nsig > 1 else 0
            result[net] = p_sorted[j][1]
        print(gname, nsig, "signals over", npins, "pins")
    json.dump(result, open(out, "w"), indent=1, sort_keys=True)
    print("wrote", out, len(result))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
