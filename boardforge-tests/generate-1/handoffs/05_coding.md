---
phase: 05_coding
agent: skidl-assembler
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 1
next_phase: 06_review
---

# Phase 5 handoff — Coding (assembly)

## Decisions
1. All 9 blocks called with the keyword signatures their `handoffs/05_blocks/*.md` declare (all report "signature changed: no"; all match `architecture/net_plan.md`). No signature or net-name disagreements; no nets renamed.
2. `afe_channel` instantiated twice: `ch="A"` (`tag='afe_ch_a'`, refs 1xx) and `ch="B"` (`tag='afe_ch_b'`, refs 2xx). Every other block tagged with its block_id.
3. Buses created at top level, index 0 = LSB: `DA`/`DB` 12, `SD_DQ` 16, `SD_A` 12, `SD_BA` 2, `FT_D` 8.
4. Drive: only `GND` gets `.drive = POWER` + `#FLG001` PWR_FLAG at top level (no block drives ground; KiCad needs a power_out on it). All other rails are driven inside their source block (`+5V` #FLG501, `+3V3` #FLG601, `+1V2`/`+3V3A`/`+4V0A`/`-4V0A` regulator power_out pins) — no top-level drive added, to avoid duplicate drivers.
5. `boardforge.toml`: added `[libraries.footprints] my_board = "footprints/my_board.pretty"` — the custom J101/J201 (BNC) and C102/C202 (trimmer) footprints existed on disk but the library was not registered (`PKG:pins` 27/29 → now passes, KiCad `footprint_link_issues` warnings gone).
6. `_stabilize_tags()` called at import time after the last block call; 0 "Missing tag" warnings.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_10msps/__init__.py` | empty | — |
| `circuits/dual_adc_10msps/__main__.py` | top-level nets, 10 block calls, `_stabilize_tags()` | Wiring questions |
| `boardforge.toml` | design file + custom footprint lib registration | Library path questions |
| `build/reports/skidl.log`, `build/reports/erc.json` | ERC detail | Classifying findings |

## Next phase must
erc-reviewer — treat these as known/intentional (from block `## Carried forward`):
1. Intentional NC pins: U301.22 (DVB; DVA clocks both channels); U103/U203 pins 1, 4 (THS4551 FB-/FB+); U701.4 (N/C); U602.4 (NC); J501 A8/B8 (SBU1/2); U1001 P72 (CMPCS_B) and spare I/O P56, P66, P67, P74, P75, P78; U801.36 (A12), U801.40; U901.32, U901.33 (ACBUS8/9).
2. U702 (LM27762) PGOOD pin 1 is open-collector and tied to GND on purpose (unused, per datasheet). It conflicts with `#FLG001` on GND: SKiDL ERC ERROR + KiCad `pin_to_pin` error (OC vs power out). Any power_out on GND triggers it; removing `#FLG001` would just swap it for a GND `power_pin_not_driven` error. See Carried forward #1.
3. U1001 P73 (SUSPEND, bidirectional) tied to GND: SKiDL + KiCad warnings vs PWR_FLAG/PGOOD — intentional (SUSPEND unused).
4. 255 `lib_symbol_mismatch` warnings: generated-schematic library cache, not design faults.
5. Netlist stability: two runs give identical `components` and `nets` (UUIDs, values, connectivity); `diff -q` still differs because pin order inside the **symbol definitions** of multi-unit symbols (OPA2810, THS4551, XC6SLX4, 74LVC2G34) varies run to run. Tool-side (SKiDL/boardforge symbol export), not tags; KiCad placement is unaffected. Report upstream; no design change possible.
6. SPICE path gates (GAIN/FLAT/ALIAS A/B) NOT CHECKED: U101/U201 (OPA2810) and others unmodelled — model coverage issue for the reviewer/librarian.
7. Gateware notes (not hardware): ADS5231 PLL-disable register write; FT232H EEPROM 245-sync, ACBUS7 suspend option off; FPGA UCF per fpga.md bank plan.

## Carried forward
Remaining KiCad ERC errors (4) and review FAILs, attributed via `handoffs/03_sourcing.md` § Parts by block:
1. **power_analog** — U702 pin 1 PGOOD (open collector) on GND vs `#FLG001` power out: KiCad `pin_to_pin` error + the 1 SKiDL ERC error. Intentional tie; block fix if 0 errors required: leave PGOOD unconnected/NC (if datasheet allows) or tie via a resistor to GND, or reviewer waives.
2. **adc** — U301 pin 5 VDRV on `+3V3_ADCIO` (FB301 output): KiCad `power_pin_not_driven`. Block sets `.drive = POWER` (SKiDL only) but has no PWR_FLAG. Fix in block: `Part('power','PWR_FLAG', ref='#FLG301')[1] += adcio`.
3. **usb_c_input** — `#PWR266` (VBUS power symbol) on local net `VBUS`: KiCad `power_pin_not_driven`; also review `DS:USBLC6-2SC6` FAIL (U501.5 power input on signal net VBUS). Fix in block: `vbus.drive = POWER` + PWR_FLAG `#FLG502` on VBUS.
4. **usb_c_input** — J501 pin `SH` (SHIELD) unconnected: KiCad `pin_not_connected` (SKiDL warning). Block connects `'S1'` but the symbol's shield pin is `SH`. Fix in block: add `j['SH']` to `gnd`.
5. **all 9 blocks** — `BOM` FAIL: all 238 parts have no `LCSC` field; `sourcing/sourced_bom.csv` has one per row. Each block coder must add `fields['LCSC']` from the CSV (warning-level per part; gate result FAIL).
6. `DS:coverage` NOT CHECKED: no extraction for PSC-1608U52GC-G4 (fpga LEDs) and TXM12M0004252FBCEO00T (usb_fifo Y901) — datasheet-librarian.
7. Open from blocks: SX3M jitter unspecified (clock); W9812G6KH-6 pinout assumed (sdram); Y901 pinout assumed (usb_fifo); AVDD/VDRV sequencing not enforced (power_analog/power_digital).

## Do not redo
- Block-internal design, values, sourcing, MPNs, footprints, pin maps (all 9 block handoffs).
- Top-level net names (match `net_plan.md` exactly; `VIN_A/B`, `AIN_*` are constraint nets).

## Receipt
9 blocks (10 instances), 238 BOM parts + 6 PWR_FLAGs = 244 components, 216 nets; parity 216/216 OK.
SKiDL ERC: 1 error / 3 warnings. KiCad ERC: 4 errors (power_analog 1, adc 1, usb_c_input 2) / 256 warnings.
Review: BOM FAIL (no LCSC fields, all blocks), DS:USBLC6 FAIL (usb_c_input), PKG:pins PASS, SPICE paths NOT CHECKED.
Result: FAIL — block-attributed errors only; no inter-block wiring errors.
