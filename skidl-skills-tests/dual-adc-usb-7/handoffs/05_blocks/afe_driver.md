---
phase: 05_blocks/afe_driver
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-22T22:05:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 handoff — block `afe_driver` (instantiated ×2)

## Decisions

1. **SIGNATURE CHANGED — one parameter renamed. `tag` → `ch`.** As written:
   `afe_driver(v_buf, adc_inp, adc_inn, adc_cm, p3v3a, gnd, ch)`.
   Reason, not negotiable: SKiDL's `@SubCircuit` decorator **consumes** a `tag=` keyword
   for its own hierarchy naming — `Node.__call__` (skidl/node.py:164-181) pops `"tag"`
   out of `kwargs` before calling the wrapped function. A parameter named `tag` can
   therefore never be filled by a keyword call; the call would raise
   `TypeError: missing required argument 'tag'`. `ch` takes `'A'` or `'B'` and anything
   else raises `ValueError` (no default — a default would silently give both instances
   1xx refs and corrupt the netlist instead of failing).
2. **Driven by this block (outputs):** `adc_inp`, `adc_inn`.
   **Sensed only (inputs):** `v_buf`, `adc_cm`, `p3v3a`, `gnd`. **Bidirectional:** none.
3. **Polarity crossing implemented as net_plan.md specifies — do not "fix" it.** FDA
   OUT+ (U2.4) leg → `adc_inn`; OUT− (U2.5) leg → `adc_inp`. The stage inverts; the
   cross at the ADC undoes it.
4. **Filter values are the architect's verbatim, per leg:** 100 Ω – 3.3 µH – 680 pF –
   5.6 µH – 680 pF, then 22 Ω series to the ADC pin. Every value/footprint string is
   copied from `sourcing/sourced_bom.csv`; nothing was rounded or substituted. The
   ±5 % L / ±2 % C0G parts are load-bearing for SPEC F8 (−3 dB 4.23 MHz, −41.8 dB
   10 MHz) — a looser substitution misses both.
5. **AAF shunt caps return to GND, not to `ADC_CM`.** `ADC_CM` carries only U2/U3 VOCM
   and C119/C219 — it tolerates ±2 mA and no resistive load (net_plan.md).
6. **THS4521 PD polarity is now CONFIRMED — closes the open row in
   `04_datasheets.md` § Carried forward.** TI's own pin table
   (`datasheets/THS4521IDR.pdf`): *"PD = logic low puts device into low-power mode.
   PD = logic high or open for normal operation."* Pin 7 is tied to `P3V3A` = enabled.
7. **U2/U3 pins addressed by number, not name.** The symbol's names (`+`, `-`,
   `V_{S+}`, `~{PD}`, `V_{OCM}`) contain regex metacharacters unsafe in SKiDL name
   lookup. Numbering: 1 VIN− · 2 VOCM · 3 VS+ · 4 VOUT+ · 5 VOUT− · 6 VS− · 7 PD ·
   8 VIN+.
8. **BAT54S orientation is explicit, not chain-derived.** `Diode:BAT54S` is a series
   pair: pin 1 = A, pin 2 = K, pin 3 = COM. Wired COM → signal node (CH*_F3P/N),
   A → GND, K → P3V3A, so the node clamps to ≈ −Vf … P3V3A+Vf.
9. **One function, called twice.** `ch` selects refdes base 100/200 and the net prefix
   `CHA_`/`CHB_`; U-ref is U2 (A) / U3 (B). No duplicated code path.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/afe_driver.py` | The `afe_driver` @SubCircuit — U2/U3, R111-R118/R211-R218, L111-L114/L211-L214, C111-C119/C211-C219, D111-D112/D211-D212 | Assembling the circuit |

## Next phase must

Addressed to **skidl-assembler**:

1. Emit exactly these two calls (note `ch=`, **not** `tag=`, for the channel selector;
   `tag=` is still passed and still means the SKiDL hierarchy tag):
```python
afe_driver(v_buf=CHA_BUF, adc_inp=ADC_INAP, adc_inn=ADC_INAN, adc_cm=ADC_CM,
           p3v3a=P3V3A, gnd=GND, ch='A', tag='afe_driver_a')
afe_driver(v_buf=CHB_BUF, adc_inp=ADC_INBP, adc_inn=ADC_INBN, adc_cm=ADC_CM,
           p3v3a=P3V3A, gnd=GND, ch='B', tag='afe_driver_b')
```
2. `P3V3A` and `GND` need **`.drive = POWER`** at the top level — this block only
   consumes them (U2/U3 VS+/VS− are `power_in`).
3. `ADC_CM` is driven by `adc_dual` (U4 CM output) and only sensed here. Do not add any
   resistive load to it anywhere in the assembly.
4. No BOM change is required by this block — 48/48 refs, values and footprints match
   `sourcing/sourced_bom.csv` exactly (checked programmatically, 0 disagreements).

## Carried forward

| Item | Note |
|---|---|
| Clamp rail reference | D111/D112/D211/D212 clamp to `P3V3A`, which also feeds U4 AVDD. `P3V3A` is not listed as a connected ref for these diodes in `net_plan.md` (that row names only the signal node), nor is U2/U3 PD listed — both additions are required for a working clamp/enable and are flagged rather than silently assumed. Schottky Vf at clamp currents (~0.2–0.3 V) keeps the node inside AVDD+0.3 V; at the 0.4 V @10 mA datasheet point it is marginal (3.7 V vs 3.6 V), which is design_risks R-10's own accepted margin. |
| Headroom at the window edge | With ÷11.0091 attenuation and diff gain 1.100, each ADC pin sits at CM ±0.5 V. If `ADC_CM` is the ADS5231's nominal ~1.5 V, that is exactly 1.0–2.0 V — no margin against gain or CM drift. Reviewer should confirm the measured CM before assuming worst-case compliance. This is the architect's gain plan, unchanged. |
| ADC_CM bypass | C119/C219 (100 nF each) are this block's; `adc_dual` deliberately provides none. |
| No pins left NC | Every U2/U3 pin is connected. |

## Do not redo

- The FDA-out → ADC-in polarity crossing (net_plan.md's explicit "do not fix this").
- Filter topology and values — the architect's computed 4-pole LC; values are BOM-verbatim.
- THS4521 PD polarity — resolved from TI's datasheet this phase (Decision 6).
- The `tag` → `ch` rename — forced by SKiDL semantics, not a preference.

## Receipt

- Block `afe_driver`: 48 parts across 2 instances (24 each), 29 nets in an isolated
  two-instance smoke test; all 48 refs unique and exactly as assigned.
- `py_compile` OK; instantiation smoke test OK; 6/6 footprint strings resolve.
- BOM cross-check: 48/48 ref/value/footprint triples match `sourced_bom.csv`, 0 drift.
- Signature changed: **yes** — `tag` → `ch` (Decision 1).
