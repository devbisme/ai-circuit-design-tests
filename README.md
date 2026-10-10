# ai-circuit-design-tests

There are now many [AI tools](https://devbisme.github.io/RepoRecon/?topic=kicad_ai&filter=&sort=pushed:desc) that claim to automate KiCad.
Some may work, many may not; it's hard to tell since example designs are either non-existent, show only partial results, or
are very simple (e.g. resistor dividers).

I'm going to try some of these AI tools to see how they perform.
This repo is the test bench. Each top-level subdirectory holds the artifacts of one tool
being exercised on a real design problem, plus an evaluation of what came out and what it
cost.

The tools that were tested fall into the following classes:

- **Generators** take a design prompt and produce a design: specs, BOM, schematics,
  netlists, and sometimes a board.
- **Analyzers** take an existing KiCad design and produce a report: design review findings,
  ERC/DRC/DFM checks, simulations, sourcing, etc. They don't create a design of their own,
  so they are run on a design produced by one of the generators tested here.
- **Hybrids** can both generate and analyze designs. They are tested in both roles: one run
  analyzes an existing design, and another creates a design from a prompt.

Because of this, the results and the directory layout differ between the classes.
A generator's output is judged by whether the design is correct and complete; an analyzer's
output is judged by whether its findings are real, relevant, and not missing anything important.

Note that I have not validated any of these designs for correctness.
I will report the results of my validation in each tool's directory when I'm done.
Please feel free to report any of your own evaluations here as an issue on this repo.

**If you are interested in trying any of these tools,**
the most important files to read are:

* `setup.md` which describes how to install the tool,

* `claude_transcript.txt` (in each run directory) which shows the interactions between the
  user and Claude when using the tool.

For a quick look at what a run produced, start with its `executive_summary.md`.

## Tools tested

| Directory | Tool | Class |
|---|---|---|
| [`skidl-skills-tests/`](skidl-skills-tests/) | [skidl-skills](https://github.com/devbisme/skidl-skills) | Generator |
| [`konnect-tests/`](konnect-tests/) | [Konnect](https://github.com/mixelpixx/Konnect) | Hybrid |
| [`copperhead-tests/`](copperhead-tests/) | [Copperhead](https://github.com/copperheadhq/copperhead) | Generator |
| [`kicad-happy-tests/`](kicad-happy-tests/) | [kicad-happy](https://github.com/aklofas/kicad-happy) | Analyzer |
| [`kicad-mcp-server-tests/`](kicad-mcp-server-tests/) | [kicad-mcp-server](https://github.com/Seeed-Studio/kicad-mcp-server) | Hybrid |
| [`kicad-mcp-pro-tests/`](kicad-mcp-pro-tests/) | [kicad-mcp-pro](https://github.com/oaslananka/kicad-mcp-pro) | Hybrid |

Each generator's `README.md` describes the tool, why it was chosen, the prompt(s) it was given,
a cross-run comparison, and an evaluation of cost, runtime and quality of results.
Each analyzer's directory holds a copy of the design it analyzed (and notes where it came from),
the reports the tool produced, and an evaluation of the findings, cost and runtime.
A hybrid's directory has one of each kind of run.

## Comparable runs

Two sets of runs share their inputs, so their results can be compared across tools.

**Same design prompt.** These runs got the dual-ADC requirements prompt (dual-channel,
±10 V, 10 MS/s, 12-bit, ≥0.1 s of capture, USB 2.0). Each was told to start from a blank
slate.

| Run | Tool's role | Reached (as reported by the session) | Equiv. API cost |
|---|---|---|---|
| [Konnect 2](konnect-tests/dual-adc-usb-2/) | Design tool | Routed 4-layer board, DRC clean | $61.12 |
| [kicad-mcp-server 2](kicad-mcp-server-tests/dual-adc-usb-2/) | Design tool, gaps filled by scripts | Routed 4-layer board, 4 DRC errors (stock USB-C footprint) | $16.93 |
| [kicad-happy 2](kicad-happy-tests/dual-adc-usb-2/) | Reviewer; Claude built the design with SKiDL and scripts | Routed 4-layer board, 0 ERC/DRC errors | $29.37 |
| [kicad-mcp-pro 2](kicad-mcp-pro-tests/dual-adc-usb-2/) | Design tool, gaps filled by scripts | Routed 4-layer board, 0 ERC/DRC errors | $19.42 |

These four runs used the prompt with an added line giving the KiCad 10 executable's path.
The version without that line was used for SKiDL Skills runs 5–9, Konnect run 1 and
Copperhead run 1.

**Same input design.** These runs analyzed the KiCad project from Konnect run 2.

| Run | Equiv. API cost |
|---|---|
| [kicad-happy 1](kicad-happy-tests/dual-adc-usb-1/) | $1.92 |
| [kicad-mcp-server 1](kicad-mcp-server-tests/dual-adc-usb-1/) | $2.05 |
| [kicad-mcp-pro 1](kicad-mcp-pro-tests/dual-adc-usb-1/) | $2.24 |

The prompts differed between these runs, so they did not ask for exactly the same things.
Each tool's `README.md` lists its prompts and findings.

None of these designs or findings has been validated yet.

## Layout

This is the layout for generators. Analyzers follow it loosely: the KiCad files in their
directories are inputs copied from a generator's run, not outputs, and the main output is
the analysis report.

```
ai-circuit-design-tests/
├── README.md                 <- this file
└── <tool-name>-tests/        <- one directory per AI tool under test
    ├── README.md             <- the tool, the design prompt, cross-run comparison, evaluation
    ├── setup.md              <- how the tool was installed and configured
    └── <design>-<run#>/      <- one directory per run
        ├── README.md         <- (some runs) what was run, what came out, evaluation, cost
        ├── *-prompt.txt          <- the verbatim prompt given to the tool
        ├── claude_transcript.txt <- transcript of interactions between the user and Claude
        ├── claude_cost.txt       <- token usage and equivalent API cost
        ├── executive_summary.md  <- overall description of the design process, results, risks.
        └── ...                   <- everything the tool produced
```

One run per directory, never overwritten. Runs are numbered so a prompt change or a tool
change can be compared against the previous attempt on the same design. Where possible,
different tools are given the same design prompt so their results can be compared.

## What each run should capture

- The verbatim prompt (`*-prompt.txt`).
- Everything the tool wrote — specs, architecture docs, BOM, datasheets, code, ERC/DRC logs,
  netlists, schematics, boards — left where the tool put it.
- The session transcript (`claude_transcript.txt`, via `/export`), when the tool is interactive.
- Cost. `claude_cost.txt` holds token counts and the equivalent first-party API price. It
  comes from `session_cost.py`, which sums usage from the main transcript **and** the
  subagent transcripts; the main file alone misses most of the spend. Save it at the end of
  the session, before doing any unrelated work in the same session, or the total will
  include that work too.
