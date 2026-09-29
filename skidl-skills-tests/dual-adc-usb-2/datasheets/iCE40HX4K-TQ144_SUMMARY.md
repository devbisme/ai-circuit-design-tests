# iCE40HX4K-TQ144 — Lattice FPGA, 3520 LUT, TQFP-144

SOURCE: model knowledge (Lattice iCE40 HX family, well-documented open FPGA family) +
WebSearch confirmation of the CBSEL0/CBSEL1/VPP_2V5 configuration-pin facts (from
Lattice's own "iCE40 Programming and Configuration" technical note, FPGA-TN-02001) + the
installed KiCad symbol `FPGA_Lattice:ICE40HX4K-TQ144`, confirmed present in
`/usr/share/kicad/symbols/FPGA_Lattice.kicad_sym`. PDF not downloaded this session
(deferred — 144-pin full datasheet is large; the symbol supplies the full pin list
directly and is authoritative for placement).

| Spec | Value |
|------|-------|
| Package | TQFP-144, 20×20 mm, 0.5 mm pitch — `[FIXED]` per sourcing, package size driven by 107 I/O need |
| Logic | 3520 LUTs (HX4K density) |
| VCC (core) | 1.2 V |
| VCCIO (per bank, 4 banks: 0–3) | Independently settable 3.3 V/2.5 V/1.8 V/1.2 V — this design uses 3.3 V on the I/O banks that face the FT232H/EEPROM/LEDs/headers |
| VCCPLL0/VCCPLL1 | 1.2 V, filtered separately from VCC core (per sourced BOM: R26 470 Ω + C63 100 nF RC filter) |
| VPP_2V5 | 2.5 V — **must be connected even if NVCM programming is never used** (per Lattice TN-02001) |
| VPP_FAST | Programming-related; tie appropriately for non-NVCM use (see Notes — not independently confirmed this session) |

## Key functional pins (full 144-pin list is in the KiCad symbol — this table covers only
the pins this design's external wiring touches; do not re-derive the rest, pull them from
the symbol at coding time)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 63 | IOB_103_CBSEL0 | bidir | Cold-boot SPI image select bit 0 — **tie to GND for single-image boot from address 0** (the simplest/default config, matches this design's single external W25Q32 flash with one bitstream image) |
| 64 | IOB_104_CBSEL1 | bidir | Cold-boot SPI image select bit 1 — **tie to GND** (same reasoning) |
| 65 | CDONE | open-collector | Configuration-done status output — needs external pull-up (shared with D4 LED + R20 per sourced BOM) |
| 66 | ~{CRESET} | input | Configuration reset, active LOW — needs pull-up (R23, 10 kΩ per sourced BOM), route to J4 programming header |
| 67 | IOB_105_SDO | bidir | SPI master mode: FPGA's data-out to external flash → W25Q32 DI |
| 68 | IOB_106_SDI | bidir | SPI master mode: FPGA's data-in from external flash ← W25Q32 DO |
| 70 | IOB_107_SCK | bidir | SPI master mode: FPGA's clock out → W25Q32 CLK |
| 71 | IOB_108_SS | bidir | SPI master mode: FPGA's chip-select out → W25Q32 ~{CS}, needs pull-up (R24, 10 kΩ per sourced BOM, "SPI_SS pull-up") |
| 72 | VCC_SPI | power in | Dedicated SPI-interface supply — tie to 3.3 V (same rail as W25Q32 VCC) |
| 53 / 127 | GNDPLL0 / GNDPLL1 | power in | PLL ground |
| 54 / 126 | VCCPLL0 / VCCPLL1 | power in | PLL supply, 1.2 V filtered (R26/C63) |
| 108 | VPP_2V5 | power in | Must be connected to 2.5 V even without NVCM use |
| 109 | VPP_FAST | power in | Programming-related supply — tie per Lattice's non-NVCM guidance (see Notes, flagged low-confidence) |

## Notes

- U9 in `fpga_core`. This is the design's central digital hub — FT232H FIFO bus, SRAM
  address/data/control, both ADCs' data buses, and the LED/trigger/header I/O all
  terminate here. Only the *external-wiring-relevant* pins are tabulated above; **the
  coder must pull the complete 144-pin name/number list directly from the installed
  KiCad symbol** (`FPGA_Lattice:ICE40HX4K-TQ144`) for all general-purpose I/O bank
  assignments — this summary does not re-derive those.
- **CBSEL0/CBSEL1 (pins 63/64) tied to GND** selects SPI Flash Master boot from the
  lowest configuration address — this is the standard default and matches a
  single-bitstream design with no multi-image cold-boot switching. If a future revision
  wants selectable dual-image boot, these pins need controlled strapping instead.
- **VPP_FAST (pin 109):** Lattice's technical note text obtained this session did not
  state its tie-off value explicitly for non-NVCM designs — **flagged, not guessed.**
  Common practice for iCE40 designs that don't use One-Time-Programmable NVCM is to tie
  VPP_FAST to GND, but verify against the iCE40 LP/HX Family Data Sheet (DS1040) power
  supply requirements table before finalizing, since an incorrect tie on a programming
  supply pin risks either non-function or (per some Lattice notes) accidental NVCM
  programming.
- J4 (2×5 1.27 mm programming header) per sourced BOM carries SPI + CRESET_B + CDONE +
  3V3 + GND — wire directly to pins 65 (CDONE), 66 (CRESET), 67/68/70/71 (SPI bus), plus
  power/ground.
- Decoupling: C47–C58 (100 nF ×12, "≥8 on VCCIO, ≥4 on VCC core, at the pins" per sourced
  BOM) + C59/C60 (1 µF) + C61/C62 (10 µF) + C63 (100 nF, VCCPLL filter cap, paired with
  R26) + C64 (100 nF, CRESET timing cap).
