# SN74LV4T125PWR — Quadruple Buffer/Level-Translator with 3-State Outputs (U16)

| Spec | Value |
|------|-------|
| Package | TSSOP-14 |
| Vcc / Vin range | 1.6V – 5.5V |
| Key output spec | 4× independent buffers, tri-state via OE#, level-shifting capable |
| Max current / power | 16mA IOH/IOL |
| Operating temp | -40°C to +125°C |

## Pinout (JLC/EasyEDA data)
| Pin | Name | Function |
|-----|------|----------|
| 1 | 1OE# | Buffer 1 output enable, active low |
| 2 | 1A | Buffer 1 input |
| 3 | 1Y | Buffer 1 output |
| 4 | 2OE# | Buffer 2 output enable, active low |
| 5 | 2A | Buffer 2 input |
| 6 | 2Y | Buffer 2 output |
| 7 | GND | Ground |
| 8 | 3Y | Buffer 3 output |
| 9 | 3A | Buffer 3 input |
| 10 | 3OE# | Buffer 3 output enable, active low |
| 11 | 4Y | Buffer 4 output |
| 12 | 4A | Buffer 4 input |
| 13 | 4OE# | Buffer 4 output enable, active low |
| 14 | VCC | Supply |

Symbol already matched (`74xx:SN74LV4T125`) — confirmed per sourcing, no generation needed.

## Notes
- Datasheet: downloaded to `datasheets/SN74LV4T125PWR.pdf` (TI).
- Drives LED_STAT/LED_ACT/EXT_TRIG_OUT/EXT_GPIO_OUT per `net_plan.md` lines 148-150 — standard
  single-supply buffer usage, OE# pins presumably tied low (always-enabled) per architecture;
  confirm in coding phase.
