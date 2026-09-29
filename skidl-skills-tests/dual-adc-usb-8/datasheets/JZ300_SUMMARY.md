# JZ300 — Knowles/Voltronics JZ-series SMD ceramic trimmer capacitor, 5.5–30 pF  [C104, C204]

Source: Knowles/Voltronics outline drawing V-7531 rev G, "Outline drawing for JZxxx series"
(LCSC C3273397 PDF, 2 pages). It is a **series** drawing, so `fetch-datasheet.py` rejected it
as "mostly JZ500" and no PDF was kept in `datasheets/`. It was read by hand from the scratchpad;
the JZ300 row is explicit in the configuration table.

Symbol: `Device:C_Variable`. Footprint: `Capacitor_SMD:C_Trimmer_Voltronics_JZ` (pads 1 at x = −1.95, 2 at x = +1.95).

| Spec | Value |
|------|-------|
| Package | SMD, body 4.5 × 3.2 mm, height 1.45 mm |
| C range | 5.5 pF min, 30 pF max (+100 %/−0 %) |
| **Temp coefficient** | **−1500 ± 1000 ppm/°C** (N1500 class, not C0G) |
| Q min @ 1 MHz | 200 |
| DC working / withstand | 125 V / 220 V |
| Insulation resistance | 10⁴ MΩ |
| Operating temp | −40…+85 °C |
| Marking | orange |

## Pinout
| Pad | Name | Function |
|-----|------|----------|
| hot end (the flat side of the body, opposite the ID-mark corners) | HOT | stator |
| rotor end | COLD (ROTOR) | touches the adjusting screwdriver |

The part is electrically non-polar, and the KiCad footprint has no polarity mark.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Range covers 23.8 pF | 5.5–30 pF | drawing V-7531 config table — **verified** |
| TC | −1500 ± 1000 ppm/°C, which is −0.5…−2.5 %/10 °C. At 23.8 pF over a 25 °C swing that is −0.3…−1.5 pF | drawing — **verified** |
| Suggested land | 2 pads 0.9 × 1.4 mm; outer span 4.8, inner gap 3.0, which gives a **3.9 mm pitch** (matches the KiCad footprint) | drawing — **verified** |

## Notes
- **Orientation for the coder:** put the **rotor (cold) terminal on GND** and the **hot terminal on A_DIV/B_DIV**. Then the tuning tool does not load the signal node. Convention: `C_Variable` pin 1 → A_DIV (hot), pin 2 → GND (rotor). Layout and assembly must place the rotor end on pad 2; add a silkscreen note, because the footprint carries no mark.
- Handling: no flow soldering, no flux or solder on the housing, no locking paint, ceramic screwdriver, axial load ≤ 1.5 N.
- Knowles may substitute an "HV" variant (yellow-green dot) under note 6.1. It is electrically equivalent or better.
