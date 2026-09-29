# dual-adc-usb-8 — SKiDL Skills, autonomous run, Opus 5.5

Fourth run of the run-5 prompt, and the first with Opus 5.5 driving. It finished in one
sitting of about 2¼ hours for $26.48, roughly a sixth of the cost of runs 5–7, with no
spend-limit kill. The model, Claude Code version and SKiDL version all changed at once, so
the saving can't be pinned on any one of them.

- **Dates:** 2026-09-25 22:45 → 2026-09-26 01:00
- **Tool:** SKiDL Skills plugin (pipeline state v5.1), Claude Code v2.1.283, **Opus 5.5**
  (Claude Pro) with Sonnet 5 subagents, **SKiDL 2.3.0** (per the netlist header; runs 2–7
  used 3.0.0), KiCad 9
- **Prompt:** [`dual-adc-prompt.txt`](dual-adc-prompt.txt) — identical to runs 5–7
- **Transcript:** [`claude_transcript.txt`](claude_transcript.txt) (100 KB)
- **Extra:** [`executive_summary.md`](executive_summary.md) — a phase-by-phase summary of
  decisions and open risks, written on 2026-09-28 after the run. It is the only run with one.

## Design that came out

USB-C receptacle, 5.1 kΩ CC pulldowns, no PD controller. 9 blocks:

| Block | Content |
|---|---|
| `usb_power_in` | USB-C, USBLC6-2SC6 ESD, TPS22919 soft-start load switch → V5 |
| `power_digital` | 2× TLV62569 buck → 3.3 V / 1.2 V, TLV75518 LDO → 1.8 V (FPGA PSRAM bank) |
| `power_analog` | TPS7A2033 3.3 V analog LDO, LM27762 → asymmetric +3.29 / −2.01 V buffer rails |
| `afe_ch_a`, `afe_ch_b` | BNC (custom footprint), 909k/100k compensated divider ≈ 1 MΩ ∥ 20 pF with a Knowles JZ300 trimmer, BAV199 clamp, OPA356 buffer, THS4551 FDA in a 2-pole MFB (−3 dB 8.86 MHz, −32 dB at 35 MHz) |
| `adc` | TI ADS5231 dual 12-bit, sampled at **40 MSPS**, decimated ×4 to 10 MSPS in the FPGA |
| `clock` | SX3M 40 MHz XO direct to the ADC; separate 33 Ω branch to the FPGA (FPGA PLL kept out of the ADC clock path) |
| `fpga` | Gowin GW1NR-9 (QN88P), 8 MB in-package PSRAM = 0.21 s, JTAG header, LEDs; all 48 usable 3.3 V I/O used |
| `usb_bridge` | FT232HL sync FIFO (~35 MB/s), powered from 5 V as in Adafruit's FT232H board, 93LC56B EEPROM |

Power budget: 1.22 W typical / 2.03 W worst. That is just over the driver's own 2.0 W
margin, so the USB-C clause fired, but ~425 mA still fits a legacy 500 mA port.

The 40 MSPS / ×4 decimation choice is the fix run 4's design review suggested and didn't
apply. It rests on the claim that the ADS5231 can't clock below 20 MSPS, which runs 4–5
also made and run 7 contradicted (10 MSPS with the PLL off over SPI). Oversampling is a
defensible choice either way, because it relaxes the anti-alias filter.

## Result — complete

- **ERC: 0 errors, 6 warnings** ([`__main__.erc`](__main__.erc)). All six are FT232H
  EECS/EECLK pins typed `input` by the stock KiCad symbol; the reviewer accepted them.
  Independent gate **FAILED** on the first pass and passed at revision 2
  ([`erc_report.md`](erc_report.md)).
- **`validate-bom.py`: exit 0**, 170 parts / 131 rows, after the assembler's first run
  failed on 9 value mismatches.
- **Exported:** [`outputs/dual_adc_usb.net`](outputs/dual_adc_usb.net) and
  [`outputs/dual_adc_usb_bom.xml`](outputs/dual_adc_usb_bom.xml) — **170 parts, 129 nets**
  (counted from the netlist); byte-identical across runs apart from the date line.
  [`footprints/ProjectLocal.pretty/`](footprints/ProjectLocal.pretty/) must ship with it
  (J2/J3).
- BOM at revision 4, live-sourced through the pcbparts MCP
  ([`sourcing/sourced_bom.md`](sourcing/sourced_bom.md), [`.csv`](sourcing/sourced_bom.csv)).
  No whole-board total was recorded. The 35 priced active and connector parts sum to
  ≈ $89; passives aren't priced in the file.
- 0 architecture reworks. Design review skipped by the driver as redundant with the ERC gate.

## Evaluation

**Good**

- **Cost and time.** $26.48 and ~2¼ h, against $93–175 and 18–22 h for runs 4–7. No
  agent was killed by the spend limit, so there were no overnight waits.
- **The independent gate failed the design correctly again.** The hand-made BNC footprint
  was mirrored (ground lead on the wrong side). The fix was checked by reading pad
  positions back in pcbnew against the maker's drawing in all three views.
- **Datasheet phase fixed facts other phases had wrong:** 5 GW1NR-9 pin names from
  EasyEDA (checked against Gowin's IDE package file and the Tang Nano 9K schematic);
  DONE/READY not bonded on this package; `net_plan.md` putting FT232H VCCD on FT_VCORE; a
  missing VCCA cap; and missing VPHY/VPLL decoupling.
- **Sourcing caught non-obvious part errors:** a "trimmer" that was actually a
  voltage-tuned capacitor (replaced with a hand-adjustable JZ300), the 8-pin
  `93LCxxB` symbol on a 6-pin SOT-23 EEPROM, an auto-matched BAV19 for BAV199, and a
  37-unit-stock cap.
- The assembler found that SKiDL 2.3 wrote the sheet list in a different order on each
  run and sorted it in `__main__.py`, restoring byte-stable netlists.
- The analog front end was checked with numbers: the OPA357 was rejected because its
  input-stage crossover starts 0.087 V above the signal peak; the asymmetric buffer rails
  keep the OPA356 in range and the LM27762 within its 5.5 V span.

**Bad**

- **The FT232H datasheet was never read.** FTDI's site blocked the download, and the file
  saved as `datasheets/FT232HL-REEL.pdf` is an unrelated oscillator sheet. The power
  wiring comes from Adafruit's schematic; the FIFO-mode pin mapping and the 12 MHz
  crystal's load capacitance come from memory and distributor data. This is the same part
  that runs 2, 5 and 7 got wrong in different ways.
- **Clock jitter unchecked again.** X1 is another Yangxing SX3M with no published jitter
  figure; 1–3 ps RMS is assumed. Run 6 replaced an SX3M for exactly this reason.
- **FPGA facts from a reference board, not Gowin:** PSRAM on the 1.8 V bank and the
  boot-mode straps come from the Tang Nano 9K. There is no spare 3.3 V I/O. The JTAG
  header pinout was copied from Altera's USB-Blaster and is unchecked against the Gowin
  cable.
- **BOM-vs-code drift, again.** Coders escalated 12 stale symbol/footprint/note cells,
  then `validate-bom.py` caught 9 value mismatches. The code was right every time; the
  BOM was not.
- The sourcer's reports ran well past the 10-line receipt limit the driver set.
- Low stock on critical parts: ADS5231 154 (single maker), GW1NR-9 173, THS4551 469.
- A subagent deleted the untracked `skidl_REPL.erc` at the repository root, outside the
  run directory. Harmless, but out of scope.
- The Stop hook printed "Circuit modified but ERC not verified or failed" 13 times,
  including after the gate passed.
- The driver's own spec relaxed the bandwidth target (≥5 MHz → 0–4 MHz passband) because
  it conflicted with anti-aliasing. Reasonable, but it was the driver's number to begin with.

## Cost

| Measure | Value | Source |
|---|---|---|
| Equivalent API cost | **$26.48** — Opus 5.5 $21.89 (459 msgs) + Sonnet 5 $4.59 (172 msgs) | [`claude_cost.txt`](claude_cost.txt) |
| Tokens | 65.9M total, 63.3M of them cache reads | [`claude_cost.txt`](claude_cost.txt) |
| Elapsed | ~2¼ h (transcript: "Cooked for 2h 14m 7s"), no spend-limit waits | transcript |
| Architecture reworks | 0 | [`pipeline_state.json`](pipeline_state.json) |

`executive_summary.md` quotes $26.36; `claude_cost.txt` was computed later and is the
figure used here.

The drop has two parts. Tokens fell to 65.9M from 139–308M in runs 4–7. And
`session_cost.py` prices Opus 5.5 below Opus 5 ($4/$20 vs $5/$25 per M in/out; cache
reads $0.20 vs $0.50 per M), which matters because cache reads are ~96 % of the tokens. The
token drop is the more informative number for comparing runs.
