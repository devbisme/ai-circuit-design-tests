---
phase: 05_blocks/adc_channel
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Wrote `circuits/dual_adc_usb/adc_channel.py`, one parameterised `@subcircuit` covering
  both ADC channels (A and B) via an added `ch='A'|'B'` argument.
- Implements the AD9235BRUZ-20 datasheet-phase strapping exactly: SENSE→AGND (2.000 Vpp
  span), VREF/REFT/REFB bypass-only (never driven/loaded), MODE→AGND (offset binary,
  DCS off), PDWN driven externally by the FPGA.
- Locally instantiated the VIN− 1.500 V bias divider (R132/R133 or R232/R233, 1.8k/1.5k
  off V3V3_A) since this block's signature has no REF2V5 net — see Decisions.
- DRVDD isolated from V3V3_D via FB10/FB20 with local decoupling on the ADC side.
- Compiled clean, footprint-validated clean, and instantiated both channels standalone
  (58 parts, 66 nets, zero ref collisions).

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/adc_channel.py | `adc_channel()` subcircuit, instantiated once per channel by the assembler | skidl-assembler |

## Key facts for the next phase

- **FINAL function signature (differs from the work order — READ THIS):**
  `adc_channel(adc_in, adc_vinn, adc_clk, pdwn, v3v3_a, v3v3_d, gnd, data, otr, ch='A')`
  — identical to the work order's signature PLUS one added keyword-only-by-convention
  parameter `ch` (`'A'` or `'B'`, default `'A'`). The assembler MUST pass `ch='A'` for
  channel A and `ch='B'` for channel B; without it both instances collide (default is A).
- Call as: `adc_channel(adc_a_in, adc_a_vinn, clk_adc_a, adca_pdwn, v3v3_a, v3v3_d, gnd, adca_d, adca_otr, ch='A')`
  and again with the `_b`/`B` nets and `ch='B'`.
- All parameters are plain `Net` objects except `data`, which must be a 12-bit SKiDL
  `Bus` (`ADCA_D[11:0]` / `ADCB_D[11:0]`), MSB-first not required — bit `data[i]` wires
  to ADC pin `Di`.
- `adc_vinn` is **driven by this block** (the 1.500 V divider lives inside
  `adc_channel`), not by `power_analog` — do not also drive it from elsewhere or you'll
  get a net conflict.
- `pdwn` and `adc_clk` are **inputs this block only consumes** — the assembler/other
  blocks (fpga_core, clock_gen) must drive them; no `.drive = POWER` needed since they're
  logic, not power nets.
- Ref designators used, per instance: `U110`/`U210` (AD9235BRUZ-20), `FB10`/`FB20`
  (ferrite bead), `R120`–`R133`/`R220`–`R233` (14 resistors: 12×100Ω data damping +
  2×divider), `C120`–`C132`/`C220`–`C232` (13 caps: 5×AVDD group, 2×DRVDD group,
  6×reference/VINN group). Matches the work order's allocation exactly.
- Footprints used (already `.pretty`-stripped): `Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm`,
  `Resistor_SMD:R_0402_1005Metric`, `Capacitor_SMD:C_0402_1005Metric`,
  `Capacitor_SMD:C_0603_1608Metric`, `Capacitor_SMD:C_0805_2012Metric`,
  `Inductor_SMD:L_0603_1608Metric`.
- Part lookup: `Part('lib/dual_adc_usb.kicad_sym', 'AD9235BRUZ-20', ref=..., tool=KICAD9, ...)`.

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| B1 | How to parameterise the two-channel instantiation | Duplicate the file per channel / add a `ch` suffix parameter | **Added `ch='A'\|'B'` parameter** (per work-order instruction) | Work order explicitly required a single parameterised file; refs/nets derived from `ch` to avoid collisions |
| B2 | VIN− 1.500 V bias source | Tap REFT/REFB directly (datasheet forbids — degrades linearity) / reuse power_analog's R7/R8 0.5V divider (wrong node, wrong voltage) / new dedicated divider off REF3025 (datasheet's stated preference, but no REF2V5 net exists in this block's signature) / build the divider locally off V3V3_A | **Build locally off V3V3_A** (R132/R133 or R232/R233, 1.8k/1.5k) | The work order's function signature and interface-nets list (fixed by the architecture/sourcing phases) has no REF2V5 parameter for this block, but it does allocate exactly 2 spare resistors beyond the 12 data dampers in my ref range (R120–R133 = 14, not 12) — strong signal the divider belongs here. 1.8k/1.5k off 3.3V gives exactly 1.500V. Heavy decoupling (2×1uF+1×10uF per the datasheet's C_ref budget) mitigates the slightly-higher source impedance vs. tapping a dedicated 2.5V reference. |
| B3 | AVDD decoupling cap placement | 1 cap per physical AVDD pin (2 pins → 2 caps) / follow sourced BOM's stated qty (4×100nF) even though the part has only 2 AVDD pins | **Follow BOM qty (4×100nF + 1×10uF), all on the shared AVDD net** | Both AVDD pins are the same net in the schematic (SKiDL doesn't distinguish per-pin decoupling location electrically) — qty-4 redundant bypass satisfies the sourced BOM's part count without misrepresenting the topology |
| B4 | OEB pin tie-off (net_plan.md mentions "U14/U15 OEB → GND") | Add an OEB pin tie to GND per net_plan / omit since the pin doesn't exist | **Omit** | The datasheet-phase pin table (28 pins, all 1–28 accounted for, cross-checked against the installed project-local symbol) has no OEB pin on this TSSOP-28 package — net_plan's mention is a stale carryover from before the datasheet phase resolved the actual pinout. Tying a nonexistent pin is not possible in SKiDL; flagging here instead of silently dropping it. |
| B5 | OTR damping | Route through a 13th "damping" resistor like the data bus / connect directly | **Connect directly** | Sourced BOM's `R_damp` is qty-12, explicitly sized for the 12-bit data bus only; OTR is a single status flag with no allocated resistor |

## Carried forward

- **Assumes upstream `afe_channel` provides `adc_in` already series-damped/filtered**
  (R_s 33Ω + C_s 22pF, per net_plan.md and the sourced BOM's block-5 allocation) — this
  block does NOT add its own R_s/C_s; those parts and refs belong to `afe_channel`
  (1xx/2xx range), not `adc_channel`.
- **Assumes `power_analog`/assembler top level does not also try to drive
  `ADC_<X>_VINN`** — this block drives it locally (see Decision B2). If a future revision
  routes a REF2V5 net into this block instead, the local divider must be removed to avoid
  a net conflict.
- **Decoupling for `v3v3_a`/`v3v3_d` at the rail-entry point (bulk caps, regulator
  output) is assumed to be `power_analog`/`power_digital`'s responsibility** — this block
  only provides the local/at-the-IC decoupling listed above.
- MODE pin strap confidence: datasheet summary flags AGND=default as "moderate
  confidence" (multi-level strap table not independently re-verified) — carried forward
  from the datasheet phase, not re-resolved here.
- Bit-order of D0(LSB)→D11(MSB) across the physical pin diagram is the standard ADI
  convention per the datasheet summary but was not pin-by-pin independently quoted —
  carried forward as a pre-layout verification item, not ERC-visible.

## Do not redo

- AD9235BRUZ-20 part identity, footprint (`Package_SO:TSSOP-28_4.4x9.7mm_P0.65mm`), and
  project-local symbol (`lib/dual_adc_usb.kicad_sym`, 28 pins, verified) — settled in
  sourcing/datasheets phases.
- SENSE/REFT/REFB/VREF strapping topology and MODE/PDWN default ties — settled in
  `datasheets/AD9235BRUZ-20_SUMMARY.md`, implemented verbatim here.
- Passive footprints (0402/0603/0805 resistor/cap families, `L_0603_1608Metric` ferrite
  bead) — settled in `sourcing/sourced_bom.md` block 6.

## Receipt (build verification)

- `python -m py_compile circuits/dual_adc_usb/adc_channel.py` → OK.
- `validate-footprints.py circuits/dual_adc_usb/adc_channel.py` → all 15 distinct
  footprint uses valid.
- Standalone instantiation of both `ch='A'` and `ch='B'` in one circuit → 58 parts,
  66 nets, ref designators exactly `U110/U210, FB10/FB20, R120–R133/R220–R233,
  C120–C132/C220–C232` with zero collisions.

## Escalation

none
