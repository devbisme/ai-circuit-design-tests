# IC selection

Stock, price and tier are live JLCPCB data pulled during this phase (2026-09-22) via the
`find-part` skill. Every candidate row was looked up; losers are kept with the one-line
reason they lost. All prices are qty-1 unless noted; qty-5 is the build quantity.

---

## 1. KEYSTONE — sample memory (≥ 4 MB at 40 MB/s write)

**Required:** 2 ch × 10 MSPS × 2 B/sample = **40 MB/s sustained write**;
0.1 s × 40 MB/s = **4,000,000 B**.

| Option | Depth | Write BW | Board pins | JLCPCB | Verdict |
|---|---|---|---|---|---|
| **GW1NR-LV9QN88PC6 — FPGA with 64 Mbit PSRAM in package** | **8,388,608 B (2.10×)** | x8 DDR @100 MHz = 200 MB/s raw; derate 50 % for refresh/turnaround → **100 MB/s (2.5×)** | **0** — the die-to-die bus never reaches the PCB | C5799578, 173 pcs, $23.32 (1+) / $22.09 (10+), Extended | **SELECTED** |
| GW1N-LV4QN88C6 + W9864G6KH-6 SDRAM | 8 MB | x16 @143 MHz = 286 MB/s | **~39 I/O** — QN88 cannot carry 39 memory + 27 ADC + 15 FIFO | C31900351 $15.81 + C62378 $4.41, both deep stock | Rejected: pin count, 54-pin TSOP-II area, and it saves only $3 |
| GW1N-4 + 2× APS6404L QSPI PSRAM (x4 each, paralleled) | 16 MB | 2 × 66 MB/s = 132 MB/s | 10 | C5360305, **only 39 pcs**, $5.70 | Rejected: stock below the 100-unit floor; tCEM 8 µs burst ceiling complicates the controller |
| Async SRAM array | 512 kB/device → 8 devices | fine | >60 | — | Rejected on device count and pins |
| MCU with on-chip SRAM (STM32H7 class, 1 MB) | 1 MB | — | — | — | **Rejected: 1 MB < 4 MB.** No MCU on JLCPCB reaches 4 MB of on-chip SRAM |

**Why it won:** the in-package PSRAM removes the memory bus from the PCB entirely — no
length-matched 39-bit bus, no extra BGA/TSOP, no signal-integrity budget — and it is the only
option that gives 2× the required depth without spending a single FPGA I/O. The cost premium
over "GW1N-4 + SDRAM" is $3.10/board.

**Headroom arithmetic:** 8,388,608 B / 40 MB/s = **0.2097 s of capture** (required 0.1 s).
Elastic buffering between the uniform 10 MHz sample stream and burst PSRAM writes uses the
FPGA's 468 kbit (58.5 kB) BSRAM; a 4 µs PSRAM chip-select burst at 200 MB/s moves 800 B, so
58.5 kB of FIFO is ~70× the largest gap.

⚠ **Unverified keystone fact** — see `## Carried forward` in the handoff: the exact free-I/O
count of the GW1NR-9 QN88P package, and whether the embedded PSRAM needs its own supply pin.
Design needs **51 user I/O**; contingency if fewer are available is in `design_risks.md` R-7.

---

## 2. Digital controller

| Candidate | Key numbers | JLCPCB | Verdict |
|---|---|---|---|
| **GW1NR-LV9QN88PC6** | 8640 LUT4, 468 kbit BSRAM, 64 Mbit PSRAM, 1.2 V core / 3.3 V I/O, embedded config flash (instant-on, no external SPI flash) | 173 pcs, $23.32 | **SELECTED** |
| GW2AR-LV18QN88C8 | 20 kLUT + 64 Mbit embedded SDRAM | 125 pcs, **$43.42** | Rejected: +$20 for logic we do not use |
| GW1NSR-LV4CQN48PC6 (Cortex-M3 + 64 Mbit PSRAM) | same memory, hard CPU | 466 pcs, $17.72 | Rejected: **QFN-48 cannot carry 51 I/O** |
| High-pin-count MCU (STM32H7 + FMC + ULPI PHY) | — | — | Rejected: no 4 MB on-chip; FMC+DCMI cannot ingest 2 simultaneous 12-bit buses at 10 MSPS and service USB HS concurrently with determinism |

An FPGA is required, not preferred: three concurrent constant-rate streams (24-bit ADC ingest,
PSRAM burst write, 60 MHz FIFO read-out) with no software jitter budget.

## 3. USB 2.0 High-Speed path

| Candidate | Key numbers | JLCPCB | Verdict |
|---|---|---|---|
| **FT232HL** | USB 2.0 HS PHY on chip, 245 sync FIFO 8 bit @60 MHz = 60 MB/s interface ceiling; royalty-free D2XX/libusb; ACBUS8/9 free in FIFO mode for **PWREN#** | C51997, **2016 pcs**, $9.72, LQFP-48 | **SELECTED** |
| FT2232HL | adds channel B for MPSSE JTAG (no separate programmer) | ~$7–13, LQFP-64 | Rejected: +$3, +16 pins, and PWREN# availability in sync-FIFO mode is murkier. A $0.10 JTAG header does the same job |
| CY7C68013A (FX2LP) | 8/16-bit slave FIFO @48 MHz, ~$3 | cheap | Rejected: needs 8051 firmware + EEPROM + driver work; no firmware phase exists in this pipeline |
| Soft USB HS inside the FPGA | — | — | Rejected: **USB HS needs a real PHY**; a full-speed-only path fails requirement 7 (≥20 MB/s) by 40× |

**Read-out arithmetic:** 4,000,000 B ÷ 30 MB/s (conservative HS bulk) = **0.13 s**; requirement
is ≥20 MB/s ⇒ ≤0.2 s. Interface ceiling 60 MB/s is never the limit.

## 4. ADC

Requirement: 2 ch, simultaneous, 12 bit, 10 MSPS, SNR ≥ 60 dB.

| Candidate | Key numbers | JLCPCB | Verdict |
|---|---|---|---|
| **ADS5231IPAGT** | **dual, simultaneous sampling in one package**, 12 bit, 40 MSPS, single +3.3 V, SNR 70.7 dBFS, 321 mW, 2 Vpp diff, VCM 1.5 V, TQFP-64 | C2670079, 154 pcs, **$31.78** ⚠ >$25 | **SELECTED** |
| 2× AD9220ARSZ-REEL | 12 bit, **10 MSPS max (zero margin)**, 5 V supply, 51 mA each = 510 mW, SSOP-28 | C653287 52 pcs + C139589 18 pcs, $14.19 ea = $28.38 | **Vetted second source.** Loses on: +190 mW, a 5 V analog rail, no oversampling headroom, and channel skew becomes a board problem instead of a die problem |
| 2× AD9235BCPZ-40 | 12 bit, 40 MSPS, 3.3 V | 139 + 26 pcs, $25.30 ea = **$50.60** | Rejected on price (2× the winner's channel cost) |
| 2× AD9629BCPZRL7-40 | 12 bit, 40 MSPS, 1.8 V | **only 20 pcs**, $16.04 ea | Rejected: stock below floor; adds a 1.8 V rail |
| ZGAD65D12C (Zynalog) | dual, simultaneous, 65 MSPS, $16.40 | **24 pcs** | Rejected: stock, unknown vendor support, LVDS serial output |
| MS9945 (Ruimeng), $4.54 | "12-bit 40 MSPS" | 102 pcs | **Rejected: it is a CCD analogue front end** (AD9945 clone — CDS + PGA, clamped CCD input), not a general-purpose ADC |

**Why ADS5231 won:** it is the only in-stock part that makes simultaneous sampling a *die*
property. `[HARD]` F1 (simultaneity) and `[SOFT]` F12 (≤5 ns skew) are then satisfied by
construction — no matched clock traces, no part-to-part aperture-delay lottery. It also shares
the 3.3 V analog rail with the FDA and gives 4× sample-rate headroom for a future
oversample-and-decimate firmware upgrade.

**Verified from the datasheet (SBAS295A) during this phase — these settle two design questions:**
1. *Minimum clock.* With the internal PLL enabled the minimum is 20 MSPS. "For operation below
   20 MSPS, the PLL can be disabled by programming the internal registers through the serial
   interface. With the PLL disabled, the clock speed can go down to 2 MSPS." ⇒ **10 MSPS is legal,
   but the FPGA must write the PLL-disable register over SEN/SCLK/SDATA at start-up.** This is
   not optional, and it is why those three pins are in the net plan.
2. *Drive.* "The differential full-scale input range … is 2 V_PP. For a nominal value of VCM
   (+1.5 V), IN and IN̄ can swing from 1 V to 2 V" and "the analog inputs should be biased to the
   recommended common-mode voltage (1.5 V)". ⇒ **single-ended drive is out** — it would need a
   0.5–2.5 V swing on one pin and would move the input common mode by ±0.5 V. A fully
   differential driver is mandatory. (Half-scale single-ended drive was considered and rejected:
   it throws away 6 dB of SNR and half the code range of a 12-bit converter.)
3. Also fixed by the datasheet: ISET = 56.2 kΩ 1 %, INT/EXT high for internal reference,
   0.1 µF on REFT and REFB, VCM buffer drive **±2 mA only** (so no resistive load may hang on it —
   one reason the anti-alias filter is singly terminated).

## 5. Analog front end

### 5a. Input buffer — AD8066ARZ-R7 (C9647, 1478 pcs, $9.07, SOIC-8, dual)

| Candidate | Why it lost / won |
|---|---|
| **AD8066ARZ-R7** — dual JFET, 120 MHz, 180 V/µs, I_B = 6 pA, 7 nV/√Hz, 5–24 V supply | **SELECTED.** One package carries both channels' buffers |
| LM6172IMX ($2.09, 100 MHz) | Rejected: I_B = 1.2 µA → 1.2 µA × 82.6 kΩ = **99 mV offset** at the divider node (11 % of the 0.909 V signal). Bias-current cancellation would need an 82.6 kΩ feedback resistor, whose 2 pF stray puts a pole at 1 MHz |
| COS8052MR ($0.32, 100 MHz, CMOS, 2.5 pA) | Rejected: **5.5 V maximum total supply.** The buffer must accept a −0.909 V input common mode *and* the AD8066-class +2.5 V headroom; ±5 V rails are 10 V total |
| ADA4807-1ARJZ ($19.34, single only on JLCPCB) | Rejected: 2 singles = $38.7 versus $9.07 |

The JFET input also matters for capacitance: ~2 pF at the divider node, which is inside the
5 pF stray budget used to set the compensation capacitor.

### 5b. Differential ADC driver — THS4521IDR (C16092, 12 361 pcs, $1.75, SOIC-8)

| Candidate | Why it lost / won |
|---|---|
| **THS4521IDR** — FDA, 95 MHz, 490 V/µs, **1.14 mA**, RRIO, adjustable V_OCM, 2.5–5.5 V single supply | **SELECTED.** Runs straight off the clean +3.3 VA rail with the ADC, V_OCM tied to the ADC's own CM pin |
| THS4503 (TI's own recommendation in the ADS5231 datasheet) | Rejected: ±5 V supply and ~23 mA — 10× the quiescent current, on a bus-powered board |
| 2 extra AD8066 halves as a discrete inverter pair | Rejected: 3 op amps/channel = 3 AD8066 packages ($27.2 vs $12.6) and +66 mA |

**Gain and level arithmetic (exact, from the specified E96 values):**
- Divider: R_top = 909 kΩ, R_bot = 90.9 kΩ → Z_in = **999.9 kΩ** (target 1 MΩ, −0.01 %);
  attenuation = 90.9/999.9 = 0.090909 = **÷11.000**. Top = 909 kΩ (to the BNC), bottom = 90.9 kΩ
  (to ground). ±10 V in → **±0.9091 V** at the buffer.
- FDA: R_g = 1.00 kΩ, R_f = 1.10 kΩ → differential gain = R_f/R_g = **1.100**.
  Differential output = 2 × 0.9091 × 1.100 = **2.000 V_PP** — exactly the ADS5231 full scale.
  Each pin swings 1.5 V ± 0.5 V = **1.0–2.0 V**, exactly the datasheet's per-pin window.
- FDA input common mode at the extremes (R_g = 1 k, R_f = 1.1 k, V_OCM = 1.5 V, reference leg to
  AGND): V_IN− = (V_in/R_g + V_o+/R_f)/(1/R_g + 1/R_f) = **0.476 V at V_in = −0.909 V**,
  **0.952 V at +0.909 V**, 0.714 V at 0 V — inside the THS4521 rail-to-rail input range on a
  3.3 V supply (needs ≥ −0.1 V, ≤ ~2.0 V) ✓.
- **Polarity:** the single-ended-to-differential stage inverts (V_d = −1.1 × V_in with the
  reference leg grounded). It is undone at the connector, not in software: **FDA OUT+ → ADC IN_x−
  and FDA OUT− → ADC IN_x+.** Overall transfer is non-inverting; the coder must not "tidy" this.
- Compensation: C_top = 15 pF, C_bot = 130 pF + 15 pF = 145 pF fixed + ~5 pF node stray = 150 pF.
  R_top·C_top = 909 kΩ × 15 pF = **13.635 µs**; R_bot·C_bot = 90.9 kΩ × 150 pF = **13.635 µs** ✓.
  Input capacitance = (15 × 150)/(15 + 150) = **13.6 pF** + ~4 pF connector/pad stray =
  **≈17.6 pF**, against the "1 MΩ ∥ ~20 pF" target. A ±3 pF error in the stray estimate gives
  ±2 % of high-frequency flatness error (±0.17 dB) above 12 kHz; DC gain is unaffected because
  it is set by resistors alone.

### 5c. Anti-alias filter — passive LC, computed not tabulated

Target: −3 dB ≥ 4 MHz, ≥ 40 dB at 10 MHz. **4 poles are needed and 4 poles are what is there**
— counted as *nodes*, not capacitors.

Per leg (4 identical legs = 2 channels × 2 phases), driven from the FDA output:
`FDA → Rs 100 Ω → L1 3.3 µH → C1 680 pF to AGND → L2 5.6 µH → C2 680 pF to AGND → 22 Ω → ADC pin`

- Pole count: C1 and C2 sit behind **different** series inductors, so they are two distinct
  poles, not one. 2 L + 2 C = **4 poles**, plus the FDA feedback pole (C_f = 4.7 pF across
  R_f = 1.1 kΩ → 30.8 MHz) = 5 poles total.
- Computed response of those exact values (ladder solved numerically, ADC pin modelled as 5 pF):
  −0.41 dB @1 MHz, −1.66 dB @3 MHz, **−0.86 dB @4 MHz**, **−3 dB at 4.23 MHz**,
  −12.1 dB @5 MHz, −33.1 dB @8 MHz, **−41.8 dB @10 MHz**, −57.1 dB @15 MHz.
- It is a Chebyshev-like alignment: the price of 42 dB at 10 MHz from 4 poles is **±1.7 dB of
  passband ripple**. A 4th-order Butterworth at the same corner would give only ~30 dB at 10 MHz,
  and the 6th-order Butterworth that would give 44 dB needs a Q = 1.93 section at 4.3 MHz —
  i.e. an active filter needing ≥170 MHz of GBW per stage. Passive LC has no GBW limit, costs no
  quiescent current, and keeps the op-amp count at two per channel.
- **Tolerance (3000-point Monte Carlo, ADC pin 3–10 pF):**

  | Component tolerance | Worst gain @4 MHz | Worst attenuation @10 MHz |
  |---|---|---|
  | **L ±5 %, C0G ±2 %** (specified) | **−2.24 dB** ✓ | **40.6 dB** ✓ |
  | L ±10 %, C ±5 % | −3.87 dB ✗ | 39.2 dB ✗ |
  | L ±20 %, C ±5 % | −5.85 dB ✗ | 37.3 dB ✗ |

  ⇒ **L1/L2 must be ±5 % and C1/C2 must be C0G ±2 %** (±1 % acceptable). This is a real sourcing
  constraint, not a preference: ±10 % parts miss both `[SOFT]` targets. If only ±10 % inductors
  can be had, the degradation is bounded and documented above — do not escalate, but say so in
  the sourced BOM.
- Drive: minimum |Z_in| of the ladder is 100 Ω, so each leg draws **5 mA peak** at 0.5 V peak;
  THS4521 delivers 35–55 mA ✓.
- The filter is **singly terminated** (source resistor only, open-circuit load). That is
  deliberate: a doubly-terminated design would need a 100 Ω load resistor per leg returning to
  VCM, which would draw ~10 mA per leg from the ADC's VCM pin — and that pin can supply ±2 mA.

## 6. Clock

| Candidate | Verdict |
|---|---|
| **SX3M10.000M20F30TNN — 10.000 MHz CMOS XO, ±30 ppm, 1.62–3.63 V, 10 mA, 3225** (C2901558, 3624 pcs, $0.32) | **SELECTED.** Feeds the ADC CLK pin directly through 33 Ω and the FPGA through 33 Ω |
| 50 MHz XO → FPGA rPLL → ADC clock | Rejected: an FPGA PLL output carries ~20 ps RMS jitter. SNR_jitter = −20·log₁₀(2π × 4 MHz × 20 ps) = **66 dB** — only 6 dB over the `[SOFT]` 60 dB target, spent for nothing |
| XO + dedicated clock fan-out buffer | Rejected: the dual ADC takes **one** clock pin; there is nothing to fan out to except the FPGA |

**Jitter arithmetic:** XO phase jitter ≈1 ps RMS →
SNR_jitter = −20·log₁₀(2π × 4 MHz × 1 ps) = **92 dB**, i.e. jitter is 30 dB below the noise
target and does not enter the error budget.
**Skew:** both ADC channels share one die and one clock pin ⇒ board-level channel skew is
**zero by construction**; the residual is the ADS5231's internal aperture match, far below the
5 ns `[SOFT]` limit.

## 7. Power ICs

| Function | Selected | Alternatives considered |
|---|---|---|
| Load switch (post-enumeration gating) | **TPS22918DBVR** (C131941, 8480 pcs, $0.40) — 2 A, 53 mΩ, soft-start via C_T, EN is 5.5 V tolerant | Discrete P-FET rejected: 3.3 V logic cannot turn it off (V_GS = −1.7 V) |
| EN inverter | **BSS138** logic-level NMOS + 100 kΩ | 2N7002 rejected: V_GS(th) up to 3 V versus a 3.3 V drive |
| 3.3 V digital, 1.2 V core | **TLV62569DBVR** ×2 (C141836, 135 k pcs, $0.08) — 2 A, 1.5 MHz, SOT-23-5 | LDO for the 1.2 V core rejected: (3.3−1.2) × 0.12 A = 252 mW wasted, +74 mA on VBUS |
| 3.3 V analog | **RT9013-33GB** (C47773, 240 k pcs, $0.14) — 500 mA, 30 µV_RMS, 50 dB PSRR @10 kHz | LP5907 (quieter) rejected as Extended/low stock; 30 µV_RMS is −87 dBFS against a 0.707 V_RMS full scale |
| −5 V analog | **TPS60403DBVR** (C11338, 16 k pcs, $0.70) — inverter, 60 mA, R_out 15 Ω | Inverting buck-boost rejected (noise, inductor near the front end); isolated module rejected (cost, size) |
| **1.8 V, U5 VCCIO3 (embedded-PSRAM bank)** | **AP2127K-1.8TRG1** (C151375, 35 912 pcs, $0.154) — 300 mA, SOT-23-5, **built-in soft-start**, output discharge | see the three-way comparison below |

⚠ TPS60403 switches at **250 kHz — inside the signal band**. Mitigation is specified, not hoped
for: R76 = 4.7 Ω + 10 µF post-filter (f_c = 3.4 kHz ⇒ **37 dB** at 250 kHz) plus AD8066 PSRR.
A 20 mV_PP raw ripple therefore reaches the buffer output at ≈0.28 mV_PP ÷ PSRR — below
−100 dBFS. Cost of the filter: 62 mV of rail drop.

<!-- revised: rev.2 — new 1.8 V rail -->
### 7a. The 1.8 V rail (new in rev. 2) — why AP2127K-1.8TRG1 won

Load: 66 mA peak / 20 mA typical, ceiling specified at 100 mA (`power_budget.md` § P1V8 rail
sizing). Every candidate clears that by 3×, so **current is not the deciding spec**. The
deciding spec is the one the FPGA datasheet actually constrains: **DS117 Table 3-3 caps the
VCCIO ramp at 10 mV/µs**, so 1.8 V must take ≥ 180 µs and the regulator's own soft-start is
what sets that — an output cap cannot, because at a 500 mA current limit even 4.7 µF ramps at
106 mV/µs.

| Candidate | LCSC | Stock | $ | I_OUT | Dropout | Soft-start | Verdict |
|---|---|---|---|---|---|---|---|
| **AP2127K-1.8TRG1** (Diodes) | C151375 | 35 912 | 0.154 | 300 mA | 600 mV @300 mA | **advertised built-in** | **Selected** — the only one of the three whose parametric record claims soft-start, and the deepest stock |
| RT9013-18GB (Richtek) | C59969 | 20 557 | 0.171 | 500 mA | 400 mV @500 mA | not listed | Lost: identical footprint and vendor to U12 (a real convenience) but no stated soft-start — it would have to be measured or a 100 µF output cap added |
| TLV73318PDBVR (TI) | C882824 | 11 871 | 0.129 | 300 mA | 125 mV @300 mA | not listed | Lost: best dropout and 125 °C T_j, but dropout is irrelevant here (1.487 V of headroom) and t_on is typically ~50 µs ⇒ 36 mV/µs, 3.6× over the ramp limit |

All three are Extended tier — JLCPCB lists **no** Basic or Preferred 1.8 V LDO in SOT-23-5
(0 of 2472 hits), which matches every other active on this board. The selection rests on a
parametric claim, not a datasheet read: **confirm t_on ≥ 180 µs in phase 4** before layout.
Dropout, thermal and PSRR arithmetic: `power_budget.md` § P1V8 topology.

## 7b. Configuration memory — no part selected, and that is the answer <!-- revised: rev.3 -->

Candidates considered: **(1) an external SPI NOR config flash** (W25Q16 class) — costs 4 more
3.3 V pins (MCLK/MCS/MISO/MOSI) against a 2-pin margin, so it does not fit; **(2) host-side
configuration over the FT232H's MPSSE JTAG engine** — zero pins, but adds host firmware and an
ADBUS arbitration window; **(3) the GW1NR-9's own embedded configuration Flash.**

**Selected: (3), no part.** DS117 §2 gives GW1NR-9 4 Mbit of embedded Flash split into
configuration Flash and user Flash; §2.12.2 states the configuration data transfers from that
Flash to SRAM on every power-up — Gowin's own "instant on". UG290 Table 5-1 confirms
MODE[2:0]=000 = AUTO BOOT from embedded Flash, which is exactly what R54/R55 = 4.7 kΩ-to-GND
already select. (1) loses on pin count; (2) loses because it solves a problem the silicon does
not have. **R-13 closed; J3 is a one-time programming header, not a run-time dongle.**

## 8. Connectors and support

| Function | Selected | Note |
|---|---|---|
| Analog input ×2 | **KH-BNC50-3511** (C2837587, 6798 pcs, $0.93) — BNC female, right-angle, through-hole | `[HARD]` I1. TH is allowed by Y3 |
| Host | **TYPE-C 16PIN 2MD(073)** (C2765186, >1 M pcs, $0.07) — 16-pin USB-2.0-only Type-C | CC1/CC2 each get 5.1 kΩ to GND; no PD controller |
| USB ESD | USBLC6-2SC6 | On D+/D− at the connector |
| FT232H EEPROM | **93LC56BT-I/OT** (C190271, 11 k pcs, $0.44) | Required — it is what selects 245 sync FIFO mode and the ACBUS9 = PWREN# function |
| FPGA programming | 1×6 2.54 mm header (TCK/TDO/TDI/TMS/GND/3V3) | Gowin JTAG. Permitted by I6; saves the FT2232H upcharge |

## Cost roll-up (qty 5, JLCPCB, indicative)

| Item | Ea | Qty | Ext |
|---|---|---|---|
| GW1NR-LV9QN88PC6 | $23.32 | 1 | $23.32 |
| ADS5231IPAGT ⚠ >$25 | $31.78 | 1 | $31.78 |
| FT232HL | $9.72 | 1 | $9.72 |
| AD8066ARZ-R7 | $9.07 | 1 | $9.07 |
| THS4521IDR | $1.75 | 2 | $3.50 |
| BNC jacks | $0.93 | 2 | $1.86 |
| Regulators, switch, pump, XO, EEPROM, USB-C, ESD | — | — | ≈$2.10 |
| Passives (≈90 parts incl. 8 precision R, 8 C0G filter caps, 8 ±5 % inductors) | — | — | ≈$6–8 |
| **Board total** | | | **≈$89–91** |

Against the `[ASSUMED]` $90 target this lands on the line. The single flagged part is the
ADS5231 at $31.78. The cheapest honest lever is the second-source ADC pair (2× AD9220, −$3.40,
costs 190 mW and moves channel skew onto the PCB); the next is the FPGA at 100+ qty ($18.10).
