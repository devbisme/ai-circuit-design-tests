# kicad-mcp-server — tests

## Tool under test

[kicad-mcp-server](https://github.com/Seeed-Studio/kicad-mcp-server) (Seeed Studio) is an MCP
server that gives Claude Code tools (`mcp__kicad__*`) for reading and checking KiCad designs:
schematic and netlist queries, hierarchical net tracing, pin/power/bus extraction, PCB
statistics and net analysis, ERC/DRC, and Gerber/SVG/3D exports. It also has a few editing
tools (add component, wire, label, board outline). It runs under KiCad's bundled Python so it
can use `pcbnew`. Installation is described in [`setup.md`](setup.md).

- **Version:** kicad-mcp-server 0.1.0, commit 4085d3f (2026-09-28).
- **Model:** Claude Opus 5.5 on a Claude Pro plan, Claude Code v2.1.295 (both runs).
- **Backend:** KiCad 10.0.4 (bundled Python 3.11.2 and `kicad-cli` in `~/bin/kicad10-root`).

## Runs

The two runs test different things, so they can't be compared directly:

| Run | What it tests | Prompts | Outcome | Equiv. API cost | Time |
|---|---|---|---|---|---|
| [`dual-adc-usb-1`](dual-adc-usb-1/) | A few commands that **analyze** an existing design | 6 short ones | Function identified, wiring checked, 13 risks listed, Gerbers and a PCB image | $2.05 | ~8 min working |
| [`dual-adc-usb-2`](dual-adc-usb-2/) | A **full design**, from requirements to Gerbers | 1 (the dual-ADC prompt) | 6-sheet schematic, routed 4-layer board, 4 DRC errors (all in the stock USB-C footprint) | $16.93 | ~2h20m wall clock, ~40 min working |

Each run directory has an `executive_summary.md`; start there. Costs are the equivalent
first-party API price of the tokens used (`claude_cost.txt`), not what the Pro subscription
billed. I have not yet validated the findings in either run myself.

## dual-adc-usb-1: trying a few commands

### Input design

The design analyzed is the KiCad project produced by
[Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel
12-bit, 10 MS/s ADC board with a USB 2.0 interface (LTC2290 ADC, iCE40HX4K FPGA, SDRAM,
FT2232HL). The `.kicad_sch`, `.kicad_pcb`, `.kicad_pro` and `.kicad_dru` files are unchanged
copies of Konnect's; this run did not modify the design. `dual-adc-prompt.txt` is the original
prompt given to Konnect to create the design. It was not given to Claude in this run.

### Quick look

Six prompts in one session, about 8 minutes of working time. The server was used only as an
analyzer: netlist, pin queries, ERC and DRC, 5 MCP calls in all.

- Correctly identified the board's function from the schematic notes and part values.
- Checked the netlist pin by pin against the schematic notes. Reported two mismatches:
  - Input capacitance of ~2 pF instead of the ~12 pF the notes claim. This may stop 10x scope
    probes from compensating.
  - iCE40 PLL ground pins tied to board ground (Claude said it was ~75 % confident).
- ERC clean; DRC 0 errors, 343 warnings (cosmetic and library-mismatch).
- The risk review listed 13 items. The most serious:
  - The FPGA has no clock at power-up, because the 10 MHz oscillator is on a rail that only
    switches on after USB enumeration.
  - The −4 V supply's feedback divider was never checked against the LM27762 datasheet.
  - Analog layout noise: the charge pump sits between the input channels, and USB is next to
    channel A.
- Generated JLCPCB Gerbers and a top/bottom PCB image. These used `kicad-cli` and Inkscape
  directly, not the MCP export tools.
- Pinouts and limits came from the model's memory of datasheets, not the documents. Claude
  said so and flagged which items to verify first.

### Prompts

Given in sequence in a single session (from `claude_transcript.txt`):

```
determine the function of the kicad design in this directory.
```
```
check the wiring against the notes with the MCP tools
```
```
identify any risks in this design that may cause it to malfunction.
```
```
generate gerbers to submit to JLCPCB for fabrication.
```
```
create a png image of the pcb showing the top and bottom layer wiring,
footprints, and silkscreen along with the board outline.
```
```
change the white background of the image to dark gray.
```

### Notes

- The session ran in the parent directory; the outputs were moved into `dual-adc-usb-1/`
  afterward, so paths in the transcript omit that subdirectory.
- The Gerbers reproduce the design as-is. None of the risks found in the review were fixed.
- The system `kicad-cli` (KiCad 9.0.9) can't open these KiCad 10 files. Claude found this
  and switched to the KiCad 10 `kicad-cli` on its own.

## dual-adc-usb-2: trying a full design

### Prompt

A single prompt, with no user intervention afterward:

```
create a design as described in dual-adc-prompt.txt.
```

`dual-adc-prompt.txt` is the same dual-ADC requirements prompt used in the
[Konnect](../konnect-tests/) tests.

### Quick look

- **Design:** made from scratch. Each channel is BNC → 1 MΩ compensated ÷10 divider → OPA810
  buffer → THS4521 → LTC2290. The capture side is an iCE40HX4K with 32 MB SDRAM and an
  FT2232H, with a USB-C connector wired as USB 2.0. Power is ~300 mA (estimated). The design
  decisions, with the options considered and the one chosen, are in `DESIGN.md`.
- **Schematic:** 6 sheets, 186 parts, ERC 0 errors. The netlist matches `design.py`
  (191/191 nets).
- **PCB:** 150 × 90 mm, 4 layers, 0 unconnected. DRC shows 4 hole-clearance errors, all
  inside KiCad's stock USB-C footprint.
- **How the server was used:** as a **design tool**.
  - Its functions placed every symbol and made every connection. `build_schematic.py` called
    them in bulk instead of through 1,000+ separate MCP calls.
  - It also ran ERC/DRC, the renders and the Gerbers.
  - It has no tools for sheets, no-connects, netlist import, placement, routing or zones.
    pcbnew scripts and Freerouting filled those gaps.
- **Server bugs found:**
  - Library parts that `extend` another part come in with no pins.
  - Labels on multi-unit parts connect only to the first unit.
  - Labels on tall ICs point sideways.
- **Not ready for fab:**
  - Part data came from the model's memory, not the datasheets.
  - USB D+/D− are plain tracks, not a controlled-impedance pair.
  - The anti-alias filter has only 2 poles.
  - A few connections, including the buck converter's switch node, were routed by a simple
    router Claude wrote.
  - The final repairs were done by hand, so the rebuild is only partly scripted.

## Layout

```
kicad-mcp-server-tests/
├── README.md                   <- this file
├── setup.md                    <- how kicad-mcp-server was installed and verified
├── dual-adc-usb-1/             <- run 1: a few analysis commands on the Konnect run-2 design
│   ├── executive_summary.md    <- start here
│   ├── claude_transcript.txt   <- session transcript (/export); contains all findings
│   ├── claude_cost.txt         <- token usage and equivalent API cost
│   ├── session_cost.py         <- script that produced claude_cost.txt
│   ├── dual-adc-prompt.txt     <- original Konnect design prompt (reference only)
│   ├── dual_adc_usb.kicad_pro  <- KiCad project (copied from Konnect run 2)
│   ├── dual_adc_usb.kicad_pcb  <- board (copied from Konnect run 2)
│   ├── dual_adc_usb.kicad_dru  <- custom design rules, 0.15 mm (copied from Konnect run 2)
│   ├── dual_adc_usb.kicad_prl  <- KiCad local settings
│   ├── dual_adc_usb.kicad_sch  <- root schematic
│   ├── afe_a.kicad_sch, afe_b.kicad_sch   <- analog front ends
│   ├── adc.kicad_sch, fpga.kicad_sch, usb.kicad_sch, power.kicad_sch
│   ├── gerbers/                <- Gerber, drill, drill-map and job files (this run)
│   ├── dual_adc_usb_jlcpcb_gerbers.zip    <- the same files zipped for JLCPCB upload
│   ├── dual_adc_usb_layers.svg <- top/bottom copper, silkscreen, fab and outline (kicad-cli)
│   └── dual_adc_usb_layers.png <- the SVG rendered by Inkscape on a dark gray background
└── dual-adc-usb-2/             <- run 2: full design from the dual-ADC prompt
    ├── executive_summary.md    <- start here
    ├── DESIGN.md               <- requirements, block diagram, budgets, decisions, risks
    ├── design_notes.txt        <- condensed design notes
    ├── claude_transcript.txt   <- session transcript (/export)
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produced claude_cost.txt
    ├── dual-adc-prompt.txt     <- the design prompt
    ├── design.py               <- parts and connections (single source of truth)
    ├── build_schematic.py      <- turns design.py into .kicad_sch files with the server's editing tools
    ├── build_pcb.py            <- imports the netlist into the server-made outline and places footprints
    ├── route_prep.py           <- GND-plane fanout and Specctra DSN for Freerouting
    ├── finish_pcb.py           <- imports Freerouting's session, adds GND pours
    ├── finish_routes.py        <- simple maze router for connections Freerouting left open
    ├── polish_pcb.py           <- widens necked-down tracks, drops duplicate vias, refills zones
    ├── dual_adc_usb.kicad_pro, .kicad_sch, .kicad_pcb, .kicad_prl
    ├── dual_adc_usb.net        <- netlist exported from the schematic
    ├── afe.kicad_sch, adc.kicad_sch, fpga.kicad_sch, usb.kicad_sch, power.kicad_sch
    ├── gerbers/                <- Gerber and drill files
    └── dual_adc_usb_render_top.png        <- 3D render of the top side
```
