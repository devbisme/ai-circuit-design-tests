# SN74LVC1G17DBVR — Single Schmitt-Trigger Buffer (clock isolation, U8)

**UPDATE (verification pass, 2026-09-21) — PDF obtained, pin mapping VERIFIED against TI
primary source.** `datasheets/SN74LVC1G17DBVR.pdf` — Texas Instruments **SCES351Y, July
2001, Revised October 2025 (Rev. Y)**, fetched from
`https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf`.

| Spec | Value |
|------|-------|
| Package | SOT-23-5 (TI calls it DBV, 5-Pin SOT-23) |
| Vcc / Vin range | 1.65–5.5 V |
| Key output spec | Schmitt-trigger input, push-pull output, 4.6 ns typ propagation delay @3.3V |
| Max current / power | ±24 mA output drive @3.3V |
| Operating temp | −40°C to +125°C |

## Pinout (VERIFIED — TI datasheet §4 "Pin Configuration and Functions", p.3, DBV package top view)
| Pin | Name | I/O | Function |
|-----|------|-----|----------|
| 1 | N.C. | — | Not connected |
| 2 | A | I | Input |
| 3 | GND | — | Ground |
| 4 | Y | O | Output (Y = A) |
| 5 | VCC | — | Power terminal |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| SOT-23-5 pin assignment (DBV package) | Pin1=N.C., Pin2=A(in), Pin3=GND, Pin4=Y(out), Pin5=VCC | TI SCES351Y (Rev. Y), §4 Pin Configuration and Functions, p.3 — **verified** |

This exactly matches the generic `74xGxx:74LVC1G17` KiCad symbol used in
`circuits/dual_adc_usb/clocking.py` (pin2 → A/input, pin4 → Y/output, pin5 → VCC, pin3 →
GND, pin1 → NC), and the code (`U8[2]` = clk_buf in, `U8[4]` = clk_out out, `U8[5]` = vdd,
`U8[3]` = gnd) is correct as written. No mismatch, no code change needed.

## Notes
- Isolates X1 (10 MHz sample clock oscillator) from the FPGA clock input path per
  `clocking` block in `sourced_bom.md` (R21/R22/R23 series resistors on either side).
- This is a single-gate device — pin 1 (N.C.) has no internal connection on the DBV
  package; TI's datasheet explicitly notes "N.C. – No internal connection." Leaving it
  unconnected (as the symbol does, `no_connect` pin type) is correct.
