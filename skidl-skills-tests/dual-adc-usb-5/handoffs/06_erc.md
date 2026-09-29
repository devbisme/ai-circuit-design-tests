---
phase: 06_erc
agent: erc-reviewer
circuit: dual_adc_usb
written: 2026-09-21T12:40:00Z
status: complete
revision: 2
next_phase: export
---

# Phase 6 handoff — ERC review (revision 2, narrow re-gate)

**0 ERC errors, 19 ERC warnings (same benign set as rev 1), 33/33 footprints → PASS.**
`outputs/dual_adc_usb.net` and `outputs/dual_adc_usb_bom.xml` are **current and correct — do not
pull them.** 175 parts / 150 nets.

Re-gate scope only (architecture rev 3, blocks `afe_channel` rev 3 and `analog_power_ref` rev 3).
Everything outside that scope stands as recorded in the revision 1 record, retained verbatim in
`erc_report.md`.

**H-1 is CLOSED.** **M-1 is CLOSED** at the top end and consciously traded at the bottom end (L-5).
Two new findings: **H-2** and **M-2**, both open, neither a gate failure.

## Decisions

1. **H-1 closed on independent arithmetic, not on the architect's say-so.** I derived the
   differential MFB transfer function from netlist node membership and reproduced **every**
   claimed figure to ≤0.02 dB: f₀ = 5.934 MHz, Q = 1.0125, output RC 6.346 MHz, −3 dB at
   **6.106 MHz**, **−0.15 dB @ 4.0 MHz**, **−25.33 dB @ 16 MHz**. `R_f` is on the MFB node and
   `C_f` alone on the FB pin, as ordered; both legs' `C_f` and `R_f` reference the same output; no
   pin is on two nets. A balance check I added — computing each summing node independently — has
   them agreeing to 0.1 mV at every input level, which is what actually proves the crosswise
   feedback sense is negative in both legs.
2. **The architect's rejection of my `R8` = 23.0 k / `VBIAS` = 1.000 V is correct and I withdraw
   it.** 23.0 kΩ is in no standard series (E96 has 22.6 / 23.2), and at 1.000 V the SPEC I5
   AIN = −30 V case puts the OPA355 input at **−0.547 V**, past its (V−) − 0.5 V abs max, at a
   current where the BAV99 has not begun to conduct. 1.100 V gives −0.452 V. My proposal was worse
   on both counts. **Do not reopen this.**
3. **M-1 is genuinely closed, not moved.** At AIN = +10 V the buffer input is 1.5442 V; with the
   rail 2 % low (`VBIAS` tracking it down to 1.078 V) the margin is **≈208 mV** against 1.734 V,
   vs 85 mV before. The architect's ≈180 mV is the more conservative figure; either way ~2.2×.
4. **The 19 warnings are accepted unchanged and the five false-positive claims were NOT
   re-verified**, per instruction. Rev 3 touched no pin on any of the six warning nets, so
   revision 1's dispositions carry forward intact. The "Missing tag" netlist warning is still
   cosmetic (rev 1 Decision 2) — do not "fix" it.
5. **M-2 is dispositioned as an open MEDIUM, not accepted.** F10 is SOFT/CLAUDE so it does not
   fail the gate, but the board currently meets it only on a typical part and only by counting an
   uncontrolled parasitic. That is a decision for `circuit-architect`, not for this gate.
6. **H-2 is escalated despite "the RGT crosswise FB↔input straps" sitting in revision 1's
   own "do not redo".** The assumption's criticality changed materially at rev 3: with `R_f` moved
   off the FB pin, an absent strap is no longer a loud failure. Escalating a settled item whose
   consequence changed is the intended behaviour, not re-litigation.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `erc_report.md` | Rev 2 re-gate: node-membership table, derived transfer function, claimed-vs-computed table, balance check, finite-GBW analysis, VBIAS arithmetic, H-2/M-2/L-5/N-3…N-7 — then the full rev 1 record | Always — before export and before touching the AFE or `VBIAS` |
| `__main__.erc` | The 19 warnings verbatim | Cross-checking the classification |
| `outputs/dual_adc_usb.net` | KiCad netlist, 175 parts / 150 nets, reproducibility verified | Export |

## Next phase must

**Export is unblocked and already done — the netlist and BOM on disk are from this verified run.**
Nothing to re-export. For any future change, re-run from the project root:

```bash
KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python3 -m circuits.dual_adc_usb
python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/validate-footprints.py circuits/dual_adc_usb
```

`symbols/` is mandatory on the path (U5, U6, X1, J1 are generated symbols). Logs land as
`__main__.erc` / `__main__.log`.

**Before fabrication — not before export — two items need owners:**

1. **`skidl-skills:datasheet-librarian` for H-2.** Obtain **TI SBOS778 (THS4551)** and read
   **Figure 9-2** (functional block diagram) to confirm FB+ (4) ↔ IN− (3) and FB− (1) ↔ IN+ (2)
   are internally strapped, **Table 6-1** (PD polarity) and **Section 9.1** (the 0.6 pF internal
   feedback capacitance). All three are cited in `afe_channel.py` but no PDF exists in
   `datasheets/`. While there, capture the **input common-mode range** — R-3 has wanted it since
   phase 04. If the straps are *not* internal, route to `circuit-architect`: `C103`/`C104` are on
   floating pins and the anti-alias is −8.6 dB at 16 MHz, not −25.3.
2. **`skidl-skills:circuit-architect` for M-2.** F10 (≥25 dB above 16 MHz) is missed by **1.84 dB**
   at ±5 % C0G / ±1 % R, and the 0.33 dB nominal margin is entirely TI's 0.6 pF parasitic. F9 has
   ~0.2 dB of flatness to trade. `C103`/`C104` 10 → 12 pF with `C111` 68 → 82 pF gives worst-case
   −26.57 dB at 16 MHz and 0.49 dB to 4 MHz across both internal-C_f assumptions — but that is
   0.01 dB inside F9. Settle it with a simulation and a Monte Carlo, then re-invoke the
   **`afe_channel`** block coder for two values, no topology change, no new refs.

Three cosmetic fixes, bundle them into whatever pass happens next: **N-3** stale `1.200 V` /
`1.140 V` comments at `circuits/dual_adc_usb/__main__.py:51-52` (`skidl-assembler`); **N-4** the
`R_f` OUT+/OUT− labels swapped in `sourcing/sourced_bom.md` lines 30–31 (`part-sourcer`); **N-5**
name the FDA output nets, currently `N$34`/`N$35`/`N$37`/`N$38` (`afe_channel` coder).

## Carried forward

Accepted, but a human should eyeball these before fabrication:

- **H-2 (HIGH, open):** as above. My judgement is that the strap claim is **probably correct** —
  the on-disk summary's FB→OUT mapping, pin adjacency ({1,2} and {3,4} pairing), and the fact that
  an FDA needs OUT+→IN− all converge on it — but it is asserted, not verified, and the failure mode
  is silent.
- **M-2 (MEDIUM, open):** as above.
- **L-5 (LOW, new):** the I5 ±30 V survival margin at the OPA355 input went 143 mV → **48 mV** when
  `VBIAS` dropped. `design_risks.md` R-3 records the −0.452 V figure, so this is a conscious trade,
  and the BAV99 begins conducting softly right at that level (Vf ≈ 0.45–0.55 V at ~10 µA, not
  0.7 V). But **the −0.5 V abs max is not on disk either** — `OPA355NA_3K_SUMMARY.md` states no
  absolute-maximum input range. Two of this block's three tightest numbers rest on unread
  datasheets.
- **The MFB network is now filter-critical and was never simulated** (risk R-5). Keep
  `R_g`/`R_f`/`R_mfb`/`C_mfb` tight and the legs symmetric; confirm on a network analyser. The
  finite-GBW margin is the reason: noise gain 5.008 against 135 MHz GBW leaves only ~4.5× f₀.
- **L-1** (one 100 nF for four THS4551 VS+ pins; `C112`/`C212` skipped with a TODO), **L-2**
  (R44/R45 10 kΩ vs FPGA config pull-ups), **L-3** (J5 has no clamp), **L-4** (SMF5.0CA standoff),
  **N-2** (`FT232HL-REEL_SUMMARY.md` wrongly says VREGIN comes from `+3V3_D` — fix the summary, not
  the code) — all unchanged from revision 1.
- Footprints not library-verified, unchanged from revision 1: the **custom** STC3MA trimmer
  footprint (C101/C201), U6's **unverified EP size**, and the J2/J3 BNC **pad-count open risk** (a
  3-hole substitute must also drop `j[4]`).
- Sourcing owes nothing new: all six rev-3 parts (`R111/R112/C111` ×2) have real MPNs, live stock
  and tiers in `sourcing/sourced_bom.md` rev 4. The rev-1 BOM-owed list is unchanged.

## Do not redo

- **The 19 ERC warnings and the five false-positive claims** — verified in revision 1 against
  actual pin types, and rev 3 touched none of those nets. Message *order* varies between runs;
  that is normal.
- **H-1's arithmetic.** The MFB node membership, the transfer function, f₀/Q, the output RC, and
  all seven claimed dB figures were derived independently here and match. Do not recompute them.
- **`VBIAS` = 1.100 V and `R8`/`R9` = 22.0 k / 11.0 k** — and specifically **not** 23.0 k / 1.000 V
  (Decision 2). Consistency verified everywhere in code, netlist, architecture, BOM and SPEC; the
  only stale text is the N-3 comment. `VREF_FE` = 1.0453 V follows from the ratio; no divider
  resistor moves.
- **M-1's top-end margin** (208 mV) and the DC chain: zero differential out at zero input
  (0.34 mV residual ≈ 0.7 LSB), 2.0 V p-p at ±10 V, 999.9 kΩ input (I4), buffer span
  0.546–1.544 V. All recomputed at 1.100 V and correct.
- **Reproducibility** — two runs, 4-line diff, all of it the `(date …)` line. No `_1` refdes.
- **Footprint validation** — 33/33 across 9 files, exit 0; rev 3's six new parts reuse existing
  0603 footprints.
- **No silent net merges** — all 150 nets parsed, no pin on more than one net. `VBIAS` (6 pins) and
  `VBIAS_DRV` (3) still distinct, so R22's isolation survives into the netlist.
- Everything in revision 1's "Do not redo" that rev 3 did not touch: FPGA bank voltages (QN88 →
  SDR SDRAM → 3.3 V, settled from the PDF), supply span vs abs max for all 12 ICs, signal level vs
  receiver rail, exposed pads, SPEC F14's clock path. **Exception:** the THS4551 FB↔IN strap has
  moved from "do not redo" to H-2, because rev 3 changed what breaks if it is wrong.

## Receipt

- ERC: **0 errors, 19 warnings** — reproduced twice; identical warning set to revision 1, none
  added or removed, five false-positive claims carried forward unre-verified as instructed.
- Footprints: **33/33 valid across 9 files**, exit 0. Netlist reproducible (date line only),
  **175 parts / 150 nets**, no duplicate refs, no net merges.
- **H-1 CLOSED** — MFB topology and all seven claimed dB figures verified independently from the
  netlist to ≤0.02 dB. **M-1 CLOSED** (208 mV, was 85 mV); my 23.0 k proposal withdrawn as wrong.
- **2 new findings: H-2** (3rd order rests on an SBOS778D claim with no PDF in the project; silent
  −8.6 dB failure mode if wrong) and **M-2** (F10 missed by 1.84 dB at worst-case tolerance; the
  nominal margin is a 0.6 pF parasitic). Plus **L-5** and notes N-3…N-7.
- **Verdict: PASS** (0 errors + valid footprints). Export stays unblocked; **the exported netlist
  and BOM are good — do not pull them.**
