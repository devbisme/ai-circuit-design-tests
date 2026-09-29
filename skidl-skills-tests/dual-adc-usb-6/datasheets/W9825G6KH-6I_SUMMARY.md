# W9825G6KH-6I — 256Mbit SDRAM (buffer memory, U40)

**UPDATE (verification pass, 2026-09-21) — PDF obtained, pinout VERIFIED against Winbond
primary source.** `datasheets/W9825G6KH-6I.pdf` — Winbond **"W9825G6KH" datasheet, Revision
A03, Publication Release Date Jun. 01, 2016** (42 pp; found via the direct LCSC asset URL
embedded in the LCSC product page's SSR data, since LCSC's own `.pdf`-suffixed page URL is
a JS-rendered redirect that returns HTML to a plain fetch — the same failure mode phase 4
hit). Title page and document body both read "W9825G6KH" (the base part number this design's
"-6I" grade belongs to; Winbond publishes one datasheet across the -5/-5I/-6/-6I/-6J/-6L/-75
speed-grade family, so this is the correct document for W9825G6KH-6I).

Section 4 "PIN CONFIGURATION" (p.3) and Section 5 "PIN DESCRIPTION" (p.4) were diffed
pin-by-pin against the `W9825G6KH-6I` symbol in `symbols/dual_adc_usb.kicad_sym`
(54 pins). **Result: all 54 pin numbers and names match exactly — no mismatches.** The only
difference is typographic: Winbond's PDF renders the four active-low control signals
(chip select, row/column address strobe, write enable) with an overbar graphic that
`pdftotext` cannot extract (comes out as bare `CS`, `RAS`, `CAS`, `WE`), while the symbol
spells them `CS#`, `RAS#`, `CAS#`, `WE#` — same signals, KiCad's standard active-low
notation, confirmed by Winbond's own "Row Address Strobe" / "Column Address Strobe" /
"Write Enable" / "Chip Select" function descriptions in Section 5. Not a naming error.

Symbol generated: `symbols/dual_adc_usb.kicad_sym:W9825G6KH-6I` (54 pins, EXACT).

| Spec | Value |
|------|-------|
| Package | TSOP-II-54, 10.2mm |
| Vcc / Vin range | 3.0–3.6 V |
| Key output spec | 166 MHz clock, 256 Mbit (16M×16 organization implied by DQ0-15) |
| Max current / power | 80 mA active, 2 mA refresh |
| Operating temp | −40°C to +85°C |

## Pinout (54-pin TSOP-II — VERIFIED against Winbond datasheet Rev A03, §4, p.3)
| Pin | Name | Pin | Name | Pin | Name |
|---|---|---|---|---|---|
| 1 | VDD | 19 | CS# | 37 | CKE |
| 2 | DQ0 | 20 | BS0 | 38 | CLK |
| 3 | VDDQ | 21 | BS1 | 39 | UDQM |
| 4 | DQ1 | 22 | A10/AP | 40 | NC |
| 5 | DQ2 | 23 | A0 | 41 | VSS |
| 6 | VSSQ | 24 | A1 | 42 | DQ8 |
| 7 | DQ3 | 25 | A2 | 43 | VDDQ |
| 8 | DQ4 | 26 | A3 | 44 | DQ9 |
| 9 | VDDQ | 27 | VDD | 45 | DQ10 |
| 10 | DQ5 | 28 | VSS | 46 | VSSQ |
| 11 | DQ6 | 29 | A4 | 47 | DQ11 |
| 12 | VSSQ | 30 | A5 | 48 | DQ12 |
| 13 | DQ7 | 31 | A6 | 49 | VDDQ |
| 14 | VDD | 32 | A7 | 50 | DQ13 |
| 15 | LDQM | 33 | A8 | 51 | DQ14 |
| 16 | WE# | 34 | A9 | 52 | VSSQ |
| 17 | CAS# | 35 | A11 | 53 | DQ15 |
| 18 | RAS# | 36 | A12 | 54 | VSS |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| 54-pin pinout (number + name, all pins) | Matches `symbols/dual_adc_usb.kicad_sym:W9825G6KH-6I` exactly, pin-for-pin | Winbond datasheet Rev A03, §4 "Pin Configuration" p.3 + §5 "Pin Description" p.4 — **verified** |
| Vcc range | 3.0–3.6 V (VDD, VDDQ) | Winbond datasheet Rev A03 — consistent with prior MCP-sourced value, not re-verified this pass against the electrical table page number |

## Notes
- Full CSV backing the symbol: `datasheets/sdram_kipart.csv`.
- A10/AP (pin 22) is dual-purpose: row address bit 10 / auto-precharge select during
  READ/WRITE commands — standard SDRAM behavior, not a strapping pin. Confirmed in
  Winbond datasheet §5: "A10 is sampled during a precharge command to determine if all
  banks are to be precharged or bank selected by BS0, BS1."
- Pin 40 = NC — leave unconnected. Confirmed in Winbond datasheet §5 ("No Connection").
