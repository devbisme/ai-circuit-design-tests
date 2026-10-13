# KiCad-AI-Assistant — tests

## Tool under test

[KiCad-AI-Assistant](https://github.com/paul356/KiCad-AI-Assistant) has two parts:

- **A KiCad action plugin.** It is a chat panel in the PCB editor with its own agent loop and a
  Freerouting integration.
- **An MCP server, `kcaa`.** It runs standalone with the "full" profile and registers 129
  tools for:
  - Schematic editing: symbol search and placement, wires, labels, no-connects, sheets and
    sheet pins, properties, symbol and library creation, group placement.
  - Schematic analysis: netlist extraction, ERC through `kicad-cli`, circuit-pattern
    recognition, BOM analysis, validation.
  - PCB editing: footprint search and placement, alignment and distribution, flipping,
    groups, board outline, zones, net classes and design rules.
  - Routing: a pad-to-pad push-and-shove router, vias, a ratsnest query, and a pure-Python
    board renderer.
  - Live-KiCad (IPC) actions: update the PCB from the schematic, refill zones, save, reload,
    and open the DRC dialog.
  - Twelve Markdown "skills" with workflow guidance.

Claude Code used only the MCP server; the plugin's chat panel was not used. Schematic tools edit
`.kicad_sch` files directly (via `kicad-skip`); the IPC tools need the KiCad GUI open with its
API server enabled. Installation is described in [`setup.md`](setup.md).

The tool is a hybrid (both analyzer and generator), so it was tested in both roles, like
[kicad-mcp-server](../kicad-mcp-server-tests/), [kicad-mcp-pro](../kicad-mcp-pro-tests/) and
[eda-agent](../eda-agent-tests/).

- **Version:** kcaa 0.2.7 from PyPI. Plugin files are from the repo at commit ce4161f
  (2026-10-09).
- **Profile:** `full` (standalone MCP server, stdio).
- **Model:** Claude Opus 5.5 on a Claude Pro plan, Claude Code v2.1.296 (both runs).
- **Backend:** KiCad 10.0.4 (`~/bin/kicad10-root`: `kicad-cli`, pcbnew Python, and the GUI for
  IPC). Run 2 also used Freerouting 2.4.1.

## Why this tool

- It is one of the few KiCad MCP servers with tools for both schematic capture **and** PCB
  work: placement, zones, rules and its own router.
- It ships workflow skills and a placement scorer, which suggest it is aimed at building
  designs, not only inspecting them.

## Runs

| Run | What it tests | Prompts | Outcome | Equiv. API cost | Time |
|---|---|---|---|---|---|
| [`dual-adc-usb-1`](dual-adc-usb-1/) | **Analysis** and JLCPCB fab outputs for an existing design | 1 (multi-part, [`analysis_prompt.txt`](dual-adc-usb-1/analysis_prompt.txt)) | ERC 0 errors, DRC 0 errors; 18 ranked findings; Gerbers, BOM, CPL, PNG. Most of the review came from fallbacks because kcaa's analysis tools failed on this design | $3.71 | ~20 min |
| [`dual-adc-usb-2`](dual-adc-usb-2/) | A **full design**, from requirements to Gerbers | 1, plus "keep going" after a usage-limit stop | 6-sheet schematic and routed 4-layer board. ERC 0 errors, DRC 0 errors / 0 unconnected / 0 parity | $19.38 | ~3h45m wall clock, including a usage-limit pause and two ~36-minute Freerouting runs |

Each run directory has an `executive_summary.md`; start there. Costs are the equivalent
first-party API price of the tokens used (`claude_cost.txt`), not what the Pro subscription
billed. I have not yet validated the findings in either run myself.

### dual-adc-usb-1: analyzer on an existing design

The input is the KiCad project produced by
[Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel 12-bit,
10 MS/s ADC board with a USB 2.0 interface (LTC2290 ADC, iCE40HX4K FPGA, SDRAM, FT2232HL).
The `.kicad_*` files are unchanged copies; the run checked their md5 sums before and after.
kicad-happy run 1, kicad-mcp-server run 1, kicad-mcp-pro run 1 and eda-agent run 1 analyzed
the same design.

Prompt ([`analysis_prompt.txt`](dual-adc-usb-1/analysis_prompt.txt)):

```
Analyze the kicad project in this directory using KiCad-AI-Assistant (kcaa). A KiCad 10
executable is in /home/devb/bin/kicad10.

Review the design for architectural, physical design, and manufacturing problems.

Output gerber files for jlcpcb.

Generate the BOM and pick-and-place files for JLCPCB

Create a PNG of the PCB showing the front and back traces, footprints, and
silkscreen along with the board edges all on a dark-gray background.

Write an executive_summary.md file explaining what you did and what results were
found for this kicad project.
```

Quick look:

- **Checks:** kcaa `run_erc` gave 0 errors. 201 of its 203 warnings are a global
  library-table artifact, not design problems. DRC via `kicad-cli`: 0 errors, 0 unconnected,
  343 warnings.
- **Findings (18, ranked):**
  - Architectural: the FPGA has no clock before enumeration, and the ADC can be back-powered
    while its rail is gated; the FDA output can overdrive the ADC inputs; USB throughput is
    marginal for streaming.
  - Decoupling far from IC pins (up to 22 mm).
  - Anti-alias caps 15–18 mm from the ADC.
  - Asymmetric differential paths; USB D+/D− not routed as a pair.
  - Two verified datasheet deviations (LM27762).
  - Silkscreen and BOM/assembly issues.
- **Datasheets:** the two that downloaded were read. The LTC2290 and FT2232H downloads failed,
  so claims about those parts are from memory and are labelled that way.
- **kcaa's analysis tools were mostly wrong or empty on this label-connected hierarchical
  design:**
  - `extract_schematic_netlist` returned no pins.
  - `find_component_connections` and `identify_circuit_patterns` see one sheet at a time, and
    their pattern guesses were often wrong.
  - `get_ratsnest` gave false "unconnected" results; `get_board_info` reported 0 copper
    layers.
  - `export_bom_csv` runs the system KiCad 9 `kicad-cli`.
  - There is no headless DRC.
- **Fallbacks:** the review relied on `kicad-cli`, a netlist pin-map script, a pcbnew geometry
  script and datasheets. Fab outputs were also made with `kicad-cli`.
- The transcript is at `dual-adc-usb-1/reports/claude_transcript.txt`.

### dual-adc-usb-2: full design

The prompt is [`dual-adc-prompt.txt`](dual-adc-usb-2/dual-adc-prompt.txt). It is identical to
the one used for the other tools' run 2.

Prompts, in sequence in one session:

```
create the design described in dual-adc-prompt.txt.
```
```
keep going
```

Claude stopped once at the Pro plan's usage limit, after the board had been placed. When the
limit reset, Claude resumed on its own. The second prompt was given while it was waiting on
Freerouting.

Quick look:

- **Design:**
  - Signal path: BNC → 1.009 MΩ ‖ 13.5 pF compensated 10:1 attenuator → BAV99 clamp →
    OPA810 → THS4521 (2-pole MFB plus an output RC pole, about 3rd-order Butterworth at
    3.2 MHz) → LTC2290.
  - Capture and link: iCE40HX4K with 32 MB SDRAM (1.6 s of capture); FT232H in synchronous
    FIFO mode.
  - Power: USB-B, about 265 mA estimated.
  - Decisions with options are in [`design_notes.md`](dual-adc-usb-2/design_notes.md).
- **Schematic:** 6 sheets, 182 parts, 160 nets.
  - Built with about 2,500 kcaa tool calls (placement, rename, stub wires, labels, power
    symbols, no-connects, properties), all driven from one netlist file
    (`scripts/design.py`). The calls were made in-process through `scripts/kcaa_call.py`,
    which runs the same code as the MCP server.
  - The kicad-cli netlist matches `design.py` exactly. ERC: 0 errors, 2 benign warnings.
  - The schematic can be rebuilt end to end from the scripts.
- **PCB:** 128 × 85 mm, 4 layers: In1 solid GND, In2 split between +3V3 (digital) and GND
  (analog), decoupling caps on B.Cu.
  - kcaa did the update from the schematic (0 warnings), footprint positioning with its
    collision guard, flips, net classes and rules, and renders.
  - Claude's scripts did placement planning, the locked plane fanout and Freerouting
    DSN/SES. Freerouting left 5 connections unrouted, but they were all complete after the
    SES import.
  - DRC: 0 errors, 0 unconnected, 0 parity issues. 147 warnings, all silkscreen.
- **kcaa gaps found** (12, all worked around):
  - Environment and index: `KICAD_SYMBOL_DIR` from the shell profile overrides kcaa's KiCad 10
    symbol path, so the index came up empty. Tools that log through `ctx.info` crash
    in-process.
  - Symbol tools: `get_symbol_pins` returns 0 pins for derived symbols. Private `KLC_*`
    properties are copied without their value, so KiCad can't open the sheet.
  - Schematic structure: child-sheet instance paths and page numbers are wrong;
    `rename_symbol` needs a uuid that `extract_schematic_netlist` doesn't return; extra units
    land off-grid; 180°/270° labels get the wrong justification; symbols are moved off
    existing wires.
  - PCB: `update_pcb_from_schematic` needs the KiCad project manager plus a click in the
    dialog (done here with xdotool); `flip_footprint` leaves the courtyard on F.CrtYd and
    doesn't mirror text.
  - Routing: there is no autorouter in the MCP server, and the plugin's Freerouting jar needs
    Java 25.
- **Self-inflicted problem, fixed:** a pcbnew `SaveBoard` from a directory with no
  `.kicad_pro` reset the project's rules to defaults. The project file was restored from
  kcaa's backup.
- **Not ready for fab:**
  - Anti-aliasing at 10 Msps is weak (−29 dB at 10 MHz); the upgrade path is the
    pin-compatible LTC2292 with decimation.
  - Pin wiring written from memory needs a datasheet check: FT232H VCCD/VPHY/VPLL, THS4521
    output polarity, LTC2290 strapping, iCE40 VPP_FAST.
  - VBUS capacitance is about 15 µF, above USB's 10 µF guideline.
  - Silkscreen needs cleanup; there are no MPN/LCSC fields.

## Layout

```
kicad-ai-assistant-tests/
├── README.md                   <- this file
├── setup.md                    <- how KiCad-AI-Assistant / kcaa was installed and configured
├── dual-adc-usb-1/             <- run 1: analysis of the Konnect run-2 design
│   ├── executive_summary.md    <- start here
│   ├── analysis_prompt.txt     <- the prompt
│   ├── claude_cost.txt         <- token usage and equivalent API cost
│   ├── session_cost.py         <- script that produced claude_cost.txt
│   ├── dual_adc_usb.kicad_pro, .kicad_pcb, .kicad_dru, .kicad_prl, .kicad_sch
│   ├── afe_a, afe_b, adc, fpga, usb, power .kicad_sch
│   ├── dual_adc_usb_pcb.png    <- PCB render on a dark-gray background
│   ├── jlcpcb/                 <- Gerber zip, unzipped gerbers, JLC BOM/CPL, THT list
│   └── reports/                <- claude_transcript.txt, kcaa ERC, DRC+parity JSON, netlist,
│                                  pinmap.txt, pcb_geometry.txt, raw BOM/pos, scripts/
└── dual-adc-usb-2/             <- run 2: full design from the dual-ADC prompt
    ├── executive_summary.md    <- start here
    ├── design_notes.md         <- requirements, budgets, decisions with options, risks
    ├── dual-adc-prompt.txt     <- the design prompt
    ├── claude_transcript.txt   <- session transcript (/export)
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produced claude_cost.txt
    ├── dual_adc.kicad_pro, .kicad_pcb, .kicad_prl, .kicad_sch (root)
    ├── power, frontend, adc, fpga, sdram, usb .kicad_sch
    ├── *.bak, dual_adc-backups/ <- backups written by kcaa and KiCad
    ├── sym-lib-table, fp-lib-table, lib/dual_adc.kicad_sym  <- project libraries
    │                              (flattened symbols; global tables were stale)
    ├── dual_adc_bom.csv        <- grouped BOM from design.py
    ├── fab/                    <- Gerbers, drill, pick-and-place, KiCad BOM
    ├── reports/                <- drc.rpt, erc.rpt, netlist_check.txt, schematic PDF,
    │                              pcb_top.pdf, pcb_render.png (kcaa renderer)
    ├── routing/                <- DSN, SES, Freerouting logs, intermediate boards, DRC runs
    └── scripts/
        ├── kcaa_call.py        <- calls kcaa tools in-process (env fix, ctx.info patch)
        ├── design.py           <- the netlist: parts, values, footprints, pin->net
        ├── filter_design.py    <- attenuator and anti-alias filter calculations
        ├── flatten_symbols.py  <- project library without `extends` / private properties
        ├── build_schematic.py  <- builds all sheets with kcaa tools (+ unit snap, label fix)
        ├── fix_hierarchy.py    <- fixes kcaa's child-sheet instance paths and page numbers
        ├── verify_netlist.py   <- kicad-cli netlist vs design.py
        ├── pins.py, sexp.py    <- pin dump via kcaa; small S-expression reader/writer
        ├── dump_fp.py, place_pcb.py  <- footprint geometry; placement plan applied with kcaa
        ├── fanout.py           <- locked GND/+3V3 plane fanout
        ├── fix_flips.py        <- repairs kcaa flip_footprint artifacts
        ├── zones.py            <- inner-layer plane zones
        ├── export_dsn.py, import_ses.py  <- Freerouting round trip
        └── make_bom.py         <- grouped BOM
```
