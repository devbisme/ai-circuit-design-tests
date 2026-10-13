# Dual-channel 12-bit 10 Msps USB ADC — design notes

## Requirements and the numbers derived from them
| Requirement | Derived figure |
|---|---|
| 2 channels, 12 bit, 10 Msps | 2 × 10 M × 16 bit words = **40 MB/s** raw (30 MB/s if 12-bit packed) |
| ≥ 0.1 s at full rate | 2 M samples × 2 bytes = **4 MB** minimum buffer |
| ±10 V input | Attenuate by about 10 to fit a 2 Vpp differential ADC span |
| Scope-lead connectors | BNC, 1 MΩ input, about 10–20 pF (so 10x probes can be compensated) |
| USB 2.0 for power and data | 2.5 W (500 mA) after enumeration. HS bulk throughput is about 35–40 MB/s, which is marginal for streaming at 40 MB/s, so samples are buffered on the board |

## Decisions (options considered → choice)
1. **ADC**
   - Options:
     - LTC2290 (dual 12-bit 10 Msps, parallel CMOS)
     - two single-channel ADCs (e.g. AD9226 class)
     - LTC2292 (dual 40 Msps) with decimation in the FPGA
     - a serial-LVDS ADC
   - **Chosen: LTC2290.** It is one part with matched channels, it is in the KiCad library, and it has a low-power 3 V supply.
   - LTC2292 is pin-compatible, so it is the upgrade path if the board should oversample to ease anti-aliasing.
2. **Capture logic**
   - Options:
     - MCU (no MCU can take 2 × 12-bit parallel buses at 10 MHz into external RAM)
     - FX2LP + CPLD
     - FPGA + SDRAM
     - FPGA with on-chip PSRAM (GW1NR-9; not in the KiCad library)
   - **Chosen: iCE40HX4K-TQ144 + MT48LC16M16A2 (32 MB).** The FPGA is in a non-BGA package, has 107 I/O, and is supported by an open-source toolchain. 32 MB holds about 1.6 s (16× the requirement).
3. **USB bridge**
   - Options:
     - FT232H in 245 synchronous FIFO mode (up to about 40 MB/s)
     - FT2232H
     - FX2LP (needs firmware)
     - USB 3 bridge (FT601; not needed)
   - **Chosen: FT232H**, configured into synchronous FIFO mode by a 93LC56B EEPROM.
4. **Connector and power**
   - Estimated load: about 265 mA at 5 V.
     - 3.3 V digital rail: about 200 mA through a buck converter.
     - FT232H: about 55 mA.
     - ADC: about 40 mA.
     - Analog stages: about 20 mA.
   - This is below the 500 mA a USB 2.0 port supplies, so a **USB-B** connector is used; USB-C was not required by the prompt's rule.
   - Before enumeration the ADC is held in shutdown by a pull-up, and the FPGA enables it only on host command, to stay near the 100 mA limit for an unconfigured device. That pre-enumeration current is an estimate and has not been measured.
5. **Analog front end** (per channel)
   - Input stage: BNC → 909 k ‖ 15 pF over 100 k ‖ (120 pF + 5–30 pF trimmer). Input is 1.009 MΩ ‖ about 13.5 pF.
   - Protection and buffer: BAV99 clamp to ±5VA → 1 k → OPA810 FET-input buffer.
   - Driver and filter: THS4521 fully-differential amplifier as a 2-pole multiple-feedback (MFB) low-pass (f0 3.2 MHz, Q 1, gain 0.953). An output 2 × 49.9 Ω / 470 pF pole follows, giving roughly a 3rd-order Butterworth response.
   - Scaling: ±10 V maps to ±0.944 V differential; full scale is ±10.59 V (5 % headroom).
   - Options considered:
     - Single-supply level-shift attenuator: rejected because the offset network complicates compensation.
     - Driving the ADC single-ended: rejected because of worse distortion.
     - Oversampling with an FPGA filter: noted as an upgrade.
   - Calculations: `scripts/filter_design.py`.
6. **Clocks**
   - A dedicated 10 MHz XO (powered from +3.3VA) drives the ADC; a separate series resistor sends a copy to an FPGA global-buffer input.
   - A 50 MHz XO is the FPGA system clock (its PLL makes the SDRAM clock).
   - The FPGA PLL is not used for the ADC clock because its jitter (hundreds of ps) would limit SNR below 12 bits at MHz input frequencies.
7. **FPGA configuration**
   - Options:
     - SPI flash plus a programming header
     - host configures the FPGA through the FT232H's MPSSE mode at each power-up
     - flash shared with the FT232H bus
   - **Chosen: W25Q32 flash plus a 2×5 header** (iceprog-style). Field updates can be done through FPGA gateware afterwards.
   - Rejected: sharing the flash with the FIFO bus risks spurious flash commands; FPGA-side MPSSE configuration needs mode juggling at boot.
8. **PCB**
   - Stackup: 4 layers. F.Cu signals, In1 solid GND, In2 split (+3V3 under the digital area, GND under the analog area), B.Cu signals plus decoupling.
   - Size: 128 × 85 mm. Signal flow left to right: BNC → front end → ADC → FPGA → SDRAM, with the FT232H and USB-B below the FPGA.

## Power tree
USB VBUS → 0.5 A polyfuse → +5V, which feeds:
- TLV62569 buck → +3V3 (digital). From +3V3, a TLV73312 LDO → +1V2 (FPGA core).
- LP5907 LDO → +3.3VA (ADC VDD, 10 MHz XO).
- Ferrite → +5VA (OPA810 and THS4521).
- TPS60403 charge pump → −5V, then ferrite → −5VA (OPA810 negative rail, clamp).
- FT232H VREGIN (its internal LDO makes its own 3.3 V and 1.8 V).

## Risks and open items (not verified against datasheets in this session)
- **Aliasing at 10 Msps.** Filter response: −2.8 dB at 3.2 MHz, −11.7 dB at 5 MHz, −29 dB at 10 MHz. Out-of-band content between 5 and 15 MHz will alias.
  - Usable bandwidth is about 3 MHz.
  - Fix if needed: LTC2292 at 40 Msps plus decimation, which has the same footprint.
- **FT232H power pins.** VCCD/VPHY/VPLL wiring (VREGIN = 5 V, VCCD 3.3 V output feeding VPHY/VPLL, VCCIO from +3V3) is from memory of FTDI's bus-powered example. Check it against DS_FT232H.
- **Strapping details to check:**
  - THS4521 pin 4 = VOUT+ and pin 5 = VOUT− (this sets the overall polarity).
  - LTC2290 MODE = VDD/3 (offset binary, duty-cycle stabilizer on), MUX = VDD, SENSE = VDD (2 Vpp span).
  - iCE40 VPP_FAST tied to 3.3 V.
- **Inrush.** About 15 µF hangs directly on +5V/VBUS, above the USB 10 µF guideline. Add a soft-start load switch if hosts complain.
- **BAV99 clamp leakage.** At about 90 kΩ node impedance, nA of leakage gives mV of offset. This is calibratable but temperature dependent; a lower-leakage clamp (e.g. BAV199 or a JFET clamp) would be better.
- **USB enumeration current.** Assumes FPGA configuration plus an idle SDRAM stays under 100 mA. Not measured.
- **Gateware and host software** are not part of this deliverable.
