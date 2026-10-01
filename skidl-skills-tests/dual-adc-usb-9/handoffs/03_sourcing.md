---
phase: 03_sourcing
agent: part-sourcer
circuit: dual_adc_usb
written: 2026-09-30T23:59:30Z
status: complete
revision: 3
next_phase: 04_datasheets
---

# Phase 3 handoff - Sourcing (rev 3: J2/J3 footprint resolved; rev 2 content otherwise unchanged)

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `sourcing/sourced_bom.md` | 59 rows / 169 refdes, MPN, LCSC, stock, footprint | Always |
| `sourcing/sourced_bom.csv` | Same, machine-readable for validate-bom.py | Coding gate |

Notes: refdes counts: 163 (rev 1) + U12, L3, C9, C93, C17, R15, R14 - R82 = 169, no duplicates, matches architecture rev 2 Parts by block. validate-bom.py not run (no circuit code yet; the coding gate runs it first). Stock from pcbparts MCP (jlc_search/get_part) on 2026-09-30. Rows not tagged in `Chg` are verbatim from rev 1.

## Decisions
- **Y1 -> OT322540MJBA4SL** (YXC, C2831396, Extended, stock 10567, 0.55 USD @1). Replaces SX3M40 (stock 2390, jitter unpublished). Footprint kept as `Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm` (resolves; same 3225 4-pad; confirm pad fit at layout). Symbol `Oscillator:ASE-xxxMHz`, EN = pin 1, tie high.
- **C110/C111 -> 0402CG330J500NT** (FH, C1562, 33 pF C0G 50 V +/-5 %, **Basic**, stock 1.32 M). Rejected Murata GJM1555C1H330FB01D (+/-1 %, 0.047 USD, Extended) as unnecessary.
- **R14 -> 0402WGF2003TCE** (Uniroyal, C25764, 200 k 1 %, **Basic**, stock 2.3 M). Pairs with R15 (100 k, existing row) for 1.800 V.
- Refs appended with no search: U12 to TLV62569DBVR row; L3 to FHD4020S-2R2MT row; C9, C93 to CL10A106KP8NNNC 10 uF 0603 row; C17 to CL21A226MAQNNNE 22 uF row; R15 to 100 k row.
- R82 removed; 4.7 k row is now R80, R81, R85 (R80/R85 to +1V8, R81 TCK pull-down).
- **Symbols (librarian corrections):** U2 `dual_adc_usb:TPS22918DBVR`, U7 `dual_adc_usb:ADS5231IPAGT`, U9 `dual_adc_usb:GW1NR-LV9QN88PC6` (all in `symbols/dual_adc_usb.kicad_sym`, replacing `my_board:` placeholders); U11 `Memory_EEPROM:93LCxxBxxOT` (exists in KiCad stock lib). The `SYMBOL NEEDED` flags are cleared.
- Kept despite concern: U7 (stock 235) and U9 (182) unchanged, single source; U1/U5 etc. untouched.
- Net-only changes (C91, R80, R81, R85, J4) need no BOM edit.
- Footprint check: Y1, 0402 C and R footprint strings confirmed present in the KiCad footprint library by `ls`; validate-footprints.py not used (timed out on a path search).

- **J2/J3 footprint (rev 3):** TRIED option 1: no in-stock JLCPCB BNC matched a KiCad Connector_Coaxial footprint (those are 4-leg TE/Amphenol/Win parts with different pad patterns; only TE 5227161-7 C591726, 455 stock, 6.28 USD, is TE and still not a verified match). Kept KH-BNC50-3511 (C2837587, stock 5724, Extended) with custom footprint. **Footprint string the AFE code must use: `ProjectLocal:KH-BNC50-3511`**; symbol `Connector:Conn_Coaxial` (pin 1 centre, pin 2 shell; pad 2 appears 3x: shell lead + 2 posts).

## Next phase must
Delta only: `datasheets/OT322540MJBA4SL_SUMMARY.md` (PDF already in `datasheets/`; jitter p.1, pinout p.2). Everything else (U12 = same MPN as U3/U4, passives) is skippable. Symbols for U2/U7/U9 already exist; confirm U11's `Memory_EEPROM:93LCxxBxxOT` pin names against the SOT-23-6 datasheet table.

## Carried forward
- J2/J3 custom footprint now created (rev 3): `ProjectLocal:KH-BNC50-3511` in `footprints/ProjectLocal.pretty/KH-BNC50-3511.kicad_mod`. Pad geometry (pin 2 offset -2.5, posts at y=+5.05) is read from a non-scaled drawing; verify against the part/DOSIN-801-0038 before fab. Project needs a `ProjectLocal` fp-lib entry pointing at `footprints/ProjectLocal.pretty`.
- Verify land pattern (unchanged): U9 EP 6.74 mm (UG119 p.31 matches), C21/C41 trimmer, L1-L3 (FNR4020S vs FHD4020S), Y1 (Abracon ASE footprint for YXC 3225).
- Single-source marginal stock: U7 (235), U9 (182). Y1 now has a second source: TAITIEN OXETGLJANF-40.000000MHZ (C7470494) per architect.
- Extended tier: 31 rows (all ICs, odd-value passives, Y1) -> setup fee per unique Extended part. Rev 2 added no new Extended row beyond the Y1 swap; R14 and C110/C111 are Basic.
- C3 is 10 uF 0603 (not the skeleton's 0805) from rev 1; DC-bias derate check at coding still open.

## Parts by block
| block_id | refs | MPNs |
|---|---|---|
| `usb_power_in` | J1, U1, U2, F1, D1, R1, R2, R3, C1, C2, C3 | TYPE-C-31-M-12, USBLC6-2SC6, TPS22918DBVR, SMD1206P075TF, SMF5.0A |
| `pwr_digital` | U3, U4, U12, L1, L2, L3, R5, R6, R7, R8, R9, R14, R15, C4, C5, C6, C7, C8, C9, C17 | TLV62569DBVR, FHD4020S-2R2MT, 0402WGF2003TCE |
| `pwr_analog` | U5, U6, R10, R11, R12, R13, C10, C11, C12, C13, C14, C15, C16 | TLV75733PDBVR, LM27762DSSR |
| `afe_ch_a` | J2, U20, U21, D20, R20-R30, C20-C31 | KH-BNC50-3511, OPA810IDBVR, THS4521IDGKR, BAV199, STC3MA06-T1 |
| `afe_ch_b` | J3, U40, U41, D40, R40-R50, C40-C51 | same as ch A |
| `adc_dual` | U7, R60, R61, R62, C60-C73 | ADS5231IPAGT |
| `clock_gen` | Y1, U8, R70, R71, C75, C76 | OT322540MJBA4SL, SN74LVC1G34DCKR |
| `fpga` | U9, R80, R81, R83-R89, D80, D81, J4, J5, C80-C93 | GW1NR-LV9QN88PC6/I5, KT-0603G, PZ254V-11-06P, PZ254V-11-03P |
| `usb_bridge` | U10, U11, Y2, R100-R103, C100-C111 | FT232HL-REEL, 93LC56BT-I/OT, X322512MSB4SI, 0402CG330J500NT |

## Do not redo
Use `sourcing/sourced_bom.csv` rows verbatim (MPN, LCSC, value, footprint, symbol). Rev 1 sourcing decisions and architect IC decisions unchanged.

## Receipt
dual_adc_usb sourcing rev 3: status complete. 169 refdes / 59 rows, 0 failures.
- Re-sourced: Y1 OT322540MJBA4SL (C2831396, 10567, Extended), C110/C111 33 pF C0G (C1562, Basic), R14 200 k (C25764, Basic).
- Appended U12, L3, C9, C93, C17, R15; removed R82.
- Symbols fixed: U2/U7/U9 -> dual_adc_usb lib, U11 -> Memory_EEPROM:93LCxxBxxOT.
- Tiers: 26 Basic, 2 Preferred, 31 Extended. Remaining flags: none for J2/J3 beyond FP verification; U7/U9 single-source marginal stock.
- validate-bom.py not run (no circuit code yet).
