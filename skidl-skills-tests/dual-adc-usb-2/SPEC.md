# SPEC.md — dual_adc_usb

Autonomously derived from `dual-adc-prompt.txt` plus sound engineering defaults. No user
interview was performed (explicit override in the run instructions). Every non-trivial
choice is enumerated with options and a recommendation in **Design Decisions** below.

## Source prompt (verbatim)

> Design a dual-channel ADC board that accepts signals in the range [-10V, +10V] and
> samples them at 10 MHz with a resolution of 12 bits. The signals should enter the
> board through connectors that mate with standard oscilloscope leads. The board should
> interface to a host through a USB 2.0 port that provides power as well as transfer of
> digitized signal samples.

---

## Functional

- **Channels:** 2, independent, simultaneously sampled (see Decision D5 — two
  independent ADC ICs, not a single multiplexed ADC).
- **Input range:** ±10 V bipolar per channel, DC-coupled.
- **Sample rate:** 10 MSPS per channel, both channels run concurrently at this rate in
  burst-capture mode.
- **Resolution:** 12 bits nominal. Target ENOB ≥ 10.5 bits (realistic for a 12-bit
  10–65 MSPS pipeline ADC; SINAD-limited, not code-limited).
- **Acquisition modes (Decision D1 — throughput):**
  - **Burst/capture mode (primary):** both channels captured simultaneously at the
    full 10 MSPS / 12-bit rate into an on-board capture buffer of **32,768 samples per
    channel** (3.2768 ms of full-rate, dual-channel, gap-free capture). Buffer is then
    drained to the host over USB 2.0 High-Speed bulk, 12-bit packed (3 bytes / 2
    samples), total ≈98,304 bytes per full dual-channel buffer, at up to ≈35 MB/s
    (280 Mbps), i.e. ≈2.8 ms readout — so back-to-back capture+readout cycles run at
    roughly 1 kHz depending on host-side pacing.
  - **Continuous streaming mode (secondary):** sustained, unlimited-duration transfer
    with 25% margin under the ≈240 Mbps practical USB 2.0 HS bulk ceiling:
    - **Single channel at full 10 MSPS / 12-bit = 120 Mbps** — comfortable margin,
      recommended default continuous mode.
    - **Dual channel, decimated to ≈8 MSPS/channel combined ≈16.7 Mbps... ** i.e.
      16 MSPS combined × 12 bit = 192 Mbps — both channels active but below the
      10 MSPS spec rate.
  - Mode is host-selectable; hardware always samples both ADCs at 10 MSPS, the digital
    controller decides what subset is forwarded live vs. captured to buffer.
- **Data packing:** 12-bit packed (not 16-bit padded) — see Decision D1.
- **Analog bandwidth:** front-end −3 dB bandwidth ≥ 5 MHz (= Nyquist at 10 MSPS) with an
  anti-alias low-pass filter corner at ≈5 MHz, ≥40 dB attenuation by ≈15–20 MHz (see
  Decision D2).

## Power

- **Source:** USB 2.0 bus power only, 5 V / 500 mA max (2.5 W), per Decision D4.
  Enumerate at 100 mA, request 500 mA configuration.
- **Rails required on-board:**
  | Rail | Use | Est. current | Generation |
  |------|-----|-------------|------------|
  | +3.3 V | FPGA/CPLD, USB bridge logic | ~120 mA | LDO or buck from 5 V |
  | +5 V (clean/analog) | ADCs, op-amp positive supply | ~90 mA | LDO from USB 5 V (filtered) |
  | −5 V (analog) | Op-amp negative supply for bipolar AFE | ~30 mA | on-board charge-pump inverter (Decision D4) |
  | 1.8 V (if FPGA core needs it) | FPGA core | ~30 mA | LDO from 3.3 V |
- **Total budget:** ≈270–300 mA estimated draw, leaving ≥40% margin under the 500 mA
  ceiling.
- **Negative rail generation:** switched-capacitor charge-pump inverter IC (e.g.
  TPS60403 / LM2776 class part), −5 V from the +5 V USB rail — no isolated or external
  supply (see Decision D4).
- **Sleep/low-power mode:** not required by the prompt; USB suspend current draw target
  ≤2.5 mA per USB spec (SOFT — revisit if the host requires strict suspend compliance).

## Interface

- **Host connector:** USB 2.0 Hi-Speed, USB-C receptacle wired for USB 2.0 only (D+/D−,
  VBUS, GND; CC1/CC2 each pulled to GND through 5.1 kΩ for default 5 V/up-to-3A source
  advertisement, device only draws what it needs) — see Decision D6.
- **USB device/controller:** FTDI FT2232H (or FT232H) operating in USB2 Hi-Speed
  synchronous FIFO (245-style) mode, paired with a small CPLD/FPGA (e.g. Lattice iCE40)
  that handles ADC clocking, dual-channel capture RAM, decimation-mode muxing, and
  12-bit packing before handing packed words to the FT2232H FIFO — see Decision D3.
- **ADC interface type:** parallel CMOS (LVCMOS), not serial LVDS — see Decision D3.
- **ADC family:** 12-bit, ≥10 MSPS pipeline/SAR ADC with parallel CMOS output, single
  3.3–5 V supply (e.g. AD9226 / AD9235 / ADS822 family — exact MPN chosen at sourcing
  phase). One ADC IC per channel (simultaneous sampling, shared convert clock).
- **Input connectors:** BNC, one per channel, **1 MΩ input impedance** (standard scope
  probe compatible) — see Decision D7.
- **Front-panel/status:** power and USB-enumeration status LEDs (assumed, SOFT).

## Physical

- **Form factor:** small standalone PCB, target ≈100 mm × 70 mm (comparable to common
  USB-scope dongles), panel-mounted BNCs and USB-C on one edge.
- **Layer count:** 4-layer PCB recommended (dedicated ground/power planes) given mixed
  analog (±10 V, sub-mV noise floor at 12-bit) and 10 MHz digital switching — see
  Decision D8.
- **Construction:** SMD-first (0603/0805 passives, TSSOP/QFN ICs) for size; through-hole
  only where mechanically required (BNC jacks, USB-C if TH variant chosen).
- **Operating temperature:** 0 °C to +50 °C (indoor lab/bench instrument default, SOFT —
  no environmental spec given by user).
- **Regulatory:** CE/FCC Class B unintentional radiator compliance assumed as design
  target (SOFT — no explicit requirement given); no functional-safety or hazardous-
  location requirements assumed.
- **Input protection:** BNC center pin protected by series resistor (part of the
  attenuator) limiting fault current, plus clamp diodes/TVS to the op-amp input rails.
  Target: survive ±40 V continuous overdrive without damage; ESD per IEC 61000-4-2 at
  the BNC connector (see Decision D2).

## Production

- **Quantity:** not specified by user. Default assumed: prototype/bring-up run of
  5–10 boards (SOFT — carried forward, see handoff).
- **Cost target:** not specified. Default assumed: BOM cost ≤$150/unit at prototype
  quantity (SOFT — carried forward).
- **Manufacturer preference:** not specified. Default assumed: JLCPCB (fab + assembly),
  consistent with this pipeline's part-sourcing tooling (SOFT — carried forward).

---

## Design Decisions

### D1 — Throughput: how to fit 240 Mbps raw into USB 2.0 HS

Raw rate = 2 ch × 10 MSPS × 12 bit = 240 Mbps, which exceeds the realistically
achievable **sustained** USB 2.0 HS bulk throughput (~200–250 Mbps of the 480 Mbps
theoretical signaling rate).

| Option | Pros | Cons |
|---|---|---|
| On-board capture RAM/FIFO + burst readout | Full-rate, full-fidelity, dual-simultaneous-channel capture (matches oscilloscope use case); readout happens at a slower, comfortably-within-budget pace | Not continuous — limited by buffer depth (here 32k samples/ch ≈ 3.3 ms) |
| Decimation/downsampling for continuous streaming | Simple, true continuous streaming, no buffer-empty gaps | Reduces effective sample rate below the 10 MSPS spec while streaming continuously |
| Single-channel-at-full-rate mode | Full 10 MSPS/12-bit on one channel fits easily (120 Mbps) | Only one channel live at a time in continuous mode |
| Data packing (12-bit packed vs. 16-bit padded) | Free 25% bandwidth reduction, no fidelity loss | Slightly more complex packing/unpacking logic on both ends |
| Lossless compression | Could reduce bandwidth further | Compression ratio on real (noisy) analog signals is close to 1 — unreliable win; adds latency and complexity for uncertain benefit |

**RECOMMENDED (adopted):** Combine capture-RAM burst mode as the primary acquisition
mode (mirrors how USB oscilloscopes work) with 12-bit packing always on, plus a
continuous-streaming secondary mode that trades channel count/rate for sustained
operation. This is the only combination that delivers true dual-simultaneous-channel
10 MSPS/12-bit capture (a hard spec requirement) while still offering a continuous-data
option. Lossless compression is rejected as unreliable for arbitrary analog input.
**Resulting hard numbers** are stated in Functional above (32,768 samples/ch burst
depth; 120 Mbps single-channel or ~192 Mbps decimated-dual-channel continuous).

### D2 — Analog front end for ±10 V into the ADC

±10 V bipolar must be attenuated and level-shifted into the ADC's unipolar input range
(assume ~0–2 V, common-mode ~1 V, typical of the recommended ADC family) with enough
bandwidth for 10 MSPS.

| Option | Pros | Cons |
|---|---|---|
| Passive resistive divider only | Simplest, cheapest | No level shift (still bipolar), poor ADC-driving impedance, no anti-alias filtering |
| Divider + single-ended op-amp level-shifter/buffer + anti-alias filter | Moderate complexity, well-understood, single-ended matches parallel-CMOS ADC's single-ended input | Op-amp adds noise/offset error budget to manage |
| Divider + fully-differential ADC driver (e.g. THS4521-class) + anti-alias filter | Best noise/distortion performance, ideal if ADC has differential input | Higher cost/complexity; recommended ADC family here is single-ended, so this is architecture-dependent |

**RECOMMENDED (adopted):** ~11:1 resistive attenuator (±10 V → ±0.91 V) into a
single-supply op-amp stage that both level-shifts to the ADC's common-mode input and
provides a 2nd/3rd-order anti-alias low-pass (Sallen-Key), driving the ADC single-ended
input. **Required analog bandwidth: ≥5 MHz** (Nyquist at 10 MSPS). **Anti-alias filter
corner: ≈5 MHz, −3 dB**, with ≥40 dB attenuation by 15–20 MHz to suppress
alias-folding of out-of-band noise/interference. If sourcing later prefers a
differential-input ADC, upgrade to the fully-differential driver option — flagged for
the architect.

### D3 — Digital controller family / ADC interface

| Option | Pros | Cons |
|---|---|---|
| FT2232H/FT232H USB2-HS sync-FIFO bridge + small CPLD/FPGA for capture logic | Lowest USB engineering risk (FTDI handles PHY + drivers, well-documented D2XX/VCP), FIFO mode throughput (up to 320 Mbps) matches the budget exactly, FPGA/CPLD only does simple capture/pack logic | Two-chip solution (FPGA + USB bridge) |
| MCU with native USB2 HS OTG + ULPI PHY (e.g. STM32H7) doing DMA capture from ADC parallel bus | Single-chip control+USB, familiar firmware toolchain | Custom USB device firmware/DMA pipeline is higher engineering risk to hit sustained HS throughput reliably |
| FPGA with its own USB2 HS PHY + soft/hard USB core | Maximum flexibility, single reprogrammable device | Significant added engineering effort to implement/validate a USB2 HS device core in fabric |

**RECOMMENDED (adopted):** small CPLD/FPGA (e.g. Lattice iCE40) for ADC convert-clock
generation, dual-channel simultaneous capture into block RAM, mode muxing
(burst/continuous), and 12-bit packing — paired with an **FT2232H in USB2 Hi-Speed
synchronous FIFO mode** for the actual USB link. **ADC interface: parallel CMOS**, not
serial LVDS — at only 10 MSPS, parallel CMOS avoids the added deserializer complexity
that LVDS is meant to solve at much higher sample rates, and keeps FPGA pin count
modest for a 2-channel, 12-bit design.

### D4 — Power budget / negative rail generation

USB bus power is 5 V/500 mA (2.5 W) max, and the total design must fit inside that with
margin; the ±10 V AFE requires a negative supply rail that isn't available from USB.

| Option (negative rail) | Pros | Cons |
|---|---|---|
| Switched-capacitor charge-pump inverter (e.g. TPS60403/LM2776) | Simple, cheap, small, adequate current (tens of mA) for op-amp bias, generates −5 V directly from +5 V USB rail | Some switching noise (manageable with filtering, non-issue for op-amp supply rail) |
| Inductor-based inverting buck-boost | Can supply more current, potentially lower ripple with good design | More complex magnetics, higher cost/area, unnecessary for the low current the AFE op-amps need |
| Isolated DC-DC converter | Provides galvanic isolation | Overkill — no isolation requirement stated, adds cost/size for no benefit |
| External wall-wart / bench supply for negative rail | Avoids on-board generation entirely | Violates the prompt's requirement that USB provides power |

**RECOMMENDED (adopted):** on-board switched-capacitor charge-pump inverter IC,
generating −5 V from the +5 V USB rail, feeding the AFE op-amp negative supply.
Estimated total board current ≈270–300 mA against the 500 mA ceiling (see Power table
above) — comfortable margin retained for BOM/part-selection variance in later phases.

### D5 — Simultaneous vs. multiplexed sampling

| Option | Pros | Cons |
|---|---|---|
| One ADC per channel (2× ADC ICs), shared convert clock — true simultaneous sampling | True time-coincident samples across both channels (matches how a 2-channel scope is expected to behave), each channel gets full 10 MSPS independently | 2× ADC cost/board area vs. one ADC |
| Single ADC + analog mux, time-interleaved between channels | Half the ADC cost | Channels are NOT time-coincident (phase-skewed by the mux switching), and to hit 10 MSPS *per channel* the ADC itself must run at ≥20 MSPS — pushes ADC selection, doesn't reduce total throughput problem, and probably the bigger issue for an instrument marketed as "dual-channel" |

**RECOMMENDED (adopted):** two independent ADC ICs (one per channel), same convert
clock, for true simultaneous 10 MSPS/channel sampling. This is what a user attaching
"standard oscilloscope leads" to look at two signals together would expect.

### D6 — Host connector

| Option | Pros | Cons |
|---|---|---|
| USB Type-B | Robust, traditional for bench instruments, panel-mountable | Larger, connector style increasingly uncommon on new host cables |
| USB Micro-B | Compact | Mechanically fragile, being phased out industry-wide |
| USB-C (USB 2.0 signaling only) | Modern standard, robust/reversible connector, matches "USB 2.0 port" requirement (SuperSpeed lanes simply unused) | Needs CC1/CC2 5.1 kΩ pull-downs for correct power-source negotiation |

**RECOMMENDED (adopted):** USB-C receptacle, wired for USB 2.0 only (D+/D−, VBUS, GND,
CC pull-downs) — modern connector standard without requiring SuperSpeed PHY.

### D7 — Input connector / impedance

Prompt requires "connectors that mate with standard oscilloscope leads" — confirmed as
**BNC**.

| Option (impedance) | Pros | Cons |
|---|---|---|
| 1 MΩ | Standard for general-purpose scope probes (1x/10x passive probes), minimal loading of the circuit under test | Bandwidth more limited by probe/cable capacitance at high frequency |
| 50 Ω | Correct for RF/matched transmission-line measurements, no reflections at high frequency | Heavily loads the source (draws real current), requires a 50 Ω-source signal — not compatible with typical passive scope probes |

**RECOMMENDED (adopted):** 1 MΩ input impedance — matches "standard oscilloscope leads"
(implies standard passive probes, not RF probes), and the ±10 V general-signal range is
consistent with general-purpose bench measurement rather than RF work.

### D8 — Layer count / board construction

| Option | Pros | Cons |
|---|---|---|
| 2-layer | Cheapest, simplest fab | Poor ground return control for the ±10 V analog section next to 10 MHz digital switching — high risk of noise coupling into 12-bit ADC codes |
| 4-layer (signal-GND-PWR-signal) | Dedicated ground/power planes isolate analog and digital, standard practice for mixed-signal ≥10-bit ADC boards | Modest cost increase over 2-layer |

**RECOMMENDED (adopted):** 4-layer, with the analog front end and digital
FPGA/USB-bridge sections laid out as separate zones over a partitioned or fully split
ground plane strategy to protect ENOB.

---
