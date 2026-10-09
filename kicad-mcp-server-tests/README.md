# kicad-mcp-server — tests

## Tool under test

[kicad-mcp-server](https://github.com/Seeed-Studio/kicad-mcp-server) (Seeed Studio) is an MCP
server that gives Claude Code tools (`mcp__kicad__*`) for reading and checking existing KiCad
designs: schematic and netlist queries, hierarchical net tracing, pin/power/bus extraction,
PCB statistics and net analysis, ERC/DRC, and Gerber/SVG/3D exports. It runs under KiCad's
bundled Python so it can use `pcbnew`. It has a few schematic-editing tools (add component,
wire, label), but those were not used, so here it is tested as an **analyzer**.
Installation is described in [`setup.md`](setup.md).

- **Version:** kicad-mcp-server 0.1.0, commit 4085d3f (2026-09-28).
- **Model:** Claude Opus 5.5 on a Claude Pro plan, Claude Code v2.1.295.
- **Backend:** KiCad 10.0.4 (bundled Python 3.11.2 and `kicad-cli` in `~/bin/kicad10-root`).

## Input design

The design analyzed is the KiCad project produced by
[Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel
12-bit, 10 MS/s ADC board with a USB 2.0 interface (LTC2290 ADC, iCE40HX4K FPGA, SDRAM,
FT2232HL). The `.kicad_sch`, `.kicad_pcb`, `.kicad_pro` and `.kicad_dru` files are unchanged
copies of Konnect's; this run did not modify the design. `dual-adc-prompt.txt` is the original
prompt given to Konnect to create the design. It was not given to Claude in this run.

## Quick look

One run so far: [`dual-adc-usb-1`](dual-adc-usb-1/). Six prompts in one session, about
8 minutes of working time, $2.05 equivalent API cost (`claude_cost.txt`).

- Correctly identified the board's function from the schematic notes and part values.
- Checked the netlist pin by pin against the schematic notes. Reported two mismatches:
  input capacitance of ~2 pF instead of the ~12 pF the notes claim (may stop 10x scope probes
  from compensating), and iCE40 PLL ground pins tied to board ground (stated as ~75 % confident).
- ERC clean; DRC 0 errors, 343 warnings (cosmetic and library-mismatch).
- Risk review listed 13 items. The most serious: the FPGA has no clock at power-up because the
  10 MHz oscillator is on a rail switched on only after USB enumeration; the −4 V supply's
  feedback divider was never checked against the LM27762 datasheet; analog layout noise
  (charge pump between the input channels, USB next to channel A).
- Generated JLCPCB Gerbers and a top/bottom PCB image.
- Pinouts and limits came from the model's memory of datasheets, not the documents. Claude
  said so and flagged which items to verify first.

There is no executive summary for this run; the findings are in `claude_transcript.txt`.
I have not yet validated them myself.

## Prompts

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

## Layout

```
kicad-mcp-server-tests/
├── README.md                   <- this file
├── setup.md                    <- how kicad-mcp-server was installed and verified
└── dual-adc-usb-1/             <- run 1
    ├── claude_transcript.txt   <- session transcript (/export); contains all findings
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produced claude_cost.txt
    ├── dual-adc-prompt.txt     <- original Konnect design prompt (reference only)
    ├── dual_adc_usb.kicad_pro  <- KiCad project (copied from Konnect run 2)
    ├── dual_adc_usb.kicad_pcb  <- board (copied from Konnect run 2)
    ├── dual_adc_usb.kicad_dru  <- custom design rules, 0.15 mm (copied from Konnect run 2)
    ├── dual_adc_usb.kicad_prl  <- KiCad local settings
    ├── dual_adc_usb.kicad_sch  <- root schematic
    ├── afe_a.kicad_sch, afe_b.kicad_sch   <- analog front ends
    ├── adc.kicad_sch, fpga.kicad_sch, usb.kicad_sch, power.kicad_sch
    ├── gerbers/                <- Gerber, drill, drill-map and job files (this run)
    ├── dual_adc_usb_jlcpcb_gerbers.zip    <- the same files zipped for JLCPCB upload
    ├── dual_adc_usb_layers.svg <- top/bottom copper, silkscreen, fab and outline (kicad-cli)
    └── dual_adc_usb_layers.png <- the SVG rendered by Inkscape on a dark gray background
```

Notes:

- The session ran in this directory; the outputs were moved into `dual-adc-usb-1/`
  afterward, so paths in the transcript omit that subdirectory.
- The Gerbers reproduce the design as-is. None of the risks found in the review were fixed.
- The system `kicad-cli` (KiCad 9.0.9) can't open these KiCad 10 files. Claude found this
  and switched to the KiCad 10 `kicad-cli` on its own.
