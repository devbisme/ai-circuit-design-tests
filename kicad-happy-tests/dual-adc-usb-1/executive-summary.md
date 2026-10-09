# Executive Summary — `dual_adc_usb` Analysis with kicad-happy

Date: 2026-10-07 · Tools: kicad-happy 2.3.1 (`kicad`, `emc`, `spice` skills), KiCad 10.0.4
`kicad-cli` (via `/home/devb/bin/kicad10`), ngspice.

## Bottom line

- The board is electrically complete. KiCad DRC finds no shorts and no unconnected items, and
  after the rule change below it has **0 DRC errors**.
- The only real layout defect was a **rules mismatch**: the routing used ~0.15 mm clearance
  and width, but the board's rules said 0.2 mm. The rules were relaxed to 0.15 mm and the
  zones refilled and saved.
- **Nothing was checked against datasheets.** None of the 56 unique parts has an MPN, and
  there is no `datasheets/` directory. Every finding is a consistency check only: the design
  agrees with itself, not necessarily with the real parts.

## Design

170 schematic parts, plus mounting holes H1–H4 that are only on the PCB. 4 layers:
In1 = GND plane, In2 = +3V3 plane. 140 × 90 mm, all parts on the top side, fully routed.

| Block | Parts |
|---|---|
| Analog front ends (×2) | BNC input, BAV199 clamp diodes, ADA4817 buffer, THS4521 differential driver |
| ADC | LTC2290 dual 12-bit ADC, SiT8008 10 MHz oscillator |
| FPGA | iCE40HX4K-TQ144, W9812G6KH SDRAM, W25Q32 configuration flash |
| USB | FT2232HL, 93LC56 EEPROM, USBLC6 ESD protection, USB-B connector |
| Power | TPS62160 (+3V3), TLV75512 (+1V2), LP5907 (+3V0), LM27762 (+4V / VEE) |

## What was run

| Step | Result |
|---|---|
| Schematic analyzer | 80 findings: 7 errors, 3 warnings, 70 info |
| PCB analyzer (`--full`) | 126 findings: 4 errors, 10 warnings, 112 info |
| Schematic/PCB cross-check | 1 warning (GND split; a false positive) |
| EMC pre-compliance | 179 findings: 124 errors, 49 warnings, 6 info. The ground-plane rule's 134 findings are wrong (see below). |
| SPICE | 36 of 36 subcircuits pass (RC filters, dividers, decoupling, inrush, op-amps, crystal) |
| Thermal | Info only. The hottest part is U403 (LP5907) at an estimated 84 °C, from an assumed 117 mA load and a pessimistic package value. |
| KiCad ERC | 157 warnings: 155 library-symbol mismatches, 2 from U603's WP/HOLD pins tied to +3V3 |
| KiCad DRC (before fix) | 524 errors (510 clearance, 14 track width), 343 warnings, 174 schematic-parity warnings |
| **Not run** | Gerber check (no Gerbers exist), lifecycle audit (no MPNs, no distributor API keys), per-chip datasheet review (no datasheets) |

Analyzer outputs are in `analysis/2026-10-07_1748/`.

## Findings

### Real issues

1. **Clearance and width rules broken (fixed).** After refilling the zones, all 500 clearance
   errors were between 0.152 and 0.200 mm, against a 0.2 mm rule. There were also 14 track
   segments at 0.15 mm, on OSC_OUT, VCCPLL0/1 and OSCI. The router clearly used ~0.15 mm rules.
2. **Stale zone fill (fixed).** The saved fill caused 237 via-to-plane clearance errors. Every
   gap was exactly 0.1505 mm, so nothing overlapped and **plotting would not have shorted
   anything**. An earlier session wrongly called this a short-causing blocker. It was still
   worth refilling.
3. **No fiducials, no test points (open).** This matters only for machine assembly; the
   0.5 mm-pitch TQFP-144 makes fiducials advisable.
4. **No MPNs (open).** This blocks sourcing, BOM pricing, lifecycle checks and datasheet checks.
5. **Few vias under exposed pads (open, low risk).** U101 and U201 have 1 each, U404 has 3,
   U301 has 21 of the 25 the analyzer wants. At these power levels this is probably fine, but
   it is a judgment, not a calculation.

### Minor items worth a look

- There is no capacitor on VBUS ahead of FB501; the 100 nF is on the +5V side.
- The THS4521 input and feedback traces run over solid GND. TI's layout guidance for
  high-speed amplifiers, as I recall, is to clear the plane under the input pins to cut stray
  capacitance. That is from memory and low priority at the LTC2290's 10 MS/s.
- The EMC check flags clock nets, including SD_CLK and ADC_CLK, for changing layers without a
  nearby stitching via. Worth a look on SD_CLK.

### Analyzer false positives (checked against the raw design files)

| Finding | Why it is not a problem |
|---|---|
| PP-001: iCE40 VCCPLL0/1 have no DC path to a power rail | They are fed from +1V2 through 100 Ω (R605/R606) into 10 µF + 100 nF. That is the usual iCE40 PLL filter (from memory); the analyzer's search doesn't go through resistors. |
| VM-001: VCMA, VCMB and AN_EN cross 4 V / 3 V domains | VCMA/VCMB are the LTC2290's analog common-mode outputs driving the THS4521 VOCM pins, not logic. AN_EN is a 2N7002 drain pulled up to +3V3 by 100 k, and both enables accept 3.3 V. |
| PU-001: PG and PGOOD pins lack pull-ups | Both pins are marked no-connect on purpose. |
| PS-002: GND plane split into 7 islands | The "islands" are U301's ground pads on F.Cu. KiCad reports 0 unconnected items. |
| EMC GP-001 (134 findings): signals over a plane gap | Tested against the raw In1 GND fill polygon: `/AFE_A/FDA_INN`, reported at 0% coverage, is 100% over GND. Refilling the zones did not change the analyzer's output. This rule cannot be trusted on this KiCad 10 file; a parsing problem is suspected but not confirmed. |
| PM-002: J101/J201 overhang the board edge by 21 mm; J501 is 0.09 mm from the edge | Horizontal BNC and USB-B connectors normally sit at or over the edge. **Please confirm this is intended.** |
| ERC/DRC library and parity warnings | Library drift, `~` vs empty Datasheet fields, and H1–H4 existing only on the PCB. All cosmetic. |

## Changes made

| File | Change |
|---|---|
| `dual_adc_usb.kicad_pro` | Default net class clearance 0.2 → 0.15 mm (line 498); board minimum track width 0.2 → 0.15 mm (line 156). The default routing width stays 0.2 mm. |
| `dual_adc_usb.kicad_pcb` | Zones refilled and saved with `kicad-cli pcb drc --refill-zones --save-board`. |

Checks after the change:

- The board file went from 2.19 MB to 1.73 MB.
- With zone fill polygons stripped out, the old and new files are identical: 2501 segments,
  493 vias and 174 footprints in both.
- DRC now shows 0 errors and 0 unconnected items. 343 warnings remain: 170 library-footprint
  mismatches and 173 silkscreen overlaps.
- The DRC report is `analysis/2026-10-07_1748/drc_after.json`.

Caveats:

- The 0.15 mm limit has not been checked against a specific fab's current rules. As far as I
  know it is within standard 4-layer capability.
- The files are not in git. Backups of the originals were saved only to a temporary session
  directory.
- The analyzer outputs in `analysis/2026-10-07_1748/` describe the board before the change.

## Recommended next steps

1. Add MPNs, then download datasheets (LCSC needs no API key) and rerun the review with
   per-chip pinout checks. This turns the consistency checks into real verification.
2. Add 3 fiducials, plus test points if the board will be machine-assembled or tested on a
   fixture.
3. Confirm the BNC overhang and the fab's 0.15 mm capability before ordering.
4. Rerun the analyzers on the saved board and generate Gerbers so they can be checked too.
