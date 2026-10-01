---
phase: 04_datasheets
agent: datasheet-librarian
circuit: dual_adc_usb
written: 2026-09-30T23:59:50Z
status: complete
revision: 2
next_phase: 05_coding
---

# Phase 4 handoff - Datasheets (rev 2, delta for architecture rev 2 / sourcing rev 2)

## Decisions
- Rev 2 scope (delta only): new Y1 summary, re-check of U11's symbol, and handoff tables updated for architecture rev 2. Every rev 1 summary, PDF and symbol stands as written.
- **Architecture blockers from rev 1 are resolved by architecture rev 2:**
  - VCCO3 is on the new +1V8 rail (U12 TLV62569, R14 200 k / R15 100 k → 1.800 V, within 1.71–1.89 V).
  - 48 of 48 3.3 V I/O are used: DVA/DVB/OVRA/OVRB and SIWU# are dropped.
  - Bank-3 config/JTAG pull-ups (R80, R85) and J4 VREF are on +1V8.
  - R82 is deleted. R81 is now the TCK pull-down.
  - No open item remains for the architect.
- **Y1 = OT322540MJBA4SL (YXC YSO110TR series).** From the image-only PDF, read as rendered pages:
  - Jitter is 0.7 ps max (12 k–20 MHz). K8 is closed and **verified**.
  - Pinout is 1 Tri-state, 2 GND, 3 OUTPUT, 4 VDD, the same as the KiCad `Oscillator:ASE-xxxMHz` (EN/GND/OUT/Vdd).
  - The YXC land pattern differs slightly from the Abracon ASE footprint (Y pitch 1.65 vs 1.9 mm, pad 1.1 vs 1.2 mm). It still covers the package pads, so it is acceptable (summary Notes).
- **U11 `Memory_EEPROM:93LCxxBxxOT` is confirmed** against DS20001794J Table 3-1 (SOT-23 column) and the p.2 package drawing: 1 DO, 2 GND (datasheet VSS), 3 DI, 4 CLK, 5 CS, 6 VCC. All six numbers match.
- `SX3M40.000B10F20TNN_SUMMARY.md` is marked SUPERSEDED and is no longer referenced.
- U12 is the same MPN as U3/U4, so `TLV62569DBVR_SUMMARY.md` covers it. The new passives (R14, R15, C9, C93, C17, C110/C111) are skipped because they are value-only parts. Their worklist numbers are below.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `datasheets/*_SUMMARY.md` (13 current + 1 superseded) | Specs, pinout with exact SKiDL names, load-bearing facts | Before coding each block |
| `datasheets/OT322540MJBA4SL_SUMMARY.md` | **New in rev 2**: Y1 | `clock_gen` |
| `datasheets/93LC56BT-I_OT_SUMMARY.md` | **Rev 2 section added**: KiCad symbol vs datasheet pin table | `usb_bridge` |
| `symbols/dual_adc_usb.kicad_sym` | ADS5231IPAGT (64), TPS22918DBVR (6), GW1NR-LV9QN88PC6 (88 + EP = 89) | Coding; `KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols"` |
| `datasheets/*.pdf` | 13 part PDFs + Gowin UG803 (pdf+xlsx), UG119, UG284, UG290 | Verifying a fact |

## Summaries by block
| block_id | summary files |
|---|---|
| `usb_power_in` | `datasheets/TPS22918DBVR_SUMMARY.md` |
| `pwr_digital` | `datasheets/TLV62569DBVR_SUMMARY.md` (U3, U4, U12) |
| `pwr_analog` | `datasheets/TLV75733PDBVR_SUMMARY.md`, `datasheets/LM27762DSSR_SUMMARY.md` |
| `afe_ch_a`, `afe_ch_b` | `datasheets/OPA810IDBVR_SUMMARY.md`, `datasheets/THS4521IDGKR_SUMMARY.md`, `datasheets/BAV199_SUMMARY.md` |
| `adc_dual` | `datasheets/ADS5231IPAGT_SUMMARY.md` |
| `clock_gen` | `datasheets/OT322540MJBA4SL_SUMMARY.md` |
| `fpga` | `datasheets/GW1NR-LV9QN88PC6_SUMMARY.md` |
| `usb_bridge` | `datasheets/FT232HL-REEL_SUMMARY.md`, `datasheets/93LC56BT-I_OT_SUMMARY.md`, `datasheets/X322512MSB4SI_SUMMARY.md` |

## Unverified keystone facts
**Driver disposition: accepted as named assumptions. Carry them into coding as assumptions, not facts.** None of them changes a pin, a part or a value in the netlist.

| Part | Fact | Best available answer | What would close it |
|---|---|---|---|
| `GW1NR-LV9QN88PC6` | K3 PSRAM IP sustains ≥40 MB/s | Raw device rate 2×x8 DDR @166 MHz = 664 MB/s (verified); IP efficiency unknown | IPUG943 (PSRAM HS IP) throughput table |
| `GW1NR-LV9QN88PC6` | K5 VCC (+1V2) dynamic current ≤150 mA | DS117 gives static only: 3.5 mA VCC | Gowin Power Analyzer (GPA) run on the gateware |
| `GW1NR-LV9QN88PC6` | K10 +1V8 (VCCO3 + in-package PSRAM) load ≤100 mA | Architect estimate 2×40 mA PSRAM active + ≈11 mA bank-3 drivers | GPA run |
| `GW1NR-LV9QN88PC6` | Exposed pad (symbol pin 89 `EP`) net = GND | Industry practice; UG119 says only "exposed pad" | Newer Gowin hardware design guide / UG284 revision |

## Next phase must
1. **U9** `Part('dual_adc_usb','GW1NR-LV9QN88PC6')`. Use the U9 pin map in `architecture/net_plan.md` §2 fpga verbatim, with full UG803 pin names.
   - **Bank 3 (1.8 V):**
     - `VCCO3` (12) → **+1V8**, decoupled by C91 0.1 µF + C93 10 µF.
     - `IOL13B/RECONFIG_N` (9) pull-up R80 → **+1V8**.
     - `IOL5A/JTAGSEL_N/LPLL_T_in` (4) pull-up R85 → **+1V8**.
     - `IOL11B/TCK` (6) → R81 4.7 kΩ pull-down to GND.
     - `IOL11A/TMS` (5), `IOL12B/TDI` (7) and `IOL13A/TDO` (8) go to J4. J4 pin 1 (VREF) → **+1V8**.
   - `IOT5A/MODE0` (88) and `IOT6B/MODE1` (87): 1 kΩ to GND (autoboot).
   - Clocks: FPGA_CLK40 → `IOR5A/RPLL_T_in` (63). FT_CLKOUT → `IOR17A/GCLKT_3` (52).
   - Power:
     - `VCC` ×4 (1, 22, 45, 66) → +1V2.
     - `VCCO1` (58), `VCCO2` ×2 (23, 44) and `VCCX/VCCO0` ×3 (64, 67, 78) → +3V3D.
     - `VSS` ×6 → GND. `EP` (89) → GND (assumption).
   - Decoupling: 0.1 µF per supply pin. There is no VCC ferrite (architect rev 2).
   - READY and DONE do not exist on this package. Do not look for them.
2. **U7** `Part('dual_adc_usb','ADS5231IPAGT')`.
   - Names: `INA`, `~{INA}`, `INB`, `~{INB}`, `INT/~{EXT}` (→ AVDD), `MSBI/SEN`, `OEA/SCLK`, `STPD/SDATA`, `OEB`, `SEL`, `D0_A..D11_A`, `D0_B..D11_B`, `CLK`, `CM`, `ISET`, `REFT`, `REFB`, `AVDD` ×3, `VDRV` ×4, `AGND` ×9, `GND` ×5.
   - **`DVA` (26), `DVB` (22), `OVRA` (39), `OVRB` (9) → NC** (rev 2).
   - REFT/REFB: 2 Ω from the pin, then 0.1 µF ‖ 2.2 µF to GND (Fig. 21), on nets ADC_REFT_F/ADC_REFB_F.
3. **U12/U3/U4** TLV62569DBV (`TLV62569DBVR_SUMMARY.md`). VFB = 0.600 V.
   - U12: R14 200 k (top), R15 100 k (bottom) → 1.800 V. `EN` = VBUS_SW, the same as U4. L3 2.2 µH.
   - The DBV package has no PG pin. tSS = 800 µs.
4. **Y1** `Part('Oscillator','ASE-xxxMHz')`, names `EN`(1) → +3V3D, `GND`(2), `OUT`(3), `Vdd`(4). Note the case of `Vdd`. 0.1 µF at Vdd (datasheet requires 0.01–0.1 µF).
5. **U11** `Part('Memory_EEPROM','93LCxxBxxOT')`, names `DO`(1), `GND`(2), `DI`(3), `CLK`(4), `CS`(5), `VCC`(6). Do not use the 8-pin `93LCxxB`.
   - EEDATA → `DI` directly, and → `DO` via R103 2.2 kΩ. R102 10 kΩ from `DO` to +3V3D.
6. **U10** FT232H uses KiCad names `XCSI`/`XCSO` and `VCCCORE`.
   - VREGIN, VCCD, VCCIO, VPLL and VPHY → +3V3D. VCCA (37) and VCCCORE (38) → FT_VCCCORE with C109.
   - `TEST` → GND. **ACBUS4 (SIWU#) → +3V3D** (rev 2).
   - Y2 load caps C110/C111 = 33 pF C0G.
7. **U2** `Part('dual_adc_usb','TPS22918DBVR')`: `VIN`, `GND`, `ON`, `CT`, `QOD`, `VOUT`.
8. Connect by pin **number** where KiCad names are blank or ambiguous:
   - U21/U41 THS4521: 4 = VOUT+, 5 = VOUT−.
   - U20/U40 OPA810: 1 = OUT.
   - D20/D40 BAV99: 1 → VAFE_N, 2 → VAFE_P, 3 → ATT node.
   - U8 74LVC1G34: 2 = A, 4 = Y.
   - D1 SMF: 1 = K (VBUS_F), 2 = A (GND).
9. **LM27762:** PGOOD (1) → GND if unused. Thermal pad is KiCad pin 13 `PAD` → GND.

## Carried forward
- No PDF for: X322512MSB4SI (CL from MCP), TLV75733PDBVR (MCP + KiCad), SMF5.0A (MCP: VRWM 5 V, VBR 7 V, VC 9.2 V, IR 400 µA), FHD4020S (L1–L3), USBLC6 (UMW). None of these is keystone.
- Custom footprint J2/J3 KH-BNC50-3511: mechanical drawing not captured. The footprint phase must fetch the KH datasheet.
- Land pattern check:
  - U9 EP 6.74 mm matches UG119 p.31.
  - Y1: the YXC 3225 recommended land (p.3) vs the Abracon ASE footprint is within 0.125 mm per pad and acceptable. Check again at layout if the assembler flags it.
- Single-source, marginal stock: U7 and U9. The JTAG programmer must support 1.8 V VREF.
- Numeric worklist, rev 2 additions:
  - Y1 jitter 0.7 ps, 5 mA, start-up 3 ms (datasheet ✓).
  - R14 200 k / R15 100 k with VFB 0.600 V → 1.800 V (TLV62569 VFB datasheet ✓, rev 1).
  - C110/C111 33 pF vs Y2 CL 20 pF (MCP ✓).
  - Rev 1 worklist entries are unchanged.

## Do not redo
- K1, K2, K4, K6, K7, K9 (rev 1) and K8 (rev 2, Y1 jitter) are verified from primary documents.
- The three generated symbols are pin-count verified (64/6/89) and load in SKiDL (`find-symbol.py` EXACT). U11 and Y1 use stock KiCad symbols, now verified against their datasheets.

## Receipt
dual_adc_usb datasheets rev 2: status complete. The only open items are 4 accepted assumptions (K3, K5, K10, EP=GND).
- Rev 2 delta: 1 new summary (Y1 OT322540MJBA4SL, with PDF). U11 93LCxxBxxOT pins verified 6/6 against DS20001794J Table 3-1. SX3M40 summary superseded.
- Totals: summaries 13 current; with PDF 12; summary-only 2 (TLV75733P, X322512); failed PDF 3 (non-keystone).
- Keystone parts with a PDF: 10/10 (adds Y1). Keystone facts verified: K1, K2, K4, K6, K7, K8, K9.
- Rev 1 architecture blockers are resolved by architecture rev 2. Symbols generated: 0 new (3 from rev 1). Cache hits: 0 (use_cache=false).
