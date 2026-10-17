---
phase: 05_blocks/clock
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - clock

## Decisions
1. Signature unchanged: `clock(v3v3, adc_clk, clk10_fpga, gnd)`.
2. Direction: drives adc_clk (U401 1Y pin 6 -> R401 33R) and clk10_fpga (U401 2Y pin 4 -> R402 33R); consumes v3v3, gnd.
3. Local rail `+3V3_CLK` = +3V3 -> FB401 (BLM18KG601SN1D); feeds Y401 Vdd(4) + EN(1, tied high = always on) and U401 VCC(5); C401/C402 100n + C403 4.7u. `.drive = POWER` + PWR_FLAG `#FLG401` (power:PWR_FLAG, no footprint) for KiCad ERC.
4. U401 (`74xGxx:74LVC2G34`, pins all named `~`) connected by pin number: 1 1A, 3 2A both on XO_OUT; 2 GND.

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/clock.py` | @SubCircuit clock, 8 BOM parts + 1 PWR_FLAG |

## Next phase must
- Emit: `clock(v3v3=P3V3, adc_clk=ADC_CLK, clk10_fpga=CLK10_FPGA, gnd=GND, tag='clock')`.
- `+3V3`, `GND` only consumed here: `.drive = POWER` at top level if the power blocks do not drive them.

## Carried forward
- SX3M10.000B10F20TNN RMS jitter NOT specified by datasheet (architecture wanted <= 5 ps); open, SNR impact only (~90 dB limit at 1 MHz input even at 5 ps).
- SN74LVC2G34 LCSC stock is a UMW clone; pinout from TI datasheet.
- No intentional NC pins. Decoupling all in-block.
- Local nets: +3V3_CLK, XO_OUT, CLKB1, CLKB2.

## Do not redo
- MPNs/footprints/values verbatim from `sourcing/sourced_bom.csv`; pins checked against KiCad symbols.

## Receipt
clock: 8 parts (Y401, U401, FB401, R401, R402, C401-C403) + #FLG401; 4 interface args, 4 local nets; py_compile OK; footprints from CSV verbatim; signature changed: no.
