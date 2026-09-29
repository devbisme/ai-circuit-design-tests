# 93LC56BT-I/OT — 2Kbit Microwire-Compatible Serial EEPROM (U14, FT232H config EEPROM)

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Vcc / Vin range | 2.5V – 5.5V |
| Key output spec | 2Kbit (128×16 or 256×8 organization), Microwire (3-wire) interface |
| Max current / power | 2mA active, 1µA standby |
| Operating temp | -40°C to +85°C (I-grade) |

## Pinout (JLC/EasyEDA data)
| Pin | Name | Function |
|-----|------|----------|
| 1 | DO | Data output |
| 2 | VSS | Ground |
| 3 | DI | Data input |
| 4 | CLK | Serial clock |
| 5 | CS | Chip select |
| 6 | VCC | Supply |

Symbol matched via "WILDCARD family symbol" (`Memory_EEPROM:93LCxxB`) per sourcing — pinout
identical across the 93LCxxB family, confirmed consistent with this table.

## Notes
- Datasheet: Microchip 93AA56X/93LC56X/93C56X family sheet (DS20001794J), downloaded to
  `datasheets/93LC56BT-I-OT.pdf`.
- Wired per `net_plan.md` line 116: CS/CLK/DI from U13 (FT232H) EECS/EECLK/EEDATA pins with
  10kΩ pull-ups (R61-R63); DO → R60 (2.2kΩ) → FT_EEDATA (shared bidirectional data line per
  DS_FT232H's EEPROM interface note). This is the FT232H's standard external EEPROM config
  circuit — no changes needed.
