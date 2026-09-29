---
phase: 05_blocks/afe_buffer
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-23T13:30:00Z
status: complete
revision: 2
next_phase: 05_coding
---

# Phase 5 handoff — block `afe_buffer` (instantiated ×1)

## Decisions

1. **Signature UNCHANGED, as written:**
   `afe_buffer(cha_att, chb_att, cha_buf, chb_buf, va_pos, va_neg, gnd)`.
   One AD8066 carries both channels, so this block is called **once**, not per-channel.
2. **Driven by this block:** `cha_buf`, `chb_buf` (op-amp outputs → `afe_driver`).
   **Sensed only:** `cha_att`, `chb_att`, `va_pos`, `va_neg`, `gnd`.
   **Bidirectional:** none. No block-internal nets.
3. **U1 uses the generated symbol `Part('dual_adc_usb', 'AD8066ARZ-R7')`** — pins
   addressed by number against ADI's verified pinout: 1 VOUT1 · 2 −IN1 · 3 +IN1 ·
   4 −VS · 5 +IN2 · 6 −IN2 · 7 VOUT2 · 8 +VS. The JLC/EasyEDA pinout rejected in
   `04_datasheets.md` decision 3 (5 of 8 pins, no second channel) was not consulted,
   and no stock-library AD8066 was searched for.
4. **Followers use a direct output→−IN short, no feedback resistor** — `net_plan.md`
   CH*_BUF says so explicitly, and at G=1 a resistor only makes a pole against the
   JFET input capacitance.
5. **REVISED rev.2 — rail bypassing is now 3 caps per rail.** `C15` = 100 nF at U1
   pin 8 (+VS) and `C16` = 100 nF at U1 pin 4 (−VS), each to `GND`, **plus** the
   pre-existing C11/C12 (1 µF + 10 µF on `VA_POS`) and C13/C14 (on `VA_NEG`).
   Rev.1 asserted "the BOM assigns U1 none" — that read the **rev.2** BOM. Sourcing
   rev.3 funded C15/C16 (`sourced_bom.csv` row 67, CL05B104KO5NNNC / C1525, 0402) in
   response to rev.1's own flag, and `net_plan.md` rev.3 mandates them. Now wired.
   **One cap per rail to GND, NOT a single VA_POS↔VA_NEG cap:** on a bipolar-supply
   op amp each output half returns its HF current through the rail sourcing or
   sinking it, so each rail needs its own low-inductance path to the ground plane.
   A rail-to-rail cap ties the rails together at HF and references neither to the
   ground the load returns to.
6. ±5 V dual-supply operation. At the ±55 V input limit the tap reaches ±5.0 V — inside
   abs-max, outside the linear CM range; the buffer saturates and recovers. That is the
   architect's accepted SPEC I3 behaviour (design_risks R-10), not a defect to design out.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/afe_buffer.py` | The `afe_buffer` @SubCircuit — U1 (AD8066), C11-C16 | Assembling the circuit |

## Next phase must

Addressed to **skidl-assembler**:

1. Emit exactly this one call:
```python
afe_buffer(cha_att=CHA_ATT, chb_att=CHB_ATT, cha_buf=CHA_BUF, chb_buf=CHB_BUF,
           va_pos=VA_POS, va_neg=VA_NEG, gnd=GND, tag='afe_buffer')
```
2. `VA_POS`, `VA_NEG`, `GND` need **`.drive = POWER`** at the top level — U1's +VS/−VS
   are `power_in` pins and this block only consumes the rails.
3. `CHA_ATT`/`CHB_ATT` come from `afe_input`; `CHA_BUF`/`CHB_BUF` go to `afe_driver`
   (`v_buf=`). Nothing else may drive `CHA_BUF`/`CHB_BUF`.
4. No BOM change from this block — 7/7 refs (U1, C11–C16), values and footprints
   match `sourcing/sourced_bom.csv` exactly. Nothing to change in the call you
   already emit: C15/C16 are block-internal, on `va_pos`/`va_neg`/`gnd`.

## Carried forward

| Item | Note |
|---|---|
| ~~No 100 nF on U1~~ | **CLOSED at rev.2.** C15/C16 are now fitted; both rails meet the 100 nF + 1 µF + 10 µF convention. No refdes or BOM change was needed — both were already funded. |
| C15/C16 are placement-critical | They are the only HF bypass on a 145 MHz-GBW part. The layout must keep each within a few mm of its own supply pin with a direct via to the ground plane; the 1 µF/10 µF may sit further out. |
| `VA_NEG` is a negative rail | C13/C14 sit VA_NEG→GND, which is the correct orientation, but they are non-polarised MLCCs (`Device:C`) — no polarity risk. Reviewer should not "flip" them. |
| Input CM range vs overload | See Decision 6 / design_risks R-10 — saturation at overload is accepted, not fixed here. |
| No pins left NC | All 8 U1 pins are connected. |

## Do not redo

- The AD8066 pinout or its symbol source (`04_datasheets.md` decision 3 — do not
  regenerate from JLC/EasyEDA, do not search stock libraries).
- The resistor-less unity-gain feedback (net_plan.md's explicit instruction).
- U1's single-source `[CRIT]` part choice — 6 pA Ib is what makes the 1 MΩ divider work.

## Receipt

- Block `afe_buffer` rev.2: **7 parts** (U1, C11–C16), 8 nets; all refs unique and
  exactly as assigned. Only change vs rev.1: C15/C16 added.
- `py_compile` OK; footprint strings all resolve; full-circuit run: **0 ERC errors,
  0 ERC warnings**.
- BOM cross-check: `validate-bom.py` **exit 0** — the C15/C16 "in BOM but not in
  circuit" mismatch is closed. `sourced_bom.csv` was **not** edited.
- Signature changed: **no** — `afe_buffer(cha_att, chb_att, cha_buf, chb_buf, va_pos,
  va_neg, gnd)` is unchanged; the assembler's existing call still applies verbatim.
