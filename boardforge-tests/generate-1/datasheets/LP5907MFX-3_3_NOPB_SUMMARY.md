# LP5907MFX-3.3/NOPB - 250 mA ultra-low-noise LDO, 3.3 V fixed

Texas Instruments, datasheet LP5907MFX-3_3_NOPB.pdf, quality 85

Package: SOT-23-5 (DBV), 5 pins, pitch 0.95 mm, thermal pad False

## Absolute maximum (min / typ / max)

- VIN_max: -0.3 / - / 6 V p2
- VEN_max: -0.3 / - / 6 V p2

## Recommended operating (min / typ / max)

- VIN: 2.2 / - / 5.5 V p4
- TA: -40 / - / 85 °C p4

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1 | IN | power_in | VIN | Input; 1 uF |
| 2 | GND | power_in |  | Ground |
| 3 | EN | input |  | Enable; internal 1 Mohm pulldown; low = off + 230 ohm output discharge |
| 4 | N/C | not_connected |  | No internal connection |
| 5 | OUT | power_out |  | Output; min 1 uF low-ESR |

## regulator

- topology: ldo
- vin_range: 2.2 / - / 5.5 V p4
- vout_range: - / 3.3 / - V (fixed) p1
- iout_max: - / - / 0.25 A p4
- enable_pin: 3
- cout_min: 7e-07 / 1e-06 / 1e-05 F (effective output capacitance; ESR 5-500 mohm) p6

