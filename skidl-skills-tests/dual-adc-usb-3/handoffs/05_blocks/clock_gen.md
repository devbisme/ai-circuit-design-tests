---
phase: 05_blocks/clock_gen
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T00:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 block handoff — `clock_gen`

10.000 MHz MEMS XO (Y1) + dual non-inverting fanout buffer (U11) + three 33 R series
terminations. File: `circuits/dual_adc_usb/clock_gen.py`.

## Decisions

1. **Signature UNCHANGED from the work order:**
   `clock_gen(v3v3, gnd, clk_adc1, clk_adc2, clk_fpga)` — parameter names verbatim,
   in that order.
2. **Net direction:** this block **drives** `CLK_ADC1`, `CLK_ADC2`, `CLK_FPGA`
   (outputs only, no sensing). It **consumes** `+3V3` and `GND` (never drives them).
   Nothing here is bidirectional.
3. **Ref assignment resolved a BOM/net-plan conflict.** `sourcing/sourced_bom.md` line 41
   labels the SiT1602 oscillator `U11` and line 42 labels the SN74LVC2G34 buffer
   "(part of clock_gen, U11)" — an ambiguous sourcing row. `architecture/net_plan.md`
   (`## Clock nets`) is unambiguous — **Y1 = XO, U11 = buffer (1A/2A/1Y/2Y)** — and it
   matches this block's assigned refs. Net plan was followed. The sourcing row's ref
   column is the error; MPN/LCSC/footprint data in both rows is used as-is.
4. **`Y2` (`X322524MOB4SI`) is NOT part of this block**, despite
   `handoffs/04_datasheets.md` listing it under `clock_gen`. It is not in this block's
   ref list, and no net in `net_plan.md`'s clock section touches it. It is a 24 MHz
   3225 crystal — almost certainly the FX2LP crystal in `usb_controller`. **Whoever
   owns `usb_controller` must claim Y2**; if nobody does, it lands in no block.
5. **Y1 symbol: `Oscillator:SiT8008xx-2x-xxE`** — SiTime's own 4-pad PQFN 3.2×2.5 mm
   part, whose KiCad `Footprint` property is exactly the sourced string
   `Oscillator:Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm`. **Source trusted for the pinout:
   the KiCad symbol** (pins `OE`=1, `GND`=2, `OUT`=3, `Vdd`=4), which independently
   corroborates the LOW-CONFIDENCE table in `datasheets/SiT1602BI-22-33E-10.000000_SUMMARY.md`.
   No SiT1602 datasheet exists on disk and none was fetched. Two independent sources now
   agree, but neither is a SiT1602 primary document — see Carried forward.
6. **Y1 OE tied to `+3V3` (always enabled).** No OE net exists anywhere in `net_plan.md`;
   floating OE on SiTime XOs defaults to output-disabled.
7. **U11 pins addressed by NUMBER, not name.** The KiCad `74xGxx:74LVC2G34` symbol is a
   3-unit symbol whose buffer I/O pins are unnamed (`~`). Mapping used (matches TI
   datasheet and `datasheets/SN74LVC2G34DBVR_SUMMARY.md`): 1=1A, 2=GND, 3=2A, 4=2Y,
   5=VCC, 6=1Y.
8. **Phase alignment** is achieved by taking both ADC clocks from the two channels of one
   die with identical 33 R terminations (matched topology). **Layout must length-match the
   `CLK_ADC1` and `CLK_ADC2` traces** — schematic-level matching is all this block can do.
9. **`CLK_FPGA` is tapped ahead of the buffer** (per `net_plan.md`), so the XO drives three
   loads: U11 1A, U11 2A, and R32. Consequence: CLK_FPGA leads the ADC clocks by the
   buffer's ~3 ns propagation delay and is **not** phase-matched to them. Fine for a
   re-timing FPGA; recorded because it is not obvious from the block name.

## Next phase must

1. **Call it exactly like this** (keyword args, from `__main__.py`):
   ```python
   clock_gen(v3v3=V3V3, gnd=GND, clk_adc1=CLK_ADC1, clk_adc2=CLK_ADC2, clk_fpga=CLK_FPGA)
   ```
2. **Set `.drive = POWER` at the top level on `+3V3` and `GND`.** This block only consumes
   them; without it ERC reports "insufficient drive" on both.
3. **Do not create `CLK_XO`, `CLK_ADC1_BUF` or `CLK_ADC2_BUF` at the top level** — all
   three are block-internal and created inside `clock_gen()`.
4. `CLK_ADC1`/`CLK_ADC2`/`CLK_FPGA` arrive at the assembler **already driven**. The
   consuming blocks (`adc_pair` U9/U10 CLK, `fpga_capture` U12 clock input) attach input
   pins only — a second driver on any of these three is an error, not a warning.

## Carried forward

- **Y1 pin-1 (OE) vs pin-4 (Vdd) is still unverified against a SiT1602 primary document.**
  Corroborated by the KiCad SiTime symbol (Decision 5) but not proven. A swap here shorts
  +3V3 through OE's internal pull and kills the clock. **Physically confirm the pin-1 dot
  against the part/tape before fab release.** Unchanged from `04_datasheets.md`.
- **`Y2` is unclaimed by any block** — see Decision 4. Escalate to the assembler/architect
  if `usb_controller` also does not include it.
- **Layout length-matching of `CLK_ADC1`/`CLK_ADC2`** — see Decision 8. Not enforceable in
  SKiDL; carry to the layout stage.
- **No `NC` pins in this block.** Every pin on Y1 and U11 is connected.
- **Decoupling is self-contained**: C71 (Y1 Vdd) and C72 (U11 VCC), 100 nF each. This block
  assumes **no** additional bulk decoupling from the assembler. If the +3V3 rail's bulk
  capacitance is far from this block, layout should add a local 1 µF — not budgeted here
  because no ref designator was allocated for one.

## Do not redo

- The Y1/U11 ref assignment (Decision 3) and the U11 pin-number map (Decision 7).
- Footprint strings — all four validated against the KiCad system library, exit 0.

## Receipt

- Block: `clock_gen` → `circuits/dual_adc_usb/clock_gen.py`
- Parts: **7** (Y1, U11, R32, R33, R34, C71, C72) — matches the assigned ref list exactly.
- Nets: **8** touched — 5 interface (`+3V3`, `GND`, `CLK_ADC1`, `CLK_ADC2`, `CLK_FPGA`),
  3 internal (`CLK_XO`, `CLK_ADC1_BUF`, `CLK_ADC2_BUF`).
- `python -m py_compile`: **OK**. Instantiation smoke test: **OK**, connectivity matches
  `net_plan.md` row for row.
- Footprints: **4 checked, all valid** (`validate-footprints.py`, exit 0).
- Signature changed: **NO**.
- No sibling design directory (`../dual-adc-usb-1`, `../dual-adc-usb-2`) was read.
