# SPEC — dual_adc_usb

Source: `dual-adc-prompt.txt` (user). The user asked that open decisions be resolved by listing
options and selecting a recommendation without pausing. Every item below is tagged:

- **[USER]** — stated in the prompt.
- **[DRIVER]** — chosen by the pipeline driver on the user's behalf (options listed in § Decisions log).

## 1. Functional

| # | Requirement | Value | Source | Hard/Soft |
|---|---|---|---|---|
| F1 | Channels | 2 analog inputs | USER | HARD |
| F2 | Input signal range | −10 V … +10 V (20 Vpp), full scale, at the board connector | USER | HARD |
| F3 | Sample rate | 10 MSPS per channel | USER | HARD |
| F4 | Resolution | 12 bits | USER | HARD |
| F5 | Sampling alignment | Both channels sampled simultaneously from one clock (≤1 clock-cycle skew) | DRIVER | HARD |
| F6 | Input coupling | DC coupled | DRIVER | SOFT |
| F7 | Input impedance | 1 MΩ ∥ 15–25 pF (oscilloscope-standard, so 1×/10× passive probes compensate) | DRIVER | HARD |
| F8 | Analog bandwidth | −3 dB ≥ 3 MHz; anti-alias roll-off so content > 5 MHz (Nyquist) is attenuated; ≥2nd-order target −3 dB 4–5 MHz | DRIVER | SOFT |
| F9 | Input overvoltage survival | ±50 V continuous at the BNC without damage (clamped, not measured) | DRIVER | SOFT |
| F10 | Accuracy | Uncalibrated gain error ≤ 2 %, offset ≤ 1 % FS; software calibration assumed. Front-end noise ≤ 1 LSB rms (≈ 4.9 mV at the input) | DRIVER | SOFT |
| F11 | Dynamic performance | ENOB ≥ 10 bits at 1 MHz input (sets sample-clock jitter ≲ 20 ps rms) | DRIVER | SOFT |
| F12 | Sample clock | On-board low-jitter oscillator; the ADC clock must not be derived from a noisy FPGA PLL unless jitter budget is shown to hold | DRIVER | SOFT |
| F13 | Data transfer mode | **Minimum [HARD]:** triggered/block capture into on-board buffer of ≥ 16 k samples/channel, then read out over USB. **Goal [SOFT]:** gap-free continuous streaming of both channels at full rate (2 × 10 MSPS × 12 b = 240 Mb/s = 30 MB/s packed, 40 MB/s as 16-bit words) | DRIVER | see text |
| F14 | Trigger | Software/host trigger mandatory; level trigger on either channel implemented in digital logic (no analog comparator required) | DRIVER | SOFT |

## 2. Power

| # | Requirement | Value | Source | Hard/Soft |
|---|---|---|---|---|
| P1 | Supply source | USB VBUS only; no external supply | USER | HARD |
| P2 | Current budget | ≤ 450 mA total from VBUS (USB 2.0 limit 500 mA, 10 % margin); ≤ 100 mA before enumeration is **not** enforced in hardware (accepted risk, typical of USB instruments) | DRIVER | HARD (450 mA) |
| P3 | Rails | Architect's choice. Analog rails must be generated/filtered so switching noise does not exceed ~½ LSB at the ADC input; LDO post-regulation of any switcher feeding analog/ADC/clock | DRIVER | SOFT |
| P4 | Bipolar front-end supply | Allowed (e.g. charge pump/inverting converter) or single-supply level-shift topology — architect decides with explicit trade-off | DRIVER | SOFT |
| P5 | Inrush | USB-compliant bulk capacitance on VBUS ≤ 10 µF before any soft-start/load switch | DRIVER | SOFT |
| P6 | Sleep modes | None required | DRIVER | — |

## 3. Interface

| # | Requirement | Value | Source | Hard/Soft |
|---|---|---|---|---|
| I1 | Signal connectors | 2 × BNC female, 50 Ω body, PCB-mount (right-angle preferred) — mates with standard scope probes and BNC leads | USER/DRIVER | HARD (BNC) |
| I2 | Host interface | USB 2.0 **High-Speed (480 Mb/s)** device; Full-Speed (12 Mb/s) cannot carry the data rate | USER/DRIVER | HARD |
| I3 | USB connector | USB Type-C receptacle, USB 2.0 only (D+/D−, CC1/CC2 each 5.1 kΩ to GND = sink, 5 V default current) | DRIVER | SOFT |
| I4 | USB ESD | TVS/ESD array on D+/D− (low capacitance, HS-rated) and VBUS | DRIVER | HARD |
| I5 | Galvanic isolation | None — input ground is the USB/host ground (as on a bench scope) | DRIVER | SOFT |
| I6 | Programming/debug | Headers for configuring/debugging every programmable device (e.g. JTAG/SWD, config flash programming) | DRIVER | HARD |
| I7 | Indicators | Power LED + at least one status LED | DRIVER | SOFT |
| I8 | Expansion | Optional: external trigger in/out or GPIO header — nice-to-have only | DRIVER | SOFT |

## 4. Physical

| # | Requirement | Value | Source | Hard/Soft |
|---|---|---|---|---|
| M1 | Assembly | SMD wherever possible; through-hole allowed for BNC and USB shell | DRIVER | SOFT |
| M2 | Board | Target ≤ 100 × 80 mm; 4-layer stack-up assumed (mixed-signal + HS USB) | DRIVER | SOFT |
| M3 | Temperature | 0 … 50 °C (lab instrument) | DRIVER | SOFT |
| M4 | Regulatory | No certification; follow good EMC/ESD practice | DRIVER | SOFT |
| M5 | Enclosure | None specified | DRIVER | — |

## 5. Production

| # | Requirement | Value | Source | Hard/Soft |
|---|---|---|---|---|
| Q1 | Quantity | 5–10 prototypes | DRIVER | SOFT |
| Q2 | Assembly house | JLCPCB PCBA; prefer Basic/Preferred parts, Extended allowed; all parts in stock | DRIVER | SOFT |
| Q3 | Cost target | BOM ≤ US$ 120 per board at qty 10 (excluding PCB) | DRIVER | SOFT |
| Q4 | Deliverable | SKiDL schematic → netlist + BOM. Firmware, FPGA/MCU code, host software, PCB layout are out of scope | DRIVER | HARD |

## Decisions log (options → selection)

1. **Connector** — options: BNC / SMA / 4 mm banana / MCX. → **BNC** (the only one that mates with standard scope leads/probes).
2. **Input impedance** — options: 1 MΩ ∥ ~20 pF / 50 Ω / switchable. → **1 MΩ ∥ ~20 pF** (scope-standard; 10× probes compensate; 50 Ω would load typical sources and dissipate 2 W at 10 V). Switchable adds relays/cost.
3. **Coupling** — options: DC only / AC only / switchable. → **DC only** (simpler; AC can be added with a series cap externally). Soft.
4. **USB speed class** — options: Full-Speed MCU / High-Speed bridge / USB 3 (FX3/FT601 on a USB-2 port). → **USB 2.0 High-Speed** (FS is 12 Mb/s, far below 240 Mb/s; USB 3 parts are out of spec for the "USB 2.0" requirement and costlier).
5. **Transfer mode** — options: (a) block capture into buffer, (b) continuous streaming, (c) both. → **(c): (a) guaranteed, (b) as a goal** — 30–40 MB/s sits at the practical ceiling of USB 2.0 HS bulk (~35–42 MB/s on good hosts), so streaming cannot be promised on all hosts.
6. **USB connector** — options: Type-C / Micro-B / Type-B. → **Type-C** (current standard, robust; USB 2.0 wiring only).
7. **Isolation** — options: none / HS USB isolator (ADuM4165-class) / isolated analog front end. → **None** (HS isolators are expensive and add power; a ground-referenced input matches bench-scope behaviour). Soft — risk: ground loops through host.
8. **Front-end supply** — options: single-supply level-shift / bipolar rails from charge pump / isolated DC-DC. → **Architect decides**, noise and current budget must be shown.
9. **Circuit name** — `dual_adc_usb`.
10. **Cache** — `use_cache = false` (user asked for a blank slate).
