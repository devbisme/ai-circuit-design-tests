# Phase Handoff Contract

The pipeline is **context-isolated**. Phases never share conversation context; they
communicate ONLY through handoff files on disk. Your handoff file is the sole thing the
next phase and the orchestrator will read from you. Write it as if the reader knows
nothing about your work.

## Project root

All paths in this document are relative to the project root:
`/home/devb/projects/AI/skidl-skills-tests/dual-adc-usb-2/`

Local toolchain facts (Python, SKiDL version, KiCad symbol paths, exact run commands)
are in `rules/environment-local.md` — read it before running any circuit.

Always use **absolute paths** in tool calls. Paths recorded *inside* handoff tables are
written relative to the project root.

## Rules for every phase

1. **Read your entry handoff first.** It is your complete entry point. Follow its
   pointers to the artifacts you need — do not guess at file locations.
2. **Do not read another phase's handoff** except the one named as your entry point
   (the assembler is the exception: it reads all block handoffs).
3. **Write your own handoff file** at the exact path the orchestrator gave you, before
   you finish. A phase without a valid handoff file has not completed.
4. **Never write another phase's handoff file**, and never write `pipeline_state.json` —
   only the orchestrator writes that.
5. **Return ≤10 lines** to the orchestrator. Detail belongs in the handoff file, not in
   your reply.
6. **Every path you list under `## Artifacts` must actually exist on disk** when you
   finish. The orchestrator gates on this and will send the handoff back if it fails.
7. **Blank slate.** Only files inside this project root are valid inputs. Never read,
   copy, or reuse files from sibling or parent directories (other design directories
   under `/home/devb/projects/AI/skidl-skills-tests/`).

## Required file format

Front matter, then the fixed sections in order. Nothing may be omitted; use "none" for
an empty section.

```markdown
---
phase: <requirements | architecture | sourcing | datasheets | coding | blocks | erc>
status: <complete | partial | failed>
next_phase: <name of the phase that reads this file, or "none">
circuit_name: dual_adc_usb
revision: <integer, starts at 1, bump on every rewrite>
date: <YYYY-MM-DD>
---

## Receipt
3-8 bullets. What you produced, in plain language. The orchestrator relays this verbatim
to the user, so it must stand alone without the artifacts.

## Artifacts
| Path | What it contains | Who reads it next |
|------|------------------|-------------------|
| architecture/net_plan.md | Net-by-net connection plan | coding |

Every row's path must exist on disk.

## Key facts for the next phase
The numbers, names, and constraints the next phase needs so it does NOT have to re-derive
them. Be specific: rail voltages and currents, part numbers, pin names, net names,
tolerances. This section is why the next phase can start cold.

## Decisions
| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|

Every non-obvious engineering choice you made. Options considered is a real list, not a
placeholder. This feeds the running Design Decisions log.

## Carried forward
Open questions, gaps, assumptions the next phase must validate, and — if
`status: partial` or `failed` — exactly what is missing and why. Use "none" if clean.

## Escalation
Only if you cannot proceed. Set `status: failed` and give:
- `escalation_reason:` one of `pin_count_mismatch`, `unsupported_mode`,
  `fundamental_conflict`, `sourcing_partial_failure`, `sourcing_failure`
- `escalation_description:` one line
Otherwise write "none".
```

## Phase-specific required content

- **requirements** → `## Key facts` must state every hard number the architecture depends
  on: rails, currents, signal ranges, bandwidth, throughput, interfaces, connectors.
- **architecture** → must include a `## Block manifest` table (extra section, after
  `## Artifacts`) with columns: `block_id | block_name | function_signature |
  interface_nets`. `block_id` is a valid Python identifier and is used as the block's
  filename. `function_signature` is the exact `@subcircuit` def line the coder must use.
- **sourcing** → must include a `## Parts by block` table: `block_id | ref designators |
  MPNs`. Every part must be a real, in-stock, orderable part.
- **datasheets** → must include a `## Summaries by block` table: `block_id | summary file
  paths`. Summaries must carry exact pin names/numbers and required external components.
- **blocks** (one per block, `handoffs/05_blocks/<block_id>.md`) → `## Key facts` must
  state the block's FINAL function signature and interface net names as implemented,
  which may differ from the architect's proposal. This is authoritative for the assembler.
- **coding** → must state the ERC result and point at the circuit entry point.
- **erc** → must state error and warning counts explicitly.

## Autonomous-run override (this project)

This run is fully autonomous. Do **not** ask the user questions and do not wait for
approval. When a design decision is required: enumerate ALL plausible options in the
relevant artifact with brief pros/cons, mark the RECOMMENDED one, proceed with it, and
record it in your `## Decisions` table.
