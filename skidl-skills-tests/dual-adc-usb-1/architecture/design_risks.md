# Design Risks & Required Analysis — `dual_adc_usb`

- **Stage:** architecture
- **Date:** 2026-09-06
- Covers: SPEC §11 W1 (mandatory), SPEC §8.1/§8.2, power budget, FPGA fit, SRAM timing,
  EMI, power integrity, layout keep-outs, cross-clock-domain timing, sourcing risks.

---

# 1. ⭐ W1 — INPUT-REFERRED NOISE BUDGET AND EXPECTED ENOB

> **SPEC §11 W1. User-required deliverable from the approval gate.**
> Run against the real candidate ADC (**LTC2292**) and the real candidate amplifiers
> (**OPA1656**, **THS4521**).

## 1.0 Result first

| | |
|---|---|
| **Expected ENOB** (input 0–3 MHz, at the 10 MSPS decimated output) | **12.49 bits** |
| **DOMINANT TERM** | **The LTC2292's own SNR — 92.2 % of the total noise power** |
| Total input-referred noise at the ADC input | **100.3 µV RMS** |
| Corresponding SNR (vs 0.7071 V RMS full-scale sine) | **76.97 dB** |
| Attenuator Johnson noise share of total noise power | **0.19 %** |
| **Verdict vs the 12 ENOB target** | **Above 12. This is not a finding requiring a spec change.** |

**But there IS a finding, and it is the opposite of the one the SPEC expected — see §1.2.**

## 1.1 Signal-chain gain and reference levels

The chain runs at **gain = 1 end to end**, deliberately (see `ic_selection.md` §1):

| Point | Full-scale signal |
|---|---|
| BNC | ±10 V (20 V p-p) |
| After the 10:1 compensated attenuator (node X) | ±1 V (2 V p-p) |
| Buffer, Sallen-Key output | ±1 V |
| FDA differential output → LTC2292 | 2 V p-p differential = **full scale** |

- Full-scale sine RMS at the ADC: `2 / (2√2)` = **0.70711 V RMS**
- Ideal 12-bit LSB at 2 V p-p: `2/4096` = 488.3 µV; quantisation noise `q/√12` = **141.0 µV RMS**
- Anti-alias filter: 4th-order Butterworth, **fc = 4.3 MHz** (see §3). Equivalent noise bandwidth
  `ENBW = 1.026 × fc` = **4.412 MHz**; `√ENBW` = **2100**

## 1.2 🔴 CORRECTION TO SPEC R5 — the attenuator noise term

**The SPEC's R5 arithmetic is 18× pessimistic, and the error is in the model, not the multiplication.**

R5 (and the gate's independent verification) computes:
`38.6 nV/√Hz × √(4 MHz) ≈ 77 µV RMS`.
That is the noise of a **90 kΩ resistor with nothing across it**, integrated flat to 4 MHz. The
divider node is not that.

The SPEC mandates a compensated 10:1 attenuator preserving **1 MΩ ∥ 15–20 pF** (§2 item 3). Being
*compensated* means `R1·C1 = R2·C2`. With `R1 = 900 kΩ`, `R2 = 100 kΩ`, and a 20 pF input
specification:

- `C_in = C1·C2/(C1+C2) = 0.9·C1` ⇒ **C1 = 22.2 pF**, and compensation forces **C2 = 9·C1 = 200 pF**
- The Thévenin impedance at node X is then

```
        Z1 = R1/(1+sR1C1),  Z2 = R2/(1+sR2C2),  with R1C1 = R2C2 = tau
        Z_th = Z1 || Z2 = R_th / (1 + s·tau)      R_th = 90 kOhm, tau = 20 us
```

i.e. node X looks **exactly like 90 kΩ in parallel with C1+C2 = 222 pF**, with a noise corner at

`f_c = 1/(2π · 90 kΩ · 222 pF)` = **7.97 kHz**

The correct integral is the textbook kT/C result (Norton form: the resistors' current noise
`4kT/R_th` through `|Z_th|²`; the series-EMF form gives a wrong "flat forever" answer because the
caps are across the resistors, not across the sources):

```
  v_n,total = sqrt(kT / C) = sqrt(1.3806e-23 x 298 / 222e-12) = 4.31 uV RMS
```

Cross-check from the density: `38.50 nV/√Hz × √(π/2 × 7.97 kHz)` = 38.50 nV × 111.9 = **4.31 µV** ✔

**The attenuator's Johnson noise is 4.31 µV RMS, not 77 µV.** The same 20 pF requirement that R5
calls immovable is what band-limits the attenuator's own noise. Note the transfer function is
unaffected — a compensated divider is exactly 1/10 at all frequencies; only the *source impedance*
rolls off. This is why real 1 MΩ scope inputs are not thermal-noise-limited.

**Sanity checks performed:**
- Single R∥C reduces to `kT/C` ✔ (classic result)
- Open-circuit BNC case: only R2 ∥ C2 remains ⇒ `√(kT/200 pF)` = 4.54 µV — same order ✔
- 38.50 nV/√Hz for 90 kΩ at 298 K reproduces the SPEC's 38.6 nV/√Hz ✔ (that part was right)

## 1.3 Term-by-term input-referred noise budget

All terms referred to the **ADC input** (= node X, since gain is 1 throughout).
`√ENBW = 2100` unless a term has its own bandwidth.

| # | Term | Density | Bandwidth applied | RMS | % of total noise **power** |
|---|---|---|---|---|---|
| 1 | **Attenuator Johnson** (90 kΩ ∥ 222 pF) | 38.50 nV/√Hz below 7.97 kHz, then −20 dB/dec | kT/C, all frequencies | **4.31 µV** | 0.19 % |
| 2 | **OPA1656 buffer voltage noise** `e_n` | 2.9 nV/√Hz @10 kHz (datasheet) | 4.412 MHz | **6.09 µV** | 0.37 % |
| 3 | **OPA1656 buffer current noise** `i_n` into the source | 6 fA/√Hz × (90 kΩ ∥ 222 pF) = 0.54 nV/√Hz at LF; HF term `2πf·C_in·e_n × Z_src` = 0.11 nV/√Hz @4.3 MHz | both | **0.23 µV** | 0.0005 % |
| 4 | **OPA1656 Sallen-Key stage** `e_n`, noise-gain peaking (Q = 1.307 stage) | 2.9 nV/√Hz × √2 effective | 4.412 MHz | **8.60 µV** | 0.74 % |
| 5 | **Anti-alias filter resistors** — 2 × 249 Ω (SK) + 4 × 249 Ω (FDA Rg/Rf) | 4.96 nV/√Hz RSS | 4.412 MHz | **10.42 µV** | 1.08 % |
| 6 | **THS4521 FDA voltage noise**, noise gain = 1+Rf/Rg = **2** | 4.6 nV/√Hz × 2 = 9.2 nV/√Hz | 4.412 MHz | **19.32 µV** | 3.71 % |
| — | *Analog front end subtotal (RSS)* | | | **24.73 µV** | 6.08 % |
| 7 | **LTC2292 own SNR** = 71.3 dB (thermal + quantisation + internal aperture jitter) | — | 0–20 MHz Nyquist | 192.5 µV **→ 96.27 µV after decimation** | **92.16 %** |
| 8 | **External clock jitter**, ≤1 ps RMS XO at 3 MHz full-scale input | `2π·f_in·t_j·V_rms` | — | **13.33 µV** | 1.77 % |
| | **TOTAL (RSS)** | | | **100.29 µV** | 100 % |

### 1.3.1 Effect of 4:1 decimation on **each** term separately (SPEC §11 W1.1)

| Term | White over 0–20 MHz? | Decimation gain | Why |
|---|---|---|---|
| 1 Attenuator Johnson | **No** — band-limited to 7.97 kHz by its own 222 pF | **0 dB** | Entirely inside the 0–5 MHz decimated passband; nothing folds away |
| 2–6 All front-end amplifier and filter noise | **No** — band-limited to 4.3 MHz by the AA filter | **0 dB** | Same reason. The decimated Nyquist is 5 MHz; the analog noise occupies 0–4.3 MHz of it |
| 7a ADC quantisation noise | **Yes** | **−6.02 dB** | Spread uniformly over 0–20 MHz; the decimation filter keeps only 0–5 MHz ⇒ ¼ the power |
| 7b ADC internal thermal noise | **Yes** | **−6.02 dB** | Same |
| 8 Clock-jitter noise | Approximately, as a broadband skirt | **taken as 0 dB (conservative)** | Treated as unreduced. If it decimates like white noise the term drops to 6.7 µV and ENOB rises to 12.51 |

The 6.02 dB is realised in full because the decimation filter's passband (0–3 MHz flat, stopband from
7 MHz) sits well inside the 5 MHz decimated Nyquist. Realised gain, allowing for the FIR transition
band, is ≈ 5.7–6.0 dB; the table uses 6.02 dB and §1.5 bounds the other end.

### 1.3.2 Why the current-noise term is 0.0005 % and not fatal

This is the one place where the part choice is doing real work. Term 3 assumes a **CMOS/JFET input**.
Substituting a typical bipolar-input amplifier at **2 pA/√Hz**:

`2 pA/√Hz × 90 kΩ = 180 nV/√Hz` → **20.1 µV RMS** even after the 7.97 kHz roll-off, and far worse
without it. That alone would be 4× the attenuator's own noise. **Any op-amp substitution at the
buffer position must keep `i_n ≤ ~100 fA/√Hz`.** Put that in the RFQ, not just in this document.

## 1.4 Expected ENOB

```
  N_total = sqrt(96.27^2 + 24.73^2 + 13.33^2) = 100.29 uV RMS
  SNR     = 20*log10(0.70711 / 100.29e-6) = 76.97 dB
  ENOB    = (76.97 - 1.76) / 6.02 = 12.49 bits
```

**Expected ENOB = 12.49 bits.** Not a range. The dominant term is unambiguous: **the LTC2292's own
SNR contributes 92.2 % of the total noise power.** Everything else combined — the entire analog
front end, the attenuator, the clock — is 7.8 %.

**Practical consequence:** the input-referred noise floor is ≈ 100 µV at the ADC, i.e.
**≈ 1.0 mV RMS referred to the BNC** (×10 attenuator), or about 0.005 % of the ±10 V full scale.

## 1.5 Bounds and caveats (stated, not buried)

| Case | Total noise | SNR | ENOB |
|---|---|---|---|
| **Nominal** (as above) | 100.3 µV | 76.97 dB | **12.49** |
| **If SPEC R5 were right** (attenuator = 77.6 µV flat-band) | 126.7 µV | 74.94 dB | **12.16** |
| **Pessimistic floor: no decimation gain at all** | 194.5 µV | 71.21 dB | **11.54** |
| **Optimistic: jitter term also decimates** | 99.4 µV | 77.05 dB | **12.51** |

Note the second row: **even under the SPEC's own pessimistic model the design lands at 12.16 ENOB,
above 12.** The R5 correction does not change the go/no-go. What it changes is where engineering
attention belongs: **not** on fighting the 1 MΩ ∥ 20 pF requirement (which costs 0.19 % of the noise
power), but on the ADC, on the FDA's noise gain of 2, and on keeping switching residue off the
analog rails (§2.2), which is a **larger** threat than every thermal term combined.

**Caveats:**
- This is an **SNR** budget (noise only), not SINAD. Adding front-end distortion — OPA1656 THD+N and
  THS4521 HD2/HD3 at ~−90 dBc at 2 MHz, plus the LTC2292's 90 dB SFDR — costs roughly 0.05–0.1 bit.
  **SINAD-based ENOB ≈ 12.4.**
- The SPEC's target is 12 bits of *resolution*, which this meets. It does **not** promise 12 ENOB at
  every input frequency: at 3 MHz full scale with a 3 ps-class XO instead of a 1 ps part, jitter
  contributes 40 µV and ENOB drops to ≈ 12.4. Still above 12.
- Reference noise: ADR4525 broadband noise, divided by 0.4 and bypassed with 10 µF at the ADC, is
  filtered below ~1 kHz and contributes gain modulation at the few-ppm level. Not in the table
  because it is not measurable against 100 µV.

## 1.6 🔶 Dependency requiring revisit after sourcing (SPEC §11 W1.3)

**The single number this whole result rests on is the LTC2292's SNR = 71.3 dB.** It is taken from
ADI's published figure for the part ("71.3dB SNR … at the Nyquist frequency",
[analog.com/LTC2292](https://www.analog.com/en/products/ltc2292.html)); **the datasheet PDF itself
could not be retrieved in this environment** — ADI's PDF host timed out on five attempts across two
fetch mechanisms. Required actions:

1. `datasheet-librarian` must attach `229321fa.pdf` and re-read: SNR at 5 MHz and at Nyquist, SFDR,
   the SENSE-pin reference mapping, VDD range, and the S/H aperture-jitter figure.
2. **If the ADC is substituted, re-run this budget** — but it is a one-line recalculation, not a
   redesign: replace term 7 and re-RSS. Every other term is independent of the ADC.
   Rule of thumb from the numbers above: **ENOB ≈ (SNR_adc + 6.02 − 1.76)/6.02 − 0.02**, i.e. the
   front end costs only ~0.02 bit.
3. If the substitute ADC's SNR falls below **68.5 dB**, ENOB drops below 12.0 and that **is** a
   finding to bring back to the user.

---

# 2. EMI — the buck and the 40 MHz clock next to a 12-bit front end

## 2.1 Buck converter (TLV62569, 1.5 MHz) — SPEC R6, accepted deliberately

**The uncomfortable fact: 1.5 MHz is inside the 4.3 MHz analog passband.** Nothing downstream can
remove it — not the anti-alias filter, not the decimation filter. Suppression must happen before the
signal path, or not at all.

**Conducted path — quantified:**

| Stage | Attenuation | Residual |
|---|---|---|
| Buck input ripple on `VBUS_5V` after L1 + 10 µF | — | ~5 mV p-p @1.5 MHz |
| L2 ferrite + 10 µF into `VBUS_A5V` (2nd-order, f₀ ≈ 50 kHz) | 40·log10(1.5 MHz/50 kHz) ≈ **59 dB** | 5.6 µV |
| LP5907 PSRR at 1.5 MHz (~20 dB, extrapolated) | 20 dB | **0.56 µV on AVDD** |

Conducted coupling is **not** the risk. The risk is **near-field/radiated** coupling from the SW node
and L3 into node X (the 90 kΩ, 222 pF attenuator node). 1 pF of stray capacitance from a 3.3 V,
1.5 MHz switching edge into 222 pF injects ~15 mV of transient — three orders of magnitude above the
noise floor. **This is a layout problem with a layout-only solution.**

**Mandatory mitigations (carry to layout):**
- Buck in a board corner, **15 mm keep-out** around L3 and the SW node.
- **Shielded** inductor for L3 — not a wirewound open-core part.
- No analog trace, no analog ground return, and no AFE component inside the keep-out.
- `VBUS_5V` / `VBUS_A5V` remain **separate nets** all the way back to L1/L2 (enforced in the netlist,
  `net_plan.md` §1.1) so layout cannot accidentally merge them.
- The buck's input loop (C10 → U1 → GND) must be the smallest loop on the board.

**Documented fallback, NOT a re-litigation of constraint 7:** the measured power budget (§5) shows
1.09 W of headroom. An LDO at 197 mA / 3.3 V from 5 V would dissipate only **335 mW** — thermally
feasible in an SOT-223 — and total draw would rise to ~1.65 W, still inside 2.5 W. Recorded here only
so that *if* rev A measures unacceptable 1.5 MHz spurs, the rev B option is on the record with its
numbers already worked out. The buck is what gets built.

## 2.2 🔴 LM27762 charge pump at 2 MHz — the largest EMI threat in the design

This one is **worse than the buck** and it is not called out in the SPEC (SPEC §3.4 anticipates
"600 kHz–1 MHz"; the real part switches at **1.7 / 2.0 / 2.3 MHz**,
[TI SNVSAF7C](https://www.ti.com/lit/ds/symlink/lm27762.pdf)).

**Quantified, unmitigated:**

| Step | Value |
|---|---|
| LM27762 output ripple @2 MHz (datasheet Fig. 5-1) | 1–5 mV p-p; take 2 mV p-p = **0.71 mV RMS** |
| OPA1656 PSRR at 2 MHz (extrapolated from the ~100 dB DC figure) | ~25 dB |
| Residual at the amplifier output | **≈ 40 µV RMS** |

40 µV is **1.6× the entire analog front-end noise budget** and 40 % of the ADC's contribution — and
it is a discrete spur at 2 MHz, sitting squarely inside the 3 MHz passband, where an FFT will show it
immediately. **Unmitigated, this is the term that would actually degrade the instrument.**

**Mandatory mitigation — per amplifier, per rail:**

```
   VP4V0 --[ 10 ohm 1% ]--+--[ 10 uF X7R ]--GND
                          +--[ 100 nF ]-----GND --> amp V+   (same for VN4V0)
```

A **10 Ω + 10 µF RC** gives a 1.6 kHz pole ⇒ **62 dB at 2 MHz**, predictably. Residual ≈ 0.03 µV.

> **Correction to the skeleton BOM:** an RC is specified here in preference to the ferrite (L101/L201)
> originally listed. A "600 Ω @ 100 MHz" bead has only ~10–30 Ω of impedance at 2 MHz — the ideal-L
> model that predicts 64 dB is wrong for a lossy bead at this frequency. The RC's pole is
> deterministic. Cost of the RC: 10 Ω × ~8 mA = 80 mV of the 4 V rail, which is irrelevant for a
> ±1 V signal. **Use the RC.**

Also required: keep the LM27762's flying-cap loop (C1+/C1−) tight and away from the AFE; it is the
highest-di/dt loop in the analog section.

## 2.3 40 MHz sample clock next to the front end

The `encClk40` net is a 3.3 V CMOS square wave with sub-nanosecond edges running to a pin ~10 mm from
a ±1 V analog input. Its fundamental and harmonics (40/80/120 MHz) are **out of band**, but they are
also **exact multiples of the sample rate** — any coupling into the analog path aliases to **DC**,
appearing as a stable offset (which calibration removes) plus jitter-correlated noise (which it
does not).

Mitigations:
- **33 Ω series at the XO output** (R40) — slows edges, damps the single-load line.
- `encClk40` has **exactly one load** (the ADC ENC+ pin). The FPGA gets a separate 100 Ω tap (R41) so
  no stub hangs off the encode net.
- Trace ≤ 15 mm, on the top layer over an uninterrupted ground plane, no vias if possible, never
  routed under or parallel to the AFE.
- ENC− bypassed to GND at the ADC pin (single-ended LVCMOS encode).

## 2.4 Digital bus aggregate di/dt

24 ADC data lines at 40 MHz, plus 37 SRAM lines at 20 MHz, plus 13 FIFO lines at 60 MHz.

- **33 Ω damping on all 26 ADC output lines** (RN1–RN6 arrays). The LTC229x datasheet explicitly
  warns that the digital outputs must drive a minimal capacitive load to avoid interaction with the
  sensitive input circuitry — this is that mitigation.
- **ADC OVDD on a separate ferrite off `V3V3_D`**, never off `V3V0_AVDD`. This is structurally the
  most important single decision for ADC SNR and it is enforced in the netlist.
- Route the 24-line ADC bus as a group on the layer away from the analog side.

---

# 3. Anti-alias filter corner: **4.3 MHz, not 4.0 MHz** — and a gateware constraint the SPEC missed

## 3.1 Why 4.3 MHz

SPEC §1.1 wants **−0.5 dB flat to 3 MHz** *and* **−74 dB alias rejection**. These pull in opposite
directions:

| fc | Attenuation at 3 MHz (flatness budget) | Attenuation at 37 MHz (aliasing at 40 MSPS) |
|---|---|---|
| 4.0 MHz | **−0.414 dB** — eats 83 % of the flatness budget | −78.5 dB ✔ |
| **4.3 MHz** | **−0.237 dB** ✔ | **−74.8 dB** ✔ |
| 4.5 MHz | −0.171 dB ✔ | −73.2 dB ✘ (short of −74) |

**4.3 MHz is the point where both specs are met with margin.** The −3 dB point lands at 4.30 MHz,
still "≈4 MHz" per SPEC §1.1, and slightly more usable bandwidth than promised.

## 3.2 🔴 A plain low-order CIC does **not** meet the −74 dB alias spec

SPEC §1.1 notes that "the 40 MSPS oversampling is what buys the −74 dB". That is true **for the
analog filter's job** — it only has to reject at 37 MHz, where a 4th-order at 4.3 MHz gives −74.8 dB.
It does not address the **digital** decimator's job, and the naive answer fails:

Content in the band **7–13 MHz** folds into the 0–3 MHz passband when the rate drops to 10 MSPS.
At **7 MHz** — the worst point, because the analog filter is weakest there — the analog filter
supplies only **17.0 dB**. A single-stage 4th-order CIC with R=4 supplies **32.9 dB**.
**Total 49.9 dB — 24 dB short of the −74 dB requirement.**

Pushing the CIC to N=8 would reach it but costs **−9.96 dB of passband droop at 3 MHz**, which is
unrecoverable within the flatness budget. The structure has to change.

## 3.3 Assumed decimation structure (this is what the group-delay number is computed from)

**Two-stage: CIC(N=4, R=2, M=1) → 21-tap symmetric decimate-by-2 FIR with inverse-sinc folded in.**

| Fold band | folds into | Analog @4.3 MHz | CIC(4, R=2) | Pre-FIR total | FIR must supply |
|---|---|---|---|---|---|
| **7 MHz** ← worst case | 3 MHz | 17.0 dB | 5.5 dB | **22.5 dB** | **51.5 dB** |
| 13 MHz | 3 MHz | 38.4 dB | 22.5 dB | 60.9 dB | 13.1 dB |
| 17 MHz | 3 MHz | 47.8 dB | 50.5 dB | 98.3 dB | ✔ met |
| 23 MHz | 3 MHz | 58.3 dB | 50.5 dB | 108.8 dB | ✔ met |
| 27 MHz | 3 MHz | 63.9 dB | 22.5 dB | 86.4 dB | ✔ met |
| 33 MHz | 3 MHz | 70.8 dB | 5.5 dB | 76.3 dB | ✔ met |
| 37 MHz | 3 MHz | 74.8 dB | 1.0 dB | 75.8 dB | ✔ met |

A 21-tap symmetric FIR with passband edge 3 MHz and stopband edge 7 MHz at a 20 MHz input rate
(Kaiser estimate: 15 taps for 51.5 dB; 21 chosen for margin **and** to absorb the inverse-sinc
correction, which costs stopband) delivers ~60 dB. **Worst-case combined = 82.5 dB, 8.5 dB of
margin on the −74 dB spec.** ✔

Passband, at 3 MHz:

```
  analog 4th-order @4.3 MHz   -0.237 dB
  CIC(N=4, R=2)               -0.974 dB
  FIR inverse-sinc            +0.974 dB (+/- 0.05 dB ripple)
  ------------------------------------------
  NET                         -0.24 +/- 0.10 dB     (spec: -0.5 dB)   PASS
```

## 3.4 ✅ SPEC §8.2 — decimation-filter GROUP DELAY (the calibratable trigger offset)

Both stages are linear phase, so the group delay is **exact and constant, not frequency dependent**.

```
  CIC:  gd = N*(R*M - 1)/2 = 4*(2-1)/2 = 2 input samples @ 40 MHz   =  50.0 ns
  FIR:  gd = (L - 1)/2     = (21-1)/2  = 10 samples    @ 20 MHz     = 500.0 ns
  ------------------------------------------------------------------------
  TOTAL DECIMATION GROUP DELAY                                      = 550.0 ns
                                                    = 5.5 decimated samples @ 10 MSPS
```

**The calibratable trigger offset required by SPEC §8.2 is 550 ns.**

Host/gateware contract:
- The trigger decision is made on the **decimated** stream, so the trigger granularity is one
  decimated sample = **100 ns** (as SPEC §1.3 already accepts).
- The sample the trigger fires on corresponds to an analog event **550 ns earlier**. The host
  subtracts 5 whole samples and applies a 50 ns residual (or simply reports 550 ns of skew, which is
  below the 100 ns granularity anyway).
- The external trigger input adds up to one 40 MHz clock (**25 ns**) of synchroniser uncertainty on
  top — see §7.

**If the gateware author changes the filter structure, this number changes and must be recomputed.**
For reference, the alternative single-stage CIC(N=4, R=4, M=1) has gd = `4*(4-1)/2` = 6 input samples
= **150 ns**, plus `(L−1)/2 × 100 ns` for whatever compensating FIR follows it — but that structure
fails §3.2 and is not the plan.

## 3.5 ✅ SPEC §8.1 — CIC passband droop compensation, recorded as a gateware task

The CIC(N=4, R=2) droops **−0.974 dB at 3 MHz**. Recorded as a gateware task per SPEC §8.1, with two
refinements:

1. **Fold the inverse-sinc into the 21-tap decimating FIR's coefficients.** It costs nothing — same
   tap count, different numbers — and avoids a separate filter stage and its extra group delay.
2. **Fallback if it does not fit:** the droop correction is a fixed linear filter and **does not have
   to be in gateware at all**. Capture is a buffered burst, not a stream, so the host can apply it
   after the drain. Only the *alias-rejecting* decimation must be on-chip, because it sits ahead of
   the SRAM. This fallback also covers pre-emphasising the analog filter's −0.237 dB if the flatness
   spec is ever tightened.

---

# 4. FPGA fit — verification of the SPEC's ~80 I/O estimate

**SPEC §4.2 estimated ~80 I/O. The real count against the parts selected is 99 of 107.**

| | SPEC estimate | Actual |
|---|---|---|
| ADC data | 24 | 24 |
| ADC control / OF (no CLKOUT — D3) | — (omitted) | **+4** |
| SRAM address | 21 | 21 |
| SRAM data | 16 | 16 |
| SRAM control | 3 | 3 |
| USB FIFO | ~12 | **14** |
| Clocks | "clocks" | 2 (XO tap, which is also the ADC capture clock, + FT2232H CLKOUT) |
| SPI config + CRESET_B + CDONE | — (omitted) | **+6** |
| Probe comp / ext trig / mode strap / LEDs | — (omitted) | **+5** |
| Spare / debug | — | 4 |
| **Total** | **~80** | **98 of 107 (9 spare)** |

The SPEC's estimate omitted the config pins, the ADC's control/status pins, and the aux I/O.
**It still fits**, but the headroom is 7 %, not the ~25 % the estimate implied.

- **HX4K vs HX8K:** `iCE40HX8K-TQ144` **does not exist** — HX8K ships only in CB132/CT256/BG121, all
  BGA, which conflicts with constraint 13. The answer is that **HX4K-TQ144 is physically an HX8K
  die**; `nextpnr-ice40 --hx8k --package tq144:4k` unlocks all 7680 LUTs. The logic estimate
  (`ic_selection.md` §2.2) is **3100–3800 LUT4**, which is *at or over* the advertised 3520 of an
  HX4K and ~45 % of an HX8K. **The HX8K build flag is load-bearing, not an optimisation.**
  Risk: this relies on documented community practice rather than a Lattice guarantee. **Mitigation:
  synthesise a skeleton design with `--hx8k --package tq144:4k` and load it onto real silicon early
  in the gateware stage, before the PCB is committed.**
- **Bank/voltage arrangement:** all four I/O banks at VCCIO = 3.3 V; `VCC_SPI` = 3.3 V (matches
  W25Q32JV); `VPP_2V5` accepts 2.30–3.47 V so it ties to 3.3 V. **No mixed-voltage bank problem
  exists.** The only surviving pin constraint is that `xoClkFpga` and `ftClk60` (only two GBINs now — `adcClkOut` was deleted by D3) must
  each land on a **GBIN** pin; TQ144 provides eight.
- **iCE40 is not 5 V tolerant.** Every interface in this design is 3.3 V. Confirmed.

---

# 5. Power budget against the 2.5 W USB limit — real datasheet numbers

Replaces SPEC §3.2's estimates.

## 5.1 `V3V3_D` rail (buck output)

| Load | Current | Source of number |
|---|---|---|
| FT2232HL core via internal LDO (VREGIN) | **70 mA** | FTDI DS_FT2232H §5.2, `Icc1` = 70 mA typ @1.8 V |
| FT2232HL VCCIO + VPHY + VPLL + I/O | 15 mA | estimate |
| iCE40 VCCIO ×4 banks, ~75 signals switching | 20 mA | CV²f estimate |
| iCE40 1.2 V core through TLV75512 | 40 mA | estimate, 40 MHz, ~45 % utilisation |
| IS61WV204816 @ 20 M cycles/s | 30 mA | scaled from the family's ~90 mA at 100 MHz |
| LTC2292 OVDD (24 outputs @40 MHz, 33 Ω into ~5 pF) | 13 mA | from the 235 mW total, minus AVDD |
| W25Q32JV idle, LEDs, pull-ups, straps | 9 mA | |
| **Total `V3V3_D`** | **197 mA** | **= 650 mW** |

## 5.2 Full 5 V budget

| Branch | Regulator | Load | Draw from 5 V | Power |
|---|---|---|---|---|
| Digital 3.3 V | TLV62569 buck @ 88 % | 197 mA @ 3.3 V | 148 mA | **739 mW** |
| ADC AVDD 3.0 V | LP5907 LDO | 64 mA @ 3.0 V | 64 mA | **320 mW** |
| ±4.00 V analog | LM27762 | +4 V: 18.5 mA, −4 V: 16.6 mA | 40 mA | **199 mW** |
| Voltage reference | direct | ADR4525 0.95 mA | 1 mA | **5 mW** |
| 40 MHz XO | LP5907 3.3 V LDO | ~25 mA | 25 mA | **125 mW** |
| TVS/soft-start/CC/leakage | — | — | 4 mA | **20 mW** |
| **TOTAL** | | | **282 mA** | **1.41 W** |

| | |
|---|---|
| **Budget (SPEC §3)** | 500 mA / **2.50 W** |
| **Typical draw** | 282 mA / **1.41 W** — **56 % of budget** |
| **Margin** | 218 mA / **1.09 W** |
| Worst case (max-spec parts, 50 °C, ×1.35) | 380 mA / 1.90 W — **still inside budget** ✔ |

**No flag raised: the real total is inside budget with 44 % headroom**, and it agrees with the SPEC's
1.2–1.6 W estimate. Two observations worth carrying forward:

- **The 40 MHz XO is 125 mW — 9 % of the whole board**, bigger than the reference, the FDAs and the
  buffers combined. Low-jitter oscillators are not free. Not a problem here, but it is the first
  place to look if the budget ever gets tight.
- **LP5907 thermal:** 64 mA × (5.0 − 3.0) V = **128 mW in a SOT-23-5** (θ_JA ≈ 250 °C/W) ⇒ ~32 °C
  rise ⇒ ~82 °C junction at 50 °C ambient. Legal but warm. **Recommend a 15 Ω series pre-drop
  resistor** ahead of U3: it moves ~61 mW into the resistor, drops the LDO to ~1.0 V of headroom
  (still above dropout), and the extra RC pole *improves* PSRR. Same treatment is not needed on the
  XO LDO (25 mA × 1.7 V = 43 mW).

---

# 6. SRAM timing verification

**Requirement (derived, not assumed):**
2 ch × 10 MSPS × one unpacked 16-bit word each = **20 M writes/s = 50 ns per word**.

| | |
|---|---|
| FPGA SRAM state machine clock | 40 MHz (25 ns/state) |
| States per word | 2 (address+data setup, then WE# pulse) = **50 ns/word** ✔ exactly meets the rate |
| Chosen device | IS61WV204816BLL-**10** ⇒ t_AA = t_RC = t_WC = **10 ns** |
| **Margin vs the device** | Device supports 100 M cycles/s; design uses 20 M ⇒ **5× margin** |
| Single-state access (25 ns/word) if ever needed | 40 M words/s ⇒ **2× headroom** on the requirement |
| **Minimum acceptable device speed** | **≤ 25 ns cycle** (1 state) or ≤ 50 ns (2 states, no margin) |
| Concurrent drain (future streaming mode): 20 M writes + 20 M reads | 25 ns/access ⇒ still inside a 10 ns part ✔ |

**USB drain reads do not contend during capture** — the buffered-burst model (SPEC §1.2) means
capture completes, *then* the drain runs. This is stated explicitly so the gateware author does not
build arbitration that isn't needed, and so the SRAM ownership handshake in §7 is understood as a
mode change, not a per-cycle arbiter.

**🔴 The trap:** `AS6C3216-55TIN` is in stock at Digi-Key, costs ~$8 instead of ~$33, is the same
2 M × 16 organisation, the same TSOP-I-48 package and the same 3.3 V — and its **55 ns** cycle time
caps it at **18.2 M writes/s against the 20 M required. It fails by 9 %.** It will look like an
obvious cost-down to anyone reading the BOM without this section. See `ic_selection.md` §3.

---

# 7. Cross-clock-domain timing

## 7.1 Domains

| # | Domain | Frequency | Source | Contents |
|---|---|---|---|---|
| 1 | Capture | 40 MHz | **`xoClkFpga`, FALLING edge** (D3 2026-09-07 — there is no ADC CLKOUT) | ADC input registers, CIC, FIR, trigger engine, SRAM writes |
| 2 | Drain | 60 MHz | `ftClk60` (FT2232H ACBUS5) | Sync-245 FIFO handshake, SRAM reads |
| 3 | FT2232H internal | 12 MHz crystal | Y1 | Not exposed to the FPGA. **Its own crystal, not shared** (SPEC §4.3) ✔ |
| — | — | — | — | Domains 1 and the housekeeping clock are now the **same** net and the same edge; there is no 40→40 MHz crossing to close. |

## 7.2 ADC data capture (domain 1) — REWRITTEN 2026-09-07 (D3)

> **The previous version of this section was built on a pin that does not exist.** It said "The
> LTC2292 provides CLKOUT, a data-ready clock that travels with the data" and instructed
> "**Do not** re-derive a capture clock from `encClk40`". Both statements are void. The LTC2292
> has CLKA (pin 8) and CLKB (pin 9), clock *inputs* only — verified against all 28 pages of the
> datasheet PDF and against the 65-pin KiCad symbol.

Capture the 24-bit data bus plus OFA/OFB into iCE40 **PIO input registers clocked by the
`xoClkFpga` global buffer on its FALLING edge**. `xoClkFpga` is the R41 tap off the same 40 MHz
XO that drives CLKA/CLKB, so it is not "re-derived" from anything — it is the same clock, one
series resistor away. SPEC Q7 is intact: the FPGA consumes the clock and never synthesises it,
and no PLL is involved on either the encode or the capture side.

**Why falling and not rising.** t_D (CLK→DATA) = 1.4 / 2.7 / 5.4 ns, so sample N is valid at the
ADC pins over [5.4, 26.4] ns of a 25 ns period. The iCE40HX4K PIO input register needs
t_SU = −0.43 ns and **t_H = 2.38 ns** (global buffer, no PLL).

- **Rising edge at t = 25 ns: raw hold is 1.4 ns — less than the FPGA's own 2.38 ns t_H.
  Net margin −1.77 ns. It cannot work.** This is the trap the imaginary CLKOUT was hiding.
- **Falling edge at t = 12.5 ns: 7.1 ns setup, 13.9 ns hold; +6.74 / +10.73 ns net after t_SU,
  t_H, 290 ps bank skew and 0.5 ns trace mismatch. Worst case over a 45–55 % XO duty cycle is
  +5.49 / +9.48 ns.** Comfortable, no PLL, no phase shifting.

Full arithmetic and the source lines for every number: `net_plan.md` §1.4.1.

**Knock-on requirement:** with the duty cycle stabiliser OFF the LTC2292 demands t_L, t_H ≥
11.8 ns each, i.e. a 47.2–52.8 % duty cycle, which a generic XO does not guarantee. `MODE` is
therefore biased to 1/3 V_DD (stabiliser ON, 40–60 % accepted; offset-binary output format).

**Residual risk:** the capture margin now depends on the XO's duty cycle, which is a specified
parameter on most 3225 parts but is **[UNVERIFIED] for the populated YXC OT322540MJBA4SL** — the
same datasheet gap as D2's jitter. Measure duty cycle at bring-up on the same scope trace as the
jitter measurement. The design tolerates 40–60 % (limited by the ADC's stabiliser range, not by
the capture margin, which survives to roughly 25–75 %).

## 7.3 The 40 ↔ 60 MHz crossing: SRAM ownership, not per-cycle arbitration

`sramData` is a genuine bidirectional bus shared between two clock domains. The design rule:

> **The SRAM has exactly one owner at a time, and ownership changes only at a burst boundary.**
> `ARMED`/`CAPTURING` → domain 1 owns it. `DRAINING` → domain 2 owns it. There is no overlap, ever.

Ownership transfer uses a request/acknowledge pair, each side synchronised with a **2-flip-flop
synchroniser**, plus a quiescent gap of ≥ 4 clocks of the *slower* domain before the new owner drives
the bus. This is exactly the "capture-to-USB domain crossing is handled through the SRAM burst
boundary" statement in SPEC §4.3, made concrete.

## 7.4 Other crossings

| Crossing | Mechanism | Risk |
|---|---|---|
| Control/status registers written from the MPSSE/drain side, read in domain 1 | Write only while `IDLE`; or toggle-handshake per register | Low, if the "write only while idle" discipline is enforced in the host driver as well as the gateware |
| Capture status/sample-count read from domain 2 | Gray-coded counter + 2-FF synchroniser | Low |
| **`extTrig` input — fully asynchronous** | 2-FF synchroniser + edge detector in domain 1 | **Adds up to 25 ns of uncertainty** to the external trigger, on top of the 100 ns decimated granularity and the 550 ns filter offset. Document in the host API |
| `extTrig` as an **output** | Registered in domain 1, 100 Ω series | Chained boards see 25 ns of skew per hop |
| `fpgaCresetBar` / `fpgaCdone` | Asynchronous by design (configuration) | None |

## 7.5 iCE40-specific timing caution

`nextpnr-ice40`'s timing-constraint support is **thinner than a vendor toolchain's** — there is no
rich equivalent of `set_false_path`/`set_max_delay` across arbitrary clock groups. Consequence:

> **Every domain crossing in this design must be *structurally* safe (synchronisers, gray codes,
> ownership handshakes), not merely *constraint*-safe.** Do not rely on the tool to catch a missing
> synchroniser. Declare both clocks in the PCF/SDC and treat anything crossing between them as
> asynchronous by default.

60 MHz on an iCE40HX is comfortable (the family reaches well past 100 MHz for simple logic), so
neither domain is near an f_max limit. The 40 MHz FIR is the only arithmetic-heavy path; pipeline it.

---

# 8. Power integrity

| Rail | Requirement | Implementation |
|---|---|---|
| `V1V2_CORE` (iCE40 core) | Low impedance to ~100 MHz | 100 nF at **every** VCC pin + 10 µF bulk; `VCCPLL` fed through a 10 Ω + 100 nF + 10 µF RC **even though the PLL is unused** — the pin must still be powered and quiet |
| `V3V3_D` (VCCIO ×4 banks) | 4 banks × several pins | 100 nF per pin, 10 µF per bank region, 22 µF bulk at the buck |
| `V3V0_AVDD` (ADC analog) | The rail the 12-bit claim depends on | Dedicated LP5907 off `VBUS_A5V` **through ferrite L4**; 10 µF + 100 nF at every VDD pin. **Never shared with digital 3.3 V** (SPEC §3.1) |
| ADC `OVDD` | Isolate output-driver di/dt | From `V3V3_D` through **ferrite L8** + 10 µF + 100 nF, plus 33 Ω on all 26 outputs |
| `VP4V0` / `VN4V0` | 2 MHz charge-pump residue | **10 Ω + 10 µF + 100 nF RC per amplifier per rail** (§2.2) — mandatory |
| `VBUS_5V` bulk | USB inrush compliance | **Held to 10 µF** + DMP2160U soft-start (~5 ms RC ramp). Always on after ramp — **not** a post-enumeration load switch (constraint 7) ✔ |
| LTC2292 exposed pad | Thermal + AC ground | Must be soldered to the analog ground pour with a via array |

**Enumeration behaviour (SPEC §3.3):** declare 500 mA in the descriptor, power up immediately with
inrush limiting, **no post-enumeration load switch**. The board draws ~282 mA typical, well under the
500 mA declared. The technical non-compliance during the enumeration window is accepted per SPEC §3.3.

---

# 9. Layout keep-outs and constraints (carry to the user's KiCad work)

| # | Constraint | Why |
|---|---|---|
| L1 | **15 mm keep-out** around the buck (U1, L3, SW node). No analog trace, no analog return, no AFE component. | §2.1 — the principal deliberate risk on the board |
| L2 | **Uninterrupted ground pour under the entire AFE.** No splits, no slots, no via fences forcing return-current detours. | SPEC §5; a split under a 90 kΩ node is fatal |
| L3 | **Node X (`attOutA` / `attOutB`) is the most sensitive net on the board.** ≤ 8 mm, guard-ringed to GND, no digital net within 5 mm, no plane above/below other than GND. | 1 pF of stray to a switching net injects mV into 222 pF |
| L4 | `encClk40` ≤ 15 mm, one load, over solid ground, no stubs, no vias if avoidable | §2.3 |
| L5 | The XO (U9) within ~10 mm of the ADC ENC pin | SPEC §2.2 "shortest possible trace" |
| L6 | BNCs vertical, on the edge opposite USB-C and the buck | SPEC §5 |
| L7 | BNC shells bonded to the analog ground pour at one defined point each | avoids shield-current loops through the AFE |
| L8 | 24-line ADC bus routed as a group, on the layer away from the analog side | §2.4 |
| L9 | USB D+/D− 90 Ω differential, short, no stubs, referenced to solid ground throughout | USB 2.0 HS |
| L10 | LM27762 flying-cap loop (C1+/C1−) minimal area, away from the AFE | highest di/dt loop in the analog section |
| L11 | 4-layer stack: **signal / solid GND / power / signal**; the GND layer is never cut under the analog section | SPEC §5 |
| L12 | All-SMD top side for JLC assembly; TH parts (2 × BNC, trigger header, probe-comp terminal, mode strap) hand-soldered | SPEC §5 |

---

# 10. Risk register (SPEC §9 re-graded against the architecture)

| # | Risk | SPEC grade | **Re-graded** | Basis |
|---|---|---|---|---|
| R1 | 2 M × 16 async SRAM availability | High | **High — CONFIRMED, already biting** | LCSC out of stock on both IS61WV204816 variants. Digi-Key/Mouser have it at ~$33. The in-stock cheap alternative (**AS6C3216-55**) **fails timing** (§6). Also: **no KiCad symbol exists** — one must be generated |
| R2 | iCE40HX4K-TQ144 and FT2232H stock/tier | Medium | **Low** | HX4K-TQ144: DigiKey "ships today", TrustedParts "in stock, low lifecycle risk". FT2232HL is a long-lived commodity. Both have KiCad symbols |
| R3 | 40 MHz XO phase jitter | Medium | **OPEN — unverified, measure at bring-up** | See §R3-UPDATE below. **The part shipped on rev A has NO published jitter spec at all.** |

### R3-UPDATE — post-sourcing, 2026-09-06 (supersedes the row above)

**Status changed from "Low" to OPEN.** Sourcing could not find *any* 40 MHz oscillator with a
published phase-jitter figure in stock at qty 5. All 94 parts in the JLCPCB library specify frequency
tolerance but **no jitter**; ASFLMB-40.000MHZ-LC-T (the architecture's part), ASEM1-40.000MHZ-LC-T and
DSC1001CI2-040.0000 are all stock 0 or MOQ 1000. SiT8008 / ECS-2520MV were not verified (Digi-Key
quota error) — unverified, not confirmed unavailable.

**User decision (D2):** populate **YXC OT322540MJBA4SL**, LCSC C2831396, $0.55, 3225 4-pad, ±10 ppm,
and **measure jitter at bring-up**.

| Item | Value |
|---|---|
| Published jitter spec | **NONE** |
| Expected (inference, not fact) | 1–3 ps RMS — 40 MHz is fundamental-mode, no PLL multiplication |
| **Practical threshold** | **~5 ps RMS** |
| Headline aperture budget (SPEC §2.2) | 10.6 ps — **not** the operative number |
| **Consequence at 10 ps** | **~0.7 ENOB lost**; jitter-limited SNR 74.5 dB vs the 76.96 dB total budget |

Jitter-limited SNR at 3 MHz full scale = `−20·log₁₀(2π·f·t_j)`:
1 ps → 94.5 dB · 3 ps → 84.9 dB · 5 ps → 80.5 dB · **10 ps → 74.5 dB**.

**Note the earlier "1.8 % of noise power" figure assumed a ≤1 ps part.** That assumption no longer
holds — it is now unverified. At 5 ps jitter is ~4 % of noise power; at 10 ps it is co-dominant.

> **BRING-UP ACTION (do not close R3 until done):** measure the XO's integrated RMS phase jitter.
> If > 5 ps, swap to a jitter-specified 3225 part — the footprint is universal, so this is a drop-in
> with no board change. Cross-referenced in `sourcing/sourced_bom.md` §0.1.
| R4 | Dual 12-bit ≥40 MSPS ADC within the power budget | Medium | **Low** | LTC2292 = 235 mW against a 350 mW allowance, parallel CMOS, existing KiCad symbol (**the "CLKOUT pin" in the original wording does not exist — D3; it was not load-bearing for this risk**) |
| R5 | Front-end thermal noise cancels the oversampling gain | Medium | **CLOSED — premise incorrect** | Attenuator noise is **4.31 µV**, not 77 µV (§1.2). It is 0.19 % of the noise power. ENOB = 12.49 |
| R6 | Buck switcher on a 12-bit board | Medium | **Medium — unchanged, accepted** | Conducted path is quantified and benign (§2.1); the radiated/near-field path is a layout problem with layout-only mitigations |
| **R7 (NEW)** | **LM27762 switching residue at 2 MHz lands in the analog passband** | — | **Medium–High if unmitigated** | 40 µV RMS spur without the per-amp RC — larger than the entire front-end noise budget. Mitigation specified and mandatory (§2.2). SPEC §3.4 anticipated 600 kHz–1 MHz; the real part is **2 MHz** |
| **R8 (NEW)** | **A low-order CIC decimator misses the −74 dB alias spec by ~24 dB** | — | **Medium (gateware)** | §3.2. Requires the two-stage CIC+FIR structure, not a plain CIC. Constrains gateware LUT budget |
| **R9 (NEW)** | **HX4K→HX8K bitstream trick is community practice, not a Lattice guarantee** | — | **Medium** | Logic estimate is 3100–3800 LUT4 vs 3520 advertised. Mitigation: prove `--hx8k --package tq144:4k` on real silicon **early**, before the PCB is committed |
| **R10 (NEW)** | **Config-bus contention between FT2232H MPSSE, the FPGA, and the flash** | — | **Medium** | Both config paths are populated (constraint 10). 100 Ω series resistors on all four shared lines are mandatory, and the **host contract** must be: assert `CRESET_B` before touching the SPI bus, and tri-state BDBUS0–3 after `CDONE` rises. This is a software contract, not just a resistor |
| **R11 (NEW)** | **`pcbparts` MCP not connected — no JLCPCB tier data anywhere in this architecture** | — | **Process risk** | Install `claude mcp add --transport http pcbparts https://pcbparts.dev/mcp`; the part-sourcer must fill in every tier field |
| **R12 (NEW)** | **LTC2292 is a QFN-64 with an exposed pad** | — | **Low–Medium** | SPEC §6.1 permits hand placement for the four critical ICs, but a QFN exposed pad is not realistically hand-solderable. Prefer JLC assembly for U7 even at Extended tier; otherwise plan hot-air rework |
| **R13 (NEW)** | **±5 V rails are not achievable from a 5 V USB bus with an LM27762** | — | **Decision needed, low technical impact** | Set to **±4.00 V**. Arithmetic and the retained benefits are in `ic_selection.md` §4.4. Flagged as a deviation from SPEC §3.1's literal wording |


---

## ADC SNR — VERIFIED, and the ENOB claim strengthened (2026-09-07)

The architecture's open dependency on the LTC2292 SNR figure is **CLOSED**. The number is now read
from the datasheet PDF, not ADI's product page.

Source: `datasheets/LTC2292_LTC2293_LTC2291_229321fa.pdf`, Dynamic Accuracy table p.4, LTC2292
column, A_IN = −1 dBFS. SNR: **71.4 dB typ @5 MHz**; **69.6 dB MIN over full temperature @20 MHz**;
71.3 dB typ @20 MHz; 71.1 dB @70 MHz; 70.7 dB @140 MHz. SFDR 90 dB @5 MHz.

**Correction:** the design's ≤3 MHz band maps to the **5 MHz** spec (71.4 dB), **not** the 71.3 dB
Nyquist figure the architecture used.

| Case | ADC term | Total noise | SNR | **ENOB** |
|---|---|---|---|---|
| 71.4 dB typ | 95.2 µV | 99.2 µV | 77.06 dB | **12.51** |
| 69.6 dB guaranteed min | 117.1 µV | 120.4 µV | 75.38 dB | **12.23** |

**The ≥12 ENOB claim now holds at GUARANTEED MINIMUM over full temperature, not merely typical.**
That is a stronger statement than the architecture was able to make, and it closes risk **F3**.

Note the LTC2292 still dominates the budget, so the XO jitter item (**R3-UPDATE**, unverified,
measured at bring-up) remains the largest *unquantified* term in the design.

### THS4521 supply-rail safety check — PASSES

The THS4521 absolute-maximum supply is **5.5 V (V_DD−V_SS)**. The analog rails are ±4.00 V = **8.0 V
differential**, which would exceed that maximum **if the FDA were run dual-supply**. It is not:
`net_plan.md` §3.5 connects **U102.VS+ ← VP4V0** and **U102.VS− ← GND**, i.e. single-supply 4.0 V
total — inside the 5.5 V limit. Verified, no change required.

Input common-mode range **[VERIFIED-PDF]**: CM low = −0.2 V min / −0.1 V typ referred to V−, so the
GND-referenced FDA input is valid. The architecture's "negative-rail input" claim is confirmed.
Only the OPA1656 (max ±18 V) sits on the true ±4 V rails.
