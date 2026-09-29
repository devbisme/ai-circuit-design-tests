---
phase: 05_blocks/power
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-22T00:00:00Z
status: complete
revision: 3
next_phase: 05_coding
---

# Phase 5 block handoff — `power`

<!-- rev.3: COMMENT-ONLY correction against erc_report.md rev.2. The R19 crosstalk
     arithmetic in the block file said -75 dB; the correct figure is -78 dB. No part,
     value, connection, signature or interface net changed in this block at rev.3.
     rev.2: narrow fix pass against erc_report.md MEDIUM-6. One part added (R19) and
     U7 unit A's output rewired through it. No signature or interface-net change.
     Every other rev.1 decision stands. -->

## Decisions

1. **Signature as written — unchanged, no keyword renamed:**
   `power(vbus_sw, v3v3d, v1v2, v3v3a_adc, v3v3a_amp, vref_off, vcm_ref, gnd)`.
2. **Driven / sensed:** `vbus_sw` and `gnd` are **sensed only**. `v3v3d`, `v1v2`,
   `v3v3a_adc`, `v3v3a_amp` are **driven but through a passive** (L1, L2, FB3, FB4), so
   ERC sees no driver on them. `vref_off` is **genuinely driven** (U7 unit A output).
   `vcm_ref` is an **unbuffered R16/R17 divider** — no driving pin.
3. **Sequencing arithmetic — R18/C22 UNCHANGED, ordering confirmed.**
   τ = 100 kΩ × 100 nF = **10.0 ms**. The AP62200T's internal 1.5 µA EN pull-up is a
   current source (infinite impedance), so it raises the asymptote, not τ:
   `V∞ = 5.00 + 1.5 µA × 100 kΩ = 5.15 V`.
   - no pull-up: `t = −10 ms·ln(1 − 1.20/5.00) = 2.744 ms` (reproduces architecture #12)
   - with pull-up: `t = −10 ms·ln(1 − 1.20/5.15) = **2.653 ms**` → **91 µs / 3.3 % shorter**
   With VBUS_SW ramping rather than stepping (≈1.86 ms, from decision #11's own 118 mA
   into 44 µF), the piecewise solution gives 3.57 ms vs 3.69 ms — same 3 % correction.
   **U4 (+1V2) cannot start until VBUS_SW clears the AP62200T's 4.2 V minimum VIN, at
   ≈1.56 ms. Margin = 3.57 − 1.56 ≈ 2.0 ms of +1V2 lead.** Core-before-I/O holds; no
   change to R18 or C22.
4. **R19 is now PLACED (rev.2) — 22 Ω 0402, U7A's capacitive-load isolation resistor
   (RNULL), between the op-amp output and `VREF_OFF`.** It was rev.1's spare; this is
   what it is spent on. **R19 must now appear in the BOM: 22 Ω, 0402, jellybean.**
   **I agree with the proposed fix, and I would upgrade it from "unsimulated risk" to a
   datasheet-backed defect.** Evidence, from the TLV237x datasheet itself (TI SLOS270F,
   fetched this pass — `datasheets/TLV2372IDR_SUMMARY.md` had no PDF):
   - §8.3.2 *Driving a Capacitive Load*: "capacitive loading directly on the output
     decreases the device phase margin leading to high frequency ringing or
     oscillations. Therefore, **for capacitive loads of greater than 10 pF**, TI
     recommends that a resistor be placed in series (RNULL) with the output, as shown in
     Figure 34. **A minimum value of 20 Ω** should work well for most applications."
   - Figure 20 (*Phase Margin vs Capacitive Load*, RNULL = 0 / 50 / 100 Ω) stops at
     **1000 pF**, with the RNULL = 0 curve already collapsed there. This net is 300×
     past the end of that curve. Figure 34 draws RNULL **outside** the loop — exactly
     the proposed topology.
   So "is it stable into 300 nF?" is **no**, by TI's own text, no simulation needed.
   Analysis agrees: with Ro = 100–1000 Ω the CL pole is 0.5–5 kHz, crossover ≈
   √(GBW·f_p) ≈ 40–90 kHz, φm a few degrees. With R19 the zero at 1/(2π·22·300 nF) =
   **24 kHz** sits a decade or more below the new crossover → φm > 70° for any plausible
   Ro. 22 Ω is the nearest E24 value ≥ TI's 20 Ω minimum.
4a. **Your three bullets, checked:**
   - **Cap placement — agreed, and it is the load-bearing detail.** C24 is on `VREF_OFF`
     (the load side), so C113/C213 in the two `analog_frontend` instances are
     automatically on the load side too. Verified in the built circuit: `VREF_OFF` =
     `R19.2, C24.1, C113.1, C213.1, C101.2, C201.2, R101.2, R201.2`; `VREF_OFF_AMP` =
     `U7.1, U7.2, R19.1`. The reason is stronger than the HF-return argument: those caps
     **are** the capacitive load — on the op-amp side R19 isolates nothing and the
     follower still drives 300 nF bare. (The HF-return term alone is small: 22 Ω against
     a 90.9 kΩ leg is 0.024 %.)
   - **DC accuracy — agreed, negligible, and your 0.024 % is the right figure for the
     gain term.** The term that is actually signal-dependent is the IR drop: the two
     attenuator legs swing **−11.8/+8.2 µA** each — *not* a symmetric ±8.2 µA. BUFIN
     spans 0.734–2.552 V about the **1.807 V** reference, so the negative excursion
     (1.073 V) is larger than the positive (0.745 V). **Corrected at rev.3.** Worst case
     is both legs at −11.8 µA → −23.6 µA × 22 Ω = **−0.52 mV** across R19 = **5.2 mV
     referred to a ±10 V input = 0.026 % of the 20 V FS span**, against F12's ±1 %
     offset / ±2 % gain. Still noise.
   - **One thing your list missed:** R19 is a *shared* impedance in both channels'
     reference return, so it adds inter-channel crosstalk. **Corrected at rev.3 from
     −75 dB to −78 dB.** CH2's worst-case −11.8 µA puts −0.26 mV on `VREF_OFF`, reaching
     CH1's BUFIN at 0.909× = 2.6 mV input-referred → **≈ −78 dB against the 20 V p-p full
     scale at DC** (−81 dB on the positive excursion), improving above 24 kHz as the
     300 nF shunts R19. At 12 bits the LSB is 4.88 mV, so that is **≈0.5 LSB**. The
     earlier −75 dB was doubly wrong: it used the symmetric ±8.2 µA *and* referenced the
     result to the 10 V peak rather than the 20 V p-p span the adjacent 0.018 % FS figure
     used. Net effect of the correction is marginally *worse* crosstalk than recorded.
     SPEC states no channel-isolation requirement, so I placed R19 anyway — but it is the
     one property the fix makes worse and it should not be discovered at bench time.
5. **FB1–FB4 allocation** (net_plan is silent; design_risks R5 says "ferrite + 10 µF in
   front of each LDO" and only accounts for two): FB1 = VBUS_SW→U5.IN, FB2 = VBUS_SW→U6.IN
   (with C11/C14 = 10 µF, exactly R5's prescription); FB3 = U5.OUT→+3V3A_ADC,
   FB4 = U6.OUT→+3V3A_AMP as output-side isolation. DCR costs ≈8 mV at 55 mA. Assumption.
6. **U5/U6 NR caps (C28/C29) are 100 nF, not 10 nF.** The TPS736 datasheet's own headline
   is "30 µVRMS with 0.1 µF CNR" — the exact figure architecture #9 / risk R5 depend on.
   Internal 27 kΩ into NR → ~14 ms extra start-up, irrelevant here. EN tied to IN on both.
7. **U7 unit B is a unity-gain follower with IN2+ on VCM_REF and OUT2→IN2−, output
   unloaded** (per datasheets "Next phase must" #7). It could instead *buffer* VCM_REF by
   also tying OUT2 to the rail — better for THS4521 VOCM bias current — but `net_plan.md`
   specifies an unbuffered divider, so the conservative form is coded. Cheap upgrade.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `datasheets/TLV2372IDR.pdf` | TI SLOS270F, fetched this pass — §8.3.2 + Fig. 20/34 are the basis of Decision 4. The summary said the PDF was never obtained; it is on disk now. | Before changing R19, C24, or anything else U7 drives |
| `circuits/dual_adc_usb/power.py` | `@SubCircuit power` — U3–U7, L1/L2, FB1–FB4, R10–**R19**, C10–C29, C32–C34 | Assembling the circuit |

## Next phase must

1. **Call it exactly like this:**

   ```python
   power(vbus_sw=VBUS_SW, v3v3d=V3V3D, v1v2=V1V2, v3v3a_adc=V3V3A_ADC,
         v3v3a_amp=V3V3A_AMP, vref_off=VREF_OFF, vcm_ref=VCM_REF,
         gnd=GND, tag='power')
   ```

2. **Set `.drive = POWER` at the top level on `+3V3D`, `+1V2`, `+3V3A_ADC`, `+3V3A_AMP`
   and `VCM_REF`.** This block generates all five but reaches them through a passive
   (L1/L2/FB3/FB4) or a divider, so ERC sees no driver. `VBUS_SW` and `GND` also need it
   (`VBUS_SW`'s only driver, U2.VOUT, lives in `usb_front`).
   **rev.2 changes the `VREF_OFF` half of this instruction.** U7 unit A now drives the
   internal net `VREF_OFF_AMP`, and `VREF_OFF` is reached through R19 — so `VREF_OFF`
   has **no driving pin any more**. It still needs **no** `.drive = POWER`: everything on
   it is passive (R19, C24, and R101/C101/C201/R201/C113/C213 in the front ends), so ERC
   stays silent, and flagging it would be suppression. Confirmed by re-running the whole
   circuit: still 0 errors, still only the two U5/U6 warnings.
   **Stale comment in the assembler's file, for whoever owns it:**
   `circuits/dual_adc_usb/__main__.py` line ~46 says "VREF_OFF is deliberately NOT
   flagged — U7.OUT drives it." The conclusion (do not flag it) is still right; the
   reason is now wrong. It should read "…— everything on it is passive; U7A drives
   VREF_OFF_AMP, one side of R19." I did not edit that file: it belongs to the assembler,
   not to this block. The driverless-net census in `erc_report.md` also goes 57 → 58.
3. **Expect 2 residual "Insufficient drive current" warnings that no top-level flag can
   clear**: U5.IN on `LDO_ADC_IN` and U6.IN on `LDO_AMP_IN` — both are internal nets fed
   from VBUS_SW through FB1/FB2, so the drive flag cannot propagate past the ferrite.
   Accept them. A third, on U7 V+, appears only if `+3V3A_AMP` is left without
   `.drive = POWER`. ERC on `usb_front` + `power` together is **0 errors**.
4. **`C34` is populated on U3 only.** U4 gets no feedforward cap — datasheet Table 1 marks
   it DNP for the 1.2 V rail. Do not mirror it.

## Carried forward

- **The bucks have no dedicated bulk input capacitance.** U3/U4 get only C10/C13 (100 nF
  local at VIN); the AP62200T datasheet wants ≥10 µF ceramic at the input. The BOM's only
  10 µF caps in this block (C11/C14) are committed to risk R5's LDO inputs, and all four
  22 µF go to the buck outputs (2 each, per Table 1). **`usb_front`'s C2/C3 (2 × 22 µF on
  VBUS_SW) are the de-facto buck input bulk and must be placed adjacent to the U3/U4 VIN
  pins**, or a dedicated input cap must be added. Layout constraint, flagged in both
  handoffs.
- **L2's footprint is an assumption.** `sourced_bom.md` gives no footprint for L1/L2. L1
  (`FNR4030S3R3MT`) maps exactly to `Inductor_SMD:L_Changjiang_FNR4030S`. L2
  (`SMNR4020-2.2UH`) has no KiCad entry; `Inductor_SMD:L_Changjiang_FNR4020S` is used as
  the same-geometry 4.0×4.0×2.0 mm land pattern. Verify against the MPN drawing before fab.
- **VIN margin is 0.2 V.** AP62200TWU-7 needs ≥4.2 V; architecture's worst-case VBUS droop
  is 4.4 V, minus U2's RDS(on) drop. Carried from sourcing, not reopened here.
- **rev.2 — R19's 22 Ω is chosen from TI's generic "minimum 20 Ω", not from a measured
  Ro.** The TLV237x datasheet publishes no open-loop output-resistance number I could
  quote, and Figure 20 stops at 1000 pF, so the phase-margin figures above are analysis,
  not datasheet curves. The conclusion is insensitive (any Ro from 100 Ω to 1 kΩ gives
  φm > 70°), but if the bench shows ringing on `VREF_OFF`, the knob is a larger R19, and
  the ceiling on it is the DC/crosstalk arithmetic in Decision 4a (100 Ω would still only
  be 0.11 % gain and −62 dB crosstalk).
- **rev.2 — `VREF_OFF` is now a low-pass node above ~24 kHz** (22 Ω into 300 nF). That is
  wanted here — it filters R14/R15 divider noise and U7A's own noise out of the offset
  reference — but it also means the reference cannot slew: nothing in this design asks it
  to, and nothing should be added that does.
- **`VCM_REF` is unbuffered** — 5 kΩ source impedance into two THS4521 VOCM pins. If VOCM
  bias current turns out to matter, use U7 unit B (see Decision 7).

## Do not redo

- AP62200TWU-7 as U3/U4, **not** the retired `SY8089AAC` symbol still sitting in
  `symbols/dual_adc_usb.kicad_sym`. VFB = 0.763 V (the "T" sub-variant, not 0.800 V).
- R10 = 33.2 k, R11 = 10.0 k, R12 = 5.76 k, R13 = 10.0 k, L1 = 3.3 µH, L2 = 2.2 µH,
  C32 = 330 nF, C33 = 100 nF, C34 = 22 pF — all verbatim from sourcing rev.4.
- Architecture #9 (analog rails LDO'd off VBUS_SW, never off a buck) and #12 (sequencing).
- The RC-delay arithmetic in Decision 3 — the open question it closed is now closed.

## Receipt

- **rev.3 pass: COMMENT ONLY.** The R19 crosstalk/IR-drop arithmetic in
  `circuits/dual_adc_usb/power.py` § 6 now reads −78 dB (worst-case −11.8 µA, referenced
  to the 20 V p-p FS) instead of −75 dB, and the current swing is stated as −11.8/+8.2 µA
  instead of ±8.2 µA. **Zero parts, values, connections or nets changed**; part count
  stays 44, net count stays 24. Arithmetic re-derived before editing: 11.8 µA × 22 Ω ×
  0.909 = 0.236 mV at the victim's BUFIN = 2.60 mV input-referred = 1.30e−4 of 20 V =
  −77.7 dB, and 2.60 mV / 4.883 mV (12-bit LSB) = 0.53 LSB.
- **rev.3 full-circuit re-run:** **0 ERC errors, 2 warnings** (the known U5/U6 LDO drive
  false positives), **243 parts / 187 nets** — the +2 parts are C116/C216 in
  `analog_frontend` rev.3, not from this block.
- **rev.2 fix pass:** +1 part (R19, 22 Ω 0402), +1 internal net (`VREF_OFF_AMP`), U7
  unit A's follower feedback moved to the op-amp output. Nothing else touched.
- block_id: `power`; parts: **44** (U3–U7, L1, L2, FB1–FB4, R10–**R19**, C10–C29,
  C32–C34).
- nets: **24** (8 interface + 16 internal: SW_3V3D, SW_1V2, FB_3V3D, FB_1V2, EN_3V3D,
  LDO_ADC_IN/OUT, LDO_AMP_IN/OUT, VREF_OFF_DIV, **VREF_OFF_AMP**, and implicit pin-to-pin
  nets).
- `python -m py_compile`: **OK**. Instantiation with real symbol libraries: OK.
- `validate-footprints.py` (re-run rev.2): **exit 0**, 12 footprints checked, all valid.
- Full circuit re-run after the rev.2 edit: **0 errors, 2 warnings** (the known U5/U6
  LDO drive false positives), 241 parts / 187 nets. (Superseded by the rev.3 run above.)
- signature changed: **no**. Interface nets changed: **no**.
