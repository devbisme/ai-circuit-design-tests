# Null test — tests

## Tool under test

None. This is a **null test**: Claude Code with Claude Opus 5.5 and no KiCad-specific MCP
server, skill, plugin, subagent or memory. It is the baseline for the other tools in this
repo: their results can be read against what Claude does with only its built-in tools.

What it has to work with:

- Claude Code's built-in tools: Bash, Read, Write, Edit, web search and fetch.
- KiCad 10's own programs: `kicad-cli` (ERC, DRC, netlist, Gerber, drill, BOM, position,
  PDF/SVG export) and the `pcbnew` Python module in KiCad 10's bundled Python 3.11.
- Whatever else it finds on the machine. That includes KiCad-specific Python packages and
  CLIs that were not removed (`skidl`, `schematizer`, `kipart`, `kinet2pcb`, `kicad-skip`; see [`setup.md`](setup.md)).

Claude can both review and create designs, so this is tested as a **hybrid**, like
[kicad-harness](../kicad-harness-tests/) and [KiCad-AI-Assistant](../kicad-ai-assistant-tests/).
Setup, including what has to be turned off before each run, is in [`setup.md`](setup.md).

- **Version:** n/a (no tool).
- **Model:** Claude Opus 5.5 on a Claude Pro plan (both runs).
- **Claude Code version:** v2.1.301 (both runs).
- **Backend:** KiCad 10.0.4 (`~/bin/kicad10-root`: `kicad-cli` and the bundled Python 3.11
  `pcbnew`).

## Why this tool

*Draft:* every other tool here is judged by what it produced, but not against what Claude
would have produced without it. The null test supplies that comparison: the same two prompts,
the same model and the same KiCad 10, with none of the tools.

## Runs

| Run | What it tests | Prompts | Outcome | Equiv. API cost | Time |
|---|---|---|---|---|---|
| [`analyze-1`](analyze-1/) | **Analysis** and JLCPCB fab outputs for an existing design (Konnect run 2) | 1 (multi-part, [`analysis_prompt.txt`](analyze-1/analysis_prompt.txt)) | ERC 0 errors, DRC 0 errors; 15 ranked findings; Gerbers, BOM, CPL, PNG. Its top finding (clamp diodes miswired) is probably a false positive | $1.91 | ~6 min |
| [`generate-1`](generate-1/) | A **full design** from the dual-ADC requirements | 1, plus 1 "are you done?" while Freerouting ran ([`design_prompt.txt`](generate-1/design_prompt.txt)) | 10-sub-sheet schematic and routed 4-layer board. ERC 0 errors, DRC 0 errors / 0 unconnected / 0 parity. Signals routed through the In1 GND plane | $11.16 | ~2 h 42 min wall clock (~1 h 17 min of Claude working time) |

Each run directory has an `executive_summary.md`; start there. Costs are the equivalent
first-party API price of the tokens used (`claude_cost.txt`), not what the Pro subscription
billed. The findings in both runs have not yet been validated by hand.

### analyze-1: analyzer on an existing design

The input is the KiCad project produced by
[Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel 12-bit,
10 MS/s ADC board with a USB 2.0 interface (LTC2290 ADC, iCE40HX4K FPGA, SDRAM, FT2232H).
The `.kicad_*` files are unchanged copies. The other tools' analysis runs used the same
design.

Prompt: `do what aanalysis_prompt.txt says to do.` (typo as typed;
[`analysis_prompt.txt`](analyze-1/analysis_prompt.txt) asks for a design review, JLCPCB
Gerbers, BOM and CPL, a dark-gray PCB PNG and an executive summary.)

Quick look:

- **Checks:** `kicad-cli` ERC gave 0 errors, 155 library-mismatch warnings and 2 benign
  pin-type warnings. DRC with schematic parity gave 0 errors and 0 unconnected; the warnings
  are library mismatches and silkscreen.
- **Review method:** a netlist export and a per-IC pin-to-net dump (`out/pinmap.txt`) checked
  against datasheet knowledge, plus a script that parsed the `.kicad_pcb` for stackup, plane
  fills, track and via sizes and decap-to-pin distances (`out/pcbstat.txt`). **No datasheets
  were fetched**; part-behaviour claims are from memory and labelled *(datasheet recall)*.
- **Findings (15, ranked High/Medium/Low):**
  - High: BAV199DW input clamps wired so they do nothing; decoupling caps 6–22 mm from their
    pins on the ADC, FPGA, SDRAM, FT2232H and charge pump; the 10 MHz oscillator runs from
    the PWREN#-gated +3V0 rail, so the FPGA has no clock until USB enumerates.
  - Medium: FT2232H channel B (flash/FPGA programming) unusable while channel A is in sync
    FIFO; USB D+/D− not impedance-controlled; the unpowered ADC is back-powered through its
    outputs; the LM27762 charge pump sits between the two AFE channels; likely over the USB
    unconfigured/suspend current limits.
  - Low: single-pole anti-alias filter, shared ADC OVDD/VDD rail, no vias in the ADA4817
    pads, unprotected header GPIO, BNC overhang, silkscreen, library/field housekeeping.
  - A list of items that were checked and found correct (divider compensation, full-scale
    range, FDA common mode, regulator setpoints, LTC2290 configuration, FT2232H support
    parts, iCE40 configuration, SDRAM pinout, planes).
- **The clamp finding is probably wrong.** [eda-agent 1](../eda-agent-tests/dual-adc-usb-1/)
  and [KiCad-AI-Assistant 1](../kicad-ai-assistant-tests/dual-adc-usb-1/) downloaded the
  Diodes BAV199DW datasheet (ds30417) and found that KiCad's pin names are misleading but the
  real package clamps correctly. This run read only the KiCad pin names. It did add "verify
  that the symbol's pin numbering matches the real BAV199DW package", but still ranked the
  finding first. Not yet checked by hand.
- **Outputs:** Gerbers and Excellon drill from `kicad-cli` (Protel extensions, zipped), a
  JLCPCB-format BOM (LCSC column empty) and CPL in `fab/`, and `dual_adc_usb_pcb.png` at
  400 dpi on #3a3a3a. Intermediate reports are in `out/`.
- **Didn't read anything outside the run directory**, as far as the transcript shows.

### generate-1: full design

The prompt is [`design_prompt.txt`](generate-1/design_prompt.txt), identical to the one used
for the other tools' design runs (the version with the KiCad 10 path line).

Prompts, in sequence in one session:

```
create the design described in design_prompt.txt
```
```
are you done?
```

The session ended its turn several times while Freerouting ran in the background, and the
router's completion notices re-started it. Once it ended its turn saying it was waiting on a
second routing pass over the routed board; after about 17 minutes, "are you done?" got it to
check. That pass had gone from 4 unrouted to 60, so Claude stopped it and went back to the first pass's board.

Quick look:

- **Design:**
  - Signal path: BNC → 1 MΩ‖20 pF attenuator with its bottom leg on a REF3020 2.048 V
    reference → BAV199 clamps → OPA356 buffer → THS4521 FDA (other input gets a buffered copy
    of the attenuator's rest voltage) → RC → LTC2290. ±10.09 V full scale, ~4.4 MHz
    bandwidth, 2nd-order anti-aliasing.
  - Capture and link: iCE40HX4K-TQ144 with an 8 MB IS42S16400J SDRAM (0.2 s at full rate,
    twice the requirement); FT232H in sync-245 FIFO mode; SPI config flash programmed from a
    2×4 header.
  - Clock: 10 MHz XO on the 3.0 V analog rail, buffered to the ADC and an FPGA global clock
    pin.
  - Power: USB-B, ~260 mA estimated, so USB-C wasn't needed. TPS62160 buck (3.3 V), AP2112
    (1.2 V), LP5907 (4.5 V analog, 3.0 V ADC/clock). Single supply; no negative rail.
  - The ten decisions (options → choice) are in the executive summary.
- **Schematic:** written in SKiDL (`dual_adc.py`) and drawn by schematizer as a root plus 10
  sub-sheets.
  - The `kicad-cli` netlist of the drawn schematic matches the SKiDL netlist
    (`compare_nets.py`, 0 differing nets). That check caught a schematizer bug that drew a
    PLL-filter R on top of its C and shorted +1V2 to GND.
  - KiCad ERC: 0 errors, 435 warnings (off-grid wire ends, library-copy mismatches, 2
    intentional flash WP/HOLD ties).
- **PCB:** 140 × 95 mm, 4 layers (In1 GND plane), 182 footprints, 339 vias.
  - Claude's `make_pcb.py` (KiCad 10 `pcbnew`) loaded footprints, assigned nets, did
    rule-based placement, the outline and the In1 plane. `route.py` handled DSN export,
    SES import, pours and copying symbol fields onto footprints.
  - Freerouting 2.4.1 took four full runs (10–30 min each). Run 3 left 0 unrouted and is the
    delivered board. Run 4, with In1 reserved for GND, left 4 signals and ~19 GND pads
    unconnected and was rejected.
  - DRC (KiCad 10, with schematic parity): 0 errors, 0 unconnected, 0 parity, 30 warnings.
    Track and hole minimums were relaxed to 0.10 mm / 0.25 mm for router neck-downs and the
    buck's thermal vias.
- **Not ready for fab:**
  - Freerouting put 81 nets (~1.7 m of track) on the In1 GND plane, including under the
    ADC. The summary calls this the biggest layout weakness.
  - USB D+/D− not routed as a 90 Ω pair; ~260 mA draw before enumeration (limit 100 mA);
    fixed (not trimmable) attenuator compensation.
  - No datasheets were re-read; LTC2290, FT232H, THS4521, iCE40, TPS62160 and REF3020
    details are from memory and labelled that way. Not simulated.
  - No Gerbers or drill files (the prompt didn't ask for them). No FPGA gateware or host
    software.
- **Problems hit:** schematizer crashed on footprint-only parts, needed `auto_stub=True` to
  route, and overlapped two parts (above); the OPA356 SOIC symbol's hidden NC pins landed on
  nets; `pcbnew`'s `board.Save()` overwrites `.kicad_pro` with default rules, so
  `write_project.py` re-applies them after every save.

### Was the null test clean?

Not entirely; both points come from the end of the generate-1 transcript and from
`setup.md`.

- **KiCad-specific packages were used.** generate-1 built the schematic with SKiDL and
  schematizer, which `setup.md` left installed. Claude also read schematizer's README and
  source to work around its bugs. analyze-1 used only `kicad-cli` and its own Python.
- **generate-1 read the repo-root README.** Asked afterwards, Claude said it read the root
  `README.md`, including the "Comparable runs" table, and that the table "is why I aimed for
  a routed, DRC-clean 4-layer board instead of stopping at a schematic". It said it chose the
  architecture before opening the README and copied no design details, but couldn't rule out
  an influence on later choices. It read none of the other tools' design files or reports.
  For future runs, moving that table aside or blocking reads above `null-tests/` would close
  this leak.

### Comparison of the two runs, and with the other tools

- **Cost:** analyze-1 ($1.91) is the cheapest of the analysis runs on this design
  ($1.92–$3.71). generate-1 ($11.16) is close to kicad-harness 2 ($10.87), the cheapest of
  the tool-assisted design runs ($10.87–$61.12).
- **Datasheets:** neither run fetched a datasheet. The tools whose runs did (eda-agent and
  KiCad-AI-Assistant in their analysis runs) avoided the clamp false positive. Fetching
  datasheets isn't something those tools add; it is a choice the session made.
- **Gap filling:** generate-1 looks like the tool-assisted design runs from the other side:
  they also ended with Claude-written scripts for placement and routing, plus Freerouting.
  The difference is the schematic, which here came from SKiDL and schematizer rather than
  the tool under test.
- **Same weak spots as the other design runs:** USB pair impedance, unconfigured USB current,
  silkscreen, and part details from memory.

## Layout

```
null-tests/
├── README.md                   <- this file
├── setup.md                    <- what was turned off for the runs, and why
├── analyze-1/                  <- run 1: analysis of the Konnect run-2 design
│   ├── executive_summary.md    <- start here
│   ├── analysis_prompt.txt     <- the prompt (unchanged copy of the repo-root one)
│   ├── CLAUDE.md               <- empty project memory file
│   ├── claude_transcript.txt   <- the session
│   ├── claude_cost.txt         <- token usage and equivalent API cost
│   ├── session_cost.py         <- script that produced claude_cost.txt
│   ├── dual_adc_usb.kicad_pro, .kicad_sch, .kicad_pcb, .kicad_prl, .kicad_dru
│   ├── adc, afe_a, afe_b, fpga, power, usb .kicad_sch
│   ├── dual_adc_usb_pcb.png    <- PCB render on a dark-gray background
│   ├── fab/                    <- Gerber zip, unzipped gerbers, JLCPCB BOM and CPL
│   └── out/                    <- ERC/DRC JSON, netlist, pin map, PCB stats, raw BOM/pos, SVG
└── generate-1/                 <- run 2: full design from the dual-ADC prompt
    ├── executive_summary.md    <- start here
    ├── design_prompt.txt       <- the design prompt
    ├── CLAUDE.md               <- empty project memory file
    ├── claude_transcript.txt   <- the session
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produced claude_cost.txt
    ├── dual_adc.py             <- SKiDL description of the circuit (source of truth)
    ├── dual_adc.kicad_pro, .kicad_sch, .kicad_pcb, .kicad_prl
    ├── dual_adc_*.kicad_sch    <- 10 sub-sheets drawn by schematizer
    ├── dual_adc_schematic.pdf, dual_adc_top.png, dual_adc_bom.csv
    ├── dual_adc.net, dual_adc_sch.net  <- SKiDL netlist / netlist of the drawn schematic
    ├── dual_adc.xml, dual_adc.erc, dual_adc.log  <- SKiDL outputs
    ├── erc.rpt, drc.rpt        <- final KiCad 10 ERC/DRC reports
    ├── dual_adc.dsn, dual_adc.ses, freerouting.log  <- Freerouting input/output
    ├── fix_sch.py              <- schematic post-fix (PWR_FLAG footprints)
    ├── compare_nets.py         <- netlist-vs-netlist check
    ├── make_pcb.py             <- footprints, nets, placement, outline, In1 plane
    ├── route.py                <- DSN export, SES import, pours, symbol-field relink
    ├── finish_board.py         <- starved-thermal fixes, board-only holes, zone refill
    └── write_project.py        <- writes .kicad_pro design rules and net classes
```
