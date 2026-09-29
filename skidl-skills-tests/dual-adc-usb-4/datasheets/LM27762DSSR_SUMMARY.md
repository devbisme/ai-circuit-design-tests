# LM27762DSSR — Low-Noise ±Output Integrated Charge Pump + LDO (U7, bipolar ±2.5V supply)

| Spec | Value |
|------|-------|
| Package | WSON-12 (2x3mm) with EP |
| Vcc / Vin range | 2.7V – 5.5V |
| Key output spec | VOUT+ adjustable 1.5-5V, VOUT- adjustable -1.5 to -5V, 2.5Ω output resistance |
| Max current / power | 250mA per output |
| Operating temp | -40°C to +85°C |

## Pinout (VERIFIED against TI SNVSAF7C Table 4-1, matches JLC/EasyEDA data exactly)
| Pin | Name | Function |
|-----|------|----------|
| 1 | PGOOD | Power-good output (optional, 10kΩ pull-up to GND-referenced logic if unused: tie to GND) |
| 2 | FB+ | Positive LDO feedback input |
| 3 | VIN | Input supply |
| 4 | GND | Ground |
| 5 | CP | Charge-pump negative unregulated output |
| 6 | OUT- | Negative LDO output |
| 7 | FB- | Negative LDO feedback input |
| 8 | EN- | Enable, charge pump + negative LDO, active high |
| 9 | C1- | Flying cap negative terminal |
| 10 | C1+ | Flying cap positive terminal |
| 11 | OUT+ | Positive LDO output |
| 12 | EN+ | Enable, positive LDO, active high |
| 13 | EP | Exposed pad (thermal/ground) |

## Notes
- Datasheet: SNVSAF7C (TI, Aug 2016, rev Oct 2025), downloaded to `datasheets/LM27762DSSR.pdf`.
- **FB divider formulas (resolves sourcing's `## Next phase must` #3, R6-R9), from §7.2.2.1 and
  §7.2.2.3:**
  - Positive output: `VOUT+ = 1.2V × (R1+R2)/R2`, where R1 connects OUT+→FB+ and R2 connects
    FB+→GND. **Constraint: R2 ≥ 50kΩ.**
  - Negative output: `VOUT- = -1.22V × (R3+R4)/R4`, where R3 connects OUT-→FB- and R4 connects
    FB-→GND. **Constraint: R4 ≥ 50kΩ.**
  - `net_plan.md` line 45 assigns **R6/R7 to the +2.50V divider and R8/R9 to the -2.50V
    divider**. Mapping R6=R1 (top, OUT+ side), R7=R2 (bottom, GND side), R8=R3 (top, OUT- side),
    R9=R4 (bottom, GND side) — following the convention that the lower ref number sits closer
    to the regulated output:
    - **R6 = 107kΩ, R7 = 100kΩ (1%, E96)** → VOUT+ = 1.2×(107+100)/100 = **2.484V** (-0.64%
      from the 2.50V target).
    - **R8 = 105kΩ, R9 = 100kΩ (1%, E96)** → VOUT- = -1.22×(105+100)/100 = **-2.501V** (+0.04%
      from the -2.50V target — near-exact).
    Both satisfy the ≥50kΩ constraint on the ground-side resistor. These are **target values
    for the coder/sourcer to place as 0402 1% Basic-tier resistors** (per sourcing's plan for
    R6-R9); this librarian did not re-run LCSC stock lookups for the exact resistor MPNs —
    that step still belongs to sourcing/coding.
  - If R6/R7/R8/R9 in `net_plan.md` are ever reassigned to the opposite (top/bottom) role by a
    later phase, swap the values accordingly — the formula pairing (top-resistor + bottom-
    resistor, bottom ≥50kΩ) is what matters, not which specific ref gets which value.
- C16 (1µF flying cap C1+/C1-), C17 (2.2µF charge-pump output on CP), and the remaining
  capacitors are already specified in `sourced_bom.md` per the architecture's C14-C21 list —
  no change needed.
