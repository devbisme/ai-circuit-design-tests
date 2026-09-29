# U9 GW1NR-LV9QN88PC6/I5 — pin assignment (source of truth: `fpga.py` constants)

For the HDL `.cst` constraints file. Pin names are from `symbols/dual_adc_usb.kicad_sym`
(Gowin IDE `GW1NR-9-PSRAM/QFN88.json`, rev-2 corrected). All 48 3.3 V I/O (banks 1+2) are used.

## Bank 2 — VCCIO2 = 3.3 V (IO_TYPE LVCMOS33)
| Pin | Pad name | Net | Dir (FPGA view) |
|---|---|---|---|
| 17 | IOB2A | DA0 | in |
| 18 | IOB2B | DA1 | in |
| 19 | IOB4A | DA2 | in |
| 20 | IOB4B | DA3 | in |
| 25 | IOB8A | DA4 | in |
| 26 | IOB8B | DA5 | in |
| 27 | IOB11A | DA6 | in |
| 28 | IOB11B | DA7 | in |
| 29 | IOB13A | DA8 | in |
| 30 | IOB13B | DA9 | in |
| 31 | IOB15A | DA10 | in |
| 32 | IOB15B | DA11 | in |
| 33 | IOB23A | DB0 | in |
| 34 | IOB23B | DB1 | in |
| 35 | IOB29A/GCLKT_4 | FPGA_CLK (40 MHz) | in, global clock |
| 36 | IOB29B/GCLKC_4 | DB2 | in |
| 37 | IOB31A | DB3 | in |
| 38 | IOB31B | DB4 | in |
| 39 | IOB33A | DB5 | in |
| 40 | IOB33B | DB6 | in |
| 41 | IOB41A | DB7 | in |
| 42 | IOB41B | DB8 | in |
| 47 | IOB43B | DB9 | in |

## Bank 1 — VCCIO1 = 3.3 V (IO_TYPE LVCMOS33)
| Pin | Pad name | Net | Dir (FPGA view) |
|---|---|---|---|
| 48 | IOR24B | DB10 | in |
| 49 | IOR24A | DB11 | in |
| 50 | IOR22B | ADC_DVA | in |
| 51 | IOR17B/GCLKC_3 | ADC_STPD | out (R15 10k pull-down in adc block) |
| 52 | IOR17A/GCLKT_3 | FT_CLKOUT (60 MHz) | in, global clock |
| 53 | IOR15B/DOUT/WE_N | FT_D0 | inout |
| 54 | IOR15A/DIN/CLKHOLD_N | FT_D1 | inout |
| 55 | IOR14B/SSPI_CS_N/D0 | FT_D2 | inout |
| 56 | IOR14A/SO/D1 | FT_D3 | inout |
| 57 | IOR13A/FASTRD_N/D3 | FT_D4 | inout |
| 59 | IOR12B/MCLK/D4 | FT_D5 | inout |
| 60 | IOR12A/MCS_N/D5 | FT_D6 | inout |
| 61 | IOR11B/MO/D6 | FT_D7 | inout |
| 62 | IOR11A/MI/D7 | FT_RXF_N | in |
| 63 | IOR5A/RPLL_T_in | FT_TXE_N | in |
| 68 | IOT42B | FT_RD_N | out |
| 69 | IOT42A | FT_WR_N | out |
| 70 | IOT41B | FT_SIWU_N | out |
| 71 | IOT41A | FT_OE_N | out |
| 72 | IOT39B | LED_ACT (R21 1k → D2) | out, active high |
| 73 | IOT39A | LED_TRIG (R22 1k → D3) | out, active high |
| 74 | IOT38B | TRIG_IN (R23 100R ← J5.1) | in |
| 75 | IOT38A | TRIG_OUT (R24 100R → J5.2) | out |
| 76 | IOT37B | GPIO1 (J5.3) | inout |
| 77 | IOT37A | GPIO2 (J5.4) | inout |

**Constraint-file must:** pins 53–62 are dual-purpose SSPI/MSPI/CPU config pins. In Gowin IDE
set *Use SSPI as regular IO* and *Use MSPI as regular IO* (and keep *Use JTAG as regular IO* OFF),
or place & route will refuse them. AUTOBOOT does not use these pins.

## Bank 3 — VCCIO3 = 1.8 V (PSRAM bank; config only)
| Pin | Pad name | Net |
|---|---|---|
| 5 | IOL11A/TMS | JTAG_TMS → J4.5 |
| 6 | IOL11B/TCK | JTAG_TCK → J4.1 |
| 7 | IOL12B/TDI | JTAG_TDI → J4.9 |
| 8 | IOL13A/TDO | JTAG_TDO → J4.3 |
| 9 | IOL13B/RECONFIG_N | FPGA_RECONFIG_N: R20 10k → V1V8, J4.6 |
| 87 | IOT6B/MODE1 | FPGA_MODE1: R19 1k → GND |
| 88 | IOT5A/MODE0 | FPGA_MODE0: R18 1k → GND |
| 3, 4, 10, 11, 13–16, 79–86 | (4 = JTAGSEL_N, internal pull-up; 10 = GCLKT_6) | NC |

## Power
V1V2: 1, 22, 45, 66 · V3V3D: 64, 67, 78 (VCCX/VCCIO0), 58 (VCCIO1), 23, 44 (VCCIO2) ·
V1V8: 12 (VCCIO3) · GND: 2, 21, 24, 43, 46, 65, EP 89.

## J4 JTAG (2×5, 2.54 mm; USB-Blaster-style layout, **verify against the programmer cable**)
1 TCK · 2 GND · 3 TDO · 4 VREF (V1V8) · 5 TMS · 6 RECONFIG_N · 7 NC · 8 NC · 9 TDI · 10 GND
