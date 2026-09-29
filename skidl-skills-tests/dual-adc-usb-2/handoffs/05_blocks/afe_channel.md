---
phase: 05_blocks/afe_channel
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-09
---

## Receipt

- Wrote `circuits/dual_adc_usb/afe_channel.py`: 20:1 compensated passive attenuator + 3
  op-amp signal chain (A1 buffer, A2 Sallen-Key, A3 inverting MFB + level-shift) per
  channel, parameterised on `ch='A'|'B'`.
- Synthesized the deferred 4th-order Butterworth filter R/C values myself (arithmetic in
  the file's docstring/comments): Section 1 (A2, Sallen-Key, unity gain) R=246 Ω,
  C1=120 pF, C2=140 pF → fc=4.993 MHz, Q=0.5400 (target 5.000 MHz / 0.5412). Section 2
  (A3, MFB, gain −2) R1=768 Ω, R2=1536 Ω, R3=300 Ω, C1=220 pF, C2=10 pF → fc=4.999 MHz,
  Q=1.307 (target 5.000 MHz / 1.3065). Both within ~0.2% of the required Butterworth pole Qs.
  Component counts: 5 filter resistors + 4 filter caps (sourced BOM's row estimated ×8/×5
  — its own count was a placeholder; see Decisions).
- Resolved the BAV99 common-anode clamp ambiguity flagged in
  `datasheets/BAV99_SUMMARY.md` by hand nodal analysis: a common-anode pair cannot
  symmetrically clamp one node to two opposite-polarity rails (the low-side diode would
  be permanently forward-biased). Implemented high-side-only clamp (pin2→signal,
  pin1→V5_A), pin3 left NC.
- Resolved the `adc_vinn` parameter ambiguity flagged in the work order: this block
  accepts it (fixed signature) but does **not** connect anything to it — `adc_channel`
  already drives/decouples it locally, and this block's own level-shift is injected
  separately at A3's + input via `vref_0v5`.
- Self-check: both `ch='A'` and `ch='B'` instances built together in one Circuit with
  zero duplicate refs (56 total parts) and `ERC()` reports **0 errors** (18 warnings, all
  expected — power rails, `VREF_0V5_<X>`, and `ADC_<X>_VINN` are driven by sibling blocks
  not present in this isolated test).
- `.claude/scripts/validate-footprints.py` does not exist in this project (checked); every
  footprint used was instead verified to exist on disk directly under
  `/usr/share/kicad/footprints` (11 distinct footprint files, all present — see Receipt
  of the coding session, or re-run the `find`/`ls` check in this file's Decisions row).

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|-------------------|
| circuits/dual_adc_usb/afe_channel.py | The `afe_channel` SubCircuit block, instantiated ×2 by the assembler | skidl-assembler |

## Key facts for the next phase

- **Function signature is UNCHANGED from the work order** — no adjustment needed:
  `afe_channel(bnc_sig, gnd, v5_a, vn5_a, v3v3_a, vref_0v5, adc_in, adc_vinn, ch='A')`.
  The assembler must call it by keyword exactly as in the work order, e.g.
  `afe_channel(bnc_sig=BNC_A_SIG, gnd=GND, v5_a=V5_A, vn5_a=VN5_A, v3v3_a=V3V3_A, vref_0v5=VREF_0V5_A, adc_in=ADC_A_IN, adc_vinn=ADC_A_VINN, ch='A')`
  and the same with the `_B` nets and `ch='B'` for the second instance.
- **Inputs (driven elsewhere, this block only loads them):** `bnc_sig` (from the BNC
  jack itself — wait, no: `bnc_sig` is actually driven BY this block's own J2/J3 pin —
  see below), `gnd`, `v5_a`, `vn5_a`, `v3v3_a` (all from `power_analog`), `vref_0v5`
  (from `power_analog`'s REF3025/divider network — **the assembler does not need to set
  `.drive = POWER`**, `power_analog` already drives it as a real net).
  Correction: `bnc_sig` is the **external-world input** — J2/J3's center pin is wired to
  it inside this block, so it is effectively board-edge-driven (off-board), not driven by
  any other SKiDL block. No `.drive` override needed at the top level.
- **Outputs this block drives:** `adc_in` (ADC_<X>_IN — drives `adc_channel`'s VIN+
  through this block's R_s/C_s damper).
- **Net this block receives but does NOT drive or load:** `adc_vinn` (ADC_<X>_VINN) —
  accepted as a parameter only because the fixed signature requires it; zero pins are
  attached to it inside this function. `adc_channel` is the sole driver.
- Internal nets created (not part of the interface, safe for the assembler to ignore):
  `ATTN_<X>_MID`, `ATTN_<X>`, `AFE_<X>_BUFIN`, `AFE_<X>_1`, `AFE_<X>_2`, `AFE_<X>_OUT`,
  `AFE_<X>_SK_NA`, `AFE_<X>_SK_NB`, `AFE_<X>_MFB_NA`, `AFE_<X>_MFB_NB`.
- Parts placed per instance (26 total: 1 connector, 2 ICs, 2 diodes, 10 resistors, 13
  caps — R110–R115/R210–R215 from the work order's allocation are unused, intentionally,
  by this synthesis).

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|
| B1 | BAV99 clamp wiring (common-anode symbol, only 1 BAV99/channel available) | (a) anode-common@signal, both cathodes to V5_A/VN5_A — fails: low-side diode permanently forward-biased in normal operation (hand nodal analysis: conducts whenever signal > V− + Vf ≈ −4.3 V, always true) (b) anode-common@signal, cathode1→V5_A, cathode2→NC — high-side only, physically correct (c) anode-common@GND — arbitrary mid-rail clamp, doesn't match net_plan intent | **(b) high-side only, pin3 NC** | Only physically valid option with this package's pinout. design_risks.md R-12 already shows the attenuator node never exceeds ±2.0 V at the ±40 V [SOFT] fault limit — well inside both ±5 V rails — so the clamp is a backup for a much larger fault, and asymmetric backup coverage is an acceptable residual (flagged below) |
| B2 | `adc_vinn` parameter — what does afe_channel do with it | (a) build a second local divider off v3v3_a, duplicating adc_channel's own | (b) route it to A3's output somehow | (c) accept param, connect nothing | **(c)** | adc_channel (already written) fully drives and decouples ADC_<X>_VINN locally from V3V3_A; this block's own level-shift (F3 arithmetic) is injected independently at A3's + input via `vref_0v5`. Duplicating a driver on the same net would be an ERC conflict (two drivers) |
| B3 | Filter topology for A2 (Sallen-Key) and A3 (MFB) | equal-R-equal-C Sallen-Key (fixes Q=0.5 regardless of components, can't hit 0.5412) / equal-R unequal-C Sallen-Key / MFB with non-inverting input grounded then a 4th op-amp for level shift / MFB with non-inverting input biased at vref_0v5 (no extra part) | **Equal-R unequal-C Sallen-Key for A2; MFB with biased +input for A3** | Equal-R-equal-C is over-constrained (Q fixed at 0.5, not 0.5412). Biasing A3's +input at vref_0v5 gets the DC level shift for free, matching ic_selection.md F3 exactly and avoiding a 4th op-amp stage (which design_risks.md R-06 explicitly forbids) |
| B4 | C_trim nominal value vs. its 2–10 pF part range | Compute C_trim to match R_top·C_top = R_bot·C_bot across the WHOLE top leg (950 kΩ), or just R_top2 (per net_plan's literal wording) | **R_top2 only, per net_plan.md's literal topology** | net_plan.md section 3 explicitly writes the topology as "R_top2 + C_trim → node", i.e. C_trim parallels R_top2 specifically, not the full top leg. Computed nominal ≈18.9 pF is ABOVE the specified 2–10 pF trimmer range — flagged as a residual open item, not silently fixed (see Carried forward) |
| B5 | Footprint validation | Run `.claude/scripts/validate-footprints.py` (per template instructions) / manual verification | **Manual** — script does not exist anywhere in this project (`.claude/` directory itself is absent) | Verified all 11 distinct footprint strings used in this file resolve to real `.kicad_mod` files under `/usr/share/kicad/footprints` by direct filesystem check |

## Carried forward

- **C_trim range mismatch (residual of design_risks.md R-05):** the nominal trim point
  computed from R_top2·C_trim = R_bot·C_bot (49.9 kΩ × 180 pF / 475 kΩ ≈ 18.9 pF) exceeds
  the sourced Voltronics JR300's 2–10 pF range. R-05 already calls attenuator compensation
  an open, per-unit bring-up trim step — this just means the trimmer part or C_bot's value
  may need revisiting on the bench. Not fixed here; flagged for bring-up/layout per R-05's
  own scope.
- **OPA836 PD pin polarity** (datasheets/OPA836IDBVR_SUMMARY.md flags this as
  low-confidence): tied to VS+ (v3v3_a) assuming active-low = enabled. If the real part is
  active-high, PD tied high would disable the amplifier. Verify against the TI datasheet
  before board spin (same flag the datasheet phase already raised, carried forward
  unresolved).
- **BAV99 asymmetric clamp** (Decision B1): only high-side (V5_A) overvoltage protection
  is implemented; low-side is unprotected by this diode (relies on the attenuator's
  inherent division per R-12). If bench testing shows a need for symmetric protection, add
  a second discrete diode (not present in the current ref allocation — would need an
  escalation to sourcing for one more part).
- **BNC jack (J2/J3) mechanical verification** — unresolved through sourcing and
  datasheet phases (Amphenol 031-6575, no dimensional drawing obtained anywhere in the
  pipeline). Still open; this block only wires it electrically.
- **Assumption on neighbouring blocks:** `power_analog` must decouple/drive `vref_0v5`
  itself (per net_plan.md section 1, R7/R8/1µF-to-GND already scoped there) — this block
  does not add any decoupling on `vref_0v5`, only loads it at A3's + input.
- Filter component counts (5 R + 4 C) are lower than the sourced BOM's placeholder
  estimate (R_filt ×8, C_filt ×5) — expected, since the sourced BOM explicitly deferred
  exact synthesis to this phase; not a discrepancy to reconcile.

## Do not redo

- 20:1 / ×2 / CM 1.500 V / span 0.5–2.5 V attenuation-and-gain plan (architecture-fixed).
- 4th-order Butterworth at fc=5.0 MHz split Q=0.5412/1.3065 (architecture-fixed; only the
  R/C values were this phase's job).
- A3 on +3V3_A single supply (architecture Decision A7 — ADC protection, not a preference).
- Polarity inversion — corrected digitally downstream, not with a 4th op-amp here.
- Attenuator top-leg resistors at 0805 (design_risks.md R-12).
- BAV99/OPA836/AD8066 MPNs and footprints (sourced_bom.md, datasheet phase — used verbatim).

## Escalation

none
