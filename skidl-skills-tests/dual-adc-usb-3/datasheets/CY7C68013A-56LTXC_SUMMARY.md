# CY7C68013A-56LTXC — EZ-USB FX2LP USB 2.0 Peripheral Controller (56-pin QFN)

Source: `datasheets/CY7C68013A-56LTXC.pdf` / `.txt` (Cypress datasheet, doc 38-08032 Rev. AD,
full document, already extracted from the prior run). Package used: **56-pin QFN**
(Figure 10), not the SSOP or TQFP variants also in this datasheet — verified by exact
`-56LTXC` ordering suffix (line ~4124, "CY7C68013A-56LTXC 56 QFN – Pb-free").

| Spec | Value |
|------|-------|
| Package | 56-pin QFN, thermal pad on underside (solder to PCB thermal/ground pad per app note text — no exact EP mm dimension found in this document; sourced footprint `Cypress_QFN-56-1EP_8x8mm_P0.5mm_EP6.22x6.22mm` is vendor-named specifically for this Cypress part family, high confidence, not flagged for re-verification by sourcing) |
| Vcc / Vin range | VCC digital 3.3V (typical USB peripheral supply — architecture's `+3V3_AON`), AVCC analog 3.3V, separate AGND/GND |
| Key output spec | 8051-based, 8/16-bit slave FIFO interface up to 96 MB/s (16-bit) / 48 MB/s (8-bit, this design's mode) at 48 MHz IFCLK |
| Max current / power | Not extracted (not decoupling-critical beyond standard practice below) |
| Operating temp | 0°C to 70°C (commercial grade, matches architecture's X5 requirement) |

## Pinout (56-pin QFN, Figure 10 — only pins relevant to this design's 8-bit slave FIFO mode
and fixed functions; full 56-pin figure is in the PDF/txt if others are needed)

| Pin | Name (silkscreen) | Function used in this design |
|-----|------|----------|
| 1 | RDY0/*SLRD | **SLRD_N** (slave FIFO read strobe, alt function selected via IFCONFIG) |
| 2 | RDY1/*SLWR | **SLWR_N** (slave FIFO write strobe) |
| 3, 7, 14 | AVCC | Analog VCC — decouple locally |
| 4 | XTALOUT | 24 MHz crystal (Y2, X322524MOB4SI) |
| 5 | XTALIN | 24 MHz crystal |
| 6, 10, 17 | AGND | Analog ground |
| 8 | DPLUS | USB D+ |
| 9 | DMINUS | USB D– |
| 11, 18, 24, 32, 34, 43, 55 | VCC | Digital VCC (+3V3_AON) |
| 12, 19, 33, 41, 44, 53, 56 | GND | Digital ground |
| 13 | *IFCLK/**PE0 | **IFCLK** (interface clock — internal or external per IFCONFIG; architecture treats this as an FX2LP output/interface clock, not fed from `clock_gen`) |
| 15 | SCL | I²C clock — to CAT24C128 EEPROM (U14) |
| 16 | SDA | I²C data — to CAT24C128 EEPROM (U14), needs external pull-ups (architecture's 2.2kΩ I²C pull-ups, already sourced) |
| 21 | RESERVED | Leave per datasheet guidance (do not treat as GPIO) |
| 25–28, 29–32 (mixed order) | PB0–PB7 / FD0–FD7 | **FD[7:0]** — the 8-bit slave FIFO data bus to the FPGA (PB0=FD0 pin25 ... PB7=FD7 pin32) |
| 29 | CTL0/*FLAGA | **FLAGA** |
| 30 | CTL1/*FLAGB | **FLAGB** |
| 31 | CTL2/*FLAGC | **FLAGC** |
| 36 | PA3/*WU2 | **FPGA_RST_N** (architecture: FX2LP PA3 → FPGA RECONFIG_N, `02_architecture.md` Carried forward I11) |
| 37 | PA4/FIFOADR0 | **FIFOADR0** |
| 38 | PA5/FIFOADR1 | **FIFOADR1** |
| 39 | PA6/*PKTEND | **PKTEND_N** |
| 40 | PA7/*FLAGD/SLCS# | Not used in this design (FLAGD/SLCS# unused signal) — leave as GPIO or NC per IFCONFIG default |
| 35 | PA2/*SLOE | **SLOE_N** |
| 42 | RESET# | FX2LP's **own** hardware reset — active low, needs external RC per datasheet timing (`TRESET` ≥ ~5ms after VCC ≥ 3.0V with crystal). Architecture's "FX2LP reset cap" + 100kΩ resistor (sourced BOM) implements this. **Do not confuse with `FPGA_RST_N`** (pin 36, PA3) which FX2LP drives *outward* to the FPGA — these are two different signals in two different directions. |
| PD0–PD7 (pins 45,46,48,49,50,51,52,54) | FD8–FD15 | **Not used** — 16-bit mode only; this design is 8-bit (architecture Decision 3). These pins are free GPIO/unused in 8-bit FIFO mode; tie or leave per Cypress's unused-pin guidance (float is acceptable for these in 8-bit mode per common FX2LP practice — datasheet does not mandate tie-off for unused Port D pins). |
| 20 | *WAKEUP | Not used — leave per datasheet default (internal pull handling exists; no explicit external requirement extracted) |

## Notes

- **8-bit slave FIFO signal map above is the authoritative pin-to-net assignment** for the
  `usb_controller` block's SKiDL pins — use exactly these pin names (`RDY0/*SLRD` etc. are the
  datasheet's own dual-function labels; SKiDL/KiCad symbol pin names may render these
  slightly differently — check the actual KiCad symbol's pin-name strings against this table
  before wiring, since a renamed pin silently fails per this project's rules).
  `*` prefix on a signal in Cypress's own notation means "programmable polarity," not a
  literal pin-name character.
- I²C EEPROM address: architecture fixed CAT24C128 at 0xA2 (I9) — SCL/SDA (pins 15/16) already
  have the 2.2kΩ pull-ups in the general passives table.
- Crystal: 24.000 MHz, CL 12pF, ±100ppm is an **FX2LP hard requirement** (per
  `02_architecture.md` Next phase must #4) — already the exact spec of the sourced
  X322524MOB4SI (12pF load caps sourced too).
- RESET# (pin 42) vs FPGA_RST_N (pin 36, PA3, FX2LP-driven output to FPGA) are unrelated
  signals with similar names — a likely SKiDL naming-collision trap. Name them distinctly in
  code (e.g. `usb_reset_n` vs `fpga_rst_n`) to avoid net merges.
