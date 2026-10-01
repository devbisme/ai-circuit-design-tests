---
phase: 05_blocks/clock_gen
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-10-01T03:18:35Z
status: complete
next_phase: 05_coding
---

# Block handoff - clock_gen

## Decisions
- Final signature (unchanged): `clock_gen(adc_clk, fpga_clk40, v3v3d, gnd)`.
- Y1 `Oscillator:ASE-xxxMHz` (OT322540MJBA4SL 40 MHz): 1 EN -> +3V3D, 2 GND, 3 OUT -> XO_OUT, 4 Vdd -> +3V3D.
- XO_OUT -> R70 33 ohm -> adc_clk. XO_OUT -> U8 `74xGxx:74LVC1G34` A (pin 2); Y (pin 4) -> FPGA_CLK40_SRC -> R71 33 ohm -> fpga_clk40.
- U8: 3 GND, 5 VCC = +3V3D, pin 1 NC. Connected by number (KiCad names for A/Y are '~').
- Decoupling in block: C75 100 nF at Y1 Vdd, C76 100 nF at U8 VCC.
- Drives: adc_clk, fpga_clk40. Consumes: v3v3d, gnd. Internal nets: XO_OUT, FPGA_CLK40_SRC.
- All parts carry MPN and LCSC fields from sourced_bom.

## Next phase must
- Import `from .clock_gen import clock_gen`. Call:
  `clock_gen(adc_clk=ADC_CLK, fpga_clk40=FPGA_CLK40, v3v3d=V3V3D, gnd=GND, tag='clock_gen')`
- `.drive = POWER` on +3V3D and GND at top level (or via regulator blocks).

## Carried forward
- U8 pin 1 NC intentionally (symbol pin type NC).
- Layout: U8 input stub <= 5 mm from Y1; R70/R71 at the source end.
- Y1 footprint is the Abracon ASE land pattern (accepted by datasheets phase; re-check at layout).
- Optional 10 uF on Y1 Vdd (datasheet test circuit) not added; not in BOM.

## Receipt
- block clock_gen: 6 parts (Y1, U8, R70, R71, C75, C76), 6 nets (4 interface + 2 internal).
- py_compile OK; smoke instantiation OK, only U8 pin 1 (NC) unconnected.
- Footprints: Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm, SOT-353_SC-70-5, R/C_0402_1005Metric. Signature changed: no.
