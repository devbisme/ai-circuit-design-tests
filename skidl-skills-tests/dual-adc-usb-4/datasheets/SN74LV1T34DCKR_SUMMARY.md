# SN74LV1T34DCKR — Single Buffer/Level Shifter (U17)

| Spec | Value |
|------|-------|
| Package | SC-70-5 |
| Vcc / Vin range | 1.6V – 5.5V |
| Key output spec | Single non-inverting buffer, push-pull output, level-shifting capable |
| Max current / power | 8mA IOH/IOL |
| Operating temp | -40°C to +125°C |

## Pinout (JLC/EasyEDA data)
| Pin | Name | Function |
|-----|------|----------|
| 1 | NC | No internal connection |
| 2 | A | Input |
| 3 | GND | Ground |
| 4 | Y | Output |
| 5 | VCC | Supply |

Symbol already matched (`Logic_LevelTranslator:SN74LV1T34DCK`) — confirmed per sourcing, no
generation needed.

## Notes
- Datasheet: downloaded to `datasheets/SN74LV1T34DCKR.pdf` (TI).
- Buffers EXT_TRIG_IN per `net_plan.md` line 151 (R84 1kΩ → U17.A, R85 100kΩ pull-down at the
  header) — standard single-supply level-shift buffer usage.
