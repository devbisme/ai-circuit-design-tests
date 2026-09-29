---
phase: 05_blocks/clock
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-26T13:20:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — clock

## Decisions
- Final signature (unchanged): `clock(adc_clk, fpga_clk, v3v3a, gnd)`.
- **Drives** adc_clk and fpga_clk (X1 OUTPUT on local XO_OUT, each through its own 33 Ω series R16/R17). **Consumes** v3v3a, gnd.
- X1 = `dual_adc_usb:SX3M40.000B10F20TNN`, pins by number: 1 Tri-State/OE → XO_VDD (enabled), 2 GND, 3 Output → XO_OUT, 4 Vdd → XO_VDD.
- Local nets: XO_VDD (v3v3a → FB2 → C31 0.1 µF + C32 1 µF; `.drive = POWER` set in-block), XO_OUT.
- Footprint `Oscillator:Oscillator_SMD_SeikoEpson_SG8002CE-4Pin_3.2x2.5mm` (datasheet librarian confirmed pad match).

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/clock.py` | block @SubCircuit | Assembly |

## Next phase must
1. skidl-assembler: `clock(adc_clk=ADC_CLK, fpga_clk=FPGA_CLK, v3v3a=V3V3A, gnd=GND, tag='clock')`.
2. `GND.drive = POWER` at top; V3V3A is driven by power_analog. No other drive settings needed.
3. Layout: R16 at X1, ADC_CLK trace ≤ 15 mm over solid GND.

## Carried forward
- **Open risk (unverified keystone):** X1 RMS phase jitter is not specified in the SCTF datasheet. Assumed 1–3 ps RMS (typical 3225 CMOS XO), within the ≤ 3 ps budget (~80 dB SNRj) for 40 MSPS / ~60 dB SNR. Close with SCTF phase-noise data or swap to an XO with a jitter spec.
- BOM cell corrections: X1 symbol `SYMBOL_NEEDED` → `dual_adc_usb:SX3M40.000B10F20TNN`. FB2 notes say "feeds FPGA_CLK branch" — wrong; FB2 feeds the XO supply (XO_VDD) per net_plan. Notes-only fix.
- No NC pins.

## Receipt
- Block clock: 6 parts (X1, FB2, R16, R17, C31, C32), 6 nets (2 local), py_compile OK, footprints 4/4 resolve, signature changed: no. Trial ERC with adc block: 0 errors.
