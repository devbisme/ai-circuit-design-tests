# IC selection and design arithmetic (dual_adc_usb)

Stock/price are live JLCPCB figures pulled 2026-09-21 via the pcbparts MCP. Price is CNY.
**The JLCPCB DB returned `basic:0 preferred:0` for every category queried — tier data was
not available in this snapshot. Every part below is therefore assumed Extended tier; the
part-sourcer must re-check tier and re-verify stock before ordering.**

---

## 1. Converter topology (open question / requirement 4)

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| (a) one dual 12-bit ADC | 1 part, 1 clock pin, guaranteed simultaneity | only JLC candidate is **ADS5231IPAGT** (C2670079, 154 pcs, ¥31.8, Iq 97.3 mA = 321 mW); no pin-compatible second source; TI lifecycle unverifiable | **rejected** |
| (b) **two single 12-bit ADCs on one clock** | 180 mW total, pin-compatible second source, single-ended or differential drive | 2 parts, clock must fan out to 2 pins | **CHOSEN** |
| (c) one faster ADC time-multiplexed | fewer parts | **violates F1 (HARD): a mux samples the two channels at different instants.** A 20 MSa/s part muxed gives 50 ns skew *and* halves each channel's aperture; F1 says "simultaneously sampled, not multiplexed" | **ruled out on F1** |

Skew for (b): both CLK pins on one net, trace-matched to ±5 mm. 5 mm of microstrip ≈ 33 ps.
**33 ps ≪ 100 ns (F13)** — 3000x margin.

### ADC part choice

| MPN | LCSC | Stock | ¥ | Package | Power @ rate | Why |
|---|---|---|---|---|---|---|
| **AD9237BCPZ-40** | C514275 | 211 | 32.84 | LFCSP-32 (5x5) | 90 mW @20 MSa/s, 135 mW @40 | **CHOSEN** |
| AD9235BCPZ-40 | C653327 | 139 | 25.30 | LFCSP-32 (5x5) | 55 mA x 3.3 V = 182 mW | **vetted second source** — same family, same 32-lead LFCSP, same 2.7–3.6 V, same parallel CMOS 12-bit interface. Lost on power (182 mW vs 90 mW) and on stock (139 vs 211). Phase 4 must confirm the pinouts are identical before it is used as a drop-in. |
| ADS5231IPAGT | C2670079 | 154 | 31.77 | TQFP-64 | 321 mW | lost: 1.8x the power of two AD9237s, no second source |

AD9237 runs at 10 MSa/s (we clock it at 10.000 MHz, well inside its 1–40 MHz range).
Budgeted at the 20 MSa/s datasheet figure, 90 mW each — conservative.

---

## 2. Front end — input impedance (open question 1, resolved)

| Option | Pros | Cons |
|---|---|---|
| **1 MΩ ∥ 20 pF compensated divider** | works with any 10x passive probe, the thing "standard oscilloscope leads" usually means; 50 V-tolerant by construction | needs a pA-bias buffer, needs C ratio matched to R ratio |
| ~100 kΩ resistive divider | cheaper, no compensation | a 10x probe into 100 kΩ reads 10x low and cannot be compensated; kills the stated use case |
| 50 Ω terminated | best HF fidelity | ±10 V into 50 Ω = 2 W; absurd here |

**Kept phase 1's choice: 1 MΩ ∥ 20 pF.** The buffer it needs (TPH2501, 0.3 pA bias) costs
¥0.53 and 21 mW — far less than the usefulness lost by breaking 10x-probe compatibility.

### Attenuator arithmetic (exact values, E96/E24)

- `R_top = 909 kΩ` (E96), `R_bot = 90.9 kΩ` (E96). **909 + 90.9 = 999.9 kΩ** -> input R is
  1 MΩ to within 0.01 %. (900 kΩ is not an E-series value; 909/90.9 is, and it lands on
  1 MΩ. Division is therefore **1/11**, not 1/10 — the FDA makes up the 1.1x.)
- Division ratio = 90.9 / 999.9 = **0.090909** (bottom leg over total — `R_top` is the leg
  from the BNC to the node, `R_bot` from the node to `VREF_OFF`).
- `C_top = 22 pF` (C0G), `C_bot = 220 pF` (C0G).
  Input capacitance = C_top·C_bot/(C_top+C_bot) = 22·220/242 = **20.0 pF** — meets I2.
- Compensation: 909 kΩ x 22 pF = **20.0 µs**; 90.9 kΩ x 220 pF = **20.0 µs**. Matched
  exactly, so the divider is flat from DC to the buffer's bandwidth.
- Offset injection: `R_bot` returns to `VREF_OFF`, not GND, so
  `V_node = 0.090909·V_in + 0.909091·VREF_OFF`. With VREF_OFF = 1.807 V ->
  V_node(0 V) = **1.643 V**, V_node(+10 V) = 2.552 V, V_node(−10 V) = 0.734 V.
  All inside a 0–3.3 V rail with 0.73 V of headroom at both ends. **This is what removes the
  −5 V rail that SPEC P5 expected** (P5 is SOFT and says the rail set is the architect's call).
- Fault: ±50 V DC at the BNC -> V_node = 0.091·(±50) + 1.64 = −2.9 V / +6.2 V, clamped by
  D100 (BAV199) through `R102 = 1 kΩ`. Clamp current = (6.2 − 3.3)/(90.9 kΩ ∥ 909 kΩ + 1 kΩ)
  = 2.9 V / 83.6 kΩ = **35 µA** — three orders below the BAV199's rating. Power in R_top at
  50 V = (50 − 1.6)²/909 kΩ = **2.6 mW** (use 0805, 150 V working).
- `VREF_OFF` divider: 10.0 kΩ (top, from +3V3A_AMP) / 12.1 kΩ (bottom, to GND) ->
  3.300 x 12.1/22.1 = **1.8068 V**, RC-filtered (5.48 kΩ ∥ 1 µF = 29 Hz) and buffered by U7.
  1 % resistors -> ±1 % on VREF_OFF -> ±16 mV at the node = **±1.6 % FS offset**, above the
  ±1 % of F12 but F12 is SOFT and explicitly "before host-side calibration".

### Anti-alias filter — why 4th order, with the working

Requirements: F8 **HARD** −3 dB ≥ 4 MHz; F9 **SOFT** ≥ 3rd order and ≥ 25 dB at 10 MHz.

**These two cannot both be met by a 3rd-order Butterworth.** For −25 dB at 10 MHz a 3rd
order needs (10/fc)^6 = 10^2.5 − 1 = 315 -> fc = 10/315^(1/6) = **3.83 MHz**, which breaks
the HARD 4 MHz. Three cascaded *real* poles are worse still (−11.8 dB at 10 MHz for a
4.2 MHz corner). A 4th order at 24 dB/octave clears both:

**4th-order Butterworth, f0 = 4.45 MHz**, as two Sallen-Key sections (low-Q first):

| section | R (x2) | C1 (feedback) | C2 (to GND) | f0 = 1/(2πR√(C1C2)) | Q = ½√(C1/C2) |
|---|---|---|---|---|---|
| A | 147 Ω (E96) | 270 pF | 220 pF | 1/(2π·147·243.7 pF) = **4.443 MHz** | ½√1.2273 = **0.554** |
| B | 137 Ω (E96) | 680 pF | 100 pF | 1/(2π·137·260.8 pF) = **4.454 MHz** | ½√6.80 = **1.304** |

(Butterworth targets are Q = 0.5412 and 1.3065 at a common f0 — ours are 0.554 / 1.304.)
**Four capacitors, four distinct nodes, four poles**: C102 sits between node `CH1_SKA_X` and
the U101 output, C103 from `CH1_SKA_Y` to GND; likewise C104/C105 in section B. No two of
them share a node behind the same series resistor.

Composite magnitude, computed from the values above (f0 = 4.45 MHz):
- **4.0 MHz:** x = 0.899. A: 1/√((1−x²)² + (x/0.554)²) = 1/√(0.0369+2.632) = 0.612.
  B: 1/√(0.0369 + (x/1.304)²) = 1/√0.5122 = 1.397. Product = **0.854 = −1.37 dB** (droop at
  the highest in-band frequency).
- **4.45 MHz:** A = 0.554, B = 1.304, product 0.722 = **−2.83 dB** -> −3 dB lands at
  ≈4.5 MHz, **≥ 4 MHz with 12 % margin** (5 % C0G caps + 1 % R shift f0 by ≈±3 %).
- **10 MHz (alias edge):** x = 2.247. A: 1/√(16.40+16.45) = 0.1745.
  B: 1/√(16.40+2.970) = 0.2272. Product = 0.0397 = **−28.0 dB ≥ 25 dB.**

The ADC kickback network (33 Ω x2 + 22 pF differential) is a 5th pole at
1/(2π·66·22 pF) = 110 MHz — deliberately far out of band, because it must also settle: its
τ = 66 Ω·22 pF = 1.45 ns, and the AD9237 track window at 10 MSa/s is ≈50 ns = **34 τ**,
far past the 8.3 τ needed for 12-bit settling.

### Front-end amplifiers

| Role | MPN | LCSC | Stock | ¥ | Why it won |
|---|---|---|---|---|---|
| follower + 2 SK sections (3 per channel, 6 total) | **TPH2501-TR** (3PEAK, SOT-23-5) | C126713 | 13 067 | 0.53 | RRIO **and** 0.3 pA bias — both are mandatory: 0.3 pA x 82.6 kΩ source = 25 nV of offset, while a bipolar 1.5 µA part (LMH6643) would give 124 mV = 12 % FS. 120 MHz GBW = 27x the 4.45 MHz f0; SR 180 V/µs vs the 2π·4.45 MHz·0.91 V = **25.4 V/µs** needed at full scale. |
| — | OPA2357AIDGSR | C529302 | 5 117 | 1.74 | lost: dual package would straddle two `analog_frontend` instances, breaking modular block boundaries; 3.3x the price |
| — | GS8052-SR | C157722 | 21 962 | 0.54 | lost: **rail-to-rail output only.** Input CM on 3.3 V tops out ≈2.1 V; our signal reaches 2.55 V. Would clip at +10 V input. |
| single-to-differential ADC driver (2) | **THS4521IDR** (SOIC-8) | C16092 | 12 361 | 1.75 | 1.14 mA/ch (3.8 mW on 3.3 V), RRI, 95 MHz, integrated VOCM. Gain Rf/Rg = 1.10 kΩ/1.00 kΩ = **1.1**, so 10 V x (1/11) x 1.1 = **1.000 V** = exactly the AD9237's 2 Vpp differential span. |
| — | THP210DR | C2873612 | 7 738 | 4.31 | lost: 9.2 MHz GBW, 15 V/µs — a precision DC part, far too slow |
| DC reference buffer (1) | SGM8521 or equivalent µA-class RRIO single | — | — | — | DC only; the sourcer may substitute freely |

---

## 3. Capture engine and host link (open question 3, resolved)

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **FPGA + SDRAM + FX2LP slave FIFO** | the sigrok/fx2lafw pattern, open firmware exists, 48 MB/s FIFO, ¥11 bridge | 3 ICs | **CHOSEN** |
| FPGA + ULPI PHY + soft USB device core | fewer ICs | a USB 2.0 HS device core is a multi-month firmware project; ULPI PHY stock at JLC is thin | rejected on risk |
| MCU only | fewest parts | **arithmetically impossible.** 2 ch x 12 bit at 10 MSa/s needs a 24-bit-wide parallel capture every 100 ns with zero jitter and 40 MB/s to RAM. The fastest JLC-stocked MCUs (STM32H7 class) have ~1 MB of SRAM — 0.025 s of capture, 4x short of F5 — and their FMC/DCMI ingest paths cannot latch two independent 12-bit buses on a 10 MHz external clock without an FPGA-like state machine. It also cannot reach 4 MB without external SDRAM, at which point the FPGA is the cheaper controller. | ruled out with numbers |

| Block | MPN | LCSC | Stock | ¥ | Why |
|---|---|---|---|---|---|
| FPGA | **XC6SLX9-2TQG144C** | C27408 | 1 245 | 7.35 | 102 user I/O in a **QFP** (no BGA — Y2), 9 152 LEs, VCCINT 1.2 V + VCCAUX/VCCO 3.3 V = only **two** rails. I/O demand: 26 (ADC data+OTR) + 1 (clk) + 39 (SDRAM) + 17 (FX2) + 3 (LED/reset) = **86 of 102**. |
| — | EP4CE6E22C8N | C36238 | 280 | 28.7 | lost: 91 I/O (86 used leaves 5 spare), needs a **third** rail (2.5 V VCCA for the PLL), 4x the price, 4.4x less stock |
| — | GW1NR-LV9QN88 | C5799578 | 173 | 23.3 | lost: QFN-88 has too few user I/O for a 39-pin SDRAM bus; its embedded-SDRAM claim could not be verified from the parts DB |
| — | ICE40UP5K-SG48I | C2678152 | 444 | 10.4 | lost: 39 I/O, and 128 kB of SPRAM is 1/32 of the required buffer |
| Buffer RAM | **W9825G6KH-6I** | C97572 | 2 978 | 9.80 | 256 Mbit = **32 MB**, x16, 166 MHz, TSOP-54. Industrial (−40–85 °C) part chosen over the 0–70 °C W9825G6KH-6 (C62246, 701 pcs) because it has 4x the stock at ¥3.6 more. |
| — | QSPI PSRAM (APS6404L) | — | — | — | lost: 4-bit at 133 MHz = 66 MB/s raw against a 40 MB/s requirement — 1.65x margin, and the 8 µs tCEM limit forces the controller to chop every burst. SDRAM gives 3.5x margin on a well-trodden path. |
| USB bridge | **CY7C68013A-56LTXC** | C14912 | 1 328 | 11.01 | QFN-56, 8-bit slave FIFO at 48 MHz = 48 MB/s ≥ the ~43 MB/s USB HS bulk ceiling, so the bridge is never the bottleneck. fx2lafw is open source. |
| — | CY7C68013A-56PVXC | C26717 | 143 | 16.75 | same die in SSOP-56 — **second source**, easier to hand-rework, but 9x less stock and 52 % dearer |
| Config flash | W25Q32JVSSIQ | — | — | — | Spartan-6 SPI master mode (M[1:0] = 01); jellybean |
| FX2 EEPROM | 24LC64-I/SN | — | — | — | VID/PID + optional firmware; jellybean |

### Memory depth and bandwidth arithmetic

- Storage per sample instant: 2 ch x 16-bit word = **4 B / 100 ns** -> **40 MB/s** write.
- 32 MB / 4 B = 8.388 MSa per channel = **0.839 s at 10.000 MSa/s**. Requirement F5 is
  0.1 s / 1 MSa per channel -> **8.4x margin** (decision 6 asked for ~8x).
- SDRAM bandwidth: x16 at 100 MHz = 200 MB/s raw. Refresh is 8 192 rows / 64 ms =
  128 k cycles/s x ~70 ns = **0.9 %** overhead. Even at 70 % page efficiency the write path
  has ≥140 MB/s against 40 MB/s needed — **3.5x margin**.
- Drain: 32 MB / 35 MB/s = **0.91 s**. Capture and drain never overlap (F6).

### Clock-jitter arithmetic (requirement 7, the highest-value constraint)

Ideal 12-bit SNR = 6.02·12 + 1.76 = 74.0 dB. Jitter-limited SNR = −20·log10(2π·f_in·t_j).
Setting them equal at the top of the passband, f_in = 4.45 MHz:
t_j = 10^(−74/20)/(2π·4.45 MHz) = 1.995e−4 / 2.796e7 = **7.1 ps RMS**.
At f_in = 5 MHz (Nyquist) it tightens to **6.35 ps** — phase 1's 6.4 ps figure reproduces.
A 5 ps XO gives 20·log10(1/(2π·5e6·5e−12)) = **76.1 dB**, i.e. jitter is not the limit.

| Role | MPN | LCSC | Stock | ¥ | Why |
|---|---|---|---|---|---|
| ADC sample clock | **SX3M10.000B10F20TNN** (SMD3225, 3.3 V CMOS, ±10 ppm) | C5452682 | 2 023 | 0.34 | 10.000 MHz exactly, 3.3 V CMOS straight into both ADC CLK pins |
| — | RO10000012 (SMD3225, ±10 ppm) | C7206322 | 2 529 | 0.50 | equal second source |
| — | RU10000032 (SMD2016) | C19173169 | 2 870 | 0.49 | smaller, ±20 ppm — lost on tolerance only |
| clock isolation buffer | SN74LVC1G17DBVR | — | — | — | keeps the FPGA's input C and trace reflections off the ADC clock node |

**No 10 MHz oscillator in the JLC catalogue publishes an RMS phase-jitter number** — see
`## Carried forward` in the handoff.

---

## 4. Power tree

| Role | MPN | LCSC | Stock | ¥ | Why |
|---|---|---|---|---|---|
| inrush / soft-start switch | **TPS22919DCKR** (SC-70-6) | C2149796 | 78 394 | 0.13 | built-in slew control, 1.5 A, 1.6–5.5 V |
| — | TPS22810DBVR | C205990 | 26 346 | 0.51 | adjustable CT — second source if TPS22919's fixed ramp proves too fast |
| 3.3 V and 1.2 V bucks (x2, same PN) | **SY8089AAC** (SOT-23-5) | C5187495 | 10 740 | 0.39 | **2.7–5.5 V input** — TPS562201 (¥0.06) was rejected because its 4.5 V minimum has no margin against a 4.4 V USB VBUS droop. 2 A, 1 MHz, VFB = 0.600 V (datasheet-confirmed). |
| — | AP61100Z6-7 | C1858397 | 8 884 | 0.22 | 2.3–5.5 V, 1 A, SOT-563 — vetted second source |
| analog LDOs (x2) | **TPS73633DBVR** (SOT-23-5) | C28038 | 8 349 | 0.52 | fixed 3.3 V (no divider to get wrong), **30 µVrms** noise, 400 mA, 75 mV dropout from 5 V. Satisfies P6/decision 13. |

### Feedback dividers — computed from SY8089A's own VREF = 0.600 V

`Vout = 0.6·(1 + R_top/R_bot)`, `R_top` from VOUT to FB, `R_bot` from FB to GND.

- **+3V3D:** R_top = **45.3 kΩ** (E96), R_bot = **10.0 kΩ** ->
  0.6·(1 + 4.530) = **3.318 V** (+0.55 %, inside every load's 3.3 V ±5 % window).
- **+1V2:** R_top = **10.0 kΩ**, R_bot = **10.0 kΩ** -> 0.6·(1 + 1.000) = **1.200 V**
  (Spartan-6 VCCINT 1.14–1.26 V).
- The TPS73633 is a **fixed** 3.3 V part — no divider, so no VREF to get wrong.

### Rail-by-rail power budget (resolves open question 2)

| Rail | Loads | Current | Conversion | Current drawn from VBUS |
|---|---|---|---|---|
| +3V3A_ADC | 2 x AD9237 @ 90 mW | 54.5 mA | LDO (1:1) | 54.5 mA |
| +3V3A_AMP | 6 x TPH2501 (6.5 mA) + 2 x THS4521 (1.14 mA) + ref buffer | 42.3 mA | LDO (1:1) | 42.3 mA |
| +3V3D | FPGA I/O 41 + VCCAUX 15 + SDRAM 60 + FX2 85 + flash/LED/XO/buffer 18 | 219 mA (budget 225) | buck, 88 % | 225·3.3/(5·0.88) = 168.8 mA |
| +1V2 | XC6SLX9 VCCINT (20 mA static + ~60 mA dynamic) | 80 mA | buck, 85 % | 80·1.2/(5·0.85) = 22.6 mA |
| — | regulator Iq, CC pulldowns, load switch | 5 mA | — | 5 mA |
| **Total** | | | | **293 mA = 1.47 W at 5 V** |

FPGA I/O figure: 38 SDRAM lines x 10 pF x 3.3² x 25 MHz effective = 103 mW, plus 24 ADC
lines at 5 MHz effective = 13 mW, plus 8 FX2 lines at 24 MHz effective = 21 mW (drain only,
never concurrent with capture) -> 137 mW = 41 mA.

**293 mA is 65 % of the 450 mA (P2) ceiling.** Adding 30 % to every line gives
**381 mA = 1.90 W**, still under 450 mA. **P3 does not fire: no CC current sensing is
required.** The USB-C connector keeps plain 5.1 kΩ CC1/CC2 pulldowns and the board is legal
on any 500 mA USB 2.0 port.

Inrush (P4): ≤10 µF sits on raw VBUS (the USB 2.0 limit); the 47 µF bulk is downstream of
U2. With TPS22919's ~2 ms ramp, I = C·dV/dt = 47 µF x 5 V / 2 ms = **118 mA**, on top of a
start-up load well under 200 mA — the 500 mA budget is never exceeded.

LDO thermals: (5.0 − 3.3) x 54.5 mA = **93 mW** in the ADC LDO; SOT-23-5 θJA ≈ 200 °C/W ->
19 °C rise -> 69 °C junction at the 50 °C ambient limit of Y3. The amp LDO dissipates 72 mW.

---

## 5. Connectors

| Role | MPN | LCSC | Stock | ¥ | Note |
|---|---|---|---|---|---|
| analog inputs (x2) | **KH-BNC50-3511** | C2837587 | 6 798 | 0.93 | 50 Ω, right-angle, THT — the Y2 exception. **Custom footprint required.** |
| — | DOSIN-801-0050 | C521210 | 1 378 | 0.78 | equivalent right-angle BNC, second source |
| host port | **TYPE-C 16PIN 2MD(073)** | C2765186 | 1 083 662 | 0.07 | USB 2.0 pinout, D+/D− on A6/B6 and A7/B7 |
| USB ESD | USBLC6-2SC6 | — | — | — | KiCad symbol exists (EXACT match) |

---

## 6. Input ESD clamp (rev.2 — re-selected after the phase-6 escalation)

<!-- revised: rev.1 chose ESD9B5.0ST5G on the strength of a "≤0.5 pF" line in the BOM that
     was wrong by 30x, and placed it on CHn_BNC where it conducted at full scale. Both the
     placement and the part are corrected here. -->

**Where it goes is settled first, because it changes what the part has to be.** The clamp
sits on `CHn_BUFIN`, behind R102 = 1.00 kΩ, alongside D100 (BAV199). The BNC node carries
no semiconductor at all. Consequences, derived in full in `net_plan.md` §"Input protection":
the clamp node spans **0.734–2.552 V** at ±10 V full scale (F2 ✓), the ±50 V DC fault is
absorbed by the 909 kΩ at **≈26 µA** into the BAV199 (I3 ✓), and `Cin` stays at exactly
**20.0 pF** with both legs τ-matched at **20.0 µs** (I2 ✓).

That leaves one thing to buy: a part whose junction capacitance does not spoil the
anti-alias response through R102.

### The pole, computed — this is the whole selection criterion

R102 = 1.00 kΩ drives everything on `CHn_BUFIN`: the TVS, D100's two junctions
(BAV199, ~1.5 pF each → ~3 pF), U100's input capacitance (TPH2501, ~3 pF) and ~1.5 pF of
trace. **Baseline node capacitance with no TVS at all is therefore ~7.5 pF**, and the
phase-6 measurement of the filter (−3 dB at 4.45 MHz, −29.4 dB at 10 MHz, +0.40 dB peaking)
did **not** include any of it. Every candidate below is scored on top of that 7.5 pF.

Chain model: the measured 4th-order response, treated as Butterworth with f_c = 4.45 MHz,
cascaded with the single real pole f_p = 1/(2π · 1.00 kΩ · C_node):

| candidate | Cj | C_node | f_p | −3 dB (nominal) | −3 dB (worst case†) | 10 MHz | verdict |
|---|---|---|---|---|---|---|---|
| ESD9B5.0ST5G (rev.1 incumbent), C111566 | 15 pF | 22.5 pF | 7.07 MHz | 4.08 MHz | **3.83 MHz** | −33 dB | **REJECTED — fails F8 (HARD)** |
| **ESD9L5.0ST5G, onsemi, C82326** | **0.9 pF** | **8.4 pF** | **18.9 MHz** | **4.39 MHz** | **4.18 MHz** | **−30.5 dB** | **SELECTED** |
| ESD9L5.0ST5G-MS, MSKSEMI, C2830130 | 0.3 pF | 7.8 pF | 20.4 MHz | 4.40 MHz | 4.19 MHz | −30.3 dB | rejected on sourcing, see below |
| no TVS at all (BAV199 only) | — | 7.5 pF | 21.2 MHz | 4.40 MHz | 4.20 MHz | −30.2 dB | rejected — I3 names an ESD clamp |

† worst case = filter C0G caps at their +5 % tolerance limit (f_c → 4.24 MHz) **and** the
TVS at its datasheet-max Cj.

Working, for the selected part, so the next reader can check it instead of trusting it:

- `f_p = 1/(2π × 1000 Ω × 8.4 pF) = 18.95 MHz`
- loss at 4.45 MHz `= 10·log10(1 + (4.45/18.95)²) = 0.233 dB`
- new −3 dB: solve `10·log10(1 + (f/4.45)^8) + 10·log10(1 + (f/18.95)²) = 3`
  → at f = 4.39 MHz the two terms are 2.781 + 0.227 = **3.008 dB** → **f_−3dB = 4.39 MHz**
- at 10 MHz: `−29.4 dB − 10·log10(1 + (10/18.95)²) = −29.4 − 1.07 = **−30.5 dB**`
- **F8 (HARD, −3 dB ≥ 4 MHz): 4.39 MHz, 9.7 % margin ✓**
- **F9 (SOFT, ≥ 25 dB at 10 MHz): 30.5 dB, 5.5 dB margin ✓**

And for the rejected incumbent, the number that decided it:
`f_p = 1/(2π × 1000 × 22.5 pF) = 7.07 MHz`; at 4.45 MHz that costs 1.449 dB, dragging the
−3 dB point to **4.08 MHz nominal**. With +5 % C0G caps and Cj at its 18 pF max it lands at
**3.83 MHz** — under a HARD 4 MHz limit, with no margin left to spend. A 3-cent part change
buys the margin back; re-centring both Sallen-Key sections to absorb the pole would mean
re-deriving the 4th-order response and re-sourcing 8 capacitors per channel to buy the same
thing. **The part changes; the filter does not.**

### Why ESD9L5.0ST5G (C82326) and not the others

- **vs. the incumbent ESD9B5.0ST5G:** 0.9 pF against 15 pF, same 5 V standoff, same SOD-923
  land pattern, same onsemi datasheet family, same Extended tier, 92,164 in stock (live) vs
  the incumbent's row that had never been sourced at all. It loses nothing and wins the only
  contested spec. It is also **unidirectional**, which is fine and in fact preferable here:
  `CHn_BUFIN` never goes below +0.734 V in normal operation, and a negative fault is already
  pinned at −0.7 V by D100's lower diode, where the TVS merely conducts in parallel at the
  same ~27 µA the 909 kΩ allows. Unidirectional is how it gets 0.9 pF at a 5 V standoff.
- **vs. MSKSEMI ESD9L5.0ST5G-MS (C2830130), 0.3 pF bidirectional:** lower Cj, but SOD-882 is
  a *different* land pattern (extra footprint work on a design whose footprint gate already
  failed twice on package variants), stock is 1,033 against 92,164, Ipp is 1 A against 4 A on
  the alternates, and the 0.3 pF buys 0.01 MHz of bandwidth. **Lost on sourcing risk for a
  benefit that rounds to zero.**
- **vs. BORN ESD9L5.0ST5G-N (C316041), 0.6 pF, 405 k stock, cheaper:** DFN1006-2, again a
  different land pattern, and a house-brand part on a node where leakage is signal error.
  Same reasoning, same verdict.
- **vs. deleting the TVS:** I3 (HARD) says "clamped, series-limited"; the BAV199 is a
  low-leakage switching pair, not a characterised ESD device. Keeping an IEC 61000-4-2-rated
  part in the path is the defensible reading and costs 0.01 MHz.
- **Vetted second source:** MSKSEMI **C7379964**, `ESD9L5.0ST5G`, SOD-923, 0.5 pF, 18,153 in
  stock — a drop-in on the same land pattern with the same polarity. Use it if C82326 moves.

**Leakage caveat, stated because it is a real cost of this choice.** The BAV199 was picked
for its ~1 nA leakage precisely because leakage at this node is signal error: the Thevenin
source is 909 kΩ ‖ 90.9 kΩ = 82.6 kΩ, so 1 µA would be an 83 mV offset (≈4.5 % FS referred
to input). onsemi specifies Ir = 1 µA **max at the full 5 V standoff**; at the 0.73–2.55 V
this node actually sees, and at room temperature, it is orders of magnitude below that.
This is a **bounded but unverified** number — see `design_risks.md` R12.

**Symbol note for the sourcer/coder:** there is no local KiCad symbol for `ESD9L5.0ST5G`
(checked: `Diode:ESD9B5.0ST5G` exists, `ESD9L…` does not). It is a 2-pin unidirectional TVS
— use `Device:D_TVS` or `Device:D_Zener` with `value='ESD9L5.0ST5G'` and
`footprint='Diode_SMD:D_SOD-923'`; no symbol generation is needed. **Cathode (pin 1) to
`CHn_BUFIN`, anode (pin 2) to `GND`.** Polarity is load-bearing now that the part is
unidirectional.
