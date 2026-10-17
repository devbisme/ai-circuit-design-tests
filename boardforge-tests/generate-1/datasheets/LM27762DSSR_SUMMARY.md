# LM27762DSSR - Low-noise positive and negative output (+/-1.5..5 V, 250 mA) charge pump + LDOs

Texas Instruments, datasheet LM27762DSSR.pdf, quality 91

Package: WSON-12 (DSS) 2x3 mm, EP 1.0x2.65 mm (pad 13), 13 pins, pitch 0.5 mm, thermal pad True

## Absolute maximum (min / typ / max)

- VIN_max: - / - / 5.8 V p2
- TJ_max: - / - / 150 °C p2

## Recommended operating (min / typ / max)

- VIN: 2.7 / - / 5.5 V p2
- TA: -40 / - / 85 °C p2

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1 | PGOOD | open_collector |  | Power good, open drain; 0 = good; connect to GND if unused |
| 2 | FB+ | input |  | Positive LDO feedback; divider OUT+ to GND; never leave open |
| 3 | VIN | power_in | VIN | Positive supply input |
| 4 | GND | power_in |  | Ground |
| 5 | CP | power_out |  | Unregulated negative charge-pump output (needs CPOUT cap) |
| 6 | OUT- | power_out |  | Regulated negative output |
| 7 | FB- | input |  | Negative LDO feedback; divider OUT- to GND; never leave open |
| 8 | EN- | input |  | Enable charge pump + negative LDO, active high |
| 9 | C1- | passive |  | Flying cap negative terminal (KiCad symbol: C-) |
| 10 | C1+ | passive |  | Flying cap positive terminal (KiCad symbol: C+) |
| 11 | OUT+ | power_out |  | Regulated positive output |
| 12 | EN+ | input |  | Enable positive LDO, active high |
| 13 | EP | power_in |  | Thermal pad = ground; do not leave unconnected (KiCad symbol: PAD) |

## regulator

- topology: charge_pump
- vin_range: 2.7 / - / 5.5 V p2
- vout_range: 1.5 / - / 5 V (OUT+ adjustable) p2
- iout_max: - / - / 0.25 A (each output) p2
- reference_voltage: 1.182 / 1.2 / 1.218 V (VFB+) p2
- feedback_pin: 2
- enable_pin: 12
- power_good_pin: 1
- switching_freq: 1.7e+06 / 2e+06 / 2.3e+06 Hz (VIN = 3.6 V) p2
- cout_min: - / 2.2e-06 / - F (test condition CIN = COUT+ = COUT- = 2.2 uF, C1 = 1 uF, CPOUT = 4.7 uF) p2

