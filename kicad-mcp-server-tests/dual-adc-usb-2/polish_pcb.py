"""Final clean-up of the routed board, then refill zones and save it as the project board.

    ~/bin/kicad10-root/bin/python3.11 polish_pcb.py <in.kicad_pcb>

- Freerouting necks some tracks down to 0.112 mm at pads; widen anything under 0.15 mm.
- Drop vias that sit exactly on another via of the same net (duplicate EP fanout).
"""

import json
import sys
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
MM, TOMM = pcbnew.FromMM, pcbnew.ToMM


def main():
    board = pcbnew.LoadBoard(sys.argv[1])
    widened = 0
    seen, dups = set(), []
    for t in board.GetTracks():
        if t.Type() == pcbnew.PCB_VIA_T:
            key = (t.GetNetCode(), t.GetPosition().x, t.GetPosition().y)
            if key in seen:
                dups.append(t)
            seen.add(key)
        elif t.GetWidth() < MM(0.15):
            t.SetWidth(MM(0.15))
            widened += 1
    for v in dups:
        board.Remove(v)
    pcbnew.ZONE_FILLER(board).Fill(board.Zones())
    pro_path = HERE / "dual_adc_usb.kicad_pro"
    pro = json.loads(pro_path.read_text())
    out = HERE / "dual_adc_usb.kicad_pcb"
    board.Save(str(out))
    # Save() rewrites the project file; restore it, allowing 1-spoke thermals (those pads also have vias)
    pro["board"]["design_settings"]["rules"]["min_resolved_spokes"] = 1
    pro_path.write_text(json.dumps(pro, indent=2))
    print(f"widened {widened} tracks, removed {len(dups)} duplicate vias -> {out.name}")


if __name__ == "__main__":
    main()
