# Executive Summary — dual_adc_usb

**Result:** a 2-channel board that samples ±10 V inputs at 12 bits and 10 MSa/s, stores ≥ 0.1 s of samples per channel (0.21 s), and connects to the host over USB-C (USB 2.0 High-Speed data and power).

- 169 parts and 131 nets.
- ERC: 0 errors, 0 warnings. Footprints and BOM checked against the code.
- **Not yet laid out or built.** No FPGA logic or host software.
- Equivalent API cost: see `claude_cost.txt` (≈ $21 at the end of the design pipeline). About 30 % of sub-agent tokens went to rework (5 of 16 sub-agent runs).

**Method:** a 6-phase pipeline driven from the main thread.

- Each phase ran as an isolated agent. It passed its results to the next phase only through handoff files on disk.
- Each phase ended with a check of its handoff file; from coding onward a script checked that the BOM matches the code.
- The prompt said not to pause for input. So at every decision the options were listed, and the recommended one was chosen and recorded.

---

## 1. Requirements (main thread)
- Wrote `SPEC.md` from the prompt:
  - 6 **hard** constraints.
  - 5 **soft** constraints chosen by the driver and marked as such: 1 MΩ probe-compatible input, DC coupling with ≥ 5 MHz bandwidth and anti-aliasing, ±50 V survival, SMD/4-layer/JLCPCB assembly, 0–70 °C.
- Recorded the user's power rule: use USB-C if the design needs more than the USB 2.0 budget (5 V, 500 mA).
- Recorded the blank-slate rule: no reuse of other designs, part cache off.

## 2. Architecture (1 run + 1 rework)

### Functional blocks
| # | Block | Function |
|---|---|---|
| 1 | `usb_power_in` | USB-C receptacle, PTC + TVS, ESD protection, soft-start load switch → VBUS_SW |
| 2 | `pwr_digital` | 3.3 V, 1.2 V and 1.8 V bucks |
| 3 | `pwr_analog` | 3.3 V analog LDO, plus ±3.4 V rails for the input buffers |
| 4 | `afe_ch_a` | Channel A: BNC → attenuator → buffer → anti-alias driver → ADC |
| 5 | `afe_ch_b` | Channel B: same as A (shared builder function) |
| 6 | `adc_dual` | Dual 12-bit ADC |
| 7 | `clock_gen` | 40 MHz oscillator, direct to the ADC and buffered to the FPGA |
| 8 | `fpga` | Capture engine: decimation, trigger, sample buffer, USB FIFO interface |
| 9 | `usb_bridge` | USB 2.0 High-Speed ↔ 8-bit parallel FIFO bridge |

### Criteria and decisions by block

**USB power input**
- *Criteria:* the user's power rule; controlled inrush; ESD on the data lines.
- *Decisions:*
  - The power budget was estimated at 1.47 W typical, ≤ 1.84 W worst case, under the 2.5 W USB 2.0 budget, so the USB-C rule did **not** fire. A **USB-C receptacle** (USB 2.0 wiring, 5.1 kΩ Rd on CC) was chosen anyway for robustness and headroom on 1.5 A hosts; micro-B is a drop-in fallback.
  - A **TPS22918** load switch provides soft start (≈ 95 mA inrush into 48 µF), and a **USBLC6-2SC6** provides ESD protection. 0.75 A PTC and SMF5.0A TVS on VBUS.
  - The later FT232H change (§6) moves its 112 mA onto VBUS through a linear regulator; the worst case at 4.4 V becomes ≈ 412 mA, and the ×1.25 design-margin line ≈ 515 mA — see Open risks.

**Digital power**
- *Criteria:* run from VBUS as low as 4.4 V; efficiency; FPGA core and bank voltages; Gowin power-up order.
- *Decisions:*
  - 3 × **TLV62569** bucks make 3.3 V, 1.2 V and 1.8 V — one part number for all three. An LDO for 1.2 V lost on wasted power from the USB budget.
  - The **1.8 V rail was added in the rework**: the datasheet phase found that the FPGA's bank 3 feeds the in-package PSRAM and must be 1.71–1.89 V. A buck was chosen over an LDO because an LDO pushed the budget past 500 mA.
  - The 3.3 V buck's enable is delayed 2–3 ms by an RC, so the FPGA core and 1.8 V rails come up first.

**Analog power**
- *Criteria:* low noise for the ADC and front end; buffer rails wide enough for the clamp window.
- *Decisions:*
  - A **TLV75733P** LDO makes 3.3 V analog.
  - An **LM27762** (charge pump + ±LDOs) makes **+3.36 / −3.42 V** for the OPA810 buffers in one 2×3 mm part. A single-supply front end lost because the BNC would sit at a DC bias.

**Analog front end, ×2**
- *Criteria:* ±10 V full scale; 1 MΩ input so standard scope probes compensate; anti-alias filtering; overvoltage protection.
- *Decisions:*
  - **Compensated divider:** 910 kΩ / 100 kΩ gives 1.01 MΩ ‖ ≈ 20 pF, ÷10.1, with a 2–6 pF trimmer for flatness.
  - **BAV199** low-leakage clamp to the ±3.4 V rails; ±50 V gives 51 µA of clamp current.
  - **OPA810** FET-input unity buffer (2 pA bias). The OPA356 lost on its 5.5 V supply limit.
  - **THS4521** fully differential driver in a 2-pole MFB filter (f0 8.84 MHz, Q 0.99) plus a 33 Ω / 270 pF output pole → 3rd order. The THS4551 lost on price and package.
  - Full scale ±11.22 V, LSB 5.48 mV.
  - −3 dB at 8.8 MHz, −0.16 dB at 5 MHz, −36 dB at the 35 MHz alias edge (ideal-amplifier model). The notebook's finite-GBW model shows ≈ 0.35 dB in-band peaking instead of droop.

**ADC**
- *Criteria:* 12 bits; simultaneous sampling of both channels; stock ≥ 100; cost.
- *Decisions:*
  - Chose the **ADS5231**, a dual 40 MSPS ADC on one die: inherent channel matching, $30 against $37–50 for two AD9235s.
  - Its minimum rate is 20 MSPS with the PLL on, so it **oversamples at 40 MSa/s** and the FPGA decimates ×4. This is also what makes an analog anti-alias filter practical: sampling at 10 MSa/s would leave no transition band.
  - The **data-valid and over-range outputs were dropped in the rework** to free FPGA pins; capture uses a phase-shifted FPGA clock, and over-range shows as saturated codes.
- *Risk:* single source, stock 235.

**Clock**
- *Criteria:* jitter ≤ 5 ps RMS (SNR ≥ 76 dB at 5 MHz).
- *Decisions:*
  - The ADC is clocked **directly from the 40 MHz oscillator**; the FPGA gets a separately buffered branch. The FPGA PLL stays out of the ADC clock path.
  - **Oscillator swapped in the rework** to the YXC OT322540MJBA4SL, which publishes 0.7 ps max. The first pick published no jitter figure.

**FPGA capture engine**
- *Criteria:* ≥ 4 MB of buffer; 24-bit parallel ADC input; multipliers for decimation; no BGA.
- *Decisions:*
  - Chose the **GW1NR-9 (QN88P)**: 8 MiB PSRAM in the package (0.21 s at 10 MSa/s), on-chip config flash, 20 multipliers.
  - Rejected: Spartan-6 + SDRAM (external memory, flash, legacy tools), iCE40 (out of stock, no multipliers), MCU with camera interface (≤ 14-bit input, DMA contention).
  - **Only 48 pins are 3.3 V-capable, against 53 planned.** Dropped ADC DV/OVR (4 pins) and tied FT232H SIWU# high (1 pin). Tying ADC_OEB low is the reserve pin.
  - JTAG and config pins sit on the 1.8 V bank, so the JTAG header references 1.8 V.

**USB bridge**
- *Criteria:* USB 2.0 High-Speed; no firmware; few FPGA pins.
- *Decisions:*
  - Chose the **FT232H** in synchronous FIFO mode: 30–40 MB/s, 15 FPGA pins (14 after SIWU#), no firmware. FX2LP lost on firmware; FT2232H's second channel is unusable in this mode.
  - Capture first, then upload: 4 MB takes 0.10–0.13 s. Streaming would need 40 MB/s sustained.

**Board-level decisions**
- 4-layer board, single solid ground plane.
- SMD parts, except through-hole BNCs and headers.

## 3. Sourcing (1 full run + 2 fix passes)
- Found an in-stock JLCPCB part for all 163 original components; 26 Basic, 2 Preferred, 31 Extended rows. Every IC is Extended.
- Rejected a wrong symbol the lookup tool had matched (BAV19 for BAV199).
- Fix passes:
  - Re-sourced the oscillator, the 33 pF crystal load caps and the 1.8 V divider after the architecture rework; added 6 refs to existing rows.
  - No stocked BNC matched a stock KiCad footprint, so a **custom footprint** was drawn for the KH-BNC50-3511 from its datasheet drawing.

## 4. Datasheets (1 full run + 1 narrow follow-up)
- Wrote 13 part summaries and collected PDFs for all 10 keystone parts.
- Generated 3 KiCad symbols with the kipart CLI (the kipart MCP server was down): ADS5231, GW1NR-9 QN88P, TPS22918.
- **Found the two architecture blockers** (1.8 V PSRAM bank; 48 vs 53 3.3 V pins) before any code was written, which sent the design back to the architect.
- Verified 7 of 10 keystone facts. Still open, carried as named assumptions: PSRAM controller throughput (K3), FPGA core current (K5), 1.8 V load (K10), exposed pad = GND.

## 5. Coding (5 work orders, one at a time, then the assembler)
- Wrote 9 SKiDL subcircuit files plus a shared AFE builder. Each block was syntax-checked and given a trial ERC.
- The assembler joined the blocks: 0 errors, 0 warnings.
- The BOM-vs-code check caught 10 value-label mismatches; the code was edited to match the BOM.

## 6. ERC gate (1 run + a driver re-check)
- An independent re-check covered ERC, footprints, supply spans against absolute maxima, signal levels across rails, every FPGA pin's bank voltage, the filter values and the sequencing.
- **Passed**, with one medium finding: the FT232H in 3.3 V mode needs ≥ 3.30 V, and the 3.3 V rail can sag to 3.21 V at worst-case tolerance.
- Options were accept, trim R6, or switch the FT232H to **VREGIN 5 V mode**. The 5 V mode was chosen as the only one that removes the problem; the USB-bridge block was rewired and the circuit re-run (0 errors, 0 warnings, BOM agrees). This change was checked by the driver, not re-run through the independent reviewer.

## 7. Review
- Skipped; `/design-review` is still available. The notebook (`dual_adc_usb.ipynb`) recomputes the key numbers from the component values and re-runs ERC.

## 8. Export
- `outputs/dual_adc_usb.net` and `outputs/dual_adc_usb_bom.xml`, generated with `PYTHONHASHSEED=0` for a repeatable netlist.
- Ship `footprints/ProjectLocal.pretty/` and `symbols/dual_adc_usb.kicad_sym` with them.

---

## Open risks
- **Power margin:** after the FT232H 5 V-mode change, the worst case at 4.4 V is ≈ 412 mA — under 500 mA, but past the ×1.25 margin line (≈ 515 mA). It rests on unverified FPGA loads (K5, K10). Holding the ADC in power-down until the host opens the device saves ≈ 55 mA. On a USB-C host advertising 1.5 A there is no issue.
- **FPGA:** PSRAM throughput, core current, 1.8 V load and exposed-pad net are assumptions. No spare 3.3 V I/O. Dual-purpose pins need "use as regular IO" in the Gowin project. Gowin's recommended ferrite + 4.7 µF on VCC is not fitted.
- **JTAG header:** 1.8 V — needs a VREF-tracking programmer.
- **Anti-alias filter:** ≈ 36–40 dB rejection at the 35 MHz alias edge; the finite-GBW model shows ≈ 0.35 dB in-band peaking. Not checked in SPICE.
- **ADC capture timing:** without DV, capture relies on a ≈ 10 ns data window and a PLL phase shift calibrated at bring-up.
- **BNC footprint:** custom, from a not-to-scale drawing; dry-fit a real connector before fabrication.
- **Stock:** low for the ADC (235) and FPGA (182), both single-source.
- **Docs drift:** `architecture/net_plan.md` and `design_risks.md` P1 still show the FT232H on the 3.3 V rail.
