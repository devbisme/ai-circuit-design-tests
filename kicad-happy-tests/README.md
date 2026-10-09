# kicad-happy — tests

## Tool under test

[kicad-happy](https://github.com/aklofas/kicad-happy) is a Claude Code plugin of 11 skills
(`kicad`, `spice`, `emc`, `datasheets`, `bom`, `digikey`, `mouser`, `lcsc`, `element14`,
`jlcpcb`, `pcbway`) that review and analyze existing KiCad designs. Its scripts parse
`.kicad_sch` / `.kicad_pcb` files directly with the Python standard library. It does not
create schematics or layouts, so it is an **analyzer**, not a generator.
Installation is described in [`setup.md`](setup.md).

- **Version:** kicad-happy 2.3.1. Skills used: `kicad`, `emc`, `spice`.
- **Model:** Claude Opus 5.5 on a Claude Pro plan, Claude Code v2.1.293.
- **Backend:** KiCad 10.0.4 `kicad-cli` (`/home/devb/bin/kicad10`) for ERC/DRC and zone
  refill; ngspice 44.2 for simulation.
- No distributor API keys and no datasheets were available, so sourcing, lifecycle and
  per-chip datasheet checks were not run.

## Input design

The design analyzed is the KiCad project produced by
[Konnect run 2](../konnect-tests/dual-adc-usb-2/): a 4-layer, 140 × 90 mm dual-channel
12-bit, 10 MS/s ADC board with a USB 2.0 interface (LTC2290 ADC, iCE40HX4K FPGA, SDRAM,
FT2232HL). The schematic files are unchanged copies of Konnect's. The `.kicad_pro` and
`.kicad_pcb` files differ because the session relaxed the design rules and refilled the
zones (see below).

## Quick look

One run so far: [`dual-adc-usb-1`](dual-adc-usb-1/). About 7 minutes of session time over
three prompts, $1.92 equivalent API cost.

- Found one real layout defect: the board was routed at ~0.15 mm clearance/width but its
  rules said 0.2 mm (524 DRC errors). At the user's request the rules were relaxed to
  0.15 mm and the zones refilled; DRC then showed 0 errors.
- Flagged missing MPNs, fiducials and test points, and thin via counts under some exposed
  pads.
- Several analyzer findings were false positives on inspection, including all 134 of the
  EMC ground-plane-gap findings.
- Every finding is a self-consistency check only, since no part has an MPN or datasheet.

For details, read [`dual-adc-usb-1/executive-summary.md`](dual-adc-usb-1/executive-summary.md).
I have not yet validated its findings myself.

## Prompts

Given in sequence in a single session (from `claude_transcript.txt`):

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

## Layout

```
kicad-happy-tests/
├── README.md                   <- this file
├── setup.md                    <- how kicad-happy was installed, verified and upgraded
└── dual-adc-usb-1/             <- run 1
    ├── executive-summary.md    <- what was run, findings, false positives, changes made
    ├── claude_transcript.txt   <- session transcript (/export)
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produced claude_cost.txt
    ├── dual_adc_usb.kicad_pro  <- KiCad project (rules relaxed to 0.15 mm by this run)
    ├── dual_adc_usb.kicad_pcb  <- board (zones refilled and saved by this run)
    ├── dual_adc_usb.kicad_prl  <- KiCad local settings
    ├── dual_adc_usb.kicad_sch  <- root schematic
    ├── afe_a.kicad_sch, afe_b.kicad_sch   <- analog front ends
    ├── adc.kicad_sch, fpga.kicad_sch, usb.kicad_sch, power.kicad_sch
    └── analysis/               <- kicad-happy output
        ├── manifest.json       <- run index and source-file hashes
        ├── capability_mode.json<- what was available (0 % datasheet coverage, no LLM review)
        └── 2026-10-07_1748/    <- analyzer reports, JSON
            ├── schematic.json, pcb.json, cross_analysis.json
            ├── emc.json, thermal.json, spice.json, parasitics.json
            ├── erc.json        <- KiCad ERC
            ├── drc.json        <- KiCad DRC, as received
            ├── drc_refill.json <- KiCad DRC after zone refill, old rules
            └── drc_after.json  <- KiCad DRC after rule change and refill
```

Notes:

- The reports in `analysis/2026-10-07_1748/` (except `drc_after.json`) describe the board
  *before* the rule change.
- `analysis/.gitignore`, written by kicad-happy, excludes everything in `analysis/` except
  `manifest.json` because the reports can be regenerated. Remove or edit it if the reports
  should be committed.
