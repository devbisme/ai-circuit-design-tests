# FT232HL — USB 2.0 Hi-Speed to FT245-style synchronous FIFO / UART bridge (LQFP-48)

SOURCE: model knowledge (FTDI FT232H, very well-documented USB bridge IC) + the
installed KiCad symbol `Interface_USB:FT232H`, confirmed present in
`/usr/share/kicad/symbols/Interface_USB.kicad_sym` — **full 48-pin table extracted
directly from the symbol below, this is the authoritative pin list for the coder.** PDF
not downloaded this session (ftdichip.com returned HTTP 403 to automated fetch —
bot-blocked; deferred).

| Spec | Value |
|------|-------|
| Package | LQFP-48, no exposed pad (matches "FT232HL" suffix — the exposed-pad variant is "FT232HQ") |
| Function | USB 2.0 Hi-Speed device controller, configurable as async/sync FIFO (FT245 mode), UART, or MPSSE |
| Core supply | Internal regulator generates VCCCORE (1.8 V) and VCCA (1.8 V PHY analog) from VREGIN |
| I/O supply (VCCIO) | 3.3 V in this design (drives ADBUS/ACBUS logic levels) |
| USB PHY supply | VPHY, internally regulated — decouple + isolate with ferrite (FB4/FB5 per sourced BOM) |

## Pinout (full 48 pins, from KiCad symbol `Interface_USB:FT232H`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | XCSI | input | Crystal osc input (unused if driven by ext. clock — this design uses crystal Y1) |
| 2 | XCSO | output | Crystal osc output |
| 3 | VPHY | power in | USB PHY analog supply (internally regulated node — decouple) |
| 4 | AGND | power in | Analog ground |
| 5 | REF | input | Bandgap reference set — **requires 12.0 kΩ ±1% to GND (R13), `[FIXED]` mandatory, board will not enumerate without it** |
| 6 | DM | bidir | USB D− |
| 7 | DP | bidir | USB D+ |
| 8 | VPLL | power in | Internal PLL supply (regulated node — decouple) |
| 9 | AGND | power in | Analog ground |
| 10 | GND | power in | Digital ground |
| 11 | GND | power in | Digital ground |
| 12 | VCCIO | power in | I/O supply, 3.3 V |
| 13 | ADBUS0 | bidir | FIFO/UART data/control bus 0 |
| 14 | ADBUS1 | bidir | FIFO/UART data/control bus 1 |
| 15 | ADBUS2 | bidir | FIFO/UART data/control bus 2 |
| 16 | ADBUS3 | bidir | FIFO/UART data/control bus 3 |
| 17 | ADBUS4 | bidir | FIFO/UART data/control bus 4 |
| 18 | ADBUS5 | bidir | FIFO/UART data/control bus 5 |
| 19 | ADBUS6 | bidir | FIFO/UART data/control bus 6 |
| 20 | ADBUS7 | bidir | FIFO/UART data/control bus 7 |
| 21 | ACBUS0 | bidir | Control bus 0 |
| 22 | GND | power in | Digital ground |
| 23 | GND | power in | Digital ground |
| 24 | VCCIO | power in | I/O supply, 3.3 V |
| 25 | ACBUS1 | bidir | Control bus 1 |
| 26 | ACBUS2 | bidir | Control bus 2 |
| 27 | ACBUS3 | bidir | Control bus 3 |
| 28 | ACBUS4 | bidir | Control bus 4 |
| 29 | ACBUS5 | bidir | Control bus 5 |
| 30 | ACBUS6 | bidir | Control bus 6 |
| 31 | ACBUS7 | bidir | Control bus 7 |
| 32 | ACBUS8 | bidir | Control bus 8 |
| 33 | ACBUS9 | bidir | Control bus 9 — **`[CRIT]` must be EEPROM-configured as PWREN# for this design** (per sourced BOM) |
| 34 | ~{RESET} | input | Reset, active LOW — **needs pull-up, R16 (10 kΩ)** |
| 35 | GND | power in | Digital ground |
| 36 | GND | power in | Digital ground |
| 37 | VCCA | power out | Internal 1.8 V analog regulator output — decouple, do NOT drive externally |
| 38 | VCCCORE | power out | Internal 1.8 V core regulator output — decouple, do NOT drive externally |
| 39 | VCCD | power in | Digital core supply input |
| 40 | VREGIN | power in | Internal regulator input — tie to VCCIO (3.3 V) per FTDI reference design |
| 41 | AGND | power in | Analog ground |
| 42 | TEST | input | Factory test — **tie to GND for normal operation** |
| 43 | EEDATA | bidir | EEPROM data — shared with 93LC46B DI/DO |
| 44 | EECLK | input | EEPROM clock — shared with 93LC46B SCLK |
| 45 | EECS | input | EEPROM chip select — shared with 93LC46B CS |
| 46 | VCCIO | power in | I/O supply, 3.3 V |
| 47 | GND | power in | Digital ground |
| 48 | GND | power in | Digital ground |

## Notes

- U6 in `usb_bridge`. Y1 (12 MHz crystal) across pins 1/2 (XCSI/XCSO) with C25/C26 load
  caps.
- **R13 (12.0 kΩ ±1%) on REF (pin 5) is mandatory** — omitting it prevents USB
  enumeration entirely (`[FIXED]` per sourcing).
- **ACBUS9 (pin 33) must be configured via the 93LC46B EEPROM (U7) as PWREN#** output —
  this is firmware/EEPROM-image configuration, not a schematic-only concern, but the
  schematic must still route ACBUS9 to wherever PWREN# is consumed (per architecture,
  likely gating Q1/power_analog enable).
- TEST (pin 42) tied to GND; RESET (pin 34) needs R16 pull-up.
- VREGIN (pin 40) → tie to VCCIO (3.3 V rail); VCCA/VCCCORE (pins 37/38) are regulator
  **outputs** — decouple locally (C35/C36, 1 µF per sourced BOM) but never drive them.
- VPHY/VPLL (pins 3/8) are internally-regulated nodes needing their own decoupling; FB4/
  FB5 ferrite beads isolate them per FTDI reference design (per sourced BOM note).
- EEDATA/EECLK/EECS (pins 43–45) wire directly to U7 (93LC46B)'s DI/DO (shared,
  half-duplex on this symbol's single EEDATA line — the 93LC46B's separate DI/DO pins
  should both tie to this one EEDATA net, per the standard FTDI EEPROM interface, with
  R17 pull-up on the shared line as sourced), SCLK, and CS respectively.
- Full 48-pin decoupling: C27–C34 (100 nF ×8, one per VCCIO/VCCD/etc. supply pin) + C35/
  C36 (1 µF, VCCA/VCCCORE) + C37/C38 (4.7 µF bulk) + C39 (10 µF bulk) + C40 (100 nF) per
  sourced BOM.
