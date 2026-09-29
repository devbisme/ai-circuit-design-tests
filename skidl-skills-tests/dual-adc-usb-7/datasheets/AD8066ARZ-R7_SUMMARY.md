# AD8066ARZ-R7 — Dual JFET-input FastFET op-amp (afe_buffer, U1)

| Spec | Value |
|------|-------|
| Package | SOIC-8 (150mil) |
| Vcc / Vin range | Single supply 5–24V; dual supply ±2.5V to ±12V (used here as ±5V, VA_POS/VA_NEG) |
| Key output spec | GBW 120MHz (145MHz per full ADI datasheet), slew rate 180V/µs, Ib=6pA, Ios=10pA |
| Max current / power | Iout 35mA, Iq 6.6mA/amp |
| Operating temp | −40°C to +85°C |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | VOUT1 | Channel 1 output |
| 2 | -IN1 | Channel 1 inverting input |
| 3 | +IN1 | Channel 1 non-inverting input |
| 4 | -VS | Negative supply (VA_NEG) |
| 5 | +IN2 | Channel 2 non-inverting input |
| 6 | -IN2 | Channel 2 inverting input |
| 7 | VOUT2 | Channel 2 output |
| 8 | +VS | Positive supply (VA_POS) |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Input bias current Ib | 6 pA typ | jlc_get_part electrical specs (C9647) — **verified** |
| Input offset current Ios | 10 pA | jlc_get_part electrical specs — **verified** |
| Gain-bandwidth product | 120–145 MHz | jlc_get_part + ADI product page cross-check — **verified** |
| Pinout (all 8 pins) | See table above | **CORRECTED from a bad source**: JLC's EasyEDA pinout for this exact LCSC# (C9647) returned only 5 of 8 pins (missing pins 5,6,7 — the entire second channel). The table above is read directly from the ADI pin-configuration diagram in `AD8066ARZ-R7.pdf` (line ~26–38, "8-Lead SOIC_N" diagram) — **verified from primary datasheet**, and is what the generated KiCad symbol (`dual_adc_usb:AD8066ARZ-R7`) uses. **Do not regenerate this symbol from the JLC/EasyEDA pinout — it is wrong.** |

## Notes
- `[CRIT]` single-source dual-JFET buffer per sourcing decision 1 — do not substitute.
- R-10 (design_risks.md): at ±10V input overload the divider node can reach ±5.0V, inside AD8066's ±5V rails/abs-max but outside its linear input CM range (V+ − 2.5V). This is an accepted intentional saturation behavior (survival, not accuracy, per requirement I3).
- Generated symbol: `dual_adc_usb:AD8066ARZ-R7` in `symbols/dual_adc_usb.kicad_sym` (8 pins, `find-symbol.py` reports `EXACT`).
- Datasheet: `datasheets/AD8066ARZ-R7.pdf` (Analog Devices AD8065/AD8066 combined datasheet).
