---
phase: 05_blocks/clock_gen
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-22T22:58:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 handoff — block `clock_gen` (instantiated ×1)

## Decisions

1. **Signature UNCHANGED, as written:** `clock_gen(clk_adc, clk_fpga, p3v3d, gnd)`.
2. **Driven by this block:** `clk_adc` (CLK10_ADC), `clk_fpga` (CLK10_FPGA).
   **Sensed only:** `p3v3d`, `gnd`. **Bidirectional:** none.
   `CLK10_OSC` (X1 OUT before the series resistors) is **block-internal** — it is not a
   parameter, so nothing outside this block can tap it.
3. **One oscillator, no divider, no buffer.** Both ADC channels sample off the same
   ADS5231 CLK pin, so channel skew is the converter's aperture matching, not clock
   distribution — that is how SPEC F12 (≤5 ns) is met. Adding a second source or a
   divider would break it.
4. **R31/R32 are per-branch series-source terminations at the oscillator**, 33 Ω each
   (net_plan.md: "33 Ω series at the source"), so the two-load fan-out is damped
   branch-by-branch instead of as one stub-split net.
5. **X1 OE (pin 1) is tied high to `P3V3D`, not left floating.** The XO is freely
   substitutable per the architecture; a substitute without an internal OE pull-up
   would come up tri-stated. Pinout 1 OE · 2 GND · 3 OUT · 4 VDD, from the generated
   symbol `dual_adc_usb:SX3M10.000M20F30TNN`, addressed by number.
6. **P3V3D is unaffected by the concurrent `02_architecture.md` power-rail revision**
   (that split is U5's VCCX/VCCIO0 → 1.8 V). X1 takes 1.62–3.63 V; 3.3 V stands.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/clock_gen.py` | The `clock_gen` @SubCircuit — X1, R31, R32, C31 | Assembling the circuit |

## Next phase must

Addressed to **skidl-assembler**:

1. Emit exactly this one call:
```python
clock_gen(clk_adc=CLK10_ADC, clk_fpga=CLK10_FPGA, p3v3d=P3V3D, gnd=GND, tag='clock_gen')
```
2. `P3V3D` and `GND` need **`.drive = POWER`** at the top level — X1's VDD/GND are
   `power_in` and this block only consumes the rail.
3. `CLK10_ADC` lands on U4 CLK (pin 24, `adc_dual`); `CLK10_FPGA` lands on a
   clock-capable GW1NR-9 input (`fpga_core`). Do not connect anything else to either —
   each is a point-to-point branch behind its own 33 Ω.
4. No BOM change from this block — 4/4 refs, values, footprints and symbols match
   `sourcing/sourced_bom.csv` exactly.

## Carried forward

| Item | Note |
|---|---|
| X1 pinout provenance | `SX3M10.000M20F30TNN.pdf` is image-only; the 1/2/3/4 = OE/GND/OUT/VDD mapping is the JEDEC-standard 4-pin 3225 arrangement plus JLC's EasyEDA pin data for this LCSC#, not datasheet text (`04_datasheets.md` carried this forward too). A substitute XO must be checked against this pinout, since 4-pin XOs with OE and VDD swapped do exist. |
| Single decoupling cap | C31 (100 nF) only; no bulk cap on X1's rail — that is what the BOM assigns. 10 mA max supply current, and `P3V3D` bulk lives in `power_tree`. |
| Jitter budget | Not analysed in this block; the XO's ±20 ppm/±30 ppm and its phase-noise behaviour are sourcing/architecture's call, unchanged here. |
| No pins left NC | All 4 X1 pins are connected. |

## Do not redo

- The single-clock topology (SPEC F12) — no second oscillator, divider or fan-out buffer.
- The 33 Ω source terminations and their placement at the oscillator.
- X1's symbol/footprint choice (generated symbol confirmed EXACT at phase 4).

## Receipt

- Block `clock_gen`: 4 parts (X1, R31, R32, C31), 6 nets in an isolated smoke test;
  all refs unique and exactly as assigned.
- `py_compile` OK; instantiation smoke test OK; 3/3 footprint strings resolve.
- BOM cross-check: 4/4 ref/value/footprint/symbol rows match `sourced_bom.csv`, 0 drift.
- Signature changed: **no**.
