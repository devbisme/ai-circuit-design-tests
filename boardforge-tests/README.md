# boardforge — tests

## Tool under test

[boardforge](https://github.com/devbisme/boardforge) turns a SKiDL circuit into a routed,
manufacturable KiCad board, headless. It has two parts:

- **A Python CLI, `boardforge`.** A project is a directory with a SKiDL file and a
  `boardforge.toml`. The CLI runs:
  - The physical pipeline (`run`, or one stage at a time): C1 `sch` (SKiDL → netlist →
    labels-only KiCad schematic via schematizer, SKiDL and KiCad ERC, netlist parity), C2
    `board`, C3 `place` (anchors, regions, FPGA/MCU pin swapping, compaction, a routability
    estimate), C4 `route` (Freerouting, then a built-in A*), C5 `check` (DRC, geometry
    checks, vendored kicad-happy 2.3.1 analyzers, thermal), C6 `fab` (JLCPCB Gerbers, BOM,
    CPL, schematic PDF, renders).
  - The B4 review gate (`review`): `constraints.json` checked against the design with
    ngspice path testbenches, rail-current budgets, datasheet absolute-max and power-pin
    checks, footprint-vs-datasheet package checks and a BOM diff.
  - A datasheet cache (`datasheets status | sync | add | check | show | publish | paths`),
    plus `render`, `status` and `doctor`.
- **A Claude Code plugin** (adapted from skidl-skills). `/new-circuit` drives seven phases:
  requirements (interview) → architecture and `constraints.json` (`circuit-architect`) →
  sourcing (`part-sourcer`) → datasheet extractions (`datasheet-librarian`) → SKiDL code
  (`skidl-coder`, or block coders plus `skidl-assembler`) → review (`erc-reviewer`) → board
  (the driver, using the CLI). There is an approval gate after each phase. Other skills:
  `design-review`, `erc-rules`, `find-part` (pcbparts MCP, with `skidl-part-search` as the
  fallback). Four hooks guard Bash calls, check written files, and print status at session
  start and stop.

The design-creating parts are `/new-circuit`, its agents, and `boardforge run`. The review
parts (`boardforge review`, `/design-review`, the C5 checks) all work on a boardforge SKiDL
project, not on an arbitrary KiCad design. So it is tested as a **generator** only.
Installation is described in [`setup.md`](setup.md).

- **Version:** boardforge 0.1.0 (PyPI). The plugin is 0.1.0 at commit 437b70d (2026-10-16),
  installed as `boardforge@devbisme-skills`.
- **Model:** Claude Opus 5.5 for the driver and the opus agents; Claude Sonnet 5.5 for
  `part-sourcer` (both set by the agents' frontmatter).
- **Claude Code version:** v2.1.302 (v2.1.301 at setup time).
- **Backend:** KiCad 10.0.4 (`~/bin/kicad10-root`: `kicad-cli` and the bundled Python 3.11
  `pcbnew`), SKiDL 3.0.0, schematizer 0.2.0, Freerouting 2.4.1, ngspice 44.2.

## Why this tool

<!-- TODO (author): drafted by Claude from the tool's description; replace with your own reasons. -->
- It is the successor to [skidl-skills](../skidl-skills-tests/), and it moves everything
  deterministic into a CLI: running the design, ERC, review gates, placement, routing and
  fab outputs. Agents only make decisions and call commands. The test is whether that
  lowers cost and gets further than skidl-skills, which stopped at a netlist.
- It covers the whole flow from prompt to fab files, with numeric review gates
  (`constraints.json` checked with ngspice) that the other generators don't have.

## Runs

| Run | What it tests | Prompts | Outcome | Equiv. API cost | Time |
|---|---|---|---|---|---|
| [`generate-1`](generate-1/) | A **full design** from the dual-ADC requirements | 1 ([`design_prompt.txt`](generate-1/design_prompt.txt)); no phase-gate approvals were needed (the prompt says not to pause) | 9-block SKiDL design → routed 4-layer 100 × 80 mm board, 239 parts. ERC 0 errors, netlist parity 217/217, review gate PASS, DRC 0 errors, release gate PASS. The C6 CPL dropped 80 parts (boardforge bug), fixed by hand | $23.89 | ~2 h 40 min wall clock (~8 min of it waiting out a session limit) |

### generate-1: full design

The prompt is [`design_prompt.txt`](generate-1/design_prompt.txt), identical to the one used
for the other tools' design runs (the dual-ADC prompt with the KiCad 10 path line).

Prompts, in sequence in one session:

```
create the design described in design-prompt.txt.
```

Claude invoked `/new-circuit` itself. Because the prompt says to choose options and not pause,
the driver ran phase 1 (requirements) without asking anything. Every requirement the prompt
didn't state is tagged `(driver)` in `SPEC.md`: 1 MΩ input, ±30 V protection, 1 MHz
passband, 4 layers, JLCPCB at qty 5. Each later approval gate was approved automatically.
One API session limit killed the datasheet agent partway through. The harness's "limit has
reset" message restarted the session, and the agent was resumed with its work intact.

Quick look:

- **Design:**
  - Signal path: BNC → 1 MΩ attenuator with a trimmer for probe compensation → BAV199
    clamp → OPA2810 buffer and two Sallen-Key stages → THS4551 FDA (MFB stage) → RC →
    ADS5231 (dual simultaneous 12-bit). The anti-alias filter has 7 poles: −80.9 dB at
    5 MHz nominal, −78.7 dB Monte-Carlo worst case (requirement ≥ 72 dB at fs/2).
  - Capture and link: XC6SLX9 Spartan-6 with a 16 MB W9812G6KH SDRAM (0.42 s at full rate)
    → FT232H sync FIFO → USB-C (USB 2.0 HS). W25Q32 config flash, JTAG and TRIG headers.
  - Power: 0.43 A worst case, so standard USB 2.0 power is enough; USB-C kept anyway.
    TLV62569 buck (3.3 V), TLV757 (1.2 V), LP5907 (3.3 V analog), LM27762 (±4 V).
  - 9 blocks (afe_channel instantiated twice), so the modular coding mode was used: 5 block
    work orders, then `skidl-assembler`.
- **Gates:**
  - Assembly first gave KiCad ERC 4 errors (missing power flags, J501 shield pin) and a BOM
    FAIL: none of the block coders set `LCSC` fields, though the rules require them.
  - One fix pass followed. It added the LCSC fields, 2 flags, the shield pin, and an R705
    pull-up for the LM27762 PGOOD pin; Claude added R705 to the BOM.
  - After that: SKiDL and KiCad ERC 0 errors, parity 217/217, `boardforge review` 43 PASS /
    0 FAIL / 13 NOT CHECKED, BOM PASS. `erc-reviewer` passed the design with 3 MEDIUM
    findings.
- **PCB (`boardforge run --from c2`):** 100 × 80 mm, 4 layers (In1 GND, In2 +3V3, GND pours
  on both outer layers).
  - Claude wrote the floorplan: 15 anchors, with the BNCs on the left edge, USB-C on the
    right, and the AFE → ADC → FPGA → FT232H chain left to right. One extra placement
    round anchored the USB ESD part U501, which C3 had put mid-board.
  - Routing took 11.4 min. Freerouting left 2 unrouted and 64 DRC errors; the A* router
    cleaned them up to 0/0.
  - DRC: 0 errors, 50 warnings (silkscreen 36, dangling stubs 9, hole-to-hole 5). Release
    gate PASS 12/12. 714 vias.
- **Not ready for fab:**
  - ADS5231 AVDD/VDRV abs-max is briefly exceeded at power-up (review W2; the fix is a
    one-net change, but it alters a block's signature). FT232H VREGIN sits at its 3.3 V
    minimum (W3).
  - ADS5231: single source, 152 in stock.
  - Facts that could not be verified:
    - The 12 MHz crystal has no datasheet.
    - The oscillator's jitter is unspecified.
    - The SDRAM facts come from the W9812G6JH datasheet.
  - The custom BNC and trimmer footprints have not been checked against their drawings.
  - No FPGA gateware, FT232H EEPROM image or host software.
- **boardforge problems found:**
  - **C6 CPL drops parts.**
    - Cause: `kicad-cli sch export bom` groups designators into ranges (`C1001-C1022`),
      and `_expand_designators` in the vendored `translate_bom_pnp.py` doesn't expand
      them. The CPL's BOM filter therefore silently dropped 80 of 239 parts.
    - Workaround: Claude regenerated the BOM and CPL in `build/fab/` with the ranges
      expanded, using boardforge's own adapter.
    - Fix: pass `--ref-range-delimiter ""` to the export call in `physical.py`.
    - Re-running `boardforge fab` brings the bug back.
  - **Review gate can't check a custom dual op-amp.** The SPICE path checks (GAIN and
    ALIAS, both HARD) report NOT CHECKED because boardforge can't map the OPA2810
    symbol's pin names (`VIN1+`, `VO1`) to op-amp roles, and `[review.models]` takes only
    one pin map per part. `erc-reviewer` re-ran the checker with the names mapped: 12/12
    pass (`build/reports/spice_patched/`).
  - **Stale stock data.** The `stock-check.py` mirror reported 7 in stock for the W25Q32;
    live stock was 12,414. The sourcer used pcbparts instead.
  - **Run-to-run netlist differences.** The symbol definitions of multi-unit parts list
    their pins in a different order on each run, so `diff` reports the netlists as
    different even though components and nets are identical.
  - **Other C4/C5 warnings:**
    - C4: fanout failed for 2 FPGA GND pads, and the copper cleanup was skipped because it
      would have disconnected 3 items.
    - C5: rail-current analysis doesn't recognise the LM27762's ±4 V outputs.
    - C6: 12 parts have CPL rotation offsets from an unverified table.
    - KiCad ERC: 258 `lib_symbol_mismatch` warnings.
  - **Agent behaviour:**
    - Block coders used two different conventions for power flags (`drive = POWER` vs
      `PWR_FLAG`), which caused 2 of the ERC errors.
    - The architect and sourcer returned receipts over the 10-line limit.

## Layout

```
boardforge-tests/
├── README.md                   <- this file
├── setup.md                    <- how boardforge was installed and configured
└── generate-1/                 <- run 1: full design from the dual-ADC prompt
    ├── .claude/settings.local.json  <- enables the plugin for this directory only
    ├── design_prompt.txt       <- the design prompt
    ├── claude_transcript.txt   <- session transcript (/export)
    ├── claude_cost.txt         <- token usage and equivalent API cost
    ├── session_cost.py         <- script that produces claude_cost.txt
    ├── executive_summary.md    <- what was done, results, risks
    ├── SPEC.md                 <- requirements, user vs. driver provenance
    ├── design_state.json       <- pipeline state written by the /new-circuit driver
    ├── handoffs/               <- one handoff per phase (and per block in 05_blocks/)
    ├── architecture/           <- block diagram, net plan, IC selection, risks, AFE SPICE deck
    ├── constraints.json        <- numeric review-gate constraints (ac_gain, rail_current)
    ├── sourcing/               <- sourced_bom.md / .csv
    ├── datasheets/             <- PDFs, extracted/*.json, *_SUMMARY.md
    ├── symbols/, footprints/   <- custom ADS5231/OPA2810 symbols, BNC and trimmer footprints
    ├── circuits/dual_adc_10msps/  <- SKiDL package: 9 block files + __main__.py
    ├── boardforge.toml         <- design, board and floorplan settings
    ├── review_report.md        <- erc-reviewer's phase 6 report
    └── build/                  <- kicad/ (schematic, board), reports/, renders/, fab/
```
