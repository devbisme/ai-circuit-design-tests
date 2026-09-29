---
phase: 05_blocks/sample_clock
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T23:35:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — sample_clock

## Decisions
- Final signature is **unchanged** from the work order: `sample_clock(adc_clk, adc_clk_fpga, va_3v3, gnd)`.
- Net roles:
  - **Driven by this block:** adc_clk (X1 → R57, 33 Ω) and adc_clk_fpga (X1 → R58, 33 Ω). Both are the same edge, series-terminated at the source.
  - **Consumed:** va_3v3, which feeds FB7.
  - **Ground:** gnd.
- Block-local nets:
  - OSC_VDD: FB7 → X1.VDD/X1.OE, C63, C64. It gets `.drive = POWER` inside the block.
  - OSC_OUT: X1.OUT → R57, R58.
- **X1 symbol resolved as the work order instructed.** I used `Oscillator:ASE-xxxMHz`, not the BOM's 2-pin `Device:Crystal`.
  - Its pins are 1 EN, 2 GND, 3 OUT, 4 Vdd. That matches the SX3M summary pinout (1 OE, 2 GND, 3 OUT, 4 VDD).
  - Its default footprint is the BOM footprint, `Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm`.
  - MPN SX3M20.000B10F20TNN and LCSC C5452685 are unchanged. The part value is `20MHz`.
- **X1 OE (pin 1) is tied to OSC_VDD.** OE is active high per the summary, so the output is always enabled, as the net plan also requires.
- Decoupling at X1: C63 (100 nF) in parallel with C64 (1 µF), OSC_VDD to GND.
- TP9 is on ADC_CLK, the ADC side of R57, per net_plan §10.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/sample_clock.py` | `@SubCircuit sample_clock`: X1, R57, R58, C63, C64, FB7, TP9 | Assembling or reviewing this block |

## Next phase must
1. skidl-assembler: call it by keyword, exactly as follows:
   `sample_clock(adc_clk=ADC_CLK, adc_clk_fpga=ADC_CLK_FPGA, va_3v3=VA_3V3, gnd=GND, tag='sample_clock')`
2. Set `.drive = POWER` at top level on VA_3V3 and GND, unless power_rails already drives them. This block has only passive or power_in pins on them.

## Carried forward
- **X1 jitter (≤ 5 ps rms) is still unconfirmed.** No datasheet for this MPN gives a jitter figure (04_datasheets). This is an open CP-spec risk, not closed here.
- **X1 land pattern is unverified.** It uses the generic Abracon ASE 3225 footprint. The pad numbering matches the standard 4-pin XO order (1 OE, 2 GND, 3 OUT, 4 VDD), but pad geometry was not checked against an SCTF drawing.
- The ERC test instantiation gave 0 errors and 2 warnings. Both are single-pin interface nets (VA_3V3, ADC_CLK_FPGA) that close at assembly.

## Do not redo
- The X1 symbol choice (`Oscillator:ASE-xxxMHz`) and OE → OSC_VDD. Do not revert to `Device:Crystal`.

## Receipt
- Block `sample_clock`: 7 parts (X1, R57, R58, C63, C64, FB7, TP9).
- 6 nets: 4 interface and 2 local.
- py_compile OK. Footprints valid (validate-footprints.py exit 0, plus a direct file check of all 5 strings).
- Test ERC: 0 errors, and no pin unconnected.
- Signature changed: **no**.
