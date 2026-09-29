# THS4521IDR — Fully differential ADC driver amplifier (afe_driver, U2/U3)

| Spec | Value |
|------|-------|
| Package | SOIC-8 (150mil) |
| Vcc / Vin range | Single supply 2.5–5.5V (used at 3.3V, P3V3A) |
| Key output spec | GBW 95MHz, slew rate 490V/µs, VOCM pin sets output common-mode |
| Max current / power | Iout 55mA, Iq 1.14mA |
| Operating temp | −40°C to +85°C |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | VIN- | Inverting input |
| 2 | VOCM | Output common-mode set/sense (drive externally, e.g. ADC_CM per net_plan) |
| 3 | VS+ | Positive supply |
| 4 | VOUT+ | Non-inverting output |
| 5 | VOUT- | Inverting output |
| 6 | VS- | Negative supply/ground |
| 7 | PD | Power-down (active low per TI convention — confirm polarity before layout, not read from full elec table in this pass) |
| 8 | VIN+ | Non-inverting input |

## Notes
- `[CRIT]` fully-differential ADC driver, symbol already exists as a prefix match (`Amplifier_Difference:THS4521ID` — drops the `R` reel suffix, pinout unaffected). **Not** regenerated — sourcing's "do not redo" applies.
- Rf=1.10kΩ (R112/114/212/214), Rg=1.00kΩ (R111/113/211/213) set differential gain 1.100, per sourced_bom.
- Datasheet: `datasheets/THS4521IDR.pdf` (TI SBOS-series, obtained via `ti.com/lit/ds/symlink/ths4521.pdf`).
