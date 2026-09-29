# dual-adc-usb-2 — SKiDL Skills, autonomous run

Second run on the same board, with the prompt changed to remove the human from the loop.
This was the first run to reach netlist export.

- **Dates:** 2026-09-08 10:20 → 2026-09-09 08:03
- **Tool:** SKiDL Skills plugin (driven through its `orchestrator` agent), Claude Code v2.1.267, Opus 5 (Claude Pro), SKiDL 3.0.0, KiCad 9.0.9
- **Prompt:** [`dual-adc-prompt.txt`](dual-adc-prompt.txt) — base prompt plus:
  > When decisions about the design are needed, list all the options and then select the one you recommend. Do not pause the design process and wait for my input.
  >
  > Do not use the results or any intermediate files from any other designs in this directory tree. Always start from a blank slate.
- **Transcript:** [`claude_transcript.txt`](claude_transcript.txt) (31 KB). It was exported after this README was first written; the timing below has been checked against it.

## Design that came out

Independent of run 1 — different ADC, different bridge, different front end. USB-C bus
powered, 4-layer, ~100 × 70 mm, 9 blocks / 11 instantiations:

| Block | Content |
|---|---|
| `usb_c_input` | USB-C, 5k1 CC, polyfuse, ESD, common-mode choke |
| `power_digital` | AP7361C-33E → 3V3_D, AP2112K-1.2 → 1V2 |
| `power_analog` | P-FET load switch, +5 V_A LC filter, LP5907 → 3V3_A, LM2776 → −5 V_A, REF3025 2.5 V |
| `clock_gen` | 10.000 MHz XO + 2× 74LVC1G34 buffer |
| `afe_channel` ×2 | 20:1 compensated attenuator, AD8066/OPA836 buffer, 4th-order 5 MHz AAF, level shift to 0.5–2.5 V |
| `adc_channel` ×2 | AD9235BRUZ-20, 12-bit, parallel CMOS |
| `sram_buffer` | IS61WV25616 256K×16, 512 kB = 131,072 samples/ch |
| `usb_bridge` | FT232HL, FT245 sync FIFO, 60 MHz, ~30 MB/s |
| `fpga_core` | iCE40HX4K-TQ144 — capture FSM, SRAM controller, decimator, 12-bit packer, command parser |

Throughput contradiction resolved by SRAM burst capture (131,072 samples/ch at full
10 MSPS) plus decimated 5 MSPS/ch continuous streaming.

## Result — complete

- **ERC on the fully assembled circuit: 0 errors, 33 warnings** ([`__main__.erc`](__main__.erc)),
  independently re-run and confirmed.
- **Netlist and BOM exported:** [`outputs/dual_adc_usb.net`](outputs/dual_adc_usb.net)
  (268 KB) and [`outputs/dual_adc_usb_bom.xml`](outputs/dual_adc_usb_bom.xml) (77 KB) —
  **238 parts, 200 nets, 0 duplicate refs, 0 unresolved footprints** (counted from the netlist).
- All 33 warnings triaged in [`handoffs/05_coding.md`](handoffs/05_coding.md): 16 spare FPGA
  GPIO, 7 rails fed through ferrites/FETs that SKiDL doesn't type as power sources, 6 FT232H
  EEPROM pins mistyped `INPUT` by the stock KiCad symbols, 2 deliberate W25Q32 `~WP`/`~HOLD`
  ties, 2 benign net-name merges.
- Per-phase handoff documents in [`handoffs/`](handoffs/) — a structural improvement over
  run 1's ad-hoc briefs.
- Custom symbols generated from SPD sources for AD9235, AD8066, OPA836 and the SRAM
  ([`lib/src/`](lib/src/)).
- 157 `Part()` calls across 2339 lines of SKiDL.

## Evaluation

**Good**

- Finished. Autonomy removed run 1's waits on approval gates, although spend-limit waits
  still stretched the elapsed time (see Cost).
- The assembler found a real defect that block-level ERC had missed: a pin-indexing bug in
  `adc_channel.py` that dead-shorted each AD9235's `OTR` and `MODE` pins to `V3V3_A`/`GND`.
  It only became visible once both channels and `fpga_core` were wired together — an
  argument for full-assembly ERC over per-block checks.
- The driver ran a per-block ERC sweep before assembly and found a second real defect: the
  `usb_bridge` coder had shorted the FT232H's two separate 1.8 V regulator outputs (VCCA,
  VCCCORE) onto one net. Split into two rails, with no BOM change
  ([`outputs/erc_blocks_preassembly.md`](outputs/erc_blocks_preassembly.md)).
- The driver re-ran the assembler's ERC itself instead of trusting the PASS report.
- Worked around a SKiDL 3.0.0 API change on its own (`Circuit.ERC()` returns `None`, not a
  tuple) instead of stalling.
- Warnings were justified individually with block attribution, not suppressed.
- Kept an explicit open-items list of what it could not verify — including the honest
  admission that the FPGA gateware doesn't exist and the board is schematic-only.

**Bad**

- **The BOM is unverified.** The pcbparts MCP was unavailable, so every stock, tier, and
  price figure in [`sourcing/sourced_bom.md`](sourcing/sourced_bom.md) is a marked estimate,
  and the ~$85–115/board number is a guess. Run 1's live-sourced $175–185 for a comparable
  board suggests the direction of the error.
- **Two known-bad values shipped ERC-clean.** The AFE attenuator compensation computes
  ~18.9 pF nominal against a sourced 2–10 pF trimmer (part or topology is wrong), and the
  OPA836 power-down polarity was never confirmed against the datasheet. Both are in
  `pipeline_state.json`'s open items; neither is anything ERC can catch.
- **Possible latent defect found later:** the FT232H EEPROM is a 93LC46B. Run 5's coder
  found FTDI's datasheet requires a 93LC56B-class (2 Kbit) part and calls the 93LC46B
  incompatible. This design has not been rechecked against that.
- The spend limit killed the orchestrator twice, along with seven block coders and the
  symbol generator. The state file went stale both times and had to be fixed by hand.
  After the second kill the driver stopped re-spawning the orchestrator, because each
  restart re-read the whole design first, and drove the remaining phases directly.
- Fewer full datasheets pulled than run 1 (4 PDFs + 22 generated summaries vs 20 PDFs),
  which is cheaper but leaves more claims resting on summaries.
- Autonomy also means the design choices — 20 MSPS parts for a 10 MSPS spec, 512 kB of
  capture RAM (1/8 of run 1's), decimated continuous mode — were made without the user ever
  seeing the options. The prompt asked for options to be listed; they were listed to nobody.

## Cost

No token or dollar totals were captured. Phase boundaries come from file mtimes, checked
against the transcript:

| Phase | Window | Duration |
|---|---|---|
| Requirements → SPEC.md | 10:20 → 10:29 | ~9 min |
| Architecture (5 docs) | 10:29 → 11:00 | ~31 min |
| *(spend limit hit at 11:00, reset 14:30; resumed by user 17:56)* | 11:00 → 18:06 | ~7 h |
| Sourcing (BOM) | → 18:07 | within the gap |
| Datasheets (4 PDFs, 22 summaries) | 18:07 → 18:33 | ~26 min |
| Block coding, round 1 (6 blocks) | 18:33 → 18:47 | ~14 min |
| *(spend limit hit at 18:47, reset 22:50; resumed by user 07:30)* | 18:47 → 07:42 | ~13 h |
| Block coding, round 2 (afe_channel, fpga_core) + pre-assembly ERC sweep | 07:30 → 07:50 | ~20 min |
| Assembly + ERC + export | 07:52 → 08:03 | ~11 min |
| **Elapsed** | **10:20 Tue → 08:03 Wed** | **~22 h** |
| **Active model time (est.)** | | **~2–3 h** |

Roughly the same model time as run 1, but this run finished with a netlist and run 1
stalled. It spent nothing on approval round-trips. It did lose work to stopped agents, and
both ~7 h and ~13 h gaps are spend-limit waits, not idle choice. The savings came out of
verification depth: fewer datasheets, no live parts data, two known-wrong values left in the
design.
