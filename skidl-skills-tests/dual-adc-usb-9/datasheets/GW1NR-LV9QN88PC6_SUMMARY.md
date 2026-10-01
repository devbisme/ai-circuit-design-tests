# GW1NR-LV9QN88PC6/I5 — Gowin LittleBee FPGA, 8640 LUT, 64 Mbit PSRAM in package, QFN-88 (QN88P)

Sources: DS117-3.2.5E (`GW1NR-LV9QN88PC6.pdf`), UG803-1.6E pinout (`GW1NR-9_UG803_pinout.pdf/.xlsx`),
UG119-1.6E package (`GW1NR_UG119_package.pdf`), UG284-1.8E schematic manual (`GW1NR_UG284_schematic.pdf`),
UG290-2.3E configuration (`Gowin_UG290_config.pdf`). All Gowin documents for GW1NR-9 / QN88P.

| Spec | Value |
|------|-------|
| Package | QN88P, 10x10 mm, 0.4 mm pitch, EP 6.74x6.74 mm (D2/E2 6.64–6.84), L 0.30–0.50 (UG119 p.31) |
| VCC (core, LV) | 1.14–1.26 V |
| VCCX/VCCO0 (pins 64,67,78, internally joined) | 2.375–3.6 V |
| VCCO1 (58), VCCO2 (23,44) | 1.14–3.6 V |
| **VCCO3 (12)** | **1.71–1.89 V — bank 3 is wired to the in-package PSRAM** (UG803 Power sheet, QN88P table; DS117 §2.2.2) |
| Static current (typ, C6, 25 °C) | ICC 3.5 mA @1.2 V, ICCX 5 mA, ICCIO 2 mA (DS117 Table 3-9) |
| Ramp rates | VCC 0.6–6 mV/µs, VCCX 0.6–10 mV/µs, VCCIO 0.1–10 mV/µs, monotonic (Table 3-3) |
| Ripple allowed | VCC 3 %, VCCIO 5 %, VCCX 5 % (Table 3-2 note) |
| PSRAM | 2 x 32 Mbit, x8 each, DDR, 166 MHz max clock, 1.8 V (DS117 §2.2.2) |
| Temp | C6/I5: TJ −40…+100 °C (industrial) |

## Pinout (QN88P, from UG803 xlsx "Pin List", column QN88P) — SKiDL names = symbol `dual_adc_usb:GW1NR-LV9QN88PC6`
Power: VCC 1,22,45,66 · VSS 2,21,24,43,46,65 · VCCO3 12 · VCCO2 23,44 · VCCO1 58 · VCCX/VCCO0 64,67,78 · EP 89 (symbol-only number for exposed pad).

| Pin | Name | Bank | Pin | Name | Bank |
|---|---|---|---|---|---|
| 3 | IOT2A | 3 | 47 | IOB43B | 2 |
| 4 | IOL5A/JTAGSEL_N/LPLL_T_in | 3 | 48 | IOR24B | 1 |
| 5 | IOL11A/TMS | 3 | 49 | IOR24A | 1 |
| 6 | IOL11B/TCK | 3 | 50 | IOR22B | 1 |
| 7 | IOL12B/TDI | 3 | 51 | IOR17B/GCLKC_3 | 1 |
| 8 | IOL13A/TDO | 3 | 52 | IOR17A/GCLKT_3 | 1 |
| 9 | IOL13B/RECONFIG_N | 3 | 53 | IOR15B/DOUT/WE_N | 1 |
| 10 | IOL15A/GCLKT_6 | 3 | 54 | IOR15A/DIN/CLKHOLD_N | 1 |
| 11 | IOL16B | 3 | 55 | IOR14B/SSPI_CS_N/D0 | 1 |
| 13 | IOL21B | 3 | 56 | IOR14A/SO/D1 | 1 |
| 14 | IOL22B | 3 | 57 | IOR13A/FASTRD_N/D3 | 1 |
| 15 | IOL25B | 3 | 59 | IOR12B/MCLK/D4 | 1 |
| 16 | IOL26B | 3 | 60 | IOR12A/MCS_N/D5 | 1 |
| 17 | IOB2A | 2 | 61 | IOR11B/MO/D6 | 1 |
| 18 | IOB2B | 2 | 62 | IOR11A/MI/D7 | 1 |
| 19 | IOB4A | 2 | 63 | IOR5A/RPLL_T_in | 1 |
| 20 | IOB4B | 2 | 68 | IOT42B | 1 |
| 25 | IOB8A | 2 | 69 | IOT42A | 1 |
| 26 | IOB8B | 2 | 70 | IOT41B | 1 |
| 27 | IOB11A | 2 | 71 | IOT41A | 1 |
| 28 | IOB11B | 2 | 72 | IOT39B | 1 |
| 29 | IOB13A | 2 | 73 | IOT39A | 1 |
| 30 | IOB13B | 2 | 74 | IOT38B | 1 |
| 31 | IOB15A | 2 | 75 | IOT38A | 1 |
| 32 | IOB15B | 2 | 76 | IOT37B | 1 |
| 33 | IOB23A | 2 | 77 | IOT37A | 1 |
| 34 | IOB23B | 2 | 79 | IOT12B | 3 |
| 35 | IOB29A/GCLKT_4 | 2 | 80 | IOT12A | 3 |
| 36 | IOB29B/GCLKC_4 | 2 | 81 | IOT11B | 3 |
| 37 | IOB31A | 2 | 82 | IOT11A | 3 |
| 38 | IOB31B | 2 | 83 | IOT10B | 3 |
| 39 | IOB33A | 2 | 84 | IOT10A | 3 |
| 40 | IOB33B | 2 | 85 | IOT8B | 3 |
| 41 | IOB41A | 2 | 86 | IOT8A | 3 |
| 42 | IOB41B | 2 | 87 | IOT6B/MODE1 | 3 |
|  |  |  | 88 | IOT5A/MODE0 | 3 |

**I/O budget per bank (pdf-table equivalent, from UG803 xlsx):** bank 1 = 25 I/O (VCCO1, up to 3.3 V); bank 2 = 23 I/O (VCCO2, up to 3.3 V); bank 3 = 23 I/O (VCCO3, **1.8 V only**); bank 0 = 0 I/O bonded. **3.3 V-capable I/O = 48**, not 71.
No READY or DONE pin is bonded on QN88P (not in the UG803 QN88P column).

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| VCCO3 voltage | 1.71–1.89 V (PSRAM bank) | UG803 Power sheet + DS117 §2.2.2 — **verified** |
| 3.3 V user I/O | 48 (bank1 25 + bank2 23) | UG803 Pin List — **verified** |
| Config pins on 1.8 V bank 3 | JTAGSEL_N 4, TMS 5, TCK 6, TDI 7, TDO 8, RECONFIG_N 9, MODE1 87, MODE0 88 | UG803 — **verified** |
| READY / DONE pins | not bonded on QN88P | UG803 QN88P column — **verified** |
| Autoboot strap (K4) | MODE[2:0]=000 = AUTO BOOT from embedded flash; unbonded MODE2 grounded internally; 1 kΩ pull-down recommended (4.7 kΩ for pull-up) | UG290-2.3E p.5 table + p.17 — **verified** |
| JTAGSEL_N, RECONFIG_N | input, internal weak pull-up; RECONFIG_N low blocks config | UG284 / UG290 — **verified** |
| Power-on time | 0.2–2 ms; if >2 ms, sequence VCC before VCCX/VCCIO | UG284-1.8E p.2 — **verified** |
| Decoupling | 0.1 µF per supply pin; VCC via ferrite bead (MH2029-221Y) + 4.7 µF | UG284 Fig.1 — **verified** |
| EP size | 6.74 mm nom — matches BOM footprint EP6.74 | UG119 p.31 — **verified** |
| EP net | GND (VSS) | **UNVERIFIED** — UG119 names it only "exposed pad"; industry practice |
| VCC current (K5) | static 3.5 mA typ; dynamic not specified | DS117 Table 3-9 — **UNVERIFIED for ≤150 mA** (needs Gowin Power Analyzer) |
| PSRAM device rate (K3) | 2×x8 DDR @ ≤166 MHz = 664 MB/s raw | DS117 §2.2.2 — **verified**; IP sustained rate (IPUG943) **UNVERIFIED** |
| Global clock pins at 3.3 V | IOR17A/GCLKT_3 (52, bank1), IOB29A/GCLKT_4 (35, bank2); IOR5A/RPLL_T_in (63) feeds right PLL | UG803 — **verified** |

## Notes
- Default config: AUTO BOOT; JTAG always available unless JTAG pins are set as GPIO.
- VCCX and VCCO0 are internally joined on QN88P; VCCX requirements (≥2.375 V) apply.
