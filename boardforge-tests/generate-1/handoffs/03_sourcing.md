---
phase: 03_sourcing
agent: part-sourcer
circuit: dual_adc_10msps
written: 2026-10-17
status: complete
revision: 2
next_phase: 05_coding
---

# Phase 3 handoff - Sourcing (revision 2)

Revision 2 closes the symbol/footprint gaps using the datasheet-librarian's phase 4 output. Every part is sourced and in stock (no sourcing_failures.md). No sourcing gaps remain.

## Decisions
1. All architect-recommended ICs kept (ADS5231, XC6SLX9, W9812G6KH-6, FT232HL, OPA2810/OPA810, THS4551, W25Q32, 93LC56B, power ICs). No substitution against `## Do not redo`.
2. FT232HL: LCSC part is FT232HL-REEL (same die/package, tape and reel). SN74LVC2G34DBVR: TI original not at JLC; UMW clone C7394039 (47.9k stk), MPN field kept as TI MPN. USBLC6-2SC6: ST original C7519.
3. Ferrites: architect default GZ1608D601TF rejected (200 mA, 450 mohm) -> BLM18KG601SN1D (600R, 1.3 A, 150 mohm, FB701 budget OK).
4. Inductor L601: TDK TMS252012ALM-2R2MTAA (2.2 uH, Isat 2.8 A, 75 mohm, 1008) instead of 4x4 mm; only 1129 stk (marginal, kept). PTC F501: 1812 JK-mSMD075-33 (hold 0.75 A, R max 0.45 ohm) - no 1206 0.75 A part in stock; VBUS drop at 0.43 A worst case = 0.19 V, acceptable.
5. Crystal Y901: 12 MHz CL=12 pF 2520 (TXM12M0004252FBCEO00T) so C901/C902 = 18 pF; 2520 not 3225 (3225 stock was CL 20 pF).
6. C0G tolerance: C106/C206 1.8 nF and C112/C212 1.2 nF are +/-1% (no 2% in stock; C112 732 stk, marginal); C110/C111 82 pF use 0603 - coder uses 0603 for all 82 pF. C101/C201 8.2 pF is 250 V Murata GQM.
7. R-values: exact E96 parts used for all (thick-film +/-1%).
8. BAV199 symbol: no KiCad BAV199; Diode:BAV99 (identical series-pair pinout, pin 3 common) used.
9. LEDs: green 0603 Vf 3.1 V - at 3.3 V with 1 k ~0.2 mA (dim). Kept; coder may drop to 330R-470R.
10. Stock source: pcbparts live data; stock-check.py mirror is stale for ICs.
11. Rev 2 symbol changes (from librarian, `handoffs/04_datasheets.md`): U902 -> `Memory_EEPROM:93LCxxBxxOT` (SOT-23-6 pinout; the SOIC `93LCxxB` symbol was wrong); U301 -> `dual_adc_10msps:ADS5231IPAGT`; U101/U201 -> `dual_adc_10msps:OPA2810IDR` (in `symbols/dual_adc_10msps.kicad_sym`; supersede the `my_board:` names).
12. Rev 2 footprints: J101/J201 `my_board:BNC_KH-BNC50-3511` and C102/C202 `my_board:C_Trimmer_SEHWA_STC3MA06` now exist in `footprints/my_board.pretty` (strings unchanged; CUSTOM FP flags cleared).
13. Kept despite librarian note: U1001 symbol stays `FPGA_Xilinx_Spartan6:XC6SLX4-TQG144` (librarian verified it matches all 144 pins of the LX9 per UG385; the exact `XC6SLX9-TQG144` symbol is an optional swap, not made, to avoid churn).

## Artifacts
| File | Contains |
|---|---|
| `sourcing/sourced_bom.md` | 238 refs, one row each |
| `sourcing/sourced_bom.csv` | 73 logical rows, machine-checked twin (symbols/footprints identical to the md) |

## Parts by block
| block_id | refs | MPNs |
|---|---|---|
| `usb_c_input` | J501, U501, D501, F501, R501, R502, C501 | TYPE-C-31-M-12, USBLC6-2SC6, SMF5.0A, JK-mSMD075-33 |
| `power_digital` | U601, U602, L601, C601-C606, R601, R602, R604, D601 | TLV62569DBVR, TLV75712PDBVR, TMS252012ALM-2R2MTAA |
| `power_analog` | U701, U702, FB701, C702, C703, C705-C709, R701-R704 | LP5907MFX-3.3/NOPB, LM27762DSSR, BLM18KG601SN1D |
| `afe_channel` | A: J101, U101-U103, D101, R101-R115, C101-C121; B: J201, U201-U203, D201, R201-R215, C201-C221 | KH-BNC50-3511, OPA2810IDR, OPA810IDBVR, THS4551IRGTR, BAV199, STC3MA06-T1 |
| `adc` | U301, FB301, R301-R307, RN301-RN306, C301-C313 | ADS5231IPAGT, BLM18KG601SN1D, 4D02WGJ0330TCE |
| `clock` | Y401, U401, FB401, R401, R402, C401-C403 | SX3M10.000B10F20TNN, SN74LVC2G34DBVR |
| `sdram` | U801, R801-R803, C801-C808 | W9812G6KH-6 |
| `usb_fifo` | U901, U902, Y901, FB901, R901-R912, C901-C913 | FT232HL, 93LC56BT-I/OT, TXM12M0004252FBCEO00T |
| `fpga` | U1001, U1002, J1001, J1002, D1002, D1003, R1001-R1006, R1008-R1010, R1012-R1016, C1001-C1025 | XC6SLX9-2TQG144C, W25Q32JVSSIQ, PZ254V-11-06P, PZ254V-11-03P, PSC-1608U52GC-G4 |

FPGA caps: the U1001 symbol has 21 supply pins -> C1001-C1021 (0.1 uF one per pin), C1022 (0.1 uF at U1002), C1023-C1025 (4.7 uF bulk). If the coder's pin count differs, update CSV rows C1001..C1022 and C1023..C1025 together.

## Next phase must
Phase 4 is already done (see `handoffs/04_datasheets.md`, status partial: W9812G6KH-6 datasheet and SX3M jitter remain open there, not sourcing issues). Coders proceed to 05_coding using the CSV strings verbatim.

## Carried forward
- No `SYMBOL NEEDED` or `CUSTOM FP NEEDED` items remain.
- Single-sourced: U301 ADS5231 (152 stk, WARN), THS4551, OPA2810/OPA810 (fixed by design).
- Marginal stock (<2000): U301 152, C112/C212 732, L601 1129, U801 1241, U103/U203 1357, U1001 1678, Y401 1999.
- Extended-tier: 50 of 73 logical rows -> ~50 x $3 setup fee; SOFT cost budget (~$30/board at qty 5 vs $18) at risk; no Basic alternatives for odd E96 values.
- Footprint caveats for coders/layout: THS4551 EP size (1.68 mm assumed), LM27762 EP, W9812 TSOP-II name, USB-C HRO footprint.
- Symbol caveat: U901 uses Interface_USB:FT232H (PREFIX match, confirm pinout).
- BOM gate: no circuit code yet, so `boardforge review` BOM check not run; the coding gate is first.

## Do not redo
Use MPNs, LCSC numbers, values, package names, footprint and symbol strings in `sourcing/sourced_bom.csv` verbatim.

## Receipt
Rev 2: updated sourced_bom.csv and .md. U902 -> Memory_EEPROM:93LCxxBxxOT; U301 -> dual_adc_10msps:ADS5231IPAGT; U101/U201 -> dual_adc_10msps:OPA2810IDR.
J101/J201 and C102/C202 footprint strings already matched the new my_board.pretty files; CUSTOM FP flags cleared.
Split unchanged: 138 Basic, 2 Preferred, 98 Extended refs; failures none. BOM gate: not run (no code yet).
status: complete.
