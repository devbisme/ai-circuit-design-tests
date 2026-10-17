---
phase: 04_datasheets
agent: datasheet-librarian
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: partial
revision: 1
next_phase: 05_coding
---

# Phase 4 handoff - Datasheets

status is `partial` only because of 2 keystone gaps (W9812G6KH-6 datasheet, SX3M jitter); everything else is verified.

## Decisions
1. All 11 architecture "unverified facts" are now VERIFIED from primary documents (table in Next phase must #1).
2. **93LC56BT-I/OT symbol is wrong in the BOM**: `Memory_EEPROM:93LCxxB` is the SOIC/DIP pinout (1 CS,2 CLK,3 DI,4 DO,5 GND,8 VCC). The OT (SOT-23-6) part is 1 DO,2 VSS,3 DI,4 CLK,5 CS,6 VCC (Microchip DS p2). Use `Memory_EEPROM:93LCxxBxxOT` (pins match). part-sourcer must update the CSV cell.
3. FPGA symbol: `FPGA_Xilinx_Spartan6:XC6SLX9-TQG144` exists and matches UG385 Table 2-2 on all 144 pins (so does the LX4 symbol in the BOM). Either is correct; recommend the exact LX9 symbol (sourcer to update cell if adopted).
4. New symbols (lib `dual_adc_10msps`, file `symbols/dual_adc_10msps.kicad_sym`): `ADS5231IPAGT` (64 pins, no EP - PAG has no pad), `OPA2810IDR` (units A, B, power). The BOM's `my_board:ADS5231IPAGT`/`my_board:OPA2810IDR` names are superseded; sourcer to write `dual_adc_10msps:ADS5231IPAGT` / `dual_adc_10msps:OPA2810IDR` into the CSV.
5. New footprints `footprints/my_board.pretty/`: `BNC_KH-BNC50-3511`, `C_Trimmer_SEHWA_STC3MA06` (names match BOM cells verbatim; validate-footprints OK).
6. `datasheets/W9812G6KH-6.pdf` is actually the **W9812G6JH** document (the add tool's name check fuzzy-matched; the guard blocks deleting it). KH PDF not obtainable (LCSC download failed, Winbond page 404, web search no PDF). Extraction is built from the JH doc with confidence `low`.
7. LED PSC-1608U52GC-G4 skipped (indicator; Vf 3.1 V from BOM only). Passives/connectors skipped per scope.
8. Footprint caveats closed: THS4551 RGT EP 1.68x1.68 (pad 17) verified (pkg drawing RGT0016C); LM27762 DSS EP 1.0x2.65 (pad 13) verified (DSS0012); W9812 TSOP-II-54 0.8 mm standard.
9. Page numbers in 5 summaries (OPA2810, OPA810, THS4551, LM27762, LP5907) were generated before an evidence-page fix and point at the TOC (p2); the extraction JSONs are authoritative. Guard blocks regeneration; values are identical.

## Artifacts
| File | Contains | Read it when |
|---|---|---|
| `datasheets/extracted/*.json` (18) | Validated extractions (all `check` OK) | Gates read these |
| `datasheets/<MPN>_SUMMARY.md` (19) | Coder-facing tables + pinouts | Before coding each block |
| `datasheets/ref/ug385.pdf`, `ds162.pdf` | Spartan-6 packaging/pinout (Table 2-2 p30-34) and DC specs | FPGA pin planning |
| `datasheets/mech/KH-BNC50-3511.pdf`, `STC3MA06-T1.pdf` | Mechanical drawings | Layout |
| `symbols/dual_adc_10msps.kicad_sym` | ADS5231IPAGT, OPA2810IDR | Coding |
| `footprints/my_board.pretty/*.kicad_mod` | BNC, trimmer | Coding/layout |

## Summaries by block
| block_id | summary files |
|---|---|
| `usb_c_input` | `datasheets/USBLC6-2SC6_SUMMARY.md`, `datasheets/SMF5_0A_SUMMARY.md` |
| `power_digital` | `datasheets/TLV62569DBVR_SUMMARY.md`, `datasheets/TLV75712PDBVR_SUMMARY.md` |
| `power_analog` | `datasheets/LP5907MFX-3_3_NOPB_SUMMARY.md`, `datasheets/LM27762DSSR_SUMMARY.md` |
| `afe_channel` | `datasheets/OPA2810IDR_SUMMARY.md`, `datasheets/OPA810IDBVR_SUMMARY.md`, `datasheets/THS4551IRGTR_SUMMARY.md`, `datasheets/BAV199_SUMMARY.md` |
| `adc` | `datasheets/ADS5231IPAGT_SUMMARY.md` |
| `clock` | `datasheets/SX3M10_000B10F20TNN_SUMMARY.md`, `datasheets/SN74LVC2G34DBVR_SUMMARY.md` |
| `sdram` | `datasheets/W9812G6KH-6_SUMMARY.md` |
| `usb_fifo` | `datasheets/FT232HL_SUMMARY.md`, `datasheets/93LC56BT-I_OT_SUMMARY.md`, `datasheets/TXM12M0004252FBCEO00T_SUMMARY.md` |
| `fpga` | `datasheets/XC6SLX9-2TQG144C_SUMMARY.md`, `datasheets/W25Q32JVSSIQ_SUMMARY.md` |

## Unverified keystone facts
| Part | Fact | Best available answer | What would close it |
|---|---|---|---|
| `W9812G6KH-6` | Pinout, VDD/VDDQ 3.0-3.6 V, abs max 4.6 V | Same as W9812G6JH doc (JEDEC TSOP-54 x16; KiCad W9812G6KH-6 symbol agrees) | Winbond W9812G6KH datasheet |
| `SX3M10.000B10F20TNN` | RMS jitter <= 5 ps (architecture requirement) | Not specified in SCTF datasheet at all | Ask SCTF, or pick an XO with a jitter spec |
| `TXM12M0004252FBCEO00T` | CL 12 pF, pinout 1/3 xtal, 2/4 GND | MCP data + 2520 convention | Yajingxin datasheet (ordinary part) |

## Next phase must
1. **Verified architecture facts** (all from the exact-part PDF):
   | Fact | Value | Source |
   |---|---|---|
   | LX4/LX9 TQG144 pinout identical | one shared table | UG385 Table 2-2 p30, symbols compared 144/144 |
   | HSWAPEN P144 | Low = pull-ups ON during config; tie high (VCCO_0) for pull-ups off | UG385 Table 1-6 p20 |
   | M1 P60 / M0 P69 | M1 = 0 master, M0 = 1 serial -> SPI master: M1 pull-down, M0 pull-up; both dual-purpose IO | UG385 p20 |
   | SUSPEND P73 | GND when suspend unused | UG385 p21 |
   | CMPCS_B_2 P72 | leave unconnected or tie to VCCO_2 | UG385 p22 |
   | VFS/VBATT/RFUSE | not present on LX9 | UG385 Table 1-2 |
   | OPA2810 SOIC-8 | 1 VO1,2 VIN1-,3 VIN1+,4 VS-,5 VIN2+,6 VIN2-,7 VO2,8 VS+ | SBOS789C p3 |
   | OPA2810/OPA810 GBW | 70 MHz (gbw = 7e7 Hz in both extractions) | p5 EC table |
   | BAV199 | pin1 = anode D1, pin3 = common (K1/A2), pin2 = cathode D2 | JSCJ DS p1 figure |
   | FT232H 3.3 V-only | VREGIN=3V3, VCCD input tied to 3V3; VCORE/VCCA 0.1 uF only | FT_000288 Fig 6.3 p44 |
   | EEPROM network | EEDATA->DI direct, ->DO via 2.2k; DO 10k to VCCD; must be 16-bit 93LC56B (93LC46B unsupported) | p11, p63 |
   | ACBUS7 = PWRSAV# | default GPIO w/ 75k pull-down; if EEPROM "suspend on ACBUS7 low" is set it must be driven high (39k from VBUS) or chip stays suspended - leave option off for bus power | p9-10, p44 |
   | LP5907 Cout | 0.7-10 uF effective, ESR 5-500 mohm | SNVS798 EC table |
   | ADS5231 PLL disable | SEL=1, low pulse on SEL after supplies (reg reset), then write addr 0011 data xx1x -> word 0x32 (D1=1 PLL off) | SBAS295A p9, p21 |
   | ADS5231 power-up | AVDD and VDRV ramp 10-50 ms, within +/-10 ms of each other (|AVDD-VDRV| <= 0.3 V abs max); SEL pulse >10 ms after; clock start t8 > 100 ms | p10, p2 |
   | TLV62569DBV pins | 1 EN, 2 GND, 3 SW, 4 VIN, 5 FB; VFB 0.6 V +/-2 % | SLVSDT3 p3, EC |
2. **skidl coders - pin names to use (KiCad symbol names, not datasheet names, where they differ):**
   - ADS5231 (`dual_adc_10msps:ADS5231IPAGT`): AVDD, VDRV, AGND, GND, INA+, INA-, INB+, INB-, CM, REFT, REFB, ISET, INT/EXT, CLK, SEL, MSBI/SEN, OEA/SCLK, STPD/SDATA, OEB, D0_A..D11_A, D0_B..D11_B, OVRA, OVRB, DVA, DVB. ISET 56.2k to AGND; REFT/REFB each 2 ohm + 0.1 uF to AGND; INT/EXT high = internal ref; 0.1 uF per AVDD/VDRV pin + 2.2-10 uF bulk (p23). At 10 MSPS PLL MUST be disabled (PLL-on minimum 20 MSPS; PLL-off 2-30 MSPS, duty 45-55 %). Output load < 15 pF; pipeline 6 clocks.
   - OPA2810 (`dual_adc_10msps:OPA2810IDR`): VIN1+, VIN1-, VO1, VIN2+, VIN2-, VO2, VS+, VS-. Rails +/-4 V = 8 V total (OK, 4.75-27 V).
   - OPA810 (`Amplifier_Operational:OPA810xDBV`): symbol names `+`(3) `-`(4) `~`(1, out) `V+`(5) `V-`(2) - match datasheet numbering.
   - THS4551 (`THS4551xRGT`): `~{PD}` pin 12 -> tie high (VS+) for normal operation; EP pin 17 to GND plane (never float). FB+/FB- are output-side feedback pins; leaving them NC (feedback from OUT+/-) is the BOM decision - not explicitly confirmed by datasheet text read. Supply max 5.5 V, turn-on <= 1 V/us.
   - BAV99 symbol for D101/D201: connect BY PIN NUMBER (symbol names K/A/K are misleading): pin 2 -> +4V0A, pin 1 -> -4V0A, pin 3 -> signal. Cd 2 pF max, Ir 5 nA max.
   - FT232H symbol names: XCSI(1), XCSO(2), VCCCORE(38), VCCA(37), VCCD(39), VREGIN(40), ~{RESET}(34), TEST(42)->GND, REF(5) 12k 1 % -> GND, EECS/EECLK/EEDATA, ADBUS0-7 = FIFO D0-7, ACBUS0 RXF#, 1 TXE#, 2 RD#, 3 WR#, 4 SIWU#, 5 CLKOUT, 6 OE#, 7 PWRSAV#. VPHY/VPLL via LC/ferrite from 3V3.
   - 93LC56B: use `Memory_EEPROM:93LCxxBxxOT` (DO 1, GND 2, DI 3, CLK 4, CS 5, VCC 6).
   - LM27762 symbol names: C+/C- (datasheet C1+/C1-), PAD(13) -> GND. VOUT+ = 1.200 V x (1 + R701/R702) = +3.984 V; VOUT- = -1.220 V x (1 + R703/R704) = -3.977 V. CIN = COUT+/- = 2.2 uF, C1 = 1 uF, CPOUT = 4.7 uF (EC test conditions). EN+/EN- active high (<= VIN). PGOOD open drain, 0 = good, tie GND if unused.
   - TLV62569: VOUT = 0.6 x (1 + 453k/100k) = 3.318 V; L 2.2 uH; EN must not float. TLV75712P: EN no internal pull -> tie to IN; Cin >= 1 uF, Cout 1-200 uF; dropout <= 1.1 V @1 A. LP5907: EN has 1 Mohm pulldown -> tie to IN; pin 4 N/C.
   - USBLC6: I/O1 = pins 1&6, I/O2 = 3&4, VBUS 5, GND 2. SMF5.0A: pin 1 (K, band) -> VBUS.
   - SX3M XO (`Oscillator:ASE-xxxMHz`): 1 EN/OE (high or open = enabled), 2 GND, 3 OUT, 4 Vdd 2.97-3.63 V.
   - W25Q32 (208 mil SOIC): /WP and /HOLD/RESET need pull-ups if not driven.
3. Spartan-6 I/O budget (TQG144, all banks VCCO = 3.3 V per design; VCCO range 1.1-3.45 V): bank0 26, bank1 24, bank2 26 (includes config dual-purpose CCLK P70, DIN P65, MOSI P64, CSO_B P38, INIT_B P39, M0 P69, M1 P60), bank3 26 = 102 user I/O. Supplies: VCCINT 1.14-1.26 V x5 (P19,28,52,89,128), VCCAUX 3.15-3.45 V x5 (P20,36,53,90,129), VCCO x11, GND x13. Dedicated: PROGRAM_B P37, DONE P71, TCK P109, TDI P110, TMS P107, TDO P106.
4. BNC footprint (origin = housing centre, connector front toward -Y): pad 1 centre contact (0, 4.95) d0.9; pad 2 ground lead (-2.5, 4.95) d0.9; two shield legs pad 2 at (+/-5.05, -0.1) d2.0. Housing 14.7 x 14.3 mm; front face at y = -7.15; 21 mm barrel (dia 9.5-12.8) overhangs - place at board edge. Trimmer: pads 1.40 x 1.30 at (0, +/-1.95), body 3.2 x 4.5 x 1.5; which pad is rotor is not stated (keep rotor/adjust side on the low-impedance node if identified on the part).

## Carried forward
- W9812G6KH-6: working from the JH datasheet (see Unverified). PDF on disk is mislabelled; record, do not trust as KH.
- SX3M jitter unspecified; architecture's <= 5 ps rms clock requirement is unproven (ADS5231 itself specified with 1 ps clock; at 1 MHz input 5 ps limits SNR only to ~90 dB, so likely non-critical - architect's call).
- TXM12M crystal: no datasheet, summary UNVERIFIED (MCP only). Crystal tol+stability 40 ppm vs FTDI's +/-30 ppm figure.
- SN74LVC2G34 LCSC part is a UMW clone; pinout taken from TI datasheet (clone DS not read).
- SMF5.0A VRWM 5.0 V < VBUS max 5.25 V: leakage may exceed 400 uA at high VBUS - include in VBUS budget. Cj not specified (VBUS only, not a signal node).
- Mechanical captures: BNC drawing KH-801-0038 rev B p1 (holes 2x d2.0 @10.1 mm, 2x d0.9 @2.5 mm, row offset 5.05 mm); trimmer STC3M-SP-15 v4.1 p3 (land pattern 1.40x1.30, outer 5.10, gap 2.60).
- Sourcer CSV cells to update: U902 symbol -> 93LCxxBxxOT; U301/U101/U201 symbols -> dual_adc_10msps:*; optionally U1001 -> XC6SLX9-TQG144.

## Do not redo
- 18 extractions validated (`boardforge datasheets check` all OK); summaries on disk are final.
- Symbols generated and verified EXACT with find-symbol.py; footprints validated.
- Not published to shared cache (use_cache=false).

## Receipt
PDFs 18 (17 exact-part + W9812 from JH doc); summary-only 1 (TXM crystal); skipped 1 (LED) + passives/connectors; failed 2 (W9812G6KH, TXM12M).
Keystone parts with PDF 12/13 (W9812G6KH missing exact doc). Unverified keystone facts: 3 rows. Cache hits 0.
Symbols generated 2 (ADS5231IPAGT, OPA2810IDR); footprints 2 (BNC, trimmer). 11/11 architect facts verified.
BOM symbol error found: U902 must use 93LCxxBxxOT. status: partial.
