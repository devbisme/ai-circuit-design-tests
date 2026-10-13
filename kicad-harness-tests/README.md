# kicad-harness — tests

## Tool under test

[kicad-harness](https://github.com/zxkmm/kicad-harness) is an Agent Skill plus a Python CLI, `kh`.
It has no MCP server and no LLM of its own; Claude Code reads the skill and runs `kh` from Bash.

- **The skill** (`SKILL.md`, `docs/`) sets the working rules: look up every library id, render
  every placement and look at the PNG, write schematics as `.kicad_sch` text, check with
  DRC/ERC, and generate missing footprints from datasheets. It also tells the agent to fix,
  commit and push the skill repo itself when it finds something wrong.
- **`kh`**, all output JSON:
  - Libraries: `sym` (search, pin numbers/coordinates, raw symbol body), `fp`, `validate`.
  - Queries: `info`, `ls` (positions, bounding boxes), `nets`, `netlist`, `bom`.
  - Renders: `view` (any board region or layer set → PNG), `sview` (schematic sheets → PNG).
  - Checks: `drc` (grouped by type, optional zone refill, schematic parity), `erc`.
  - Generation: `board-from-netlist` (netlist → `.kicad_pcb` with footprints and nets,
    headless), `place` (move footprints in the file), `outline` (rectangular Edge.Cuts).
  - Live (KiCad IPC): `live`, `exec <script.py>` (run kipy scripts against an open PCB editor).
- **Footprints from datasheets** are a documented procedure (`docs/footprints/`) using
  KiCad's wizard templates, not a command.
- **Not included:** a schematic API (schematics are text), an autorouter (the skill documents
  the Specctra DSN/SES bridge to an external router), and ratsnest in renders.

It can both create designs (schematic authoring recipes, `board-from-netlist`, `place`,
`outline`, footprint generation; the README's demo is a TP4056 charger built from scratch) and
review them (`drc`, `erc`, `netlist`, `nets`, `view`/`sview`; "Review your design" is one of
its stated uses). So it is tested as a **hybrid**.

Installation is described in [`setup.md`](setup.md).

- **Version:** commit db4bcdb (2026-10-11), package version 0.1.0, kicad-python 0.8.0.
- **Model:** Claude Opus 5.5 on a Claude Pro plan, Claude Code v2.1.296 (both runs).
- **Backend:** KiCad 10.0.4 (`~/bin/kicad10-root`: `kicad-cli` and the bundled Python 3.11
  `pcbnew`). Library lookups resolve to the KiCad 9.0.9 libraries in `/usr/share/kicad`
  (see `setup.md`).

## Why this tool

- It is a different shape from the MCP servers tested so far: a skill plus a CLI that Claude
  drives from Bash, with no tool-call schema in between.
- It gives the agent eyes: `view`/`sview` render any board region or sheet to a PNG that the
  agent is told to look at after every placement.
- `board-from-netlist`, `place` and `outline` cover the schematic → PCB step headlessly, which
  most of the other tools needed the KiCad GUI for.

## Runs

| Run | What it tests | Prompts | Outcome | Equiv. API cost | Time |
|---|---|---|---|---|---|
| [`analyze-1`](analyze-1/) | **Analysis** and JLCPCB fab outputs for an existing design (Konnect run 2) | 1 (multi-part, [`analysis_prompt.txt`](analyze-1/analysis_prompt.txt)) | ERC 0 errors, DRC 0 errors; 14 ranked findings; Gerbers, BOM, CPL, PNG. Found a `kh drc --refill` bug that reports 856 false violations | $3.02 | ~9 min |
| [`generate-1`](generate-1/) | A **full design** from the dual-ADC requirements | 1, plus 4 "keep going" while Freerouting ran ([`design_prompt.txt`](generate-1/design_prompt.txt)) | 6-sheet schematic and routed 4-layer board. ERC 0 errors, DRC 0 errors / 0 unconnected / 0 parity | $10.87 | ~1 h wall clock (~46 min of Claude working time) |

Each run directory has an `executive_summary.md`; start there. Costs are the equivalent
first-party API price of the tokens used (`claude_cost.txt`), not what the Pro subscription
billed. The findings in both runs have not yet been validated by hand.

### analyze-1: analyzer on an existing design

The input is the KiCad project produced by
[Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel 12-bit,
10 MS/s ADC board with a USB 2.0 interface (LTC2290 ADC, iCE40HX4K FPGA, SDRAM, FT2232H).
The `.kicad_*` files are unchanged copies; the run checked the board's md5 before and after.
The other tools' analysis runs used the same design.

Prompt: `do what analysis-prompt.txt says.` ([`analysis_prompt.txt`](analyze-1/analysis_prompt.txt)
asks for a design review, JLCPCB Gerbers, BOM and CPL, a dark-gray PCB PNG and an executive
summary.)

Quick look:

- **Checks:** `kh drc` gave 0 errors, 0 unconnected, clean schematic parity and 343 warnings.
  `kh erc` gave 0 errors; 201 of its warnings are a stale global library table and 2 are
  benign pin-type warnings.
- **Review method:** every sheet rendered with `kh sview` and read, `kh netlist` plus a
  pin-by-pin dump of every IC, `kh view` renders, and pcbnew scripts for decoupling distance,
  via-in-pad, layer use, pair lengths and stackup. Three datasheets/app notes were fetched and
  cited (FTDI AN_130, TI LM27762, ADA4817).
- **Findings (14, ranked):**
  - Assembly: no LCSC/MPN fields in the BOM; CPL rotations unverified; four through-hole parts.
  - Architecture: FT2232H channel B (the FPGA flash path) is dead while channel A runs sync
    FIFO; the LM27762 divider values check out but R406/R408 are just under the 50 kΩ minimum
    and PGOOD floats; likely over the USB suspend-current limit.
  - Layout: FPGA decaps 6–18 mm from their pins; the AFE sits over the digital +3V3 plane;
    the charge pump sits between the two AFE channels; 9 vias in the ADC's exposed pad;
    no stackup or net classes, so USB D+/D− impedance is uncontrolled; silkscreen overlaps.
  - A list of items that were checked and found correct (divider compensation, gain chain,
    VOCM, clock pins, VBUS capacitance, etc.).
- **Outputs:** `kh` has no fab export, so Gerbers, drill and CPL came from `kicad-cli` 10; the
  BOM came from `kh bom`. All are reformatted for JLCPCB in `analyze-1/jlcpcb/`.
- **kicad-harness problems found:**
  - `kh drc --refill` copies only `.kicad_pcb` and `.kicad_pro` to a temp directory, so the
    project's `.kicad_dru` rules are lost. Result: 856 false violations (499 clearance, 14
    track width). The skill says to "always use --refill".
  - ERC JSON coordinates are 100× too small (passed through from kicad-cli 10 unscaled).
  - `rsvg-convert` is not installed, so `view`/`sview` fail; an Inkscape shim in the
    scratchpad stood in.
- **Not done on purpose:** SKILL.md tells the agent to commit and push fixes to the skill
  repo. Claude didn't, because the user's rules require permission for any git action.

### generate-1: full design

The prompt is [`design_prompt.txt`](generate-1/design_prompt.txt), identical to the one used
for the other tools' design runs.

Prompts, in sequence in one session:

```
do what design_prompt.txt says.
```
```
keep going        (x4)
```

Claude ended its turn each time it was waiting on Freerouting in the background, so the
"keep going" prompts were needed to make it check progress. It then killed and relaunched
the router with fewer passes and finished the last 12 connections with its own A* router.

Quick look:

- **Design:**
  - Signal path: BNC → 1 MΩ‖15 pF 10:1 compensated attenuator → clamp → OPA810 buffer →
    THS4521 FDA (gain 0.95) → single-pole RC anti-alias filter (4.8 MHz) → LTC2290.
  - Capture and link: iCE40HX4K-TQ144 with an 8 MB IS42S16400J SDRAM (0.2 s at full rate,
    twice the requirement); FT232H in sync-245 FIFO mode; W25Q32 config flash.
  - Power: USB-B, about 256 mA estimated, so USB-C wasn't needed. TLV62569 buck (3.3 V),
    LP5907 (3.0 V), AP2112 (1.2 V), TPS60403 (−5 V).
  - Decisions with options are in the executive summary.
- **Schematic:** root plus 6 sheets (Power, FrontEnd, ADC, FPGA, Memory, USB), 163 parts,
  176 nets.
  - Written as label-based `.kicad_sch` text by Claude's `gen_sch.py` from a Python netlist
    (`design.py`); every symbol, footprint and pin number was looked up with `kh sym --pins`
    and `kh validate`.
  - The kicad-cli netlist matches `design.py` exactly. ERC: 0 errors, 2 warnings (FT232H
    symbol pin types).
- **PCB:** 120 × 88 mm, 4 layers: In1 GND plane, In2 +3V3 plane, signals on F/B.Cu.
  - `kh board-from-netlist` created the board. Claude's scripts did placement (anchors,
    FPGA pin swapping by angle with the pin map fed back to the schematic, greedy decap
    placement), net classes, plane zones and 196 locked fanout vias.
  - Freerouting 2.4.1 on a DSN with the plane nets removed left 12 unrouted; a small grid A*
    (`fix_route.py`) finished them. One net uses a short run on the In2 plane layer.
  - DRC (kicad-cli 10, refilled): 0 errors, 0 unconnected, 0 parity issues, 41 warnings.
  - Track minimum was relaxed to 0.10 mm because Freerouting necked some tracks.
- **Not ready for fab:**
  - FTDI, ADI and Lattice datasheets couldn't be downloaded, so FT232H, LTC2290 and iCE40
    pin wiring is from memory and is labelled that way.
  - ~250 mA draw before USB configuration (limit 100 mA); no load switch on PWREN#.
  - Single-pole anti-aliasing; USB D+/D− not routed as a 90 Ω pair; SDRAM bus not
    length-matched; fixed (not trimmable) probe compensation.
  - No FPGA gateware or host software.
- **kicad-harness / environment problems found:**
  - `kh` library lookups fell back to KiCad 9 libraries, where the USB-B shield pad is named
    `5` instead of `SH`. Fixed with project `sym-lib-table`/`fp-lib-table` files.
  - `rsvg-convert` missing (same Inkscape shim as run 1).
  - KiCad 10 pcbnew SWIG: `BOARD.Tracks()` breaks after `Remove()`, and removing Edge.Cuts
    drawings segfaults.
  - No autorouter in `kh`; the DSN/SES bridge to Freerouting is documented but scripted by
    Claude.
- **Not done on purpose:** no commits to the skill repo, as in run 1.

### Comparison of the two runs

- `kh` did most of the inspection and checking work in both runs, but Claude wrote 16
  Python scripts to do the actual design: schematic writing, placement, routing prep and route
  completion. kicad-harness is closer to a set of instruments than to a design tool.
- The skill's "render it and look" rule was followed in both runs and was useful for
  reviewing placement.
- Both runs found real `kh` bugs (`--refill` losing `.kicad_dru`, ERC coordinate scale) and
  environment gaps that the tool doesn't check for (`rsvg-convert`, stale library tables).

## Layout

```
kicad-harness-tests/
├── README.md                   <- this file
├── setup.md                    <- how kicad-harness was installed and configured
├── analyze-1/                  <- run 1: analysis of the Konnect run-2 design
│   ├── executive_summary.md    <- start here
│   ├── analysis_prompt.txt     <- the prompt
│   ├── claude_transcript.txt   <- the session
│   ├── claude_cost.txt         <- token usage and equivalent API cost
│   ├── session_cost.py         <- script that produced claude_cost.txt
│   ├── dual_adc_usb.kicad_pro, .kicad_pcb, .kicad_dru, .kicad_prl, .kicad_sch
│   ├── afe_a, afe_b, adc, fpga, usb, power .kicad_sch
│   ├── dual_adc_usb_pcb.png    <- PCB render on a dark-gray background
│   └── jlcpcb/                 <- Gerber zip, unzipped gerbers, JLCPCB BOM and CPL
└── generate-1/                 <- run 2: full design from the dual-ADC prompt
    ├── executive_summary.md    <- start here
    ├── design_prompt.txt       <- the prompt
    ├── claude_transcript.txt   <- the session
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produced claude_cost.txt
    ├── dual_adc/               <- the KiCad 10 project
    │   ├── dual_adc.kicad_pro, .kicad_pcb, .kicad_prl, .kicad_sch
    │   ├── Power, FrontEnd, ADC, FPGA, Memory, USB .kicad_sch
    │   ├── sym-lib-table, fp-lib-table  <- point at the KiCad 10 libraries
    │   ├── fab/                <- Gerbers, drill, pick-and-place, BOM, schematic PDF
    │   └── renders/            <- board front/back and schematic sheet PNGs
    ├── work/                   <- intermediate boards, DSN/SES, Freerouting log, DRC/ERC
    │                              JSON, renders
    └── scripts/
        ├── circuit.py          <- small netlist DSL (parts, pin->net maps, sheets)
        ├── design.py           <- the netlist: parts, values, footprints, pin->net
        ├── pins.py             <- symbol pin dump via `kh sym --pins`
        ├── pins10.py, fpinfo.py  <- pin and pad dumps read straight from the KiCad 10 libraries
        ├── sexp.py             <- small S-expression reader/writer
        ├── gen_sch.py          <- writes the label-based hierarchical schematic
        ├── verify_netlist.py   <- kicad-cli netlist vs design.py
        ├── place.py, pinmap.json  <- placement and FPGA pin reassignment
        ├── route_prep.py       <- net classes, plane zones, locked fanout, DSN export
        ├── edit_fanout.py      <- one-off fix to a bad GND fanout at U10
        ├── dsn_cut.py          <- removes plane nets from the DSN
        ├── import_ses.py       <- Freerouting SES import, pour refill
        ├── fix_route.py        <- grid A* for the connections Freerouting left
        └── prune.py, polish.py <- dead-end spur removal; outline, holes, silk
```
