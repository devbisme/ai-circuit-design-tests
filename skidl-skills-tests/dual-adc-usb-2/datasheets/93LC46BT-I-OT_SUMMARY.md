# 93LC46BT-I/OT — 1 Kbit Microwire config EEPROM (SOT-23-6)

SOURCE: model knowledge (Microchip 93LC46B, standard FTDI companion EEPROM). PDF not
downloaded this session (deferred). Pin table below is read directly from the installed
KiCad symbol `Memory_EEPROM:93CxxC` (noted "pin-compatible" by sourcing), confirmed
present in `/usr/share/kicad/symbols/Memory_EEPROM.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Density | 1 Kbit (64×16 or 128×8, selectable via ORG pin) |
| Interface | Microwire (CS/SCLK/DI/DO) |
| Supply | 1.8 V–5.5 V class (93LC46B "-I" industrial grade); this design runs it at 3.3 V from VCCIO |

## Pinout (from KiCad symbol `Memory_EEPROM:93CxxC`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | CS | input | Chip select |
| 2 | SCLK | input | Serial clock |
| 3 | DI | input | Serial data in |
| 4 | DO | tri-state | Serial data out |
| 5 | GND | power in | Ground |
| 6 | ORG | input | Organization select: tie to VCC for ×16 (128×16-bit-equivalent... actually 64×16 for 1 Kbit), tie to GND for ×8 |
| 7 | NC | no connect | Not internally connected |
| 8 | VCC | power in | Supply, 3.3 V |

## Notes

- U7 in `usb_bridge`: DI and DO both tie to the FT232H's single shared EEDATA net (pin
  43) per the standard FTDI Microwire interface — **DI and DO are physically separate
  pins on this part but logically share one wire on the FT232H side; R17 (2.2 kΩ pull-up)
  goes on that shared EEDATA/DO line** per sourced BOM ("EEPROM DO pull-up").
- CS (pin 1) → FT232H EECS (pin 45). SCLK (pin 2) → FT232H EECLK (pin 44).
- **ORG (pin 6):** tie to VCC for ×16 organization — this is the FTDI-recommended
  configuration (16-bit word EEPROM image matches FT232H's EEPROM programming utility
  expectations). Do not leave floating.
- Decoupling: shares the usb_bridge block's C27–C34 (100 nF) per-pin decoupling group.
