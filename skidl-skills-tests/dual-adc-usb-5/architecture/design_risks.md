# Design risks — dual_adc_usb

Severity: **H** = can make the board fail a HARD requirement · **M** = costs performance or
a rework cycle · **L** = watch item.

---

## R-1 · ADC availability, lifecycle, and minimum clock — **H**

`ADS5231IPAGT` is a **single-source, Extended-tier, legacy TI part** with stock 154 (below
SPEC Q4's 200). Three separate exposures:

1. **Lifecycle.** The ADS523x family is old; NRND is plausible. JLCPCB's mirror carries no
   lifecycle data.
2. **Stock.** 154 units is 30 boards' worth. Fine for 5 prototypes, thin for anything after.
3. **Minimum clock frequency.** The whole clocking architecture rests on 20 MHz being a
   legal ADC clock (the JLCPCB record says 20–40 MHz). If the real minimum is higher, the
   raw-capture-at-20-MSPS scheme collapses.

**Mitigation, pre-decided:** if the minimum clock is >20 MHz, change X1 to 40.000 MHz (same
footprint, same family, **zero layout change**) and make a 4:1 FPGA decimator a firmware
requirement. Do not re-architect anything else. If the part is EOL or stock collapses, the
substitution ladder is in `ic_selection.md` § 1 — and note that every rung changes channel
count, pin count, or rail count, so it is an architecture escalation, not a drop-in.

**Action:** datasheet phase must read the minimum-clock and lifecycle pages first, before
anything else in this design.

---

## R-2 · Divider compensation is a manual trim, and it cannot be designed out — **M**

The 1 MΩ ÷20 attenuator is flat only when `R_top·C_top = R_bot·C_bot_total`. `C_bot_total`
includes the OPA355's input capacitance (~1 pF), the BAV99 clamp's junction capacitance
(~3 pF for the pair), and trace/pad stray (~3 pF) — roughly 7 pF of a ~89 pF total, none of
it predictable to better than ±30 %. That ±30 % of 8 % is a **±2 % step in the HF response**,
i.e. ±0.17 dB appearing somewhere in the 1–5 MHz region, straight into F9's 0.5 dB budget.

| Option | Pros | Cons |
|---|---|---|
| **Trimmer capacitor (chosen)** | nulls all stray, per-board; standard scope practice | manual trim step per channel per board; a mechanical part |
| Fixed C, computed | no trim labour; cheaper | leaves an unpredictable few-% HF step; kills F9 margin |
| Fixed C + host-side digital equalisation | no trim, no part | the ÷20 ratio error is real gain error; equalising it needs a per-board calibration sweep, which is more work than turning a screw |

**Chosen: trimmer**, one per channel, 2–10 pF. **The sourcer must not substitute a fixed
capacitor to save $0.40.**

**Action:** document the trim procedure (square wave at ~1 kHz into the BNC, adjust for flat
corners — the same procedure as compensating a scope probe) for the eventual test doc.

---

## R-3 · Buffer input common-mode margin — **M** (improved in rev 3, still the tightest number)

<!-- revised: rev3 — ERC finding M-1: VBIAS 1.200 V -> 1.100 V. -->

The tightest number in the analog design. OPA355's input common-mode limit on a 3.3 V rail is
**(V+) − 1.5 V = 1.800 V**, and **1.734 V** with the rail 2 % low. The buffer input sits at
`0.950095·VBIAS + 0.049905·AIN`:

| `VBIAS` | input at AIN = +10 V | worst-case margin | input at AIN = −30 V (I5) |
|---|---|---|---|
| 1.200 V (rev 1–2, as built) | 1.639 V | **85 mV** | −0.357 V |
| **1.100 V (rev 3)** | **1.544 V** | **≈180 mV** | **−0.452 V** ✓ inside abs max |
| 1.000 V (ERC's proposal) | 1.449 V | 285 mV | −0.547 V ✗ past (V−) − 0.5 V |

**rev 3 sets `VBIAS` = 1.100 V** (R8 = 22.0 kΩ, R9 = 11.0 kΩ; 3.3·11/33 = 1.1000 V exactly).
That is 2.1× the margin where SPEC F11's full-scale ENOB is measured, and unlike the 1.000 V
proposal it keeps the −30 V overrange case inside the OPA355's abs-max input so the BAV99
never has to conduct in normal spec'd operation. It also avoids a non-standard resistor: the
23.0 kΩ the ERC review asked for **is not an E96, E24 or E192 value**.

Gain, the zero-input match and input impedance are untouched — they depend on *ratios* only
(`net_plan.md` § VBIAS = 1.100 V). Residual differential offset at zero input is 0.34 mV
(≈0.7 LSB, covered by F12).

This is also *why the attenuator is ÷20 and not ÷10*: at ÷10 the node would swing
0.35…2.35 V and exceed the limit outright. The FDA's G = 2 restores full scale afterwards.

**Residual exposure:**
- A buffer substitution that changes the CM range breaks this **silently** — the board simply
  distorts near +10 V. **Any buffer substitution must be checked against "input CM range
  ≥ 1.65 V on a 3.3 V supply".**
- **The THS4551's own input CM range has never been read from a datasheet** — phase 04 could
  not obtain the PDF. The FDA summing node moves from 1.093–1.426 V to **1.030–1.363 V** in
  rev 3. That is a 63 mV shift and almost certainly fine, but it is asserted, not verified;
  it is a second reason 1.100 V beats 1.000 V (which would have reached 0.967 V). Get
  SBOS778's input-CM spec before the board spin.

---

## R-4 · Sample-clock jitter is unverified — **M**

F14 allows 14 ps RMS; D10 asks for ≤5 ps. **No JLCPCB oscillator record publishes phase
jitter.** Commodity CMOS XOs are typically 1–5 ps RMS integrated (12 kHz–20 MHz), so the
chosen part very probably passes with ~3× margin — but "probably" is not a spec.

At 4.5 MHz full scale, jitter-limited SNR = −20·log₁₀(2π·f·t_j): 14 ps → 68 dB (≈11.0 ENOB),
5 ps → 77 dB (negligible), 30 ps → 61.5 dB (≈9.9 ENOB, **fails F11**). So the failure mode
is real and the threshold is not far above typical.

**Action:** datasheet phase must obtain a real datasheet number for X1, or substitute a
part that specifies jitter (SiTime SiT8008, Epson SG-210STF, Abracon ASDMB class).
Layout: X1 on `+3V3_A` behind FB4, its ground returned to the analog region, its output
stubs to ADC and FPGA both <15 mm with 33 Ω series damping at the source.

---

## R-5 · Anti-alias filter — **CLOSED in rev 3** (was: values not synthesised) — **L**

<!-- revised: rev3 — ERC finding H-1. Risk closed: the pole plan is now specified, not provisional. -->

**What went wrong.** Rev 1/2 left `C_f`/`R_o`/`C_diff`/`C_cm` as placeholders "giving the right
topology and part count". They did not: the topology itself was wrong. `C_cm` and `C_diff` sit
on the same node behind the same `R_o`, so **differentially they merge into one pole** and the
filter was **2nd-order, not 3rd** — −3 dB at 3.1 MHz and **−4.55 dB at 4.0 MHz** (ERC H-1).
A "provisional value" note is not a substitute for checking that the network has the order it
claims; that is the lesson, and it is why rev 3 specifies exact values instead.

**Why adding RC sections was never going to work.** For a cascade of *real* poles, a droop
budget of D dB at 4 MHz caps the attenuation at 16 MHz at (16/4)²·D = 16·D. So 0.5 dB of
passband droop buys **at most ~8 dB** at 16 MHz — *at any order*. The ERC review's suggestion
to "split the CM caps behind their own series resistors so they form a genuine second stage"
would have added 6 parts and bought ~2 dB. **Complex poles are mandatory**, so the filter must
run through the FDA's feedback, not merely after it.

**Resolution: 2nd-order MFB around U_fda + one output RC = 3rd-order Butterworth,
f₋₃dB ≈ 6.1 MHz.** Exact values and realized response: `net_plan.md` § Anti-alias filter.
Cost: **+3 parts per channel (+6 board-wide)** — `R_mfb` ×2 and one differential `C_mfb`.
No inductors, so the reason rev 1 rejected the LC elliptic still holds. Nominal response
−0.15 dB at 4.0 MHz, −25.3 dB at 16 MHz; worst case over ±5 % C0G and ±1 % R,
≤0.40 dB and ≥22.7 dB.

**Residual risk (why this is still listed, at L).** The response is computed analytically from
the MFB transfer function, **not SPICE-simulated**, and it ignores the FDA's own ≈65 MHz
closed-loop pole (a decade up — it adds <0.2 dB below 10 MHz but does lift the stopband floor
above ~30 MHz, harmlessly). The MFB node is now a filter-critical node: keep `R_g`/`R_f`/
`R_mfb`/`C_mfb` tight around the FDA and keep the two legs' layout symmetric, or the CM/DM
split of `C_mfb` degrades. Verify on the bench with a network analyser before committing to a
second board spin.

---

## R-12 · The 16 MHz alias edge is only valid if the host's decimator filters — **H**, and it is **software**

<!-- revised: rev3 — new risk, made explicit as ERC H-1 demanded. -->

The board samples at **20 MSPS** and delivers **10 MSPS/ch** (SPEC F3) by **2:1 decimation in
host software** (decision 4). Two different alias edges follow, and only one of them is the
analog filter's problem:

1. **The ADC's own sampling (20 MSPS).** Energy above 10 MHz folds into 0–10 MHz; to land
   inside the **0–4 MHz measurement band** it must be above **16 MHz** (|f − 20| ≤ 4).
   This is the analog filter's job, and 25.3 dB at 16 MHz is what rev 3 delivers. **This
   argument does not depend on the host at all.**
2. **The 2:1 decimation.** Everything the ADC legitimately digitised between **5 and 10 MHz**
   folds straight into 0–5 MHz if the host simply drops every other sample. The analog filter
   gives only 1–13 dB there, and no achievable analog filter could give more without wrecking
   F9 (that would demand ≥25 dB at 5 MHz with −0.5 dB at 4 MHz ⇒ n ≈ 9).

**So the answer to the ERC review's question is: yes — the 15/16 MHz alias edge depends on the
host's 2:1 decimation containing a real digital low-pass.** Recorded as a requirement on
software that is otherwise out of scope:

> **S1 [HARD, DERIVED] — host decimation filter.** The host's 2:1 decimation from 20 MSPS to
> 10 MSPS/ch must apply a digital low-pass with **≥40 dB stopband above 5.0 MHz** and ≤0.1 dB
> ripple to 4.0 MHz before discarding samples. A ~33-tap symmetric FIR at 20 MSPS is enough
> and costs nothing on any host CPU. **Naïve sample-dropping makes the board fail F9/F10 in
> software, with no hardware symptom** — this is the one place where a firmware/software
> shortcut silently destroys the analog design.

Consequence if S1 is not honoured: the honest spec collapses to "flat to 4 MHz, aliases from
5–10 MHz unattenuated". No hardware change can rescue it.

---

## R-6 · Power integrity: one switcher, in-band — **M**

The SY8089 switches at **1.5 MHz, inside the 0–5 MHz measurement band**. Its ripple reaching
the front end would appear as a fixed spur, not as broadband noise — the worst kind for a
digitizer, because it looks like signal.

**Mitigations designed in:**
- The analog rail is an **LDO fed from the 5 V node, not from the buck output**. Buck ripple
  reaches analog only by conducting back into 5 V and then through the LDO.
- **FB3 + 10 µF π-filter** at that LDO's input: >20 dB above 1 MHz.
- LDO PSRR 46 dB at 100 kHz (degrading with frequency) on top.
- The ADC's `DRVDD` comes from `+3V3_ADCD` — `+3V3_D` through **FB2** — so 24 data lines'
  worth of switching current returns to the *digital* rail, not the analog one.

**Residual:** SPEC P8 asks for ≥50 dB PSRR at 100 kHz and the chosen LDO gives 46 dB. **P8
is met by the LDO plus its input filter, not by the LDO alone.** If a TPS7A2033-class
low-noise LDO is in stock, take it — straight F11 margin.

**Action (layout):** keep the buck's switch node, inductor, and input/output loop entirely
within the digital region; no analog trace may cross under L1.

---

## R-7 · Ground and layout partition — **M**

There is **one** `GND` net (see `net_plan.md`). The partition is a copper instruction:

- **4-layer stack:** signal / **solid GND** / power / signal. Do **not** cut the GND plane.
- Partition by **placement and by power-plane splits**, not by ground splits: analog parts
  (J2, J3, dividers, buffers, FDAs, U5's analog half, U3, U4, X1) in one contiguous region;
  digital (U6, U7, U1, U2, L1, LEDs, headers) in another; U5 straddles the boundary with its
  analog pins facing analog.
- The ADC data bus crosses the boundary once, damped at the source, on the digital-side
  layer with GND directly beneath.
- `USB_DP`/`USB_DM` as a 90 Ω differential pair, length-matched, referenced to the GND
  plane, no stubs except the USBLC6.
- `AIN1`/`AIN2` from BNC to divider: short, guarded, and **away from any switching node** —
  47.5 kΩ of source impedance at the divider node makes that node the highest-impedance,
  most pickup-prone spot on the board. Guard-ring it with `VBIAS`, not with GND (a GND guard
  adds capacitance to the wrong leg of the compensated divider).

**Action:** the layout phase (outside this pipeline) must be handed this section verbatim.

---

## R-8 · Thermal — **L**, but check the packages

Total board dissipation ≈2.2 W at 5 V, ~373 mA typical. Worst-case ≈485 mA.

| Dissipator | Power | Package requirement |
|---|---|---|
| U2, 1.2 V core LDO | **315 mW** | **thermal-pad package mandatory** — a SOT-23-5 would rise ~80 °C |
| U3, analog LDO | 200 mW | WSON-6 with pad: ~14 °C rise → 64 °C junction at 50 °C ambient ✓ |
| U5, ADC | 320 mW | TQFP-64 handles it; keep the thermal land connected to the plane |
| U7, FT232H | ~350 mW incl. its internal 5 V→3.3 V LDO | LQFP-48 ✓ |
| U6, FPGA | ~440 mW | QFN-88 centre pad **must** be soldered to the plane |

H3 is 0…+50 °C commercial. Nothing is marginal *provided* U2 and U3 keep their thermal pads.

---

## R-9 · USB enumeration inrush and pre-configuration current — **L** (solved in rev 2)

<!-- revised: rev2 — rev 1's bare P-FET could not be turned off by a 3.3 V PWREN#; the gating
it claimed did not exist. Re-solved with an integrated active-low-EN switch. -->

A bus-powered device may draw ≤100 mA before USB configuration. This board draws ~373 mA
once running — most FTDI-based boards simply violate this.

**What rev 1 got wrong.** It gated the rail tree with **Q1**, a bare P-FET (HL2301A) with its
source on `+5V_IN` and its gate on PWREN#. PWREN# is a 3.3 V CBUS output, so the *most
positive* gate level is ~3.3–3.5 V → Vgs = −1.5…−1.7 V, past the part's −0.4…−1.0 V
threshold. Q1 stayed partially on and the whole tree came up at plug-in. No value of the gate
pull-up fixes it: a pull-up strong enough to hold the gate at 5 V fights the FT232H's drive.

**Solved by design (rev 2):** **U9 = AP2161WG-7**, a 1 A current-limited high-side switch
whose **EN is active-low and GND-referenced** (VIH 2.0 V min, VIL 0.8 V max). PWREN# is
active-low, so it drives EN directly — no inverter, no level shift. 3.3 V = off, 0 V = on.
Before configuration only U7 is powered (~70 mA ✓). SPEC P4 is met properly, not ignored.

Three things to verify:
- **PWREN# must be enabled in the EEPROM** (U8) — it is a configurable function, not a
  default. If the EEPROM image is wrong, the board never powers its rails and looks dead.
- A **DNP 0 Ω** from `PWREN_N` to GND (**R6**) is specified so a bare board can be brought up
  on the bench without a configured EEPROM: populating it pulls EN low = switch ON. Do not
  omit it — it is the escape hatch from the bootstrap problem above.
- **The current limit must bracket the load.** U9's over-load limit is 1.1 / 1.5 / 1.9 A
  against a 485 mA worst-case draw: no nuisance trip, and the 1 A recommended continuous
  rating is 2× the load. Any substitute must keep both ends of that bracket — a 500 mA-class
  part (TPS2041B, STMPS2141) is **not** acceptable.

VBUS bulk is held to **≤10 µF total** (P4) — **C1 + C2 = 4.7 + 4.7 = 9.4 µF** as of rev 2;
rev 1's 2 × 10 µF violated it. Downstream inrush is now bounded too: U9's 0.6 ms controlled
rise time into the ~20 µF behind it is ≈167 mA, where the bare FET had no slew control at all.

---

## R-11 · `VBIAS` drives 200–250 pF with no isolation — **L** (solved in rev 2)

<!-- revised: rev2 — new risk, found by the analog_power_ref coder. -->

`VBIAS` is the AFE dividers' return and the front end's AC ground, so both channels' 82 pF
`C_bot` legs plus routing stray — 200–250 pF — hang directly on U4A's output. A 10 MHz-GBW
RRIO op-amp driving that much capacitance directly loses phase margin and can ring, and it
rings on the one node the measurement uses as its reference. **Solved by R22 = 10 Ω** between
U4A's output (`VBIAS_DRV`) and `VBIAS`, with the feedback taken inside R22. Isolation zero
≈64 MHz; 10 Ω against the 50 kΩ `R_bot` is −74 dB of error in the AC-ground role; DC drop at
~2.4 µA is 24 nV. If U4 is ever substituted for a lower-GBW part, R22 stays; for a
higher-GBW part, R22 matters *more*, not less.

---

## R-10 · Firmware is out of scope but two things must remain possible — **L**

Not a hardware risk, a scope risk. The bitstream, USB descriptors, and host software are
outside this pipeline. The architecture deliberately keeps the *hardware* sufficient with
the *simplest possible* firmware:

- No DSP is required. The FPGA writes raw 20 MSPS samples; the host decimates. Every HARD
  requirement is met by a plain capture engine.
- The only genuinely asynchronous clock crossing is memory-domain → `FIFO_CLK` (60 MHz), and
  it needs a dual-clock async FIFO. Everything upstream of it is synchronous to X1.
- JTAG (J4) and the FPGA's internal config flash mean no programming hardware is designed
  in and none is needed beyond a standard cable.

**What would break if someone "optimises" later:** deriving `ADC_CLK` from an FPGA PLL to
save an oscillator. That violates F14/D10 and costs 1–2 ENOB. It is listed under
`## Do not redo` for a reason.

---

## Requirements this architecture knowingly deviates from

All of these are CLAUDE-tagged (my own upstream choices), not USER statements. Each is flagged
rather than silently violated, per the upstream handoff's instruction.

| Req | Original | Delivered | Why |
|---|---|---|---|
| **Q3** | parts ≤$70/board at qty 5 | **≈$85.5** | ADC + FPGA = $55 and nothing cheaper is in stock that meets the HARD requirements (`ic_selection.md` § 1, § 2) |
| **Q4** | every part ≥200 in stock | U5 = 154, U6 = 180 | Relaxed to the `find-part` rule (>100, warn <500). 5 prototypes need 5 of each; no 12-bit ≥10 MSPS ADC in the JLCPCB catalogue clears 200 except AD9237, which fails F11 |
| **F9** | −0.5 dB to 4.0 MHz **and** −3 dB ≤ 5 MHz | **≤0.5 dB to 4.0 MHz, −3 dB at 6.1 MHz** (0.40 dB / 5.6–6.4 MHz worst case) | The two original clauses together demand a 1.25:1 knee ⇒ **n ≈ 5** and an LC filter. The "−3 dB ≤ 5 MHz" clause was written assuming direct 10 MSPS sampling; at 20 MSPS the analog Nyquist is 10 MHz, so bounding the bandwidth at 5 MHz buys nothing and costs the passband. **The flatness clause — the one that is a real performance number — is now met with margin (−0.15 dB nominal) instead of missed by 4.1 dB.** rev 3 |
| **F10** | ≥25 dB above 7 MHz (≥3rd-order) | **≥25 dB above 16 MHz** analog (22.7 dB worst case), ≥13 dB at 10 MHz, genuinely 3rd-order; 5–10 MHz is **S1's** job | 16 MHz, not 15, is the exact frequency above which 20 MSPS aliases reach the 0–4 MHz band. 7 MHz analog is unreachable: it needs n ≈ 7 with F9 attached. **Conditional on R-12/S1** |
| **I4** | 1 MΩ **to GND** | 1 MΩ to a **1.100 V buffered bias** (rev 3: was 1.200 V) | No negative rail is permitted (P6), so the level shift must happen in the divider return. Consequence: the BNC sources **1.1 µA** DC into the DUT — negligible for bench work, but it is a real deviation |
| **P5** | rails incl. +1.8 V | **no 1.8 V rail** | Nothing needs it: the ADC is 3.0–3.6 V and the FPGA is assumed 1.2 V + 3.3 V only. ⚠ Contingent on the GW1NR-9C datasheet (`ic_selection.md` § 2) |

## Requirements comfortably exceeded

- **F3**: 20 MSPS/ch raw available, against 10 MSPS required.
- **F5**: 104.9 ms of both channels at 20 MSPS; 209 ms at the required 10 MSPS.
- **F11**: ≈11.4 ENOB from the ADC, ≈11.0 after front-end noise (est. 150 µVrms total input
  noise, 70.7 dB combined SNR), against ≥10.5 required.
- **I5**: survives ±30 V — at ±30 V the clamp does not conduct
  (node = **−0.45 V** at `VBIAS` = 1.100 V, still inside the OPA355's (V−) − 0.5 V abs max);
  the practical limit is the 475 kΩ resistors' voltage rating, ~±150 V.
- **P3**: ≈373 mA typical / ≈485 mA worst case at 5 V, against a 700 mA target. Note that
  485 mA sits right on the 500 mA USB-A line — **USB-C is what makes this safe**, which is
  exactly the reasoning in SPEC D2.
