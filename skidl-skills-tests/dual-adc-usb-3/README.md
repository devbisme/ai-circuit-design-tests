# dual-adc-usb-3 — SKiDL Skills, autonomous run (driver-rescued)

Third run, same prompt as run 2. Reached export with a clean ERC, but only because the
main thread wrote five of the nine blocks itself after the spend limit killed every block
coder. The same session then measured its own cost and refactored the plugin, so the tail
of the transcript is plugin development, not design work.

- **Dates:** 2026-09-09 22:37 → 2026-09-10 07:41 (design); plugin work continued through 2026-09-10
- **Tool:** SKiDL Skills plugin, Claude Code v2.1.267, Opus 5 (Claude Pro), SKiDL 3.0.0, KiCad 9
- **Prompt:** [`dual-adc-prompt.txt`](dual-adc-prompt.txt) — identical to run 2 (base prompt + "decide autonomously" + "blank slate")
- **Transcript:** [`claude_transcript.txt`](claude_transcript.txt) (161 KB). Lines 1–1500 are the design; 1501 onward are cost measurement and the plugin refactor.

## Design that came out

USB-C bus-powered, 9 blocks (`analog_frontend` instantiated ×2):

| Block | Content |
|---|---|
| `usb_c_port` | USB-C receptacle, CC pulldowns, ESD, VBUS entry |
| `power_digital` | AP2112K always-on LDO, TLV62569 + TLV62568 bucks, LP5907 LDO → +3V3_AON / +3V3 / +1V2 / +1V8 |
| `power_analog` | LM27762 → ±4.2 V bipolar rails, +3V0A AVDD |
| `analog_frontend` ×2 | BNC 1 MΩ ∥ ~20 pF, ÷11 compensated attenuator (909k/90.9k), BAV199 clamp, AD8066 buffer + Sallen-Key, THS4551 FDA with MFB section (4th-order total) |
| `adc_pair` | 2× AD9235BCPZ-40 (12-bit), shared clock, refs, VCM divider |
| `clock_gen` | SiT1602BI 10 MHz XO + 74LVC2G34 fanout |
| `fpga_capture` | Gowin GW1NR-9 (QN88P) — 12-bit packing, 64 Mbit in-package PSRAM burst buffer (2.8 Mpt/ch, 280 ms at full rate) |
| `usb_controller` | CY7C68013A (FX2LP) slave FIFO, CAT24C128 boot EEPROM |
| `aux_io` | External trigger header with ESD, power and capture LEDs |

Throughput contradiction resolved by making on-board 12-bit packing mandatory (30 MB/s
packed vs 40 MB/s padded) plus a triggered burst buffer so full-rate capture never depends
on the host.

## Result — complete

- **ERC: 0 errors, 0 warnings** ([`__main__.erc`](__main__.erc)); independent ERC review
  PASS on second pass ([`erc_report.md`](erc_report.md), [`handoffs/06_erc.md`](handoffs/06_erc.md)).
- **Exported:** [`outputs/dual_adc_usb.net`](outputs/dual_adc_usb.net) and
  [`outputs/dual_adc_usb_bom.xml`](outputs/dual_adc_usb_bom.xml) — **218 parts, 136 nets**
  (counted from the netlist). Pre-fab checklist in [`outputs/EXPORT_NOTES.md`](outputs/EXPORT_NOTES.md).
- Driver decisions that overrode the architecture, with options considered:
  [`architecture/driver_amendments.md`](architecture/driver_amendments.md).
- Three symbols (AD9235, AD8066, GW1NR-9) generated with kipart; one custom inductor
  footprint in [`footprints/`](footprints/).
- Netlist UUIDs made stable (tags derived from refdes) — every run of the circuit now
  produces the same netlist apart from the date line.

## Evaluation

**Good**

- The independent ERC reviewer found two HIGH defects in code that ERC called clean:
  - **H1:** the MFB section in the FDA stage was wired so the summing node carried a
    single resistor; the "4th-order" filter was really 3rd-order and missed the HARD
    stopband spec (−27.2 dB vs ≥30 dB at 10 MHz). The same degenerate placement was in
    `net_plan.md`, so it came from the architecture. Rebuilt and re-derived independently
    by the reviewer to within 0.05 dB.
  - **H2:** the AD9235 clock swung to 3.318 V against a 3.30 V absolute maximum. Clock
    buffer moved to the +3V0A rail.
- The driver caught three more defects before review: the THS4551 wired across ±4.2 V
  (8.4 V on a 5.5 V abs-max part); a 3.3 V FX2LP output driving a 1.8 V FPGA bank pin;
  and the GW1NR-9 I/O budget, which the datasheet phase had reported as 71 usable pins
  (true for the die) when the QN88P package has 48 at 3.3 V for 47 signals.
- Three `net_plan.md` errors caught against datasheets: the AD9235 LFCSP has no OEB pin,
  FX2LP SLWR is RDY1/pin 2 (not PA1), and wrong Bank-3 pull-up references.
- The datasheet agent found that several "PDFs" on disk were HTML error pages, and
  checked that none of the summaries had been written from them.

**Bad**

- **The spend limit dominated the run.** The datasheet agent died on it repeatedly, then
  all nine block coders died together (a 9-way Opus fan-out). Four block files survived;
  the driver wrote the other five, the assembly, and the three symbols. The H1 filter
  defect was in the driver's own code, which is why the independent review mattered.
- One resumed datasheet agent was context-exhausted rather than rate-limited: identical
  result text, ~199k tokens and ~77 tool calls on every resume. Resuming it again would
  have repeated that; the driver switched to a fresh agent with a narrower scope.
- The LLM-backed PreToolUse hook blocked a legitimate heredoc write into `circuits/` and
  flagged several read-only commands as risky. The driver said "third false positive this
  session".
- Two items were left for a human at export: the BNC footprint (confirmed wrong: 10.1 mm
  hole spacing vs a 2.54 mm grid) and the SiT1602BI pinout (no datasheet found). The
  SiT1602 risk was closed later in the same session once a working datasheet URL turned up.

## Cost

This is the first run with token accounting. The session wrote
[`session_cost.py`](session_cost.py), which sums per-message `usage` from the main
transcript **and** the subagent task transcripts. Reading only the main file would have
missed about two-thirds of the spend. Dollar figures are equivalent first-party API cost,
not the Pro subscription bill.

| Measure | Value | Source |
|---|---|---|
| Design only (through export) | **$124.91** — Opus $105.88 + Sonnet $19.04, 1,537 messages, 181.7M tokens (174M cache reads) | [`session_cost.json`](session_cost.json), computed at 07:48 on 2026-09-10 |
| Whole session incl. plugin refactor | $249.82 — 1,958 messages, 358.6M tokens | [`claude_cost.txt`](claude_cost.txt), computed 2026-09-11 |
| Elapsed, design | ~9 h (22:37 → 07:41), including a ~5 h wait for the 05:00 limit reset | transcript |
| Per-agent split (design) | block coders $22.05 (9 runs, 4 of 9 files delivered) · ERC reviewer $15.39 · datasheet librarian $14.01 (3 runs, 82 min) · architect $9.48 · sourcer $5.01 · driver ~$59 | transcript, line ~1623 |

**Use $124.91 for comparisons with other runs.** The $249.82 figure includes roughly the
same amount again spent on plugin development in the same session.

## Plugin changes made in this session

After the design finished, the session was asked for cost-reduction recommendations and
then to implement them in the plugin working tree (`~/projects/AI/skills/skidl-skills`,
`reduce_cost` branch, no commits). From the transcript:

- Cap block-coder concurrency at ~3; batch small blocks into shared work orders.
- Every agent writes its handoff skeleton first and saves artifacts as it goes.
- Never resume a context-exhausted agent; restart it narrower.
- Replace the LLM-backed PreToolUse and Stop hooks with deterministic scripts.
- Scripts for batch sourcing, validated PDF fetching (`partdoc.py` rejects HTML-as-PDF
  and wrong-part PDFs), and a cross-project part cache (`part-cache.py`, with an off
  switch so blank-slate runs can disable it).
- SKiDL syntax rules updated: stable tags, deterministic refdes for multi-instance blocks,
  netted exposed pads, run with `python -m`.

Runs 4–8 show these changes at work (capped fan-out, `use_cache: false`,
disk-first resume after limit kills). That is an inference from their transcripts; the
plugin's git history would confirm it.
