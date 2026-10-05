# Konnect — tests

## Tool under test

[Konnect](https://github.com/mixelpixx/Konnect) is an MCP server plus a set of Claude Code
skills and agents that let Claude edit KiCad projects directly: schematic capture, ERC, PCB
placement, routing and DRC. Installation is described in [`setup.md`](setup.md).

- **Version:** Konnect v0.12.1 (MCP server and the PCBNEW plugin), installed with
  `konnect init`. Skills used: `konnect`, `kicad-schematic`, `kicad-pcb`, `kicad-review`.
- **How it talks to KiCad:** schematic edits go through Konnect's file-based tools. PCB edits
  go over live KiCad IPC, which needs PCBNEW open with the Konnect plugin's server started.
  Some steps (layer changes, closing/reopening the board) need the user to act in the GUI.
- **Model:** Claude Opus 5.5 on a Claude Pro plan, Claude Code v2.1.289 (run 1). Run 2's
  session states that no sub-agents were used; a single main-thread session drove everything.
- **Backend:** KiCad 10 (`~/bin/kicad10`, 10.0.4 per run 1's notes). Konnect writes
  `generator_version "10.0"` files, which the system KiCad 9.0.9 refuses to open.
- **Freerouting 2.4.1** was used for autorouting, outside Konnect, on scratch copies of the
  board.
- **Unlike the [SKiDL Skills tests](../skidl-skills-tests/), layout and routing are in
  scope.** The deliverable is a KiCad project with a routed PCB, not just a netlist.

## Why this tool

It edits KiCad projects directly and carries the design through PCB layout and routing, not
just a netlist.

## Quick look

Two trials so far (Opus 5.5, KiCad 10) on the same dual-ADC prompt. Both reached a placed and
routed 4-layer board:
* [`dual-adc-usb-1`](dual-adc-usb-1/): 6 connections left unrouted, $78 equivalent API cost.
* [`dual-adc-usb-2`](dual-adc-usb-2/): 100 % routed and DRC-clean, $61 equivalent API cost, ~7 h elapsed.

Neither board is ready for fab: the anti-alias filtering is weak in both, and run 2 lists
several unverified power-supply details. I also had to step in for some PCBNEW GUI actions.
For a quick look at the better of the two runs, read `executive_summary.md` in
`dual-adc-usb-2`. Details follow below.

## The design problem

Prompt (both runs), the same as SKiDL Skills runs 5–8:

```
Design a dual-channel ADC board that accepts signals in the range [-10V, +10V] and samples them
at 10 MHz with a resolution of 12 bits.
A minimum of 0.1 seconds of samples at the maximum rate is required.
The signals should enter the board through connectors that mate with standard oscilloscope leads.
The board should interface to a host through a USB 2.0 port
that provides power as well as transfer of digitized signal samples.
If insufficient power is available, use a USB C prt.

When decisions about the design are needed, list all the options and then select the one you recommend.
Do not pause the design process and wait for my input.

Do not use the results or any intermediate files from any other designs in this directory tree.
Always start from a blank slate.
```

Run 2 adds one line: `You will find the KiCad 10 executable in /home/devb/bin/kicad10.`
Run 1 had to discover the KiCad 9/10 mismatch itself.

Both runs caught the throughput problem (2 ch × 10 MSPS at 16-bit containers = 40 MB/s,
at or above the practical USB 2.0 bulk ceiling) and resolved it with on-board capture memory,
as every SKiDL Skills run did.

## Runs

| Run | Dates | Reached | ERC (err/warn) | Parts / nets | Equiv. API cost | Elapsed | Notes |
|---|---|---|---|---|---|---|---|
| [`dual-adc-usb-1`](dual-adc-usb-1/) | 10-01 → 10-05 | 4-layer board, 6 connections unrouted | 1 / 2 ¹ | 180 / 198 ² | $77.58 | not recorded | flat schematic; most datasheet checking |
| [`dual-adc-usb-2`](dual-adc-usb-2/) | 10-05 | 4-layer board, 100 % routed | 0 / 2 ¹ | 170 / 214 | $61.12 | ~7 h ³ | 7-sheet hierarchy; USB diff pair hand-routed |

Costs are the equivalent first-party API price of the tokens used (from `claude_cost.txt`),
not what the Pro subscription billed. Token totals: 218.4M (run 1), 164.8M (run 2).

¹ All listed items are intentional (an open-collector PGOOD tied to GND in run 1, flash
WP#/HOLD# tied to +3V3 in both). Not counted: 200–320 `lib_symbol_issues` warnings in each
run caused by a stale global KiCad 10 `sym-lib-table`, not by the design.
² Component and net counts from `outputs/dual_adc_usb.net` (exported 10-02). The design notes
say 161 parts at an earlier point; I didn't reconcile the two.
³ Wall clock from the prompt file (09:26) to `claude_cost.txt` (16:31), including time spent
waiting for the user to open/close boards in PCBNEW. Approximate.

### DRC state of the delivered boards

Re-run on 2026-10-05 with KiCad 10 `kicad-cli pcb drc` on copies of the current boards:

| Run | Board | Unconnected | DRC errors | Notes |
|---|---|---|---|---|
| 1 | 120 × 80 mm, 4 layers | 6 | 83 clearance, 2 drill-out-of-range | The session left 6 connections for the user to finish by hand; that hasn't happened. I haven't determined whether the clearance errors are real or a netclass/rules-file problem like the one run 2 hit (see below). |
| 2 | 140 × 90 mm, 4 layers | 0 | 0 | The 2 orphan vias the session reported (Konnect can't delete vias) are gone; presumably removed in the GUI. ~170 silkscreen warnings remain. |

## Comparison

| Run | ADC | Front end | Capture logic + memory | Record at full rate | USB bridge / connector | Analog rails |
|---|---|---|---|---|---|---|
| 1 | LTC2290 dual (10 MSPS) | ÷21 compensated divider + OPA356 Sallen-Key + THS4521 FDA | iCE40HX4K-TQ144 + 32 MB SDRAM (MT48LC16M16A2) | ~0.8 s | FT232H sync FIFO / USB-C wired as USB 2.0 | LM27762 ±2.5 V |
| 2 | LTC2290 dual (10 MSPS) | ÷20 compensated divider + ADA4817 buffer + THS4521 FDA | iCE40HX4K-TQ144 + 16 MB SDRAM (W9812G6KH) | ~0.4 s | FT2232H (A: sync FIFO, B: MPSSE for flash programming) / USB-B | LM27762 ±3.97 V |

The two runs converged far more than the SKiDL Skills runs did: same ADC, same FPGA, same
SDRAM-buffered architecture, same FTDI family, same negative-rail charge pump. Two runs is too
few to say whether that is the tool, the model (Opus 5.5 for both, versus mostly Opus 5 in the
SKiDL tests) or chance. Both estimated the power budget under 500 mA, so the USB-C clause never
fired, though run 1 chose a USB-C receptacle anyway.

## What the tool did well

- **Got all the way to a routed 4-layer board.** None of the SKiDL Skills runs attempted
  layout. Run 2 ended at 0 DRC errors and 0 unconnected, with the USB pair re-routed by hand
  as a ≈ 90 Ω differential pair over the GND plane, including a polarity-swap via.
- **Cheaper and faster than the SKiDL Skills runs on Opus 5**, while doing more ($61–78 versus
  $93–175 for a netlist only). Run 8 of the SKiDL tests, also on Opus 5.5, cost $26 for a
  netlist, so the model is probably most of the difference.
- **Datasheet checking in run 1** found and fixed real defects after ERC was clean: an ADC
  rail that could back-power the LTC2290 through its clock input, missing FT232H VPHY/VPLL
  filtering, wrong VCORE/VCCA decoupling, a misplaced EEPROM pull-up, and an un-balanceable
  probe-compensation trimmer. It also ran 54 scripted connectivity checks against the netlist.
- **The rendered sheet caught a short.** In run 2 an auto-routed `connect_pins` wire crossed a
  pin and tied VCMB to +3V0; it was spotted by rendering the schematic, not by ERC.
- **Worked around Freerouting's blind spot.** Freerouting ignores inner planes, so both runs
  scripted locked plane-fanout vias, cut the plane nets in the DSN, routed, then merged the SES
  back. A small A* router finished the last connections in run 2.
- Options → choice was recorded for every decision, as the prompt asked, in `DESIGN_NOTES.md`
  (run 1) and `README.md` / `executive_summary.md` (run 2).

## Where it broke

- **Konnect's schematic tools have sharp edges** (both runs): auto-routed wires shorting
  through pins, sheet pins left off resized sheet blocks, duplicate `#PWR` references across
  sheets, missing bus labels.
- **Konnect can't do everything on the PCB.** It couldn't delete vias (run 2), and its
  file-only `add_layer` was blocked by Claude Code's auto-mode permission classifier as a
  destructive in-place edit, so stackup and routing were done on a scratch copy. Adopting that
  copy by renaming dropped its netclasses and DRC jumped to 519 clearance errors; the rules
  were restored in a `.kicad_dru` file.
- **KiCad's Python API was unstable under scripting** (run 1): removing tracks mid-script broke
  footprint and track iteration, so edits had to be restructured into collect-then-apply passes.
- **Run 1 never closed the routing.** Six connections were stuck behind neighbouring copper,
  hand-placed fixes caused shorts and were discarded, and the job was handed back to the user.
  The board also currently shows 83 clearance errors (cause not determined).
- **The analog front end is weak in both runs.** Run 1's filter is about −23 dB at Nyquist; run
  2's is two poles near 7 MHz, so content above 5 MHz aliases freely. Neither is close to the
  ~72 dB a 12-bit converter wants. Both runs said so, rather than hiding it.
- **Run 2 left more unverified than run 1**: the LM27762 feedback topology and capacitor
  values, ADA4817 headroom and exposed-pad connection, BAV199DW symbol pin names, LTC2290 MODE
  table and FT2232H dual-mode use are all listed as unchecked.
- **The layouts are autorouted and unreviewed for analog/SI quality**: long detours on the
  analog rails, digital traces crossing the AFE, an unreviewed 10 MHz clock route and no
  outer-layer GND pour (run 2's own list).
- **Environment friction**: KiCad 9 vs 10 file versions, and a stale global symbol/footprint
  library table that adds hundreds of spurious ERC/DRC warnings in both runs.

## Verdict

Konnect gets Claude from a prompt to a placed and routed board, which is a step past the SKiDL
Skills pipeline. Run 2 is DRC-clean, but "DRC-clean autorouted board with known-weak
anti-aliasing and unverified power-supply details" is still a draft, not something to send to
fab. Run 1 did the more careful circuit work and the less finished layout; run 2 the reverse.
Cost was $61–78 of API-equivalent usage per run on Opus 5.5, and the user had to step in for
GUI actions in both. Two runs is not enough to separate the tool from the model or from luck;
treat these as two case studies.
