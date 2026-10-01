# OT322540MJBA4SL — YXC YSO110TR 40 MHz CMOS XO, 3.2x2.5 mm, 1.8–3.3 V

Source: `OT322540MJBA4SL.pdf` (YXC YSO110TR "Wide Voltage" series sheet, 4 pp., image-only;
the document LCSC C2831396 links for this MPN). The sheet does not decode the MPN suffix;
the 3225 / 40 MHz / CMOS identity comes from the LCSC listing.

| Spec | Value |
|------|-------|
| Package | SMD 3.2 x 2.5 x 1.2 mm max, 4 pads (p.3) |
| VDD | 1.8–3.3 V (used at +3V3D) |
| Output | CMOS, 15 pF load; VOH ≥ 90 % VDD, VOL ≤ 10 % VDD; tr/tf ≤ 4 ns; duty 45–55 % |
| Current | ≤ 5 mA @ 3.3 V (1–40 MHz, 3225, 15 pF) |
| Phase jitter (12 kHz–20 MHz) | **0.7 ps max** |
| Start-up | ≤ 3 ms |
| Stability | ±10/±20 ppm tol @25 °C; ±20/30/50 ppm over temp; aging ±3 ppm/yr |
| Operating temp | −40 to +85 °C |
| Tri-state | Enable: high or floating (≥ 70 % VDD); disable: low (≤ 30 % VDD) |

## Pinout (p.2, Pin Assignments)
| Pin | Datasheet name | KiCad `Oscillator:ASE-xxxMHz` name | Function |
|-----|------|------|----------|
| 1 | Tri-state | `EN` | Output enable, tie to +3V3D |
| 2 | GND | `GND` | Ground |
| 3 | OUTPUT | `OUT` | CMOS clock out |
| 4 | VDD | `Vdd` | Supply |

SKiDL: `Part('Oscillator','ASE-xxxMHz', footprint='Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm')`;
pin names are case-sensitive — `Vdd`, not `VDD`. Numbers are safer: 1 EN, 2 GND, 3 OUT, 4 Vdd.

## Notes
- Decoupling: datasheet p.3 note 1 requires 0.01–0.1 µF VDD–GND; the test circuit (p.4) adds 10 µF.
- Land pattern (p.3): YXC recommends 1.3 x 1.2 mm pads, 0.8 mm X gap, 0.7 mm Y gap (centres ±1.05, ±0.95).
  KiCad Abracon ASE footprint has 1.3 x 1.1 mm pads at ±1.05, ±0.825. The X positions are the same,
  but the KiCad pads sit 0.125 mm further in on Y and are 0.1 mm shorter. Both still cover the 1.0 mm package
  pad. Pin order is the same (1 BL, 2 BR, 3 TR, 4 TL, top view), so the footprint is acceptable.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| RMS phase jitter (K8) | 0.7 ps max, 12 kHz–20 MHz | p.1 spec table — **verified** (series sheet; this row has no variant column) |
| Pinout | 1 Tri-state, 2 GND, 3 OUTPUT, 4 VDD | p.2 — **verified** |
| OE polarity | high/floating = enabled, low = disabled | p.1 — **verified** |
| Supply current | ≤ 5 mA @ 3.3 V, 40 MHz, 3225 | p.1 current table (1.000–40.000 MHz column) — **verified** |
| VDD range | 1.8–3.3 V | p.1 — **verified** |
