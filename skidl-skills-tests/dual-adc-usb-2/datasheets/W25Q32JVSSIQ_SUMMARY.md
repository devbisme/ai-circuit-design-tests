# W25Q32JVSSIQ — 32 Mbit SPI NOR flash (SOIC-8)

SOURCE: model knowledge (Winbond W25Q32JV, common FPGA config flash). PDF not downloaded
this session (deferred). Pin table below is read directly from the installed KiCad
symbol `Memory_Flash:W25Q32JVSS`, confirmed present in
`/usr/share/kicad/symbols/Memory_Flash.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | SOIC-8 |
| Density | 32 Mbit (4 MB) — exceeds the "≥1 Mbit" architecture requirement with margin |
| Supply | 2.7 V–3.6 V (3.3 V in this design) |
| Interface | Standard/Dual/Quad SPI (this design uses standard single-SPI mode with the iCE40) |

## Pinout (from KiCad symbol `Memory_Flash:W25Q32JVSS`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | ~{CS} | input | Chip select, active LOW |
| 2 | DO/IO1 | bidir | Data out (standard SPI) / IO1 (quad mode) |
| 3 | ~{WP}/IO2 | bidir | Write protect (standard SPI, active LOW) / IO2 (quad mode) — **tie HIGH (VCC) via pull-up when using single-SPI mode** |
| 4 | GND | power in | Ground |
| 5 | DI/IO0 | bidir | Data in (standard SPI) / IO0 (quad mode) |
| 6 | CLK | input | Serial clock |
| 7 | ~{HOLD}/~{RESET}/IO3 | bidir | Hold (standard SPI, active LOW) / IO3 (quad mode) — **tie HIGH (VCC) via pull-up when using single-SPI mode** |
| 8 | VCC | power in | Supply, 3.3 V |

## Notes

- U18 in `fpga_core`: connects to the iCE40's dedicated SPI configuration bus for
  FPGA-as-SPI-master boot (see `iCE40HX4K-TQ144` summary): CLK↔SCK (iCE40 pin 70),
  DI↔iCE40 SDO (pin 67, FPGA drives flash's DI), DO↔iCE40 SDI (pin 68, flash drives
  FPGA's SDI), ~{CS}↔iCE40 SS (pin 71, pulled up by R24 per sourced BOM so the flash
  stays deselected during FPGA reset/reconfiguration).
- **~{WP} (pin 3) and ~{HOLD} (pin 7) must be pulled HIGH** (to VCC) since this design
  uses standard single-SPI, not quad mode — leaving them floating risks spurious
  write-protect or hold assertion. This is not itemized as a separate resistor in the
  sourced BOM's `fpga_core` passives list — **flag for the coder:** add 2× pull-ups (or
  tie directly to VCC if no quad-mode future-proofing is wanted) during coding.
- Decoupling: shares the fpga_core block's C47–C58 (100 nF ×12) and bulk cap groups.
