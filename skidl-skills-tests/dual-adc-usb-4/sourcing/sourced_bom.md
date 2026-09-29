# Sourced BOM — dual_adc_usb

Stock/price/tier from pcbparts MCP (live JLCPCB mirror), queried 2026-09-10. Footprint strings
validated against `$KICAD9_FOOTPRINT_DIR` (`/usr/share/kicad/footprints`) with
`validate-footprints.py` — 18/18 non-generic footprints resolve. Symbols checked with
`find-symbol.py` plus manual KiCad `Device`/`Diode`/`Connector` library lookups for generic
parts the exact-MPN pass missed (TVS, trimmer cap, R-network, USB-C/BNC connectors).

Columns: `Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes`

## usb_power_in

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| J1 | TYPE-C-31-M-12 | C165948 | 275,804 | $0.186 | SMD RA 16P | Extended | Connector:USB_C_Receptacle_USB2.0_16P | Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12 | exact vendor footprint in KiCad lib |
| U1 | USBLC6-2SC6 (UMW) | C2687116 | 65,891 | $0.048 | SOT-23-6 | Extended | Power_Protection:USBLC6-2SC6 | Package_TO_SOT_SMD:SOT-23-6 | exact symbol match |
| D1 | SMF5.0A (hongjiacheng) | C19077497 | 276,661 | $0.030 | SOD-123FL | Preferred | Device:D_TVS | Diode_SMD:D_SOD-123F | generic uni-TVS symbol; JLC "SOD-123FL" = KiCad "SOD-123F" |
| U2 | SY6280AAC | C55136 | 63,781 | $0.092 | SOT-23-5 | Extended | ⚠️ SYMBOL NEEDED | Package_TO_SOT_SMD:SOT-23-5 | pin table: Silergy SY6280 datasheet p.1 (pkg/pinout), ISET formula p.6 |
| FB1 | BLM21PG221SN1D | C85840 | 160,452 | $0.030 | 0805 | Extended | Device:FerriteBead | Inductor_SMD:L_0805_2012Metric | 220Ω@100MHz/2A/45mΩ — substituted for the skeleton's illustrative 600Ω part, whose DCR (140mΩ) fails the ≤0.1Ω spec; this one meets ≥1A and ≤0.1Ω |
| R1, R2 | 0603WAF5101T5E | C23186 | 23.8M | $0.002 | 0603 | Basic | Device:R | Resistor_SMD:R_0603_1608Metric | 5.1kΩ 1% CC pull-down |
| R3 | — (value from SY6280 ISET formula) | — | — | — | 0603 | — | Device:R | Resistor_SMD:R_0603_1608Metric | **carried forward** — needs SY6280AAC datasheet ISET equation for ≈0.8 A limit |
| R4 | 0603WAF1004T5E | C22935 | 7.9M | $0.002 | 0603 | Basic | Device:R | Resistor_SMD:R_0603_1608Metric | 1MΩ 1% shield bleed |
| C1 | CL10A475KO8NNNC | C19666 | 3.7M | $0.033 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 4.7µF 16V X5R |
| C2 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF 50V X7R |
| C3 | CL21A106KAYNNNE | C15850 | 7.2M | $0.084 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10µF 25V X5R |
| C4 | CC0603KRX7R0BB472 | C115052 | 199,040 | $0.017 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | 4.7nF 100V X7R |

## power_rails

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U3 | TLV1117LV33DCYR (genuine TI) | C15578 | 842 | $0.335 | SOT-223 | Extended | Regulator_Linear:TLV1117-33 | Package_TO_SOT_SMD:SOT-223-3_TabPin2 | **decision:** chose genuine TI over the cheaper JSMSEMI clone C48937499 (166,989 stock, $0.11) — the clone's listed dropout is 1.2V@1A, which fails the architect's stated ≤0.6V-dropout reason for rejecting AMS1117. Genuine TI: 455mV@1A |
| U4 | TLV75512PDBVR (sub for AP2112K-1.2) | C2877864 | 3,636 | $0.233 | SOT-23-5 | Extended | Regulator_Linear:TLV75512PDBV | Package_TO_SOT_SMD:SOT-23-5 | **decision:** AP2112K-1.2TRG1 (C460310) is now at 77–80 units — FAIL (<100). Switched to the architect's own vetted second source (§ Next phase must #4). 1.2V/500mA fixed LDO, TI, SOT-23-5 |
| U5 | TLV75518PDBVR | C2877863 | 7,290 | $0.212 | SOT-23-5 | Extended | Regulator_Linear:TLV75518PDBV | Package_TO_SOT_SMD:SOT-23-5 | |
| U6 | TPS7A2033PDBVR | C2862740 | 58,150 | $0.219 | SOT-23-5 | Extended | ⚠️ SYMBOL NEEDED | Package_TO_SOT_SMD:SOT-23-5 | a 5-pin TPS7A20xx symbol exists (TPS7A20xxxDQN, X2SON-5) but package/pin order must be confirmed against the DBV datasheet before reuse — do not assume compatible |
| LED1 | CT-1608UGC-P4 | C52675989 | 237,305 | $0.003 | 0603 | Extended | Device:LED | LED_SMD:LED_0603_1608Metric | green, 520nm |
| R5 | 0603WAF1001T5E | C21190 | 27.0M | $0.003 | 0603 | Basic | Device:R | Resistor_SMD:R_0603_1608Metric | 1kΩ 1% |
| C5, C6 | CL21A106KAYNNNE | C15850 | 7.2M | $0.084 | 0805 | Basic | Device:C | Capacitor_SMD:C_0805_2012Metric | 10µF 25V X5R |
| C7 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF |
| C8–C13 | CL05A105KA5NQNC | C52923 | 9.9M | $0.012 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1µF 25V X5R ×6 |
| TP1–TP6 | generic test point | — | — | — | pad | — | Connector:TestPoint | TestPoint:TestPoint_Pad_D1.5mm | no MPN needed |

## bipolar_supply

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U7 | LM27762DSSR | C473398 | 10,397 | $1.009 | WSON-12-EP(2×3) | Extended | Regulator_SwitchedCapacitor:LM27762 | Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65 | **CP**, confirmed. Verify EP orientation/pin-1 mark against SNVSAF7C mechanical drawing in datasheet phase |
| R6–R9 | — (FB divider values from datasheet) | — | — | — | 0402 | — | Device:R | Resistor_SMD:R_0402_1005Metric | **carried forward from architecture** — LM27762 FB-resistor values for ±2.50V still `[VERIFY]`; use UNI-ROYAL 0402WGF Basic-tier series once values are known |
| C14 | CL10A106MA8NRNC | C96446 | 5.1M | $0.055 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 10µF 25V X5R, CP_VIN |
| C15 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF |
| C16 | CL05A105KA5NQNC | C52923 | 9.9M | $0.012 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1µF 25V X5R, flying cap |
| C17–C19, C98, C99 | 0603B225K160NT | C43922 | 454,894 | $0.027 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | 2.2µF 16V X7R ×5 — C98/C99 = ADS5231 REFT/REFB 2.2 µF (SBAS295A Fig. 21, design review) |
| C20, C21 | CL10A106MA8NRNC | C96446 | 5.1M | $0.055 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 10µF 25V X5R, post-filter |
| FB2–FB4 | BLM21PG601SN1D | C41556732 | 7,165 | $0.060 | 0805 | Extended | Device:FerriteBead | Inductor_SMD:L_0805_2012Metric | 600Ω@100MHz — matches skeleton note exactly |
| TP7, TP8 | generic test point | — | — | — | pad | — | Connector:TestPoint | TestPoint:TestPoint_Pad_D1.5mm | |

## analog_front_end (per channel ×2; channel A refs, B = +10)

| Ref (A/B) | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| J2 / J3 | BNC-KWE-6 | C20415789 | 615 | $2.747 | THT elbow | Extended | Connector:Conn_Coaxial | ProjectLocal:BNC_cntitle_BNC-KWE-6_Horizontal | generic right-angle BNC footprint (SUB per skeleton: any PCB BNC); stock 615 is above the 500 WARN line but worth watching | **[Coding: footprint replaced — Amphenol 031-6575 is a dual BNC; custom single-jack footprint generated from maker drawing]**
| R10, R11 / R20, R21 | FRC1206F4533TS | C2999488 | 6,270 | $0.005 | 1206 | Extended | Device:R | Resistor_SMD:R_1206_3216Metric | 453kΩ 1% 200V — **PKG** fixed; only 6 JLC listings meet 1%/200V/1206, all Extended |
| R12 / R22 | RT0603BRD07100KL | C122538 | 1.28M | $0.032 | 0603 | Extended | Device:R | Resistor_SMD:R_0603_1608Metric | 100kΩ 0.1% 25ppm |
| R13 / R23 | 0603WAF1001T5E | C21190 | 27.0M | $0.003 | 0603 | Basic | Device:R | Resistor_SMD:R_0603_1608Metric | 1kΩ 1% |
| R14, R15 / R24, R25 | PTFR0603B1K10P9 | C351674 | 54,698 | $0.065 | 0603 | Extended | Device:R | Resistor_SMD:R_0603_1608Metric | Rg 1.10kΩ 0.1% 25ppm, matched pair |
| R16, R17 / R26, R27 | FRH0603B1001TS | C49196685 | 565,595 | $0.010 | 0603 | Extended | Device:R | Resistor_SMD:R_0603_1608Metric | Rf 1.00kΩ 0.1%, matched pair |
| R18, R19 / R28, R29 | 0402WGF499JTCE | C25120 | 1.8M | $0.003 | 0402 | Basic/Preferred | Device:R | Resistor_SMD:R_0402_1005Metric | 49.9Ω 1% |
| C30 / C40 | GCM1885C2A150JA16D | C388905 | 10,907 | $0.036 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | 15pF C0G 100V |
| VC1 / VC2 | STC3MA06-T1 | C22468120 | 4,760 | $0.494 | SMD 4.5×3.2mm | Extended | Device:C_Trim | ProjectLocal:C_Trimmer_SEHWA_STC3M | 2–6pF, 100V — footprint is a generic trimmer body; verify pad pattern against SEHWA mechanical drawing (4.5×3.2mm) before layout | **[Coding: custom footprint from SEHWA land pattern, p.3]**
| C31 / C41 | GRM1885C1H161JA01D | C710893 | 7,762 | $0.040 | 0603 | Extended | Device:C | Capacitor_SMD:C_0603_1608Metric | 160pF C0G 50V 5% |
| C32, C33 / C42, C43 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF ×4 |
| C34, C35 / C44, C45 | GRM1555C2A220JA01D | C710855 | 1,877 | $0.031 | 0402 | Extended | Device:C | Capacitor_SMD:C_0402_1005Metric | Cf 22pF C0G 100V ×4 — only 1 JLC listing meets 22pF/100V/C0G/0402; stock 1,877 clears WARN but watch it |
| C36 / C46 | GRM1555C1H221JA01D | C71693 | 1.15M | $0.005 | 0402 | Extended | Device:C | Capacitor_SMD:C_0402_1005Metric | Cdiff 220pF C0G 50V — note this is a different value from the C34/C35/C44/C45 Cf caps (22pF, different LCSC#) despite similar part numbers; don't conflate them |
| C37, C38 / C47, C48 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF ×4 |
| D2 / D3 | BAV199 | C5184419 (HXY) | 103,861 | $0.014 | SOT-23 | Extended | ⚠️ SYMBOL NEEDED | Package_TO_SOT_SMD:SOT-23 | **architecture flagged this explicitly:** the auto-matched `Diode:BAV19` is a single diode, wrong. `Diode:BAV99` (common-cathode dual) also does **not** match — BAV199 is a series-connected pair, different topology. Needs a generated symbol; pin table on the BAV199 datasheet (Nexperia/onsemi), p.1–2 |
| U8 / U10 | OPA354AIDBVR | C36384 | 847 | $1.781 | SOT-23-5 | Extended | ⚠️ SYMBOL NEEDED | Package_TO_SOT_SMD:SOT-23-5 | stock down from 3,147 (architecture snapshot) to 847 — still clears the >500 WARN line. `Amplifier_Operational:OPA356xxDBV` is SOT-23-5 same-family pinout but not confirmed identical; do not substitute without checking TI's SOT-23-5 5-pin op-amp pinout convention in the datasheet phase |
| U9 / U11 | THS4521IDGKR | C170157 | 4,386 | $1.396 | VSSOP-8 (listed MSOP-8) | Extended | Amplifier_Difference:THS4521IDGK | Package_SO:VSSOP-8_3x3mm_P0.65mm | **CP**, confirmed |

## adc

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U12 | ADS5231IPAGT | C2670079 | 160 | $31.71 | TQFP-64 (10×10) | Extended | ⚠️ SYMBOL NEEDED | Package_QFP:TQFP-64_10x10mm_P0.5mm | **CP, single-source, WARN stock (<500).** Buy full 10-board qty now per architecture instruction #6 |
| R50 | FRC0603F5622TS | C2930117 | 199,980 | $0.003 | 0603 | Extended | Device:R | Resistor_SMD:R_0603_1608Metric | ISET 56.2kΩ 1% |
| R51, R52 | FRC0402F2R00TS | C2998051 | 399,200 | $0.002 | 0402 | Extended | Device:R | Resistor_SMD:R_0402_1005Metric | 2Ω 1%, REFT/REFB |
| R53–R56 | 0402WGF1002TCE | C25744 | 30.5M | $0.003 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 10kΩ 1% pull-downs ×4 |
| RN1–RN7 | 4D03WGJ0330T5E | C25508 | 153,387 | $0.020 | 0603×4 | Extended | Device:R_Network04 | Resistor_SMD:R_Array_Convex_4x0603 | isolated 4-resistor array, 33Ω ±5% |
| C50–C52, C54–C56, C58–C61 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF ×10 |
| C53 | CL05A105KA5NQNC | C52923 | 9.9M | $0.012 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1µF |
| C57, C62 | CL10A106MA8NRNC | C96446 | 5.1M | $0.055 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 10µF 25V X5R |
| FB5, FB6 | BLM21PG601SN1D | C41556732 | 7,165 | $0.060 | 0805 | Extended | Device:FerriteBead | Inductor_SMD:L_0805_2012Metric | 600Ω@100MHz |

## sample_clock

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| X1 | SX3M20.000B10F20TNN | C5452685 | 3,210 | $0.466 | SMD3225-4P | Extended | ⚠️ SYMBOL NEEDED | Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm | **CP spec** (≤5ps rms jitter — confirm on datasheet, per architecture). No EasyEDA footprint on file (`has_easyeda_footprint:false`); used a generic 3225 4-pin oscillator footprint — pad geometry is standard across vendors for this package but should be spot-checked |
| R57, R58 | 0402WGF330JTCE | C25105 | 2.2M | $0.004 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 33Ω 1% |
| C63 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF |
| C64 | CL05A105KA5NQNC | C52923 | 9.9M | $0.012 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 1µF |
| FB7 | BLM21PG601SN1D | C41556732 | 7,165 | $0.060 | 0805 | Extended | Device:FerriteBead | Inductor_SMD:L_0805_2012Metric | 600Ω@100MHz |
| TP9 | generic test point | — | — | — | pad | — | Connector:TestPoint | TestPoint:TestPoint_Pad_D1.5mm | |

## usb_bridge

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U13 | FT232HL-REEL | C51997 | 2,474 | $9.702 | LQFP-48 (7×7) | Extended | Interface_USB:FT232H | Package_QFP:LQFP-48_7x7mm_P0.5mm | **CP**, confirmed |
| U14 | 93LC56BT-I/OT | C190271 | 13,008 | $0.489 | SOT-23-6 | Extended | Memory_EEPROM:93LCxxB | Package_TO_SOT_SMD:SOT-23-6 | WILDCARD family symbol — pinout identical across the 93LCxxB family |
| Y1 | X322512MSB4SI | C9002 | 110,251 | $0.095 | SMD3225-4P | Basic | Device:Crystal | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | 12MHz, CL=20pF — **sets C65/C66 to 20pF per skeleton note** (was TBD pending Y1 selection) |
| C65, C66 | GRM1555C2A220JA01D | C710855 | 1,877 | $0.031 | 0402 | Extended | Device:C | Capacitor_SMD:C_0402_1005Metric | 22pF C0G 100V — nearest standard value to Y1's 20pF load spec (2pF off, negligible); same part as C34/C35/C44/C45 |
| C67–C74 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF ×8, per DS_FT232H §6 |
| C75, C76 | CL10A475KO8NNNC | C19666 | 3.7M | $0.033 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 4.7µF ×2, per DS_FT232H §6 (skeleton's "0402/0603" note resolved to 0603 for the 4.7µF pair) |
| C77 | CL10A475KO8NNNC | C19666 | 3.7M | $0.033 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 4.7µF VPHY/VPLL bulk |
| C78, C79 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF ×2 |
| FB8 | BLM21PG601SN1D | C41556732 | 7,165 | $0.060 | 0805 | Extended | Device:FerriteBead | Inductor_SMD:L_0805_2012Metric | 600Ω@100MHz |
| R60 | 0402WGF2201TCE | C25879 | 1.4M | $0.004 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 2.2kΩ 1% |
| R61–R63, R65, R67 | 0402WGF1002TCE | C25744 | 30.5M | $0.003 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 10kΩ 1% ×5 |
| R64 | 0402WGF1202TCE | C25752 | 742,335 | $0.004 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 12kΩ 1% REF |
| R66 | 0402WGF330JTCE | C25105 | 2.2M | $0.004 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 33Ω 1% |

## fpga_core

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U15 | GW1NR-LV9QN88PC6/I5 | C5799578 | 182 | $23.27 | QFN-88 (10×10) | Extended | ⚠️ SYMBOL NEEDED | ⚠️ **CUSTOM FP NEEDED (verify first)** — best candidate `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` | **CP, single-source, WARN stock (<500).** The only QFN-88/10×10/0.4mm footprint in the KiCad lib is a 3rd-party (ArtInChip) part; its exposed-pad size (6.74×6.74mm) is **not confirmed** against Gowin UG803's QN88P mechanical drawing. Datasheet-librarian must check EP dimensions before this is trusted for layout — flag as CUSTOM until verified. Buy full 10-board qty now (architecture instruction #6) |
| J4 | generic 1×7 2.54mm header | C492406 | 57,462 | $0.045 | THT | Extended | Connector_Generic:Conn_01x07 | Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical | JTAG header; VREF = VD_1V8 per architecture |
| R70, R71 | 0402WGF1001TCE | C11702 | 12.3M | $0.004 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 1kΩ 1% — MODE0/1 pull-down (UG290 recommends 1 k; changed from 4.7 k in design review) |
| R73, R75 | 0402WGF4701TCE | C25900 | 18.6M | $0.003 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 4.7kΩ 1% — TCK pull-down, DONE pull-up (UG290; R75 added in design review) |
| R72, R74 | 0402WGF1002TCE | C25744 | 30.5M | $0.003 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 10kΩ 1% — RECONFIG_N, JTAGSEL_N |
| C80–C83, C85–C87, C89, C91, C92, C94 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF ×11 |
| C84, C88 | CL10A106MA8NRNC | C96446 | 5.1M | $0.055 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 10µF 25V X5R ×2 |
| C90, C93, C95 | CL10A475KO8NNNC | C19666 | 3.7M | $0.033 | 0603 | Basic | Device:C | Capacitor_SMD:C_0603_1608Metric | 4.7µF ×3 |
| TP10 | generic test point | — | — | — | pad | — | Connector:TestPoint | TestPoint:TestPoint_Pad_D1.5mm | |

## io_expansion

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U16 | SN74LV4T125PWR | C90755 | 7,661 | $0.785 | TSSOP-14 | Extended | 74xx:SN74LV4T125 | Package_SO:TSSOP-14_4.4x5mm_P0.65mm | confirmed |
| U17 | SN74LV1T34DCKR | C78541 | 103,515 | $0.117 | SC-70-5 | Extended | Logic_LevelTranslator:SN74LV1T34DCK | Package_TO_SOT_SMD:SOT-353_SC-70-5 | confirmed |
| LED2, LED3 | CT-1608UGC-P4 | C52675989 | 237,305 | $0.003 | 0603 | Extended | Device:LED | LED_SMD:LED_0603_1608Metric | status LEDs |
| R80, R81 | 0402WGF1001TCE | C11702 | 12.3M | $0.004 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 1kΩ 1% |
| R82, R83 | 0402WGF1000TCE | C25076 | 3.6M | $0.004 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 100Ω 1% |
| R84 | 0402WGF1001TCE | C11702 | 12.3M | $0.004 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 1kΩ 1% |
| R85 | 0402WGF1003TCE | C25741 | 12.1M | $0.003 | 0402 | Basic | Device:R | Resistor_SMD:R_0402_1005Metric | 100kΩ 1% |
| C96, C97 | CL05B104KB54PNC | C307331 | 19.9M | $0.009 | 0402 | Basic | Device:C | Capacitor_SMD:C_0402_1005Metric | 0.1µF ×2 |
| J5 | generic 1×6 2.54mm header | C37208 | 322,421 | $0.042 | THT | Extended | Connector_Generic:Conn_01x06 | Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical | ext trigger/GPIO header |

## Cost estimate (qty 10, parts only)

ADC $31.71 (1×). FPGA $23.27 (1×). FT232H $9.70 (1×). Front-end ICs per board: OPA354 $1.78×2 +
THS4521 $1.40×2 ≈ $6.35. BNC $2.75×2 = $5.49. Power-tree ICs: U3 $0.33 + U4 $0.23 + U5 $0.21 +
U6 $0.22 + U7 $1.01 ≈ $2.00. Other ICs (U1, U2, U14, U16, U17) ≈ $1.53. Passives, connectors,
and headers ≈ $9 (revised up from the architecture's $8 estimate — several precision passives
came back Extended-only at higher unit prices). **≈ $91/board**, still under the $120 target
(Q3 of `SPEC.md`). Extended-tier part count: **≈ 27 unique Extended MPNs** (up from the
architect's ~25 estimate — the U3 genuine-TI swap and the FB1/J4/J5/TP-family substitutions
added a few), ≈ $8/board loading fee at qty 10.
