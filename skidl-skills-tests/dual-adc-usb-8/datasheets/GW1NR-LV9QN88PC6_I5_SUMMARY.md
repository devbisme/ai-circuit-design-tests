# GW1NR-LV9QN88PC6/I5 — Gowin LittleBee FPGA, 8.6k LUT, 64 Mbit PSRAM in package  [KEYSTONE, U9]

Sources:
- `datasheets/GW1NR-LV9QN88PC6_I5.pdf` = UG119-1.8.4E, *GW1NR Package & Pinout*: pin quantities, the QN88P pin/bank view (Fig 3-8, p.15) and the package outline (p.22–23).
- `datasheets/GW1NR-9_DS117.pdf` = DS117-3.2.5E datasheet: ROC, static current, PSRAM.
- `datasheets/GW1NR-9_UG284.pdf` = UG284-1.9.7E schematic manual: MODE, RECONFIG_N/READY/DONE, JTAGSEL_N.
- **UG803 is behind a Gowin login.** Rev 2 per-pin names come from Gowin IDE package data (`GW1NR-9-PSRAM/QFN88.json`, GitHub mirror `abhra0897/gowin-easy-linux`), cross-checked against the Sipeed Tang Nano 9K schematic.

Symbol: generated `dual_adc_usb:GW1NR-LV9QN88PC6` (89 pins, EP = pin 89). Footprint: `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` (EP pad "89").

| Spec | Value |
|------|-------|
| Package | QN88P, 10×10 mm, 0.4 mm pitch, A(nom) 0.75 mm |
| VCC (core, LV) | 1.14–1.26 V; ripple ≤3 % |
| VCCX | 2.375–3.6 V; ripple ≤5 % |
| VCCIOx | 1.14–3.6 V; ripple ≤5 %. VCCX/VCCIO0 share pins on QN88P; VCCX limits govern |
| Ramp | monotonic; VCC 0.6–6 mV/µs; VCCX 0.6–10 mV/µs; VCCIO 0.1–10 mV/µs |
| Static current (typ, 25 °C) | ICC 3.5 mA; ICCX 5 mA; ICCIO 2 mA |
| Temp (I5) | TJ –40…+100 °C |

## Power pins (UG119 Table 3-8, **verified**)
| Pins | Name in symbol | Net |
|---|---|---|
| 1, 22, 45, 66 | VCC | V1V2 |
| 64, 67, 78 | VCCX/VCCIO0 | V3V3D |
| 58 | VCCIO1 | V3V3D |
| 23, 44 | VCCIO2 | V3V3D |
| **12** | **VCCIO3** | V1V8 (PSRAM bank, see below) |
| 2, 21, 24, 43, 46, 65 | VSS | GND |
| 89 | EP | GND (thermal) |

**EasyEDA/LCSC labels pin 12 "VCCX/VCCO0". That is wrong.** Gowin UG119 Table 3-8 lists 12 as VCCIO3 and VCCX/VCCIO0 as 64/67/78 only. The generated symbol follows Gowin.

## Bank membership (UG119 Fig 3-8 colours vs Table 2-6 counts, **verified**)
| Bank | Pins | Count | VCCIO |
|---|---|---|---|
| BANK1 | 48–57, 59–63, 68–77 | 25 | VCCIO1 (pin 58) = 3.3 V |
| BANK2 | 17–20, 25–42, 47 | 23 | VCCIO2 (pins 23, 44) = 3.3 V |
| BANK3 | 3–11, 13–16, 79–88 | 23 | VCCIO3 (pin 12) = 1.8 V |
| BANK0 | — | 0 | (VCCX/VCCIO0 pins only) |

**3.3 V I/O budget = 25 + 23 = 48** (banks 1 and 2). Bank 3 (23 pins, including MODE0/1, JTAG, RECONFIG_N and DONE) runs at 1.8 V.

## Per-pin names (rev 2, **cross-checked from two sources**)
The sources are Gowin's own IDE package file `GW1NR-9-PSRAM/QFN88.json`. `device_package.csv` maps
GW1NR-LV9QN88PC6/I5 to it. It is a GitHub mirror of Gowin IDE data (`abhra0897/gowin-easy-linux`),
so it is vendor data but not the UG803 document. The second source is the Sipeed Tang Nano 9K
schematic (same GW1NR-LV9QN88P). The two agree on every pin.

**Corrections vs EasyEDA (rev 1). The symbol is fixed.**
| Pin | EasyEDA (wrong) | Gowin IDE + Tang Nano 9K |
|---|---|---|
| 3 | IOL2A | **IOT2A** |
| 10 | IOL14A/DONE | **IOL15A/GCLKT_6** |
| 11 | IOL15A/GCLKT_6 | **IOL16B** |
| 13 | IOL22A | **IOL21B** |
| 15 | IOL26A | **IOL25B** |

**DONE and READY are not bonded on QN88P.** Neither source lists them. Do not wire, pull up or
probe a "DONE" pin 10.

- **Bank 3 (1.8 V):**
  - 3 IOT2A; 4 IOL5A/JTAGSEL_N/LPLL_T_in; 5 IOL11A/TMS; 6 IOL11B/TCK; 7 IOL12B/TDI; 8 IOL13A/TDO
  - 9 IOL13B/RECONFIG_N; 10 IOL15A/GCLKT_6; 11 IOL16B; 13 IOL21B; 14 IOL22B; 15 IOL25B; 16 IOL26B
  - 79 IOT12B, 80 IOT12A, 81 IOT11B, 82 IOT11A, 83 IOT10B, 84 IOT10A, 85 IOT8B, 86 IOT8A
  - 87 IOT6B/MODE1; 88 IOT5A/MODE0
- **Bank 2:** 17 IOB2A, 18 IOB2B, 19 IOB4A, 20 IOB4B, 25 IOB8A, 26 IOB8B, 27 IOB11A, 28 IOB11B, 29 IOB13A,
  30 IOB13B, 31 IOB15A, 32 IOB15B, 33 IOB23A, 34 IOB23B, **35 IOB29A/GCLKT_4**, 36 IOB29B/GCLKC_4,
  37 IOB31A, 38 IOB31B, 39 IOB33A, 40 IOB33B, 41 IOB41A, 42 IOB41B, 47 IOB43B.
- **Bank 1:**
  - 48 IOR24B; 49 IOR24A; 50 IOR22B; 51 IOR17B/GCLKC_3; **52 IOR17A/GCLKT_3** (Tang Nano 9K feeds its 27 MHz XO here)
  - 53 IOR15B/DOUT/WE_N; 54 IOR15A/DIN/CLKHOLD_N; 55 IOR14B/SSPI_CS_N/D0; 56 IOR14A/SO/D1; 57 IOR13A/FASTRD_N/D3
  - 59 IOR12B/MCLK/D4; 60 IOR12A/MCS_N/D5; 61 IOR11B/MO/D6; 62 IOR11A/MI/D7; 63 IOR5A/RPLL_T_in
  - 68 IOT42B … 77 IOT37A (pairs 42/41/39/38/37, B before A)
- Power-name spelling: Gowin IDE says `VCCO3`, `VCCO0/VCCX`. The symbol keeps UG119's `VCCIO3`,
  `VCCX/VCCIO0`. Same pins; reference power pins by number anyway.

In SKiDL, **refer to U9 pins by number** (e.g. `u9[35]`). The names contain `/`.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Power-pin numbers | as table above | UG119 Table 3-8 p.15 — **verified** |
| 3.3 V-capable I/O count | 48 (bank1 25 + bank2 23) | UG119 Table 2-6 + Fig 3-8 — **verified** |
| Bank of pins 5–10, 87–88 | bank 3 (1.8 V side) | UG119 Fig 3-8 — **verified** |
| Bank of pin 35 / pin 52 | bank 2 / bank 1 | UG119 Fig 3-8 — **verified** |
| PSRAM interface bank voltage | "bank that connects to the PSRAM needs to be 1.8 V" | DS117 §2.2.2 — **verified** |
| *Which* bank connects to PSRAM | bank 3 | **REF-DESIGN corroborated.** The Tang Nano 9K runs only bank 3 at 1.8 V (all its bank-3 nets are suffixed `_1V8`, VCCO3_1V8), consistent with DS117's "PSRAM bank must be 1.8 V". No Gowin document states the bank number. Plus the QN88→QN88P diff-pair inference below |
| AUTOBOOT (internal flash) | MODE[2:0] = 000 | UG284 Table 6 — **verified** |
| MODE pin strapping | Gowin recommends 1 kΩ pull-down (4.7 kΩ pull-up); internal weak pull-ups | UG284 §MODE — **verified** |
| MODE0 = pin 88, MODE1 = pin 87 | — | Gowin IDE package data + Tang Nano 9K agree — **vendor data (not UG803)** |
| MODE2 on QN88P | not bonded (absent from the Gowin IDE pin file). The Tang Nano 9K pulls MODE0/MODE1 down (4.7 kΩ) and autoboots from internal flash, so MODE2 behaves as 0 | **REF-DESIGN** — no Gowin text |
| RECONFIG_N (READY/DONE unbonded here) | internal weak pull-up; reference circuit uses 4.7 kΩ pull-ups to the pin's bank voltage | UG284 Fig 5 — **verified** |
| JTAG pins | TMS 5, TCK 6, TDI 7, TDO 8; JTAGSEL_N 4; RECONFIG_N 9 | Gowin IDE package data + Tang Nano 9K — **vendor data (not UG803)** |
| DONE / READY | **not bonded on QN88P** | Gowin IDE package data (absent) + Tang Nano 9K (pin 10 = LED1 on IOL15A) |
| GCLK pins | GCLKT_4 = 35, GCLKT_3 = 52, GCLKT_6 = 10 | Gowin IDE package data + Tang Nano 9K — **vendor data (not UG803)** |
| EP size | package D2/E2 6.64/6.74/6.84 mm; recommended land 6.8×6.8 mm; lead land 0.85×0.20 mm, pitch 0.4, row pitch P = 9.90 | UG119 p.22–23 — **verified** |

The bank-3 inference is not proof. Between QN88 and QN88P, only bank 3's differential-pair counts change (8/4 → 6/3). Banks 1 and 2 are identical. That points at bank 3 being the one shared with the PSRAM.

## Notes
- The footprint EP is 6.74 mm, which is the package nominal. Gowin's recommended land is 6.8 mm, so they are compatible and the footprint is OK.
- Dynamic core/IO current is not in the datasheet: run the Gowin Power Estimator. Static values are the floor.
