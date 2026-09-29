---
phase: 05_blocks/clock_gen
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Wrote `circuits/dual_adc_usb/clock_gen.py`: 10 MHz XO (X1) fanned out through R10 (33 Ω)
  to two independent 74LVC1G34 buffers (U16 → CLK_ADC_A via R11, U17 → CLK_ADC_B via R12),
  with CLK_10M tapped directly off the same post-R10 node as an unbuffered reference to the
  FPGA.
- Compiles clean (`py_compile`) and passes the project's footprint validator hook with no
  errors.
- Standalone SKiDL execution (temp harness, own driver nets, not the real assembler)
  produced 9 parts / 8 nets, ERC: **0 errors, 9 warnings** — all 9 warnings are expected
  artifacts of testing this block in isolation (single-pin interface nets, no POWER-drive
  source on V3V3_CLK/GND yet) and are not code defects.
- Function signature used exactly as given in the work order — no changes.

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/clock_gen.py | `clock_gen` SubCircuit block (X1, U16, U17, R10-R12, C22-C24) | skidl-assembler |

## Key facts for the next phase

- **Final function signature (unchanged from work order):**
  `def clock_gen(v3v3_clk, gnd, clk_adc_a, clk_adc_b, clk_10m):`
- **Net directions (all are plain bidirectional `Net` params — SKiDL doesn't type-enforce
  direction, but logically):**
  - `v3v3_clk` — **input** (consumed only). This block does not regulate/generate 3.3 V; it
    expects `power_analog`'s V3V3_A rail already stepped down through FB6 upstream, per
    net_plan.md line 16. **The assembler must ensure whichever block supplies V3V3_CLK sets
    `.drive = POWER` on it** (this block only adds a POWER-IN load, it does not source
    current) — otherwise ERC will flag insufficient drive current (seen in isolated testing
    above; expected to clear once wired to the real V3V3_A/FB6 source).
  - `gnd` — input/shared (global ground net, same convention as every other block).
  - `clk_adc_a`, `clk_adc_b` — **outputs**, driven by U16/U17 through R11/R12. This block
    drives them; `adc_channel` (×2) consumes them at U14/U15 CLK pins.
  - `clk_10m` — **output**, driven directly off the R10-terminated XO node (unbuffered — see
    Decisions). This block drives it; `fpga_core` consumes it at U9's GBIN pin.
- Internal nets (not exposed, no assembler action needed): `clk_xo_raw` (X1 OUT → R10),
  `clk_10m_xo` (post-R10 fan-out node, merges with `clk_10m` net by SKiDL net-merge — see
  Decisions), `clk_adc_a_pre` / `clk_adc_b_pre` (buffer outputs → R11/R12).
- 74LVC1G34 KiCad symbol (`74xGxx:74LVC1G34`) reports the A/Y pins generically as `~` (not
  named) — connected by **pin number** (`u16[2]`=A/input, `u16[4]`=Y/output) instead of by
  name. VCC/GND/NC pin names work as expected by name.

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| CG1 | CLK_10M topology (buffered vs. direct tap) | Add a 3rd buffer stage for CLK_10M / tap directly off the R10-terminated node | **Direct tap, no extra buffer** | net_plan.md line 56 describes a single R-33Ω termination shared by the whole fan-out ("X1 OUT → R 33Ω → fan to U16 IN, U17 IN, and (via R 33Ω) CLK_10M"); sourced BOM allocates exactly 3 resistors (R10-R12) to this block, matching XO-out + 2 ADC legs — there is no 4th resistor or 3rd buffer IC sourced for a dedicated CLK_10M driver. This also directly satisfies the binding constraint that the ADC sample clock is never generated in/routed through FPGA fabric — CLK_10M is purely a downstream reference tap, not a re-driven/looped signal. |
| CG2 | Decoupling cap assignment (C22/C23/C24 across 3 ICs) | Strict 100nF+10µF per IC (generic template rule) / follow sourced BOM's actual 3-cap allocation | **Follow sourced BOM**: C22, C23 (100 nF each) + C24 (1 µF bulk), all wired across V3V3_CLK/GND | Sourced BOM (sourcing/sourced_bom.md line 84-85) and the ASEM1/74LVC1G34 datasheet summaries explicitly describe C22/C23 as one shared 100 nF bypass group across X1+U16+U17, with C24 as a shared 1 µF bulk cap — not a distinct 100nF+10µF pair per IC. Inventing extra caps would contradict "use parts exactly as listed in the BOM." Electrically all three ICs share one V3V3_CLK net so any bypass cap on that net serves all of them; physical placement (closest to X1 vs. the buffers) is a layout-phase concern, noted in code comments. |
| CG3 | 74LVC1G34 A/Y pin access | Connect by name (`"A"`/`"Y"`) / by pin number | **By pin number** (`u16[2]`, `u16[4]`) | The installed KiCad symbol `74xGxx:74LVC1G34` reports pins 2 and 4 with generic name `~` (not `A`/`Y`) — connecting by name raised `TypeError` (`+=` on `None`). Verified by instantiating the part standalone and printing `pin.num, pin.name`. Pin 2 = A (input), pin 4 = Y (output) per the datasheet summary's pinout table, confirmed by package convention. |

## Carried forward

- **V3V3_CLK must get `.drive = POWER`** set on the source side (wherever `power_analog`/
  FB6 hands off V3V3_CLK), or the top-level ERC will show "insufficient drive current"
  warnings for X1/U16/U17's VCC pins — this block is a consumer only.
- Decoupling C22-C24 assumed sufficient per sourced BOM (see CG2) — if the assembler's
  full-circuit ERC or a later review wants stricter per-IC decoupling, that requires a BOM
  change (new part rows), which is out of this block's scope to invent.
- `clk_10m_xo` (internal fan-out net) and the `clk_10m` parameter net will be merged by
  SKiDL's net-merge-on-connect behavior (seen as an ERC INFO/WARNING "Merging two named
  nets" in isolated testing) — this is expected/benign, not an error.
- Assumed `fpga_core`'s U9 GBIN pin is a high-impedance clock input requiring no additional
  buffering beyond the R10 series termination — matches net_plan.md's stated topology;
  not independently re-verified against the iCE40 datasheet summary by this block (out of
  scope — `fpga_core`'s coder owns that pin).

## Escalation

none
