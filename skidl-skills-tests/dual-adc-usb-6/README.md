# dual-adc-usb-6 — SKiDL Skills, autonomous run, record-length prompt

Second run of the run-5 prompt. It produced the most thoroughly verified design so far and
also the most expensive complete run. The architecture differs from runs 5 and 7: two
separate ADCs, a Xilinx FPGA, external SDRAM and an FX2LP bridge.

- **Dates:** 2026-09-21 15:11 → 2026-09-22 10:28
- **Tool:** SKiDL Skills plugin (pipeline state v5.1), Claude Code v2.1.278, Opus 5 (Claude Pro), SKiDL 3.0.0, KiCad 9
- **Prompt:** [`dual-adc-prompt.txt`](dual-adc-prompt.txt) — identical to runs 5, 7 and 8
- **Transcript:** [`claude_transcript.txt`](claude_transcript.txt) (210 KB, the largest; most of the bulk is subagent hand-back reports quoted in full)

## Design that came out

USB-C receptacle (power budget fits a plain 500 mA port, so the USB-C clause did not
fire), 8 blocks / 10 instances:

| Block | Content |
|---|---|
| `usb_front` | USB-C 16P (custom footprint from the vendor drawing), USBLC6 ESD, TPS22919 soft-start load switch |
| `power` | 2× AP62200T buck (replaced NRND SY8089), 2× TPS73633 LDO, TLV2372 reference buffer → +3V3D, +1V2, +3V3A_ADC, +3V3A_AMP, VREF_OFF, VCM_REF |
| `analog_frontend` ×2 | BNC (custom footprint), 1 MΩ ∥ 20 pF built as 909k/90.9k + 22 p/(200 p ∥ 10 p), BAV199 clamp + ESD9L5.0 TVS on the buffer node, TPH2501 buffers, 4th-order Sallen-Key Butterworth (4.45 MHz), THS4521 FDA |
| `adc_channel` ×2 | AD9237BCPZ-40 (AD9235 qualified as second source via DNP strap resistor) |
| `clocking` | TAITIEN OXETDLJANF 10 MHz XO (≤1 ps RMS jitter), 74LVC1G17 isolation buffer for the FPGA copy |
| `fpga_core` | Xilinx XC6SLX9-2TQG144C (86 of 102 I/O), W25Q32 config flash, JTAG |
| `buffer_memory` | W9825G6KH 32 MB SDR SDRAM → 0.839 s at full rate (8.4× the requirement) |
| `usb_bridge` | CY7C68013A (FX2LP) 8-bit slave FIFO, 24LC64 boot EEPROM at 0x51 |

Power budget: 293 mA / 1.47 W at 5 V.

## Result — complete

- **ERC: 0 errors, 2 warnings** ([`__main__.erc`](__main__.erc)). Both are LDO inputs
  behind ferrites, verified as false positives. Independent gate **FAILED** on the first
  pass and passed at revision 2 ([`erc_report.md`](erc_report.md)).
- **Exported:** [`outputs/dual_adc_usb.net`](outputs/dual_adc_usb.net) and
  [`outputs/dual_adc_usb_bom.xml`](outputs/dual_adc_usb_bom.xml) — **243 parts, 186 nets**
  (counted from the netlist); byte-identical across regenerations apart from the date line.
- BOM at revision r7, live-verified through the pcbparts MCP (available in this run).
  No whole-board total was recorded. The architect's ~$30/board estimate can't be right:
  the two AD9237s alone cost $65.67 at the live price.
- Issue tracker in [`pipeline_state.json`](pipeline_state.json) `open_issues`: 21
  items were raised and all were closed or deliberately accepted.

## Evaluation

**Good**

- **The first independent gate failed the design correctly.** The input TVS sat directly
  on the BNC node, so at the board's own rated ±10 V input it was 2.2 V into breakdown.
  The part survived four phases because a BOM cell listed it as "≤0.5 pF" when it is 15 pF.
  Simply moving that part would have put −3 dB at 3.996 MHz against a 4.000 MHz floor,
  so it was also replaced with a 0.9 pF ESD9L5.0.
- The reviewer then found a problem it had missed on its first pass. Clamp-node
  capacitance sits across the attenuator's bottom leg, giving a 4.2 % τ mismatch
  (−0.345 dB shelf) against a ±2 % spec. The driver fixed it with 200 pF ∥ 10 pF, which
  also restores a trim point in place of the unavailable SMD trimmer.
- Defects were caught against primary datasheets before or during coding: an NRND buck
  with no datasheet was replaced; the AP62200**T** VFB of 0.763 V differs from the base
  part's 0.800 V; the FX2LP boot EEPROM must be at 0x51 (Infineon Table 8); the FX2 reset
  RC was 5× too short for PLL lock; a 10 kΩ pull-down on the Spartan-6 mode pins would
  have left M1 at an invalid level; the reference buffer needed ≥20 Ω RNULL into 300 nF;
  and VCCAUX ties to +3V3D.
- Every EasyEDA- or catalogue-sourced pin fact that reached code was later checked
  against a manufacturer PDF: the SDRAM's 54 pins, the FPGA clock pins, TPS22919
  polarity, 74LVC1G17 and BAV199. All matched.
- Agents repeatedly corrected the agent that briefed them. The driver listed four cases:
  the architect fixed the driver's pole arithmetic, a coder fixed the driver's
  isolation-resistor reasoning, the sourcer fixed the architect's BAV199 capacitance
  model, and the footprint agent fixed the sourcer's reading of the USB-C drawing.

**Bad**

- **Tooling gap:** `validate-footprints.py` only checks that the library file exists. It
  never sees the sourced part's package, so two wrong-package footprints with matching
  pad counts passed it (SOIC-8 150 mil vs 208 mil flash; SOD-523 vs SOD-923 TVS). The
  reviewer caught them by hand. Logged as OI-21.
- **BOM-vs-code drift** reached a gate four times: the crystal symbol, the "≤0.5 pF"
  cell, U31's package and R52's value. The final pass was a full consistency sweep. It
  found another case: a "same MPN as C101" note would have silently changed an unrelated
  Sallen-Key cap.
- The driver's "only these two rows" instruction to the sourcer left dependent passives
  stale after the regulator swap. The driver called this its own scoping error.
- Interruptions: two spend-limit kills, then API 500/529 errors that killed the first two
  ERC gate attempts overnight. The user had to prompt "complete the design" to restart.
- Accepted with the risk recorded: TVS leakage (needs a bench offset check), both
  project-local footprints (need human review before fab), and X1 single-sourced at
  50 pcs, kept because it's the only in-stock 10 MHz XO with a published jitter figure.

## Cost

| Measure | Value | Source |
|---|---|---|
| Equivalent API cost | **$175.32** — Opus $129.29 (1,189 msgs) + Sonnet $46.03 (1,208 msgs) | [`claude_cost.txt`](claude_cost.txt) |
| Tokens | 308.1M total, 293.8M of them cache reads | [`claude_cost.txt`](claude_cost.txt) |
| Elapsed | ~19 h, including ~3 h and ~3.6 h spend-limit waits and an ~8 h overnight stall after API 500/529 errors | transcript |
| Architecture reworks | 1 (TVS placement) | [`pipeline_state.json`](pipeline_state.json) |

This is the most expensive complete run. Most of the extra spend went to verification
(re-gating, primary-source pin checks, BOM sweeps) rather than rework.

[`session_cost.json`](session_cost.json) is a stale copy of run 3's file (same session
UUID, $124.91) and does not describe this run. Use `claude_cost.txt`.
