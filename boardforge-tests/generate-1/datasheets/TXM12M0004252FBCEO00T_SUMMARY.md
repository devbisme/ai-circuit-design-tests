# TXM12M0004252FBCEO00T - 12 MHz crystal, 2520 4-pad (Yajingxin) - NO DATASHEET, every fact UNVERIFIED

Source: pcbparts MCP (LCSC C284155) only; LCSC datasheet download failed.

| Spec | Value |
|------|-------|
| Package | SMD2520-4P (2.5 x 2.0 mm) - UNVERIFIED |
| Frequency | 12 MHz - UNVERIFIED (MCP) |
| Load capacitance CL | 12 pF - UNVERIFIED (MCP) |
| Tolerance / stability | +/-10 ppm / +/-30 ppm - UNVERIFIED (MCP) |
| ESR | 120 ohm max - UNVERIFIED (MCP) |
| Operating temp | -40..+85 C - UNVERIFIED (MCP) |

## Pinout (UNVERIFIED - common 2520 4-pad convention, matches KiCad Device:Crystal_GND24)
| Pin | Name | Function |
|-----|------|----------|
| 1 | 1 | Crystal terminal (to FT232H OSCI) |
| 2 | G | Case/GND |
| 3 | 3 | Crystal terminal (to FT232H OSCO) |
| 4 | G | Case/GND |

## Notes
- C901/C902 = 2 x (CL - Cstray 3 pF) = 18 pF.
- FT232H wants 12 MHz +/-30 ppm (datasheet FT_000288 Table 6.1); tolerance+stability here may total 40 ppm - acceptable for USB HS (+/-500 ppm) but outside FTDI's stated figure.
