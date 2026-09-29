# dual-adc-usb-4 — SKiDL Skills, autonomous run (revised plugin)

Fourth run, same prompt as runs 2–3. It is the first run on the plugin as revised during
run 3 (capped coder fan-out, write-as-you-go agents, script hooks). It was the cheapest
complete run on Opus 5 (run 8, on Opus 5.5, was cheaper) and the only one to end with a formal design review.

- **Dates:** 2026-09-10 13:25 → 2026-09-11 07:33
- **Tool:** SKiDL Skills plugin, Claude Code v2.1.267, Opus 5 (Claude Pro), SKiDL 3.0.0, KiCad 9
- **Prompt:** [`dual-adc-prompt.txt`](dual-adc-prompt.txt) — identical to runs 2–3
- **Transcript:** [`claude_transcript.txt`](claude_transcript.txt) (39 KB)

## Design that came out

USB-C bus-powered, 9 blocks:

| Block | Content |
|---|---|
| `usb_power_in` | USB-C, USBLC6 + SMF5.0A ESD, SY6280 current-limited load switch |
| `power_rails` | TLV1117LV33, TLV75512, TLV75518, TPS7A2033 LDOs → 3V3D / 1V2 / 1V8 / 3V3A |
| `bipolar_supply` | LM27762 → ±2.5 V for the front-end amps |
| `analog_front_end` | 2× BNC 1 MΩ ∥ ~20 pF, 10:1 divider with trimmer, BAV199 clamps, OPA354 buffer, THS4521 FDA, 2nd-order AAF |
| `adc` | TI ADS5231 dual 12-bit, run at 20 MSPS, decimated to 10 MSPS/ch in the FPGA |
| `sample_clock` | 20 MHz 3.3 V CMOS XO, series-terminated to the ADC and the FPGA |
| `fpga_core` | Gowin GW1NR-9 (QN88P) with in-package PSRAM capture buffer (spec: ≥16k samples/ch) |
| `usb_bridge` | FT232H in 245 sync FIFO mode, 93LC56 EEPROM |
| `io_expansion` | Status LEDs, external trigger/GPIO header, 1.8 V ↔ 3.3 V/5 V level translation (SN74LV4T125, SN74LV1T34) |

Guaranteed mode is block capture; continuous streaming (30 MB/s vs a ~40 MB/s practical
ceiling) is best-effort only.

## Result — complete

- **ERC: 0 errors, 0 warnings** ([`__main__.erc`](__main__.erc)); independent ERC gate PASS
  ([`outputs/erc_report.md`](outputs/erc_report.md)).
- **Design review:** [`outputs/design_review.md`](outputs/design_review.md) — 0 high,
  3 medium, 14 low, 5 fixed. The driver re-ran ERC and the footprint check after the
  review edits but did **not** re-run the independent reviewer.
- **Exported:** [`outputs/dual_adc_usb.net`](outputs/dual_adc_usb.net) and
  [`outputs/dual_adc_usb_bom.xml`](outputs/dual_adc_usb_bom.xml) — **204 parts, 169 nets**
  (counted from the netlist).
- Six symbols generated into [`symbols/`](symbols/); BNC and trimmer footprints built from
  vendor drawings in [`footprints/`](footprints/).
- BOM ≈ $91/board at qty 10 ([`sourcing/sourced_bom.md`](sourcing/sourced_bom.md)),
  priced against live JLCPCB data.

## Evaluation

**Good**

- Coders caught several bad BOM symbol/footprint choices: resistor arrays with a common
  pin (would have shorted all ADC data lines together), a dual-BNC footprint used for a
  single jack, an 8-pin EEPROM symbol on a 6-pin part, and a crystal symbol that put a
  pin on a ground pad.
- The design review found two gaps against vendor reference circuits and fixed them:
  missing 2.2 µF ADS5231 REFT/REFB caps (TI Fig. 21), and Gowin MODE pull-downs at
  4.7 kΩ instead of 1 kΩ plus a missing DONE pull-up (UG290).
- The driver moved the FT232H 4.7 µF bulk cap onto the correct pin per FTDI's 3.3 V
  reference schematic.
- The driver overruled a false alarm from the datasheet phase ("avoid FPGA pins 68–88")
  after checking Gowin's pin table and pinout figure itself.
- SKiDL bugs found for upstream: `MPN=`/`LCSC=` passed as `Part()` keywords never reach
  the netlist (confirmed with a test netlist; worked around in `__main__.py`);
  `gen_xml.py:67` iterates `net.pins` unsorted so BOM XML line order changes between runs;
  the root node's empty tag triggers a spurious "Missing tag" warning.

**Bad**

- **Aliasing risk accepted rather than fixed.** The AAF is 2nd-order, giving only
  −14.5 dB at 15 MHz; at 20 MSPS, 15–20 MHz content folds into 0–5 MHz and decimation
  can't remove it. Logged as a medium accepted risk. The cheapest fix the review
  suggested (run the ADC at 40 MSPS with 4:1 decimation) was not applied.
- The capture spec is only ≥16k samples/ch (1.6 ms), far short of what the in-package
  PSRAM could hold. The prompt didn't ask for a record length. From run 5 on, the prompt
  requires ≥0.1 s.
- The sample-clock XO has no published jitter figure, so it can't be checked against
  the jitter budget on paper.
- The spend limit killed the first ERC reviewer. It left only an empty handoff and
  cost an overnight wait.
- The assembler wrote the netlist and BOM before the independent gate had run.

## Cost

| Measure | Value | Source |
|---|---|---|
| Equivalent API cost | **$93.45** — Opus $78.01 (808 msgs) + Sonnet $15.44 (331 msgs) | [`claude_cost.txt`](claude_cost.txt) |
| Tokens | 138.8M total, 132.7M of them cache reads | [`claude_cost.txt`](claude_cost.txt) |
| Elapsed | ~18 h, including ~4.7 h and ~11 h waits on spend-limit resets | transcript |
| Longest agents | architect 34.6 min · datasheets 17.7 min · sourcing 13 min · ERC reviewer 15 min | transcript |

[`session_cost.json`](session_cost.json) is a stale copy of run 3's file (same session
UUID, $124.91) and does not describe this run. Use `claude_cost.txt`.
