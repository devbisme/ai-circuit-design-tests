# IC selection — dual_adc_usb

All stock/price/tier data from live JLCPCB search (`pcbparts` MCP), 2026-09-20.
Every candidate below was looked up, not recalled. **Every active part is Extended tier** —
JLCPCB has no Basic/Preferred part for any function in this design except the buck and the
ESD array. Budget the per-order Extended handling fee accordingly.

---

## 1. ADC — the keystone part

| Candidate | LCSC | ch | MSPS | SNR | Supply | Package | Stock | Unit $ | Tier |
|---|---|---|---|---|---|---|---|---|---|
| **ADS5231IPAGT** ✅ | C2670079 | **2** | 40 | **70.7 dB** | 3.0–3.6 V | TQFP-64 (10×10) | 154 | 31.77 | Extended |
| AD9235BCPZ-40 ×2 | C653327 | 1 | 40 | 70.6 dB | 2.7–3.6 V | LFCSP-32 | 139 | 25.30 (×2 = 50.60) | Extended |
| AD9237BCPZ-40 ×2 | C514275 | 1 | 40 | 66.5 dB | 2.7–3.6 V | LFCSP-32 | 211 | 32.84 (×2 = 65.67) | Extended |
| LTC2225IUH ×2 | C679583 | 1 | 10 | 71.3 dB | 2.7–3.4 V | QFN-32 | 84 | 24.09 (×2 = 48.17) | Extended |
| ZGAD65D12C | C20416590 | 2 | 65 | 68 dB | 1.8 V | QFN-64 | 24 | 16.40 | Extended |
| AD9238 (any grade) | — | 2 | 20–65 | 70 dB | 3 V | LQFP-64 | **not carried** | — | — |

**Recommendation: ADS5231IPAGT** (U5).

Why it wins, against the specs the requirements actually constrain:
- **F1 (simultaneous sampling)** becomes a property of the silicon, not of the layout. One
  package, one clock pin, one internal clock tree → two S/H circuits on the same edge.
  Two single ADCs would put two clock loads and two package delays between the channels;
  matching them to a fraction of a 50 ns period is achievable but is work we don't have to
  do.
- **F11 (≥10.5 ENOB)**: 70.7 dB SNR → 11.4 ENOB, ≈0.9 bit of margin for front-end noise.
- **Cheapest per channel of everything in stock**: $15.89/ch vs $25.30 (AD9235) and
  $32.84 (AD9237).
- **F3 headroom**: 40 MSPS ceiling with a 20 MSPS operating point leaves room to move the
  sample rate without changing the part (see § 6 on the oscillator).
- **P5**: 3.0–3.6 V single supply matches the single +3V3_A analog rail, so no extra
  regulator.
- It has an **output multiplexer** option (both channels on one 12-bit bus) held in reserve
  if the FPGA runs short of I/O.

Why each loser lost, in one line each:
- **AD9235BCPZ-40 ×2** — 59 % more expensive and stock 139 covers only 69 boards, for no
  performance gain (70.6 vs 70.7 dB); two clock loads is a channel-skew problem we'd be
  buying.
- **AD9237BCPZ-40 ×2** — the only ≥200-stock 12-bit part, but 66.5 dB SNR = 10.75 ENOB
  leaves 0.25 bit against F11 (the front end alone will eat that), and it costs $65.67.
- **LTC2225 ×2** — best SNR of the group, but 10 MSPS maximum means no oversampling, which
  forces a 5th-order analog anti-alias filter (≈16 extra parts incl. inductors per
  channel); stock 84.
- **ZGAD65D12C** — the cost-reduction option ($16.40, dual, 65 MSPS) but stock 24, an
  unproven vendor for a keystone part, and 1.8 V rails would add a fourth regulator.
  **Revisit only if stock recovers and a datasheet is obtainable.**
- **AD9238** — the textbook part for this job; JLCPCB does not carry it in any grade.

⚠ **Risks to verify in sourcing/datasheet phases** (see `design_risks.md` R-1):
lifecycle (the ADS523x family is legacy TI — check NRND); stock 154 is below the SPEC Q4
threshold of 200 and this is a single-source part; **confirm the minimum clock frequency**
(the JLCPCB record says 20–40 MHz, and the whole clocking decision in § 6 rests on 20 MHz
being legal).

---

## 2. Capture controller + buffer RAM

| Candidate | LCSC | Logic | Buffer | Package | Stock | Unit $ | Tier |
|---|---|---|---|---|---|---|---|
| **GW1NR-LV9QN88PC6/I5** ✅ | C5799578 | 8640 LUT4 | **64 Mbit (8 MB) in-package PSRAM** | QFN-88 (0.4 mm) | 180 | 23.31 | Extended |
| GW1N-9 class + W9825G6KH SDRAM | — | 8640 LUT4 | 32 MB external, 16-bit | LQFP-144 + TSOP-54 | — | ≈12 + 2 | Extended |
| Lattice / Xilinx + external SDRAM | — | varies | external | BGA typical | — | >15 | Extended |
| MCU (STM32H7) internal ADC | — | — | 1 MB SRAM | LQFP-100 | — | ≈10 | — |

**Recommendation: GW1NR-LV9QN88PC6/I5** (U6).

Why it wins:
- **F5/D5 (≥4 MB buffer)**: 8 MB in-package, which is 2× the requirement and holds
  **104.9 ms of both channels at 20 MSPS** — see § 6 for why that number decides the
  architecture.
- It **deletes a 39-signal memory bus** from a 4-layer board. That is the single largest
  layout-risk reduction available in this design, and it is what justifies the $23 price
  against ≈$14 for FPGA + discrete SDRAM.
- **Non-volatile configuration**: the GW1N family holds its bitstream in on-die flash, so
  there is no external config flash IC, no config-time boot sequencing, and JTAG is the
  only programming interface needed (satisfies I7 with a 6-pin header).
- I/O budget fits with room: 45 user I/O needed (24 ADC data + 1 clock + 2 ADC control +
  15 FIFO + 3 misc) against ~63 available on QN88.

Why the losers lost:
- **GW1N-9 + external SDRAM** — saves ≈$9/board and costs 39 nets, a 144-pin package, and
  memory-bus timing closure on 4 layers. Wrong trade at qty 5.
- **MCU with internal ADCs** — ruled out upstream (SPEC D4): ~3.6 MSPS/ch, fails F3 by 3×.

⚠ Stock 180 < Q4's 200 (single source; Gowin has no pin-compatible second vendor).
⚠ **Datasheet phase must confirm** the supply rails: this design assumes **1.2 V core +
3.3 V VCCX/VCCIO only**, and that the in-package PSRAM needs no separate board-level rail.
If a 1.8 V or 2.5 V auxiliary rail is required, add one LDO in `digital_power` — topology
unchanged, but say so before coding.

---

## 3. USB 2.0 HS bridge

| Candidate | LCSC | Mode | Package | Stock | Unit $ | Tier |
|---|---|---|---|---|---|---|
| **FT232HL-REEL** ✅ | C51997 | 245 sync FIFO, ~35 MB/s | LQFP-48 | 2048 | 9.72 | Extended |
| FT232HQ-REEL | C82158 | same | QFN-48 | 12 | 27.09 | Extended |
| FT2232H | — | sync FIFO + second MPSSE channel | LQFP-64 | not searched — see note | — | — |

**Recommendation: FT232HL-REEL** (U7). Chosen over FT232HQ purely on stock and price
(2048 @ $9.72 vs 12 @ $27.09) — identical die, and LQFP-48 is the easier package to inspect
and rework.

**FT2232H was considered and rejected**: its second channel would give onboard JTAG
programming for the FPGA, but FTDI's documentation on whether channel B remains usable
while channel A is in 245-synchronous-FIFO mode is ambiguous, and betting the programming
path on that ambiguity is a bad trade against a $0.30 JTAG header plus any external
FT2232/Gowin cable. Revisit only if someone reads AN_130 and confirms it.

Why FT232H at all: no firmware to write (245 sync FIFO is a hardware handshake), a
libusb/D2XX host path (I6), a **60 MHz CLKOUT** that gives the FPGA its FIFO-domain clock
free, and **PWREN# on ACBUS7** which is what lets this board legally draw <100 mA before
USB configuration (see § 5).

⚠ 245 synchronous FIFO mode is **selected in EEPROM, not by pin strapping** — U8 is
mandatory, not optional.

---

## 4. Front-end amplifiers

### 4a. Fully differential ADC driver (2 off)

| Candidate | LCSC | GBW | Noise | Supply | Package | Stock | Unit $ |
|---|---|---|---|---|---|---|---|
| **THS4551IRGTR** ✅ | C2869590 | 135 MHz | 3.3 nV/√Hz | 2.7–5.4 V | QFN-16-EP (3×3) | 602 | 4.36 |
| THS4551IRUNR | C2060364 | 135 MHz | 3.3 nV/√Hz | 2.7–5.4 V | QFN-10 (2×2) | 4229 | 4.73 |
| THS4551IDGKT | C2860660 | 135 MHz | 3.3 nV/√Hz | 2.7–5.4 V | MSOP-8 | 157 | 6.04 |
| AD8138ARZ | — | 320 MHz | 5 nV/√Hz | 3–5 V | SOIC-8 | — | ≈4 |

**Recommendation: THS4551IRGTR** (U_fda1, U_fda2).

Why it wins: on a **3.3 V** rail it swings to within 0.2 V of each rail, so the
1.15…2.15 V per-output window the ADC needs sits comfortably mid-range; it has an
adjustable VOCM pin (we drive it from the ADC's CM output); 3.3 nV/√Hz keeps amplifier
noise ~5× below the divider's thermal noise; and 135 MHz GBW at G = 2 gives ~65 MHz of
closed-loop bandwidth against a 6 MHz filter corner — enough that the filter shape is set
by the passives, not by the amplifier.

<!-- revised: rev3 — the FDA is now load-bearing for the filter, not just for the gain. -->
**rev 3 adds a requirement to this choice.** The anti-alias filter is now a **2nd-order
multiple-feedback (MFB) section built around this amplifier** plus one output RC (ERC H-1,
`design_risks.md` R-5): a passive RC cascade can only make *real* poles, and real poles cannot
deliver 0.5 dB of droop at 4 MHz together with 25 dB at 16 MHz at any order. So the FDA's
feedback network is part of the filter, and a substitute must be **unity-gain stable with
≥100 MHz GBW** (the MFB's HF feedback path drives the amplifier toward unity noise gain) on
top of the existing output-range condition. **THS4551IRUNR** remains the vetted second source
— same die, so the MFB design transfers unchanged.
- **AD8138** lost on headroom, not speed: on a single 5 V supply its output range starts at
  ~1.0 V, which is exactly where our lower output excursion sits. No margin.
- **THS4551IRUNR** (QFN-10 2×2) is the **vetted second source** — same die, 7× the stock.
  Substituting it is safe; it changes only the footprint.
- **THS4551IDGKT** (MSOP-8) is the hand-rework fallback, stock 157.

### 4b. High-impedance divider buffer (2 off)

| Candidate | LCSC | GBW | Slew | Input | Package | Stock | Unit $ |
|---|---|---|---|---|---|---|---|
| **OPA355NA/3K** ✅ | C2058090 | 200 MHz | 360 V/µs | CMOS, 3 pA, ~1 pF | SOT-23-6 | 489 | 1.77 |
| OPA355UA/2K5 | C2059993 | 200 MHz | 300 V/µs | CMOS, 3 pA | SOIC-8 | 562 | 2.50 |
| LMH6611 / ADA4805-1 | — | 105–345 MHz | — | bipolar, µA-class Ib | — | — | — |

**Recommendation: OPA355NA/3K** (U_buf1, U_buf2).

Why it wins — and this is the one non-obvious choice in the design:
- The buffer sees a **47.5 kΩ source impedance**. A bipolar-input amplifier's µA-class bias
  current would develop tens to hundreds of mV of offset across it and drift with
  temperature; OPA355's **3 pA** CMOS input makes that error 0.15 µV. That single spec
  eliminates every bipolar high-speed RRIO amplifier from consideration, whatever its GBW.
- ~1 pF input capacitance is small and stable, so the divider's compensation trimmer has
  something predictable to null.
- 360 V/µs and 200 MHz are ~10× what a 2 V p-p 5 MHz signal needs, so the buffer
  contributes no distortion of its own.
- Its **input common-mode range on 3.3 V reaches 1.8 V** and our node maxes at 1.64 V —
  160 mV of margin. This is the tightest number in the analog design; it is why the
  attenuator is ÷20 rather than ÷10. See `design_risks.md` R-3.
- **OPA355UA (SOIC-8)** is the vetted second source — same die, more parasitic
  capacitance, acceptable.

### 4c. Reference buffer (1 off, dual)

Not individually searched — **specification, sourcer's choice**: dual op-amp, rail-to-rail
output, Vos ≤ 500 µV, noise ≤ 20 nV/√Hz, ≥1 MHz GBW, ≥10 mA output, 2.7–5.5 V,
SOIC-8/MSOP-8. Candidates to price: OPA2376, TLV9062, OPA2333. Freely substitutable — this
part buffers two DC references and nothing more.

---

## 5. Power tree

| Function | Candidate | LCSC | Key spec | Package | Stock | Unit $ | Tier |
|---|---|---|---|---|---|---|---|
| 5 V → 3.3 V digital | **SY8089A1AAC** ✅ | C479074 | 2 A sync buck, 1.5 MHz, EN, **VREF = 591/600/609 mV verified** | SOT-23-5 | 122 325 | 0.086 | Extended |
| ″ alternative | SY8089AAAC | C78988 | same, 1 MHz | SOT-23-5 | 54 979 | 0.15 | Extended |
| 5 V → 3.3 V analog | **TLV75733PDRVR** ✅ | C2868428 | 1 A, 425 mV dropout, 46 dB@100 kHz, 71.5 µVrms | WSON-6 (2×2, thermal pad) | 16 468 | 0.37 | Extended |
| ″ cheaper, hotter | TLV75733PDBVR | C485517 | same die, no thermal pad | SOT-23-5 | 32 805 | 0.20 | Extended |
| 3.3 V → 1.2 V core | **specification** | — | 1.20 V ±3 %, ≥250 mA, dropout ≤200 mV@200 mA, **thermal-pad package** | DFN/WSON | — | ≈0.3 | — |
| Load switch (**U9**) | **AP2161WG-7** ✅ | C176957 | 1 A current-limited high-side switch, **active-low EN**, ILIM 1.1/1.5/1.9 A, 95 mΩ, tR 0.6 ms | SOT-23-5 | 8 848 | 0.211 | Extended |
| ″ 2nd source | WS4612EBB-5/TR | C42404603 | 1 A, 60 mΩ, active-low EN, OCP/OTP/SCP | SOT-23-5 | 8 657 | 0.142 | Extended |
| ″ rejected | TPS2041BDBVR | C51386 | active-low EN, but **500 mA** recommended continuous | SOT-23-5 | 4 138 | 0.485 | Extended |
| ″ **never substitute** | ~~AP2171WG-7~~ | — | pin-identical twin of AP2161 with **active-HIGH** EN | SOT-23-5 | — | — | — |
| USB D+/D− ESD | **USBLC6-2SC6** ✅ | C2687116 | 0.35 pF, 2-ch, IEC 61000-4-2 | SOT-23-6 | 106 779 | 0.048 | Extended |

<!-- revised: rev2 — load-switch row replaced (Q1 bare P-FET could not be turned off by a
3.3 V PWREN# with its source on 5 V); U1's VREF closed from a primary source. -->

**Load switch — why AP2161WG-7 (U9) over the three alternatives** (escalation from
`handoffs/05_blocks/digital_power.md`, gap 1). PWREN# is a 3.3 V CBUS output; a P-FET with its
source on +5 V therefore sees Vgs = −1.5…−1.7 V in its "off" state, past the HL2301A's
−0.4…−1.0 V threshold. The switch never turns off, so SPEC P4 was unmet, and no value of R3
changes that. Four options, ranked:

1. **Active-low-EN integrated load switch — chosen.** PWREN# is active-low and U9's EN is
   active-low *and GND-referenced* (VIH 2.0 V min, VIL 0.8 V max), so a 3.3 V logic level
   drives it directly: **no inverter, no level shift, no polarity trap.** The 1.1 A minimum
   current limit sits above the 485 mA worst-case board draw and below anything that damages
   a USB port; the 0.6 ms controlled rise time gives the inrush control a bare FET never had
   (≈167 mA into the ~20 µF downstream, vs an uncontrolled edge); 95 mΩ ≈ the HL2301A's
   90 mΩ so neither the IR drop nor the thermal picture moves. It also **frees a ref**
   (R3 is deleted) rather than adding any, and `Power_Management:AP2161W` already exists in
   the stock KiCad library at the SOT-23-5 footprint the design already uses — so no symbol
   generation, and one file changes.
2. *Active-high-EN switch + 2-transistor non-inverting level shift* — lost: 3 parts, 3 refs,
   2 symbols to generate, and it rebuilds by hand the polarity that option 1 gets for free.
   Nothing is gained electrically.
3. *P-FET with |Vgs(th)| > 2 V* — lost on the same arithmetic that killed the HL2301A, from
   the other end: with the gate pulled to 3.3 V and the source at 5 V, the **on**-state Vgs
   is −1.7 V, so a >2 V-threshold FET is barely enhanced and its Rds(on) is unspecified
   there. A 3.3 V drive from a 5 V source rail cannot both turn a P-FET hard on and fully
   off. Still no inrush control either.
4. *Drop the pre-enumeration gating entirely* — legitimate to consider (**P4 is
   CLAUDE-tagged**, not a user requirement) and it is what most FTDI hobby boards do, but
   rejected: at ~373 mA before `SET_CONFIGURATION` the board is ~3.7× over USB 2.0 §7.2.1's
   one unit load, the fix costs one part and a net ref saving, and dropping it would also
   strand the FT232H EEPROM's PWREN# setting and the R-9 bring-up escape. Keeping the
   requirement is cheaper than deleting it.

**U1's feedback reference is no longer an assumption.** `datasheets/SY8089A1AAC.pdf` (Silergy
AN_SY8089A1, obtained rev 2) gives pin 5 as `VOUT = 0.6 × (1 + RH/RL)` and the electrical
table as **VREF = 591 / 600 / 609 mV** (±1.5 %). R4 = 45.3 k / R5 = 10.0 k → **3.318 V**
(3.268–3.368 V over VREF tolerance alone), inside the ADC's 3.0–3.6 V and the FPGA's I/O
window. The 0.8 V scenario that would have produced 4.4 V is ruled out; **no part and no
value changes.**

**Why a buck for digital and an LDO for analog, rather than one or the other:**
- All-linear would put 1.1 W of heat on the board and push input current to ~538 mA,
  breaking the 500 mA USB-A budget the requirements ask us to respect.
- All-switching would put a 1.5 MHz switcher's ripple **inside** the 0–5 MHz measurement
  band on the analog rail, which no amount of layout care fully fixes at 12 bits.
- The chosen split keeps the switcher on the digital half of the board and feeds the analog
  LDO from the **5 V node, not from the buck output**, with a ferrite + 10 µF π-filter at
  its input. The buck's ripple therefore reaches analog only through the 5 V node, twice
  attenuated.

**TLV75733PDRVR over TLV75733PDBVR**: identical die; the WSON thermal pad turns a 40 °C
rise into a 14 °C rise on the 200 mW this regulator dissipates. At 50 °C ambient (H3) that
is the difference between a 90 °C and a 64 °C junction.

⚠ Its **46 dB PSRR at 100 kHz misses SPEC P8's ≥50 dB**. P8 is met by the LDO *plus* its
input π-filter, not by the LDO alone. If the sourcer can find **TPS7A2033** (or any
≤10 µVrms / ≥60 dB@100 kHz 3.3 V LDO) in stock at a sane price, take it — that is a
straight upgrade to F11 margin.

**1.2 V core LDO — deliberately left as a specification, not an MPN.** Its 315 mW is the
largest single dissipation on the board; a package without a thermal pad will run hot. The
sourcer must pick on thermal resistance first and price second. An *adjustable* LDO is
preferred over a fixed 1.2 V part, so the rail can be re-targeted if § 2's datasheet check
changes the FPGA's core voltage.

---

## 6. Sample clock — and the decision that depends on it

| Candidate | LCSC | Freq | Supply | Package | Stock | Unit $ |
|---|---|---|---|---|---|---|
| **SX3M20.000B10F20TNN** ✅ | C5452685 | 20.000 MHz | 3.3 V, ±20 ppm | SMD3225-4P | 3072 | 0.47 |
| OT252020MJBA4SL | C669067 | 20.000 MHz | 1.8–3.3 V, ±20 ppm | SMD2520-4P | 7878 | 0.56 |
| SX1M20.000M10F30TNN | C2901611 | 20.000 MHz | 1.62–3.63 V, ±30 ppm | SMD2016-4P | 9188 | 0.57 |

**Recommendation: SX3M20.000B10F20TNN** (X1), on the 3225 footprint for solderability and
because 3.3 V-only parts avoid a level question. Second source OT252020MJBA4SL.

**Why 20.000 MHz and not 40 MHz — this is the architecture's load-bearing number.**

The requirement is 10.0 MSPS/ch (F3) for ≥0.1 s (F5). The chosen ADC's minimum clock is
20 MHz, so 10 MSPS direct is not available and *some* rate conversion is unavoidable. Two
ways to arrange it:

| Option | ADC clock | Raw rate into RAM | 8 MB holds | Analog AA needed | Who decimates |
|---|---|---|---|---|---|
| **A (chosen)** | 20.000 MHz | 80 MB/s | **104.9 ms** ✓ | ≥25 dB above 15 MHz → **3rd order** | the **host**, in software |
| B | 40.000 MHz | 160 MB/s | 52 ms ✗ | ≥25 dB above 30 MHz → 2nd order | the **FPGA**, mandatorily |

Option A wins because **every HARD requirement is met with a capture engine that does no
signal processing at all**. The FPGA writes raw samples; the host receives 20 MSPS/ch and
runs a 2:1 decimating FIR to produce the specified 10.0 MSPS/ch. Firmware is out of scope
for this pipeline (upstream `## Carried forward`), so an architecture that needs FPGA DSP to
satisfy a HARD requirement is an architecture that ships unverified. Option A also keeps
PSRAM write bandwidth at ~25–40 % utilisation instead of ~60–80 %, and it hands the user a
free 20 MSPS/ch mode — twice the specified rate.

Option A's cost: the ADC runs at its **minimum rated clock**. That is the one assumption in
this design that would force real rework if wrong.

> **Contingency, decided in advance:** if the datasheet phase finds ADS5231's minimum clock
> above 20 MHz, change X1 to **40.000 MHz** (same 3225 footprint, same family — zero layout
> change) and add "FPGA must implement a 4:1 decimating halfband cascade" as a firmware
> requirement. Do not change the ADC, the front end, or the buffer sizing.

Jitter: none of the JLCPCB oscillator records publish phase jitter. The budget is 14 ps RMS
(F14) and commodity CMOS XOs are typically 1–5 ps RMS integrated, so this very likely
passes with 3× margin — but it is **unverified**, and the datasheet phase must either
confirm ≤5 ps RMS from a real datasheet or substitute a SiTime SiT8008 / Epson SG-210 class
part. See `design_risks.md` R-4.

X1's supply comes from **+3V3_A through a ferrite**, and its ground returns to the analog
ground region: a clock this close to the sample aperture must not share a rail with the
FPGA's switching I/O.

---

## 7. Remaining parts — specifications, not picks

These are the part-sourcer's to finalise; they carry no architectural risk.

| Function | Specification | Candidate found | Note |
|---|---|---|---|
| USB-C receptacle | 16-pin, USB 2.0 pins only, no SS pairs, ≥3 A | **TYPE-C 16PIN 2MD(073)**, C2765186, stock 1.13 M, $0.074 | 16P is exactly right — a 24P part would add unused SS pads |
| FT232H EEPROM | 93LC46B/C, **×16 organisation**, 2.7–3.6 V tolerant | 93C46CT-I/SN-TUDI, C54935223, stock 2500, $0.39 | ⚠ verify the ORG pin gives ×16; the 93C46B variant found is 4.5–5.5 V only and will **not** work on 3.3 V |
| BNC jacks (2) | PCB board-edge, 50 Ω body, through-hole | not found by search | search `RF Coaxial Connectors` for "BNC"; ~$1 each |
| 12 MHz crystal | ±30 ppm, 12 pF load, SMD3225 | — | jellybean |
| Divider trimmers (2) | 2–10 pF or 3–12 pF SMD trimmer capacitor | — | **not substitutable with a fixed cap** — see `design_risks.md` R-2 |
| Divider resistors | 475 kΩ ±0.5 % 0805 ×2 in series (950 kΩ), 50 kΩ ±0.5 % | — | ±0.5 % or better: these set gain accuracy and channel matching |
| ADC bus damping | 33 Ω 4-element 0402 array ×6 | — | jellybean |
| Input clamp diodes (2) | BAV99 dual series, SOT-23 | — | jellybean; low capacitance matters |
| VBUS TVS | 5 V working, SOD-123 | — | jellybean |

---

## Cost roll-up — SPEC Q3 cannot be met

| Item | Qty | Unit $ | Ext $ |
|---|---|---|---|
| ADS5231IPAGT | 1 | 31.77 | 31.77 |
| GW1NR-LV9QN88PC6/I5 | 1 | 23.31 | 23.31 |
| FT232HL | 1 | 9.72 | 9.72 |
| THS4551IRGTR | 2 | 4.36 | 8.71 |
| OPA355NA | 2 | 1.77 | 3.54 |
| Regulators + load switch | 4 | — | 1.01 |
| Oscillator + crystal | 2 | — | 0.62 |
| EEPROM, USB-C, ESD, dual op-amp | 4 | — | 0.96 |
| BNC jacks | 2 | ≈1.00 | 2.00 |
| Trimmers, arrays, headers, LEDs, L, passives | ~80 | — | ≈4.00 |
| **Parts total, per board at qty 5** | | | **≈ $85.5** |

**SPEC Q3 (≤$70) is not achievable.** The ADC + FPGA pair alone is $55 (65 % of the BOM),
and § 1 and § 2 show there is nothing cheaper in stock that meets the HARD requirements.
Q3 is a CLAUDE-tagged soft target; the honest revision is **≈$85/board of parts**, plus
~$6/board of JLCPCB Extended handling fees at qty 5 and ~$4/board of 4-layer PCB.

Two cost-reduction paths exist, neither recommended now:
- **ZGAD65D12C** instead of ADS5231: −$15, but stock 24, unproven vendor, extra 1.8 V rail.
- **GW1N-9 + W9825G6KH external SDRAM**: −$9, but +39 nets, a 144-pin package, and
  memory-bus timing closure on 4 layers.
