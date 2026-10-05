# SKiDL Skills plugin — tests

## Tool under test

The [SKiDL Skills](https://github.com/devbisme/skidl-skills) plugin for Claude Code is a
multi-agent pipeline that takes a plain-English board description to a KiCad netlist, with
SKiDL Python code as the intermediate representation.

- **Plugin:** `~/.claude/skills/skidl-skills` (symlink to `~/projects/AI/skills/skidl-skills`).
  It currently has 7 agents: circuit architect, part sourcer, datasheet librarian, SKiDL
  coder, block coder, assembler and ERC reviewer. It also has skills (`new-circuit`,
  `find-part`, `erc-rules`, `design-review`), hooks and helper scripts. Runs 1–2 used a
  separate `orchestrator` agent. From run 3 on, the main Claude Code session drives the
  pipeline itself.
- **Pipeline:** requirements → architecture → sourcing → datasheets → coding (modular:
  one `@subcircuit` file per block) → assembly → independent ERC gate → netlist/BOM export.
  Handoff files in `handoffs/` carry each phase's result, and `pipeline_state.json` is the
  resume point.
- **Model:** Claude Opus 5 drives runs 1–7; subagents use a mix of Opus 5 and Sonnet 5.
  Run 8 is driven by **Opus 5.5** (Sonnet 5 subagents). Claude Code v2.1.263 → v2.1.283
  across the runs, all on a Claude Pro plan.
- **Backend:** SKiDL 3.0.0 (runs 2–7) and 2.3.0 (run 8, per its netlist header), KiCad 9
  symbol/footprint libraries.
- Layout and routing are out of scope. The deliverable is a netlist.
- **The plugin changed during the test series.** Run 3's session measured its own cost and
  then refactored the plugin: capped coder fan-out, write-as-you-go agents, script-based
  hooks, validated PDF fetching, and a part cache with an off switch. Runs 4–7 ran the
  revised plugin, and runs 6–8 show pipeline state v5.1. Runs 1–3 and 4–8 are therefore
  not strictly comparable, and run 8 also changed model and SKiDL version at once.

## Why this tool

1. It's very easy to use (it's just a skill that can be run in Claude Code).
2. It uses SKiDL and I'm interested in how that performs.

## Quick look

I've run eight trials of `skidl-skills` in an attempt to reduce the cost and time required
to produce a design.
The fastest, cheapest, and most interesting is the last run: `dual-adc-usb-8`.
That result could arise from:
* Optimization of the skill.
* Using the new Opus 5.5 (earlier runs used older models; see **Model** above).
* Pure luck.

You can make a quick assessment of the [`dual-adc-usb-8`](dual-adc-usb-8/) run using these files:
* The prompt that initiates the design flow: `dual-adc-prompt.txt`.
* An executive summary describing the design phases: `executive_summary.md`.
* A more detailed description: `README.md`.
* An even more detailed sequence of Claude's operations: `claude_transcript.txt`.
* An executable Jupyter design doc: `dual_adc_usb.ipynb`.

I have not validated any of these designs for correctness.
That will be my next task now that I have been able to generate a design
within a reasonable time with a reasonable cost.
I will report the results of my validation here when I'm done.

## The design problem

Base prompt (all runs):

```
Design a dual-channel ADC board that accepts signals in the range [-10V, +10V] and samples them
at 10 MHz with a resolution of 12 bits.
The signals should enter the board through connectors that mate with standard oscilloscope leads.
The board should interface to a host through a USB 2.0 port
that provides power as well as transfer of digitized signal samples.
```

It is deliberately under-specified and contains one hard contradiction: 2 ch × 10 MSPS ×
12 bit = 240 Mbit/s sustained, which USB 2.0 high-speed can't reliably carry. **Every run
detected this** and resolved it with on-board burst capture. That is still the most
consistent result in this directory.

Prompt variants:

| Runs | Additions to the base prompt |
|---|---|
| 1 | none; the user answered interview questions and approved each gate |
| 2–4 | "list the options and pick one; do not pause for my input" + "start from a blank slate; ignore other designs in this tree" |
| 5–8 | the above, plus "a minimum of 0.1 s of samples at the maximum rate" and "if insufficient power is available, use a USB C port" |

Runs 2–4 share one prompt and runs 5–8 share another, so each group shows how much the
output varies between runs.

## Runs

| Run | Dates | Reached | ERC (err/warn) | Parts / nets | Equiv. API cost | Elapsed | Notes |
|---|---|---|---|---|---|---|---|
| [`dual-adc-usb-1`](dual-adc-usb-1/) | 09-06 → 09-07 | coding/assembly | 0 / 14 | not exported | not measured | ~27 h | stopped by monthly spend limit |
| [`dual-adc-usb-2`](dual-adc-usb-2/) | 09-08 → 09-09 | export | 0 / 33 | 238 / 200 | not measured | ~22 h | BOM unverified (no parts MCP) |
| [`dual-adc-usb-3`](dual-adc-usb-3/) | 09-09 → 09-10 | export | 0 / 0 | 218 / 136 | $124.91 ¹ | ~9 h | all 9 block coders killed; driver wrote 5 blocks |
| [`dual-adc-usb-4`](dual-adc-usb-4/) | 09-10 → 09-11 | export + design review | 0 / 0 | 204 / 169 | $93.45 | ~18 h | cheapest on Opus 5; aliasing risk accepted |
| [`dual-adc-usb-5`](dual-adc-usb-5/) | 09-20 → 09-21 | export | 0 / 19 | 175 / 150 | $149.87 | ~21 h | 2 arch. reworks; depends on host decimation |
| [`dual-adc-usb-6`](dual-adc-usb-6/) | 09-21 → 09-22 | export | 0 / 2 | 243 / 186 | $175.32 | ~19 h | most verified; first ERC gate FAILED correctly |
| [`dual-adc-usb-7`](dual-adc-usb-7/) | 09-22 → 09-23 | export | 0 / 0 | 170 / 127 | $155.97 | ~21 h | 2 arch. reworks; first run with BOM-vs-code gate |
| [`dual-adc-usb-8`](dual-adc-usb-8/) | 09-25 → 09-26 | export | 0 / 6 | 170 / 129 | **$26.48** | **~2¼ h** | Opus 5.5; no spend-limit kills; FT232H datasheet never read |

Part and net counts come from each exported netlist. Costs are the equivalent first-party
API price of the tokens used (from `claude_cost.txt`), not what the Pro subscription billed.
¹ Run 3's design-only figure. Its `claude_cost.txt` says $249.82 because the same session
went on to refactor the plugin. The `session_cost.json` files in runs 4–7 are stale copies of
run 3's and should be ignored. Run 8's cost is on Opus 5.5 pricing, which
`session_cost.py` sets below Opus 5's; its token count (65.9M vs 139–308M) is the fairer
comparison.

## Comparison

| Run | ADC (sample rate) | Front end | Capture logic + memory | Record at full rate | USB bridge | BOM / board |
|---|---|---|---|---|---|---|
| 1 | LTC2292 dual (40 MSPS, ÷4) | OPA1656 + THS4521, ±4 V | iCE40HX4K + 4 MB SRAM | ~100 ms | FT2232HL | $175–185 live |
| 2 | 2× AD9235-20 | AD8066/OPA836, ±5 V | iCE40HX4K + 512 kB SRAM | 13 ms | FT232HL | ~$85–115, unverified |
| 3 | 2× AD9235-40 | AD8066 + THS4551 | GW1NR-9, in-package PSRAM | 280 ms | CY7C68013A | ~$104 (architect) |
| 4 | ADS5231 dual (20 MSPS, FPGA ÷2) | OPA354 + THS4521, ±2.5 V | GW1NR-9, in-package PSRAM | spec only ≥16k samples | FT232H | ≈ $91 live |
| 5 | ADS5231 dual (20 MSPS, host ÷2) | OPA355 + THS4551, single 5 V | GW1NR-9, 8 MB | 105 ms @ 20 MSPS | FT232H | ≈ $85 live |
| 6 | 2× AD9237-40 (10 MSPS) | TPH2501 + THS4521, single 3.3 V | XC6SLX9 + 32 MB SDRAM | 839 ms | CY7C68013A | not totalled (ADCs alone $66) |
| 7 | ADS5231 dual (10 MSPS, PLL off) | AD8066 + THS4521 + LC AAF | GW1NR-9, 8 MB PSRAM | ≥100 ms | FT232HL | ≈ $89–91 live |
| 8 | ADS5231 dual (40 MSPS, FPGA ÷4) | OPA356 + THS4551 MFB, +3.29/−2.01 V | GW1NR-9, 8 MB PSRAM | 210 ms | FT232HL | not totalled (actives ≈ $89) |

The same prompt produced three different chip sets in runs 2–4 and three more in runs 5–8
(runs 5, 7 and 8 converged on ADS5231 + GW1NR-9 + FT232H, at three different ADC clock rates).
Run-to-run variation is at least as large as the effect of any prompt change tested here.

## What the tool did well

- **Caught the throughput contradiction every time**, before designing anything, and
  recorded the trade-off in `SPEC.md` rather than silently picking an answer.
- **The independent ERC reviewer is the most valuable agent.** In runs 3, 5, 6, 7 and 8 its
  first pass found at least one HIGH defect in a circuit that ERC called clean:
  - a mis-wired MFB stage that made the anti-alias filter one order short (runs 3 and 5);
  - an ADC clock over its absolute maximum (run 3);
  - an input TVS 2.2 V into breakdown at the rated input (run 6);
  - a JTAG header referenced to 3.3 V on a 1.8 V bank (run 7);
  - a mirrored custom BNC footprint (run 8).

  In run 3 it cost $15 of a $125 run.
- **Agents correct the agent that briefed them.** Coders routinely caught net-plan and BOM
  errors against primary datasheets: pin numbers, EEPROM compatibility, regulator VFB
  variants, boot-strap values and reset timing. Run 6's driver listed four such
  corrections in one run.
- **Recovery from spend-limit kills improved.** From run 4 on, agents write to disk as
  they go, and the driver checks disk before re-spawning. Kills in runs 5–7 lost almost
  no completed work. Run 8 had none.
- Netlists are byte-stable across regenerations from run 3 on (tags derived from refdes).
  Without that, KiCad's "update PCB from schematic" would discard placement every time.
- Every run from 3 on generated missing KiCad symbols (kipart) and some custom footprints
  from vendor drawings, and checked pin counts against datasheets.

## Where it broke

- **The Claude Pro spend limit shaped runs 1–7.** Run 1 stopped because of it. Runs 2–7
  each hit it two to five times. Their elapsed times (18–22 h for a complete run) are
  mostly waiting for limit resets, not work. Run 8, on Opus 5.5, used a third to a fifth
  of the tokens and never hit it. One run doesn't show whether that holds. Parallel Opus fan-out made it worse: a 9-way
  burst killed every coder at once in run 3.
- **ERC-clean is a low bar.** Every exported netlist was ERC-clean, and every one still
  carried defects that needed a datasheet or an analog calculation to find. Some were
  caught before export, and some are still open (see each run's README).
- **Recurring defect classes** across independent runs:
  - Anti-alias filter topology or order wrong (runs 3, 5); 2nd-order filter accepted with
    an aliasing risk (run 4).
  - GW1NR-9 QN88P I/O budget over-reported as 71 when only 48 are usable at 3.3 V
    (runs 3 and 7), plus a mislabelled pin-12 supply in the generated symbol.
  - FT232H internal-regulator pins mishandled: two outputs shorted (run 2), VCORE driven
    from 3.3 V (run 7), VCCD on the VCORE net in the net plan (run 8, caught). EEPROM
    compatibility got wrong (run 5; possibly still present in run 2). Run 8 never obtained
    the FT232H datasheet at all.
  - BNC and USB-C footprints wrong or unverified in nearly every run (mirrored in run 8).
  - Sample-clock jitter unchecked: Yangxing SX3M oscillators with no published jitter
    figure were accepted in runs 7 and 8; run 6 rejected one for that reason.
  - A bad BOM cell propagates because nothing downstream re-derives it. Examples: a 15 pF
    TVS listed as ≤0.5 pF (run 6); five decoupling shortfalls from the skeleton BOM (run 7); 12 stale BOM cells plus 9
    value mismatches, with the code right every time (run 8).
- **Tooling gaps found by the pipeline itself:** `validate-footprints.py` checks that a
  footprint file exists, not that its package matches the part (runs 6, 7). BOM-vs-code
  drift reached gates repeatedly until `validate-bom.py` was used (runs 7–8).
- **Facts disagree between runs.** Runs 4, 5 and 8 said the ADS5231 can't clock below
  20 MHz; run 7 ran it at 10 MSPS with the PLL disabled over SPI. Oscillator jitter was
  checked and the part replaced in runs 5–6, and never questioned in run 7. Nothing in
  the pipeline carries a verified fact from one run to the next; the part cache that could
  is switched off to keep runs independent.
- **Sourcing quality depends on the parts MCP.** Without it (run 2) the BOM is plausible
  guesses. With it (runs 4–8) stock and price are live, but the architect's early cost
  estimate can still be off by more than 2× (run 6).
- LLM-backed hooks gave false positives and added latency in runs 1–3. They were replaced
  with scripts after run 3.

## Verdict

After eight runs the pipeline still gets to roughly "netlist you would review, not netlist
you would fabricate." The independent ERC review and datasheet-driven coders catch a lot.
Each run still exports with open items: footprints, jitter, bench-verify conditions and
analog margins. On Opus 5, cost per complete run was about $90–175 of API-equivalent usage
and roughly a day of elapsed time on a Pro plan. Run 8 on Opus 5.5 took $26 and ~2¼ h with
comparable verification depth, though it left the FT232H unread and the clock jitter
assumed. That is one run with three things changed at once, so it needs repeating before
it counts as a trend. The run-to-run variance in the architecture means one run tells you
about that run, not about the tool. Treat these as eight case studies, not a benchmark.
