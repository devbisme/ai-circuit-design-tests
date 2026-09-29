# SPEC — dual_adc_usb

Dual-channel 12-bit / 10 MSa-per-second USB oscilloscope-style digitizer.

Source of requirements: `dual-adc-prompt.txt`.
Mark on every line: **[U]** = stated by the user, **[C]** = chosen by Claude in phase 1
(the user delegated all decisions and asked not to be interrupted).
Constraint strength: **[HARD]** = must meet, **[SOFT]** = may be traded with justification.

---

## 1. Functional

| # | Requirement | Src | Strength |
|---|---|---|---|
| F1 | 2 analog input channels, simultaneously sampled (not muxed) | [U] | HARD |
| F2 | Input range ±10 V full scale (20 Vpp) on each channel | [U] | HARD |
| F3 | Sample rate 10.000 MSa/s per channel, both channels at once | [U] | HARD |
| F4 | Resolution 12 bits | [U] | HARD |
| F5 | Capture depth ≥ 0.1 s at full rate = **≥ 1 MSa/channel, 2 MSa total** | [U] | HARD |
| F6 | Capture is burst-to-memory then drain over USB. 2 ch x 10 MSa/s x 16 bit = **40 MB/s**, above dependable USB 2.0 HS bulk throughput (~35–43 MB/s best case), so continuous streaming at full rate is not a requirement and is not promised. | [C] | HARD |
| F7 | Sample buffer sized ≥ 4 MB (2 MSa x 16 bit); 32 MB recommended so the depth requirement has ≥ 8x margin | [C] | HARD (4 MB) / SOFT (32 MB) |
| F8 | Analog bandwidth: −3 dB at ≥ 4 MHz per channel | [C] | HARD |
| F9 | Anti-alias filter: minimum 3rd-order low-pass, −3 dB ≈ 4 MHz, ≥ 25 dB attenuation at 10 MHz (first alias of the DC..Nyquist band). Higher order is welcome if power and part count allow. | [C] | SOFT |
| F10 | DC coupled. AC coupling not required. | [C] | SOFT |
| F11 | Trigger: software/immediate start is sufficient. A comparator-based analog trigger is a nice-to-have, not required. | [C] | SOFT |
| F12 | Gain accuracy ≤ ±2 % FS, offset ≤ ±1 % FS, before host-side calibration | [C] | SOFT |
| F13 | Channel-to-channel skew ≤ 1 sample period (100 ns) | [C] | HARD |

## 2. Power

| # | Requirement | Src | Strength |
|---|---|---|---|
| P1 | All power comes from the host USB port. No barrel jack, no battery. | [U] | HARD |
| P2 | **Steady-state board draw ≤ 450 mA @ 5 V (2.25 W)** so the board is legal on any 500 mA USB 2.0 port. Phase-1 estimate lands near 1.7–1.9 W; see the budget in §2 notes. | [C] | HARD |
| P3 | If the architecture's real budget exceeds 2.25 W, the escape hatch is **CC pull-up sensing on the USB-C connector** to claim 1.5 A or 3.0 A, and the board must then refuse to run (hold analog rails off) on a default-power source. This is the user's "if insufficient power, use USB-C" clause. | [C] | HARD (conditional) |
| P4 | Inrush limited so the host's 500 mA budget is never exceeded at plug-in: soft-start or a current-limited load switch ahead of the bulk capacitance | [C] | HARD |
| P5 | Rails expected: +5 V (USB), +3.3 V digital, FPGA core rail (1.0–1.2 V), +1.8 V aux if the FPGA needs it, +5 V analog and −5 V analog for the front end, and a clean ADC analog rail | [C] | SOFT (exact set is the architect's call) |
| P6 | Analog rails derived through LDOs or a low-noise charge pump, not directly from a switcher output, so switching ripple stays out of the signal chain | [C] | HARD |
| P7 | No sleep or low-power mode required | [C] | SOFT |

**Phase-1 power estimate (to be replaced by the architect's real budget):**
front end ~0.30 W, ADCs ~0.25 W, buffer memory ~0.15 W, FPGA ~0.40 W, USB bridge ~0.27 W
= ~1.37 W of load; ~1.7–1.9 W at the USB connector after conversion losses. Fits 2.25 W with
roughly 20 % margin. This is the single biggest risk to the "USB 2.0 powers it" claim.

## 3. Interface

| # | Requirement | Src | Strength |
|---|---|---|---|
| I1 | Analog inputs on **BNC** connectors — this is what "mates with standard oscilloscope leads" means | [U] | HARD |
| I2 | Input impedance **1 MΩ ∥ ~20 pF**, with a trimmable compensation cap, so standard 10x passive probes can be compensated | [C] | HARD |
| I3 | Input protection: survive ±50 V DC continuous and ESD on the BNC centre pin without damage (clamped, series-limited) | [C] | HARD |
| I4 | Host link: **USB 2.0 High Speed device**, bulk endpoints for sample transfer | [U] | HARD |
| I5 | Connector: **USB-C receptacle**, USB 2.0 signalling only (D+/D− on both A6/A7 and B6/B7), 5.1 kΩ CC1/CC2 pull-downs | [C] | HARD |
| I6 | Debug/bring-up: FPGA programming header (JTAG or SPI-flash), USB-bridge configuration EEPROM, and at least 2 status LEDs | [C] | SOFT |
| I7 | No SD card, no display, no expansion header | [C] | SOFT |

## 4. Physical

| # | Requirement | Src | Strength |
|---|---|---|---|
| Y1 | 4-layer PCB, ≤ 100 x 80 mm | [C] | SOFT |
| Y2 | SMD throughout except BNC and USB connectors; all parts must be placeable by JLCPCB | [C] | HARD |
| Y3 | Operating range 0–50 °C, indoor benchtop | [C] | SOFT |
| Y4 | No regulatory certification (prototype/lab instrument) | [C] | SOFT |
| Y5 | Analog and digital ground handled as one plane with partitioned placement, not a split plane with a stitch | [C] | SOFT |

## 5. Production

| # | Requirement | Src | Strength |
|---|---|---|---|
| R1 | Quantity: 5–10 prototypes | [C] | SOFT |
| R2 | BOM target ≤ $100/board at qty 10 | [C] | SOFT |
| R3 | JLCPCB assembly; prefer Basic/Preferred library parts; every part must have live JLCPCB stock ≥ 100 | [C] | HARD |
| R4 | No part may be single-sourced through an obsolete or NRND MPN | [C] | HARD |

---

## Open questions carried into phase 2

1. Is the 1 MΩ ∥ 20 pF scope-probe-compatible front end worth its cost, versus a simpler
   ~100 kΩ resistive divider that works with plain BNC test leads but cannot compensate a
   10x probe? Phase 1 chose 1 MΩ. The architect may overturn it with a stated reason.
2. Does the real power budget stay under 2.25 W? If not, P3 fires.
3. Which USB 2.0 HS path: a dedicated bridge IC in slave-FIFO mode, or a soft device core
   in the FPGA driving a ULPI PHY? Phase 1 leans to the bridge IC for risk, not elegance.
