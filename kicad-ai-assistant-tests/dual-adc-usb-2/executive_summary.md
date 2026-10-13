# dual-adc-usb-2 — executive summary

## What was done
Claude designed a complete board from `dual-adc-prompt.txt`, from requirements to Gerbers, starting from a blank project. KiCad-AI-Assistant's MCP server (**kcaa 0.2.7**) was the **design tool**:
- placing symbols, wiring, labels, sheets and properties;
- running ERC;
- updating the PCB from the schematic;
- positioning and flipping footprints;
- setting net classes and design rules;
- rendering the board.

Most kcaa calls were made in-process from Python scripts (`scripts/kcaa_call.py`), which run the same code as the MCP server, because there were about 2,500 of them. Scripts filled the gaps kcaa doesn't cover: the netlist definition, placement planning, plane fanout, Freerouting, and fabrication exports with kicad-cli 10.

The run was interrupted once by the usage limit and then resumed. The user's only inputs were "create the design…" and "keep going".

## The design
A dual-channel, 12-bit, 10 Msps ADC with ±10 V inputs, bus-powered over USB 2.0. The decisions, the options weighed for each, and the power budget are in `design_notes.md`.

- **Signal path, per channel:**
  - BNC input, then a 1.009 MΩ ‖ ~13.5 pF compensated 10:1 attenuator (works with 10x scope probes, compensated by a trimmer).
  - BAV99 clamp to ±5VA, then an OPA810 FET-input buffer.
  - THS4521 differential driver wired as a 2-pole MFB low-pass. With an output RC pole the response is about 3rd-order Butterworth at 3.2 MHz.
  - LTC2290 dual ADC. Full scale is ±10.59 V.
- **Capture:** an iCE40HX4K-TQ144 FPGA plus an MT48LC16M16A2 SDRAM (32 MB). That holds about 1.6 s at full rate; 0.1 s was required.
- **Host link:** FT232H in 245 synchronous FIFO mode (about 40 MB/s), configured by a 93LC56B EEPROM. A W25Q32 flash and a 2×5 iceprog header hold the FPGA configuration.
- **Clocks:** a dedicated low-jitter 10 MHz oscillator for the ADC (with a copy to the FPGA) and a 50 MHz oscillator for the FPGA.
- **Power:** estimated at about 265 mA, so USB 2.0 is enough and a **USB-B** connector is used (USB-C was not needed).
  - Rails: TLV62569 buck to 3.3 V, TLV73312 LDO to 1.2 V, LP5907 LDO to 3.3VA, ferrite-filtered +5VA, TPS60403 charge pump to −5 V.
  - The ADC is held in shutdown until the FPGA enables it.

## Results
| Item | Result |
|---|---|
| Schematic | 6 hierarchical sheets, 182 parts, 160 nets. The kicad-cli netlist matches `scripts/design.py` exactly (`reports/netlist_check.txt`). **ERC: 0 errors**, 2 benign warnings (flash WP#/HOLD# tied to +3V3). |
| PCB | 128 × 85 mm, 4 layers: F signal / In1 solid GND / In2 split +3V3 (digital) and GND (analog) / B signal plus decoupling caps. 2,625 track segments and 529 vias, including 443 locked plane-fanout items. |
| DRC | **0 errors, 0 unconnected, 0 schematic-parity issues.** 147 warnings, all silkscreen: reference text over pads or overlapping, and the BNC/USB overhang at the board edge. |
| Outputs | `fab/` (Gerbers, drill, positions, KiCad BOM), `dual_adc_bom.csv` (grouped BOM), `reports/` (DRC, ERC, schematic PDF, PCB render) |
| Cost and time | See `claude_cost.txt`: about $19 equivalent API cost at the time of writing, no subagents. About 3.5 h of wall clock, including two 36-minute Freerouting runs. |

## How kcaa held up
**Worked well:**
- Symbol placement and wiring primitives (fast, about 40 ms per call).
- `extract_schematic_netlist` pin coordinates and directions.
- Batched `set_symbol_property`.
- `run_erc` on KiCad 10.
- `update_pcb_from_schematic`, once the project manager was used: 0 warnings.
- The collision guard in `set_footprint_position`.
- Net-class and rule editing.
- `export_pcb_layer_image`.

**Gaps that needed workarounds** (details in `scripts/` and in memory):
1. An empty symbol index: `KICAD_SYMBOL_DIR` from the shell profile (a KiCad 5 path) overrides kcaa's KiCad 10 path. The global lib tables also point to a stale AppImage mount.
2. `get_symbol_pins` returns 0 pins for derived (`extends`) symbols. This affected LTC2290, OPA810 and most regulators. Fixed with a flattened project library.
3. KiCad-library symbols with private `KLC_*` properties are copied without the property value, and KiCad then can't load the sheet at all.
4. Child-sheet instance paths are written as `/<child-uuid>` and every page is numbered 1.
5. `extract_schematic_netlist` returns no uuid, but `rename_symbol` requires one.
6. Extra units of multi-unit symbols are stacked off-grid (+10 mm), and `move_component` can't snap them back. Power symbols placed on those off-grid stubs got snapped away from them.
7. Local labels at 180°/270° are written with the wrong text justification.
8. `add_symbol_to_schematic` moves a symbol whose pin would land on an existing wire, so power symbols had to be placed before any wiring.
9. `update_pcb_from_schematic` doesn't work with standalone pcbnew. It needs the project manager, plus a human (here, xdotool) to click "Update PCB".
10. `flip_footprint` leaves courtyards on F.CrtYd, doesn't mirror text, and doesn't mirror pad positions. The first two were repaired; the pad positions are harmless for symmetric 2-pad caps.
11. Tools that log through `ctx.info` (`sync_*_index`, `search_footprints`) crash when called outside an MCP session.
12. There is no automatic router in the MCP server (only pad-to-pad), and no headless DRC. The plugin's bundled Freerouting 2.2.3 jar needs Java 25, so the bundled 2.4.1 binary was used instead.

## Risks and things to check before fabrication
- **Aliasing at 10 Msps.** The filter gives −11.7 dB at 5 MHz and −29 dB at 10 MHz, so usable bandwidth is about 3 MHz. The pin-compatible LTC2292 (40 Msps) with decimation in the FPGA is the upgrade path.
- **Pin details written from memory, not checked against datasheets:**
  - FT232H VCCD/VPHY/VPLL/VREGIN wiring.
  - THS4521 output pin polarity.
  - LTC2290 MODE/MUX/SENSE strapping.
  - iCE40 VPP_FAST.
- **Inrush.** About 15 µF sits on VBUS, above the USB 10 µF guideline. Pre-enumeration current is estimated, not measured.
- **Layout.** BUCK_SW missed the Power net class (local nets carry a sheet prefix), so it is routed at 0.2 mm. That is adequate for about 0.3 A average.
- **Silkscreen.** Labels overlap pads; clean them up before fabrication.
- **Not included:** FPGA gateware and host software.
