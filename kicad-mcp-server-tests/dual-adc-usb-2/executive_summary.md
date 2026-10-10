# dual-adc-usb-2 — executive summary

## What was done

A single prompt (`create a design as described in dual-adc-prompt.txt`) with no user intervention.
Claude designed a complete board from scratch, from requirements to Gerbers, using
kicad-mcp-server as a **design tool**. In run 1 it was used only as an analyzer.

## The design

A dual-channel, 12-bit, 10 MS/s ADC with ±10 V inputs, bus-powered over USB 2.0.

- **Signal path (per channel):** BNC → 1 MΩ compensated ÷10 divider (scope-probe compatible)
  → clamp → OPA810 buffer → THS4521 differential driver → LTC2290 dual ADC.
- **Capture:** iCE40HX4K FPGA → 32 MB SDRAM (0.8 s at full rate; 0.1 s required).
- **Host link:** FT2232H. Channel A is a sync FIFO for data (~35–40 MB/s); channel B programs
  the FPGA config flash.
- **Power:** ~300 mA estimated, within USB 2.0's 500 mA. USB-C connector wired as a USB 2.0 device.
- Each design decision lists its options and the one chosen, as the prompt required
  (`DESIGN.md` §Decisions).

## Results

| Item | Result |
|---|---|
| Schematic | 6 sheets, 186 parts. ERC: 0 errors (197 warnings from the stale global `sym-lib-table`). Netlist matches `design.py` (191/191 nets). |
| PCB | 150 × 90 mm, 4 layers, 534 vias, 0 unconnected |
| DRC | 4 errors, all hole clearance (0.194 mm) inside KiCad's stock USB-C footprint. The rest are silkscreen and BOM-flag warnings. |
| Fab outputs | `gerbers/`, 3D render (`dual_adc_usb_render_top.png`) |
| Cost / time | $16.93 equivalent API cost (`claude_cost.txt`). ~2h20m wall clock (9:05 to 11:24), of which ~40 min was the model actively working. |

## How kicad-mcp-server held up

- **Used for:** placing every symbol, making every connection with global labels, drawing the
  board outline, ERC/DRC, renders and Gerbers. Its functions were called in bulk from
  `build_schematic.py` rather than through 1,000+ separate MCP calls.
- **Bugs:**
  - Library parts defined as variants of another part (`extends`) come in with no pins.
  - Labels on multi-unit parts (the FPGA has five units) connect only to the first unit.
  - Labels on tall ICs point sideways.
- **Missing tools:** schematic sheets, no-connect markers, netlist import, placement, routing, zones.
- **Workaround:** pcbnew scripts and Freerouting filled the gaps.
- **Not an MCP bug:** KiCad's stock USB-C footprint names its shell pad `SH` while the symbol
  uses `S1`, so the shield had no net. Claude caught and fixed it.

## Risks and caveats

These are as Claude reported them. They have not been independently validated.

- **Part data** came from the model's memory, not the datasheets. Check first:
  - The LM27761 feedback formula that sets the −3.3 V rail.
  - The LTC2290 reference network and MODE pin.
  - How the iCE40's PLL ground pins should connect.
  - Whether FT2232H channel B can program the flash while channel A is in FIFO mode.
  - The THS4521 pin 4/5 output assignment.
- **Layout:**
  - USB D+/D− are plain tracks, not a 90 Ω pair.
  - Anti-aliasing is only 2 poles, so signals above 5 MHz will alias.
  - Analog and digital share one ground plane.
  - ~5 connections were finished by a simple router Claude wrote: 0.15 mm wide with staircase
    jogs, including the buck converter's switch node, which needs reworking.
  - Silkscreen wasn't cleaned up.
- **Reproducibility:** the rebuild is only partly scripted. The last rip-up and shield-routing
  repairs were done by hand.

## Sources

`DESIGN.md`, `design_notes.txt`, `claude_cost.txt`, `claude_transcript.txt` (closing summary
and timestamps), `dual_adc_usb_render_top.png`.
