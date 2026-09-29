---
phase: 05_blocks/analog_frontend
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-22T00:00:00Z
status: complete
revision: 3
next_phase: 05_coding
---

# Block handoff — analog_frontend

<!-- rev.3: narrow fix pass against erc_report.md rev.2 MEDIUM-1 (attenuator
     compensation). One value changed (C101/C201 220pF -> 200pF) and one part added per
     channel (C116/C216, 10 pF). Signature, interface nets and every other decision are
     untouched from rev.2.
     rev.2: narrow fix pass against handoffs/02_architecture.md rev.2 (D-r2.1, D-r2.2)
     and erc_report.md HIGH-1/2/4. Exactly one part definition and two net assignments
     changed. Signature, interface nets, passive values and every other decision below
     are untouched from rev.1. -->

## Decisions

1. **Signature unchanged from the work order:**
   `analog_frontend(ch, bnc_in, avdd, vref_off, vcm_ref, ain_p, ain_n, gnd)`.
   No parameter was renamed. One parameterised file, instantiated twice.
2. **`ch` is the instance selector, `'CH1'` / `'CH2'`** (an int `1`/`2` also works). It
   derives the refdes bank (`b = 100*n` → R100.../R200...), the jack (`J{n+1}` → J2/J3)
   and the internal net prefix (`CH1_…`/`CH2_…`). Nothing else varies between instances.
3. **Direction of each interface net:** `bnc_in` sense-only (input); `ain_p`/`ain_n`
   **driven** by this block (FDA outputs through the 33 Ω kickback resistors);
   `avdd`, `vref_off`, `vcm_ref`, `gnd` **consumed only** — this block never drives them.
4. **THS4521 (U103/U203) is wired entirely by pin number.** Pins 4/5 have empty name
   fields in `Amplifier_Difference:THS4521ID`, and pins 1/8 are named just `-`/`+`.
   Mapping used: 1=VIN−, 2=VOCM, 3=VS+, 4=VOUT+, 5=VOUT−, 6=VS−, 7=PD, 8=VIN+.
5. **PD (pin 7) is tied to `avdd`**, not left floating, per the work order.
6. **The attenuator bottom-leg capacitance returns to `VREF_OFF`, in parallel with
   R101/R201**, not to GND. `net_plan.md` lists only R101 on `VREF_OFF`; the parallel-cap
   reading is the one consistent with the skeleton BOM's "[calc] τ match 20.0 µs both legs".
   **rev.3 — the bottom leg is now 210 pF of fixed capacitance, not 220 pF**, split as
   **C101/C201 = 200 pF** plus a new parallel **C116/C216 = 10 pF**, both C0G 0603 on the
   same two nets (`CHn_ATT`, `VREF_OFF`). Reason (erc_report.md rev.2 MEDIUM-1): R102 does
   not isolate `CHn_BUFIN`'s ~9.4 pF from the divider at the 8.8 kHz compensation corner,
   so C_node sits **across the bottom leg**. Compensating on the fixed part alone gave
   τ_bot = 90.9 k·(220 p + 9.4 p) = 20.85 µs against τ_top = 909 k·22 p = 20.00 µs — a
   +4.27 % mismatch, i.e. a −0.33 dB / −3.7 % gain shelf DC..1 MHz, outside SPEC F12's
   ±2 % across the whole plausible C_node range (−2.4 % at 6 pF, −5.5 % at 14 pF).
   Re-verified arithmetic at 210 pF fixed: τ_bot = 19.94 µs, **−0.27 % residual, +0.25 %
   shelf**, and the 6–14 pF C_node range maps to **+1.7 % … −1.6 %** — inside F12 across
   the range. 210 pF is not an E-series MLCC value, hence the two-part build; C116/C216 is
   also the natural trim refdes SPEC I2 asks for.
7. **D100/D200 (BAV199LT1G) clamp orientation:** pin 3 (`C/A`, the series common node)
   on `CHn_BUFIN`, pin 1 (`A`) to `GND`, pin 2 (`C`) to `avdd`. This gives conduction
   GND→signal on undershoot and signal→rail on overshoot.
8. **Custom footprint built this pass:**
   `footprints/ProjectLocal.pretty/BNC_KH-BNC50-3511_Horizontal.kicad_mod`, referenced as
   `ProjectLocal:BNC_KH-BNC50-3511_Horizontal`. Sourcing left this as ⚠️ CUSTOM FP NEEDED.
9. **rev.2 — D101/D201 moved off `CHn_BNC` and changed part.** The clamp is now on
   `CHn_BUFIN`, behind R102 (1.00 k), and the part is **ESD9L5.0ST5G** (LCSC C82326,
   onsemi, 0.9 pF, SOD-923) instead of the 15 pF ESD9B5.0ST5G. Architecture rev.2
   D-r2.1/D-r2.2. Nothing clamps the BNC node any more: `CH1_BNC` is now exactly
   `J2.1, R100.1, C100.1` (verified in the built circuit). `CH1_BUFIN` is
   `R102.2, D100.3, D101.1, U100.3`, with `D101.2` on `GND`.
10. **rev.2 — D101/D201 polarity is load-bearing and the symbol does not show it.**
   The part is unidirectional: **pin 1 = CATHODE → `CHn_BUFIN`, pin 2 = ANODE → `GND`**.
   Coded as prescribed with `Part('Device', 'D_TVS', …)`. Note for whoever reads the
   schematic: KiCad's `Device:D_TVS` is the *bidirectional* glyph and names its pins
   `A1`/`A2`, so the symbol asserts a polarity that is not the part's. Only the pin
   **numbers** reach the netlist and those are correct, so this is a drawing/review
   hazard, not a netlist defect. `Device:D_Zener` (pin 1 = `K`, pin 2 = `A`, same pin
   numbers, same netlist) is the honest glyph and is explicitly allowed by architecture
   rev.2; I kept `D_TVS` because that is what the work order specified verbatim. A
   one-token change if the schematic reviewer wants the polarity visible.
11. **All `[calc]` values used verbatim except the bottom-leg compensation cap**
   (rev.3, see §6): 909 k / 90.9 k / 22 pF / **200 pF + 10 pF** / 1.00 k /
   147 Ω ×2 / 270 pF / 220 pF / 137 Ω ×2 / 680 pF / 100 pF / 1.00 k ×2 / 1.10 k ×2 /
   33 Ω ×2 / 22 pF. Nothing rounded or substituted.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/analog_frontend.py` | The `@SubCircuit` block, 37 parts / 20 nets per instance (**rev.3**: C101/C201 → 200 pF, C116/C216 added) | Assembling the circuit |
| `footprints/ProjectLocal.pretty/BNC_KH-BNC50-3511_Horizontal.kicad_mod` | J2/J3 custom THT footprint, 4 pads | Footprint validation / PCB layout |

## Next phase must

1. Emit exactly these two calls in `__main__.py` (keyword args, `tag` per instance):

```python
analog_frontend(ch='CH1', bnc_in=CH1_BNC, avdd=V3V3A_AMP, vref_off=VREF_OFF,
                vcm_ref=VCM_REF, ain_p=CH1_AIN_P, ain_n=CH1_AIN_N, gnd=GND,
                tag='afe_ch1')
analog_frontend(ch='CH2', bnc_in=CH2_BNC, avdd=V3V3A_AMP, vref_off=VREF_OFF,
                vcm_ref=VCM_REF, ain_p=CH2_AIN_P, ain_n=CH2_AIN_N, gnd=GND,
                tag='afe_ch2')
```

2. **Set `.drive = POWER` at top level on `GND` and `+3V3A_AMP`** — this block only
   consumes them. If the `power` block's U7 does not present an OUTPUT-drive pin on
   `VREF_OFF` and `VCM_REF`, those two need `.drive = POWER` as well; from this block's
   side they are pure loads.
3. **`CHn_BNC` has no external driver** — J2/J3 is a passive connector symbol. Expect an
   ERC "no driving pin" note on `CH1_BNC`/`CH2_BNC`; that is correct for a signal input
   jack, not a defect.
4. **rev.3 — no assembler-visible change.** Same signature, same interface nets, same
   parameter names. Part count per instance goes 36 → 37 (C116/C216); both new parts land
   on nets this block already owned, so no net is created or removed. The two calls in §1
   above are still exactly right; do not re-emit anything.
   (rev.2: `D101/D201` moved to an internal net only — also assembler-invisible.)
5. Run with `KICAD9_SYMBOL_DIR` including `$PWD/symbols` — J, D_clamp and the TPH2501
   op-amps come from the project library `dual_adc_usb`.

## Carried forward

- **BAV199LT1G pin-3 identity is EasyEDA-sourced, not manufacturer-verified**
  (`datasheets/BAV199LT1G_SUMMARY.md` says so explicitly). If pin 3 is not the series
  common node, the clamp orientation in §3 of the block file is wrong and D100/D200 would
  need re-wiring. No primary source was available to close this; flagged, not guessed
  around.
- **C107–C115 / C207–C215 allocation is mine, not sourcing's.** `sourced_bom.md` groups
  them only under "decoupling generally". Assigned: 100 nF each on U100/U101/U102/U103
  (`C{b+7}`..`C{b+10}`), 10 µF local bulk at U103 (`C{b+11}`), 100 nF `VCM_REF` bypass
  (`C{b+12}`, satisfies `net_plan.md`'s "C-bypass" on that net), 100 nF `VREF_OFF` bypass
  (`C{b+13}`), 10 µF + 100 nF `+3V3A_AMP` block bulk/entry (`C{b+14}`, `C{b+15}`).
  `C{b+16}` (C116/C216) is **not** decoupling — it is the rev.3 attenuator trim cap.
  100 nF → `CL05B104KB54PNC` 0402; 10 µF → `CL21A106KAYNNNE` 0805, both from the BOM's
  generic buckets.
- **BNC footprint hole pattern read from the drawing, verify before fab.**
  Drawing KH-801-0038 Rev B, PCB detail: 2×Ø2.00 legs 10.1 mm apart on one row, 2×Ø0.90
  on a row 5.05 mm away, the right Ø0.90 sitting 5.05 mm from the right Ø2.00 (i.e. on
  the connector axis → that one is the centre contact, pad 1) and the other Ø0.90 2.5 mm
  to its left. Pads 2/3/4 are all GND so any mix-up among them is netlist-harmless, but
  the *geometry* has not been checked against a physical part.
- **C100/C200 is 0402/50 V per `sourced_bom.md`**, while `skeleton_bom.md` asked for
  0603/100 V on the attenuator top-leg compensation cap. Took the BOM verbatim as
  instructed; the voltage-rating discrepancy against a ±10 V (150 V working) input node
  is worth a second look by review.
- **rev.2 — R12 (TVS leakage) is inherited, not closed.** Architecture rev.2 assumes
  ESD9L5.0ST5G leakage at 0.73–2.55 V / ≤85 °C is ≤50 nA. At the 82.6 kΩ source
  impedance seen at `CHn_BUFIN`, the datasheet's 1 µA max (5 V, 150 °C corner) would be
  0.91 V referred to input = 4.5 % FS. Nothing in this block can bound that; it needs a
  leakage-vs-voltage curve from onsemi. A substitute with a worse Ir spec is not safe.
- **rev.2 — R13 (ESD energy on the attenuator mid node) is accepted, not mitigated
  here.** With no clamp on the BNC, a strike couples through C100 into `CHn_ATT` for a
  few nanoseconds before R102 bleeds it into D101. C100/C101 are 100 V C0G and R100 is
  an 0805, which is the conventional scope-front-end compromise.
- **rev.3 — C116/C216's sourcing is not in `sourced_bom.md`.** Both new values were
  supplied with the fix order: 200 pF = `0603CG201J500NT` (LCSC C1649, 43,613 stock) and
  10 pF = `CL10C100JB8NNNC` (LCSC C1634, Samsung, Basic tier, ~1.5 M stock). The block
  file carries only value + footprint, so the netlist is unaffected, but **the BOM needs
  two rows added and the 220 pF row retired** before export.
- **rev.3 — C_node = 9.4 pF is an estimate, not a measurement.** The fix centres the
  compensation on it; if the real node lands outside 6–14 pF, F12 is missed again. C116/
  C216 is the refdes to change, and a ±2 % window corresponds to roughly ±9 pF of C_node.
- No pins are left `NC` in this block. No decoupling is assumed to come from elsewhere —
  every amp rail pin in the block is bypassed locally here.

## Do not redo

- The `[calc]` passive values and the attenuator/AAF/FDA topology — taken verbatim from
  `sourcing/sourced_bom.md` and `architecture/net_plan.md` § "analog_frontend instance
  nets". Do not re-derive them.
- THS4521 pin-number wiring — the empty-name pins 4/5 are a KiCad symbol property, not a
  mistake to be "fixed" by switching to names.
- The `ProjectLocal` BNC footprint — it exists and validates; do not regenerate.
- **rev.3 — the 210 pF total.** It is deliberately 10 pF short of the naive 220 pF; that
  10 pF is C_node. Do not "correct" C101/C201 back to 220 pF, and do not delete C116/C216
  as a stray duplicate.
- **rev.2 — the clamp node.** `CHn_BUFIN`, behind R102. Not the BNC, not `CHn_ATT`
  (there the 90.9 kΩ leg would see 235 pF and compensation breaks outright). And the
  anti-alias filter values do **not** move to absorb R102's 18.9 MHz pole — the low-Cj
  part is what buys F8 back (−3 dB at 4.39 MHz nominal / 4.18 MHz worst case).

## Receipt

- **rev.3 fix pass:** 1 value changed (`C_att_b` 220 pF → 200 pF, C101/C201), 1 part added
  per channel (`C_att_trim`, C116/C216, 10 pF C0G 0603, on `CHn_ATT` / `VREF_OFF`),
  section-2 and docstring comments updated to match. Arithmetic re-derived independently
  before implementing — see §6. Signature, interface nets, every other value: unchanged.
- **rev.3 counts:** 37 parts / 20 nets per instance (74 parts for the two instances).
  `py_compile` OK, footprint validation OK (`Capacitor_SMD:C_0603_1608Metric` already in
  use in this block). Refdes check: C116/C216 sit immediately above the existing
  C100–C115 / C200–C215 banks; the built circuit shows no duplicate and no `_1` suffix.
- **rev.3 full-circuit re-run:** `python3 -m circuits.dual_adc_usb` → **0 ERC errors,
  2 warnings** (the known U5/U6 LDO drive false positives), **243 parts / 187 nets**
  (186 real nets + the `__NOCONNECT` pseudo-net, which is the count convention
  `erc_report.md` uses).
- **rev.2 fix pass:** 1 part definition changed (ESD9B5.0ST5G/SOD-523 →
  ESD9L5.0ST5G/SOD-923, `Device:D_TVS`), 2 net assignments moved (`D101/D201` off
  `CHn_BNC`, onto `CHn_BUFIN` with pin 1 = cathode), docstring updated. Part count,
  net count and signature unchanged.
- Block `analog_frontend` — 1 file, parameterised, instantiated twice.
- 36 parts / 20 nets per instance (72 parts, 33 signal nets + 4 shared for both).
- `py_compile` OK. Smoke-instantiated twice: all refs land exactly on J2/J3,
  U100–U103/U200–U203, R100–R112/R200–R212, C100–C115/C200–C215, D100/D101, D200/D201 —
  zero SKiDL `_1` uniquification, zero collisions.
- `validate-footprints.py` (re-run rev.2): ✓ all 11 distinct footprints valid.
- Signature changed: **no**. Interface nets changed: **no**.
- Full circuit re-run after the rev.2 edit: **0 ERC errors, 2 warnings** (the known
  U5/U6 LDO drive false positives), 241 parts / 187 nets. (Superseded by the rev.3 run
  above: 243 parts / 187 nets.)
