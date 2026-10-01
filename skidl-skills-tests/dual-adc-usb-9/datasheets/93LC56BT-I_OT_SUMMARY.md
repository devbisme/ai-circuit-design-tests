# 93LC56BT-I/OT — Microchip 2 Kbit Microwire EEPROM, x16 (B), SOT-23-6

Source: `93LC56BT-I_OT.pdf` (DS20001794J).

| Spec | Value |
|------|-------|
| VCC | 2.5–5.5 V |
| Organisation | 128 x 16 (B version, no ORG pin) |
| Clock | 2 MHz (≥2.5 V) |

## Pinout — SOT-23-6 differs from DIP/SOIC
| Pin | Name |
|-----|------|
| 1 | DO |
| 2 | VSS |
| 3 | DI |
| 4 | CLK |
| 5 | CS |
| 6 | VCC |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| SOT-23 pinout | as above | Table 3-1 — **verified** (matches EasyEDA) |
| Correct KiCad symbol | **`Memory_EEPROM:93LCxxBxxOT`** (1 DO, 2 GND, 3 DI, 4 CLK, 5 CS, 6 VCC). The BOM's `93LCxxB` is the 8-pin DIP/SOIC numbering — do not use | KiCad lib — **verified** |

## Rev 2 re-check: KiCad symbol vs datasheet
Checked against DS20001794J p.2 (Package Types, SOT-23) and Table 3-1 (SOT-23 column).
`Memory_EEPROM:93LCxxBxxOT` (extends `93LCxxAxxOT`, footprint `Package_TO_SOT_SMD:SOT-23-6`):

| Pin | Datasheet | KiCad name (SKiDL) | KiCad type |
|-----|-----------|--------------------|------------|
| 1 | DO | `DO` | tri_state |
| 2 | VSS | `GND` | power_in |
| 3 | DI | `DI` | input |
| 4 | CLK | `CLK` | input |
| 5 | CS | `CS` | input |
| 6 | VCC | `VCC` | power_in |

All 6 numbers match. The only name difference is VSS on the datasheet vs `GND` in KiCad, so use `GND` in SKiDL.
SOT-23 has no ORG pin, so x16 organisation is fixed by the B suffix, which the FT232H needs.
CS is active-high. Decouple VCC with 0.1 µF. **Verified.**
