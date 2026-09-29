---
phase: 05_blocks/power_tree
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-23T19:40:00Z
status: complete
revision: 2
next_phase: 05_coding
---

# Phase 5 handoff — block `power_tree`

## Decisions

1. **SIGNATURE CHANGED — `ft_3v3` ADDED** (between `pwren_n` and `gnd`). Final, as written:
   `power_tree(vbus, vbus_sw, p3v3d, p1v8, p1v2, p3v3a, va_pos, va_neg, pwren_n, ft_3v3, gnd)`
   **Calling it with architecture rev.3's 10-arg list raises `TypeError`.** R71 (U9's EN
   pull-up) must return to `FT_3V3` — net_plan.md `LS_EN` and sourced_bom.csv both say so, and
   both are right: a pull-up to `P3V3D` is a bootstrap deadlock (P3V3D is downstream of U9), and
   a pull-up to `VBUS` asserts EN at plug-in before `FT_3V3` exists to hold Q1's gate, powering
   the board pre-enumeration and breaking SPEC P3. `FT_3V3` is unreachable from the declared
   parameter list and a local `Net('FT_3V3')` would be a *different* net (SKiDL renames the
   duplicate), so the parameter was added. The top-level net already exists — `usb_bridge` takes
   it as `ft_3v3`, driven by U6 pin 39.
2. **`p1v8` is U15's OUTPUT; U14's output is the block-internal net `P1V8_PRE`.** `fpga_core`
   needs no re-code: its `p1v8` parameter (U5 pin 12 / VCCIO3, R53, C511–C513) now lands on the
   slew-limited side, which is exactly what its own rev.1 risk row asked for. C85/C86 sit on
   `P1V8_PRE` and serve as U15's VIN bypass (sourcing rev.4 Decision 2).
3. **U15.ON tied to `P1V8_PRE` (its own VIN).** The BOM is final at 169 refdes with no spare
   resistor in this block, so a direct tie was the only option; `P3V3D` would assert ON ~1 ms
   before U15's input exists, `P1V8_PRE` never does. V_IH ≤ 1.05 V vs 1.8 V drive, pin is 5.5 V
   tolerant. Keeps VCCIO3 the last rail up (what the MODE0/MODE1 GND straps depend on) and
   orders power-down too. **Residual risk in Carried forward — read it.**
4. **U9 enable polarity, both directions.** PWREN# high (pre-enumeration) → Vgs = +3.3 V, ≥1.8 V
   overdrive even at BSS138's 1.5 V max threshold → Q1 ON → LS_EN = 0.1 mV ≤ V_IL 0.5 V → U9
   **OFF**, board draws 98 mA ≤ 150 mA (SPEC P3). PWREN# low (enumerated) → Vgs = 0 V, below the
   0.8 V *minimum* threshold → Q1 OFF → LS_EN = 3.1 V ≥ V_IH 1.0 V → U9 **ON**.
5. **QOD left `NC` on both U9 and U15.** TI specifies both switches' rise times with "QOD =
   Open", and those two numbers (U9's ~2 ms inrush ramp, U15's 260 µs VCCIO3 ramp) are what this
   design is betting on. Consequence accepted: neither gated rail is actively discharged.
6. **Divider values used verbatim, not recomputed.** V_FB = 0.600 V verified; R72/R73 = 180 k /
   40.2 k → 3.287 V, R74/R75 = 100 k / 100 k → 1.200 V. Both bucks' and both LDOs' EN pins tie to
   their own input rail — U9 is the one sequencing gate; a second would only add a hang path.
7. **Drive:** driven here — `vbus_sw` (U9.VOUT, power_out), `p1v8` (U15.VOUT, power_out),
   `p3v3a` (U12.VOUT, power_out), `p3v3d` / `p1v2` / `va_pos` / `va_neg` (through L71 / L72 /
   FB1 / R76, all PASSIVE). Sensed only — `vbus`, `pwren_n`, `ft_3v3`, `gnd`. Nothing bidirectional.
8. **C88 ADDED AT REV.2 — 100 nF 0402 at U12's VIN, and at U12's only.** This **reverses
   rev.1's own disposition** on the missing at-pin 100 nF. The erc-reviewer adjudicated it
   (erc_report MED-2): **agreed** for U9/U10/U11 — U9's VIN is a DC node with a ~2 ms ramp
   and no switching currents, and C72/C74 *are* the hot-loop input caps TI specifies for the
   TLV62569, so the 10 µF dominates — and **disagreed** for U12. U12 is the analog-rail LDO:
   `P3V3A` feeds the ADS5231 AVDD and both THS4521 FDAs, while its input `VBUS_SW` is shared
   with two 1.5 MHz switchers, and RT9013's PSRR falls from ~70 dB at 1 kHz to ~20–30 dB by
   1.5 MHz. At 12 bits 1 LSB = 2 V / 4096 = 488 µV, so the residue lands in the signal path
   against SPEC F10 (SNR ≥ 60 dB). C88 = `CL05B104KO5NNNC` / LCSC `C1525`, 0402, already in
   `sourced_bom.csv` rev.5 row 59 — **the BOM was NOT edited by this block.** C88.1 on
   `VBUS_SW`, C88.2 on `GND`. **U9/U10/U11 stay bare on purpose — do not "complete the set".**
   Signature untouched.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/power_tree.py` | The `power_tree` @SubCircuit — U9–U15, Q1, FB1, L71/L72, R71–R76, C71–C88 | Assembling the circuit |

## Next phase must

Exact call for the assembler:

```python
power_tree(vbus=VBUS, vbus_sw=VBUS_SW, p3v3d=P3V3D, p1v8=P1V8, p1v2=P1V2, p3v3a=P3V3A,
           va_pos=VA_POS, va_neg=VA_NEG, pwren_n=PWREN_N, ft_3v3=FT_3V3, gnd=GND)
```

- `VBUS_SW` is loaded only inside this block; still create it at top level and pass it.
- **`.drive = POWER` needed at top level for `P3V3D`, `P1V2`, `VA_POS`, `VA_NEG`, `GND`** — their
  only source here is an inductor/ferrite/resistor pin, so ERC sees no driver.
- **Not needed for `P1V8`, `P3V3A`, `VBUS_SW`** — each has a real power_out pin here. Setting it
  anyway is harmless; `fpga_core`'s handoff asks for `P1V8.drive = POWER` and that stays fine.
- `VBUS`, `PWREN_N`, `FT_3V3` are driven by `usb_bridge`; this block only senses them.

## Carried forward

- **[HIGH] U15's ON-pin tie is outside TI's characterized condition — bench-verify before fab.**
  SLVSDG1x §6.6 preamble scopes the whole switching-characteristics table (including the 260 µs
  CT rise time) to "the power-up sequence where VIN is already in steady state condition before
  the ON pin is asserted high." No rail on this board comes up *after* `P1V8_PRE` settles, so
  with a frozen BOM there is no in-spec option — `P3V3D` violates it worse. Physical argument
  that it still holds: U14's 50 µs VIN ramp is 5× faster than the 260 µs CT-governed gate ramp,
  so the pass FET cannot be enhanced before VIN is settled. Sound, but not a datasheet guarantee.
  Scope VCCIO3's rise for ≥180 µs monotonic. **If it fails, the fix is an RC on U15.ON fed from
  `P3V3D` (10 k + 100 nF ≈ 1 ms) — 2 new refs, which is why it was not done here.**
- **[LOW] Decoupling short by 3 × 100 nF — U9, U10, U11. Settled, not open.** net_plan
  requires 100 nF at every IC supply pin; funded here are U12 (**C88, new at rev.2**), U13
  (C82), U14 (C84), U15 (C85). Bare: **U9 VIN, U10 VIN, U11 VIN** — accepted by the
  erc-reviewer (erc_report MED-2) because each has ≥10 µF on its own net and those 10 µFs are
  the hot-loop input caps TI specifies, so this is at-pin HF impedance, not a missing bypass.
  Severity dropped MED → LOW: the one instance with a path to a stated spec number (U12 → SNR,
  SPEC F10) is now closed by C88. Do not re-open for U9/U10/U11.
- **[LOW] net_plan.md defect, resolved locally.** It lists C81 under *both* `VBUS_SW` and
  `VA_POS`, and lists C72/C74 nowhere. Resolved: C81 = VA_POS bulk after FB1 (that rail would
  otherwise have none), C72/C74 = the two 10 µF buck input caps net_plan's own policy calls for.
  All of C71–C88 used exactly once either way.
- **Assumed provided elsewhere:** R65 (PWREN# pull-up) is in `usb_bridge`, not here. C511/C512/
  C513 in `fpga_core` are U15's output-side bypass (checked against TI's ≥1 µF VIN / optional CL
  guidance, sourcing rev.4 Decision 2) — do not delete them on the theory that power_tree covers
  VCCIO3. R53's 180 µA pull-up now draws through U15; drop is <4 mV, no action needed.
- **Intentional `NC`:** U9.QOD, U15.QOD (decision 5), U12.NC (pin 4), U14.NC (pin 4).
- **U14's Shutdown pin: do not add an RC.** Verified non-fix (04_datasheets Decision 16). EN is
  tied to `P3V3D` on purpose.

## Do not redo
- **C88 at U12's VIN, and U9/U10/U11 left bare** (decision 8). erc_report MED-2 is closed
  in both directions; neither half is to be re-litigated.
- Decision 1's `ft_3v3` parameter, decision 2's `P1V8` = U15 output / `P1V8_PRE` = U14 output
  split, decision 3's U15.ON tie, and the C81 / C72 / C74 net_plan resolution.

## Receipt

- rev.2: block `power_tree`; **35 parts** (U9–U15, Q1, FB1, L71/L72, R71–R76, C71–C88), **23 nets**
  (11 interface + 12 internal: LS_EN, LS_CT, SW_3V3, FB_3V3, SW_1V2, FB_1V2, CP_CAP_P, CP_CAP_N,
  VA_NEG_RAW, P1V8_PRE, LS2_CT).
- Only change vs rev.1: **C88 added** at U12's VIN (erc_report MED-2). Nothing else touched.
- Refdes set matches `sourcing/sourced_bom.csv` rev.5 exactly — includes U15, C87 and **C88**.
  `sourced_bom.csv` was **not** edited here; `validate-bom.py` **exit 0**, 170 parts.
- Full-circuit run after the fix: **0 ERC errors, 0 ERC warnings**. Netlist confirms
  `C88.1 → VBUS_SW`, `C88.2 → GND`.
- `py_compile` OK. Standalone smoke run: **0 ERC errors**, 5 warnings, all of them artifacts of
  running the block alone (`P1V8`/`PWREN_N`/`FT_3V3` one-pin nets — they get their other end
  from `fpga_core`/`usb_bridge`).
- All 9 distinct footprint strings verified present in the KiCad libraries.
- **Signature changed at rev.2: NO.** (It changed at rev.1 — `ft_3v3` added; see Decision 1
  and the call block above, which still applies verbatim.)
