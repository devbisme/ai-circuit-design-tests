# kicad-mcp-pro — tests

## Tool under test

[kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro) is an MCP server plus a Claude
Code plugin of 7 skills (`kicad-design-review`, `schematic-review`, `pcb-design`,
`drc-check`, `fabrication-output`, `visual-excellence`, `wired-subcircuit-design`). With the
configuration used here, it exposes 289 tools for:

- Inspecting and checking designs: schematic and PCB queries, net tracing, ERC/DRC, DFM,
  quality gates, and SI/PI/EMC/thermal estimates.
- Authoring schematics: symbols, wires, labels, sheets, and `sch_build_circuit`.
- Limited PCB edits.
- Manufacturing exports, and part sourcing (JLCPCB by default; Nexar, DigiKey and Mouser
  need API keys).

ERC, DRC and exports run through `kicad-cli`. Live PCB edits need KiCad open with its IPC
API enabled. Installation is described in [`setup.md`](setup.md).

The tool is a hybrid (both analyzer and generator), so it is tested in both roles, like
[kicad-mcp-server](../kicad-mcp-server-tests/).

- **Version:** kicad-mcp-pro 4.1.0 from PyPI. The plugin skills are from the repo at tag
  `mcp-server-v4.1.0` (commit 7611c20, 2026-10-09).
- **Profile / mode:** `full` / `write` (see [`setup.md`](setup.md)).
- **Model:** Claude Opus 5.5 on a Claude Pro plan, Claude Code v2.1.296 (both runs).
- **Backend:** KiCad 10.0.4 `kicad-cli` (`~/bin/kicad10-root/bin/kicad-cli`), Freerouting
  2.4.1, ngspice.

## Why this tool

- It claims both review and design capabilities, unlike kicad-happy (analysis only).
- It is newer and much larger than the Seeed kicad-mcp-server, which was missing tools for
  sheets, no-connects, netlist import, placement and routing.

## Runs

| Run | What it tests | Prompts | Outcome | Equiv. API cost | Time |
|---|---|---|---|---|---|
| [`dual-adc-usb-1`](dual-adc-usb-1/) | **Analysis** and fab outputs for an existing design | 4, plus 2 for the summary | ERC/DRC 0 errors; quality gate FAIL, mostly false positives; Gerbers, BOM, CPL, PNG | $2.24 | ~16 min wall clock, ~5 min working |
| [`dual-adc-usb-2`](dual-adc-usb-2/) | A **full design**, from requirements to Gerbers | 1, plus 1 for the summary | 7-sheet schematic, routed 4-layer board, ERC and DRC 0 errors | $19.42 | ~1h35m wall clock |

Each run directory has an `executive_summary.md`; start there. Costs are the equivalent
first-party API price of the tokens used (`claude_cost.txt`), not what the Pro subscription
billed. They include the summary-writing prompts, so they are slightly higher than the
figures quoted in the executive summaries ($2.07 and $18.90). I have not yet validated the
findings in either run myself.

### dual-adc-usb-1: analyzer on an existing design

The input is the KiCad project produced by
[Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel
12-bit, 10 MS/s ADC board with a USB 2.0 interface (LTC2290 ADC, iCE40HX4K FPGA, SDRAM,
FT2232HL). The `.kicad_sch`, `.kicad_pcb`, `.kicad_pro`, `.kicad_dru` and `.kicad_prl` files
are unchanged copies of Konnect's; this run did not modify the design. kicad-happy run 1
and kicad-mcp-server run 1 analyzed the same design, so the three tools' findings can be
compared directly.

Prompts, in sequence in one session (from `claude_transcript.txt`):

```
use kicad-pro to analyze the kicad project in this directory. A KiCad 10
executable is in /home/devb/bin/kicad10.
```
```
output gerber files for jlcpcb.
```
```
generate the BOM and pick-and-place files for JLCPCB
```
```
create a PNG of the PCB showing the front and back traces, footprints, and
silkscreen along with the board edges all on a dark-gray background.
```
```
write an executive_summary.md file explaining what you did and what results were
found for this kicad project.
```
```
add the cost and time row
```

Quick look:

- ERC 0 errors (201 of 203 warnings come from a stale global `sym-lib-table`, a machine
  setup problem). DRC 0 errors, 0 unconnected, 343 warnings.
- Real findings were minor: flash WP/HOLD tied to +3V3 (no quad SPI), footprint library
  drift, silkscreen, BNCs overhanging the edge.
- **The kicad-pro quality gate failed, but most of its blocking items were false
  positives** on inspection. It treats label-connected parts as isolated, measures
  decoupling distance and edge clearance from part centres, and counts KiCad's automatic
  `unconnected-(…)` nets as mismatches. Several DFM checks need the live KiCad connection.
- Gerbers/drill, a JLCPCB zip, BOM and CPL were produced. The MCP pick-and-place export was
  in inches and was redone in mm with `kicad-cli`; the JLCPCB column layout and the PNG
  render were done outside the server.
- Server quirks: it refuses output directories outside the project, lost its active project
  once, and returned ERC/DRC results too large for one response.

### dual-adc-usb-2: full design

The prompt is [`dual-adc-prompt.txt`](dual-adc-usb-2/dual-adc-prompt.txt). It is identical
to the one used for Konnect run 2, kicad-mcp-server run 2 and kicad-happy run 2.

Prompts, in sequence in one session, with no other user intervention:

```
create the design described in dual-adc-prompt.txt.
```
```
create executive_summary.md as was done for previous tests.
```

Quick look:

- **Design:** BNC → 1 MΩ compensated ÷10 divider → BAV99 clamp → OPA810 → THS4521 →
  LTC2290; iCE40HX4K with 8 MB SDRAM; FT2232HL (channel A data FIFO, channel B flash
  programming); USB-B; ~320 mA estimated. Decisions with options are in
  [`design_notes.md`](dual-adc-usb-2/design_notes.md).
- **Schematic:** 7 sheets, 175 parts, 233 nets, ERC 0 errors. Each sheet was captured with
  one `sch_build_circuit` call.
- **PCB:** 115 × 85 mm, 4 layers (In1 GND plane). DRC 0 errors, 0 unconnected, 0 parity
  issues, 18 warnings.
- **How the server was used:** as a **design tool** for project and sheet creation,
  schematic capture, ERC, `pcb_sync_from_schematic`, gates, and exports.
- **Server bugs found:**
  - Can't read KiCad 10 `.kicad_symdir` libraries, so pin lookups fail silently. The needed
    libraries were flattened into `dual_adc_usb/libs/`.
  - Multi-unit parts: only one unit resolves, and 92 FPGA nets were silently dropped.
  - Child sheets get a bad instance path; `#PWR` numbers repeat across sheets; PWR_FLAGs
    are added on every sheet; no no-connect support; `sch_delete_symbol` also deleted a
    neighbouring label.
  - PCB tools are gated off if KiCad IPC isn't up at server start. They were called
    in-process through `scripts/mcp_call.py`.
  - The sync pre-check only looks at the root sheet; footprint IDs lack the library
    nickname; auto-placement scored 1/100; DSN/SES routing requires the KiCad GUI.
- **Gaps filled by Claude's own scripts:** placement, GND fanout, Freerouting DSN/SES, a
  small A* router for the last 4 connections, schematic fix-ups and no-connects (all in
  `scripts/`).
- **Not ready for fab:** part data from the model's memory, not datasheets; 2-pole
  anti-alias filter; USB D+/D− not an impedance-controlled pair; shared analog/digital
  ground; nothing simulated; no MPN/LCSC numbers. The `sch_build_circuit` inputs exist only
  in the transcript, so the schematic rebuild is not fully scripted.

## Layout

```
kicad-mcp-pro-tests/
├── README.md                   <- this file
├── setup.md                    <- how kicad-mcp-pro was installed and configured
├── dual-adc-usb-1/             <- run 1: analysis of the Konnect run-2 design
│   ├── executive_summary.md    <- start here
│   ├── claude_transcript.txt   <- session transcript (/export)
│   ├── claude_cost.txt         <- token usage and equivalent API cost
│   ├── session_cost.py         <- script that produced claude_cost.txt
│   ├── dual_adc_usb.kicad_pro, .kicad_pcb, .kicad_dru, .kicad_prl, .kicad_sch
│   ├── afe_a, afe_b, adc, fpga, usb, power .kicad_sch
│   ├── .kicad-mcp/             <- server state
│   └── mcp_out/                <- outputs of this run
│       ├── erc_report.json, drc_report.json
│       ├── schematic_quality_gate.json, pcb_quality_gate.json, dfm_profile_check.json
│       ├── gerber/, dual_adc_usb_jlcpcb.zip   <- Gerbers/drill, and the JLCPCB upload
│       ├── bom.csv, pos/       <- server BOM and pick-and-place (pos/ has inch and mm)
│       ├── jlcpcb/             <- BOM and CPL in JLCPCB's column layout
│       ├── render/             <- dual_adc_usb_pcb.png and pcb.svg
│       └── pcb_sync.net
└── dual-adc-usb-2/             <- run 2: full design from the dual-ADC prompt
    ├── executive_summary.md    <- start here
    ├── design_notes.md         <- requirements, budgets, decisions with options
    ├── dual-adc-prompt.txt     <- the design prompt
    ├── claude_transcript.txt   <- session transcript (/export)
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produced claude_cost.txt
    ├── dual_adc_usb/           <- the KiCad project
    │   ├── dual_adc_usb.kicad_pro, .kicad_pcb, .kicad_prl, .kicad_sch
    │   ├── afe_a, afe_b, adc, fpga, memory, usb, power .kicad_sch
    │   ├── libs/, sym-lib-table <- flattened symbol libraries (symdir workaround)
    │   └── output/             <- Gerbers, drill, BOM, pos, schematic.pdf, render_top.png,
    │                              ERC report, quality-gate and DFM JSON
    ├── routing/                <- Freerouting DSN in/out, SES, and log
    └── scripts/                <- workarounds for server gaps
        ├── mcp_call.py         <- calls kicad-mcp-pro tools in-process (gated PCB tools)
        ├── fixup_sch.py        <- fixes sheet instance paths and duplicate #PWR refs
        ├── prune_pwr_flags.py  <- removes surplus PWR_FLAGs
        ├── add_no_connects.py  <- adds no-connect markers
        ├── place_board.py      <- board outline, layers and floorplan placement
        ├── gnd_fanout.py       <- locked GND vias to the In1 plane
        ├── prep_dsn.py         <- makes the DSN Freerouting-friendly
        ├── import_ses.py       <- imports the routed session, adds GND pours
        ├── finish_routes.py    <- A* router for the last connections
        ├── set_netclasses.py   <- net classes (re-run after any pcbnew save)
        └── silk_cleanup.py     <- hides passive refs on silkscreen
```
