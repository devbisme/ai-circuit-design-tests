# SPEC — dual_adc_usb

**Source:** `dual-adc-prompt.txt`, elaborated autonomously (user directed: "list all the
options and then select the one you recommend… do not pause the design process").

Every requirement below is tagged with its provenance:
- `[USER]` — stated directly in the prompt.
- `[DERIVED]` — forced arithmetically or electrically by a `[USER]` requirement.
- `[ASSUMED]` — a design decision made by the assistant in place of a user answer. Each of
  these is listed with its alternatives in `## Decision log`.

---

## 1. Functional

| # | Requirement | Prov. |
|---|---|---|
| F1 | Two analog input channels, sampled **simultaneously** (not multiplexed). | `[USER]` 2 ch; `[ASSUMED]` simultaneity |
| F2 | Full-scale input range **−10 V to +10 V** (20 Vpp) on each channel. | `[USER]` |
| F3 | Sample rate **10 MSPS per channel**, continuous for the capture window. | `[USER]` |
| F4 | Resolution **12 bits** per sample. | `[USER]` |
| F5 | Capture depth ≥ **0.1 s at 10 MSPS on both channels simultaneously** = 1,000,000 samples/ch = 2,000,000 samples total. | `[USER]` |
| F6 | On-board sample buffer ≥ **4,000,000 bytes** (2 M samples × 2 B, 12-bit right-aligned in a 16-bit word). | `[DERIVED]` from F5 |
| F7 | Operating mode is **burst capture then read out** — acquire to on-board memory at full rate, then stream to host. Continuous real-time streaming at 40 MB/s is *not* required. | `[DERIVED]` — see Decision D6 |
| F8 | Analog front end: DC-coupled, −3 dB bandwidth ≥ **4 MHz**, with anti-alias filtering ≥ 40 dB attenuation at ≥ 10 MHz. | `[ASSUMED]` D4 |
| F9 | DC gain accuracy ≤ ±1 % FS, offset ≤ ±0.5 % FS, both channels, uncalibrated. | `[ASSUMED]` |
| F10 | SNR ≥ 60 dB (≈ 10 ENOB) at 1 MHz input. 12-bit *resolution* is required; 12 *noise-free* bits is not. | `[ASSUMED]` D5 |
| F11 | Capture start is **host-commanded (software trigger)**. No analog/level trigger, no external trigger input. | `[ASSUMED]` D9 |
| F12 | Channel-to-channel skew ≤ 5 ns. | `[DERIVED]` from F1 |

## 2. Power

| # | Requirement | Prov. |
|---|---|---|
| P1 | **Bus-powered only.** No barrel jack, no battery. | `[USER]` ("provides power") |
| P2 | Total input current ≤ **1.5 A @ 5 V (7.5 W)** hard ceiling; design target ≤ **1.0 A (5 W)**. | `[ASSUMED]` D2 |
| P3 | Board must advertise its current need correctly on the USB connector and must not exceed **150 mA** before enumeration/negotiation completes. | `[DERIVED]` USB spec |
| P4 | Analog rails required by the front end (bipolar supply for ±10 V handling) are generated **on board** from the 5 V bus. | `[DERIVED]` from F2 + P1 |
| P5 | No sleep or low-power mode. The board is an actively-used bench instrument. | `[ASSUMED]` |
| P6 | Analog and digital supplies separated (separate regulators/filtering) to protect F10. | `[ASSUMED]` |

## 3. Interface

| # | Requirement | Prov. |
|---|---|---|
| I1 | Analog inputs terminate in connectors that **mate with standard oscilloscope probes/leads**: **BNC female, PCB-mount**, one per channel. | `[USER]` intent; `[ASSUMED]` BNC choice — D1 |
| I2 | Input impedance **1 MΩ ∥ ~20 pF**, the standard scope front-end impedance, so 1× and 10× passive probes work. | `[ASSUMED]` D3 |
| I3 | Input overvoltage survival ≥ **±50 V** continuous without damage (clamped, not necessarily accurate). | `[ASSUMED]` |
| I4 | Host interface: **USB 2.0 High-Speed (480 Mb/s)**, bulk transfer, sustained read-out ≥ 20 MB/s. | `[USER]` USB 2.0; `[DERIVED]` HS |
| I5 | Connector: **USB Type-C receptacle (USB 2.0 signalling only)**, with CC1/CC2 5.1 kΩ pulldowns so a Type-C source offers ≥ 1.5 A. | `[USER]` conditional ("if insufficient power… use a USB C"); condition evaluated true — D2 |
| I6 | No other host-facing interfaces. Debug/programming headers for the on-board logic device are permitted. | `[ASSUMED]` |

## 4. Physical

| # | Requirement | Prov. |
|---|---|---|
| Y1 | PCB ≤ **100 × 80 mm**, rectangular. | `[ASSUMED]` |
| Y2 | **4-layer** stack-up (signal / GND / PWR / signal) — required for 10 MSPS mixed-signal integrity and for USB HS impedance control. | `[ASSUMED]` D8 |
| Y3 | **SMD throughout**, except the BNC jacks and any header, which may be through-hole. | `[ASSUMED]` |
| Y4 | Operating temperature **0 °C to +70 °C** (commercial). | `[ASSUMED]` |
| Y5 | No regulatory certification required (bench/lab prototype). USB-IF electrical compliance is a design goal, not a certified requirement. | `[ASSUMED]` |
| Y6 | Unenclosed board. No mounting/enclosure constraints beyond Y1. | `[ASSUMED]` |

## 5. Production

| # | Requirement | Prov. |
|---|---|---|
| R1 | Quantity: **5 prototype boards**. | `[ASSUMED]` |
| R2 | Assembly: **JLCPCB**; prefer Basic/Preferred-tier parts; every part must be in stock at sourcing time. | `[ASSUMED]` D7 |
| R3 | BOM cost target ≤ **$90/board** at qty 5. Not a hard limit — flag any single part over $25. | `[ASSUMED]` |
| R4 | No second-source requirement, but single-source parts must be flagged. | `[ASSUMED]` |

---

## Decision log

Each entry: the options considered, and the one selected.

**D1 — Scope-lead connector.**
- *BNC female PCB jack* — what every scope probe and BNC lead terminates in; standard bench interface.
- *SMA* — better >1 GHz, but no standard scope probe mates with it.
- *Banana / binding post* — DMM leads, not scope leads; poor above ~100 kHz.
- **Selected: BNC female, PCB-mount.** The prompt says "mate with standard oscilloscope leads"; that is BNC by definition.

**D2 — USB connector and power budget.**
- *USB 2.0 Type-B / Type-A*: 5 V @ 500 mA = **2.5 W** ceiling.
- *USB Type-C, 5.1 kΩ CC pulldowns*: 5 V @ 1.5 A or 3 A depending on source = **7.5–15 W**.
- *USB-C with a PD controller*: more than needed, adds cost and firmware.
- Load estimate: 2× high-speed ADC (~0.15–0.4 W), FPGA/logic + memory (~0.5–1.5 W), USB HS PHY/bridge (~0.15 W), analog front end on bipolar rails (~0.5 W), plus the efficiency loss of generating a negative rail. A 2.5 W ceiling leaves no margin and would likely be violated.
- **Selected: USB Type-C receptacle, USB 2.0 signalling, 5.1 kΩ CC pulldowns, no PD.** This is exactly the prompt's stated fallback, and the condition triggering it is met.

**D3 — Input impedance.**
- *1 MΩ ∥ 20 pF* — matches every scope front end; 10× probes are compensated for it.
- *50 Ω* — needed only for >100 MHz coax work; a 10× probe into 50 Ω reads wrong.
- *Switchable* — extra relay/FET per channel, cost and leakage for no stated need.
- **Selected: 1 MΩ ∥ ~20 pF, fixed.**

**D4 — Analog bandwidth / anti-alias filter.**
- *Nyquist-exact (5 MHz brick wall)* — needs a 7th-order-plus filter; large, expensive, group-delay ripple.
- *−3 dB at ~4 MHz, ≥40 dB at 10 MHz* (3rd–4th order) — practical, alias energy pushed below ~1 LSB for typical bench signals.
- *No filter* — any out-of-band energy folds in; unacceptable at 12 bits.
- **Selected: −3 dB ≥ 4 MHz, ≥40 dB at 10 MHz.** Documented as the anti-alias limit; the user gets 12-bit samples, not a guarantee against aliasing a deliberately injected 9 MHz tone.

**D5 — Noise target.**
- *ENOB ≈ 12 (SNR ≥ 74 dB)* — demands a very low-noise front end, a premium ADC, and careful layout; drives cost hard.
- *ENOB ≈ 10 (SNR ≥ 60 dB)* — comfortable for a bus-powered bench digitizer.
- **Selected: SNR ≥ 60 dB.** The prompt specifies resolution (12 bits), not accuracy. Flagging this explicitly because it is the single largest cost lever in the design; if the user wants true 12-bit accuracy, this is the requirement to revisit.

**D6 — How to meet "0.1 s of samples at max rate".**
- *Stream continuously to host*: 2 ch × 10 MSPS × 2 B = **40 MB/s**. USB 2.0 HS bulk tops out near 42 MB/s in ideal conditions and well below that under a loaded host OS. Marginal-to-impossible; a dropped packet loses samples.
- *Burst to on-board memory, then read out*: needs ≥ 4 MB of memory; read-out at 20 MB/s takes ~0.2 s. Deterministic, no host-timing dependence.
- *Compress on the fly* — signal-dependent, no guarantee.
- **Selected: burst capture to on-board memory, then read out.** This makes "≥ 4 MB of fast memory" a hard architectural requirement (F6) and is the most consequential decision in the spec.

**D7 — Assembly house.**
- **Selected: JLCPCB**, because it is what the sourcing stage in this pipeline can verify stock against in real time.

**D8 — Layer count.**
- *2-layer* — cannot give a clean ground plane under a 10 MSPS ADC or controlled-impedance USB HS pair.
- *4-layer* — sufficient; standard cost at JLCPCB.
- *6-layer* — no justification.
- **Selected: 4-layer.**

**D9 — Triggering.**
- *Software trigger only* — host says "go", board captures 0.1 s. Meets the stated requirement exactly.
- *Analog level trigger in the FPGA* — nice, more logic, not requested.
- *External trigger input* — an extra connector, not requested.
- **Selected: software trigger only.** Pre-/post-trigger positioning can be added in logic later without a board change.

---

## Open questions (assumptions that would change the design if wrong)

1. **D5 (SNR ≥ 60 dB vs. true 12-bit accuracy)** — largest cost/complexity lever.
2. **D6** — if the user actually wants an *unbounded* streaming digitizer rather than a
   0.1 s burst instrument, USB 2.0 is the wrong interface and the whole architecture changes.
3. **P2** — the 1.5 A ceiling assumes the host is a Type-C source offering ≥ 1.5 A. A legacy
   A-to-C cable presents only 500 mA (Rp default); the board must either fit in 500 mA or
   detect and refuse. **Architect must state which.**
4. **R3** — $90/board is an assumed target, not a user constraint.
