# dual-adc-usb-1 — SKiDL Skills, interactive run

First run of the SKiDL Skills pipeline on the dual-channel ADC board. Human in the loop at
every approval gate.

- **Dates:** 2026-09-06 13:30 → 2026-09-07 16:30
- **Tool:** SKiDL Skills plugin, Claude Code v2.1.263, Opus 5 (Claude Pro), SKiDL 3.0.0, KiCad 9.0.9
- **Prompt:** [`dual-adc-prompt.txt`](dual-adc-prompt.txt) — base prompt only, no autonomy instruction
- **Transcript:** [`claude_transcript.txt`](claude_transcript.txt) (59 KB, the only run with one)

## Design that came out

USB-C bus-powered, 4-layer, 12 blocks:

| Block | Content |
|---|---|
| `usb_power_input` | USB-C 2.0, 2×5.1k CC, ESD/TVS, P-FET soft start, digital/analog rail split |
| `power_digital` | TLV62569 buck 5V→3V3, LDO →1V2 core |
| `power_analog` | LP5907 →3V0 AVDD, LM27762 → ±4 V |
| `vref_2v5` | ADR4525 2.5 V 2 ppm/°C, 0.1 % divider → 1.000 V, OPA192 buffer |
| `afe_channel` ×2 | BNC 1 MΩ‖20 pF, 10:1 compensated attenuator, BAV199 clamps, OPA1656 buffer + Sallen-Key, THS4521 FDA, 4th-order Butterworth fc = 4.3 MHz |
| `adc_dual` | LTC2292 dual 12-bit 40 MSPS, parallel CMOS, 33 Ω damping |
| `clock_40m` | 40 MHz ≤1 ps-class XO on its own LDO + LC |
| `fpga_ice40` | iCE40HX4K-TQ144 — 4:1 decimation, trigger, SRAM burst controller, FIFO drain |
| `sram_buffer` | IS61WV204816BLL-10, 2M×16, 10 ns, 4 MB = 1 MS/ch |
| `config_flash` | W25Q32JV SPI + mode strap |
| `usb_bridge_ft2232h` | FT2232HL — ch A sync 245 FIFO, ch B MPSSE for FPGA config, 93LC66 cal EEPROM |
| `aux_io` | probe comp 1 kHz, ext trigger, status LEDs |

Throughput contradiction resolved by 40 MSPS sampling → 4:1 decimation → 1 MS/ch burst
capture into SRAM, drained over the FIFO.

## Result

- All 12 block files written; `circuits/dual_adc_usb/__main__.py` instantiates all of them.
- Last recorded ERC ([`__main__.erc`](__main__.erc), 2026-09-07 16:21): **0 errors, 14 warnings**
  (13 "insufficient drive current" on rails fed through ferrites/LDOs, 1 open-collector↔
  bidirectional CDONE tie, 1 genuinely unconnected `TLV62569 GND` pin — that last one is a
  real defect, not a false positive).
- **No netlist or BOM exported.** `pipeline_state.json` was never updated past
  `stage: coding` and still lists blocks as `in_progress`/`escalated`, so the state file
  understates what actually landed on disk.
- 189 `Part()` calls across 2811 lines of SKiDL.

## Evaluation

**Good**

- The interview surfaced the USB-2.0-vs-240 Mbit/s contradiction and the 500 mA budget
  problem in the first 90 seconds, before any design work.
- Sourcing was genuinely rigorous: rejected AS6C3216 on bus timing (tAW = 50 ns min in a
  50 ns slot — zero margin) *and* on availability (discontinued at Digi-Key, successor
  $36.46 ×2 vs $33.54 for one IS61WV204816BLL); flagged that the LTC2292 SNR figure came
  from a product page rather than the PDF and refused to close the ENOB budget until the
  28-page datasheet was retrieved.
- Cost was tracked honestly against the estimate: $70–100 quoted at interview → $104–153 at
  architecture → **$175–185/board actual**, with the drivers named (LTC2292 at $51.64,
  ~$24/board of uncounted JLCPCB extended-part setup fees).
- Caught its own architecture's hallucination: the LTC2292 has no `CLKOUT` pin (only CLKA/
  CLKB inputs). The block coder found it against the datasheet and escalated it as blocking,
  and the resolution (falling-edge capture, 7.1 ns setup / 13.9 ns hold, no PLL) is in
  [`CODING_BRIEF.md`](CODING_BRIEF.md).

**Bad**

- Repeated subagent truncation. Context was lost twice to stopped agents, which is why
  `SOURCING_BRIEF.md` and `CODING_BRIEF.md` exist at all — they are hand-built prosthetics
  for a pipeline whose own state file wasn't carrying the load.
- One resumed coding agent burned 45 tool calls and ~150K tokens on datasheet fetching that
  had been explicitly marked non-blocking, and wrote nothing to disk.
- Every hook invocation failed (`Permission denied` on `~/.claude/skills/skidl-skills/scripts/*.sh`
  — not executable). Harmless but constant noise, and a write-protection hook blocked the
  session's final repair of `clock_40m.py`.
- The architecture was frozen before the datasheets were read, so datasheet-driven
  corrections (the CLKOUT pin, the TLV62569 package, the XO fanout to three loads) arrived
  as expensive rework during coding.

## Cost

No token or dollar totals were captured — this predates any cost-logging convention here.
What is recoverable:

| Measure | Value | Source |
|---|---|---|
| Elapsed wall clock | ~27 h across 2 days (13:30 Sun → 16:30 Mon, including an ~11 h overnight idle) | file mtimes + transcript |
| Model time, main thread | ~49 min | sum of transcript thinking timers |
| Model time, subagents | ~107 min over 18 agent runs (longest: 48m 52s, 19m 42s, 10m 23s) | transcript `finished ·` lines |
| Total model time | **~2.6 h** | sum of the two above |
| Human time | substantial — 9+ interview questions plus 3 approval gates | transcript |
| Datasheets pulled | 20 PDFs, ~40 MB | `datasheets/` |
| **Terminating condition** | **Claude Pro monthly spend limit reached (HTTP 429) mid-coding** | transcript |

The last line is the finding that matters. On a Pro plan, one board of this complexity —
12 blocks, 189 parts, 20 datasheets, live sourcing — exhausted the monthly budget before
producing a netlist. Run 2 was the response.
