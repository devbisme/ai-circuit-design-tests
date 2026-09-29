# SPEC — dual_adc_usb

Dual-channel 12-bit / 10 MSPS oscilloscope-lead digitizer, USB bus-powered.

Source: `dual-adc-prompt.txt` (single prompt, no interactive interview — the prompt
instructed: list options, choose the recommendation, do not pause). Every requirement
below is tagged with its provenance:
**[USER]** = stated in the prompt, **[DERIVED]** = arithmetic consequence of a [USER] item,
**[CLAUDE]** = engineering choice made by me because the prompt left it open.

---

## 1. Functional

| # | Requirement | Value | Class | Prov. |
|---|---|---|---|---|
| F1 | Analog input channels | 2, simultaneously sampled (no mux) | HARD | USER |
| F2 | Input signal range (at the connector, 1:1 lead) | −10 V … +10 V, 20 V p-p FSR | HARD | USER |
| F3 | Sample rate, per channel | 10.0 MSPS, continuous during a capture | HARD | USER |
| F4 | Resolution | 12 bit | HARD | USER |
| F5 | Capture depth at full rate | ≥ 0.1 s ⇒ ≥ 1 Msample/channel, 2 Msample total | HARD | USER |
| F6 | Raw capture payload | 24 Mbit = 3.0 MB packed 12-bit; 4.0 MB stored as 16-bit words | HARD | DERIVED |
| F7 | Sustained sample data rate during capture | 2 ch × 10 MSPS × 12 b = **240 Mbit/s = 30 MB/s** | HARD | DERIVED |
| F8 | Capture model | Burst-to-onboard-RAM, then read out over USB (see D1) | HARD | DERIVED |
| F9 | Analog bandwidth | −0.5 dB to 4.0 MHz, −3 dB ≤ 5 MHz — **SUPERSEDED, see note ¹** | SOFT | CLAUDE |
| F10 | Anti-alias filtering | ≥ 25 dB attenuation above 7 MHz (≥ 3rd-order) — **SUPERSEDED, see note ¹** | SOFT | CLAUDE |
| F11 | Dynamic performance | ≥ 10.5 ENOB (≈ 65 dB SNR) at 1 MHz in, full scale | SOFT | CLAUDE |
| F12 | DC accuracy | gain/offset error correctable in host software; no onboard calibration DAC | SOFT | CLAUDE |
| F13 | Trigger | host-commanded start (software trigger) minimum; simple level trigger in logic if I/O allows | SOFT | CLAUDE |
| F14 | Sample-clock jitter | ≤ 14 ps RMS to hold 11 ENOB at 4.5 MHz ⇒ use ≤ 5 ps XO, **not** an FPGA PLL output | HARD | DERIVED |

> **¹ F9 and F10 were renegotiated by architecture revision 3** (both are SOFT/CLAUDE — my own
> choices, not the user's — and as written they are mutually unachievable: together they need
> n ≈ 7, and F9's two clauses alone need n ≈ 5). **The numbers this board is held to now live in
> `architecture/design_risks.md` § "Requirements this architecture knowingly deviates from",
> and that table is the authority:** F9 → ≤0.5 dB to 4.0 MHz, −3 dB at 6.1 MHz (the "−3 dB
> ≤ 5 MHz" clause is deleted); F10 → ≥25 dB above 16.0 MHz analog, 3rd-order. A new
> **S1 [HARD, DERIVED]** requires the host's 2:1 decimation to include a real digital low-pass
> (≥40 dB above 5.0 MHz) — without it the 5–10 MHz octave folds into the band and F9/F10 are
> lost in software with no hardware symptom (`design_risks.md` R-12).

## 2. Power

| # | Requirement | Value | Class | Prov. |
|---|---|---|---|---|
| P1 | Sole power source | USB bus, 5 V. No external supply, no battery. | HARD | USER |
| P2 | Connector/power contingency | USB-C receptacle, 5.1 kΩ CC1/CC2 pulldowns (see D2) | HARD | USER+CLAUDE |
| P3 | Budget ceiling | ≤ 1.5 A @ 5 V (7.5 W) available; design target ≤ 700 mA (3.5 W) | SOFT | CLAUDE |
| P4 | Inrush / enumeration | ≤ 500 mA until configured; bulk cap ≤ 10 µF at VBUS entry | HARD | CLAUDE |
| P5 | Rails required (est.) | +3.3 V digital/IO, +1.2 V FPGA core, +1.8 V ADC digital (if needed), analog +5 V/+3.3 V clean | HARD | CLAUDE |
| P6 | Negative rail | none — the front end attenuates passively before any active stage, so no ±12 V is needed | HARD | CLAUDE |
| P7 | Sleep / low-power modes | none required (bench instrument, active only when host is streaming) | HARD | CLAUDE |
| P8 | Analog rail noise | ADC/amp rails via LDO (≥ 50 dB PSRR at 100 kHz), not directly off a switcher | SOFT | CLAUDE |

## 3. Interface

| # | Requirement | Value | Class | Prov. |
|---|---|---|---|---|
| I1 | Host interface | USB 2.0 High-Speed (480 Mbit/s), bulk transfer | HARD | USER |
| I2 | USB connector | USB-C receptacle, USB 2.0 pins only (no SS pairs, no PD controller) | HARD | CLAUDE |
| I3 | Analog input connectors | BNC, board-edge, 50 Ω body — mates with standard scope leads/probes | HARD | USER |
| I4 | Input impedance | 1 MΩ ±1 % to GND, compensated attenuator ⇒ works with 1:1 and 10:1 scope probes | HARD | CLAUDE |
| I5 | Input protection | survives ±30 V DC continuous at the BNC without damage | SOFT | CLAUDE |
| I6 | Host-side software | libusb / FTDI D2XX class driver; no custom kernel driver | SOFT | CLAUDE |
| I7 | Config/debug | JTAG header for FPGA (2.54 mm or Tag-Connect), status LEDs (power, capture) | SOFT | CLAUDE |

## 4. Physical

| # | Requirement | Value | Class | Prov. |
|---|---|---|---|---|
| H1 | Construction | 4-layer PCB, all SMD except BNCs and headers | HARD | CLAUDE |
| H2 | Board outline | ≤ 100 × 80 mm (JLCPCB standard-price tier) | SOFT | CLAUDE |
| H3 | Temperature range | 0 … +50 °C, commercial | SOFT | CLAUDE |
| H4 | Regulatory | none (lab/personal instrument, not a product) | HARD | CLAUDE |
| H5 | Mechanical | free-standing board, BNCs one edge, USB-C the opposite edge | SOFT | CLAUDE |

## 5. Production

| # | Requirement | Value | Class | Prov. |
|---|---|---|---|---|
| Q1 | Quantity | 5 prototypes | SOFT | CLAUDE |
| Q2 | Assembly | JLCPCB PCBA; prefer Basic/Preferred-tier parts; single-side placement if possible | HARD | CLAUDE |
| Q3 | BOM cost target | ≤ $70 in parts at qty 5 (ADCs dominate) | SOFT | CLAUDE |
| Q4 | Part availability | every part in stock at JLCPCB ≥ 200 units at design time; no NRND/EOL | HARD | CLAUDE |
| Q5 | Blank slate | no reuse of artifacts, caches, or parts lists from sibling designs in this tree | HARD | USER |

---

## Design decisions (options considered → recommendation)

### D1 — Can USB 2.0 carry 30 MB/s live, or is an onboard buffer mandatory?
| Option | Pros | Cons |
|---|---|---|
| Stream live over USB 2.0 HS | no RAM needed | 30 MB/s sustained is 60–75 % of the *theoretical* 40–45 MB/s HS bulk ceiling and above what any commodity HS FIFO bridge holds reliably under host-scheduling jitter; any dropout corrupts the record |
| **Burst into onboard RAM, then read out (chosen)** | capture rate decoupled from USB; 4 MB read-out at ~30 MB/s takes ~0.15 s; deterministic | needs ≥ 4 MB of RAM and a controller |
| USB 3.0 (FX3) live streaming | no depth limit | violates the USER's "USB 2.0" requirement |
**Recommendation: burst-to-RAM.** F5 (0.1 s at full rate) is a *finite record*, which is exactly what a buffered digitizer does well. This also makes USB throughput a convenience, not a correctness requirement.

### D2 — USB-A (5 V / 500 mA) or USB-C?
Estimated load: FPGA ~250 mW, 2× ADC ~350 mW, 4× amplifier ~300 mW, bridge + clocks + LEDs ~350 mW, regulator losses ~20 % ⇒ **≈ 1.5 W ≈ 300 mA typ, ~450 mA worst case** at 5 V. That *just* fits a 500 mA USB-A budget, with no margin for a front-end change.
| Option | Pros | Cons |
|---|---|---|
| USB-A/B, 500 mA | simplest | zero headroom; a beefier amp or a second regulator breaks the budget |
| **USB-C, 5.1 kΩ CC pulldowns (chosen)** | 5 V up to 1.5–3 A when the source advertises it, graceful 500 mA fallback, reversible, current connector; no PD silicon needed | 2 extra resistors, 16-pin receptacle footprint |
| USB-C + PD sink controller | could request 9/12 V | pointless — we need 5 V only; adds cost, firmware, risk |
**Recommendation: USB-C with plain CC pulldowns**, per the prompt's "if insufficient power … use a USB C port". Data is still USB 2.0 only.

### D3 — Front-end topology for ±10 V from a 5 V-only board
| Option | Pros | Cons |
|---|---|---|
| **Passive compensated 10:1 divider (1 MΩ) → low-voltage amp → ADC (chosen)** | no ±12 V rails, no boost converter, inherent overvoltage tolerance, scope-probe-compatible 1 MΩ | needs C-compensation across the divider to stay flat to 5 MHz; resistor noise/tolerance set gain accuracy |
| High-Z FET buffer at full ±10 V, then divide | best BW, lowest source loading | requires ±12 V rails from USB 5 V (boost + inverter): noise, cost, ~1 W of loss |
| 50 Ω terminated input | flattest response | wrong impedance for scope probes, loads the DUT, ±10 V into 50 Ω = 2 W |
**Recommendation: passive-attenuate-first.** It is the only topology that keeps a USB-bus-powered board on a single-polarity 5 V input while accepting ±10 V, and it is what bench scopes do.

### D4 — Digitizer/controller silicon
| Option | Pros | Cons |
|---|---|---|
| **FPGA + ADCs + USB 2.0 HS FIFO bridge (chosen)** | deterministic 10 MSPS×2 capture, RAM controller, proven bridge (FTDI) needs no firmware development | FPGA toolchain + bitstream, JTAG/flash |
| MCU (STM32H7) internal ADCs | one chip, C firmware | internal ADCs reach ~3.6 MSPS/ch (≈7.2 interleaved) — fails F3 by ~3× |
| Cypress FX2LP + CPLD | cheap, GPIF does 8-bit 48 MHz | 8051 firmware, lifecycle/stock risk, still needs external RAM+glue |
| Dedicated USB scope ASIC | turnkey | none available at 2 ch × 12 b × 10 MSPS |
**Recommendation: FPGA + 2 ADCs + FTDI HS FIFO bridge.** Prefer an FPGA with **in-package SDRAM/PSRAM ≥ 64 Mbit** (e.g. Gowin GW1NR-9 class) so the 4 MB buffer needs no external memory bus — big reduction in layout and pin-count risk. Fall back to an external 16-bit SDR SDRAM if stock/tooling says otherwise. Final part choice belongs to phase 2/3 with live stock data.

### D5 — Sample clock
| Option | Pros | Cons |
|---|---|---|
| FPGA PLL output → ADCs | free | PLL jitter (tens of ps) eats 1–2 ENOB near Nyquist (F14) |
| **Dedicated low-jitter XO (≤ 5 ps RMS) → both ADCs; separate XO/crystal for logic+USB (chosen)** | meets F14 with margin; both channels share one edge ⇒ true simultaneity | 1 extra oscillator, one clock-domain crossing in the FPGA |
**Recommendation: dedicated ADC clock oscillator**, FIFO across to the logic domain.
