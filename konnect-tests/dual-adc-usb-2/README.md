# Dual-channel 12-bit 10 MSPS USB digitizer — `dual_adc_usb`

KiCad 10 project built with Konnect MCP tools. The work so far covers the schematic only; the PCB has not been laid out yet (see "Status").

## Requirements trace

| Requirement | How it is met |
|---|---|
| 2 channels, ±10 V input | Two identical AFE sheets (`afe_a`, `afe_b`): 1.003 MΩ compensated ÷20 divider → ADA4817 FET buffer → THS4521 FDA. ±10 V gives ±0.951 V differential at the ADC, which is 95% of its ±1 V full scale. |
| 10 MSPS, 12 bit | LTC2290 is a dual, simultaneous-sampling 12-bit ADC rated at 10 MSPS. It is clocked by a 10 MHz SiT8008 MEMS oscillator with about 1 ps rms jitter. |
| ≥0.1 s at max rate | One sample pair is 2 × 12 bit, stored in 32 bits. 10 M pairs/s × 0.1 s × 4 B = **4 MB**. The W9812G6KH SDRAM holds 16 MB, which is about 0.4 s. |
| Scope-lead connectors | BNC inputs with 1 MΩ ‖ ~12 pF. C103/C203 trimmers set probe compensation. |
| USB 2.0, power + data | FT2232H high-speed USB, bus powered, USB-B receptacle. |
| USB-C if power insufficient | Not needed. Estimated draw is ~370 mA against the 500 mA limit (see the power budget below). |

## Design decisions (options → choice)

1. **Data path / buffering**
   - (a) FPGA + SDRAM + FT2232H sync FIFO ← **chosen**. It gives a guaranteed 0.1 s capture whatever the host latency, and all parts are hand-solderable (TQFP/TSOP).
   - (b) Stream directly to the host through FT232H. 30–40 MB/s is needed against ~35–40 MB/s available, so there is no margin and host hiccups drop samples.
   - (c) MCU with HS USB + SDRAM (i.MX RT / STM32H7 + ULPI PHY). This means more firmware complexity, and capturing a 20 MHz parallel bus with an MCU is awkward.
   - (d) FT601 USB 3. This violates the "USB 2.0" requirement.
2. **ADC**: LTC2290 (dual, 10 MSPS, 3 V, in the KiCad library) ← **chosen**. LTC2291/2292 (25/40 MSPS) are pin-compatible fallbacks if you want rate margin. A pair of single ADCs would need more parts and give worse channel matching.
3. **FPGA**: iCE40HX4K-TQ144 ← **chosen**. It has 107 I/O (91 used), an open toolchain (yosys/nextpnr/iceprog), and a TQFP package. ECP5 is overkill and BGA. A MachXO2 would also work, but its library symbol is not available.
4. **Capture memory**: SDR SDRAM 16 MB ← **chosen**, because it is cheap and has 4× margin. 4 MB async SRAM needs no refresh but costs more for the same pin count.
5. **USB bridge**: FT2232H ← **chosen**. Channel A runs sync FIFO for data; channel B runs MPSSE so the board's SPI flash can be programmed over the same cable. FT232H has one channel, so there is no in-system programming path. The FX2LP needs its own firmware.
6. **USB connector**: USB-B ← **chosen**: robust for a bench instrument, and the power budget fits USB 2.0. Micro-B and USB-C (as USB 2.0 + 5.1 k CC) were the alternatives.
7. **Analog supplies**: LM27762 for ±3.97 V (single chip, low noise) ← **chosen**. The alternatives were TPS65131 (inductive and noisier) or a ±5 V isolated module (overkill).
8. **Front-end topology**: ÷20 divider + FET buffer + FDA ← **chosen**. A ÷10 divider would need a larger buffer input common-mode range than the ±4 V rails allow. A direct FDA input cannot present 1 MΩ to a probe.

## Power budget (estimate, from 5 V VBUS)

| Rail | Load | From 5 V |
|---|---|---|
| +3V3 (buck, ~85 %) | FT2232H ~70 mA, SDRAM ~90 mA, FPGA I/O ~30 mA, 1V2 core ~30 mA, misc ~10 mA ≈ 230 mA | ~180 mA |
| +3V0 (LDO) | LTC2290 ~40 mA + oscillator ~5 mA | ~45 mA |
| ±4 V (LM27762) | 2× ADA4817 ~19 mA each + 2× THS4521 ~1.2 mA | ~125 mA |
| **Total** | | **~350–380 mA** |

The +3V0 and ±4 V rails are gated by FT2232H `PWREN#` through Q401. Before enumeration the board draws roughly 70–90 mA, under the 100 mA unconfigured limit. The board has about 8 µF on VBUS, under the 10 µF USB limit.

## FPGA pin allocation

- **Bank 3** (left): ADC channel A data on DA0–11 → pins 1–16, OFA/OFB on 17/18, channel B data on DB0–11 → 19–34. `CLK_10M` goes to pin 21 (GBIN6).
- **Bank 0** (top): FT2232H FIFO D0–7 on 110–118 and control on 119–125. `FT_CLK` goes to pin 129 (GBIN0). SDRAM control is on 135–144, and `SD_CLK` leaves pin 143 through a 33 Ω resistor.
- **Bank 1** (right): SDRAM DQ0–15, A0–A11 and BA0.
- **Bank 2** (bottom): LED0/1, expansion header J601 (TRIG_IN on GBIN5 plus GPIO0–5), and the SPI config pins.

## Verification done

- kicad-cli ERC: **0 errors**. There are two warnings, both intentional: W25Q32 WP#/HOLD# are tied directly to +3V3, which carries a PWR_FLAG. There are also 201 `lib_symbol_issues` warnings. These come from the environment, not the design: the global KiCad 10 `sym-lib-table` points at a stale AppImage mount path, and the symbols embedded in the schematic are complete.
- Netlist: 170 components, 214 nets, no single-node nets, no duplicate references. All key nets were spot-checked (ADC→FPGA, FPGA↔SDRAM, FIFO, SPI config, VCM, PWREN).
- All 170 footprints exist in the KiCad 10 footprint libraries.

## Open items / uncertainties (verify before fab)

- **LM27762**: I am not certain of the FB− divider topology and reference polarity, or of the recommended CP and flying-cap values. They are set as 115 k/49.9 k, 1 µF and 4.7 µF; check them against the TI datasheet.
- **ADA4817 input CM range** needs about 2.8 V of headroom to +Vs. ±0.5 V at the buffer input on ±3.97 V rails should be fine, but confirm it. The exposed pad is tied to VEE; confirm that is allowed.
- **BAV199DW**: the KiCad symbol's pin names look inconsistent with its pin numbers. Confirm that the pin 1 / 6 / 2 series pair matches the Diodes Inc. datasheet.
- **LTC2290 MODE** is set to 2/3·VDD (two's complement, duty-cycle stabilizer on), and SENSE=VDD gives a 2 Vpp range. Confirm against the datasheet table.
- **FT2232H**: channel B MPSSE can only be used while channel A is not in sync-FIFO mode. This has not been verified on hardware.
- **Anti-alias filtering** is only two poles (~7 MHz) and is not a brick-wall filter. Content above 5 MHz will alias, so a higher-order filter is an option if the application needs it.
- Cosmetic: some labels overlap on the FPGA sheet (R602–R604 pull-up labels) and on the USB connector pins.

## Status / next steps

1. **PCB layout: done as a candidate board.** `dual_adc_usb_routed.kicad_pcb` (+ its own `.kicad_pro`) is 140 × 90 mm and 4 layers: F.Cu signal / In1 GND plane / In2 +3V3 plane / B.Cu signal. It is 100 % routed, and kicad-cli DRC reports 0 errors and 0 unconnected. Rules: 0.15 mm clearance and minimum track; 0.2 mm default tracks; 0.4 mm on the Power netclass; 0.6/0.3 mm vias. The original `dual_adc_usb.kicad_pcb` is still the placed-but-unrouted 2-layer board; the candidate also includes ~20 small decap moves. Routing scripts and the final SES are in `routing/`. Autorouted, so not yet reviewed for analog/SI quality (see below).
   PCB review items (autorouter output, not yet hand-tuned):
   - USB D+/D− were not routed as a controlled-impedance differential pair. They are short (~20 mm), but should be re-routed as a 90 Ω pair.
   - Some ±4 V, +3V0 and VCM routes take long detours, and a few digital traces cross the analog section. Re-route the AFE and ADC area by hand.
   - The 10 MHz ADC clock (OSC_OUT/ADC_CLK) should be short and kept away from data lines. Check it.
   - No outer-layer GND pours or stitching yet. Consider B.Cu GND fill under the AFE.
   - About 170 silkscreen warnings (overlaps, silk over copper and near the board edge) and 170 `lib_footprint_mismatch` warnings. The mismatch warnings come from the stale global footprint library table.
2. FPGA gateware: ADC capture → SDRAM controller → FT245 sync FIFO readout. Bitstream programming through `iceprog -I B`.
3. Host software (libftdi / pyftdi): arm, capture, read back.
