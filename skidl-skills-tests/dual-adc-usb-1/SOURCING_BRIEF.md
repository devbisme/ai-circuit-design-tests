# Sourcing brief — `dual_adc_usb`

Written 2026-09-06 at the architecture→sourcing handoff, because the `pcbparts`
MCP was installed mid-session and requires a Claude Code restart before its tools
are callable. This file exists so the queued work items survive that restart.

**Resume point:** `pipeline_state.json` is at `stage: "architecture"`,
`architecture_complete: true`, `coding_mode: "modular"`. Next stage is **part sourcing**.
Re-invoke `/skidl-ee:new-circuit` (or the orchestrator directly) and it resumes here.

## Pre-flight check

Confirm `mcp__pcbparts__*` tools are callable. `claude mcp list` showing "Connected"
is NOT sufficient — that was true before the restart while the tools were still
unavailable. Verify via ToolSearch. If they are still missing, stop and report;
the user chose to install this MCP specifically to avoid vendor-page guesswork.

## Work items

1. **SRAM shared-bus timing investigation.** Evaluate 2× AS6C3216-55TIN (one per
   channel, shared address/data bus, separate CE#/WE#) against the single
   IS61WV204816BLL-10TLI (~$33.54 Digi-Key, out of stock at LCSC).

   Per-device cycle time is NOT the question — each device sees 10 M writes/s
   = 100 ns/word against a 55 ns cycle, which is comfortable. The question is the
   **shared 50 ns bus slot** carrying all 20 M words/s. Verify from the actual
   AS6C3216 datasheet that t_WP (~40–45 ns typical for a 55 ns part) plus address
   setup/hold, data setup/hold, and device-to-device bus release (t_OHZ / t_WHZ)
   all fit inside 50 ns with margin.

   If it does not fit, fall back to the IS61WV204816BLL and say so plainly.
   Do not stretch the timing to make the cheap option work.

   Distinct from the architect's rejected option S5 (separate data buses, +17 pins).
   The shared-bus variant costs +2 FPGA pins (8 spare) and one more hand-soldered
   TSOP-48; it doubles depth to 2 MS/ch for ~$16 instead of ~$33.54.

2. **KiCad symbol generation** for whichever SRAM wins, via the kipart MCP
   (verified callable). Neither candidate has an existing symbol.

3. **Tier column filled for every BOM line.** The four critical ICs (ADC, FPGA,
   SRAM, FT2232H) may go Extended or off-JLC per SPEC §6.1.

4. **Hard floors carried forward** — specifications, not preferences:
   - SRAM cycle ≤ 25 ns for the single-device topology
   - Buffer op-amp i_n ≤ ~100 fA/√Hz
   - XO ≤ 3 ps RMS is acceptable; do not escalate over a 2–3 ps part
   - 0.1% thin-film and C0G in the signal path
   - **ADC SNR ≥ 68.5 dB** is the substitution gate. Below it the design drops
     under 12 ENOB and must come back to the user.

## Open verification item

LTC2292 SNR = 71.3 dB is currently sourced from Analog Devices' **product page**,
not the datasheet PDF (their host timed out five times across two fetch mechanisms).
The datasheet-librarian must confirm it from the PDF itself. The whole 12.49 ENOB
result rests on this number — the LTC2292 contributes 92.2% of total noise power.

## Closed

- **R5** (front-end thermal noise) — closed as unfounded. The original model treated
  the attenuator tap as a bare 90 kΩ resistor over 4 MHz (77 µV). A compensated
  divider forces R1C1 = R2C2, so preserving 20 pF input gives C1 = 22.2 pF,
  C2 = 200 pF, and the tap's Thevenin is 90 kΩ ∥ 222 pF with a 7.96 kHz corner.
  The correct integral is √(kT/C) = 4.30 µV — 18× lower. Verified independently.
  Budget: total 100.29 µV RMS → SNR 76.96 dB → **12.49 ENOB**.
- **A1** (regulatory) — user-confirmed: none for rev A, bench prototype.
- **Analog rails** — user-accepted ±4.00 V, superseding ±5 V. SPEC §3.1 updated.
