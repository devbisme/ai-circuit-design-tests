# dual-adc-usb-2 — executive summary

## What was done

The design came from a single prompt (`create the design described in dual-adc-prompt.txt.`) with no user intervention.
Claude designed a complete board from scratch, from requirements to Gerbers, using
kicad-mcp-pro 4.1.0 as a **design tool**. Run 1 used it only as an analyzer.

## The design

A dual-channel, 12-bit, 10 MS/s ADC with ±10 V inputs, bus-powered over USB 2.0.

- **Signal path, per channel:**
  - BNC input, then a 1 MΩ compensated ÷10 divider (909 k ‖ 18 pF over 101 k ‖ 160 pF).
    The ~16 pF input capacitance lets scope probes be compensated.
  - BAV99 clamp to ±4.5 V.
  - OPA810 buffer.
  - THS4521 differential driver (gain 0.91, ~9 % headroom, 4.8 MHz pole), then the LTC2290 dual ADC.
- **Capture:** iCE40HX4K FPGA and an 8 MB SDRAM (AS4C4M16SA). That holds 0.2 s at full rate; 0.1 s was required.
- **Clocks:** a dedicated 10 MHz oscillator clocks the ADC, and a buffered copy goes to the FPGA. A separate 50 MHz oscillator is the FPGA's system clock.
- **Host link:** FT2232HL.
  - Channel A is an async FIFO for data: 4 MB uploads in about 0.5 s. The board is wired so sync FIFO can also be used.
  - Channel B programs the FPGA config flash (iceprog `-I B`).
- **Power:** estimated at about 320 mA (≈ 1.6 W), within USB 2.0's 500 mA, so USB-C wasn't needed.
  - Connector: USB-B, with a polyfuse and USBLC6 ESD protection.
  - Regulators: TLV75733 for 3.3 V, TLV75712 for 1.2 V, LP5907 for the 3.3 V analog rail, and an LM27762 charge pump for ±4.5 V.
- **Decisions:** every design decision lists its options and the one chosen, as the prompt required
  (`design_notes.md` §Decisions).

## Results

| Item | Result |
|---|---|
| Schematic | 7 hierarchical sheets, 175 parts, 233 nets. **ERC: 0 errors.** 2 intentional warnings: flash WP#/HOLD# tied to +3V3. |
| PCB | 115 × 85 mm, 4 layers: F signal / In1 GND plane / In2 signal+power / B signal+GND pour. 2686 track segments, 530 vias. |
| DRC | **0 errors, 0 unconnected, 0 schematic-parity issues.** 18 warnings: silkscreen where the BNC/USB connectors overhang the edge, plus one `lib_footprint_mismatch` on J701 that persists after reloading it from the library. |
| Fab outputs | `dual_adc_usb/output/`: Gerbers + drill, `bom.csv`, `pos/`, `schematic.pdf`, `render_top.png` |
| Cost / time | **$18.90** equivalent API cost (`claude_cost.txt`). About 1h35m wall clock (09:07 to ~10:40), including two ~17-minute Freerouting runs. No subagents. |

## How kicad-mcp-pro held up

**Used for:**
- creating the project and the 7 sheets;
- capturing each sheet with one `sch_build_circuit` call, connecting nets by name with labels and power symbols;
- ERC;
- moving footprints and nets onto the PCB with `pcb_sync_from_schematic` (100 % of pads net-mapped);
- the quality/DFM gates;
- the Gerber, drill, BOM, pick-and-place and schematic-PDF exports.

**Bugs in schematic capture:**
- It can't read KiCad 10's `.kicad_symdir` libraries: it looks only for `<lib>.kicad_sym`, so every pin lookup failed.
  Library *search* worked, which hides the problem.
  Workaround: the needed libraries were flattened into `dual_adc_usb/libs/` with a project `sym-lib-table`.
- **Multi-unit parts:** pin positions are keyed by reference only, so only one unit of the FPGA resolved and **92 nets were silently dropped**.
  Workaround: each unit was built under a temporary reference, then renamed.
- Child sheets got a random root instance path and an empty project name.
- `#PWR` references restart on every sheet.
- PWR_FLAGs are added on every sheet, including regulator-driven rails. That caused 19 ERC errors.
- There is no no-connect support.
- `sch_delete_symbol` also deleted a neighbouring label stub, which disconnected FT2232H pin 9. It was caught by diffing netlists.

**Bugs in the PCB tools:**
- **Gated at startup.** The PCB tools were gated off when the server started, because KiCad's IPC wasn't up. Starting pcbnew later did not expose them to the session.
  Workaround: they were called in-process through `scripts/mcp_call.py`.
- **`pcb_sync_from_schematic` pre-sync gate** checks only the root sheet, so on a hierarchical design it always fails.
  Workaround: it was run with `force=True`.
- **Footprint IDs:** it wrote them without the library nickname, giving 175 parity errors.
- **Auto-placement** scored 1/100: parts overlapped and connectors sat 10–22 mm from the edge.
- **Routing is "human-gated":** DSN export and SES import both require the KiCad GUI.
  - `export_3d_render` failed.
  - `sch_render_png` needs packages that aren't installed.
  - The DFM check reported "no active board" for its layer, track and via checks.
  - The PCB gate treats silkscreen warnings as blocking.

**Workaround: KiCad 10 Python scripts and Freerouting** (all in `scripts/`) filled the gaps:
- placement with a keep-clear band around the fine-pitch ICs;
- a locked GND fanout to the In1 plane;
- DSN export, Freerouting and SES import;
- a small A* router for the last 4 connections;
- net classes re-applied after each pcbnew save.

## Risks and caveats

These are as Claude reported them. They have not been independently validated.

- **Part data** came from the model's memory, not the datasheets. Check first:
  - The LM27762 feedback equations: 274 k/100 k sets +4.5 V and 374 k/100 k sets −4.5 V.
  - The LTC2290 REFH/REFL decoupling and the MODE level (1/3 VDD).
  - iCE40 VPP_2V5 tied to 3.3 V.
  - The THS4521 pin 4/5 output polarity.
  - The BAV99 pinout. The KiCad symbol's pin names disagree with its graphic; the wiring follows the graphic.
- **Analog:**
  - Anti-aliasing is only 2 poles, so signals above 5 MHz will alias.
  - The divider compensation (160 pF / 18 pF) assumes about 2 pF of parasitics and may need a trimmer.
  - Nothing was simulated.
- **Layout:**
  - USB D+/D− are plain autorouted tracks, not a 90 Ω pair.
  - Analog and digital share one ground plane.
  - Placement was done by script and not hand-reviewed.
  - Freerouting necked 23 segments down to 0.112 mm. That is fine for 4-layer fab, but tighter than 5 mil.
  - The 4 A*-routed connections are 0.15 mm wide with staircase jogs.
- **USB compliance:** the board draws more than 100 mA before USB enumeration.
- **Not done:** FPGA gateware, host software, and BOM part numbers (MPN/LCSC).
- **Process:** a buggy PWR_FLAG-pruning script corrupted several sheets mid-run. All 7 were regenerated with the same tool calls.
  The rebuild is scripted from that point, but `sch_build_circuit` inputs exist only in the transcript, not in a file.

## Sources

`design_notes.md`, `claude_cost.txt`, `claude_transcript.txt` (closing summary and timestamps),
`dual_adc_usb/output/render_top.png`, `scripts/`, `routing/fr.log`.
