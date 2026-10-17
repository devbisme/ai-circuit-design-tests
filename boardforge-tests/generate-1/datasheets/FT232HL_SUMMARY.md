# FT232HL - Hi-Speed USB to UART/FIFO (FT232H, LQFP-48)

FTDI, datasheet FT232HL.pdf, quality 55

Package: LQFP-48 7x7 mm, 48 pins, pitch 0.5 mm, thermal pad False

## Absolute maximum (min / typ / max)

- VCCIO_max: -0.3 / - / 4 V p6
- VCORE_max: -0.3 / - / 2 V p6
- VUSB_IO: -0.5 / - / 3.63 V (USBDP/USBDM) p6
- VIO_5V: -0.3 / - / 5.8 V (ACBUS/ADBUS inputs) p6

## Recommended operating (min / typ / max)

- VCCIO: 2.97 / - / 3.63 V p40
- VREGIN: 3.3 / 3.3 / 3.6 V (3.3 V input mode (5 V mode: 3.6-5.5 V)) p40
- TA: -40 / - / 85 °C p6

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1 | OSCI | input |  | Oscillator input (KiCad symbol: XCSI) |
| 2 | OSCO | output |  | Oscillator output (KiCad symbol: XCSO) |
| 3 | VPHY | power_in | VCCIO | +3.3 V USB PHY supply; must come from a 3.3 V regulator; LC filter recommended |
| 4,9,41 | AGND | power_in |  | Analog ground |
| 5 | REF | input |  | Current reference: 12 kohm 1 % to GND |
| 6 | DM | bidirectional |  | USB D- |
| 7 | DP | bidirectional |  | USB D+ |
| 8 | VPLL | power_in | VCCIO | +3.3 V PLL supply; LC filter recommended |
| 10,11,22,23,35,36,47,48 | GND | power_in |  | Ground |
| 12,24,46 | VCCIO | power_in | VCCIO | +3.3 V I/O supply; all three must be connected |
| 31 | ACBUS7 | bidirectional |  | ACBUS7 / PWRSAV# (EEPROM option "suspend on ACBUS7 low"); default GPIO with 75k pull-down |
| 34 | RESET# | input |  | Active-low reset (KiCad symbol: ~{RESET}) |
| 37 | VCCA | power_out |  | +1.8 V internal regulator output; terminate with 0.1 uF to GND only |
| 38 | VCORE | power_out |  | +1.8 V core regulator output; terminate with 0.1 uF to GND only (KiCad symbol: VCCCORE) |
| 39 | VCCD | power_in | VCCIO | +3.3 V: input when VREGIN = 3.3 V (output when VREGIN = 5 V) |
| 40 | VREGIN | power_in | VREGIN | Regulator input: +5 V or +3.3 V |
| 42 | TEST | input |  | Test pin: connect to GND |
| 43 | EEDATA | bidirectional |  | EEPROM data: to EEPROM DI directly, to DO via 2.2k; DO pulled to VCCD with 10k |
| 44 | EECLK | output |  | EEPROM clock |
| 45 | EECS | bidirectional |  | EEPROM chip select |
| 13 | ADBUS0 | bidirectional |  | ADBUS0; sync 245 FIFO D0 |
| 14 | ADBUS1 | bidirectional |  | ADBUS1; sync 245 FIFO D1 |
| 15 | ADBUS2 | bidirectional |  | ADBUS2; sync 245 FIFO D2 |
| 16 | ADBUS3 | bidirectional |  | ADBUS3; sync 245 FIFO D3 |
| 17 | ADBUS4 | bidirectional |  | ADBUS4; sync 245 FIFO D4 |
| 18 | ADBUS5 | bidirectional |  | ADBUS5; sync 245 FIFO D5 |
| 19 | ADBUS6 | bidirectional |  | ADBUS6; sync 245 FIFO D6 |
| 20 | ADBUS7 | bidirectional |  | ADBUS7; sync 245 FIFO D7 |
| 21 | ACBUS0 | bidirectional |  | ACBUS0; sync 245 FIFO: RXF# |
| 25 | ACBUS1 | bidirectional |  | ACBUS1; sync 245 FIFO: TXE# |
| 26 | ACBUS2 | bidirectional |  | ACBUS2; sync 245 FIFO: RD# |
| 27 | ACBUS3 | bidirectional |  | ACBUS3; sync 245 FIFO: WR# |
| 28 | ACBUS4 | bidirectional |  | ACBUS4; sync 245 FIFO: SIWU# |
| 29 | ACBUS5 | bidirectional |  | ACBUS5; sync 245 FIFO: CLKOUT |
| 30 | ACBUS6 | bidirectional |  | ACBUS6; sync 245 FIFO: OE# |
| 32 | ACBUS8 | bidirectional |  | ACBUS8; sync 245 FIFO: GPIO |
| 33 | ACBUS9 | bidirectional |  | ACBUS9; sync 245 FIFO: GPIO |

