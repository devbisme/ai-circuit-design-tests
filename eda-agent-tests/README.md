# eda-agent — tests

## Tool under test

[eda-agent](https://github.com/salitronic/eda-agent) is an MCP server with three backends:
Altium Designer (the default and most complete, Windows only), KiCad, and EasyEDA Pro. These
tests used the **KiCad backend**, which exposes 109 tools (`mcp__eda-kicad__*`) for:

- Design creation from a JSON **DesignPlan** written by the LLM: `design_validate_plan`,
  `design_review_plan`, and `kicad_generate_project`, which writes `.kicad_pro`,
  `.kicad_sch` and `.kicad_pcb` from the plan.
- Review: `kicad_full_review` (ERC + DRC + schematic review + schematic/PCB compare),
  `kicad_review_schematic`, `kicad_compare_sch_pcb`.
- Board queries and simple edits (tracks, vias, zones, moves) over KiCad's IPC API.
- Exports (Gerbers, drill, BOM, STEP, renders, …), SPICE, and PCB calculators.

Nearly every KiCad tool needs the KiCad GUI open with its IPC API server enabled. The
`kicad_generate_*` tools write files directly. The autonomous spec-to-board harness
(`autodesign` skill) exists only for Altium and EasyEDA, so it was not installed.
Installation is described in [`setup.md`](setup.md).

The tool is a hybrid (both analyzer and generator), so it is tested in both roles, like
[kicad-mcp-server](../kicad-mcp-server-tests/) and [kicad-mcp-pro](../kicad-mcp-pro-tests/).

- **Version:** eda-agent 0.6.1 (Alpha), commit 8e659a2 (2026-10-07), installed from `main`.
- **Toolset:** full (not `EDA_AGENT_TOOLSET=minimal`), headless (no web dashboard).
- **Model:** Claude Opus 5.5 on a Claude Pro plan, Claude Code v2.1.296 (both runs).
- **Backend:** KiCad 10.0.4 (`~/bin/kicad10-root`, IPC API and bundled Python 3.11),
  Freerouting 2.4.1.

## Runs

| Run | What it tests | Prompts | Outcome | Equiv. API cost | Time |
|---|---|---|---|---|---|
| [`dual-adc-usb-1`](dual-adc-usb-1/) | **Analysis** and fab outputs for an existing design | 1 (`analysis_prompt.txt`) | ERC/DRC 0 errors; 19 ranked issues; Gerbers, BOM, CPL, PNG | $3.43 | ~14 min |
| [`dual-adc-usb-2`](dual-adc-usb-2/) | A **full design**, from requirements to Gerbers | 1, plus 1 for the summary | 7-sheet schematic, routed 4-layer board, ERC and DRC 0 errors | $18.47 | ~1h56m wall clock, ~47 min working |

Each run directory has an `executive_summary.md`; start there. Costs are the equivalent
first-party API price of the tokens used (`claude_cost.txt`), not what the Pro subscription
billed. Run 2's `claude_cost.txt` was generated after the session ended, from that session's
transcripts; it includes the summary prompt. I have not yet validated the findings in either
run myself.

### dual-adc-usb-1: analyzer on an existing design

The input is the KiCad project produced by
[Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel
12-bit, 10 MS/s ADC board with a USB 2.0 interface (LTC2290 ADC, iCE40HX4K FPGA, SDRAM,
FT2232HL). The KiCad files are unchanged copies of Konnect's (the `.kicad_pcb` md5 matches),
and this run did not modify them. kicad-happy, kicad-mcp-server and kicad-mcp-pro run 1
analyzed the same design.

Prompt (from `claude_transcript.txt`):

```
execute the instructions in analysis_prompt.txt.
```

[`analysis_prompt.txt`](dual-adc-usb-1/analysis_prompt.txt) asks for an architectural,
physical-design and manufacturing review **using eda-agent**, JLCPCB Gerbers, BOM and
pick-and-place files, a dark-gray PCB PNG, and `executive_summary.md`.

This run replaces an earlier run 1 whose prompt didn't name eda-agent; in that one Claude
used only `kicad-cli` and pcbnew Python and made no `eda-kicad` calls. The only change to
the prompt is the words "using eda-agent".

Quick look:

- **Connecting to KiCad:** the dual-adc-usb-2 session's pcbnew held `/tmp/kicad/api.sock`,
  so Claude started a second pcbnew on this board, which took over the socket, and pointed
  the socket back at the other instance afterwards.
- **eda-agent tools used:** `kicad_full_review`; board queries (summary, stackup, fab stats,
  vias, zones, layer usage, trace lengths, diff pairs, net classes, tracks, pads); the
  impedance calculators; `kicad_export_netlist`, `kicad_export_gerbers`, `kicad_export_drill`,
  `kicad_export_bom`, `kicad_export_pos`; and the `kicad_cli` passthrough.
- **Checks:** ERC 0 errors, 203 warnings (201 are missing-library warnings from the
  kicad-cli environment, so ERC's library-mismatch check didn't run). DRC 0 errors,
  0 unconnected, 343 cosmetic or library warnings. Parity: 174 warnings, all `Datasheet`
  field noise or the mounting holes.
- All 34 embedded symbols match the stock KiCad library pin-for-pin. The BAV199DW clamp
  wiring was confirmed against the Diodes datasheet, despite misleading KiCad pin names.
- 19 ranked issues. The most serious:
  - The FPGA's 10 MHz clock runs from the gated analog rail, so there is no clock until USB
    enumerates, and the unpowered ADC may be back-powered by the FPGA.
  - ADC inputs can be driven past absolute maximum by large BNC voltages.
  - Decoupling caps sit 5–22 mm from their pins (14 of 16 FPGA supply pins over 5 mm), and
    the anti-alias caps are 16–18 mm from the ADC.
  - LM27762 feedback resistors (49.9 kΩ) are below the datasheet's 50 kΩ minimum, and its
    unused PGOOD is left open instead of grounded.
  - 40 MB/s is at or above the FT2232H sync-FIFO limit; 16 MB SDRAM gives only ~0.4 s.
- JLCPCB Gerber zip, BOM (blank LCSC column), CPL and a 400 dpi PNG were produced.
- Only the LM27762 and BAV199DW datasheets could be downloaded (FTDI returned 403;
  analog.com timed out). Findings that rest on the FT2232H, LTC2290 and ADA4817 are from the
  model's memory, and the summary marks them.

eda-agent gaps that Claude worked around:

- Every query needs a running KiCad, and the server connects only to `/tmp/kicad/api.sock`.
- `kicad_full_review` truncates ERC and DRC to 200 rows each, so they were rerun in full
  through `kicad_cli`. Its schematic and PCB findings were 53 deliberate single-pin
  no-connect nets, and its decoupling check tests only that caps exist, not their distance.
- `kicad_list_pads` omits component references, so the per-IC geometry (decoupling distances,
  per-net routing) was done with KiCad's bundled pcbnew Python, read-only
  (`reports/scripts/pcb_an.py`).
- The exports aren't fab-ready: Gerbers include all 20 layers, the BOM is one ungrouped row
  per part, and the position file is ASCII in inches. Claude zipped only the fab layers,
  regenerated positions as mm CSV via `kicad_cli`, and converted both to JLC format by
  script. The PNG came from an SVG plotted through `kicad_cli`.

### dual-adc-usb-2: full design

The prompt is [`dual-adc-prompt.txt`](dual-adc-usb-2/dual-adc-prompt.txt). It is identical
to the one used for Konnect run 2, kicad-mcp-server run 2, kicad-happy run 2 and
kicad-mcp-pro run 2.

Prompts, in sequence in one session, with no other user intervention:

```
create the design described in dual-adc-prompt.txt.
```
```
write the executive_summary.md for this run
```

Quick look:

- **Design:** BNC → 1 MΩ compensated ÷11 divider → BAV99 clamp → OPA1656 buffer → THS4521
  FDA → LTC2290; iCE40HX4K with 32 MB SDRAM (0.8 s capture); FT232H sync FIFO; USB-B, bus
  powered (~330 mA estimated). Decisions with options are in
  [`design_decisions.md`](dual-adc-usb-2/design_decisions.md).
- **Schematic:** 7 sheets, 179 parts, 185 nets, ERC 0 errors. The netlist matches the
  DesignPlan net-for-net.
- **PCB:** 125 × 95 mm, 4 layers (In1 GND, In2 +3V3 with a +3V3A island). DRC 0 errors,
  0 unconnected, 0 parity issues, 19 silkscreen warnings. `kicad_full_review` 0 errors.
- **How the server was used:** as a **design tool** for plan validation and review, project
  generation, and the final review and exports. The ~50 kB DesignPlan went through
  `scripts/mcp_call.py`, which calls the tool functions in-process.
- **What it contributed:** the plan validator caught real errors, and the generated board
  had every pad on the right net (725/725), so it became the starting board.
- **Server bugs and gaps:**
  - The generated schematic has no connectivity: its global labels touch no pins (780 ERC
    violations, empty netlist), and multi-unit parts get only unit 1.
  - Symbol and footprint lookup needs a running KiCad, silently falls back to box symbols
    without one, and can't read KiCad 10 `.kicad_symdir` libraries.
  - The generated board is 2-layer with grid placement, FPIDs without library nicknames, and
    no symbol links.
  - No placement, routing, zone or DSN/SES tools on KiCad.
  - `design_review_plan` misidentifies circuits (calls the compensated divider an RC
    high-pass and low-pass).
  - The IPC tools only try `/tmp/kicad/api.sock`; a stale socket blocked them until it was
    relinked.
- **Gaps filled by Claude's own scripts:** a label-based schematic writer, 4-layer
  conversion and placement, plane fanout and DSN, 4 Freerouting runs, a small A* router and
  local re-layout around the LM27762 (all in `scripts/`).
- **Not ready for fab:** the FT232H and LTC2290 support circuits weren't checked against
  datasheets (both downloads failed); input compensation caps are estimates; first-order
  anti-alias filter; no USB pre-enumeration current limit; no SDRAM/FIFO length matching;
  no gateware or host software.

## Layout

```
eda-agent-tests/
├── README.md                   <- this file
├── setup.md                    <- how eda-agent was installed and configured
├── dual-adc-usb-1/             <- run 1: analysis of the Konnect run-2 design
│   ├── executive_summary.md    <- start here
│   ├── analysis_prompt.txt     <- the analysis prompt
│   ├── claude_transcript.txt   <- session transcript (/export)
│   ├── claude_cost.txt         <- token usage and equivalent API cost
│   ├── session_cost.py         <- script that produced claude_cost.txt
│   ├── dual_adc_usb.kicad_pro, .kicad_pcb, .kicad_dru, .kicad_prl, .kicad_sch
│   ├── afe_a, afe_b, adc, fpga, usb, power .kicad_sch
│   ├── reports/                <- drc.json, erc.json, eda_agent_full_review.json, netlist,
│   │                              raw eda-agent BOM/positions, pcb_geometry.txt, scripts/
│   ├── jlcpcb/                 <- Gerber zip, gerbers/, assembly/ (BOM and CPL)
│   └── dual_adc_usb_pcb.png    <- PCB image on a dark-gray background
└── dual-adc-usb-2/             <- run 2: full design from the dual-ADC prompt
    ├── executive_summary.md    <- start here
    ├── README.md               <- run details, eda-agent findings, regeneration steps
    ├── design_decisions.md     <- requirements, derived numbers, decisions with options
    ├── dual-adc-prompt.txt     <- the design prompt
    ├── claude_transcript.txt   <- session transcript (/export)
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produced claude_cost.txt
    ├── plan/                   <- DesignPlan (full and compact), review output, no-connects
    ├── eda_agent_raw/          <- the project as kicad_generate_project wrote it
    ├── kicad/                  <- the final KiCad project
    │   ├── dual_adc.kicad_pro, .kicad_sch, .kicad_pcb, .kicad_prl
    │   ├── power, usb, frontend, adc, fpga, memory .kicad_sch
    │   ├── erc.rpt, drc.rpt, dual_adc.net, dual_adc_bom.csv
    │   ├── dual_adc_schematic.pdf, dual_adc_pcb_top.pdf, dual_adc.png (3D render)
    │   └── fab/                <- Gerbers, drill and positions
    ├── route/                  <- placed/prerouted/routed boards, DSN, SES, Freerouting logs
    └── scripts/                <- workarounds for server gaps
        ├── build_plan.py       <- writes the DesignPlan (single source of truth)
        ├── check_pins.py       <- pin coverage check of the plan
        ├── symlib.py           <- reads KiCad 10 .kicad_symdir libraries
        ├── sch_writer.py       <- label-based schematic writer
        ├── mcp_call.py         <- calls eda-agent tools in-process
        ├── build_pcb.py        <- 4 layers, FPIDs, symbol links, placement
        ├── board_sync.py       <- relinks the board to new schematic UUIDs
        ├── route_prep.py       <- plane fanout and DSN for Freerouting
        ├── post_route.py       <- imports the SES
        ├── fix_unrouted.py     <- grid A* router for leftover connections
        ├── surgery_lm27762*.py <- one-off local re-layout around the LM27762
        ├── cleanup_board.py    <- final board cleanup
        ├── patch_project.py    <- net classes (pcbnew Save rewrites .kicad_pro)
        └── check_pcb_nets.py, compare_netlist.py, plot_area.py, plot_draw.py
```
