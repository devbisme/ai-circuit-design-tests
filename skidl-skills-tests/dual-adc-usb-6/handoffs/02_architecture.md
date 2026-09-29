---
phase: 02_architecture
agent: circuit-architect
circuit: dual_adc_usb
written: 2026-09-22T00:00:00Z
status: complete
revision: 2
next_phase: 03_sourcing
escalated_from: handoffs/06_erc.md
---

# Phase 2 handoff — Architecture (rev.2)

<!-- revised: narrow rework driven by handoffs/06_erc.md findings HIGH-1, HIGH-2 and OI-6.
     Scope is exactly three things: (a) the input ESD clamp's node AND part, (b) the
     line-15/line-96 DRVDD contradiction in net_plan.md, (c) naming and blessing the
     FB1-FB4 allocation. Nothing else in rev.1 is reopened. Every rev.1 decision not
     restated below still stands. -->

**One sentence:** the input TVS moves from `CHn_BNC` to `CHn_BUFIN` **and changes part** —
relocating the 15 pF ESD9B5.0ST5G alone would have traded three broken HARD requirements
for a fourth.

---

## Decisions

### D-r2.1 — The input ESD clamp moves to `CHn_BUFIN`, behind R102 (adopted)

`net_plan.md` rev.1 line 35 put D101/D201 across the BNC centre contact, upstream of both
the 909 kΩ attenuator and the 1 kΩ limiter. The ERC reviewer's analysis is correct and I
adopt the relocation. Recomputed from the real values rather than taken on trust
(R100 = 909 kΩ, R101 = 90.9 kΩ → VREF_OFF = 1.807 V, ratio 90.9/999.9 = **1/11.0**):

| requirement | rev.1 (clamp on BNC) | rev.2 (clamp on BUFIN) |
|---|---|---|
| **F2** ±10 V FS (HARD) | node swings ±10 V into a 5 V-standoff / 7.8 V-VBR part → **conducting 2.2 V past breakdown at rated input** | node swings **0.734 – 2.552 V**; nothing conducts |
| **I3** ±50 V DC (HARD) | both limiters downstream; bench source drives a SOD-923 part through its own Zout → **fails short** | BUFIN pinned at +4.0 V / −0.7 V by D100; node balance gives **≈26 µA** into the clamp vs the BAV199's 200 mA rating (**7600×**); the TVS sits below its 5 V standoff and never conducts during the DC fault |
| **I2** 1 MΩ ∥ ~20 pF (HARD) | 15 pF on the BNC node → **Cin ≈ 35 pF**, outside a 10× probe's trim range | BNC node carries only C100·C101/(C100+C101) = 22·220/242 = **20.0 pF exactly** |

Working for F2: `V(BUFIN) = 1.807 + (Vin − 1.807) × 0.090909` → +10 V gives 2.552 V,
−10 V gives 0.734 V. Working for I3 at Vin = +50 V: (50 − 4.03)/909 kΩ = +50.6 µA in,
(4.03 − 1.807)/90.9 kΩ = −24.5 µA out through R101, remainder ≈ 26 µA into D100.
Full derivation is now in `net_plan.md` §"Input protection".

### D-r2.2 — The clamp part changes: ESD9B5.0ST5G → **ESD9L5.0ST5G** (C82326, onsemi)

This is the part of the fix the escalation did not ask for, and it is the part that matters.

**F8 / F9 verdict, which was the question put to me:** with the relocation *and the
incumbent 15 pF part*, **F8 (HARD, −3 dB ≥ 4 MHz) is not safe.** With the low-capacitance
part it is. Numbers, from the measured 4.45 MHz / −29.4 dB chain cascaded with the real
pole `f_p = 1/(2π · R102 · C_node)`:

| clamp part | Cj | C_node | f_p | −3 dB nominal | −3 dB worst case† | 10 MHz |
|---|---|---|---|---|---|---|
| ESD9B5.0ST5G (15 pF) | 15 pF | 22.5 pF | 7.07 MHz | 4.08 MHz | **3.83 MHz — fails F8** | −33 dB |
| **ESD9L5.0ST5G (0.9 pF)** | 0.9 pF | 8.4 pF | 18.9 MHz | **4.39 MHz** | **4.18 MHz** | **−30.5 dB** |

† filter C0G caps at their +5 % limit (f_c → 4.24 MHz) **and** Cj at its datasheet max.

`f_p = 1/(2π × 1000 Ω × 8.4 pF) = 18.95 MHz`; loss at 4.45 MHz =
`10·log10(1 + (4.45/18.95)²)` = 0.233 dB; solving
`10·log10(1+(f/4.45)^8) + 10·log10(1+(f/18.95)²) = 3` gives 2.781 + 0.227 = 3.008 dB at
**f = 4.39 MHz**. At 10 MHz: −29.4 − 1.07 = **−30.5 dB**. **F8 ✓ (9.7 % margin), F9 ✓
(5.5 dB margin).**

**Correction to the escalation brief — `C_node` is not 15 pF, it is 22.5 pF.** The brief
computed the pole from the TVS alone. `CHn_BUFIN` also carries D100 (BAV199, two junctions,
~1.5 pF each → ~3 pF), U100's input capacitance (TPH2501, ~3 pF) and ~1.5 pF of trace —
**~7.5 pF of baseline that the phase-6 4.45 MHz measurement did not include either**. That
is what turns the brief's comfortable 10.6 MHz pole into 7.07 MHz and the passband edge
into 3.83 MHz worst case.

**Why ESD9L5.0ST5G and not the alternatives** (full comparison in `ic_selection.md` §6):
same 5 V standoff, **same SOD-923 land pattern** the coder is already being told to correct
to, same onsemi family, same Extended tier, **92,164 in live stock** against an incumbent
row that had never been sourced at all — and 0.9 pF instead of 15 pF. It is unidirectional,
which is correct here: BUFIN never goes below +0.734 V in service, and negative faults are
already pinned at −0.7 V by D100. MSKSEMI's 0.3 pF bidirectional C2830130 lost on SOD-882
being a *different* land pattern on a design whose footprint gate has already failed twice
on package variants, and on 1,033 stock vs 92,164, to buy 0.01 MHz. BORN's C316041 lost the
same way (DFN1006-2). Deleting the TVS entirely lost because I3 says "clamped,
series-limited" and the BAV199 is a low-leakage switching pair, not a characterised ESD
device.

### D-r2.3 — **The brief's τ-matching premise is wrong, and it is a second reason the part had to change**

The brief states that the 15 pF "lands behind R102, not on the mid node, so both legs stay
at 20.0 µs." **R102 does not isolate at the compensation frequency.** At 1/(2π·20 µs) ≈
8 kHz, R102 = 1.00 kΩ is negligible against the divider's 82.6 kΩ Thevenin source, so
everything on `CHn_BUFIN` appears in parallel with C101. R102 only isolates in the MHz
decade — which is exactly why it makes a pole there and not a τ error. Computed:

| clamp-node C | τ_top = R100·C100 | τ_bot = R101·(C101+C_node) | mismatch | HF-vs-DC gain step |
|---|---|---|---|---|
| 7.5 pF (no TVS) | 20.00 µs | 20.68 µs | +3.4 % | −0.265 dB (−3.0 %) |
| **8.4 pF (rev.2 part)** | 20.00 µs | **20.76 µs** | **+3.8 %** | **−0.296 dB (−3.4 %)** |
| 22.5 pF (rev.1 part) | 20.00 µs | 22.04 µs | **+10.2 %** | **−0.772 dB (−8.5 %)** |

The 0.9 pF part contributes **0.4 %** of the mismatch; the rest is the BAV199, the amplifier
and the trace, which risk R11 already owned (its "~2–3 %" is corrected to ~3–4 %). The 15 pF
part would have tripled it and hung a **−0.77 dB flat droop across the entire passband**.
Recorded in `design_risks.md` R11.

### D-r2.4 — `+3V3A_ADC` carries **AVDD only**; DRVDD is on `+3V3D` (closes OI-6)

`net_plan.md` line 15 contradicted line 96 and the block signature. **Line 15 was wrong and
line 96 is right**; the code already follows line 96. Corrected in place. Reasons, in the
order that matters:

1. It keeps 12 switching CMOS output drivers per ADC off a 55 mA low-noise analog LDO whose
   whole purpose (decision 9 / risk R5) is a clean AVDD. Output-driver switching current on
   the analog rail is the classic way to put a data-dependent tone into a converter's own
   supply.
2. It is marginally better on the VBUS budget. `I_DRVDD` ≈ 13 outputs × 5 pF × 3.3 V ×
   10 MHz × 0.5 toggle ≈ 1.1 mA, round up to **3 mA/ADC = 6 mA**. Through the LDO that is
   6 mA drawn from VBUS; through the 88 %-efficient buck it is
   `6 mA × 3.3 V / (5.0 V × 0.88)` = **4.5 mA**. **Saves ≈1.5 mA** on a 293 mA budget —
   genuinely slight, and not the reason for the change. Rev.1's 293 mA becomes **≈292 mA**;
   P3 still does not fire.
3. `+3V3D` goes 225 mA → **231 mA**. `+3V3A_ADC`'s budget is **left at ≤55 mA** rather than
   shaved to ~49 mA: the AVDD/DRVDD split is derived, not datasheet-quoted, and a 400 mA LDO
   has no reason to be re-budgeted on an estimate.

### D-r2.5 — FB1–FB4: the coder's allocation is **blessed as built**

| ref | from | to | purpose |
|---|---|---|---|
| FB1 | `VBUS_SW` | `LDO_ADC_IN` | R5's literal prescription — bead + C11 (10 µF) in front of U5 |
| FB2 | `VBUS_SW` | `LDO_AMP_IN` | same, in front of U6 |
| FB3 | `LDO_ADC_OUT` | `+3V3A_ADC` | output-side isolation; C12 (1 µF) before, C16/C26 after |
| FB4 | `LDO_AMP_OUT` | `+3V3A_AMP` | same on the amp rail |

R5 as written named only the input pair; the coder placed the output pair and recorded it as
an assumption. It is the right call. Arithmetic (BLM21PG601SN1D, **R_DC = 140 mΩ**,
C41556732, live-verified — the coder's "~0.15 Ω / ~8 mV" comment is correct):

- **Cost:** 55 mA × 0.140 Ω = **7.7 mV** on `+3V3A_ADC`, 43 mA × 0.140 Ω = **6.0 mV** on
  `+3V3A_AMP`. Both outside the LDO loop, both far inside every fed part's tolerance.
- **Benefit:** at 1 MHz, where the bucks switch and the TPS73633's PSRR has already
  collapsed, the bead is ≈40 Ω into C16‖C26 = 1.1 µF (|Z| = 0.145 Ω) → **≈49 dB** of
  rejection nothing else provides. **Do not delete FB3/FB4 any more than FB1/FB2.**
- **Residual, stated not implied:** C12 – FB3 – C16‖C26 is a series tank at
  `1/(2π√(1 µH · 0.524 µF))` ≈ **220 kHz** with **Q ≈ 9** (damped only by 140 mΩ + ESR),
  contributing ≈**50 µVrms** = **0.10 LSB** of 488 µV. Accepted. Logged as R5's addendum
  with the damping fix if bench measurement disagrees.
- **Binding on the coder:** the TPS73633's output capacitor (C12, C15) must stay **between
  OUT and the bead** — it is the loop compensation cap. The current code does this correctly.

### Rev.1 decisions 1–12 stand unchanged

Two ADCs on one clock; XC6SLX9-2TQG144C; W9825G6KH-6I; FX2LP slave FIFO; 1 MΩ ∥ 20 pF built
from 909 k/90.9 k + 22 p/220 p; no negative rail; **4th-order Butterworth AAF at 4.45 MHz,
values untouched**; LDO'd analog rails off VBUS_SW; ADC clock straight from X1; TPS22919
soft start; +1V2 before +3V3D. **The filter is not re-centred** — see `Do not redo`.

---

## Artifacts

| File | Contains | Read it when | rev.2? |
|---|---|---|---|
| `architecture/net_plan.md` | Every net, type, connected refs, per-block interface lists | Always — before writing any code | **yes** — lines 13/15/16 (rails), the BNC/BUFIN rows, new FB1–FB4 table, new §"Input protection" |
| `architecture/ic_selection.md` | Candidates per block, winner + why the loser lost, all design arithmetic | Before substituting any part | **yes** — new §6, input ESD clamp |
| `architecture/skeleton_bom.md` | function / MPN / package / qty / notes; `[calc]` = do not substitute | Sourcing, and before changing any passive | **yes** — input ESD diode row |
| `architecture/design_risks.md` | R1–R13, EMI / PI / thermal / layout / timing | Layout, and phase 4 for R2/R4/R12 | **yes** — R5 addendum, R11 restated, R12 and R13 new |
| `architecture/block_diagram.md` | Mermaid block diagram + clock tree + signal flow | Orientation | no (never showed D101) |

## Block manifest

**Unchanged from rev.1.** No block gained or lost an interface net; no signature changed.
D101/D201 keep their refdes and stay inside `analog_frontend`.

| block_id | block_name | function_signature | interface_nets |
|---|---|---|---|
| `usb_front` | USB-C input + soft start | `usb_front(vbus, vbus_sw, usb_dp, usb_dm, gnd)` | `VBUS, VBUS_SW, USB_DP, USB_DM, GND` |
| `power` | Rails + references | `power(vbus_sw, v3v3d, v1v2, v3v3a_adc, v3v3a_amp, vref_off, vcm_ref, gnd)` | `VBUS_SW, +3V3D, +1V2, +3V3A_ADC, +3V3A_AMP, VREF_OFF, VCM_REF, GND` |
| `analog_frontend` | ±10 V AFE + AAF + FDA (**2 instances**, `ch="CH1"/"CH2"`) | `analog_frontend(ch, bnc_in, avdd, vref_off, vcm_ref, ain_p, ain_n, gnd)` | `CHn_BNC, +3V3A_AMP, VREF_OFF, VCM_REF, CHn_AIN_P, CHn_AIN_N, GND` |
| `adc_channel` | 12-bit ADC (**2 instances**) | `adc_channel(ch, ain_p, ain_n, clk_adc, data, otr, pdwn, avdd, dvdd, gnd)` | `CHn_AIN_P, CHn_AIN_N, CLK_ADC, ADCn_D[11:0], ADCn_OTR, ADC_PDWN, +3V3A_ADC, +3V3D, GND` |
| `clocking` | 10 MHz XO + isolation buffer | `clocking(vdd, clk_adc, clk_fpga, gnd)` | `+3V3D, CLK_ADC, CLK_FPGA, GND` |
| `fpga_core` | Capture FSM host, config flash, JTAG | `fpga_core(adc1_d, adc2_d, adc1_otr, adc2_otr, adc_pdwn, clk_fpga, sdr_dq, sdr_a, sdr_ba, sdr_clk, sdr_cke, sdr_cs_n, sdr_ras_n, sdr_cas_n, sdr_we_n, sdr_ldqm, sdr_udqm, fifo_d, ifclk, slwr_n, slrd_n, sloe_n, pktend_n, fifoadr, flagb, flagc, v3v3d, v1v2, gnd)` | `ADC1_D[11:0], ADC2_D[11:0], ADC1_OTR, ADC2_OTR, ADC_PDWN, CLK_FPGA, SDR_DQ[15:0], SDR_A[12:0], SDR_BA[1:0], SDR_CLK, SDR_CKE, SDR_CS_N, SDR_RAS_N, SDR_CAS_N, SDR_WE_N, SDR_LDQM, SDR_UDQM, FIFO_D[7:0], IFCLK, SLWR_N, SLRD_N, SLOE_N, PKTEND_N, FIFOADR[1:0], FLAGB, FLAGC, +3V3D, +1V2, GND` |
| `buffer_memory` | 32 MB SDRAM | `buffer_memory(sdr_dq, sdr_a, sdr_ba, sdr_clk, sdr_cke, sdr_cs_n, sdr_ras_n, sdr_cas_n, sdr_we_n, sdr_ldqm, sdr_udqm, v3v3d, gnd)` | `SDR_DQ[15:0], SDR_A[12:0], SDR_BA[1:0], SDR_CLK, SDR_CKE, SDR_CS_N, SDR_RAS_N, SDR_CAS_N, SDR_WE_N, SDR_LDQM, SDR_UDQM, +3V3D, GND` |
| `usb_bridge` | FX2LP slave FIFO | `usb_bridge(usb_dp, usb_dm, fifo_d, ifclk, slwr_n, slrd_n, sloe_n, pktend_n, fifoadr, flagb, flagc, v3v3d, gnd)` | `USB_DP, USB_DM, FIFO_D[7:0], IFCLK, SLWR_N, SLRD_N, SLOE_N, PKTEND_N, FIFOADR[1:0], FLAGB, FLAGC, +3V3D, GND` |

8 blocks, 10 instances -> modular mode. **Only `analog_frontend` (both instances) needs
re-coding for rev.2.**

## Parts by block

**Unchanged from rev.1.**

| block_id | refs |
|---|---|
| `usb_front` | J1, U1, U2, R1, R2, R3, C1, C2, C3 |
| `power` | U3, U4, U5, U6, U7, L1, L2, R10–R19, C10–C29, FB1–FB4 |
| `analog_frontend` (CH1) | J2, U100, U101, U102, U103, R100–R112, C100–C115, D100, D101 |
| `analog_frontend` (CH2) | J3, U200, U201, U202, U203, R200–R212, C200–C215, D200, D201 |
| `adc_channel` (CH1) | U150, R150, C150–C161 |
| `adc_channel` (CH2) | U250, R250, C250–C261 |
| `clocking` | X1, U8, R21, R22, R23, C30, C31 |
| `fpga_core` | U30, U31, J4, D30, D31, R30–R39, C40–C69 |
| `buffer_memory` | U40, R40, C70–C78 |
| `usb_bridge` | U50, U51, Y1, R50–R55, C80–C91 |

---

## Next phase must

### `skidl-block-coder` — `analog_frontend` (both instances). This is the whole code change.

Exactly two lines of net assignment move, and one part definition changes. Nothing else in
the block is touched — not a resistor, not a filter cap, not a footprint on any other part.

```python
# WAS (rev.1):
    D_esd = Part('Diode', 'ESD9B5.0ST5G', ref=f'D{b + 1}', value='ESD9B5.0ST5G',
                 footprint='Diode_SMD:D_SOD-523')
    bnc_in += J[1], D_esd[1]        # centre contact
    gnd    += D_esd[2]
    att    += R_clamp[1]
    bufin  += R_clamp[2], D_clamp[3], U_buf['IN+']

# IS (rev.2):
    D_esd = Part('Device', 'D_TVS', ref=f'D{b + 1}', value='ESD9L5.0ST5G',
                 footprint='Diode_SMD:D_SOD-923')
    bnc_in += J[1]                  # centre contact -- NO clamp on this node
    att    += R_clamp[1]
    bufin  += R_clamp[2], D_clamp[3], D_esd[1], U_buf['IN+']   # pin 1 = CATHODE
    gnd    += D_esd[2]                                         # pin 2 = ANODE
```

- **Refdes is unchanged** — D101 / D201, same as rev.1.
- **Polarity is now load-bearing.** ESD9L5.0ST5G is **unidirectional**: cathode (pin 1) to
  `CHn_BUFIN`, anode (pin 2) to `GND`. Reversing it shorts the signal to ground through a
  forward diode. The rev.1 part was bidirectional and orientation-free; this one is not.
- **Symbol:** there is no local `ESD9L5.0ST5G` symbol (checked — `Diode:ESD9B5.0ST5G` exists,
  `ESD9L…` does not). Use `Device:D_TVS` (or `Device:D_Zener`) with `value='ESD9L5.0ST5G'`.
  Both are EXACT-resolving 2-pin passive symbols; **no symbol generation is needed**, so
  phase 4 is not re-entered for this.
- **Footprint:** `Diode_SMD:D_SOD-923`. This also closes ERC finding HIGH-4 — the rev.1
  `D_SOD-523` was wrong for the old part too, so do not "restore" it.
- Update the block docstring: the clamp chain is now
  `BNC → R100‖C100 → ATT → R102 → BUFIN{D100, D101, U100.IN+}`, and record that R102's pole
  into the ~8.4 pF clamp node is **18.9 MHz**, costing 0.06 MHz of passband edge.

### `skidl-block-coder` — `adc_channel`, `power`, `fpga_core`

**No rev.2 change.** `adc_channel`'s DRVDD-on-`+3V3D` assumption is now ratified in
`net_plan.md` — delete the "net_plan.md says otherwise" caveat from its docstring and stop
carrying it as an unverified fact. `power`'s FB1–FB4 assumption is likewise ratified; its
FB3 comment ("~0.15 Ω, ~8 mV") is **correct** — the real DCR is 140 mΩ. The other phase-6
findings (U31's SOIC-8 land pattern, U7A's 22 Ω isolation, the 43 mA docstring figure) are
unrelated to this revision and still stand as phase-6 wrote them.

### `part-sourcer`

1. **D101/D201 — re-source.** `ESD9L5.0ST5G`, **LCSC C82326**, onsemi, SOD-923, 92,164 in
   stock (live), ¥0.0429 @100, Extended. Vetted **second source: C7379964** (MSKSEMI,
   `ESD9L5.0ST5G`, SOD-923, 0.5 pF, 18,153) — drop-in on the same land pattern with the same
   polarity. This closes phase-6 findings MEDIUM-5 (unsourced row, SPEC R3) and HIGH-4
   (package) together.
2. **Delete the "≤0.5 pF" note wherever it appears.** It was wrong by 30× for the old part
   and it is what hid this defect from phases 2–5. The rev.2 row carries **0.9 pF max**.
3. **This part is NOT freely substitutable any more.** Rev.1's `Next phase must` #2 listed
   "ESD parts" as free. **Corrected: Cj > 2 pF on `CHn_BUFIN` is a HARD-requirement
   violation (F8).** Any substitute must be ≤2 pF, Vrwm ≥ 5 V, and ideally SOD-923.
4. Everything else in rev.1's sourcing instructions is unchanged, including the packages
   fixed by decision (909 kΩ stays 0805 for its 150 V working voltage; C0G mandatory in the
   attenuator, both Sallen-Key sections and the kickback network; no BGA).

### `erc-reviewer`

Re-gate after the `analog_frontend` change. Expect the two U5/U6 drive warnings to persist —
they are still correct to ignore, and FB1–FB4 are now architecturally blessed, so nobody
should "fix" them by deleting a bead.

---

## Carried forward

- **Assumption, stated because it is the one number in D-r2.2 I could not verify from a
  datasheet curve:** the clamp node's non-TVS capacitance is **~7.5 pF** (BAV199 ~3 pF +
  TPH2501 input ~3 pF + trace ~1.5 pF). Every margin in D-r2.2 and D-r2.3 rests on it. It is
  a conservative-side estimate; if the real figure is lower the margins only improve, and
  even at a 12 pF node the rev.2 part still lands at 4.33 MHz. **The same estimate would have made
  the rev.1 part fail harder, not pass.**
- **Assumption: ESD9L5.0ST5G leakage at 0.73–2.55 V and ≤85 °C is ≤50 nA** (spec is 1 µA max
  at the full 5 V standoff, 150 °C corner). At 82.6 kΩ source impedance, 1 µA would be
  **0.91 V referred to input — 4.5 % FS**. New risk **R12**; phase 4 should pull the onsemi
  leakage-vs-voltage curve. A substitute with a worse Ir spec is not safe.
- **Assumption: the BLM21PG601SN1D's low-frequency inductance is ≈1 µH** — the datasheet
  publishes impedance at 100 MHz, not L. The 220 kHz / Q≈9 figure in R5's addendum depends
  on it. The conclusion (0.10 LSB, accepted) is insensitive to a 2× error either way.
- **New risk R13 — ESD energy lands on the attenuator mid node.** Moving the clamp behind
  R102 means a strike couples through C100 into `CHn_ATT`, ~700 V for a few nanoseconds
  before R102 bleeds it into the clamp. This is the conventional scope front-end compromise,
  C100/C101 are already 100 V C0G and R100 is an 0805, and **rev.1 had the identical exposure
  plus a TVS that failed short at rated input.** Accepted, not deferred.
- **R11 is restated, not merely renumbered.** Its "~2–3 % mismatch" becomes **~3–4 %** now
  that the clamp node's capacitance is counted properly. Still low severity, still accepted,
  still no trimmer available in the JLCPCB catalogue (I2's "trimmable" wording remains
  overturned, for the rev.1 reason).
- Rev.1's remaining carried-forward items are unchanged and still binding: R2 oscillator
  jitter (now closed by phase 4's ≤1 ps part), R3 thin ADC stock, the AD9237 power
  assumption, the TPS22919 slew assumption, F11 dropped, R7's gain/offset overrun.

## Do not redo

- **The anti-alias filter values.** 147 Ω/270 pF/220 pF and 137 Ω/680 pF/100 pF are
  unchanged. Re-centring both Sallen-Key sections to absorb a pole was the alternative to
  changing a 3-cent diode; it would mean re-deriving the 4th-order response, re-sourcing 8
  capacitors per channel, and re-running phase 6's filter audit — to buy back margin the
  part change buys for free. **The part changes; the filter does not.**
- **The attenuator.** 909 k / 90.9 k / 22 p / 220 p are exact. Rev.2 does not touch them, and
  the clamp deliberately does **not** go on `CHn_ATT` — there it would push the bottom leg to
  90.9 kΩ × 235 pF = 21.4 µs and break compensation outright.
- **The clamp node.** `CHn_BUFIN`, behind R102. Not the BNC, not the mid node.
- Everything in rev.1's `Do not redo`: the five [U] requirements, burst-to-RAM (F6), the ADC
  clock from its own oscillator, the ÷11 × 1.1 = 0.1000 gain pairing.
- **The two U5/U6 ERC drive warnings.** Permanent, correct, and now doubly load-bearing:
  FB1–FB4 are blessed architecture.

## Receipt

- **Revision 2.** Scope: 1 topology defect (clamp node), 1 part substitution it forced,
  2 documentation corrections. 8 blocks and 10 instances unchanged; no signature or
  interface-net change.
- **1 block needs re-coding:** `analog_frontend` (both instances) — 2 net-assignment lines
  and 1 part definition.
- **ICs: 14 (12 unique), unchanged.** 1 BOM line changed (D101/D201).
- **HARD requirements restored: F2, I3, I2.** F8 verified at **4.39 MHz** (needs ≥4 MHz),
  F9 at **−30.5 dB** (needs ≥25 dB), both *with* the new pole included.
- **Risks: R1–R13.** Unresolved: R3 (thin ADC stock), R12 (TVS leakage unverified),
  R13 (mid-node ESD, accepted). R5 extended to four ferrites.
- **1 premise in the escalation brief corrected** (D-r2.3: R102 does not isolate the clamp
  node from the divider at 8 kHz).
- Status: complete. Next: `part-sourcer` for D101/D201, then `skidl-block-coder`
  (`analog_frontend`), then re-gate with `erc-reviewer`.
