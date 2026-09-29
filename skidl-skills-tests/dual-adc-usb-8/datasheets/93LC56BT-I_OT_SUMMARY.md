# 93LC56BT-I/OT — Microchip 2 Kbit Microwire EEPROM, x16 (B version), SOT-23-6  [U11, FT232H config]

Source: `datasheets/93LC56BT-I_OT.pdf` = Microchip 93AA56X/93LC56X/93C56X datasheet (DS20001794). Symbol: **generated `dual_adc_usb:93LC56BT-I_OT`**. **Do NOT use KiCad `Memory_EEPROM:93LCxxB`.** That is the 8-pin SOIC/DIP pinout (1 CS, 2 CLK, 3 DI, 4 DO, 5 GND, 8 VCC); on the SOT-23-6 footprint it would wire every pin wrong. Footprint: `Package_TO_SOT_SMD:SOT-23-6`.

| Spec | Value |
|------|-------|
| VCC | 2.5–5.5 V |
| Organisation | **128 × 16-bit, fixed (B version, no ORG pin)** |
| Clock | 2–3 MHz max (VCC dependent) |
| Temp | I: –40…+85 °C |

## Pinout (p.2 "Package Types", SOT-23)
| Pin | Name | Function |
|-----|------|----------|
| 1 | DO | serial data out |
| 2 | VSS | ground |
| 3 | DI | serial data in |
| 4 | CLK | serial clock |
| 5 | CS | chip select (active high) |
| 6 | VCC | supply |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| SOT-23-6 pin map | as above | p.2 — **verified** |
| Word size | x16 fixed | p.1 selection table — **verified** |
| FT232H compatibility (x16 93xx56) | compatible | **UNVERIFIED** — FT232H datasheet not obtained |
