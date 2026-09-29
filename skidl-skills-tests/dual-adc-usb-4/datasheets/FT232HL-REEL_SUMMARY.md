# FT232HL-REEL — USB 2.0 Hi-Speed to UART/FIFO/JTAG/SPI/I2C Bridge (U13)

| Spec | Value |
|------|-------|
| Package | LQFP-48 (7x7mm, 0.5mm pitch) |
| Vcc / Vin range | VCCIO 1.62-1.98V or 2.97-3.63V (selectable); VREGIN for internal 1.8V/3.3V LDO |
| Key output spec | USB 2.0 Hi-Speed (480Mbps), configurable UART/FIFO/JTAG/SPI/I2C via MPSSE |
| Max current / power | 70mA active, 10µA quiescent (suspend) |
| Operating temp | -40°C to +85°C |

## Pinout (48 pins, JLC/EasyEDA data)
| Pin | Name | Pin | Name | Pin | Name | Pin | Name |
|---|---|---|---|---|---|---|---|
| 1 | XCSI | 13 | ADBUS0 | 25 | ACBUS1 | 37 | VCCA |
| 2 | XCSO | 14 | ADBUS1 | 26 | ACBUS2 | 38 | VCORE |
| 3 | VPHY | 15 | ADBUS2 | 27 | ACBUS3 | 39 | VCCD |
| 4 | AGND | 16 | ADBUS3 | 28 | ACBUS4 | 40 | VREGIN |
| 5 | REF | 17 | ADBUS4 | 29 | ACBUS5 | 41 | AGND |
| 6 | DM | 18 | ADBUS5 | 30 | ACBUS6 | 42 | TEST |
| 7 | DP | 19 | ADBUS6 | 31 | ACBUS7 | 43 | EEDATA |
| 8 | VPLL | 20 | ADBUS7 | 32 | ACBUS8 | 44 | EECLK |
| 9 | AGND | 21 | ACBUS0 | 33 | ACBUS9 | 45 | EECS |
| 10 | GND | 22 | GND | 34 | RESET# | 46 | VCCIO |
| 11 | GND | 23 | GND | 35 | GND | 47 | GND |
| 12 | VCCIO | 24 | VCCIO | 36 | GND | 48 | GND |

Symbol already matched: `Interface_USB:FT232H` — confirmed **CP** per sourcing, no generation
needed. This pinout table is provided for the coder's decoupling/net-assignment reference.

## Notes
- Datasheet: FTDI DS_FT232H (2024 edition), downloaded to `datasheets/FT232HL-REEL.pdf`.
- ACBUS5 (pin 29) is FT_CLKOUT source per `net_plan.md` line 109-110 (60MHz clock via R66 to
  U15 pin 52); EECS/EECLK/EEDATA (pins 45/44/43) go to U14 (93LC56BT EEPROM) per line 116.
- REF (pin 5) sets USB PHY reference current via R64=12kΩ 1% to GND per `net_plan.md` line 115
  — already resolved by architecture, no change needed.
- Decoupling: C67-C74 (0.1µF ×8) and C75-C77 (4.7µF bulk) already specified per DS_FT232H §6
  recommendations in `sourced_bom.md`.
