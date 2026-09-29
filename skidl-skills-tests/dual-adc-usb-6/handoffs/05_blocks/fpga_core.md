---
phase: 05_blocks/fpga_core
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-22T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---

# Phase 5 block handoff — fpga_core

## Decisions
1. **Signature unchanged from the work order** — `fpga_core(adc1_d, adc2_d, adc1_otr, adc2_otr, adc_pdwn, clk_fpga, sdr_dq, sdr_a, sdr_ba, sdr_clk, sdr_cke, sdr_cs_n, sdr_ras_n, sdr_cas_n, sdr_we_n, sdr_ldqm, sdr_udqm, fifo_d, ifclk, slwr_n, slrd_n, sloe_n, pktend_n, fifoadr, flagb, flagc, v3v3d, v1v2, gnd)`. No parameter was renamed.
2. **Directions** — driven by this block: `ADC_PDWN`, all `SDR_*` except `SDR_DQ`, `SLWR_N`, `SLRD_N`, `SLOE_N`, `PKTEND_N`, `FIFOADR[1:0]`. Sensed only: `ADC1_D`, `ADC2_D`, `ADC1_OTR`, `ADC2_OTR`, `CLK_FPGA`, `IFCLK`, `FLAGB`, `FLAGC`. Bidirectional: `SDR_DQ[15:0]`, `FIFO_D[7:0]`. Consumed only: `+3V3D`, `+1V2`, `GND`.
3. **R30/R34–R39 resolved — UG380 v2.11 was obtained this pass** (phase 4's open question #6 is closed, not carried): R30 = PROGRAM_B pull-up **4.7 kΩ**; R34 = INIT_B pull-up **4.7 kΩ** (open-drain pin, Fig. 2-12 note 5); R35 = DONE pull-up **330 Ω** (Fig. 2-12 note 11 — required for iMPACT indirect flash programming, not the 2.4 kΩ of older UG380 revisions); R36 = CSO_B/`SPI_CS_N` pull-up **4.7 kΩ** (Fig. 2-12 note 9); R37 = CMPCS_B pull-up **4.7 kΩ** (Table 5-1: "Reserved. Leave unconnected or pull up"); R38/R39 = U31 `~WP` and `~HOLD` pull-ups **10 kΩ** (Fig. 2-12 note 8). Every refdes got a function — none declined, none invented.
4. **M0/M1/HSWAPEN carry no resistor — deliberately.** UG380 p.24: "The M1 and M0 mode pins should be set at a constant DC voltage level and **tied directly** to ground or VCCO_2." Master Serial/SPI = M[1:0] = **01** (Table 2-1), so M0 (pin 69) → +3V3D, M1 (pin 60) → GND. HSWAPEN (pin 144) → GND so the internal I/O pull-ups are **enabled** during configuration (Table 5-2), which holds every active-low SDRAM/FX2LP control line inactive-high while the FPGA is unconfigured. SUSPEND (pin 73) → GND (Table 5-1, mandatory when Suspend is unused). These are strap ties, not signals.
5. **VCCAUX → +3V3D** (all 5 pins), VCCINT → +1V2 (5 pins), all 11 VCCO_BANK0-3 pins → +3V3D. No 2.5 V rail invented, per phase-4 Decision #3.
6. **Pin assignment is by physical pin number**, tabulated at the top of the block file as `_P_*` constants with the bank rationale. Banks: 0 = ADC capture + `CLK_FPGA` (pin 124, GCLK13); 3 = `SDR_DQ[15:0]` + `SDR_A[9:0]`; 1 = rest of SDRAM + ADC sideband + LEDs + `FPGA_RESET_N`; 2 = the 17 FX2LP signals (`IFCLK` on pin 56, GCLK1) alongside the 7 SPI-boot pins. 95 of 102 user I/O used.
7. **J4 is 6-pin, so it carries VREF/GND + TMS/TCK/TDO/TDI only** (1=+3V3D, 2=GND, 3=TMS, 4=TCK, 5=TDO, 6=TDI). `net_plan.md` line 87 also lists PROGRAM_B/INIT_B/DONE on J4; they do not fit and stay on-board with their pull-ups. Recorded as an assumption, not a silent drop.
8. Symbols: `Part('dual_adc_usb', 'XC6SLX9-2TQG144C')`, `Part('Memory_Flash', 'W25Q32JVSS')` (indexed by pin **number** — its names carry `~{}` overbar markup), `Part('Connector_Generic', 'Conn_02x03_Odd_Even')` for J4 per phase-4 Decision #6. `Device:LED` is pin 1 = K / pin 2 = A, so the LED anodes are wired explicitly rather than through a `&` chain.
9. **rev.2 — U31 footprint corrected to the 208-mil SOIC-8.** `W25Q32JVSSIQ` (LCSC
   C179173) is Winbond's `SS` suffix = **SOIC-8 208 mil**. The block carried
   `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`, the 150-mil narrow body (≈6.0 mm lead span
   against the part's ≈5.3 mm body / ≈8.0 mm span) — the part would not solder. Now
   `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm` (present in KiCad 9). Pad counts match either
   way, which is why existence-based footprint validation never caught it; this was
   erc_report.md HIGH-3. **Only U31 moved.** U7 (TLV2372, `power` block) legitimately
   stays on the 150-mil `SOIC-8_3.9x4.9mm_P1.27mm` — do not "fix" it to match.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/fpga_core.py` | The block, plus the full FPGA pin map as `_P_*` constants | Assembling, or re-checking any FPGA pin assignment |

## Next phase must
1. Call it exactly: `fpga_core(adc1_d=ADC1_D, adc2_d=ADC2_D, adc1_otr=ADC1_OTR, adc2_otr=ADC2_OTR, adc_pdwn=ADC_PDWN, clk_fpga=CLK_FPGA, sdr_dq=SDR_DQ, sdr_a=SDR_A, sdr_ba=SDR_BA, sdr_clk=SDR_CLK, sdr_cke=SDR_CKE, sdr_cs_n=SDR_CS_N, sdr_ras_n=SDR_RAS_N, sdr_cas_n=SDR_CAS_N, sdr_we_n=SDR_WE_N, sdr_ldqm=SDR_LDQM, sdr_udqm=SDR_UDQM, fifo_d=FIFO_D, ifclk=IFCLK, slwr_n=SLWR_N, slrd_n=SLRD_N, sloe_n=SLOE_N, pktend_n=PKTEND_N, fifoadr=FIFOADR, flagb=FLAGB, flagc=FLAGC, v3v3d=V3V3D, v1v2=V1V2, gnd=GND, tag='fpga_core')`.
2. `+3V3D`, `+1V2` and `GND` must all get `.drive = POWER` at the top level — this block only consumes them (48 / 14 / 50 pins land on them here).
3. Bus widths the block indexes from 0: `ADC1_D`/`ADC2_D` 12, `SDR_DQ` 16, `SDR_A` 13, `SDR_BA` 2, `FIFO_D` 8, `FIFOADR` 2. Bit 0 = LSB throughout.
4. **BOM update required** (like the R10–R13 fix in phase 4): `sourced_bom.md` still lists R30/R34–R39 as 10 kΩ placeholders. R30/R34/R36/R37 are now **4.7 kΩ 0402** and R35 is **330 Ω 0402** — two values not yet in the BOM, both jellybean JLC Basic parts. R31/R38/R39 stay 10 kΩ (existing C25744 line).
5. **rev.2 — `sourcing/sourced_bom.md` line 28 needs the same U31 package correction**
   (`SOIC-8-208mil`, `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm`). The code is now right and
   the BOM is not; this is a `part-sourcer` edit, not a coding one.

## Carried forward
- **Seven user I/O are `NC` on purpose**: 66/67 (CMPMOSI/CMPCLK — kept clear because CMPCS_B is reserved), 74/75 (DOUT_BUSY / AWAKE), 102/104/105 (genuine spares). Promote any of them to a test point only by editing this block.
- **Firmware constraint from the HSWAPEN strap**: the FPGA design must never drive pin 144 (`IO_L1P_HSWAPEN_0`); it is hard-tied to GND. Same for M0/M1 (pins 69/60) after configuration.
- **CCLK/flash datapath termination not placed** — UG380 Fig. 2-12 notes 3 and 4 ask for CCLK termination and a series resistor on the flash datapath, with the value "determined from simulation". No refdes was left for it and no value could be derived without SI simulation; flagged as a layout/SI item rather than an invented 33 Ω.
- **LED current is ~1.3–1.9 mA** (1 kΩ from `sourced_bom.md` against a 3.3 V drive). Adequate for indicators, dim for a bright panel — the BOM value was used verbatim rather than recomputed.
- **The EasyEDA-sourced per-pin name caveat from phase 4 still stands.** UG380 confirmed the *config* pins and modes, but UG385's per-package pinout was still not obtained, so which physical ball carries GCLK13 vs GCLK1 rests on `datasheets/xc6slx9_kipart.csv`. The bank-level and count-level structure is self-consistent (95 of 102 I/O placed, each interface inside one bank). Re-verify pins 124 (`CLK_FPGA`) and 56 (`IFCLK`) against UG385 before fabrication — those two are the only assignments where an EasyEDA naming error would cost a board spin.
- `datasheets/XC6SLX9-2TQG144C.pdf` and `..._DS162.pdf` are **not on disk** although `XC6SLX9-2TQG144C_SUMMARY.md` cites them; only the summary survived. Not blocking — UG380 (fetched this pass) covered everything this block needed.

## Do not redo
- The config-strap analysis in Decisions 3–4. It is primary-source (UG380 v2.11 Table 2-1, Table 5-1, Table 5-2, Figure 2-12 and its notes), not a hypothesis.
- The bank allocation and pin map. It is capacity-tight (bank 0 and bank 3 are exactly full), so a partial re-shuffle will not fit.

## Receipt
- Block `fpga_core`: 45 parts (U30, U31, J4, D30, D31, R30–R39, C40–C69), 107 nets at smoke-test.
- `python -m py_compile` OK; block instantiates cleanly against the project symbol library with every refdes landing exactly as assigned (no SKiDL uniquification).
- Footprints valid (re-validated rev.2): all 9 distinct footprint strings present in the
  KiCad 9 libraries. **rev.2 changed exactly one line — U31's footprint string.**
- Signature changed: **no**. Interface nets changed: **no**.
- Full circuit re-run after the rev.2 edit: **0 ERC errors, 2 warnings** (the known
  U5/U6 LDO drive false positives).
- Phase-4 open question #6 (R30/R34–R39 function) closed with a primary source; 1 new open item (CCLK termination value) carried forward.
