---
phase: 05_blocks/afe_input
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-22T22:45:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 handoff — block `afe_input` (instantiated ×2)

## Decisions

1. **SIGNATURE CHANGED — `tag` → `ch`.** As written:
   `afe_input(v_att, va_pos, va_neg, gnd, ch)`. Same forced rename the `afe_driver`
   coder hit: SKiDL's `@SubCircuit` pops `tag=` out of kwargs (`skidl/node.py`
   `Node.__call__`) for its own hierarchy name, so a parameter literally named `tag`
   can never be filled by keyword. `ch` takes `'A'`/`'B'`, no default, `ValueError`
   otherwise (a default would give both instances 1xx refs and corrupt the netlist).
2. **Driven by this block:** `v_att` (CHA_ATT / CHB_ATT), high-Z, 82.6 kΩ source.
   **Sensed only:** `va_pos`, `va_neg`, `gnd`. **Bidirectional:** none.
   `CHA_IN`/`CHB_IN` (BNC centre → divider top) are block-internal; J1/J2 live here.
3. **`Diode:BAV19` (sourced symbol) is unusable and was replaced by `Diode:BAV99`** —
   see § Carried forward, the one BOM-vs-code drift in this block. `BAV19` is a 2-pin
   DO-35 *single* diode; it cannot sit on the sourced 3-pad SOT-23 footprint and cannot
   clamp to two rails. `Diode:BAV99` is the SOT-23 series-double-diode pinout, which is
   the family BAV199 belongs to (`datasheets/BAV199_SUMMARY.md`).
4. **Clamp orientation is explicit, not chain-derived**, and taken from the BAV99
   symbol *geometry*, because its pin names are junk (`K`,`A`,`K` for a series pair):
   pin 1 = anode D1, pin 3 = common (K1/A2), pin 2 = cathode D2; conduction 1→3→2.
   Wired pin 3 → `v_att`, pin 1 → `va_neg`, pin 2 → `va_pos`, giving a tap clamped to
   ≈ (VA_NEG − Vf) … (VA_POS + Vf) (SPEC I3, design_risks R-10).
5. **Compensation caps placed per the divider math, not as decoupling.** C101/C201
   (15 pF) sits **across R101/R201**, `CH*_IN` ↔ `CH*_ATT`; C102/C202 (130 pF) and
   C103/C203 (15 pF) go tap → GND. 910k·15p = 13.65 µs ≈ 90.9k·150p = 13.64 µs with the
   architect's 5 pF node stray, so attenuation is flat; 15p ∥ 150p = 13.6 pF sets the
   input capacitance (~17.6 pF with strays) — SPEC I2, with 910k+90.9k = 1.0009 MΩ.
6. 910k (not the architect's 909k) is the sourcing substitution already decided in
   `03_sourcing.md` — ratio 11.0091. Not re-litigated here.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/afe_input.py` | The `afe_input` @SubCircuit — J1/J2, R101/R102/R201/R202, C101-C103/C201-C203, D101/D201 | Assembling the circuit |

## Next phase must

Addressed to **skidl-assembler**:

1. Emit exactly these two calls (`ch=`, **not** `tag=`, selects the channel; `tag=` is
   still the SKiDL hierarchy tag and should still be passed):
```python
afe_input(v_att=CHA_ATT, va_pos=VA_POS, va_neg=VA_NEG, gnd=GND, ch='A', tag='afe_input_a')
afe_input(v_att=CHB_ATT, va_pos=VA_POS, va_neg=VA_NEG, gnd=GND, ch='B', tag='afe_input_b')
```
2. `VA_POS`, `VA_NEG` and `GND` all need **`.drive = POWER`** at the top level — this
   block only consumes them (the clamp ends are passive diode pins).
3. Tell the driver the BOM needs one cell changed before `validate-bom.py` passes:
   row `"D101,D201"` symbol `Diode:BAV19` → `Diode:BAV99`. The code side is right.

## Carried forward

| Item | Note |
|---|---|
| **BOM drift (1 cell): D101/D201 symbol** | `sourced_bom.csv` says `Diode:BAV19` (2-pin DO-35 single diode); the code uses `Diode:BAV99` (3-pin SOT-23 series pair). MPN, value, LCSC and footprint are unchanged. `validate-bom.py` will flag this until the sourcer fixes the BOM cell — do not "fix" it by editing the code back. |
| `net_plan.md` omits `VA_POS` from the clamp | Line 20 lists no D101/D201 on `VA_POS`, and line 22 calls VA_NEG the "clamp cathode-side". Both are wrong for a working two-rail clamp: cathode-to-VA_NEG would forward-bias permanently. The work order's own signature carries `va_pos`, so the clamp is wired to both rails as in Decision 4. Flagged, not silently assumed. |
| BAV199 topology rests on the sourcing/summary claim | `datasheets/BAV199.pdf` is image-only — "series-connected double diode" comes from `BAV199_SUMMARY.md` + the part family, not from extracted datasheet text. If BAV199 were a common-cathode/common-anode variant, the clamp would be wrong. Cheap to confirm visually from the PDF's internal-schematic figure. |
| J1/J2 footprint still unverified | `KH-BNC50-3511_SUMMARY.md` carries this forward: BNC pad spacing not diffed against `Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal`. Layout/reviewer item. |
| Node capacitance budget | D101/D201 junction C and J1/J2 sit directly on `CH*_ATT`; the architect's stray budget for that node is 5 pF total. Guard-ring/layout item, not wiring. |
| No pins left NC | Every pin of J1/J2 and D101/D201 is connected. |

## Do not redo

- The `tag` → `ch` rename (SKiDL semantics, same as `afe_driver`).
- The 910k-for-909k substitution and the 11.0091 ratio (sourcing, already decided).
- Compensation cap placement/values — they are the flat-attenuator condition, not decoupling.

## Receipt

- Block `afe_input`: 14 parts across 2 instances (7 each), 8 nets in a two-instance
  smoke test; all 14 refs unique and exactly as assigned (J1/J2, R101/R102/R201/R202,
  C101-C103/C201-C203, D101/D201).
- `py_compile` OK; instantiation smoke test OK; all footprint strings resolve.
- BOM cross-check: 14/14 ref/value/footprint triples match `sourced_bom.csv`;
  **1 symbol-column drift** (D101/D201, § Carried forward).
- Signature changed: **yes** — `tag` → `ch`.
