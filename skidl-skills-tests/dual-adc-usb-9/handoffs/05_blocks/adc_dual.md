---
phase: 05_blocks/adc_dual
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-10-01T03:18:35Z
status: complete
next_phase: 05_coding
---

# Block handoff - adc_dual

## Decisions
- Final signature (unchanged): `adc_dual(aina_p, aina_n, ainb_p, ainb_n, adc_vcm, adc_clk, adc_da, adc_db, adc_sel, adc_msbi_sen, adc_oea_sclk, adc_stpd_sdata, adc_oeb, v3v3a, v3v3d, gnd)`.
- U7 `dual_adc_usb:ADS5231IPAGT`, all pins connected by number (names contain ~{}/slashes).
- adc_da / adc_db are 12-bit Buses; index i -> D{i}_A (pin 27+i) / D{i}_B (pin 10+i); index 0 = LSB.
- Internal reference: INT/~{EXT} (56) tied to +3V3A.
- REFT/REFB per datasheet Fig. 21 (K9): pin -> 2 ohm (R60/R61) -> 0.1 uF || 2.2 uF to GND (C69+C70 on ADC_REFT_F, C72+C73 on ADC_REFB_F).
- ISET (60) -> R62 56.2k 1 % -> GND. CM (52) = adc_vcm, bypassed by C71 100 nF.
- Decoupling in block: AVDD C60-C62 100 nF + C63 10 uF (0603); VDRV C64-C67 100 nF + C68 10 uF (0603).
- Drives: adc_da, adc_db, adc_vcm (CM output). Senses: aina_p/n, ainb_p/n, adc_clk, adc_sel, adc_msbi_sen, adc_oea_sclk, adc_stpd_sdata, adc_oeb. Power-in: v3v3a, v3v3d, gnd. No bidirectional nets (SEL=0 parallel mode assumed; in serial mode STPD/SDATA is still an input).
- Internal nets: ADC_REFT, ADC_REFT_F, ADC_REFB, ADC_REFB_F, ADC_ISET.
- All parts carry MPN and LCSC fields from sourced_bom.

## Next phase must
- Import `from .adc_dual import adc_dual`. Call:
  `adc_dual(aina_p=ADC_AINA_P, aina_n=ADC_AINA_N, ainb_p=ADC_AINB_P, ainb_n=ADC_AINB_N, adc_vcm=ADC_VCM, adc_clk=ADC_CLK, adc_da=ADC_DA, adc_db=ADC_DB, adc_sel=ADC_SEL, adc_msbi_sen=ADC_MSBI_SEN, adc_oea_sclk=ADC_OEA_SCLK, adc_stpd_sdata=ADC_STPD_SDATA, adc_oeb=ADC_OEB, v3v3a=V3V3A, v3v3d=V3V3D, gnd=GND, tag='adc_dual')`
  with ADC_DA = Bus('ADC_DA', 12), ADC_DB = Bus('ADC_DB', 12); V3V3A/V3V3D are nets named +3V3A/+3V3D.
- `.drive = POWER` on +3V3A, +3V3D, GND at top level (or via regulator blocks): this block only sinks them.
- Symbol lib `symbols/dual_adc_usb.kicad_sym` must be on the search path: `lib_search_paths[KICAD].append('<project>/symbols')` (setting KICAD9_SYMBOL_DIR in the shell was overridden by the user profile in my test).

## Carried forward
- NC intentionally: U7 pins 9 OVRB, 22 DVB, 26 DVA, 39 OVRA (arch rev 2).
- No decoupling expected from the assembler for U7.
- Assumes ADC_VCM's only other loads are THS4521 VOCM inputs (afe_ch_a/b); CM is the sole driver.
- Assumes FPGA drives SEL/MSBI/OEA/STPD/OEB low after config (net_plan power-on defaults); no pull resistors in this block.

## Receipt
- block adc_dual: 18 parts (U7, R60-R62, C60-C73), 45 nets (40 interface incl. 24 bus bits + 5 internal).
- py_compile OK; smoke instantiation with clock_gen: only the 4 intended NC pins unconnected.
- Footprints: TQFP-64_10x10mm_P0.5mm, R/C_0402_1005Metric, C_0603_1608Metric (all stock KiCad). Signature changed: no.
