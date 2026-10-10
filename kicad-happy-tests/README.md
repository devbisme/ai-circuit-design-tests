# kicad-happy — tests

## Tool under test

[kicad-happy](https://github.com/aklofas/kicad-happy) is a Claude Code plugin of 11 skills
(`kicad`, `spice`, `emc`, `datasheets`, `bom`, `digikey`, `mouser`, `lcsc`, `element14`,
`jlcpcb`, `pcbway`) that review and analyze existing KiCad designs. Its scripts parse
`.kicad_sch` / `.kicad_pcb` files directly with the Python standard library. It does not
create schematics or layouts, so it is an **analyzer**, not a generator.
Installation is described in [`setup.md`](setup.md).

- **Version:** kicad-happy 2.3.1.
- **Model:** Claude Opus 5.5 on a Claude Pro plan.
- **Backend:** KiCad 10.0.4 `kicad-cli` (`/home/devb/bin/kicad10`) for ERC/DRC and zone
  refill; ngspice 44.2 for simulation.
- No distributor API keys were available, so sourcing and lifecycle checks were not run.

## Runs

The two subdirectories test kicad-happy in different roles:

| Run | Purpose | kicad-happy's role | Session |
|-----|---------|--------------------|---------|
| [`dual-adc-usb-1`](dual-adc-usb-1/) | Review an **existing** design | The whole job: analyze and report | ~7 min, 3 prompts, $1.92 |
| [`dual-adc-usb-2`](dual-adc-usb-2/) | Design a board **from scratch**, with kicad-happy installed | Review step inside a larger design flow | ~3.5 h, 2 prompts, $29.37 |

Costs are equivalent first-party API cost, not what the Pro plan billed.

### dual-adc-usb-1: analyzer on an existing design

Tests kicad-happy as advertised: point it at a finished KiCad project and see what it
finds.

- **Input:** the KiCad project produced by
  [Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel
  12-bit, 10 MS/s ADC board with USB 2.0 (LTC2290 ADC, iCE40HX4K FPGA, SDRAM, FT2232HL).
  The schematic files are unchanged copies of Konnect's. The `.kicad_pro` and
  `.kicad_pcb` differ because the session relaxed the design rules and refilled the zones.
- **Skills used:** `kicad`, `emc`, `spice`. No datasheets were available.
- **Claude Code:** v2.1.293.
- **Results:**
  - Found one real layout defect: the board was routed at ~0.15 mm clearance/width but its
    rules said 0.2 mm (524 DRC errors). At the user's request the rules were relaxed to
    0.15 mm and the zones refilled; DRC then showed 0 errors.
  - Flagged missing MPNs, fiducials and test points, and thin via counts under some
    exposed pads.
  - Several findings were false positives on inspection, including all 134 EMC
    ground-plane-gap findings.
  - Every finding is a self-consistency check only, since no part has an MPN or datasheet.
- **Details:** [`executive-summary.md`](dual-adc-usb-1/executive-summary.md). I have not
  yet validated its findings myself.

Prompts, in sequence in one session (from `claude_transcript.txt`):

```
use kicad-happy to analyze the kicad project in this directory. A KiCad 10
executable is in /home/devb/bin/kicad10.
```
```
relax the rules to 0.15 mm, refill and save the board
```
```
write an executive summary file explaining what you did and what results were
found for this kicad project.
```

### dual-adc-usb-2: full design with kicad-happy available

Tests whether having kicad-happy installed helps Claude produce a design from a
requirements prompt. kicad-happy cannot create schematics or layouts, so Claude built the
board with SKiDL, its own scripts, and Freerouting, then used kicad-happy to review it.
The prompt is identical to the one used in Konnect run 2 and both kicad-mcp-server runs,
and it forbids reusing outputs of other designs in the tree.

- **Input:** [`dual-adc-prompt.txt`](dual-adc-usb-2/dual-adc-prompt.txt) only.
- **Skills used:** the full analysis suite (schematic, PCB, cross-domain, EMC, thermal,
  Gerber, SPICE). Datasheets were downloaded for most parts, but not for the
  LTC2291 ADC or the FT2232H.
- **Claude Code:** v2.1.295.
- **Result (as reported by the session):** a complete KiCad 10 project. It has a
  130 × 90 mm 4-layer board (LTC2291, iCE40HX4K, 8 MB SDRAM, FT2232H, USB-B), 0 ERC
  violations, 0 DRC errors, 100 % MPN coverage, and fab outputs.
  - Open items include unverified ADC and USB-bridge pin wiring, 0.1 mm track/space on the
    ADC bus, a 2nd-order anti-alias filter, and high EMC risk.
  - SKiDL's built-in schematic generator produced a wrong schematic, so Claude wrote a
    replacement (`scripts/sch_writer.py`).
- **Details:** [`executive_summary.md`](dual-adc-usb-2/executive_summary.md),
  [`design_decisions.md`](dual-adc-usb-2/design_decisions.md),
  [`design_review.md`](dual-adc-usb-2/design_review.md), and the run's own
  [`README.md`](dual-adc-usb-2/README.md) (file map and regeneration commands). I have
  not yet validated the design myself.

Prompts, in sequence in one session (from `transcript.txt`):

```
create the design described in dual-adc-prompt.txt
```
```
create an executive_summary.md file explaining what was done.
```

## Layout

```
kicad-happy-tests/
├── README.md                   <- this file
├── setup.md                    <- how kicad-happy was installed, verified and upgraded
├── dual-adc-usb-1/             <- run 1: analysis of an existing design
│   ├── executive-summary.md    <- what was run, findings, false positives, changes made
│   ├── claude_transcript.txt   <- session transcript (/export)
│   ├── claude_cost.txt         <- token usage and equivalent API cost
│   ├── session_cost.py         <- script that produced claude_cost.txt
│   ├── dual_adc_usb.kicad_pro  <- KiCad project (rules relaxed to 0.15 mm by this run)
│   ├── dual_adc_usb.kicad_pcb  <- board (zones refilled and saved by this run)
│   ├── dual_adc_usb.kicad_prl  <- KiCad local settings
│   ├── dual_adc_usb.kicad_sch  <- root schematic
│   ├── afe_a.kicad_sch, afe_b.kicad_sch   <- analog front ends
│   ├── adc.kicad_sch, fpga.kicad_sch, usb.kicad_sch, power.kicad_sch
│   └── analysis/               <- kicad-happy output
│       ├── manifest.json       <- run index and source-file hashes
│       ├── capability_mode.json<- what was available (0 % datasheet coverage, no LLM review)
│       └── 2026-10-07_1748/    <- analyzer reports, JSON
│           ├── schematic.json, pcb.json, cross_analysis.json
│           ├── emc.json, thermal.json, spice.json, parasitics.json
│           ├── erc.json        <- KiCad ERC
│           ├── drc.json        <- KiCad DRC, as received
│           ├── drc_refill.json <- KiCad DRC after zone refill, old rules
│           └── drc_after.json  <- KiCad DRC after rule change and refill
└── dual-adc-usb-2/             <- run 2: design from scratch (file map in its README.md)
```

Notes on run 1:

- The reports in `analysis/2026-10-07_1748/` (except `drc_after.json`) describe the board
  *before* the rule change.
- `analysis/.gitignore`, written by kicad-happy, excludes everything in `analysis/` except
  `manifest.json` because the reports can be regenerated. Remove or edit it if the reports
  should be committed.
