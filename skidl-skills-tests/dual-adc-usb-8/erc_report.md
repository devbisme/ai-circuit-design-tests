# ERC review — dual_adc_usb (revision 2, re-gate after F1 fix)

**0 errors, 6 warnings, 1 note. Circuit is PASS.**

This is a re-gate. The only change since revision 1 is `footprints/ProjectLocal.pretty/BNC_Kinghelm_KH-BNC50-3511_Horizontal.kicad_mod`, used by J2 and J3 (afe_ch_a rev 2). No `.py` file changed. F1 is now closed. The ERC result, both validators and the netlist are the same as in revision 1, apart from the netlist `(date …)` line.

Run (2026-09-26, from the project root):
`KICAD_SYMBOL_DIR=/usr/share/kicad/symbols KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python3 -m circuits.dual_adc_usb`

The full log of this run and both validator outputs are in `outputs/erc_run_rev2.txt`. `outputs/erc_run.txt` is the revision 1 log and is kept unchanged because the hook protects it. Its ERC content is identical.

## Findings (severity order)

### F1 — CLOSED (was HIGH) — J2/J3 BNC footprint mirrored
I re-checked the footprint against drawing KH-801-0038 rev B (the rendered page), and loaded it in pcbnew to read the pad positions back:

| Feature | Drawing | Footprint (pcbnew readback) | OK |
|---|---|---|---|
| Shell pegs | 2 × Ø2.00, 10.1 apart, symmetric | pad 2 at (±5.05, −2.525), drill 2.0 | yes |
| Centre contact | on axis, 5.05 from each peg | pad 1 at (0, +2.525), drill 0.9 | yes |
| Ground lead | 2.5 mm from centre, on the **left** in top view (front up) | pad 2 at (**−2.5**, +2.525), drill 0.9 | **yes (was +2.5)** |
| Lead row to peg row | 5.05 mm, leads behind pegs | 2.525 − (−2.525) = 5.05 | yes |
| Peg to flange | 28.5 − 21.0 = 7.5 | flange/panel line at y = −10.025 | yes |
| Peg to thread tip | 28.5 | nose ends at y = −31.025 | yes |
| Body rear | 35.5 − 28.5 = 7.0 behind pegs | rear at y = +4.475 | yes |
| Body width | 14.7 | ±7.35 | yes |

The side of the ground lead is consistent across all three views. In the PCB view, the right-hand Ø0.9 hole is the one 5.05 mm from the right peg, which puts it on the axis, so the ground-lead hole is to its left. The front view has the ground lead to the viewer's right, and the rear view has it to the viewer's left. Both of those map to −x in a top view with the front at −y.

- **Courtyard:** now covers the body and the nose out to y = −31.275. DRC will see the overhang.
- **Front-edge marker:** present on F.Fab ("FRONT / PANEL EDGE") and as a dashed Dwgs.User line at y = −10.025. This closes the MEDIUM sub-item.
- **Silk and pads:** the silk outline clears every pad.
- **Pin mapping:** pad names 1 and 2 still match the `Connector:Conn_Coaxial` pins. The netlist has J2.1 → A_BNC, J3.1 → B_BNC, and J2.2/J3.2 → GND.

### W1–W6 — WARNING (accepted false positive, unchanged) — FT_EECS / FT_EECLK "No drivers" / "Insufficient drive"
The KiCad `Interface_USB:FT232H` symbol types EECS (pin 45) and EECLK (pin 44) as `input`. On the silicon, the FT232H is the Microwire master that drives the 93LC56B CS and CLK pins. The optional silencing snippet for `usb_bridge.py` is unchanged from revision 1:
```python
u10['EECS'].func = Pin.types.OUTPUT
u10['EECLK'].func = Pin.types.OUTPUT
```

### N1 — NOTE (accepted, unchanged) — "Missing tag on <root>"
This note comes from the SKiDL root hierarchy node. Two runs gave netlists that differ in nothing, including the date line (both runs fell in the same minute).

## Regression check
- **ERC:** same 6 warnings and 1 note as revision 1, and 0 errors.
- **Netlist:** the revision 1 gate netlist and this run's netlist differ only in the `(date …)` line.
- **Reproducibility:** two back-to-back runs gave byte-identical netlists, with no `_N` refdes.
- **validate-footprints.py:** exit 0. All 72 footprint strings resolve across the 10 files.
- **validate-bom.py:** exit 0. BOM and circuit agree: 170 parts, 131 rows. The same 15 package notes appear, and all were reviewed in revision 1. The J2/J3 note ("THT right-angle BNC") is now confirmed by the geometry table above.

## Summary
| Check | Result |
|---|---|
| ERC errors | 0 |
| ERC warnings | 6 (FT_EECS/FT_EECLK symbol typing, accepted) |
| Notes | 1 (root-node tag, accepted) |
| validate-footprints.py | 72/72 resolve |
| validate-bom.py | exit 0, 170 parts / 131 rows, 15 notes all reviewed |
| Footprint geometry (manual) | F1 closed. The J2/J3 BNC matches KH-801-0038 rev B |
| Reproducibility | identical |
| Checklist (supply span, levels, banks, MFB, EP) | unchanged from revision 1, all OK (no `.py` change) |
| **Verdict** | **PASS** |
