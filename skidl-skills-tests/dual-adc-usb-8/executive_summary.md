# Executive Summary — dual_adc_usb

**Result:** a 2-channel board that samples ±10 V inputs at 12 bits and 10 MSa/s, stores ≥ 0.1 s of samples per channel, and connects to the host over USB-C (USB 2.0 High-Speed data).

- 170 parts and 129 nets.
- ERC: 0 errors. Footprints and BOM checked.
- **Not yet laid out or built.** No FPGA logic or host software.
- Equivalent API cost: $26.36. About 17 % of that was rework.

**Method:** a 6-phase pipeline driven from the main thread.

- Each phase ran as an isolated agent. It passed its results to the next phase only through handoff files on disk.
- Each phase ended with a check of its handoff file.
- The prompt said not to pause for input. So at every decision the options were listed, and the recommended one was chosen and recorded.

---

## 1. Requirements (main thread)
- Wrote `SPEC.md` from the prompt:
  - 7 **hard** constraints.
  - 6 **soft** constraints chosen by the driver and marked as such: 1 MΩ probe-compatible input, ≥ ±30 V survival, capture-then-upload, SMD, JLCPCB assembly, 0–50 °C.
- Recorded the user's power rule: use USB-C if the design draws more than the USB 2.0 budget.
- Recorded the blank-slate rule: no reuse of other designs, part cache off.

## 2. Architecture

### Functional blocks
| # | Block | Function |
|---|---|---|
| 1 | `usb_power_in` | USB-C receptacle, ESD protection, soft-start load switch → V5 |
| 2 | `power_digital` | 3.3 V and 1.2 V bucks, 1.8 V LDO for the FPGA |
| 3 | `power_analog` | 3.3 V low-noise analog LDO, plus bipolar rails for the front end |
| 4 | `afe_ch_a` | Channel A: BNC → attenuator → buffer → anti-alias driver → ADC |
| 5 | `afe_ch_b` | Channel B: same as A |
| 6 | `adc` | Dual 12-bit ADC |
| 7 | `clock` | 40 MHz oscillator, one output to the ADC and one to the FPGA |
| 8 | `fpga` | Capture engine: decimation, trigger, sample buffer, USB FIFO interface |
| 9 | `usb_bridge` | USB 2.0 High-Speed ↔ 8-bit parallel FIFO bridge |

### Criteria and decisions by block

**USB power input**
- *Criteria:* the user's power rule; controlled inrush; ESD on the data lines.
- *Decisions:*
  - The power budget is 1.22 W typical and 2.03 W worst case. That exceeds the ~2.0 W threshold, so the board uses a **USB-C receptacle** with 5.1 kΩ Rd on CC and no PD controller.
  - Worst-case current is ~425 mA, under 500 mA, so the board still works from a legacy USB 2.0 port.
  - A **TPS22919** load switch provides soft start, and a **USBLC6-2SC6** provides ESD protection.

**Digital power**
- *Criteria:* run from VBUS as low as 4.4 V; efficiency; FPGA core and bank voltages.
- *Decisions:*
  - 2 × **TLV62569** bucks make 3.3 V and 1.2 V. The TPS563201 was rejected because its 4.5 V minimum input is above the VBUS minimum.
  - A **TLV75518** LDO makes 1.8 V for the FPGA's memory bank.

**Analog power**
- *Criteria:* low noise for the ADC and front end; the buffer's input range must cover the full signal swing.
- *Decisions:*
  - A **TPS7A2033** makes 3.3 V analog (6.5 µVrms noise).
  - An **LM27762** makes **asymmetric +3.29 / −2.01 V** buffer rails. Symmetric ±2.5 V rails would violate the OPA356's input-range limit at the ±1.11 V signal peak.
  - Total rail span is ≤ 5.44 V, within the 5.5 V absolute maximum.

**Analog front end, ×2**
- *Criteria:* ±10 V full scale; 1 MΩ input so standard scope probes compensate correctly; anti-alias filtering; overvoltage protection; low offset.
- *Decisions:*
  - **Compensated divider:** 909 kΩ / 100 kΩ gives ≈ 1 MΩ ‖ 20 pF, with a hand trimmer for flatness. The trimmer was later changed from a voltage-tuned part to a **Knowles JZ300**.
  - **BAV199** low-leakage clamp diodes.
  - **OPA356** unity-gain buffer. The OPA357 was rejected because its input-stage crossover region starts too close to the signal peak.
  - **THS4551** fully differential driver in a 2-pole filter (f0 9.28 MHz, Q 0.77).
  - Full scale is ±11.2 V, LSB 5.47 mV.
  - −3 dB at 8.86 MHz, −32 dB at the 35 MHz alias frequency.
  - **Bandwidth target relaxed:** 5 MHz up to Nyquist is incompatible with anti-aliasing. The 10 MSa/s output passes 0–4 MHz.

**ADC**
- *Criteria:* 12 bits; simultaneous sampling of both channels; stock ≥ 100; cost.
- *Decisions:*
  - Chose the **ADS5231**, a dual 40 MSPS ADC on a single die. It gives inherent channel matching and costs $30, against $50–65 for two single-channel ADCs.
  - Its minimum rate is 20 MSPS, so it **oversamples at 40 MSa/s** and the FPGA decimates ×4 to 10 MSa/s. This also relaxes the anti-alias filter.
  - Runs in parallel-pin mode with the internal reference. Its output-driver supply comes from the analog 3.3 V rail, as its absolute-maximum ratings require.
- *Risk:* single source.

**Clock**
- *Criteria:* jitter ≤ 3 ps RMS, which keeps the SNR loss to 0.4 dB at 5 MHz.
- *Decisions:*
  - The ADC is clocked **directly from the 40 MHz oscillator**. The FPGA's PLL is kept out of the ADC clock path because its ~50–100 ps jitter would limit SNR to about 50 dB.
  - The FPGA gets a separate 33 Ω-buffered branch from the same oscillator.
- *Risk:* the chosen oscillator's datasheet gives no jitter spec.

**FPGA capture engine**
- *Criteria:* ≥ 4 MB of buffer; 24-bit parallel ADC input; DSP for decimation; no BGA; low part count.
- *Decisions:*
  - Chose the **GW1NR-9 (QN88P)**. It has 8 MB of memory in the package, enough for 0.21 s, plus internal configuration flash and 20 multipliers.
  - Rejected:
    - GW2AR-18: 2.4× the cost.
    - ECP5 + SDRAM: BGA, an external memory chip and a flash.
    - MCU with camera interface: that interface is ≤ 14 bits wide, and 24 are needed.
  - All 48 of its 3.3 V I/O pins are used.
  - The trigger is software start, plus a digital level/edge trigger and external TRIG_IN/TRIG_OUT on a header.

**USB bridge**
- *Criteria:* USB 2.0 High-Speed; no firmware; few FPGA pins.
- *Decisions:*
  - Chose the **FT232H** in synchronous FIFO mode: ~35 MB/s, 15 FPGA pins, no firmware.
  - Capture first, then upload: 4 MB takes ~0.11 s.
  - Rejected:
    - FX2LP: needs firmware and more pins.
    - FT601: needs 32 data pins.
  - Later changed to run from **5 V**, as in Adafruit's open-source FT232H board.

**Board-level decisions**
- 4-layer board.
- Single ground plane.
- SMD parts, except through-hole BNCs and headers for mechanical strength.

## 3. Sourcing (1 full run + 3 fix passes)
- Found an in-stock JLCPCB part for all 164 original components, with live stock checks.
- Rejected a wrong symbol the lookup tool had matched automatically (BAV19 for BAV199).
- Replaced a capacitor with only 37 in stock.
- Fix passes:
  - Replaced the voltage-tuned "trimmer" with a real hand trimmer (JZ300).
  - Corrected the EEPROM symbol.
  - Changed the FPGA MODE resistors to 1 kΩ.
  - Added VPHY/VPLL ferrite filters for the FT232H.
  - Brought 12 symbol, footprint and note entries into line with the code.

## 4. Datasheets (1 full run + 1 follow-up)
- Wrote 19 part summaries and collected 16 PDFs.
- Generated 7 KiCad symbols. 5 FPGA pin names were later corrected against Gowin's package file and the Tang Nano 9K board.
- Settled key facts from reference designs:
  - **FT232H power wiring**, from Adafruit's open-source schematic. The FTDI site blocked the datasheet download.
  - The **FPGA's memory bank** (1.8 V) and boot configuration.
- Still open, with named assumptions: the oscillator's jitter and the crystal's load capacitance.

## 5. Coding (5 work orders, one at a time, then the assembler)
- Wrote 9 SKiDL subcircuit files. Each block was syntax-checked and given a trial ERC.
- Created the custom BNC footprint and the FPGA pin map (`circuits/dual_adc_usb/fpga_pinmap.md`).
- The assembler joined the blocks: 0 errors, 6 warnings that are known symbol false alarms.
- The BOM-vs-code check caught 9 value-label mismatches; the code was edited to match the BOM.

## 6. ERC gate (2 runs)
- An independent re-check covered ERC, footprints, supply spans, signal levels, FPGA bank voltages, the filter response and the packages.
- **The first run failed:** the BNC footprint was mirrored. It was fixed, and the second run **passed**.

## 7. Review
- Skipped, since it would mostly repeat the ERC gate. `/design-review` is still available.

## 8. Export
- `outputs/dual_adc_usb.net` and `outputs/dual_adc_usb_bom.xml`, both produced by the run that passed the ERC gate.
- Ship `footprints/ProjectLocal.pretty/` with them, because J2/J3 use it.

---

## Open risks
- **FT232H:** the FIFO-mode pin mapping and the crystal's load capacitance are unverified against its datasheet.
- **FPGA:** the memory-bank and boot assumptions come from reference-design evidence, not a Gowin document. There is no spare 3.3 V I/O pin.
- **JTAG header:** its pinout and 1.8 V level are unchecked against the Gowin programming cable.
- **Oscillator:** no published jitter spec.
- **JZ300 trimmer:** its setting drifts about 0.3–1.5 pF over a 25 °C change.
- **BNC footprint:** custom-made; dry-fit a real connector before fabrication.
- **Stock:** low for the ADC (154), FPGA (173) and THS4551 (469), and the ADC has a single maker.
