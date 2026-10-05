# Executive Summary — dual_adc_usb

**Result:** a 2-channel board that samples ±10 V inputs at 12 bits and 10 MSa/s. It stores ≥ 0.1 s of samples (16 MB SDRAM, ≈ 0.4 s for both channels) and connects to the host over USB 2.0 High-Speed through a USB-B receptacle, which also powers it.

- 170 parts (plus 4 board-only mounting holes) and 214 nets.
- ERC: 0 errors. 2 deliberate warnings (flash WP#/HOLD# tied to +3V3) and 201 environment warnings (stale global KiCad symbol-library table).
- **PCB:** 140 × 90 mm, 4 layers, placed and 100 % routed. USB D+/D− re-routed by hand as a ≈ 90 Ω differential pair.
  - DRC: 2 errors remain. Both are orphan vias left from the old USB route, which Konnect cannot delete; they must be removed in the KiCad GUI.
- **Not yet built.** No FPGA logic or host software.
- Equivalent API cost: see `claude_cost.txt` (≈ $61 for the whole session: schematic, layout and the USB rework). No sub-agents were used.

**Method:** a single main-thread session driving KiCad 10 through the Konnect MCP server.

- Schematic edits went through Konnect's file-based schematic tools; PCB edits went through live KiCad IPC.
- Autorouting was done with Freerouting 2.4.1 on a scratch copy of the board.
- The prompt said not to pause for input. At each decision the options were listed, and the recommended one was chosen and recorded (README "Design decisions").
- Three points needed the user: opening the board in pcbnew, closing it for file-level steps, and adopting the routed candidate board.

---

## 1. Requirements (main thread)
- Read `dual-adc-prompt.txt`. Hard requirements:
  - 2 channels, ±10 V input range
  - 10 MSa/s, 12 bits
  - ≥ 0.1 s of capture at full rate
  - scope-lead-compatible connectors
  - USB 2.0 data and power, with USB-C only if the power budget requires it
  - blank slate: nothing reused from other designs
- Soft constraints chosen by the driver:
  - 1 MΩ probe-compatible input, DC coupling
  - anti-alias filtering near Nyquist
  - hand-solderable packages (no BGA)
  - 4-layer board

## 2. Architecture

### Functional blocks (one hierarchical sheet each)
| # | Sheet | Function |
|---|---|---|
| 1 | `afe_a` / `afe_b` | BNC → compensated ÷20 divider → FET buffer → fully differential driver → ADC (B is a copy of A, refs 2xx) |
| 2 | `adc` | Dual 12-bit 10 MSPS ADC, references, 10 MHz MEMS oscillator |
| 3 | `fpga` | iCE40 FPGA, 16 MB SDRAM, SPI config flash, LEDs, expansion header |
| 4 | `usb` | USB-B, ESD, FT2232H (ch A sync FIFO, ch B MPSSE), 12 MHz crystal, config EEPROM |
| 5 | `power` | 3.3 V buck, 1.2 V LDO, 3.0 V analog LDO, ±4 V charge pump, enumeration-gated enable |

### Criteria and decisions by block

**Data path and buffering**
- *Criteria:* guaranteed 0.1 s capture whatever the host latency; USB 2.0 only; no BGA.
- *Decisions:*
  - **FPGA + SDRAM + FT2232H sync FIFO** — capture first, then upload.
  - Rejected:
    - direct streaming through an FT232H: 30–40 MB/s needed against ~35–40 MB/s available, so no margin
    - an MCU with HS USB and SDRAM: firmware load, and capturing a 20 MHz parallel bus is awkward
    - FT601: USB 3, which the prompt rules out

**ADC**
- *Criteria:* 12 bits, simultaneous sampling of both channels, a symbol in the stock KiCad library.
- *Decisions:*
  - **LTC2290**: dual, 10 MSPS, 3 V, parallel CMOS outputs, internal 2 Vpp reference.
  - Two's-complement output, clock duty-cycle stabilizer on (MODE = 2/3 VDD).
  - Pin-compatible fallbacks with rate margin: LTC2291 / LTC2292 (25 / 40 MSPS).
  - It runs at its rated maximum of 10 MSPS, so there is no oversampling.

**Clock**
- *Criteria:* jitter ≤ ~6 ps RMS for 12-bit SNR at 5 MHz.
- *Decisions:*
  - **SiT8008 10 MHz MEMS oscillator** (≈ 1 ps phase jitter), powered from the 3.0 V ADC rail.
  - It clocks both ADC channels and the FPGA through separate 33 Ω series resistors.
  - The FPGA PLL is kept out of the ADC clock path.

**Analog front end, ×2**
- *Criteria:* ±10 V full scale; 1 MΩ ‖ low pF so scope probes compensate; overvoltage protection; anti-alias filtering.
- *Decisions:*
  - **Compensated divider:**
    - 953 kΩ ‖ 2.2 pF over 49.9 kΩ ‖ (27 pF + 4.5–20 pF trimmer)
    - 1.003 MΩ, ÷20.1
  - ÷20 rather than ÷10, so the buffer stays inside its input common-mode range on ±4 V rails.
  - **BAV199DW** low-leakage clamps to the ±4 V rails; fault current is limited by the 953 kΩ.
  - **ADA4817-1** FET-input unity buffer: low bias current into the 47 kΩ divider source impedance.
  - **THS4521** fully differential driver:
    - gain 953/499 = 1.91, VOCM taken from the ADC
    - ±10 V → ±0.951 V differential (95 % of full scale, ~5 % headroom)
  - **Anti-alias filtering:** two poles only (Rf‖Cf at 7.6 MHz, output RC at 7.3 MHz) — see Open risks.

**FPGA and capture memory**
- *Criteria:* ≥ 4 MB of buffer; 24 data bits + 2 over-range bits from the ADC; FIFO interface; open toolchain; no BGA.
- *Decisions:*
  - **iCE40HX4K-TQ144** (107 I/O, 91 used; yosys / nextpnr / iceprog). ECP5 lost on BGA and overkill.
  - **W9812G6KH-6** SDR SDRAM: 16 MB, 4× the 4 MB requirement, 200 MB/s peak against 40 MB/s needed.
  - Bank plan:
    - bank 3 = ADC (CLK_10M on GBIN6)
    - bank 0 = FT2232H FIFO (60 MHz FT_CLK on GBIN0) plus SDRAM control
    - bank 1 = SDRAM data and address
    - bank 2 = LEDs, expansion header (TRIG_IN on GBIN5), SPI config
  - **W25Q32JV** config flash; iCE40 boots from it as SPI master.

**USB bridge**
- *Criteria:* USB 2.0 High-Speed; reprogramming the FPGA over the same cable; no firmware.
- *Decisions:*
  - **FT2232H:**
    - channel A runs 245 synchronous FIFO (~35–40 MB/s)
    - channel B runs MPSSE wired to the iceprog `-I B` pinout, to program the flash and reset the FPGA
  - Rejected: FT232H (single channel, so no in-system programming path), FX2LP (needs firmware).
  - **93LC56** EEPROM holds the FIFO-mode configuration.
  - **USBLC6-2SC6** ESD protection.

**Power**
- *Criteria:* USB 2.0 budget (5 V, 500 mA); ≤ 100 mA before enumeration; quiet analog rails.
- *Decisions:*
  - The budget was estimated at ≈ 350–380 mA, so the USB-C rule did **not** fire.
  - A **USB-B** receptacle was chosen for robustness on a bench instrument; micro-B and USB-C (as USB 2.0) were the alternatives.
  - Regulators:
    - **TPS62160** buck: 3.3 V
    - **TLV75512**: 1.2 V FPGA core
    - **LP5907-3.0**: ADC and clock
    - **LM27762**: ±3.97 V for the front ends
  - FT2232H PWREN# (inverted by Q401) enables the analog and ADC rails only after USB configuration, keeping the pre-enumeration draw under 100 mA.
  - VBUS capacitance ≈ 8 µF, under the 10 µF limit.

## 3. Schematic capture (main thread, Konnect)
- 7 sheets.
- Cross-sheet digital nets use global labels; the AFE↔ADC links use hierarchical pins.
- The SDRAM bus uses bus fan-out with group bus labels.
- AFE_B was made with `duplicate_sheet`, then its references were renumbered to 2xx.
- Fixes found by checking:
  - An auto-routed `connect_pins` wire crossed the SENSEB pin and **shorted VCMB to +3V0**. Caught on the rendered sheet, then rerouted.
  - Power symbols numbered `#PWR001…` on every sheet produced a kicad-cli annotation error; renumbered per sheet.
  - Resized sheet blocks left their pins off the edge; moved the pins and rewired.
  - A dangling tie wire; missing bus labels; a PWR_FLAG conflicting with the USB connector's GND pin.

## 4. ERC and netlist verification
- kicad-cli ERC: 0 errors.
- Exported netlist:
  - 170 components, 214 nets
  - no single-node nets, no duplicate references
  - key nets spot-checked: ADC→FPGA, FPGA↔SDRAM, FIFO, SPI config, VCM, PWREN
- All 170 footprints exist in the KiCad 10 libraries.
- Outputs:
  - `dual_adc_usb_schematic.pdf`
  - `dual_adc_usb_bom.csv`
  - README with power budget, pin allocation and open items

## 5. PCB placement (live IPC)
- Netlist pushed with `update_pcb_from_schematic`: 170 footprints in one undo step.
- Board: 140 × 90 mm outline, 4 × M3 mounting holes.
- 170 placements were computed in a script with a courtyard-overlap check, then applied in one IPC batch.
- Placement follows the signal flow, left to right:
  - BNCs and both AFE chains on the left, with the ±4 V and 3.0 V supplies between them
  - the ADC beside FPGA bank 3, then the FPGA, then the SDRAM beside bank 1
  - the FT2232H above bank 0, with the USB-B on the top edge
  - digital power bottom-right
- About 20 decap moves were made later during routing, mainly to unblock fanout and the ADC's top-edge data pins.

## 6. Routing (scratch copy, Freerouting 2.4.1)
- Konnect's file-only `add_layer` was **blocked by the auto-mode permission classifier** as an in-place destructive edit. So the stackup and routing were done on a scratch copy and delivered as a separate candidate board, which the user then adopted.
- **Stackup:** F.Cu signal / In1 GND plane / In2 +3V3 plane / B.Cu signal.
- **Rules:** clearance and minimum track 0.15 mm (needed for 0.5 mm-pitch fanout and the THS4521 footprint); 0.2 mm default track; 0.4 mm Power class; 0.6/0.3 mm vias.
- **Plane fanout:** a script added a locked via and stub for every SMD GND/+3V3 pad (≈ 224 vias, 3×3 via-in-pad on the QFN). The DSN plane nets were then cut to one pin, because Freerouting ignores inner planes.
- **Three full Freerouting runs, about 25 min each.** Between runs:
  - Fixed fanout bugs: F.Paste-only pads treated as copper; SWIG pad identity; adjacent 0.5 mm-pitch GND/+3V3 pins.
  - Cut the ADC exposed-pad vias from 5×5 to 3×3.
  - Moved the ADC decap row 3 mm away from the pin tips.
  - Final run: 1 connection unrouted.
- An incremental Freerouting pass on the routed export made things worse (75 unrouted) and was abandoned.
- A small pure-Python A* grid router finished the last connections.
- Result: **0 DRC errors, 0 unconnected** on the candidate.

## 7. USB differential pair (live IPC)
- **Netclass rules lost:** adopting the candidate by renaming dropped its `.kicad_pro` netclasses, and DRC jumped to 519 clearance errors. The 0.15 mm rules were restored as per-layer constraints in `dual_adc_usb.kicad_dru`, which KiCad does not overwrite while the project is open.
- **Geometry:** 0.28 mm traces, 0.18 mm gap, F.Cu over the In1 GND plane.
  - ≈ 90 Ω by IPC-2141A, for the JLC04161H-7628 stackup (0.21 mm prepreg, εr 4.4).
  - Neck-down to 0.2 mm for the last 1.2 mm into the 0.5 mm-pitch FT2232H pins.
- **Polarity swap:** the connector has D+ above D−, while the ESD chip and FT2232H have D− on top. D+ breaks out on B.Cu and returns through one via.
- **VBUS:** ESD pin 5 sat between the pair; VBUS now leaves through a via under the SOT-23 body.
- DRC after the rework: 2 errors, both orphan vias from the old route that Konnect cannot delete.

## 8. Outputs
- `dual_adc_usb.kicad_pro` / `.kicad_sch` (7 sheets) / `.kicad_pcb` (routed, 4-layer) / `.kicad_dru`
- `dual_adc_usb_v1.kicad_pcb`: the earlier placed-only 2-layer board
- `dual_adc_usb_schematic.pdf`, `dual_adc_usb_bom.csv`, `README.md`
- `routing/`: fanout, SES-merge and cleanup scripts, the final SES, and a board render

---

## Open risks
- **Board not fab-ready:**
  - Delete the 2 orphan USB vias at (131.63, 67.73) and (147.61, 66.95).
  - Set the stackup in Board Setup; the USB width assumes JLC04161H-7628, so recompute it for another fab.
  - Restore the Power/USB netclasses in `.kicad_pro`.
- **Autorouted layout, not hand-reviewed:**
  - Some ±4 V, +3V0 and VCM routes take long detours.
  - Digital traces cross the analog section.
  - The 10 MHz ADC clock route is unreviewed.
  - No outer-layer GND pour or stitching.
- **Unverified datasheet items:**
  - LM27762 negative-feedback topology and capacitor values
  - ADA4817 input common-mode headroom, and its exposed pad tied to VEE
  - BAV199DW symbol pin naming
  - LTC2290 MODE / SENSE table
  - FT2232H channel B MPSSE usable while channel A is not in sync-FIFO mode (untested)
- **Anti-alias filter:** two poles only; content above 5 MHz aliases. Not simulated.
- **ADC at its rating:** the LTC2290 runs at exactly its rated 10 MSPS; LTC2291 is the drop-in for margin.
- **Power margin:** the ≈ 370 mA estimate was not measured. FPGA and SDRAM currents depend on the gateware.
- **Environment:** the global KiCad 10 symbol and footprint library tables point at a stale AppImage mount. That causes about 370 `lib_symbol_issues` / `lib_footprint_mismatch` warnings, a configuration issue rather than a design one.
