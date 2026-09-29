---
phase: 05_blocks/clock_20m
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-20T18:45:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — clock_20m

## Decisions

1. **Signature is UNCHANGED from the work order**: `clock_20m(adc_clk, fpga_clk, v3v3_a, gnd)`.
2. **Direction map** — DRIVEN by this block (through a series resistor, so passive at the
   net boundary): `ADC_CLK`, `FPGA_CLK`. CONSUMED only: `+3V3_A`, `GND`.
3. **X1 = OT252020MJBA4SL**, symbol `Part('dual_adc_usb','OT252020MJBA4SL')`, footprint
   `Oscillator:Oscillator_SMD_Kyocera_KC2520Z-4Pin_2.5x2.0mm` — the substitution from
   handoff 04 item 5 (0.7 ps RMS jitter vs. no published spec on the sourced part).
4. **Pin 1 (Tri-state/OE) is tied to `XO_VDD`, the post-ferrite node**, not directly to
   `+3V3_A`. Electrically the same "tied high to +3V3_A" the work order asks for (FB4 is a
   DC short), but it keeps all X1 current — including the OE pin's — behind the bead and the
   OE pin at exactly the part's own VDD. Never floating.
5. **Both series-termination resistors kept, one per branch at the oscillator end**:
   `XO_OUT` = X1 pin 3; `R_s1` (33 Ω) → `ADC_CLK`; `R_s2` (33 Ω) → `FPGA_CLK`. One XO, two
   loads, per `architecture/net_plan.md` § Clock nets. `ADC_CLK` is never driven by the FPGA.
6. **C56 and C57 are both 100nF at pin 4** (as sourced, CL05B104KO5NNNC 0402). See Carried
   forward — a bulk cap would be the better second value.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/clock_20m.py` | The block (6 parts, 7 nets) | Assembling |
| `datasheets/OT252020MJBA4SL_SUMMARY.md` | X1 pin map, jitter spec, footprint | Reviewing X1 |

## Next phase must

1. **Call the block with keywords, exactly this:**
   ```python
   clock_20m(adc_clk=ADC_CLK, fpga_clk=FPGA_CLK, v3v3_a=V3V3_A, gnd=GND)
   ```
2. **Set `.drive = POWER` at the top level on `+3V3_A` and `GND`** — this block only
   consumes them.
3. **Put `symbols/` on `KICAD9_SYMBOL_DIR`** before running the assembled circuit — X1's
   symbol is the generated `dual_adc_usb:OT252020MJBA4SL`, not a stock-library part.
4. **Expect, and do not "fix", ERC warnings of the "no driving pin / insufficient drive"
   class on `ADC_CLK` and `FPGA_CLK`.** The only pins on each net are a passive resistor end
   and an IC clock input, because the XO output is deliberately isolated by R_s1/R_s2.
   Silencing them by connecting X1's output pin directly to either net would destroy the
   termination scheme.

## Carried forward

- **C56/C57 are both 100nF.** Normal practice at an XO is 100nF at the pin **plus** a ~1µF
  bulk behind the ferrite; sourcing bought two identical 100nF 0402s, and this block does
  not re-source parts. Recommend changing C57 to 1µF 0402 at BOM reconciliation — no code
  change beyond the `value=` string.
- **FB4 = PBY160808T-601Y-N (600 Ω @ 100 MHz, 0603)** as sourced; the bead's DC resistance
  and the XO's ≤4 mA draw give a negligible drop, but the bead's usefulness assumes the
  layout puts it right at the X1 supply pin (`design_risks.md` R-7 territory).
- **Jitter budget is inherited, not re-verified here** — 0.7 ps RMS [12 kHz–20 MHz] from
  the manufacturer's sheet, against architecture R-4's 5 ps. No measurement exists yet.
- **Stub-length constraint is a layout instruction, not a schematic one**: net_plan requires
  both clock stubs < 15 mm. Nothing in this file can enforce it.

## Do not redo

- The X1 substitution and its footprint choice (handoff 04 item 5, pre-authorized by
  architecture R-4).
- The single-oscillator/two-series-resistor topology — it is the net plan's, and it is what
  keeps `ADC_CLK` off any FPGA output.

## Receipt

- block: `clock_20m` → `circuits/dual_adc_usb/clock_20m.py`
- parts 6 (X1, FB4, R_s1, R_s2, C56, C57), nets 7 (4 interface + `XO_VDD`, `XO_OUT`)
- `python -m py_compile` OK; block instantiates cleanly with the keyword call above
- footprints: 4 distinct strings, all validated present in the stock KiCad libraries
- signature changed: **no**
- status: complete
