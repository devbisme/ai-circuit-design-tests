
# PRELUDE

There are now many [AI tools](https://devbisme.github.io/RepoRecon/?topic=kicad_ai&filter=&sort=pushed:desc) that claim to automate KiCad.
Some may work, many may not; it's hard to tell since example designs are either non-existent, show only partial results, or
are very simple (e.g. resistor dividers).

I'm going to try some of these AI design tools to see how they perform.
Currently, I've only tried one: [skidl-skills](https://github.com/devbisme/skidl-skills) because:
1. It's very easy to use (it's just a skill that can be run in Claude Code).
2. It uses SKiDL and I'm interested in how that performs.

I've run eight trials of `skidl-skills` in an attempt to reduce the cost and time required
to produce a design.
The fastest, cheapest, and most interesting is the last run: `dual-adc-usb-8`.
That result could arise from:
* Optimization of the skill.
* Using the new Opus 5.5 (previous runs used Opus 4.8 and 5).
* Pure luck.

You can make a quick assessment of the `dual-adc-usb-8` run using these files:
* The prompt that initiates the design flow: `dual-adc-prompt.txt`.
* An executive summary describing the design phases: `executive_summary.md`.
* A more detailed description: `README.md`.
* An even more detailed sequence of Claude's operations: `claude_transcript.txt`.
* An executable Jupyter design doc: `dual_adc_usb.ipynb`.

Note that I have not validated any of these designs for correctness.
That will be my next task now that I have been able to generate a design
within a reasonable time with a reasonable cost.
I will report the results of my validation here when I'm done.
Please feel free to report any of your own evaluations here as an issue on this repo.


# ai-circuit-design-tests

Test bench for AI tools that generate circuits and PCBs. Each subdirectory holds the
artifacts of one tool being exercised on a real design problem, plus an evaluation of what
came out and what it cost.

## Layout

```
ai-circuit-design-tests/
├── README.md                 <- this file
└── <tool-name>-tests/        <- one directory per AI tool under test
    ├── README.md             <- the tool, the design prompt, cross-run comparison
    └── <design>-<run#>/      <- one directory per run
        ├── README.md         <- what was run, what came out, evaluation, cost
        ├── dual-adc-prompt.txt   <- the verbatim prompt given to the tool
        ├── claude_transcript.txt <- exported session transcript
        ├── claude_cost.txt       <- token usage and equivalent API cost (run 3 on)
        └── ...                    <- everything the tool produced
```

One run per directory, never overwritten. Runs are numbered so a prompt change or a tool
change can be compared against the previous attempt on the same design.

## Tools under test

| Directory | Tool | Design | Runs | Status |
|---|---|---|---|---|
| [`skidl-skills-tests/`](skidl-skills-tests/) | [SKiDL Skills](https://github.com/devbisme/skidl) Claude Code plugin (multi-agent) driving SKiDL → KiCad netlist | Dual-channel ±10 V, 12-bit, 10 MSPS USB 2.0 acquisition board | 8 | run 1 stalled at coding; runs 2–8 exported netlist + BOM |

## What each run should capture

- The verbatim prompt (`*-prompt.txt`).
- Everything the tool wrote — specs, architecture docs, BOM, datasheets, code, ERC logs,
  netlists — left where the tool put it.
- The session transcript (`claude_transcript.txt`, via `/export`), when the tool is interactive.
- Cost. Runs 1–2 recorded none. From run 3 on, `claude_cost.txt` holds token counts and the
  equivalent first-party API price. It comes from `session_cost.py`, which sums usage from
  the main transcript **and** the subagent transcripts; the main file alone misses most of
  the spend. Save it at the end of the session, before doing any unrelated work in the same
  session. Run 3 didn't, and its total includes plugin development.

## Standing observations across tools

- **Budget binds, not time — on Opus 5.** Run 1 ended at a monthly spend limit, and runs
  2–7 hit the limit several times each. Most of their ~day of elapsed time is waiting for
  limit resets. Run 8 (Opus 5.5) used a third to a fifth of the tokens, never hit the
  limit, and finished in ~2¼ h for $26. One run; it needs repeating.
- **ERC-clean is a low bar.** Every exported netlist was ERC-clean and still carried real
  design defects that a netlist checker can't see: wrong filter topology, parts over
  absolute-max ratings, rail/bank voltage mismatches, wrong-package footprints. ERC checks
  connectivity, not intent.
- **An independent reviewer pays for itself.** The separate ERC-review agent found a HIGH
  defect on its first pass in five of the six runs where it ran (runs 3, 5, 6, 7, 8).
- **Run-to-run variance is large.** The same prompt produced three different chip sets in
  four runs, with record lengths from 0.1 s to 0.84 s. One run per configuration isn't
  enough to compare prompts or tool versions.
- **Live parts data changes the answer.** Runs with working supplier lookups revised their
  BOMs and caught stock, lifecycle (NRND) and compatibility problems. The run without them
  shipped an unverified, estimated BOM.
