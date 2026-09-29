# Design risks — dual_adc_usb (revision 1)

## 1. Power budget and the USB 2.0 vs USB-C rule
Inputs come from datasheet typ/max values where they are known. Values marked (est.) are unverified estimates. Efficiencies: bucks 90 %/85 % (3V3D), 80 %/75 % (1V2). Linear loads draw their output current from V5 at 5.0 V typ / 5.25 V max.

| Rail (source) | Loads (typ / max mA) | Rail I typ / max | P from V5 typ / max |
|---|---|---|---|
| V3V3A (TPS7A2033 LDO) | ADS5231 AVDD 71.4/82.1 (235.5/271 mW ÷ 3.3); VDRV 25.9/33.0 (85.5/109 mW ÷ 3.3); THS4551 ×2 2.8/3.84; XO 10/20; misc 0.1/0.2 | 110.2 / 139.1 mA | 5.0 × 110.2 → 551 mW / 5.25 × 139.1 → 730 mW |
| VP_AFE + VN_AFE (LM27762) | OPA356 ×2 per rail: (8.3 + 1 load) × 2 → 18.6 / (11 + 2) × 2 → 26 mA per rail; IQ 1/2 (est.) | VIN 38.2 / 54 mA | 5.0 × 38.2 → 191 mW / 5.25 × 54 → 284 mW |
| V3V3D (TLV62569 buck) | FT232H 60/80 (est.); FPGA VCCX+VCCIO 20/45 (est.); V1V8 LDO pass-through 25/60 (est., PSRAM); EEPROM 0.5/1; LEDs 3.9; pull-ups 0.5/1 | 109.9 / 190.9 mA | 3.315 × 109.9 / 0.90 → 405 mW / 3.381 × 190.9 / 0.85 → 759 mW |
| V1V2 (TLV62569 buck) | GW1NR-9 core 50/150 (est.) | 50 / 150 mA | 1.2 × 50 / 0.80 → 75 mW / 1.224 × 150 / 0.75 → 245 mW |
| Load switch loss | 0.40² × 0.09 Ω | — | 0 / 14 mW |
| **Total** | | | **1.22 W typ / 2.03 W worst case** |

The worst-case VBUS current at 4.75 V is 139.1 + 54 + (759 + 245)/4.75 → **404 mA**, which is under 500 mA.

**Rule applied:** the typical draw of 1.22 W fits USB 2.0. The worst case, 2.03 W, is above the user's ~2.0 W threshold, and the FPGA and FT232H figures are estimates. **The board therefore gets a USB-C receptacle** (TYPE-C-31-M-12, USB 2.0 D+/D− only, Rd = 5.1 kΩ on CC1 and CC2).
- Because the worst-case current is 404 mA < 500 mA, the board still runs from a legacy USB 2.0 Type-A port through an A-to-C cable.
- A USB-C source gives ≥ 1.5 A headroom if the real FPGA power comes in above the estimate.
- Phase 4 must replace the (est.) rows with the Gowin power-estimator result and FT232H datasheet currents.

## 2. Signal integrity and front-end accuracy
- **Anti-alias filter (4 poles, 4 distinct nodes).** The poles are:
  - R_S·C_S on node A_BUF_IN: 1k × 8.2p → 19.4 MHz.
  - The MFB 2-pole: C1 counted as 2 × 27 pF per half-circuit, C2 12 pF, R2 909, R3 499, R1 1k. f0 = 1/(2π√(909 × 499 × 54p × 12p)) → 9.28 MHz; Q = ω0·C1/(1/R1 + 1/R2 + 1/R3) → 0.767.
  - The output RC on the AIN pins: 2 × 49.9 Ω with 56 + 3 pF → 27.0 MHz.

  The node-analysis model (finite GBW 135 MHz) gives the end-to-end response from BNC to ADC:

  | Frequency | Response |
  |---|---|
  | 1 MHz | −0.02 dB |
  | 4 MHz | −0.32 dB |
  | 5 MHz (top of 10 MSa/s band) | −0.58 dB |
  | 8.86 MHz | −3 dB |
  | 35 MHz (alias edge, 40 − 5) | −32.1 dB |
  | 39 MHz | −35.4 dB |

  There is no peaking, and C1/C2 at ±5 % keeps peaking < 0.01 dB. **Residual risk:** out-of-band content at 35–40 MHz aliases into 0–5 MHz with only 32–35 dB rejection. The FPGA decimator removes 5–20 MHz but cannot remove what has already aliased. It is acceptable for probe-bandwidth signals and documented as a spec limit.
- **Delivered bandwidth.** At the 10 MSa/s output the decimation FIR sets the band: pass 0–4 MHz with ≤ 0.1 dB ripple after analog-droop equalization, −3 dB ≈ 4.5 MHz, stop ≥ 60 dB from 6 MHz. A raw 40 MSa/s mode delivers the full 8.9 MHz analog band (depth 8 MiB ÷ (2 × 2 B × 40 M) → 0.05 s).
- **Compensated divider.** It needs R_T·C_T = R_B·C_B, i.e. C_B = 200.0 pF. The trimmer (16.5–33 pF) takes up tolerance, but only if the ±1 % C0G parts are used. With ±5 % parts the trim range can run out. Adjust with a 1 kHz square wave at test (factory step).
- **ADC input CM** must be VCM ± 50 mV. The THS4551 VOCM is driven from U8.CM (pin 52), and the VOCM offset of ±12 mV fits.
- **FS and gain:** gain 0.09009 V/V, FS ±11.21 V, LSB 5.47 mV. ADC gain error (±3.5 %) plus resistor tolerance still gives an FS ≥ 11.21 × (1 − 0.035 − 0.03) → 10.48 V > 10 V ✓. Gain and offset are calibrated in host software.
- **Overvoltage (±30 V):** 30 × 0.09911 → 2.97 V at A_DIV. The clamps (BAV199 to +3.29/−2.01 V) hold the node within about −2.5…+3.8 V. Fault current is 30/909k → 33 µA. R_S 1 kΩ limits current into OPA356 ESD cells to < 0.1 mA. R_T dissipates 30²/909k → 1 mW. C_T must be rated ≥ 100 V.
- **ESD at BNC:** there is no TVS, because TVS leakage times a 10× probe's 9 MΩ would cause volt-level error. The 1206 R_T, the C0G ≥ 100 V C_T and the clamps into bypassed rails carry the ESD. This is a prototype-level risk.

## 3. Timing and clocking
- **ADC clock jitter ≤ 3 ps rms** (80.5 dB SNRj at 5 MHz). The XO drives the ADC directly. It must never pass through the FPGA or its PLL (50–100 ps → ≤ 50 dB).
- **ADS5231 PLL mode needs a 20–40 MSPS clock with 45–55 % duty.** Verify the XO duty cycle in phase 4.
- The ADC data-capture phase into the FPGA (6-clock latency, DVA output) must be timing-closed in HDL. Use a PLL phase shift on FPGA_CLK, or capture on ADC_DVA.
- **FT232H sync FIFO at 60 MHz:** keep FT_* traces ≤ 50 mm and length-matched ±5 mm to FT_CLKOUT. FT_CLKOUT must land on a GCLK pin.
- USB_DP/DN: route as a 90 Ω differential pair, ≤ 50 mm, no stubs, with U1 at the connector.

## 4. Power integrity and thermal
- **TPS7A2033 dissipation:** (5.25 − 3.3) × 0.139 → 0.27 W. At ~200 °C/W (SOT-23-5, est.) that is +54 °C, so TJ ≈ 104 °C at 50 °C ambient, under the 125 °C limit. Give it a copper pour of ≥ 2 cm². If phase 4 finds θJA > 250 °C/W, move X1 (20 mA) to V3V3D behind FB2.
- LM27762 PD = 5.25 × (26 + 26 + 2) mA − (3.380 × 26 + 2.058 × 26) mA → 0.142 W. That is fine.
- ADS5231: 0.38 W max at θJA 42.8 °C/W → +16 °C.
- **Inrush:** 4.7 µF sits before U2. Everything downstream (> 100 µF) charges through TPS22919's controlled rise.
- ADS5231 |AVDD − VDRV| < 0.3 V abs max is guaranteed by feeding VDRV from V3V3A through FB1. Never feed VDRV from V3V3D.
- LM27762 is a 2 MHz charge pump. Keep C14/C15 loops tight and away from A_DIV/A_BUF_IN. The buffer's PSRR at 2 MHz is modest, so add 0.1 µF right at U101/U201.

## 5. Layout
- 4-layer (SIG / GND / PWR / SIG). One continuous GND plane.
- The analog region (J2/J3 → U8) sits on one side, the digital region (U9, U10, J1) on the other, and U8 straddles the boundary with its digital outputs facing U9.
- The A_DIV node is high-impedance (100 kΩ ‖ 200 pF). Guard it with a GND ring, keep it free of solder mask slivers, and keep 1 MΩ leakage paths away. It is sensitive to board contamination (clean after assembly).
- GW1NR-9 QN88 has a 0.4 mm pitch, and its exposed pad goes to GND.

## 6. FPGA-specific
- **Bank 3 is 1.8 V** (VCCIO3 feeds the PSRAM). JTAG runs at 1.8 V, so the programming cable must support a 1.8 V VREF. No 3.3 V signal may land on bank 3.
- The 3.3 V I/O budget is tight: 44 used of ≈ 48. OVRA, OVRB and DVB were dropped for that reason.
- MODE0/MODE1 strap values for AUTOBOOT come from UG290/UG803 and are unverified.
