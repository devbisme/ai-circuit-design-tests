# SPEC — dual_adc_usb

Dual-channel 12-bit / 10 MSPS oscilloscope-style digitizer, USB 2.0 bus-powered.

Provenance tags: **[USER]** = stated in `dual-adc-prompt.txt`; **[DRIVER]** = decided by the
pipeline driver in autonomous mode (user instructed: "list all the options and then select
the one you recommend... do not pause"). Every [DRIVER] item lists the options considered.

---

## 1. Functional

| ID | Requirement | Value | Type | Src |
|---|---|---|---|---|
| F1 | Analog input channels | 2, simultaneously sampled | HARD | [USER] ch. count / [DRIVER] simultaneity |
| F2 | Full-scale input range | ±10 V (20 Vpp) at the BNC, 1× probe | HARD | [USER] |
| F3 | Sample rate | 10 MSPS per channel, continuous | HARD | [USER] |
| F4 | Resolution | 12 bits | HARD | [USER] |
| F5 | Coupling | DC-coupled | HARD | [DRIVER] |
| F6 | Usable analog bandwidth | DC – 4 MHz (−3 dB) | HARD | [DRIVER] |
| F7 | Anti-alias filtering | ≥30 dB at 10 MHz, ≥50 dB at 20 MHz (4th-order class) | HARD | [DRIVER] |
| F8 | DC gain accuracy | ±2 % FS after one-time host-side calibration | SOFT | [DRIVER] |
| F9 | Input overload survival | ±50 V DC continuous, no damage | SOFT | [DRIVER] |
| F10 | Channel-to-channel skew | ≤ 1 sample period (100 ns) | SOFT | [DRIVER] |
| F11 | SNR / ENOB | ≥ 60 dB SNR, ≥ 9.5 ENOB at 1 MHz | SOFT | [DRIVER] |
| F12 | Capture modes | (a) triggered burst into on-board buffer at full rate, guaranteed lossless; (b) continuous streaming, best-effort with an explicit overrun flag in the data stream | HARD | [DRIVER] |
| F13 | Trigger | Host-armed software trigger + hardware level/edge trigger on either channel | SOFT | [DRIVER] |

**F1 simultaneity** — options: (a) one ADC + 2:1 mux at 20 MSPS, (b) dual/two-channel ADC
sampling both channels on the same clock edge, (c) two independent ADCs on a shared clock.
Chose (b)/(c): a mux introduces 50 ns inter-channel skew and halves usable BW per channel;
scope-style use assumes simultaneous capture.

**F5 coupling** — options: DC-only, AC-only, switchable (relay + film cap). Chose DC-only:
switchable coupling costs a relay + bias network per channel for no stated requirement.
AC coupling is deferred (see Carried forward).

**F6/F7 bandwidth** — 10 MSPS puts Nyquist at 5 MHz. Options: (a) −3 dB at 4.5 MHz with a
brick-wall (≥8th-order) filter, (b) −3 dB at 4 MHz with a 4th-order max-flat filter,
(c) no AAF, rely on source bandwidth. Chose (b): a 4th-order filter reaches ~32 dB at
10 MHz and ~56 dB at 20 MHz, which is the usual scope-front-end compromise; (a) costs
2–3 extra op-amps per channel and adds passband ripple/group-delay error.

**F12 capture modes** — see §3 for the bandwidth arithmetic that forces this.

## 2. Power

| ID | Requirement | Value | Type | Src |
|---|---|---|---|---|
| P1 | Source | USB VBUS only, bus-powered, no barrel jack, no battery | HARD | [USER] ("provides power") |
| P2 | Total draw | ≤ 450 mA @ 5 V sustained (USB 2.0 500 mA limit, 10 % margin) | HARD | [DRIVER] |
| P3 | Pre-enumeration draw | ≤ 100 mA until configured | HARD | [DRIVER] |
| P4 | Rails required | +3.3 V digital; analog rails sufficient for a ±10 V-swing front end (bipolar, e.g. ±5 V or ±6 V); ADC/ref rails per chosen converter; core rail if a programmable-logic device is used | HARD | [DRIVER] |
| P5 | Analog rail noise | ≤ 100 µVrms (10 Hz–1 MHz) at the ADC and reference pins; LDO post-regulation on every analog rail | HARD | [DRIVER] |
| P6 | Sleep / low-power modes | None required — the board is idle-powered when not capturing | SOFT | [DRIVER] |
| P7 | Inrush | Meet USB 2.0 §7.2.4.1 (≤10 µF effective bulk at VBUS or soft-start) | SOFT | [DRIVER] |

**P4 bipolar rails** — options: (a) single-supply front end with a mid-rail pedestal,
(b) bipolar rails from an inverting charge pump / DC-DC. Chose (b): a ±10 V input scaled
into a single-supply amplifier still needs headroom for overdrive and puts the summing
node at risk on overload; bipolar rails also keep the attenuator/buffer linear through
the full overload range (F9).

## 3. Interface

| ID | Requirement | Value | Type | Src |
|---|---|---|---|---|
| I1 | Host interface | USB 2.0 high-speed (480 Mb/s), device only | HARD | [USER] |
| I2 | USB connector | USB-C receptacle, USB 2.0 signalling only, 2× 5.1 kΩ CC pulldowns | HARD | [DRIVER] |
| I3 | Analog connectors | 2× PCB-mount BNC female jack, one per channel, standard 50 Ω-body scope-lead mating | HARD | [USER] ("mate with standard oscilloscope leads") |
| I4 | Input impedance | 1 MΩ ∥ ≤ 25 pF, compensated | HARD | [DRIVER] |
| I5 | Sustained payload | 2 ch × 10 MSPS × 12 b = 240 Mb/s = 30 MB/s when samples are bit-packed; 40 MB/s if each 12-bit sample is padded to 16 bits | — | derived |
| I6 | Sample packing | Samples must be bit-packed (4 samples → 3 × 16-bit words) before the USB endpoint | HARD | [DRIVER] |
| I7 | Streaming protocol | Bulk IN endpoint, double-buffered, ≥ 512 B packets | HARD | [DRIVER] |
| I8 | Control channel | Vendor control endpoint: gain/range, trigger config, arm, start/stop, status | HARD | [DRIVER] |
| I9 | Firmware load | USB device may enumerate from an on-board EEPROM or be host-loaded; an EEPROM must be fitted | SOFT | [DRIVER] |
| I10 | External trigger | 1× 0.1" 3-pin header, 3.3 V logic trigger in/out, ESD-clamped | SOFT | [DRIVER] |
| I11 | Debug | JTAG/programming header for any programmable logic; 2 status LEDs (power, capture) | SOFT | [DRIVER] |

**I5/I6/I12 — the central design tension.** USB 2.0 high-speed bulk tops out near 53 MB/s
theoretically and 35–43 MB/s in practice on a good host controller. 40 MB/s unpacked leaves
essentially no margin and will drop data on many hosts; 30 MB/s packed leaves ~25 % margin.
Options considered:
- (a) Stream unpacked 16-bit samples, 40 MB/s — simplest logic, unreliable on real hosts. Rejected.
- (b) Bit-pack to 30 MB/s and stream continuously — needs a packing engine (CPLD/FPGA or a
  USB MCU with FIFO logic) but fits USB 2.0. **Selected as the streaming path.**
- (c) Reduce sample rate or channel count in streaming mode — violates F3. Rejected as the
  primary mode, retained as a host-selectable decimation option.
- (d) Capture bursts into on-board memory and drain slower — guarantees lossless full-rate
  capture regardless of host. **Selected as the guaranteed path (F12a).**
The architecture must implement (b) and (d) together: (d) is what makes the specified
10 MSPS honest, (b) is what makes it useful as a live streamer.

**I2 connector** — options: USB-C (modern cables, needs CC pulldowns), Micro-B (legacy,
fragile), Type-B (robust, bulky). Chose USB-C: current cable availability, mechanically
sturdier than micro-B, and USB 2.0-only wiring is trivial.

**I4 input impedance** — options: (a) 1 MΩ ∥ ~20 pF scope-style, (b) 50 Ω terminated,
(c) switchable. Chose (a): "standard oscilloscope leads" means passive probes, which are
compensated for a 1 MΩ ∥ 15–25 pF load and will show gross amplitude/frequency error into
50 Ω. Cost: a compensated attenuator and a low-capacitance high-Z buffer are required.

## 4. Physical

| ID | Requirement | Value | Type | Src |
|---|---|---|---|---|
| X1 | Board size | ≤ 100 × 80 mm | SOFT | [DRIVER] |
| X2 | Stackup | 4-layer FR4, 1.6 mm, continuous ground plane under the analog front end | HARD | [DRIVER] |
| X3 | Assembly | All SMD, single-sided placement where possible; BNC/USB/headers may be through-hole | HARD | [DRIVER] |
| X4 | Minimum package | 0402 passives, 0.5 mm-pitch fine-pitch ICs acceptable; no BGA below 0.8 mm pitch | SOFT | [DRIVER] |
| X5 | Temperature range | 0 – 70 °C commercial | HARD | [DRIVER] |
| X6 | Regulatory | None — lab prototype, not a sold product. Design for EMC good practice, no certification | HARD | [DRIVER] |
| X7 | Mounting | 4× M3 mounting holes | SOFT | [DRIVER] |

## 5. Production

| ID | Requirement | Value | Type | Src |
|---|---|---|---|---|
| N1 | Quantity | 5 prototype boards | SOFT | [DRIVER] |
| N2 | Assembly house | JLCPCB; prefer Basic/Preferred parts; every part must be in stock | HARD | [DRIVER] |
| N3 | BOM cost target | ≤ $180 per board at qty 5 | SOFT | [DRIVER] |
| N4 | Lifecycle | No NRND/EOL parts; flag any single-source part | HARD | [DRIVER] |
| N5 | Test | Power-rail test points + a test point on each ADC input | SOFT | [DRIVER] |
