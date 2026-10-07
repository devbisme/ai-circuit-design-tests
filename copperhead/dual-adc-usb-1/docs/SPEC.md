# SPEC — Dual-Channel ±10 V, 12-bit, 10 MSPS USB ADC Board

Status: stage 1 (spec-seed). Source of truth for all later stages.
Items marked **ASSUMED** are not in the brief. Each is a proposed default that can be revised; record the change in docs/DECISIONS.md if you revise one.
Every numeric budget below is also recorded in `.copperhead/constraints.json`.

## 1. What the device is

This is a bus-powered USB data-acquisition board with two analog inputs.
- **Inputs:** each input accepts a signal in [-10 V, +10 V] through a connector that mates with standard oscilloscope leads.
- **Sampling:** both channels are digitized at 10 MSPS with 12-bit resolution.
- **Capture:** at least 0.1 s of samples per channel at the maximum rate goes into on-board memory.
- **Transfer:** samples go to a host PC over USB 2.0 High-Speed (480 Mbit/s).
- **Power:** the same USB port powers the board.

## 2. Functional requirements

| ID | Requirement | Source |
|----|-------------|--------|
| F1 | 2 analog input channels, sampled simultaneously (same clock edge) | Brief: 2 channels. Simultaneity is **ASSUMED** (natural for a scope-like tool) |
| F2 | Input range -10 V to +10 V full scale, DC-coupled | Brief: range. DC coupling is **ASSUMED** |
| F3 | Sample rate 10 MSPS per channel (both channels at once) | Brief |
| F4 | Resolution 12 bits | Brief |
| F5 | Capture depth ≥ 0.1 s per channel at 10 MSPS, i.e. ≥ 1,000,000 samples/channel and ≥ 2,000,000 samples total | Brief |
| F6 | Inputs on connectors that mate with standard oscilloscope leads/probes | Brief |
| F7 | Host interface: USB 2.0, used for both power and sample transfer | Brief |
| F8 | Use a USB-C port if USB 2.0 power is insufficient | Brief |
| F9 | Trigger: software (host-commanded) start, plus a per-channel level/edge trigger in logic | **ASSUMED** |
| F10 | Lower sample rates selectable by decimation (10 MSPS / N) | **ASSUMED** |

## 3. Derived budgets

| Key | Budget | Derivation |
|-----|--------|------------|
| `adc.sample_rate_MSPS` | ≥ 10 per channel | F3 |
| `adc.resolution_bits` | ≥ 12 | F4 |
| `input.voltage_range_V` | -10 … +10 (full scale at the connector) | F2 |
| `capture.depth_s` | ≥ 0.1 at 10 MSPS, both channels | F5 |
| `capture.buffer_MB` | ≥ 4 MB (32 Mbit) | 2 ch × 10 MSPS × 0.1 s = 2 M samples × 2 B each (12 bits stored in a 16-bit word) = 4 MB. Packed 12-bit storage would need 3 MB; 16-bit words are kept for simplicity |
| `data.raw_rate_MBps` | 40 MB/s (16-bit words) or 30 MB/s (packed) | 2 × 10 MSPS × 2 B |
| `usb.throughput_MBps` | Design for ≥ 30 MB/s bulk readout. Real-time streaming is NOT guaranteed | USB 2.0 HS bulk: 53 MB/s theoretical, about 35–42 MB/s in practice and host-dependent. 40 MB/s continuous is not reliably achievable, so the architecture is capture-to-buffer then readout. 4 MB reads out in about 0.1–0.15 s |
| `power.vbus_voltage_V` | Operate from 4.4 V to 5.25 V at the board connector | USB 2.0: 4.75–5.25 V at the host port, with cable/hub drop down to 4.4 V |
| `power.vbus_current_mA` | ≤ 450 mA steady state (90 % of the 500 mA USB 2.0 high-power limit) | USB 2.0 §7.2.1. The 10 % margin covers estimate error |
| `power.preconfig_current_mA` | ≤ 100 mA before the host sets configuration | USB 2.0 unit load. The analog front end, ADC, and buffer rails must be power-gated until the device is configured |
| `power.suspend_current_mA` | ≤ 2.5 mA in USB suspend | USB 2.0 §7.2.3 |
| `power.vbus_capacitance_uF` | ≤ 10 µF directly on VBUS. Anything more goes behind a soft-start/load switch | USB 2.0 inrush limit |
| `clock.jitter_ps_rms` | ≤ 5 ps rms at the ADC clock pin | SNR_jitter = −20·log10(2π·f_in·t_j). For SNR ≥ 74 dB (ideal 12-bit) at f_in = 5 MHz (Nyquist), t_j ≤ 6.3 ps. 5 ps gives margin |
| `input.impedance` | 1 MΩ ∥ ~20 pF per channel | **ASSUMED**: the oscilloscope-input standard, so passive 1×/10× probes compensate correctly |
| `input.overvoltage_V` | Survive ±30 V continuous at the connector with no damage | **ASSUMED**: protects against a probe set to the wrong range |
| `analog.bandwidth_MHz` | -3 dB ≥ 3 MHz; anti-alias filter attenuates ≥ 40 dB at ≥ 7.5 MHz (folds to 2.5 MHz) | **ASSUMED**: the brief gives no bandwidth; this is chosen for 10 MSPS Nyquist |
| `analog.enob_bits` | ≥ 10.5 ENOB at f_in = 1 MHz, end to end | **ASSUMED** |
| `analog.dc_accuracy` | Post-calibration gain error ≤ 1 %, offset ≤ ±20 mV referred to input, using per-channel constants stored on the board (93LC56). Uncalibrated: gain error ≤ 3 %, offset ≤ ±150 mV RTI (sets the calibration range only) | **DECIDED** (user, 2026-10-06, option (a)) |

### 3.1 Preliminary power estimate (to be refined in part selection)

| Block | Estimate |
|-------|----------|
| Dual 12-bit ADC (≥10 MSPS class) | 100–250 mW |
| Front end (2 × buffer + driver, ±5 V-class rails) | 200–350 mW |
| Capture logic (small FPGA) | 150–400 mW |
| SDRAM buffer (active) | 100–250 mW |
| USB bridge | 150–300 mW |
| Converter losses (~85 % efficiency) | +15–20 % |
| **Total at VBUS** | **~0.8–1.8 W, i.e. about 170–410 mA at 4.4 V** |

The upper end of the estimate is close to the 450 mA budget. This is why §4.5 recommends a USB-C connector. Even so, the design must still fit the 450 mA budget.

## 4. Design decisions (options → recommendation)

### 4.1 Input connector

Options:
- (a) BNC 50 Ω PCB jack
- (b) SMA
- (c) 4 mm banana
- (d) 2.54 mm header with test clips

→ **Recommend (a) BNC, right-angle PCB mount, shell to GND.** This is what "standard oscilloscope leads" means: passive probes and BNC-to-clip leads both mate with it.

### 4.2 Front-end input impedance

Options:
- (a) 1 MΩ ∥ ~20 pF
- (b) 50 Ω
- (c) selectable

→ **Recommend (a).** Scope probes require 1 MΩ, and 50 Ω would load the ±10 V sources and dissipate 2 W at full scale.

### 4.3 Capture architecture

Options:
- (a) Stream continuously over USB
- (b) Capture to an on-board buffer, then read out
- (c) Hybrid: a buffered capture by default, plus best-effort streaming at reduced rate or packed data

→ **Recommend (c), with (b) as the guaranteed mode.** 30–40 MB/s is at or above practical USB 2.0 HS bulk throughput, so the 0.1 s requirement is met by the buffer and does not depend on the host.

### 4.4 Buffer memory

Options:
- (a) FPGA block RAM: too small, since 4 MB exceeds small-FPGA BRAM
- (b) 16-bit SDR SDRAM, ≥ 256 Mbit
- (c) HyperRAM, 64 Mbit
- (d) QSPI PSRAM, 64 Mbit
- (e) DDR3

→ **Recommend (b) SDR SDRAM ×16, 256 Mbit (32 MB).**
- Cheap and widely available.
- 200 MB/s raw at 100 MHz, far above the 40 MB/s write rate.
- Gives about 0.8 s of depth, 8× the requirement.
- An easy controller for any small FPGA.

(c) is the fallback if pin count gets tight.

### 4.5 USB connector / power source

Options:
- (a) USB 2.0 Type-B or Micro-B, 500 mA
- (b) USB-C receptacle carrying USB 2.0 HS data, power sink with 5.1 kΩ Rd on CC1/CC2: Default (500 mA), plus 1.5 A or 3 A when the source advertises it
- (c) USB-C with USB-PD negotiation

→ **Recommend (b).**
- **Why USB-C:** the power estimate (§3.1) is close to the 500 mA limit, which is the brief's trigger for USB-C.
- **Data stays USB 2.0 HS**, which satisfies F7.
- **No dependence on the extra current:** the board is still budgeted to ≤ 450 mA, so it works on any USB 2.0 host through a C-to-A cable. Type-C Current advertisements are headroom only.
- **No PD:** PD controller cost and complexity are not justified at 5 V.

### 4.6 USB bridge

Options:
- (a) FTDI FT232H in synchronous 245 FIFO mode
- (b) Infineon/Cypress FX2LP (CY7C68013A)
- (c) Infineon FX3 (CYUSB3014) running at HS
- (d) MCU with a HS PHY (e.g. STM32 + ULPI PHY)
- (e) FPGA soft USB + ULPI PHY

→ **Recommend (a) FT232H.**
- Its sync FIFO (≈ 40 MB/s) maps directly to FPGA logic.
- No bridge firmware to write.
- Mature host drivers (D2XX/libftdi).

(b) is the fallback if custom USB descriptors or endpoints are needed. Before committing, the FT232H's suspend current must be checked against `power.suspend_current_mA` in the part-selection stage.

### 4.7 Capture/control logic

Options:
- (a) Small FPGA (e.g. iCE40, ECP5, Gowin, Spartan-7 class)
- (b) MCU with a parallel capture port and SDRAM controller (e.g. STM32H7 DCMI + FMC)

→ **Recommend (a) FPGA.** It gives deterministic 2×12-bit capture at 10 MSPS, SDRAM control, triggering, and the FT232H FIFO interface in one device.

### 4.8 ADC topology

Options:
- (a) One dual-channel simultaneous-sampling 12-bit ADC
- (b) Two single-channel ADCs on a shared clock

→ **Recommend (a).** It gives inherent channel-to-channel timing alignment and fewer parts. The part is chosen in the part-selection stage, and must be in a hand-solderable or standard reflow package with an installed KiCad symbol.

## 5. Other ASSUMED defaults

| Item | Default |
|------|---------|
| Isolation | None; input ground = USB ground = BNC shell. Not for mains-referenced measurements (**ASSUMED**) |
| Probe attenuation | The ±10 V range is at the BNC. A 10× probe extends it to ±100 V at the probe tip, but the board does not detect the probe (**ASSUMED**) |
| Operating environment | 0–40 °C, indoor lab (**ASSUMED**) |
| Board | ≤ 100 × 80 mm, 4-layer (signal/GND/power/signal), standard 1.6 mm FR-4 (**ASSUMED**) |
| Enclosure | Optional; BNCs and USB-C on board edges (**ASSUMED**) |
| Host software | Out of scope for hardware. Board exposes a capture/arm/readout command set over the FT232H FIFO (**ASSUMED**) |
| Calibration storage | Small I²C/SPI EEPROM, or FPGA config-flash sector, for gain/offset constants (**ASSUMED**) |

## 6. Open items for later stages

The stage 2 architecture is in docs/SUBSYSTEMS.md. It defines the rails, per-rail current allocations, the power-gating sequence (§2.6), the jitter allocation (§6) and the per-part selection limits (§4, §7, §8).

- Select the ADC, front-end op amps, bipolar rail generation, FPGA, SDRAM, and clock oscillator. Check each against the SUBSYSTEMS.md allocations, which sum to the §3 budgets.
- Confirm the FT232H suspend current (allocated ≤1.2 mA) and its maximum operating current (allocated ≤60 mA). See SUBSYSTEMS.md §2.3 and §2.4.
- ~~Define the power-gating sequence~~: done in SUBSYSTEMS.md §2.6. FT232H `PWREN_N` gates `VBUS_SW`, and the FPGA `AFE_EN` gates the ±5V_A rails.
- ~~**AT RISK:** the `analog.dc_accuracy` offset budget~~: resolved 2026-10-06 by user decision (option a). The limit now applies after calibration; the uncalibrated limit is relaxed to ≤3 % / ±150 mV RTI. The SUBSYSTEMS.md §7.6 ADC allocations (≤0.5 % / ≤0.9 mV) now apply post-calibration residuals, not raw ADC error. Verify LTC2290 offset/gain against its datasheet.
