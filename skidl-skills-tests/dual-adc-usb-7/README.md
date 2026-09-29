# dual-adc-usb-7 — SKiDL Skills, autonomous run, record-length prompt

Third run of the run-5 prompt. This run had the most architecture churn: two reworks
(the cap) to fix an FPGA power rail and I/O budget that the datasheet phase had
misjudged. It was also the only run to finish with ERC 0/0 *and* a passing BOM-vs-code
gate (`validate-bom.py`).

- **Dates:** 2026-09-22 12:34 → 2026-09-23 09:49
- **Tool:** SKiDL Skills plugin (pipeline state v5.1), Claude Code v2.1.278, Opus 5 (Claude Pro), SKiDL 3.0.0, KiCad 9
- **Prompt:** [`dual-adc-prompt.txt`](dual-adc-prompt.txt) — identical to runs 5, 6 and 8
- **Transcript:** [`claude_transcript.txt`](claude_transcript.txt) (132 KB)

## Design that came out

USB-C, 5.1 kΩ CC pulldowns, 8 blocks (`afe_input` and `afe_driver` parameterised per channel):

| Block | Content |
|---|---|
| `afe_input` ×2 | BNC, 1 MΩ ∥ 20 pF ÷11 divider, BAV199 clamp to both rails (±50 V survival) |
| `afe_buffer` | AD8066 dual JFET unity buffer |
| `afe_driver` ×2 | THS4521 FDA + 4-pole passive LC anti-alias (−3 dB at 4.23 MHz, −41.8 dB at 10 MHz), BAT54S clamps |
| `adc_dual` | TI ADS5231 dual 12-bit at **10 MSPS** (PLL disabled over SPI; SEL driven by the FPGA) |
| `clock_gen` | SX3M 10 MHz CMOS XO, series terminations to the ADC and the FPGA |
| `fpga_core` | Gowin GW1NR-9 (QN88P), 64 Mbit in-package PSRAM = 8 MB (≥0.1 s needs 4 MB), JTAG, LEDs; AUTOBOOT from on-die flash |
| `usb_bridge` | USB-C, USBLC6 ESD, FT232HL sync FIFO, 93LC56B EEPROM |
| `power_tree` | TPS22918 load switch + BSS138, 2× TLV62569 buck, RT9013 analog LDO, TPS60403 charge pump (negative rail), AP2127K-1.8 + second TPS22918 as a VCCIO3 slew limiter |

Power budget: 255 mA typical / 424 mA worst. That fits a legacy 500 mA port, but the
Type-C receptacle was kept because 85 % loading leaves little margin.

## Result — complete

- **ERC: 0 errors, 0 warnings** ([`__main__.erc`](__main__.erc)). The EEPROM-bus warnings
  were removed by overriding pin functions, not by suppressing ERC, so the nets are still
  fully checked. Independent gate FAILED the first pass and passed on the re-gate
  ([`erc_report.md`](erc_report.md)).
- **`validate-bom.py`: exit 0, 170/170 refdes** matched between code and BOM.
- **Exported:** [`outputs/dual_adc_usb.net`](outputs/dual_adc_usb.net) and
  [`outputs/dual_adc_usb_bom.xml`](outputs/dual_adc_usb_bom.xml) — **170 parts, 127 nets**
  (counted from the netlist); byte-identical across runs.
- BOM rev 4, ≈ $88.9–90.9/board at qty 5, live-sourced
  ([`sourcing/sourced_bom.md`](sourcing/sourced_bom.md), [`.csv`](sourcing/sourced_bom.csv)).
- Documentation defects that don't affect the netlist, and bench-verify items, are listed
  in [`handoffs/doc_defects.md`](handoffs/doc_defects.md).

## Evaluation

**Good**

- **The FPGA rail/I-O question needed three agents to settle.** The datasheet phase
  inferred the PSRAM's bank and reported 71 free I/O. A coder escalated a BANK0 rail
  conflict. The driver checked the fact before re-architecting on it. The architect then
  reversed the driver's proposed fix: putting 1.8 V on VCCX would have bricked the board
  (2.375 V minimum). The real PSRAM bank is BANK3/pin 12, confirmed against a Tang Nano 9K
  schematic. The final budget is 48 usable 3.3 V I/O for 46 used. Run 3 made the same
  "71 → 48" correction on the same part.
- **The architect's pin-saving strap was rejected against the datasheet.** Making ADS5231
  SEL static would have left no reliable way to disable the PLL (TI SBAS295A p.19),
  so 10 MSPS would have failed. SEL was restored as a dynamic pin, and the 3-pin shortfall
  was closed another way.
- **A soft-start fix that did nothing was caught.** Sourcing proposed an RC on the LDO's
  enable pin to slow the 1.8 V ramp. A datasheet check showed that only delays turn-on
  without changing dV/dt. Replaced by a second TPS22918, whose CT pin gives a 260 µs rise.
- **A power-sequencing deadlock was found in code:** P3V3D sat downstream of the switch it
  would enable, which would have powered the board before enumeration.
- The independent gate found the JTAG header referenced to 3.3 V while the JTAG pins are
  on the 1.8 V BANK3 (2.1 V abs max). The block contradicted itself 40 lines later. On
  the re-gate, the reviewer enumerated all 13 BANK3 pins against the netlist instead of
  re-reading the coder's list.
- Net-plan errors caught by coders: FT232H VCORE tied to 3.3 V (it's a 1.8 V LDO
  *output*); wrong FT232H supply pin numbers; a clamp to only one rail; RESET# missing.
  A rejected EasyEDA AD8066 pinout had 5 of 8 pins and no second channel.

**Bad**

- **Five separate decoupling shortfalls** came from the skeleton BOM, including an op amp
  with no bypass at all. The driver called it a systematic allocation gap, not chance.
- `validate-bom.py` caught 13 BOM-vs-code mismatches at assembly, including six caps that
  sourcing had funded but no code instantiated.
- **Signature drift:** five of eight blocks ended with signatures different from the
  architecture. One was forced by SKiDL: `@SubCircuit` consumes `tag=`, so a block
  parameter named `tag` can never be set by keyword.
- Open at export: the J1/J2 BNC and J4 USB-C footprints use other manufacturers' land
  patterns (`validate-footprints.py` can't detect this, as in run 6). U15's ON-tied-to-VIN
  arrangement is outside TI's characterised condition and needs bench verification.
  ADS5231 and GW1NR-9 are each the entire JLCPCB stock.
- **Clock jitter was never checked.** X1 is a Yangxing SX3M10.000M20F30TNN, and its
  summary calls it "freely substitutable". Run 6 read the datasheet for an SX3M sibling,
  found no phase-jitter figure, and replaced the part. This run never raised the question.
  Run 8 repeated the pattern with a 40 MHz SX3M.
- The driver's "write the skeleton first" instruction made the architect overwrite the
  rev-2 handoff before reading it. Rev 3 was rebuilt from intact artifacts; the driver
  called that luck.
- The spend limit killed agents four times. None lost completed work, but the waits
  added ~17 h of elapsed time.
- The driver's own spec set SNR ≥ 60 dB (≈10 ENOB), not true 12-bit accuracy. It flagged
  this at the end as the largest cost lever in the design.

## Cost

| Measure | Value | Source |
|---|---|---|
| Equivalent API cost | **$155.97** — Opus $110.24 (1,252 msgs) + Sonnet $45.73 (761 msgs) | [`claude_cost.txt`](claude_cost.txt) |
| Tokens | 257.6M total, 241.9M of them cache reads | [`claude_cost.txt`](claude_cost.txt) |
| Elapsed | ~21 h, including ~1.5 h, ~3.9 h and ~11.4 h spend-limit waits | transcript |
| Architecture reworks | 2 of 2 allowed | [`pipeline_state.json`](pipeline_state.json) |

[`session_cost.json`](session_cost.json) is a stale copy of run 3's file (same session
UUID, $124.91) and does not describe this run. Use `claude_cost.txt`.
