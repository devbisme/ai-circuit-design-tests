# Sourced BOM — dual_adc_usb (qty 5 build), rev.4

Rev.4 is a **tiny, targeted addition pass** against phase-4 rev.6 (Decision 16) plus a
fpga_core-coder-reported decoupling gap — not a re-source: the 163 previously-verified refs
keep their prior stock/price/tier/symbol/footprint data unchanged. Only 6 new refs were added
and freshly verified live via the `pcbparts` MCP on 2026-09-23:
- **U15, C87** — second TPS22918DBVR load switch + 220 pF C0G CT cap, fixing U14's 50 µs
  soft-start vs. the 180 µs VCCIO3 ramp floor (see `power_tree`, below).
- **C514-C517** — 4 more 100 nF decoupling caps on U5 (GW1NR-9), closing a 7-of-11 shortfall
  against `net_plan.md`'s decoupling policy (see `fpga_core`, below).

One stale note was also corrected in place: U5's I/O-margin note (was "unverified", now closed
per phase 4 rev.5: 48 available vs. 46 required, +2 margin). `use_cache = false` — no
cross-project cache was read or written for this pass.

Columns: `Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes`

## afe_input (A: J1/R101/R102/C101-103/D101 — B: J2/R201/R202/C201-203/D201)

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| J1, J2 | KH-BNC50-3511 | C2837587 | 6798 | $0.9327 | TH-Right-Angle | Extended | Connector:Conn_Coaxial | Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal | ⚠️ Footprint resolves but pin spacing not cross-checked against KH-BNC50-3511's own mechanical drawing — confirm at datasheet phase |
| R101, R201 | ARG05BTC9103 (Viking Tech) | C2828756 | 4148 | $0.0298 | 0805 | Extended | Device:R | Resistor_SMD:R_0805_2012Metric | **[calc] 910 kΩ 0.1%, not the architect's exact 909 kΩ** — E96 909 kΩ at 0.1% has only 10–17 pcs in stock (fails the 100-unit floor); 910 kΩ 0.1% is the nearest in-stock value. Shifts the divider from ÷11.000 to ÷11.0091 (+0.09%), inside the architecture's own ±1% DC-gain fallback band. 150 V rated, matches the 0805-for-75V-working-voltage requirement |
| R102, R202 | RT0603BRD0790K9L (YAGEO) | C728600 | 20986 | $0.0430 | 0603 | Extended | Device:R | Resistor_SMD:R_0603_1608Metric | Exact 90.9 kΩ 0.1% |
| C101, C201 | 0603CG150G500NT (FH) | C2836768 | 8757 | $0.0155 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | 15 pF C0G ±2% — divider top compensation, exact spec |
| C102, C202 | C0603C131F5GACTU (KEMET) | C2342146 | 4040 | $0.3877 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | 130 pF C0G **±1%** (beats the ±2% spec) — no 0603 130 pF C0G ±2% part is in stock; ±1% costs more ($0.39 ea) but keeps the tolerance requirement |
| C103, C203 | 0603CG150G500NT (FH) | C2836768 | 8757 | $0.0155 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | Same part as C101/C201 — divider bottom's fixed 15 pF leg |
| D101, D201 | BAV199 (HXY MOSFET) | C5184419 | 82914 | $0.0139 | SOT-23 | Extended | Diode:BAV99 | Package_TO_SOT_SMD:SOT-23 | **Symbol corrected rev.3: `Diode:BAV19` → `Diode:BAV99`.** `BAV19` is a 2-pin DO-35 single diode — cannot sit on this 3-pad SOT-23 footprint or clamp two rails. MPN/LCSC/footprint unchanged |

## afe_buffer (U1, C11-C14, C15, C16)

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U1 | AD8066ARZ-R7 | C9647 | 1478 | $9.0690 | SOIC-8-150mil | Extended | ⚠️ SYMBOL NEEDED | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm | `[CRIT]` single-source dual-JFET buffer — I_B≤55nA requirement, do not substitute |
| C11, C13 | CL05A105KA5NQNC (Samsung) | C52923 | 7212978 | $0.0099 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1 µF X5R — rail bulk, VA_POS/VA_NEG local |
| C12, C14 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R — rail bulk, VA_POS/VA_NEG local |
| **C15, C16 (NEW)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — U1 HF decoupling at the pins, C15 on `VA_POS`, C16 on `VA_NEG`. Rev.2 gave U1 no HF bypass at all — a defect on a 10 MSPS front end |

## afe_driver (A: U2/R111-118/L111-114/C111-119/D111-112 — B: U3/R211-218/L211-214/C211-219/D211-212)

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U2, U3 | THS4521IDR | C16092 | 12361 | $1.7513 | SOIC-8-150mil | Extended | Amplifier_Difference:THS4521ID | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm | `[CRIT]` FDA, symbol is a prefix match (drops the `R` reel suffix) — pinout unaffected |
| R111, R113, R211, R213 | RT0402BRD071KL (YAGEO) | C852624 | 820234 | $0.0271 | 0402 | Extended | Device:R | Resistor_SMD:R_0402_1005Metric | 1.00 kΩ 0.1% — Rg |
| R112, R114, R212, R214 | RT0402BRD071K1L (YAGEO) | C852602 | 17232 | $0.0272 | 0402 | Extended | Device:R | Resistor_SMD:R_0402_1005Metric | 1.10 kΩ 0.1% — Rf, sets differential gain 1.100 |
| C111, C112, C211, C212 | 0402CG4R7C500NT (FH) | C1569 | 668020 | $0.0058 | 0402 | Preferred | Device:C | Capacitor_SMD:C_0402_1005Metric | 4.7 pF C0G — FDA feedback/stability cap |
| R115, R116, R215, R216 | 0402WGF1000TCE (UNI-ROYAL) | C25076 | 5040965 | $0.0037 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 100 Ω 1% — AAF series/source resistor |
| L111, L113, L211, L213 | MLF2012A3R3JT000 (TDK) | C275371 | 7235 | $0.0389 | 0805 | Extended | Device:L | Inductor_SMD:L_0805_2012Metric | 3.3 µH **±5%**, SRF 60 MHz (spec: ≥40 MHz) — AAF L1 |
| L112, L114, L212, L214 | FHW0805UF5R6JST (FH) | C393992 | 602 | $0.0595 | 0805 | Extended | Device:L | Inductor_SMD:L_0805_2012Metric | 5.6 µH **±5%**, SRF 70 MHz (spec: ≥30 MHz) — AAF L2. Stock 602 — above the 100-unit floor but the thinnest margin on the board; buy the full qty-5 build (20 pcs) in one order |
| C113-C116, C213-C216 | GRM1885C1H681GA01D (Murata) | C464441 | 1497 | $0.0411 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | 680 pF C0G ±2% — AAF caps, exact spec |
| R117, R118, R217, R218 | 0402WGF220JTCE (UNI-ROYAL) | C25092 | 3963115 | $0.0029 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 22 Ω 1% — ADC series isolation |
| D111, D112, D211, D212 | BAT54S (hongjiacheng) | C7420333 | 1074516 | $0.0137 | SOT-23 | Preferred | Diode:BAT54S | Package_TO_SOT_SMD:SOT-23 | ADC input clamp pair, exact symbol match |
| C117, C217 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — P3V3A pin decoupling at U2/U3 |
| C118, C218 | CL05A105KA5NQNC (Samsung) | C52923 | 7212978 | $0.0099 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1 µF X5R — P3V3A local bulk at U2/U3 |
| C119, C219 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — ADC_CM decoupling (VOCM buffer, ≤±2 mA load only) |

## adc_dual (U4, R401, R402, C401-C410)

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U4 | ADS5231IPAGT | C2670079 | 154 | $31.7723 | TQFP-64-64P(10x10) | Extended | ⚠️ SYMBOL NEEDED | Package_QFP:TQFP-64_10x10mm_P0.5mm | `[CRIT]` **>$25 flag confirmed live.** 154 pcs at JLCPCB — the entire float. Single source, not EOL-flagged in this listing but TI's SBAS295A is a 2004/2007-era datasheet (R-8). Buy all 5 units for the build in one order; do not split across multiple JLC orders |
| R401 | 0402WGF5622TCE (UNI-ROYAL) | C25796 | 155052 | $0.0032 | 0402 | Preferred | Device:R | Resistor_SMD:R_0402_1005Metric | 56.2 kΩ 1% — ISET, datasheet-mandated value |
| R402 | 0402WGF1002TCE (UNI-ROYAL) | C25744 | 25516238 | $0.0034 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | **Placeholder 10 kΩ.** `R402`'s function is not stated in `net_plan.md` (only R401/ISET is documented) — likely the ADC_SEL serial-interface strap. Basic-tier, in-stock regardless of final value; datasheet-librarian to confirm SBAS295A's SEL strapping and correct the value if not 10 kΩ |
| C401-C405, C407-C410 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — AVDD pins ×5, REFT/REFB ×2, remaining pins ×2, per net_plan's ADS5231 decoupling policy |
| C406 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R — AVDD bulk |

R402 was deleted by the driver in an earlier pass (no datasheet-justified function on ADS5231) and
**stays deleted** — architecture rev.3 confirms `ADC_SEL` is FPGA-driven, not a strap (SBAS295A p.19).

## clock_gen (X1, R31, R32, C31)

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| X1 | SX3M10.000M20F30TNN | C2901558 | 3624 | $0.3158 | SMD3225-4P | Extended | ⚠️ SYMBOL NEEDED | Oscillator:Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm | 10.000 MHz CMOS XO, 1.62–3.63 V, 10 mA — freely substitutable per architecture (any ≤3.3 V, ≥±50 ppm, low-jitter XO) |
| R31, R32 | 0402WGF330JTCE (UNI-ROYAL) | C25105 | 1739786 | $0.0035 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 33 Ω 1% — clock series termination |
| C31 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — X1 supply decoupling |

## fpga_core (U5, J3, D51, D52, R51-R55, C501-C517)

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U5 | GW1NR-LV9QN88PC6/I5 | C5799578 | 173 | $23.3121 | QFN-88-1EP(8x8) | Extended | ⚠️ SYMBOL NEEDED | ⚠️ CUSTOM FP NEEDED | `[CRIT]` **Keystone part — memory architecture and I/O budget both depend on it.** 173 pcs, single source. No standard KiCad QFN-88 footprint exists (nearest is QFN-68/64/48-1EP at the same 8×8 mm body) — datasheet-librarian must build the exact QFN-88 pad ring from the Gowin package drawing. **Free-I/O verified closed (phase 4 rev.5, UG803): 48 3.3 V-capable I/O (BANK1+BANK2) vs. 46 required by architecture rev.3, +2 margin** — superseded the earlier "need ≥51, unverified" note |
| J3 | 2.54-1x6P Straight pin (BOOMELE) | C37208 | 309387 | $0.0416 | TH-1x6-2.54mm | Extended | Connector_Generic:Conn_01x06 | Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical | JTAG header |
| D51 | PSC-1608U52GC-G4 (HONGLITRONIC) | C22371297 | 413642 | $0.0146 | 0603 | Extended | Device:LED | LED_SMD:LED_0603_1608Metric | Green status LED |
| D52 | KT-0603R (Hubei KENTO) | C2286 | 2953947 | $0.0075 | 0603 | Basic | Device:LED | LED_SMD:LED_0603_1608Metric | Red status LED |
| R51, R52 | 0402WGF1001TCE (UNI-ROYAL) | C11702 | 10402570 | $0.0022 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 1 kΩ — LED current-limit |
| R53 | 0402WGF1002TCE (UNI-ROYAL) | C25744 | 25516238 | $0.0034 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 10 kΩ — RECONFIG_N pull-up |
| **R54, R55 (NEW)** | 0402WGF4701TCE (UNI-ROYAL) | C25900 | 16534319 | $0.0027 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 4.7 kΩ — MODE0 (U5 pin 88, R54) / MODE1 (U5 pin 87, R55) straps to `GND`. MODE[1:0]=00 → AUTO BOOT (UG290 Table 5-1, verified); MODE2 not bonded on QN88P |
| C501-C506 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — VCCIO ×4, VCC core ×2 per net_plan policy |
| C507, C509 | CL05A105KA5NQNC (Samsung) | C52923 | 7212978 | $0.0099 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1 µF X5R — P3V3D/P1V2 local bulk |
| C508, C510 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R — P3V3D/P1V2 rail bulk |
| **C511 (NEW)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — U5 pin 12 (`VCCIO3`, the PSRAM bank) point-of-load HF decoupling |
| **C512 (NEW)** | CL10A475KO8NNNC (Samsung) | C19666 | 2858952 | $0.0295 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 4.7 µF X5R — U5 pin 12 local bulk, sized above the 66 mA PSRAM peak transient |
| **C513 (NEW)** | CL21A226MAQNNNE (Samsung) | C45783 | 4468530 | $0.2221 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 22 µF X5R — `P1V8` rail bulk reservoir between U14 and U5 pin 12 |
| **C514, C515 (NEW, rev.4)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — the 2 remaining `P3V3D` VCCIO/VCCX pin-decoupling caps of the 6 `net_plan.md` line 178 requires (pins 23, 44, 58, 64, 67, 78); C501-C506 previously covered only 4 of the 6 |
| **C516, C517 (NEW, rev.4)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — the 2 remaining VCC-core pin-decoupling caps of the 4 `net_plan.md` line 178-179 requires (pins 1, 22, 45, 66); C501-C506 previously covered only 2 of the 4. **Closes a 7-of-11 100 nF shortfall on U5** found by the fpga_core coder reading `net_plan.md`'s decoupling policy against the BOM — see handoff `## Carried forward` |

## usb_bridge (U6, U7, U8, J4, Y1, R61-R66, R67, C601-C609, C610-C612)

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U6 | FT232HL-REEL | C51997 | 2016 | $9.7200 | LQFP-48-48P(7x7) | Extended | Interface_USB:FT232H | Package_QFP:LQFP-48_7x7mm_P0.5mm | `[CRIT]` symbol is a prefix match (generic FT232H, correct LQFP-48 pinout) |
| U7 | 93LC56BT-I/OT | C190271 | 11422 | $0.4395 | SOT-23-6 | Extended | Memory_EEPROM:93LCxxBxxOT | Package_TO_SOT_SMD:SOT-23-6 | `[CRIT]` do not substitute — 93LC46/66 are pin-compatible but organisation-incompatible. **Symbol corrected rev.3: `93LCxxB` → `93LCxxBxxOT`** (BOM cell was the 8-pin DIP/SOIC symbol; sourced part is SOT-23-6). Confirm pin 1 orientation before layout |
| U8 | USBLC6-2SC6 (UMW) | C2687116 | 98047 | $0.0476 | SOT-23-6 | Extended | Power_Protection:USBLC6-2SC6 | Package_TO_SOT_SMD:SOT-23-6 | Cheapest of 9 in-stock USBLC6-2SC6 sources, all electrically identical |
| J4 | TYPE-C 16PIN 2MD(073) (SHOU HAN) | C2765186 | 1071008 | $0.0745 | SMD-16P-RightAngle | Extended | Connector:USB_C_Receptacle_USB2.0_16P | Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal | `[PKG]` 16-pin body confirmed (6-pin bodies lack the second CC). Footprint resolves as the closest 16P horizontal match — verify against the SHOU HAN datasheet's mechanical drawing before layout |
| Y1 | X322512MOB4SI (YXC) | C70565 | 33683 | $0.0945 | SMD3225-4P | Extended | Device:Crystal_GND24 | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | 12 MHz, 12 pF load, ±20 ppm stability (beats the ±30 ppm spec). **Symbol corrected rev.3: `Device:Crystal` → `Crystal_GND24`** (BOM cell was the 2-pin symbol; sourced part is a 4-pad 3225) |
| R61, R62 | 0402WGF5101TCE (UNI-ROYAL) | C25905 | 6741851 | $0.0024 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 5.1 kΩ 1% — CC1/CC2 Type-C sink pulldowns |
| R63 | 0402WGF1202TCE (UNI-ROYAL) | C25752 | 1206266 | $0.0032 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 12 kΩ 1% — FT232H REF, FTDI-mandated |
| R64 | 0402WGF2201TCE (UNI-ROYAL) | C25879 | 1283229 | $0.0053 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 2.2 kΩ — EEPROM `EE_DO` series resistor |
| R65 | 0402WGF1002TCE (UNI-ROYAL) | C25744 | 25516238 | $0.0034 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 10 kΩ — FT232H `PWREN#` pull-up, FTDI Table 3.5 (confirmed, phase 4 rev.3) |
| **R66 (NEW)** | 0402WGF1002TCE (UNI-ROYAL) | C25744 | 25516238 | $0.0034 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 10 kΩ — EEPROM `EE_DO` pull-up to `FT_3V3` (FTDI Table 3.3), **in addition to** R64's 2.2 kΩ series resistor. **Distinct part from R67** — rev.3 refdes collision resolved, R66 keeps the EEPROM assignment |
| **R67 (NEW)** | 0402WGF1002TCE (UNI-ROYAL) | C25744 | 25516238 | $0.0034 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 10 kΩ — `FIFO_SIWU_N` tie-off to `FT_3V3`, inactive-high (SIWU# is a plain input, safe to strap). **Distinct part from R66** — the SIWU strap moved here to resolve the collision |
| C601, C602 | 0402CG120J500NT (FH) | C1547 | 1310066 | $0.0056 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 12 pF C0G — Y1 load caps |
| C603-C605 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — `FT_3V3` pin decoupling |
| C606 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | **Note corrected rev.3:** on `FT_VCCA_1V8` (U6 pin 37), a +1.8 V **output** of the FT232H's internal LDO — one cap to GND, **never** tied to `FT_3V3` or `P1V8` (decision #5). Previously grouped with the C603-C606 `FT_3V3` bucket, which was wrong for this one ref |
| C607, C609 | CL05A105KA5NQNC (Samsung) | C52923 | 7212978 | $0.0099 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1 µF X5R — FT_3V3 local bulk |
| C608 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | **Note corrected rev.3:** on `FT_VCORE_1V8` (U6 pin 38), a +1.8 V **output** of the FT232H's internal LDO — one cap to GND, **never** tied to `FT_3V3` or `P1V8` (decision #5). Previously mislabelled "U7 EEPROM VCC decoupling"; U7 VCC had no cap at all, hence new C612 below. C606 (in the C603-C606 row above) is the same situation on `FT_VCCA_1V8` (U6 pin 37) |
| **C610 (NEW)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — U6 `VPHY` (pin 16) decoupling |
| **C611 (NEW)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — U6 `VPLL` (pin 20) decoupling |
| **C612 (NEW)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — U7 EEPROM `VCC` decoupling. Rev.2 left VPHY/VPLL/U7 VCC with no decoupling at all (C608 is on a *different* net, U6's internal `FT_VCORE_1V8`, not U7) |

## power_tree (U9-U15, Q1, L71, L72, FB1, R71-R76, C71-C87)

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U9 | TPS22918DBVR | C131941 | 8480 | $0.3991 | SOT-23-6 | Extended | ⚠️ SYMBOL NEEDED | Package_TO_SOT_SMD:SOT-23-6 | `[CRIT]` load switch, EN 5.5 V-tolerant confirmed in listing |
| U10, U11 | TLV62569DBVR | C141836 | 135052 | $0.0757 | SOT-23-5 | Extended | Regulator_Switching:TLV62569DBV | Package_TO_SOT_SMD:SOT-23-5 | V_FB = 0.6 V confirmed live ("600mV~5.5V Adjustable") — R72/R73/R74/R75 values are valid as computed |
| U12 | RT9013-33GB | C47773 | 240200 | $0.1371 | SOT-23-5 | Extended | ⚠️ SYMBOL NEEDED | Package_TO_SOT_SMD:SOT-23-5 | Confirmed Richtek-branded (not the cheaper unbranded C19268157 clone) — chose the branded part for datasheet reliability |
| U13 | TPS60403DBVR | C11338 | 15985 | $0.6983 | SOT-23-5 | Extended | Regulator_SwitchedCapacitor:TPS60403DBV | Package_TO_SOT_SMD:SOT-23-5 | **250 kHz confirmed live — no ≥1 MHz pin-compatible inverting charge pump was found in stock at JLCPCB.** Architecture's R76+C80 RC mitigation (37 dB at 250 kHz) stands as specified |
| **U14 (NEW)** | AP2127K-1.8TRG1 | C151375 | 35912 | $0.1537 | SOT-23-5 | Extended | Regulator_Linear:AP2127K-1.8 | Package_TO_SOT_SMD:SOT-23-5 | `[CRIT]` 1.8 V LDO for U5 `VCCIO3`/PSRAM bank — the entire 4 MB sample buffer rail. **Selected on soft-start, not current or dropout** (Gowin caps the VCCIO ramp at 10 mV/µs ⇒ t_on ≥ 180 µs). Stock/package/symbol/footprint all confirmed. **Datasheet finding (Diodes DS36478 Rev.7-2 p.5, Electrical Characteristics):** `t_ss` (Soft Start Time) = **50 µs typ, no max spec** — a 0→1.8 V step in 50 µs is ≈36 mV/µs average, roughly **3.6× faster** than the ≤10 mV/µs / ≥180 µs floor the architecture requires. AP2127K is still the only one of the three candidates whose JLC parametric record advertises "Built-in soft-start" at all — RT9013-18GB and TLV73318PDBVR show no soft-start feature in their records either, and TLV73318P's own datasheet describes a **capacitor-free, minimal-delay** architecture, which reads as *faster*, not slower. **No in-stock candidate has been confirmed ≥180 µs by its own datasheet.** Sourced as directed (in stock, package/footprint/symbol all correct) but flagging this as an open electrical risk rather than silently passing it — see handoff `## Carried forward` for the recommended next step (external RC delay on the SOT-23-5 Shutdown pin, pin 3, for an independent slow turn-on) |
| Q1 | BSS138 (hongjiacheng) | C7420339 | 126833 | $0.0264 | SOT-23 | Preferred | Transistor_FET:BSS138 | Package_TO_SOT_SMD:SOT-23 | V_GS(th)=1.2V confirmed (≤1.5V requirement met) — upgraded to the Preferred-tier source over the Extended-tier C78284 at the same price point |
| L71, L72 | WIP201610P-2R2ML (INPAQ) | C315717 | 16293 | $0.0237 | 0806-Shielded | Extended | Device:L | Inductor_SMD:L_Murata_DFE201610P | 2.2 µH, 1.71 A saturation, shielded wirewound — meets the ≥1.5 A / shielded requirement. Footprint is the closest same-body-code (201610) match; confirm pad pattern against the INPAQ datasheet before layout |
| FB1 | CBW160808U601T (FH) | C139183 | 662682 | $0.0116 | 0603 | Extended | Device:L | Inductor_SMD:L_0603_1608Metric | **Package substitution 0805→0603** (`[FREE]` tag) — no 0805 ferrite bead at 600Ω@100MHz meets the ≥1A current spec (max found was 500mA); this 0603 part hits 600Ω@100MHz at 1A exactly |
| R71 | 0402WGF1003TCE (UNI-ROYAL) | C25741 | 9667613 | $0.0025 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 100 kΩ — load-switch EN pull-up. **Must return to FT_3V3, never P3V3D** (net_plan hard rule) |
| R72 | RC0402FR-07180KL (YAGEO) | C138046 | 524205 | $0.0041 | 0402 | Extended | Device:R | Resistor_SMD:R_0402_1005Metric | 180 kΩ 1% — 3V3D buck feedback high side |
| R73 | RC0402FR-0740K2L (YAGEO) | C137983 | 1466394 | $0.0025 | 0402 | Extended | Device:R | Resistor_SMD:R_0402_1005Metric | 40.2 kΩ 1% — 3V3D buck feedback low side (180k/40.2k = 4.478, gives 3.287 V from 0.6 V ref, matches architecture) |
| R74, R75 | 0402WGF1003TCE (UNI-ROYAL) | C25741 | 9667613 | $0.0025 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 100 kΩ 1% ×2 — 1V2 buck feedback (1:1 ratio gives 1.2 V from 0.6 V ref) |
| R76 | FRC0402F4R70TS (FOJAN) | C2909356 | 878375 | $0.0016 | 0402 | Extended | Device:R | Resistor_SMD:R_0402_1005Metric | 4.7 Ω 1% — VA_NEG post-filter, R-2 mitigation |
| C71 | 0402B102K500NT (FH) | C1523 | 3961246 | $0.0042 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1 nF X7R — LS_CT soft-start timing |
| C72, C74 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R — buck input caps (U10/U11 VIN) |
| C73, C75 | CL21A226MAQNNNE (Samsung) | C45783 | 4468530 | $0.2221 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 22 µF X5R — buck output bulk |
| C76 | CL05A105KA5NQNC (Samsung) | C52923 | 7212978 | $0.0099 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1 µF X5R — P3V3A LDO output local |
| C77 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R — P3V3A LDO output bulk |
| C78 | CL10B105KB8NQNC (Samsung) | C5199872 | 2585968 | $0.0269 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | 1 µF X7R 50V — TPS60403 flying cap |
| C79 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R — charge pump raw output |
| C80 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R — VA_NEG post-filter (with R76: 37 dB at 250 kHz, R-2 mitigation) |
| C81 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R — VBUS_SW bulk |
| C82 | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | TPS60403 input bypass cap (CI) on `VA_POS` at U13.IN — resolved in phase 4 rev.3 (TI app note calls for three 1 µF-class caps: CI/Cfly/CO; C78=fly, C79=out, C82=in) |
| C83 | CL21A106KAYNNNE (Samsung) | C15850 | 5969884 | $0.0790 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10 µF X5R 25V — VBUS bulk, ≤10 µF total ahead of the load switch (USB inrush limit) |
| **C84 (NEW)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — U14 `VIN` pin decoupling on `P3V3D` |
| **C85 (NEW)** | CL05B104KO5NNNC (Samsung) | C1525 | 27385222 | $0.0045 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 100 nF X7R — U14 `VOUT` pin HF decoupling on `P1V8` |
| **C86 (NEW)** | CL10A475KO8NNNC (Samsung) | C19666 | 2858952 | $0.0295 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 4.7 µF X5R — U14 `VOUT` local bulk. Exceeds the AP2127K datasheet's typical-app-circuit minimum (1 µF ceramic for C_IN/C_OUT) with margin for the PSRAM's 66 mA peak transient |
| **U15 (NEW, rev.4)** | TPS22918DBVR | C131941 | 8022 | $0.3988 | SOT-23-6 | Extended | `dual_adc_usb:TPS22918DBVR` | Package_TO_SOT_SMD:SOT-23-6 | `[CRIT]` **The fix for U14's soft-start finding (phase 4 rev.6, Decision 16).** Second load switch, inserted between U14 `VOUT` (`P1V8`) and U5 pin 12 (`VCCIO3`), with C87 on its CT pin providing an independent, datasheet-measured 260 µs rise time — clears the 180 µs VCCIO ramp floor with ~44% margin; U14's own 50 µs internal soft-start cannot. **Same MPN/LCSC as U9** (already a qualified, in-stock, same-footprint part on this BOM) — stock re-verified live this pass (8022 pcs vs. U9's 8480 at its own sourcing time; still deep stock). Symbol already generated (`dual_adc_usb:TPS22918DBVR`, `find-symbol.py` `EXACT`, confirmed phase 4). **ON-pin drive left to the power_tree coder** (mirror U9's R71 100 kΩ pull-up pattern to `FT_3V3`, or tie to U14's own enable) — no new resistor sourced speculatively, since neither `net_plan.md` nor the phase-4 recommendation specifies one. U14 and its C84/C85/C86 stay exactly as sourced |
| **C87 (NEW, rev.4)** | CC0402JRNPO9BN221 (YAGEO) | C107001 | 412572 | $0.0041 | 0402 | Extended | Device:C | Capacitor_SMD:C_0402_1005Metric | 220 pF **C0G/NP0** (not X7R — slew timing is dielectric-sensitive, X7R would drift the ramp) — U15's CT pin to GND. TI SLVSD76C §8.3.3/Table 2: 220 pF → 260 µs 10-90% rise time at V_IN=1.8 V. **No separate U15 VIN/VOUT bypass caps added** — checked, not assumed: `P1V8` (U15's VIN, shared with U14's VOUT) already carries C85 (100 nF) + C86 (4.7 µF); `VCCIO3` (U15's VOUT) already carries C511 (100 nF) + C512 (4.7 µF) + C513 (22 µF) downstream. Both sides exceed TI's ≥1 µF VIN-bypass / optional-C_L recommendation (datasheet §9.2.2/§10, p.16-20) with margin |

## Cost roll-up (qty 5, indicative, qty-1 unit pricing)

Actives + connectors ≈ $81.77; passives (precision R/C, AAF L/C, decoupling) ≈ $6-8 as the architect
estimated. Rev.3's 16 added refs (U14 + its passives, R54/R55, R66/R67, C15/C16, C610-C612) added
≈ $0.48/board, landing rev.3 at ≈ $88.5-90.5/board.

**Rev.4 adds 6 more refs (U15, C87, C514-C517), ≈ $0.42/board** — U15 is the only non-trivial line
($0.3988, Extended-tier SOT-23-6 load switch); C87 ($0.0041) and the four C514-C517 100 nF caps
($0.0045 each, $0.018 total) are sub-cent 0402 passives. **New total ≈ $88.9-90.9/board.** This
**pushes the top of the range ≈ $0.9 over the `[ASSUMED]` $90 target** — flagging plainly, not
absorbing quietly: rev.3 already had ~$0 headroom, and this pass had no offsetting cut to give (it
was scoped as fixes to two open correctness findings, not a cost pass). ADS5231 remains the **only**
part over the $25 flag, confirmed live at $31.7723 — no other new or existing part crosses that line.
C87 (YAGEO CC0402JRNPO9BN221) is a genuinely new Extended-tier part number — not a reused MPN like
U15/U9 — so it is the one line in this pass that adds an incremental JLCPCB Extended-part setup fee
the board did not already carry.
