# FT232HL-REEL — FTDI Hi-Speed USB to UART/FIFO bridge, LQFP-48

Source: `FT232HL-REEL.pdf` (DS_FT232H FT_000288 v1.0 via Reichelt mirror; pinout unchanged in later revs).

| Spec | Value |
|------|-------|
| VREGIN | 3.6–5.5 V (5 V mode) **or 3.3–3.6 V (3.3 V mode)** |
| VCCIO / VPLL / VPHY | 2.97–3.63 V / 3.0–3.6 V / 3.3 V |
| Current | Ireg 52 mA (VREGIN 3.3 V) + Iccphy 30 typ / 60 max mA (HS) |
| Crystal | 12 MHz fundamental, parallel; example 27 pF load caps; pick per crystal CL |
| Temp | −40…+85 °C |

## Pinout — SKiDL names are the **KiCad `Interface_USB:FT232H`** names (datasheet name in brackets where different)
| Pin | Name | Function |
|-----|------|----------|
| 1 / 2 | XCSI [OSCI] / XCSO [OSCO] | 12 MHz crystal |
| 3 | VPHY | 3.3 V PHY supply (LC filter recommended, Fig 6.1) |
| 4,9,41 | AGND | |
| 5 | REF | 12 kΩ 1 % to GND |
| 6 / 7 | DM / DP | USB |
| 8 | VPLL | 3.3 V PLL supply (LC filter recommended) |
| 10,11,22,23,35,36,47,48 | GND | |
| 12,24,46 | VCCIO | 3.3 V I/O supply |
| 13–20 | ADBUS0–ADBUS7 | FIFO D0–D7 |
| 21 | ACBUS0 | RXF# |
| 25 | ACBUS1 | TXE# |
| 26 | ACBUS2 | RD# |
| 27 | ACBUS3 | WR# |
| 28 | ACBUS4 | SIWU# (tie to VCCIO if unused) |
| 29 | ACBUS5 | CLKOUT 60 MHz |
| 30 | ACBUS6 | OE# |
| 31–33 | ACBUS7–9 | unused in 245 mode |
| 34 | ~{RESET} | active-low reset |
| 37 | VCCA | 1.8 V output, do not load |
| 38 | VCCCORE [VCORE] | 1.8 V output, do not load |
| 39 | VCCD | input when VREGIN = 3.3 V |
| 40 | VREGIN | regulator input |
| 42 | TEST | to GND |
| 43 / 44 / 45 | EEDATA / EECLK / EECS | 93LC56B interface |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| VREGIN at 3.3 V (K6) | allowed; VCCD becomes an input and is tied to 3.3 V with VCCIO, VPLL, VPHY | Table 3.1 note + §6 Fig 6.3 — **verified** |
| 245 sync FIFO pin map (K6) | ACBUS0 RXF#, 1 TXE#, 2 RD#, 3 WR#, 4 SIWU#, 5 CLKOUT, 6 OE#; ADBUS = D0–D7 | Table 3.7 p.14 — **verified** |
| EEPROM wiring | EEDATA direct to EEPROM DI; to EEPROM DO via 2.2 kΩ; DO pulled up 10 kΩ to VCCD | Table 3.3 p.9 — **verified** (R103 2.2k, R102 10k correct) |
| EEPROM type | 16-bit organised, 93LC56B class | §4 p.~25 — **verified** |
| Supply current (K6) | ≈82 mA typ, up to ≈112 mA max (52 + 30/60) from 3.3 V, plus I/O | Tables 5.3/5.4 — **verified** (architecture assumed ~70 mA) |
| 245 mode enable | EEPROM set to 245 FIFO, then Set Bit Mode from host | §3.5.2 — **verified** |
