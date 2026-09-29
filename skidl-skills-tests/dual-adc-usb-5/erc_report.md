# ERC report — dual_adc_usb (revision 2)

**0 errors, 19 warnings, 5 notes. Circuit is PASS.**

Revision 2 is a **narrow re-gate** of architecture rev 3 / block rev 3, not a re-review of the
board. Scope: (1) re-run ERC + footprints, (2) independently verify the new MFB anti-alias
topology and its claimed response, (3) verify `VBIAS` = 1.100 V is consistent and that M-1 is
closed rather than moved, (4) re-check H-1. Everything else stands as recorded in the
revision 1 record, retained verbatim below.

**H-1 is CLOSED. M-1 is CLOSED at the top end and partly traded at the bottom end (L-5).**
Two new findings: **H-2** (the 3rd order now rests on an unverified datasheet claim) and
**M-2** (F10 is met at nominal only, not at worst-case tolerance).

`outputs/dual_adc_usb.net` / `outputs/dual_adc_usb_bom.xml` are **good — do not pull them.**

---

## Re-gate results

```bash
KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python3 -m circuits.dual_adc_usb
python3 /home/devb/projects/AI/skills/skidl-skills/scripts/validate-footprints.py circuits/dual_adc_usb
```

| Check | Result |
|---|---|
| ERC | **0 errors, 19 warnings** — reproduced twice |
| Warning set | **identical to revision 1**: `VBUS_RAW`×4, `XO_VDD`×1, `EE_CS`×3, `EE_CLK`×3, `FT232H_3V3`×7, `V5_LDO_IN`×1 = 19. None added, none removed |
| Footprints | **33/33 valid across 9 files**, exit 0 (rev 3's six new parts reuse `R_0603`/`C_0603`) |
| Netlist | **175 parts / 150 nets** (+6 parts, +4 nets vs rev 1 — exactly `R111/R112/C111` ×2 and `CH<n>_MFBP/MFBN`) |
| Reproducibility | two consecutive runs differ **only in the `(date …)` line** — 4-line diff, all of it the timestamp |
| Duplicate refs | none; **no `_1`-suffixed refdes** |
| Net merges | all 150 nets parsed; **no pin appears on more than one net** |
| Netlist-gen warning | 1, the "Missing tag" message — cosmetic, dispositioned in revision 1 Decision 2. Unchanged |

The five false-positive claims verified in revision 1 were **not** re-verified, per instruction.
Rev 3 touched no pin on any of the six warning nets, so their disposition carries forward intact.

---

## H-1 — CLOSED. Verified independently from the netlist, not from the comments.

The topology **is** a genuine differential multiple-feedback (Rauch) section, and **every number
the architect and coder claim follows from the netlist values.** Node membership, from
`outputs/dual_adc_usb.net`:

| Node | Members | Verdict |
|---|---|---|
| `CH1_MFBP` | `R105.2` (R_g1), `R107.1` (R_f), `R111.1` (R_mfb), `C111.1` (C_mfb) | MFB summing node, 4 elements ✓ |
| `CH1_MFBN` | `R106.2`, `R108.1`, `R112.1`, `C111.2` | mirror ✓ |
| `CH1_INP` | `R111.2`, `U_fda1.2` (IN+) | amp input, R_mfb only ✓ |
| `CH1_FBN` | `C104.1`, `U_fda1.1` (FB−) | **C_f only — R_f is off the FB pin, as ordered** ✓ |
| `CH1_INN` / `CH1_FBP` | `R112.2`,`U_fda1.3` / `C103.1`,`U_fda1.4` | mirror ✓ |
| `N$34` (OUT−) | `C104.2`, `R107.2`, `R110.1`, `U_fda1.11` | C_f and R_f of the P leg both land on the **same** output ✓ |
| `N$35` (OUT+) | `C103.2`, `R208`-equivalent `R108.2`, `R109.1`, `U_fda1.10` | mirror ✓ |

Channel 2 (`CH2_*`, `N$37`/`N$38`) is identical. No pin on two nets anywhere.

**Transfer function, derived rather than quoted.** Differential half-circuit: a component between
symmetric nodes P and N appears at half its impedance to the symmetry axis, so `C_mfb` → 2×68 =
**136 pF** and the output `C_diff` → 2×330 + 100 = **760 pF**. With R1 = R_g = 499, R2 = R_f =
1000, R3 = R_mfb = 499, C2 = C_f:

```
H(s) = -(R2/R1) / [ 1 + s·C2·(R2·R3/R1 + R3 + R2) + s²·C1·C2·R2·R3 ]
```

| Quantity | My value | Claimed | |
|---|---|---|---|
| MFB f₀ | 5.934 MHz | 5.93 MHz | ✓ |
| MFB Q | 1.0125 | 1.012 | ✓ |
| Output RC diff. pole | 6.346 MHz | 6.35 MHz | ✓ |
| Output RC CM pole | 48.2 MHz | 48 MHz | ✓ |
| −3 dB | **6.106 MHz** | 6.1 MHz | ✓ |
| 4.0 MHz | **−0.15 dB** | −0.15 dB | ✓ |
| 5 MHz / 7 MHz / 10 MHz | −1.00 / −5.25 / −13.31 dB | −1.0 / −5.25 / −13.3 | ✓ |
| **16 MHz** | **−25.33 dB** | −25.3 dB | ✓ |
| 20 MHz | −31.12 dB | −31.1 dB | ✓ |

Every figure reproduces to ≤0.02 dB. `R_f` lands where the architect intended (MFB node, not the
FB pin); `C_f` stays on the FB pin; DC gain is still R_f/R_g = 2.004 with no DC current in
`R_mfb`, so the gain chain and the zero-input match are untouched.

**Independent balance check (not asked for, but it is what proves the crosswise sense).** The two
summing nodes must sit at the same potential if the feedback is negative in both legs. Computing
them separately from the network: at AIN = −10 V both land on **1.080 V**; at AIN = +10 V both
land on **1.413 V**. They agree to 0.1 mV at every input level — the P leg (IN+, feedback from
OUT−) and N leg (IN−, feedback from OUT+) are both negative, and the RGT crosswise mapping is
used consistently. A sign error in either leg would show here as a divergence.

**Finite amplifier bandwidth does not threaten the result.** MFB noise gain is
1 + R_f/(R_g‖R_mfb) = 5.008, so the THS4551's 135 MHz GBW leaves ~27 MHz of closed-loop
bandwidth, 4.5× f₀ — thin for an MFB. Modelling the amp as a single pole moves −3 dB from 6.11 to
**5.70 MHz** and *improves* 16 MHz to −27.2 dB, with ≤0.3 dB of passband peaking. The direction is
favourable and both renegotiated specs still hold, but a single-pole model of an FDA is crude;
this is the strongest argument for the network-analyser check the block handoff already asks for.

---

## H-2 — HIGH (new) — The 3rd order now rests entirely on a THS4551 datasheet claim the project cannot check.

The complex pole pair exists **only** if the RGT package internally straps FB+ (pin 4) to IN−
(pin 3) and FB− (pin 1) to IN+ (pin 2), crosswise, as `afe_channel.py` asserts. There is **no
THS4551 PDF in `datasheets/`** — `datasheets/THS4551IRGTR_SUMMARY.md` says *"No PDF obtained
(LCSC-hosted URL returned an HTML anti-bot page)"* — yet the block file cites **SBOS778D Table
6-1, Figure 9-2 and Section 9.1**. None of those three citations is backed by an artifact on disk,
and `design_risks.md` R-3 independently records that *"the THS4551's own input CM range has never
been read from a datasheet — phase 04 could not obtain the PDF."*

**Consequence if the straps are not internal:** `C103`/`C104` hang on floating pins, C2 = 0, the
MFB's b₁ and b₂ both vanish, and the anti-alias collapses to the single output RC —
**−8.6 dB at 16 MHz instead of −25.3 dB.** The amplifier still works at G = 2 through
R_g → MFB → R_mfb → input, so the board powers up, passes ERC, and measures fine below 4 MHz.
Silent, total loss of the anti-alias filter. At revision 1 the same assumption was benign: `R_f`
sat on the FB pin, so an absent strap would have opened the DC feedback path and been obvious on
the bench. Rev 3 moved `R_f` off that pin and turned a loud failure into a quiet one. That is why
this is escalated rather than left under revision 1's "do not redo".

**My judgement: the claim is probably correct.** Three independent arguments converge:

1. The on-disk summary's own mapping — *"FB+ … connects to OUT+ through R_f"*, *"FB− … to OUT−"* —
   is only consistent with **negative** feedback if FB+ is internally IN−, since an FDA requires
   OUT+ → IN− and OUT− → IN+.
2. Pin adjacency: {1 FB−, 2 IN+} and {3 IN−, 4 FB+} put each summing node's two pins next to each
   other. The alternative pairing crosses them, which no one would lay out.
3. The code's stated 3.3 Ω strap resistance is the kind of figure that only exists because the
   strap does.

But it is asserted, not verified. **Pull SBOS778 and read Figure 9-2 before the board spin.** If
the straps turn out to be external, the fix is a short between pins 1–2 and 3–4 — not achievable
without a layout rework, which is why this must be settled before fab, not after.

---

## M-2 — MEDIUM (new) — SPEC F10 is met at nominal only, and its margin is bought with a parasitic.

F10 (renegotiated) asks **≥25 dB above 16.0 MHz**. As built:

| Case | 16 MHz | vs F10 |
|---|---|---|
| Nominal, counting TI's +0.6 pF internal C_f | −25.33 dB | met by **0.33 dB** |
| Nominal, `C_f` = the 10 pF actually on the BOM | −24.76 dB | **missed by 0.24 dB** |
| Worst case, ±5 % C0G / ±1 % R | **−23.16 dB** | **missed by 1.84 dB** |

So the entire nominal margin is supplied by an **uncontrolled parasitic** — TI's 0.6 pF internal
feedback capacitance — and the design is out of spec across tolerance. The block file discloses
the worst case (*"≥22.7 dB @ 16 MHz"*, close to my −23.2 dB) but does not say that this is below
F10's 25 dB. Meanwhile the passband has slack: worst-case deviation to 4.0 MHz is **0.27 dB**
against F9's 0.50 dB limit. There is roughly 0.2 dB of flatness available to trade into the stopband.

**Two values, no topology change, no new refs, both E12/E24 C0G 0603 jellybeans:**

```python
# afe_channel.py — trade passband slack for stopband margin (M-2)
c_f_p = Part('Device', 'C', ref=c_ref(3), value='12pF', footprint=_FP_C0603)   # was 10pF
c_f_n = Part('Device', 'C', ref=c_ref(4), value='12pF', footprint=_FP_C0603)   # was 10pF
c_mfb = Part('Device', 'C', ref=c_ref(11), value='82pF', footprint=_FP_C0603)  # was 68pF
```

Swept over ±5 % C, ±1 % R **and both internal-C_f assumptions (0 and 0.6 pF)**: worst-case 16 MHz
= **−26.57 dB** (met with 1.6 dB) and worst-case deviation to 4 MHz = **0.49 dB** (met by 0.01 dB).
That is razor-thin on F9; 11 pF/82 pF gives 0.51 dB / −25.72 dB, i.e. the mirror trade. **There is
no value set at this topology with comfortable worst-case margin on both** — which is the
architect's own "real-pole bound" restated. This is a MEDIUM for `circuit-architect` to settle with
a real simulation and a Monte Carlo, not with my hand analysis. F10 is SOFT/CLAUDE, so it is not a
gate failure; it is a spec the board currently meets only on the typical part.

---

## VBIAS = 1.100 V — consistent, and M-1 is closed

**Consistency.** Netlist: `R8.1`→`+3V3_A`, `R8.2`/`R9.1`→`VBIAS_DIV`, `R9.2`→`GND`, `R10.1`→
`VBIAS_DIV`, `R22.2`→`VBIAS` with `R19.1` and both channels' `R_bot.2`. Values `R8` = 22.0k,
`R9` = 11.0k in `analog_power_ref.py`. Recomputed:

| Quantity | My value | Stated | |
|---|---|---|---|
| `VBIAS` = 3.3·11/33 | 1.10000 V | 1.1000 V | ✓ (11/33 = ⅓ exactly, both E24) |
| `VREF_FE` = VBIAS·19.1/20.1 | 1.04527 V | 1.0453 V | ✓ |
| Tap at AIN = 0 = VBIAS·950/999.9 | 1.04510 V | 1.0452 V | 0.1 mV nit, already disclosed |
| Zero-input differential offset | 0.169 mV × 2.004 = **0.34 mV** | 0.34 mV | ✓ ≈0.7 LSB |
| Buffer input span over ±10 V | 0.5460 … 1.5442 V | 0.546 … 1.544 V | ✓ |
| Full-scale output | ±0.49906 × 2.004 = 2.0 V p-p diff | 2.0 V p-p | ✓ |

Only one stale reference survives anywhere in the tree — see N-3. Divider ratios, gain, input
impedance and the /20 topology are untouched, as claimed.

**M-1 is closed at the top end.** At AIN = +10 V the buffer input is 1.5442 V. With `+3V3_A` 2 %
low the OPA355 ceiling is 3.234 − 1.5 = 1.734 V, and `VBIAS` tracks the same rail down to
1.078 V, so the input falls to 1.5235 V: **≈208 mV of margin** (the architect says ≈180 mV, more
conservative; both are ~2.2× the 85 mV that raised M-1). Not a wash — genuinely fixed.

**The architect's rejection of my 23.0 k / 10.0 k is correct on both grounds, and I withdraw it.**
23.0 kΩ is in no standard series (E96 offers 22.6 and 23.2). And at `VBIAS` = 1.000 V the SPEC I5
survival case AIN = −30 V puts the buffer input at 1.000·0.950095 − 30·0.049905 = **−0.547 V**,
past the OPA355's (V−) − 0.5 V input abs max, at a current (~10 µA through 47.5 kΩ ‖ the 1 kΩ
clamp leg) where the BAV99 has not yet begun to conduct. At 1.100 V it is −0.452 V, inside. My
proposal was worse on two counts.

**Partly traded, not moved — L-5.** The bottom-end margin during that same I5 event went from
143 mV (at 1.200 V) to **48 mV**. `design_risks.md` R-3's table records the −0.452 V figure
explicitly, so this was a conscious trade, not an oversight, and the BAV99's soft forward
conduction at ~10 µA (Vf ≈ 0.45–0.55 V, not 0.7 V) begins helping right at that level. But note
that the −0.5 V abs-max figure itself is **not on disk either** — `OPA355NA_3K_SUMMARY.md` states
no absolute-maximum input range, only "check the datasheet's Input Common-Mode Voltage Range". Two
of this block's three tightest numbers now rest on datasheets nobody in this pipeline has read.

---

## Notes (revision 2)

- **N-3 — stale comments in the top-level assembly file, the exact trap H-1 was.**
  `circuits/dual_adc_usb/__main__.py:51-52` still reads `# 1.200 V divider return` and
  `# 1.140 V = 0.95 * VBIAS`. The nets are right; only the comments lie, in the first file a
  reader opens. Fix:
  ```python
  VBIAS = Net('VBIAS')       # 1.100 V divider return; U4A through R22 (10 R)
  VREF_FE = Net('VREF_FE')   # 1.0453 V = 0.95025 * VBIAS, U4B output
  ```
- **N-4 — BOM labels for `R_f` are swapped relative to the code.** `sourcing/sourced_bom.md`
  lines 30–31 label `107/207` = "R_f (OUT+)" and `108/208` = "R_f (OUT−)"; the netlist has
  `R107.2` on pin 11 (OUT−) and `R108.2` on pin 10 (OUT+). Identical 1.00 kΩ parts, zero
  electrical effect — the block coder's Decision 3 swap was simply not propagated to the BOM's
  descriptive column. `C103`/`C104`'s labels are correct.
- **N-5 — the two FDA output nodes are the only unnamed nets in the AFE** (`N$34`/`N$35`,
  `N$37`/`N$38`). They now carry `C_f`, `R_f` and `R_o` and are filter-critical; every other
  internal AFE node got a name. Suggest `Net('CH%d_OUTP' % ch)` / `'CH%d_OUTN'`.
- **N-6 — no action.** The architect's FDA summing-node range (1.030–1.363 V) is 50 mV below my
  1.080–1.413 V. Theirs is the more conservative on the low end, so R-3's conclusion is
  unaffected. The THS4551 input-CM range is still unread (same gap as H-2).
- **N-7 — `C112`/`C212` (L-1) still skipped**, with a TODO in the file, as permitted.

---

## Summary table (revision 2)

| ID | Sev | Status | Owner |
|---|---|---|---|
| H-1 | HIGH | **CLOSED** — MFB topology and all response claims verified independently | — |
| H-2 | HIGH | **OPEN** — 3rd order depends on an unverifiable SBOS778D claim; pull the PDF before fab | `datasheet-librarian`, then `circuit-architect` if wrong |
| M-1 | MED | **CLOSED** at top end (208 mV); bottom end traded to 48 mV → L-5 | — |
| M-2 | MED | **OPEN** — F10 met at nominal only, missed by 1.84 dB at worst case; margin is a parasitic | `circuit-architect` |
| L-5 | LOW | OPEN — I5 survival margin 143 → 48 mV vs an OPA355 abs max not on disk | human, before fab |
| L-1…L-4 | LOW | unchanged from revision 1 | — |
| N-3…N-5 | note | comment/label/naming hygiene, no electrical effect | `skidl-assembler`, `part-sourcer`, `afe_channel` coder |

**Gate: 0 errors + 33/33 footprints → PASS.** Export stays unblocked; the exported netlist and
BOM are current and correct.

---
---

# Revision 1 record (retained verbatim)

Everything below is the revision 1 report, kept for its evidence: the 19-message classification
table, the false-positive verdicts, the supply/abs-max table, the FPGA bank proof, and the full
checklist. **Two of its findings are superseded by revision 2 above: H-1 is closed, and M-1's
recommended `R8` = 23.0 k / `R9` = 10.0 k was rejected by the architect on grounds revision 2
confirms are correct — do not apply it.**

## Findings by severity

### H-1 — HIGH — The differential anti-alias filter is 2nd-order, not 3rd. Misses SPEC F9 and F10.

Both AFE channels (`afe_channel.py`, R1xx/C1xx and R2xx/C2xx). The code comments label the
output network "poles 2 and 3 of the 3rd-order ~6 MHz differential anti-alias filter" and claim
"24 dB at 15 MHz". Traced from the netlist, that is not what is built.

`C_cm_p` (220 pF, `adc_in_p`→GND) and `C_diff` (470 pF, `adc_in_p`→`adc_in_n`) hang off **the
same node, behind the same 33 Ω series resistor** `R_o_p`. Two capacitors on one node behind one
resistor are one pole, not two. Differentially they are in parallel, so they merge; the
common-mode caps add a common-mode pole only, which does nothing to the differential signal the
ADC actually digitizes. This is the classic "capacitor in a branch that sets no pole" failure —
the filter silently lost an order.

What the netlist values actually give, per differential half-circuit:

| Pole | Elements | Frequency |
|---|---|---|
| 1 — FDA feedback | `R_f` 1 kΩ ∥ `C_f` 27 pF (+0.6 pF internal ≈ 27.6 pF) | 5.77 MHz |
| 2 — output RC (differential) | `R_o` 33 Ω into `C_cm` 220 pF + 2·`C_diff` 940 pF = 1160 pF | **4.16 MHz** |
| (common-mode only, not in the signal path) | `R_o` 33 Ω into `C_cm` 220 pF | 21.9 MHz |

The code's own arithmetic for pole 2 is also wrong on its own terms — it computes "2×33 Ω with
470 pF → 5.1 MHz", neglecting that `C_cm_p`/`C_cm_n` load the same nodes differentially. Do not
trust those inline numbers.

Resulting response `|H| = 1/√((1+(f/5.77)²)(1+(f/4.16)²))`, against spec:

| Frequency | Actual | SPEC | Verdict |
|---|---|---|---|
| 4.0 MHz | **−4.55 dB** | F9: −0.5 dB | **fails by 4.1 dB** |
| −3 dB corner | **3.1 MHz** | F9: usable band to 4–5 MHz | **fails** |
| 7.0 MHz | **−9.8 dB** | F10: ≥ 25 dB | **fails by 15 dB** |
| 15 MHz (architecture's claimed alias edge) | −20.4 dB | code claims 24 dB | claim overstated |

**This is not a two-capacitor fix, and it is not the block coder's to own.** F9 (−0.5 dB at
4.0 MHz *and* −3 dB ≤ 5 MHz) together with F10 (≥ 25 dB above 7 MHz) are not simultaneously
achievable at 3rd order — and F10's own parenthetical says "≥ 3rd-order". Solving the Butterworth
order for both constraints, −0.5 dB at 4 MHz with 25 dB at 7 MHz needs **n ≈ 7**; with the −3 dB
pinned at 5 MHz, F9's two clauses alone need **n ≈ 5**. So the requirement pair is internally
inconsistent at the order the architecture budgeted, and the architecture papered over it by
redefining the alias edge to 15 MHz (valid only if the host's 2:1 decimation includes a digital
low-pass — if it just drops samples, 5–15 MHz content folds straight into the band).

**Owner: `circuit-architect`.** It must reconcile F9/F10/F3 and re-budget the filter order, then
hand `afe_channel` a corrected pole plan. Minimum honest options: relax F10 to what the 15 MHz
alias edge and a real decimation filter justify, or raise the filter order (a 5th-order
realization needs another RC section per leg between the FDA and the ADC, with the common-mode
caps split behind their own series resistors so they form a genuine second stage).

Interim, if the passband matters more than the stopband, raising both poles recovers F9's flatness
but cannot reach F10 at this order:

```python
# afe_channel.py — poles up; F9 flatness only, NOT an F10 fix.
c_f_p = Part('Device', 'C', ref=c_ref(3), value='10pF', footprint=_FP_C0603)  # was 27pF
c_f_n = Part('Device', 'C', ref=c_ref(4), value='10pF', footprint=_FP_C0603)
c_diff = Part('Device', 'C', ref=c_ref(5), value='150pF', footprint=_FP_C0603)  # was 470pF
c_cm_p = Part('Device', 'C', ref=c_ref(6), value='68pF', footprint=_FP_C0603)   # was 220pF
c_cm_n = Part('Device', 'C', ref=c_ref(7), value='68pF', footprint=_FP_C0603)
```

### M-1 — MEDIUM — OPA355 input common-mode headroom is 0.26 V at full scale; left open by phase 04.

`datasheets/OPA355NA_3K_SUMMARY.md` explicitly deferred this: *"Input common-mode range does NOT
[reach the rails] … check the datasheet's Input Common-Mode Voltage Range spec, page ~5, before
finalizing R_top/R_bot values."* Nothing downstream closed it, so it is checked here.

Buffer input (`CHn_BUFIN` = divider tap, `U_bufn` pin 3) over the full ±10 V input range, with
the divider returning to `VBIAS` = 1.200 V and a 49.9 k/999.9 k ratio:

- AIN = +10 V → 1.200 + (10 − 1.200)·0.049905 = **1.639 V**
- AIN = 0 V → **1.140 V** (= `VREF_FE`, so zero differential out — DC design is correct)
- AIN = −10 V → 1.200 + (−11.2)·0.049905 = **0.641 V**

Verified against the datasheet PDF below: OPA355's VCM window is (V−) − 0.1 V to **(V+) − 1.5 V**
= −0.1 V … **1.800 V** on this 3.3 V rail. The +10 V case lands at 1.639 V — inside it, but with
only **85 mV of worst-case margin** once the rail's −2% and the divider tolerances are stacked,
and that margin is spent exactly where SPEC F11's full-scale ENOB is measured. **Not a violation,
so not a gate failure**, and phase 04's question is answered affirmatively (the existing R_top/R_bot
are admissible). A two-resistor change tripling the margin is given in § Analog verification.

### L-1 — LOW — THS4551 has one 100 nF for four VS+ pins.

`afe_channel.py` gives `u_fda` a single `c_ref(10)` 100 nF; pins 5/6/7/8 are all tied to `+3V3_A`.
TI's layout guidance for the RGT package is a 0.1 µF at each supply pin pair plus local bulk. The
channel does carry `c_ref(9)` 1 µF on the same rail (nominally the buffer's), so the rail is not
bare. Cosmetic for ERC; worth one more 0402 per channel at layout.

### L-2 — LOW — `ADC_OE_N` / `ADC_PDWN` pull-downs fight the FPGA's configuration-time pull-ups.

`adc_dual.py` R44/R45 are 10 kΩ to GND so the ADC defaults to outputs-enabled / not-powered-down
while U6 is unconfigured. Gowin GW1N I/Os have weak pull-ups active during configuration. At the
weak end (~50 kΩ) the net sits at 3.3·10/60 = 0.55 V — safely a valid low. At the strong end
(~10 kΩ) it would sit near 1.65 V, indeterminate. Consequence if it goes wrong is benign (the
ADC's 24 outputs idle instead of driving, or drive early into 3.3 V FPGA pins — no abs-max issue
either way), but if you want it deterministic, drop R44/R45 to 2.2 kΩ.

### L-3 — LOW — Trigger input J5 has series resistance but no clamp.

`fpga_core.py`: J5.1 → R17 10 k pull-down → R16 1 k series → U6 pin 74. An external trigger relies
on the FPGA's internal ESD diodes through R16; a 12 V misconnection injects ~8.7 mA into the pin
clamp. SPEC I5's ±30 V survival requirement is scoped to the BNC inputs, not this header, so this
is a robustness note, not a spec miss.

### L-4 — LOW — SMF5.0CA standoff sits under the USB VBUS maximum.

`usb_c_input.py` D2 = SMF5.0CA, V_RWM = 5.0 V, on a rail specified to 5.25 V (USB 2.0 VBUS max).
Below V_BR(min) = 6.4 V so conduction is leakage-only and the part is not stressed, but a 5.0 V
standoff on a 5.25 V rail is tighter than the usual practice of one step up. Acceptable as drawn.

### N-1 — NOTE — The assembler's warning bookkeeping double-counts by one.

`handoffs/05_coding.md` item 2 is headed "Known false positives — all 19 warnings", then lists
6 + 7 + 4 + 1 + 1 = 19 **ERC** warnings *plus* the "Missing tag" line as a sixth bullet. The tag
line is a **netlist-generation** warning in `__main__.log`, not one of the 19 in `__main__.erc`.
The 19 ERC warnings are fully accounted for; the total message count is 20.

### N-2 — NOTE — `datasheets/FT232HL-REEL_SUMMARY.md` has VREGIN wrong; the coder correctly overrode it.

The summary's pin table says VREGIN (40) comes "from `+3V3_D`". `usb_bridge.py` instead ties it to
`+5V_IN` and takes VCCD (39) as a 3.3 V **output**, citing FT_000288 §6.1 "USB Bus Powered
Configuration". The coder is right, and it is load-bearing: the FT232H must run *before* the
PWREN#-gated load switch closes, so it cannot be fed from `+3V3_D`, which is downstream of that
switch. Fix the summary, not the code.

---

## Every ERC message, classified

All 19 warnings fall into five groups. **Every one is benign, and every one of the assembler's
five false-positive claims held up** — but each was re-verified here against the actual pin
electrical type SKiDL used, not accepted on the strength of the justification.

Pin-type ground truth, read back through SKiDL from the same libraries the run used
(`func` codes: 1=INPUT, 2=OUTPUT, 3=BIDIR, 5=PASSIVE, 7=PWRIN, 8=PWROUT, 13=NOCONNECT):

| Group | Count | Message | Root cause | Claim verdict |
|---|---|---|---|---|
| `EE_CS`, `EE_CLK` | 6 | 1× "No drivers" + 2× "Insufficient drive" each | `Interface_USB:FT232H` types **pin 45 EECS = INPUT (1)** and **pin 44 EECLK = INPUT (1)**, though the FT232H is the Microwire *master* and drives them. U8 `93CxxC` pin 1 CS and pin 2 SCLK are also INPUT. Net of all-INPUT pins ⇒ no driver. Genuine symbol pin-type error. | **ACCEPTED — verified.** Mechanism named specifically and confirmed in the library. No driver or pull-up is actually missing; FTDI's reference needs pull-ups only on DO (`R_eedo` present). |
| `FT232H_3V3` | 7 | "Insufficient drive current" on VPLL(8), VCCD(39), VPHY(3), U8 VCC(8), VCCIO(46/24/12) | **Pin 39 VCCD = PWRIN (7)** in the symbol, but with VREGIN at 5 V it is the internal LDO's 3.3 V *output*. A rail whose only source is typed PWRIN has no power driver. | **ACCEPTED — verified.** Topology is FTDI's standard bus-powered configuration and is required by the PWREN# sequencing (see N-2). Count matches exactly: 7 PWRIN pins on the net. |
| `VBUS_RAW` | 4 | "Insufficient drive current" on J1 A4/A9/B4/B9 | All four J1 VBUS pads are **PWRIN (7)**; the only other pins on the net are passive (`D1[5]`, `D2[1]`, `FB1[1]`). The actual supply is the host cable, off-board. | **ACCEPTED — verified.** 7 nodes on the net in the netlist, 4 of them PWRIN ⇒ 4 warnings. |
| `XO_VDD` | 1 | "Insufficient drive current" on X1 pin 4 VDD | **X1 pin 4 = PWRIN (7)**, fed through FB4, a passive ferrite, which breaks `+3V3_A`'s POWER drive. | **ACCEPTED — verified.** Deliberate supply isolation (`clock_20m` decision 4). |
| `V5_LDO_IN` | 1 | "Insufficient drive current" on U3 pin 6 IN | **U3 pin 6 = PWRIN (7)**, fed through FB3 — the SPEC-P8 pi-filter. Same ferrite mechanism. | **ACCEPTED — verified.** Load-bearing for P8, must not be "fixed". |
| **Total** | **19** | | | **5 of 5 claims upheld** |

Netlist-generation message (`__main__.log`, not part of the 19):

| Message | Classification | Disposition |
|---|---|---|
| `WARNING: Missing tag on  instantiated at <frozen importlib._bootstrap>:491` | **NOTE** — the unnamed root hierarchy node | **ACCEPTED.** The consequence the coder's Decision 7 was protecting against — netlist instability — is disproved by direct measurement: two consecutive runs are byte-identical (0-line diff). I did not independently reproduce the claim that tagging the root makes `generate_netlist()` raise; the property that matters is stability, and that is verified. Do not "fix" this. |

No message was reclassified upward. Nothing in the 19 is masking a real defect: `EE_DATA`
(pin 43 = BIDIR) drew no warning, consistent with the wiring, and no net is missing a driver that
the schematic intends to have one.

---

## Footprint validation

```
python3 ${CLAUDE_PLUGIN_ROOT}/scripts/validate-footprints.py circuits/dual_adc_usb
✓ All footprints valid (33 checked across 9 files)     exit 0
```

Clean — no missing footprint, so nothing here blocks KiCad import. Every distinct footprint string
used, with its source:

| Footprint | Used by |
|---|---|
| `Resistor_SMD:R_0603_1608Metric` | most R |
| `Resistor_SMD:R_0805_2012Metric` | R1x1/R1x2 divider top legs (voltage rating) |
| `Resistor_SMD:R_Array_Concave_4x0402` | RA1–RA6 |
| `Capacitor_SMD:C_0402_1005Metric` / `C_0603_1608Metric` / `C_0805_2012Metric` | C |
| `Capacitor_Trimmer_SEHWA:C_Trimmer_SEHWA_STC3MA-2Pin_4.5x3.2mm` | C101/C201 — **project-local library, generated in phase 04, not KiCad stock** |
| `Inductor_SMD:L_0603_1608Metric` | FB1–FB4 |
| `Inductor_SMD:L_Changjiang_FNR3015S` | L1 |
| `Package_TO_SOT_SMD:SOT-23-5` | U1, U9 |
| `Package_TO_SOT_SMD:SOT-23-6` | D1, U_buf1/2 |
| `Package_TO_SOT_SMD:SOT-23` | D_clamp1/2 |
| `Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm` | U2, U3 |
| `Package_DFN_QFN:WQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm` | U_fda1/2 |
| `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` | U6 — EP size still unverified against Gowin's package drawing (phase 04 carried this forward) |
| `Package_QFP:TQFP-64_10x10mm_P0.5mm` | U5 |
| `Package_QFP:LQFP-48_7x7mm_P0.5mm` | U7 |
| `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | U4, U8 |
| `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` | J1 |
| `Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal` | J2, J3 — **open risk from phase 04**: pad count/shell geometry not confirmed against KH-BNC50-3511 |
| `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` / `1x02` | J4, J5 |
| `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` | X2 |
| `Oscillator:Oscillator_SMD_Kyocera_KC2520Z-4Pin_2.5x2.0mm` | X1 |
| `LED_SMD:LED_0603_1608Metric` | D4, D5 |
| `Diode_SMD:D_SOD-123F` | D2 |

---

## Checklist — defects that pass ERC

| Check | Result |
|---|---|
| **Supply span vs absolute maximum** | **PASS.** Every IC's actual rails vs abs max, traced from the netlist — table below. No violation; the checklist's FDA trap (a 5.5 V part across ±4.2 V) does **not** occur: THS4551 is single-supply 3.3 V, total span 3.3 V against 5.5 V abs max. |
| **Signal level vs receiver's rail** | **PASS.** Every crossing is 3.3 V→3.3 V. ADC drivers on `+3V3_ADCD` → FPGA banks on `+3V3_D`; FT232H VCCIO 3.3 V → FPGA; X1 at `XO_VDD` (3.3 V) → U5 CLK and U6 pin 11. Pull-ups checked too: R15→`+3V3_D`, R14/R_eedo/R_pwren→`FT232H_3V3` (3.3 V), all onto 3.3 V pins. `PWREN_N` at 0/3.3 V into U9's GND-referenced EN# (V_IH 2.0 V min) on a 5 V part — valid, no level shifter needed. No 1.8 V domain exists anywhere on this board. |
| **FPGA/MCU bank voltages** | **PASS — and the checklist's specific trap was checked against the PDF, not the comment.** See § FPGA bank verification. |
| **Active filter topology** | **FAIL → finding H-1.** The only checklist item that caught a real defect. |
| **Exposed pads** | **PASS.** Every `-1EP` footprint has its EP pin on a net: U2 pin 7→GND, U3 `EP`→GND, U6 pin 89→GND, U_fda1/U_fda2 pin 17→GND. No other part has an EP (TQFP-64, LQFP-48, SOIC-8, SOT-23 have none). |
| **Reproducibility** | **PASS.** Two consecutive runs → `diff` of `outputs/dual_adc_usb.net` = **0 lines**, date line included. Zero `_1`-suffixed refdes. 169 parts / 146 nets. |

Additional structural check, beyond the checklist: parsed all 146 nets and confirmed **no pin
appears on more than one net** (0 hits), so nothing was silently merged. All rails are distinct in
the netlist, including the pairs most at risk of collapsing together — `VBIAS` (6 pins) vs
`VBIAS_DRV` (3 pins), so R22's capacitive-load isolation survives into the netlist, and
`+3V3_A` (37) / `+3V3_D` (28) / `+3V3_ADCD` (11) / `FT232H_3V3` (18) all separate.

### Supply span vs absolute maximum

| IC | Supply pins → net | Actual | Abs max | Margin |
|---|---|---|---|---|
| U1 SY8089A1AAC | IN/EN → `+5V_SW` | 5.0 V | 6 V | ✓ |
| U2 TLV75801 | IN/EN → `+3V3_D` | 3.32 V | 6 V | ✓ |
| U3 TLV75733 | IN → `V5_LDO_IN`, EN → `+5V_SW` | 5.0 V | 6 V | ✓ |
| U4 TLV9062 | V+ → `+3V3_A`, V− → GND | 3.3 V | 6 V | ✓ |
| U5 ADS5231 | AVDD → `+3V3_A`, VDRV → `+3V3_ADCD` | 3.32 V | **3.6 V** | ✓ (AVDD range 3.0–3.6) |
| U6 GW1NR-9 | VCC → `+1V2_D`; VCCX/VCCIO0-3 → `+3V3_D` | 1.199 V / 3.32 V | 1.32 V / 3.75 V | ✓ |
| U7 FT232H | VREGIN → `+5V_IN` | 5.0 V (5.25 max) | 5.5 V | ✓ tight |
| U8 93LC56B | VCC → `FT232H_3V3` | 3.3 V | 6.5 V | ✓ |
| U9 AP2161WG-7 | IN → `+5V_IN` | 5.25 V | 6 V | ✓ |
| U_buf1/2 OPA355 | V+ → `+3V3_A`, V− → GND | 3.3 V | 7 V | ✓ |
| U_fda1/2 THS4551 | VS+ → `+3V3_A`, VS− → GND | 3.3 V total | **5.5 V total** | ✓ |
| X1 | VDD → `XO_VDD` | 3.3 V | 3.6 V | ✓ |

`+1V2_D` = 0.55·(1 + 11.8/10) = **1.199 V** (R20/R21) and `+3V3_D` = 0.600·(1 + 45.3/10) =
**3.318 V** (R4/R5), both recomputed from the netlist values; worst-case over the SY8089 V_REF
spread (591/600/609 mV) is 3.268–3.368 V, still well under the FPGA's 3.75 V.

### FPGA bank verification — the checklist's 1.8 V PSRAM trap does not apply to this MPN

The checklist warns that "the GW1NR-9's PSRAM bank is 1.8 V only", and `fpga_core.py` ties
**every** VCCIOx to 3.3 V while routing `ADC_D2[9:11]` onto pins 13/14/15 and `FPGA_CLK` onto
pin 11 — all Bank 3. If Bank 3 were pinned to 1.8 V, that would be 3.3 V logic into a 1.8 V bank
plus an over-volted in-package die: a dead board. `datasheets/GW1NR-LV9QN88PC6-I5_SUMMARY.md`
asserts the trap does not apply, so the claim was checked against the datasheet PDF directly.

From `datasheets/GW1NR-LV9QN88PC6-I5.pdf` (Gowin DS117-2.9.3E):

- **Table 2-2, Package and Memory Information:** package **`QN88` → Memory `SDR SDRAM`, 64 M,
  16 bits**. `QN88P` is the row that carries PSRAM. This MPN, `GW1NR-LV9**QN88**PC6/I5`, is the
  non-P package.
- **§3.2.1 SDR SDRAM:** *"The supply voltage for the SDRAM interface is 3.3V; the BANK voltage
  that connects to the SDRAM needs to be 3.3V."*
- **§3.2.2 PSRAM**, scoping note: *"The features described below apply to the packages of MG81P,
  QN88P, LQ144P, MG100P, MG100PF, MG100PT, and MG100PS"* — `QN88` is absent — and only then
  *"The power supply for the PSRAM interface is 1.8V."*

So the embedded memory here is SDR SDRAM, the bank it connects to **must** be 3.3 V, and tying
all four banks to 3.3 V is not merely tolerated but required. The phase-04 correction (QN88 =
SDRAM, QN88P = PSRAM) is **right**, and the coder honoured it correctly.

Pin-to-bank map read back from the generated symbol (89/89 pins), confirming the code's own bank
comments and that no I/O landed on a supply pin:

| Bank | VCCIO pin(s) → net | I/O pins in use | Signals |
|---|---|---|---|
| 3 (IOL, left) | 12 → `+3V3_D` | 3, 5–9, 11, 13–16 | `ADC_PDWN`, JTAG, `RECONFIG_N`, `FPGA_CLK` (11 = IOL15A/**GCLKT_6**), `ADC_D2[9:11]`, `ADC_OE_N` |
| 2 (IOB, bottom) | 23, 44 → `+3V3_D` | 17–20, 25–34, 37–42, 47 | `ADC_D1[11:0]`, `ADC_D2[8:0]` |
| 1 (IOR, right) | 58 → `+3V3_D` | 52 | `FIFO_CLK` (52 = IOR17A/**GCLKT_3**) |
| 0 (IOT, top) | 64, 67, 78 → `+3V3_D` | 68–75, 79–88 | FIFO bus + control, `MODE[1:0]` straps |

Both clocks are on real global-clock pins, and pin 12 is kept as `VCCIO3` distinct from the
64/67/78 group exactly as phase 04 instructed. SPEC **F14** is satisfied structurally: `ADC_CLK`
comes from X1 through `R_s1` and is never sourced from an FPGA PLL.

### Signal-chain arithmetic, recomputed from netlist values

Confirming the AFE's DC design independently (it is correct, and worth recording so the H-1 rework
does not disturb it): divider ratio 49.9 k/999.9 k = 0.049905 returning to `VBIAS` = 1.200 V, so
AIN 0 V → tap 1.140 V = `VREF_FE` → **zero differential output at zero input**. Gain to the ADC
= 0.049905 × 1 × (1.00 k/499) = 1/10.02, so ±10 V in → **±1.000 V differential = 2.0 Vpp**, which
is the ADS5231's full scale. `VBIAS` = 3.3·12.0/33.0 = 1.20000 V and `VREF_FE` = 1.200·19.1/20.1
= 1.1403 V both check out. Input impedance 999.9 kΩ meets **I4** (1 MΩ ±1%). At the ±30 V of
**I5** the tap reaches 2.637 V / −0.357 V, drawing 28.8 µA — the clamp does not conduct on the
positive side and the divider is not stressed.

FDA internal summing-node potential, solved from the netlist network (`R_g` 499, `R_f` 1 k,
`VOCM` 1.5 V): **1.260 V** at zero input, **1.426 V** at full scale — inside THS4551's
input common-mode range on a 3.3 V supply. FDA outputs swing 1.001–1.999 V around `VOCM`, against
an output range that reaches 0.2 V of each rail. ✓

---

## Analog verification — OPA355 input common-mode

This is the open item `datasheets/OPA355NA_3K_SUMMARY.md` deferred to whoever finalized
R_top/R_bot ("check the datasheet's Input Common-Mode Voltage Range spec, page ~5, before
finalizing"). Nothing between phase 04 and here closed it. Closing it now, from the PDF.

From `datasheets/OPA355NA_3K.pdf`, Electrical Characteristics, INPUT VOLTAGE RANGE:

```
VCM   Common-mode voltage range    (V–) – 0.1  …  (V+) – 1.5   V
CMRR  Common-mode rejection ratio  VS = 5.5 V, –0.1 V < VCM < 4 V    66 / 80 dB
```

The CMRR test condition (−0.1 V to 4.0 V at V_S = 5.5 V) independently confirms the upper limit
is **(V+) − 1.5 V**, not a rail-to-rail input. On this board V+ = `+3V3_A` = 3.3 V, so:

**Usable VCM window = −0.1 V … 1.800 V.**

Buffer input (`CHn_BUFIN`) against that window, nominal and worst case:

| Condition | Buffer input | Limit | Margin |
|---|---|---|---|
| AIN = −10 V | 0.641 V | ≥ −0.1 V | 0.741 V ✓ |
| AIN = 0 V | 1.140 V | — | ✓ |
| AIN = +10 V, nominal rail | 1.639 V | ≤ 1.800 V | **0.161 V** |
| AIN = +10 V, `+3V3_A` low by 2% (3.234 V ⇒ limit 1.734 V) | 1.639 V | ≤ 1.734 V | **0.095 V** |
| AIN = +10 V, rail low **and** ±0.5% divider/VBIAS tolerance stacked | 1.649 V | ≤ 1.734 V | **0.085 V** |

**Verdict: within spec, but only just — 85 mV of worst-case margin at positive full scale.** No
violation, so this does not fail the gate, and phase 04's question is answered: the existing
R_top/R_bot values *are* admissible. The concern is that the margin is spent exactly where SPEC
**F11** (≥ 10.5 ENOB at full scale) is measured — the top ~1.7% of the positive range is where
CMRR degradation and offset shift would show up as distortion. The negative side has 8× the
margin; the window is badly asymmetric because `VBIAS` sits at 1.200 V, near the middle of a
window whose top is 1.8 V.

Beyond ±10 V the buffer input leaves the CM window (2.637 V at the +30 V of SPEC **I5**), but that
is non-destructive — abs-max input is (V−) − 0.5 V to (V+) + 0.5 V and the BAV99 clamp holds
`bufin` inside it — and the signal is out of range anyway. Overrange behaviour is saturation, not
damage. Acceptable.

**Recommended fix — two resistor values, and it costs nothing else.** Lower `VBIAS` from 1.200 V
to 1.000 V by re-splitting the R8/R9 divider while keeping the 33 kΩ sum. Every other property of
the front end is preserved, because the zero-input match and the gain depend only on the divider
*ratio*, not on `VBIAS`'s absolute value:

```python
# analog_power_ref.py — VBIAS 1.200 V -> 1.000 V: 3.3 * 10.0/33.0 = 1.00000 V exactly.
R8 = Part('Device', 'R', ref='R8', value='23.0k', footprint=_FP_R0603)   # was 21.0k
R9 = Part('Device', 'R', ref='R9', value='10.0k', footprint=_FP_R0603)   # was 12.0k
```

Verified consequences of that change:

- `VREF_FE` = 0.95025 × 1.000 = **0.950 V** (R19/R11 unchanged).
- Zero-input match still exact: tap at AIN = 0 is `VBIAS`·(950/999.9) = 0.950 V = `VREF_FE`, so
  differential output is still precisely zero at zero input.
- Full-scale gain unchanged: ±10 V → ±1.000 V differential = **2.0 Vpp**, still the ADS5231's FS.
- Buffer input window becomes **0.451 V … 1.449 V** ⇒ worst-case headroom **285 mV**, a 3.4×
  improvement, and roughly symmetric.
- FDA summing node stays in range across the sweep: 0.967 V at −10 V, 1.133 V at 0 V, 1.299 V at
  +10 V (THS4551 input CM range on 3.3 V comfortably contains these).
- `VBIAS` keeps its AC-ground role and R22's isolation unchanged; the divider current and source
  impedance are essentially unchanged (sum stays 33 kΩ).

This is a recommendation, not a gate failure. It touches `analog_power_ref` (values only) and
would be sensibly bundled with the H-1 filter rework rather than done as a separate pass.

---

## Summary table

| Severity | ID | Finding | Owner |
|---|---|---|---|
| HIGH | H-1 | Differential anti-alias filter is 2nd-order, not 3rd; −4.6 dB at 4 MHz (F9 wants −0.5), −9.8 dB at 7 MHz (F10 wants 25). C_cm caps set no differential pole. F9+F10 unachievable at 3rd order. | `circuit-architect`, then `afe_channel` |
| MEDIUM | M-1 | OPA355 VCM limit is (V+) − 1.5 V = 1.800 V; +10 V input reaches 1.639 V, leaving 85 mV worst-case margin where F11's full-scale ENOB is measured. Closes phase 04's deferred check — values are admissible. Fix: R8 23.0k / R9 10.0k ⇒ VBIAS 1.000 V, margin 285 mV, all else preserved. | `analog_power_ref` (values only) |
| LOW | L-1 | One 100 nF for THS4551's four VS+ pins. | layout / `afe_channel` |
| LOW | L-2 | R44/R45 10 k pull-downs vs FPGA config-time pull-ups. | `adc_dual` (optional) |
| LOW | L-3 | Trigger header has series R but no clamp. | accepted as drawn |
| LOW | L-4 | SMF5.0CA 5.0 V standoff on a 5.25 V-max rail. | accepted as drawn |
| NOTE | N-1 | Assembler's warning count double-counts the netlist tag warning (19 ERC + 1 log = 20). | none |
| NOTE | N-2 | FT232H summary's VREGIN source is wrong; code correctly overrode it. | `datasheet-librarian` |
| NOTE | — | 19 ERC warnings, all benign; 5 of 5 false-positive claims upheld. | none |

**Gate: 0 errors, 33/33 footprints valid → PASS.** Export is unblocked. H-1 is a spec-compliance
defect, not a netlist defect, and I am explicitly **not** dispositioning SPEC F9/F10 on my own
authority — they are SOFT/CLAUDE requirements, so the user or the architect must decide whether to
relax them or rework the filter before fabrication.
