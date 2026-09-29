# Design risks — dual_adc_usb

Severity: **H** = can break a HARD requirement or the board; **M** = degrades a SOFT target; **L** = nuisance.
[VERIFY] = the datasheet phase must confirm; the architecture assumes the stated value.

## 1. Power integrity

### Current budget vs the 450 mA HARD limit (P2)

| Rail (source) | Load | Typ mA | Budget mA | Basis |
|---|---|---|---|---|
| VD_3V3 (U3) | FT232H (VREGIN 3.3 V) | 52 | 70 | DS_FT232H: Ireg 52 mA @ 3.3 V |
| | FPGA VCCX + VCCIO0/1/2 | 20 | 30 | estimate [VERIFY Gowin power estimator] |
| | → U4 VD_1V2 (FPGA core) | 50 | 80 | estimate, ~60 % LUT use + PSRAM ctrl [VERIFY] |
| | → U5 VD_1V8 (VCCIO3 + PSRAM) | 20 | 30 | estimate [VERIFY] |
| | EEPROM, U16, U17, pull-ups, LED1–3 | 6 | 7 | 1.3 mA per LED |
| | **U3 total** | **148** | **217** | |
| VA_3V3 (U6) | ADS5231 AVDD | 71 | 82 | SBAS295A: 235.5 / 271 mW ÷ 3.3 V |
| | ADS5231 VDRV (via FB5) | 13 | 20 | 85.5 mW @ 40 MSPS, ~half at 20 MSPS |
| | THS4521 ×2 | 2.3 | 3 | 1.14 mA/ch |
| | X1 oscillator | 6 | 10 | listed max 10 mA |
| | **U6 total** | **92** | **115** | TPS7A20 rating 300 mA |
| ±2.5 V (U7) | OPA354 ×2, both rails | 10 + 10 | 15 + 15 | 5 mA/ch typ; LM27762 draws ≈ I+ + I− + 0.4 mA |
| | **U7 input** | **21** | **32** | |
| **VBUS total** | | **≈ 261** | **≈ 364** | **margin 86 mA (19 %) against 450 mA** ✔ |

- **M: budget margin rests on estimates.** The FPGA and FT232H figures carry about ±30 % uncertainty.
  Trip point: if bring-up measures more than 400 mA, replace U3 with a 5 V → 3.3 V buck (≈ 60 mA saved). That
  fallback is documented, not built, because a switcher adds in-band spurs.
- **L: pre-enumeration draw (≈ 260 mA) exceeds USB's 100 mA.** This is an accepted risk (SPEC P2). Gateware can
  hold the ADC in STPD until the host configures, cutting about 70 mA, but it will still exceed 100 mA.
- **H→mitigated: ADS5231 abs-max |AVDD − VDRV| ≤ 0.3 V** (SBAS295A p. 2). The mitigation is decided: VDRV
  (ADC_VDRV) comes from **VA_3V3 through FB5**, not from VD_3V3, so both pins track one regulator through every
  ramp. The ADC's 3.3 V output levels still match the FPGA's 3.3 V banks.
- **M: LM27762 switches at 2 MHz, inside the 0–5 MHz passband.** Its 2 and 4 MHz spurs reach the buffers.
  Mitigation: integrated LDOs, then FB3/FB4 + 10 µF π-filters, then OPA354 PSRR. Target: spur < ½ LSB
  (≈ 0.25 mV at the ADC). [VERIFY on first boards with an FFT of a grounded input.]
- **L: VBUS droop.** U3 needs ≥ 3.6 V in at 217 mA (TLV1117LV dropout ≈ 0.3 V). With a 4.40 V worst-case USB
  corner minus about 0.1 V across FB1 + U2, there is about 0.7 V of margin.
- **L: inrush.** Keep ≤ 10 µF ahead of U2 (C1 4.7 µF + U1). Everything downstream charges through U2's
  soft start.

## 2. Thermal (0–50 °C ambient, M3)

| Part | Dissipation (worst) | Package | Rise est. | Tj @ 50 °C |
|---|---|---|---|---|
| U3 TLV1117LV33 | (5.25 − 3.3) × 0.217 = 0.42 W | SOT-223 + copper pour | ~35 °C | ~85 °C ✔ |
| U6 TPS7A2033 | (5.25 − 3.3) × 0.115 = 0.22 W | SOT-23-5 | ~40 °C | ~90 °C ✔ (give it copper) |
| U4 AP2112K-1.2 | 2.1 × 0.08 = 0.17 W | SOT-23-5 | ~35 °C | ~85 °C ✔ |
| U12 ADS5231 | ≈ 0.32 W | TQFP-64 | ~20 °C | ~70 °C ✔ |

Board total ≈ 1.8 W worst. No heatsinks. **PKG: U3 must stay SOT-223 or larger.**

## 3. Analog / signal-chain

- **M: anti-aliasing is only 2nd order.** Poles at 7.2 MHz and 7.2 MHz put −3 dB at about 4.6 MHz. With 20 MSPS
  oversampling, the alias band that folds into 0–5 MHz is 15–25 MHz, attenuated 14.5–20 dB. The FPGA
  half-band decimator must remove 5–15 MHz. At a plain 10 MSPS (the fallback clock) the 5–15 MHz band would
  be attenuated only about 4–10 dB, which is why the 20 MSPS mode was chosen. Signals above 15 MHz at the
  BNC alias at about −15 dB. This is scope-like behaviour and is accepted. Option: lower Cf/Cdiff for
  6 MHz poles (−3 dB 3.9 MHz, still ≥ 3 MHz).
- **M: F10 gain error.** ADS5231 reference error is ±1 % typ but **±3.5 % max** (SBAS295A p. 4), which exceeds
  the 2 % uncalibrated target in the worst case. The ±10 V range is placed at 89.5 % FS, so even −3.5 %
  plus resistor tolerance never clips ±10 V. Software per-board calibration (SPEC-assumed) closes the gap.
- **M: attenuator compensation needs a one-time trim.** VC1/VC2 are adjusted with a 1 kHz square wave, as
  with probe calibration. Untrimmed, the HF/LF gain mismatch is ≤ ±5 %.
- **M: BNC ESD has no primary TVS.** A TVS rated for the ±50 V survival spec (F9) would add ≥ 50 pF and break
  15–25 pF (F7). Instead, protection comes from the 906 kΩ series element (fault current ≤ 55 µA at 50 V),
  the C30/C31 capacitive divider, BAV199 clamps to ±2.5 V, and R13 1 kΩ into the op-amp. Residual risk:
  direct 8 kV contact discharge on the centre pin. Layout may add a spark-gap pad at J2/J3.
- **L: overload recovery.** When the tap clamps, the THS4521 inputs are pulled ≈ 0.4 V below its NRI limit
  (V− − 0.1 V), and the current is limited to < 1 mA by the 1.1 kΩ Rg. Recovery time is uncharacterised.
  [VERIFY on bench.]
- **L: offset.** OPA354 Vos ≤ 8 mV maps to ≤ 80 mV at the BNC (0.4 % FS), which meets F10 (≤ 1 %).
  Input bias 3 pA × 90 kΩ is negligible.
- **L: noise.** Front-end noise ≈ 32 µV rms at the ADC (0.07 LSB) plus ADC noise ≈ 0.42 LSB gives a total of
  about 0.43 LSB rms (F10 ≤ 1 LSB ✔).

## 4. Clock / timing

- **L: jitter budget.** ENOB ≥ 10 at 1 MHz allows ≈ 117 ps rms total; a full-scale 5 MHz input allows
  ≈ 23 ps. ADS5231 aperture jitter is 1 ps, and a CMOS XO is typically a few ps. **X1 must be specified
  ≤ 5 ps rms jitter.** [VERIFY the X1 datasheet; the SCTF listing gives no jitter figure.]
- **L: ADC → FPGA capture.** At 20 MSPS, setup is ≥ 10 ns and hold ≥ 20 ns (SBAS295A timing table). The
  capture clock is the same XO edge (ADC_CLK_FPGA), with skew < 1 ns, so there is ample margin.
- **M: FT232H 60 MHz sync FIFO.** The CLKOUT → GCLKT_3 (pin 52) placement is fixed. Keep the FT bus ≤ 50 mm,
  on one layer, over unbroken GND. Gateware must meet FT232H setup/hold (DS_FT232H §4.4).
- **M: streaming (SOFT F13) is best effort.** 30 MB/s packed is 75 % of FT232H's 40 MB/s ceiling. It is
  achievable only on hosts that sustain ≥ 32 MB/s bulk-in; the 8 MB PSRAM FIFO rides out stalls up to about
  280 ms. **Block capture (HARD) does not depend on host throughput.**

## 5. EMI

- The FT232H 60 MHz bus, 480 Mb/s USB, and 24 ADC outputs toggling at 20 MHz are the emitters. The 33 Ω arrays
  RN1–RN7 at the ADC pins limit edge rates and ground-bounce kickback into the ADC. R66 series-terminates
  FT_CLKOUT.
- The USB pair is 90 Ω differential with no stubs, and U1 sits at J1. The shield is bled through R4/C4, not
  hard-grounded.
- The XO output is series-terminated at the source (R57/R58).

## 6. Layout (for the out-of-scope layout phase; the schematic must allow it)

- 4-layer: L1 components/signals, L2 solid GND (never split), L3 power islands (VA_3V3 / VD_3V3 / VD_1V2 /
  VD_1V8 / ±2.5 V), L4 signals.
- Floor plan, left to right: BNC → AFE → ADC → FPGA → FT232H → USB-C. Put the LM27762 and all digital parts
  on the far side of the ADC from the AFE. Place U7 ≥ 20 mm from the AFE, with a tight flying-cap loop.
- The high-Z nodes BNC_x / AFE_x_TAP get guard traces to GND, no digital routing underneath, and the 1206
  attenuator resistors at the BNC.
- U15 QFN-88 at 0.4 mm pitch plus EPAD is within JLC 4-layer capability; the EPAD needs ≥ 9 ground vias.
- Bank-3 nets are 1.8 V. Never tie them to 3.3 V parts except through U16/U17.

## 7. Programming / debug

- **M: JTAG is 1.8 V** (QN88P bank 3 is fixed at 1.8 V). A fixed-3.3 V JTAG cable would over-drive bank 3.
  J4 pin 1 carries VREF = 1.8 V; use a VREF-following adapter (Gowin USB cable, or a Tigard/FT2232H
  adapter set to 1.8 V with openFPGALoader). No on-board JTAG translator is fitted; that is decided, since
  it would cost four more parts for a one-time-per-user issue.
- FT232H EEPROM (U14) is programmed over USB itself (FT_Prog/libftdi). No header is needed; USB is its
  programming port. This satisfies I6.
- The ADS5231 registers are written by the FPGA at run time; the pull-downs give a valid default mode with the
  FPGA unconfigured.

## 8. Sourcing (constrains the part-sourcer)

- **H: ADS5231IPAGT is single-source**, with stock 160–235 and lifecycle unchecked. Buy for all boards at once.
  There is no drop-in second source; the fallback is 2 × AD9235BCPZ-40, which means an architecture rework.
- **H: GW1NR-LV9QN88PC6/I5 is single-source**, with stock 182 (WARN). The pin plan is bound to QN88P, so it
  cannot be substituted without rework. No other GW1N(R)-9 is stocked.
- **M: KiCad symbols are missing** for ADS5231, GW1NR-9, OPA354, TPS7A2033, and SY6280AAC; the datasheet phase
  must generate them. BAV199's `find-symbol` hit (Diode:BAV19) is **wrong** and must be regenerated or mapped
  to a verified series-pair symbol.
- **L:** about 25 Extended-tier parts add JLC loading fees (≈ $75 per order).
