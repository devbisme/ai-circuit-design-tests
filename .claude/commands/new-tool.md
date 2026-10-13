---
description: Vet, install, and set up test runs for a new KiCad AI tool
argument-hint: <github-repo-url>
---

Set up a test bench for the KiCad AI tool at: $ARGUMENTS

If no URL was given, stop and ask for one.

Work from the repo root (`/home/devb/projects/AI/ai-circuit-design-tests`). Read `README.md`
first to learn this repo's layout and conventions. Use `kicad-ai-assistant-tests/` and
`eda-agent-tests/` as reference examples of a finished tool directory.

Do not perform any git operations (commit, branch, push, etc.).

## 1. Vet the tool

Read the repo's README, docs, and install instructions. Decide whether Claude Code can drive
the tool. It qualifies if it is one of:

- an MCP server (stdio or HTTP) that Claude Code can register,
- a Claude Code skill or plugin,
- a CLI or Python library that Claude Code can call from Bash.

It does NOT qualify if it:

- works only through a GUI (a KiCad plugin panel, a web app) with no scriptable entry point,
- requires its own paid LLM API key for its core function (Claude Code can't stand in for it),
- is a hosted SaaS with no local component.

Also check:

- **KiCad version.** These tests use KiCad 10 (`/home/devb/bin/kicad10`, root at
  `~/bin/kicad10-root`). If the tool supports only older versions, say so and treat it as a
  risk, not an automatic stop.
- **Already tested?** If the tool is already in the "Tools tested" table in `README.md`,
  or a `<tool>-tests/` directory already exists, stop and report. Never overwrite an existing
  test directory.

If the tool does not qualify, stop here. Report in a few lines which criterion failed, with
evidence (quote or link the relevant part of its docs). Create nothing.

## 2. Classify the tool

Classify it using the definitions in `README.md`:

- **Generator:** creates designs from a prompt.
- **Analyzer:** reviews an existing KiCad design.
- **Hybrid:** both.

Base this on what its tools/commands actually do, not on its marketing. List the evidence:
the tool, command, or skill names that create designs and the ones that review them.

## 3. Create the test directory

Name: `<repo-name, lowercased>-tests/` (e.g. `KiCad-AI-Assistant` → `kicad-ai-assistant-tests/`).
Below, `<TOOL>` is the tool's display name and `<SHORT>` is how its docs refer to it (e.g.
"KiCad-AI-Assistant (kcaa)").

### If it can analyze: `analyze-1/`

1. Copy `analysis_prompt.txt` from the repo root. In the first line, change
   "Analyze the kicad project in this directory." to
   "Analyze the kicad project in this directory using <SHORT>."
   Make no other changes.
2. Copy **only** these files from `konnect-tests/dual-adc-usb-2/`. They are Konnect run 2's
   KiCad project:
   - `dual_adc_usb.kicad_pro`, `dual_adc_usb.kicad_sch`, `dual_adc_usb.kicad_pcb`,
     `dual_adc_usb.kicad_prl`, `dual_adc_usb.kicad_dru`
   - `adc.kicad_sch`, `afe_a.kicad_sch`, `afe_b.kicad_sch`, `fpga.kicad_sch`,
     `power.kicad_sch`, `usb.kicad_sch`

   Do NOT copy anything else. In particular, leave out `executive_summary.md`, `README.md`,
   `claude_cost.txt`, `PCB.png`, `*_v1.*`, `*_routed.*`, the PDF, and `routing/`. They would
   leak Konnect's own results into the review.
3. Check that every sheet the root schematic references is present.

### If it can generate: `generate-1/`

1. Copy `design_prompt.txt` from the repo root, unchanged.

### In each run directory created

- Copy `session_cost.py`.

If the tool is analyzer-only, `generate-1/` is not created, and generator-only tools get
no `analyze-1/`.

## 4. Install the tool

Follow the repo's install instructions. As you go, write `<tool>-tests/setup.md`, modeled on
`kicad-ai-assistant-tests/setup.md`:

- **Prerequisites:** KiCad version, runtimes, API keys and whether they are needed under
  Claude Code, and whether a running KiCad GUI (IPC API) is needed.
- **What the tool is:** its parts and which of them Claude Code uses.
- **Quick option: let Claude Code install it:** say that it was installed via `/new-tool`.
- Numbered install steps with the exact commands run, including any **deviations from the
  repo's instructions** and why.
- **Every file or config touched outside this repo** (venvs, `~/.claude.json`, MCP config,
  KiCad plugin dirs, skills), so it can be uninstalled.
- **Verify:** the command that shows it works, and its output.
- **Notes:** gotchas.

Register MCP servers so they are available when `claude` is started **inside the run
directories**. Check this by running `claude mcp list` from a run directory. Point the tool at
KiCad 10, not the system KiCad 9.

If installation fails and can't be fixed in a reasonable number of attempts, stop. Record what
failed and why in `setup.md`, and report. Leave the test directory in place.

If you hit non-obvious install gotchas, save them as a memory, as was done for earlier tools.

## 5. Check for contamination from other tools

Earlier tools may still be registered (MCP servers, skills, plugins). A run could end up using
them instead of the tool under test. List every KiCad-related MCP server and skill that would
be active in the run directories (`claude mcp list`, `.claude/settings.local.json` →
`skillOverrides`, `~/.claude/skills/`). Recommend which to disable for the runs. Don't disable
anything outside this repo yourself; list the commands instead.

## 6. Write the tool README and update the top-level README

1. Create `<tool>-tests/README.md` with the same sections as
   `kicad-ai-assistant-tests/README.md`:
   - **Tool under test:** what it is, its capabilities (summarize the actual tool and command
     list), and version / commit / profile / backend. Leave the model and Claude Code
     version as `TODO`.
   - **Why this tool:** leave as `TODO` for me, unless something in its docs makes the
     reason obvious. If you fill it in, mark it as a draft.
   - **Runs:** the table with one row per run directory created. Fill in Run, What it tests,
     and Prompts. Put `TODO` in Outcome, cost, and time.
   - `### analyze-N` and `### design-N` subsections per run, each containing only `TODO`.
   - **Layout:** the directory tree as it currently stands.
2. Add a row to the "Tools tested" table in the top-level `README.md`. Do not touch the
   "Comparable runs" tables; they get updated after the runs finish.

## 7. Report and hand off

Report briefly:

- the class, with evidence,
- what was installed and where, and any deviations,
- the contamination list and the recommended disables,
- risks (KiCad version, GUI/IPC requirements, missing features seen in the docs),
- whether Claude Code must be restarted for the MCP server to load.

Then give me the exact steps for each run. Each run must be a **fresh `claude` session started
inside the run directory**, so its transcript and cost stay separate from this setup session.

```
cd <repo>/<tool>-tests/design-1 && claude
> <the prompt file's contents: paste it, or "Do what <prompt file> says.">
...when done:
> /export claude_transcript.txt
> ! ./session_cost.py > claude_cost.txt
```

Do not start the runs yourself.
