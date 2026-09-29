# dual-adc-usb-5 — SKiDL Skills, autonomous run, record-length prompt

First run with the revised prompt, which requires ≥0.1 s of samples at the full rate and
permits USB-C if bus power is short. Runs 5–8 use the same prompt, so they show
how much the output varies between runs.

- **Dates:** 2026-09-20 11:12 → 2026-09-21 08:27
- **Tool:** SKiDL Skills plugin, Claude Code v2.1.268, Opus 5 (Claude Pro), SKiDL 3.0.0, KiCad 9
- **Prompt:** [`dual-adc-prompt.txt`](dual-adc-prompt.txt) — base prompt plus:
  > A minimum of 0.1 seconds of samples at the maximum rate is required.
  > …
  > If insufficient power is available, use a USB C prt.

  plus the run-2 autonomy and blank-slate instructions.
- **Transcript:** [`claude_transcript.txt`](claude_transcript.txt) (32 KB)

## Design that came out

USB-C bus-powered, single +5 V supply (no negative rail), 8 blocks / 9 instances:

| Block | Content |
|---|---|
| `usb_c_input` | USB-C, 5.1 kΩ CC pulldowns, USBLC6 + SMF5.0CA ESD |
| `digital_power` | SY8089A buck, TLV758 LDO, AP2161W load switch gated by FT232H PWREN# → +3V3_D / +3V3_ADCD / +1V2_D |
| `analog_power_ref` | TLV757 analog LDO, TLV9062 bias/reference buffers |
| `afe_channel` ×2 | BNC, 1 MΩ compensated ÷20 divider returning to a 1.1 V bias (the level shift), STC3MA trimmer, BAV99 clamp, OPA355 buffer, THS4551 FDA, 3rd-order Butterworth AAF (−3 dB at 6.1 MHz) |
| `adc_dual` | TI ADS5231 dual 12-bit, sampled at 20 MSPS |
| `clock_20m` | OT252020 20 MHz XO (0.7 ps jitter) |
| `fpga_core` | Gowin GW1NR-9 (QN88), 64 Mbit in-package SDRAM → 8 MB = 104.9 ms of both channels at 20 MSPS |
| `usb_bridge` | FT232H in 245 sync FIFO mode, 93LC56B EEPROM |

The architect claimed the ADS5231's minimum clock is 20 MHz, so the board samples at
20 MSPS and the **host** is expected to decimate 2:1. Run 7 later ran the same ADC at
10 MSPS with its PLL disabled over SPI, and this run's own datasheet phase pointed that
out. The driver decided not to reopen the architecture over it.

## Result — complete

- **ERC: 0 errors, 19 warnings** ([`__main__.erc`](__main__.erc)), all on block-internal
  nets; the independent reviewer upheld all 5 false-positive claims.
  Independent gate PASS after a post-fix re-gate ([`erc_report.md`](erc_report.md)).
- **Exported:** [`outputs/dual_adc_usb.net`](outputs/dual_adc_usb.net) and
  [`outputs/dual_adc_usb_bom.xml`](outputs/dual_adc_usb_bom.xml) — **175 parts, 150 nets**
  (counted from the netlist); netlist byte-identical across runs.
- BOM at revision 4, ≈ $85/board (ADC $31.77 + FPGA $23.31), live-sourced.
- Architecture reworked twice (the cap is 2): power tree, then the filter.

## Evaluation

**Good**

- Four defects that ERC can't see were caught before export:
  - **93LC46B EEPROM incompatible with the FT232H.** The coder found the FTDI datasheet
    that the datasheet phase couldn't get; §4 requires a 93LC56B-class part. Re-sourced
    to a pin-compatible replacement.
    (Run 2's BOM uses a 93LC46BT with its FT232HL. Nobody has checked that design against
    this finding.)
  - **Load switch Q1 couldn't turn off:** a P-FET with its source at 5 V, driven by a
    3.3 V PWREN#. Replaced by an AP2161WG-7 with a ground-referenced enable.
  - **SY8089 VFB unverified.** If it were 0.8 V rather than the assumed 0.6 V, the
    3.3 V rail would come up at 4.4 V. Confirmed at 0.6 V from Silergy's own document.
  - **AAF was 2nd-order, not 3rd:** C_cm and C_diff shared a node behind the same 33 Ω
    and merged into one pole, giving −4.55 dB at 4 MHz. The ERC reviewer found it; the
    architect reworked the filter; a second independent gate checked the new topology.
- The architect rejected the reviewer's proposed bias-resistor values with arithmetic
  (one of them wasn't an E96 value) and supplied its own.
- The driver re-gated after the filter fix instead of trusting its own ERC re-run,
  because the AFE topology had changed.

**Bad**

- **The design depends on host software.** Any 2:1 decimation must include a ≥40 dB
  digital low-pass above 5 MHz; plain sample-dropping loses the anti-alias spec with no
  hardware symptom. Recorded as requirement S1 / risk R-12.
- **Open at export:** the 3rd-order filter relies on the THS4551's internal FB↔IN
  strapping, and the SBOS778 datasheet was never obtained (H-2). The stopband misses by
  1.84 dB at ±5 % C0G tolerance; the nominal margin rests on a 0.6 pF parasitic in TI's
  model (M-2). The BNC footprint and the FPGA exposed pad are unverified.
- The spend limit killed three block coders at once (Opus, parallel), then the ERC
  reviewer. Recovery lost no work: completed files were found on disk and resumed rather
  than redone.
- Requirement-phase targets (the $70 cost cap and 200-unit stock floor) were the
  driver's own numbers, and the design missed both. This was flagged honestly.

## Cost

| Measure | Value | Source |
|---|---|---|
| Equivalent API cost | **$149.87** — Opus $120.45 (1,029 msgs) + Sonnet $29.41 (602 msgs) | [`claude_cost.txt`](claude_cost.txt) |
| Tokens | 201.2M total, 188.9M of them cache reads | [`claude_cost.txt`](claude_cost.txt) |
| Elapsed | ~21 h, including ~5.5 h and ~12 h waits on spend-limit resets | transcript |
| Architecture reworks | 2 of 2 allowed | [`pipeline_state.json`](pipeline_state.json) |

[`session_cost.json`](session_cost.json) is a stale copy of run 3's file (same session
UUID, $124.91) and does not describe this run. Use `claude_cost.txt`.
