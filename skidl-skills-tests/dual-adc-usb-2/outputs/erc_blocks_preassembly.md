# Pre-assembly per-block ERC sweep — dual_adc_usb
Date: 2026-09-09  ·  Scope: **individual blocks in isolation** (NOT the full circuit)

## Status: NOT a release gate
`fpga_core` is not yet written and `__init__.py`/`__main__.py` do not exist, so the
assembled circuit cannot be ERC'd. This sweep exercises each block on its own to catch
defects early. Full-circuit ERC must still run before any netlist export.

## Results (8 of 9 blocks)

| Block | ERC errors | Notes |
|---|---|---|
| usb_c_input   | 0 | clean, no warnings |
| power_digital | 0 | 3 isolation warnings |
| power_analog  | 0 | 8 isolation warnings |
| clock_gen     | 0 | 9 isolation warnings |
| afe_channel   | 0 | 9 isolation warnings |
| adc_channel   | 0 | 30 isolation warnings |
| sram_buffer   | 0 | 89 isolation warnings (18 addr + 16 data lines undriven) |
| usb_bridge    | 0 | **1 error found and FIXED** (below); 44 isolation warnings |
| fpga_core     | — | not yet written |

All warnings are of the "no drivers / only one pin / insufficient drive current" family,
which is the expected signature of a block ERC'd with its interface nets unconnected.
They should disappear on assembly; any that remain are real and must be triaged then.

## Error found and fixed

**usb_bridge — FT232H 1.8 V regulator outputs shorted together.**
`POWER-OUT pin 38/VCCCORE <==> POWER-OUT pin 37/VCCA` on net `FT_VCORE_1V8`.
VCCA (PHY analog) and VCCCORE (digital core) are two independent internal 1.8 V regulator
outputs. Split into `FT_VCCA_1V8` (C35, 1 uF) and `FT_VCORE_1V8` (C36, 1 uF). No BOM change.

## Carried into full-circuit ERC / design review

1. **afe_channel C_trim out of range** — attenuator compensation computes to ~18.9 pF
   nominal against a sourced 2-10 pF trimmer. Either the part or the compensation topology
   is wrong. ERC cannot catch this; it needs a human/reviewer decision.
2. **afe_channel: OPA836 PD pin polarity** unconfirmed against the datasheet.
3. Any isolation warning that survives assembly.
