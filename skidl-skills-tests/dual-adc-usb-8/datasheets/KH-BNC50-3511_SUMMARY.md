# KH-BNC50-3511 — Kinghelm right-angle PCB BNC jack, 50 Ω, THT  [J2, J3]

Source: `datasheets/KH-BNC50-3511.pdf` (Kinghelm drawing KH-801-0038 rev B, 1 page). The mechanical data below comes from that drawing. Footprint: **CUSTOM needed**.

| Spec | Value |
|------|-------|
| Impedance / range | 50 Ω, DC–3 GHz, VSWR 1.3 |
| Working voltage | 500 V rms |
| Body | 14.7 ± 0.3 wide × 12.5 high (panel face); centre height 11 mm; overall length 35.5 REF; 1/2-28UNEF thread, Ø9.5 |

## PCB pattern (drawing p.1, "PCB" view, dimensions in mm — **verified from drawing**)
| Feature | Value |
|---|---|
| Mounting/shell pegs | 2 × Ø2.00 mm holes, 10.1 mm apart (symmetric about the connector axis) |
| Signal + ground leads | 2 × Ø0.90 mm holes, 2.5 mm apart |
| Lead row to peg row | 5.05 mm (lead row behind the peg row, away from the board edge) |
| Centre contact | on the connector axis (5.05 mm from each peg); ground lead offset 2.5 mm |
| Front of body to peg row | ≈1.8 mm (1.80 ± 0.10 in side view); body overhangs the board edge per 21.0/28.5 mm dims |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | centre | signal (Ø0.9 hole on axis) |
| 2 | ground lead | shell/GND (Ø0.9 hole, 2.5 mm off axis) |
| MH1, MH2 | pegs | shell/GND (Ø2.0 holes) |

## Notes
- The drawing is dense. The footprint author should re-read the "PCB" view (lower right of p.1) to confirm which Ø0.9 hole lies on the axis before committing.
