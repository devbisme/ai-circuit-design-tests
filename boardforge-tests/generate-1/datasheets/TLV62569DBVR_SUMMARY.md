# TLV62569DBVR - 2 A 1.5 MHz synchronous step-down converter, adjustable

Texas Instruments, datasheet TLV62569DBVR.pdf, quality 87

Package: SOT-23-5 (DBV), 5 pins, pitch 0.95 mm, thermal pad False

## Absolute maximum (min / typ / max)

- VIN_max: -0.3 / - / 6 V p3
- FB_max: -0.3 / - / 5.5 V p3
- TJ_max: - / - / 150 °C p3

## Recommended operating (min / typ / max)

- VIN: 2.5 / - / 5.5 V p4
- TJ: -40 / - / 125 °C p4

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1 | EN | input |  | Enable, high = on (do not float) |
| 2 | GND | power_in |  | Ground |
| 3 | SW | power_out |  | Switch node to inductor |
| 4 | VIN | power_in | VIN | Input supply |
| 5 | FB | input |  | Feedback; divider from VOUT |

## regulator

- topology: buck
- vin_range: 2.5 / - / 5.5 V p4
- vout_range: 0.6 / - / - V (up to VIN) p4
- iout_max: - / - / 2 A p4
- reference_voltage: 0.588 / 0.6 / 0.612 V (VFB) p4
- feedback_pin: 5
- enable_pin: 1
- switching_freq: - / 1.5e+06 / - Hz (VOUT = 2.5 V) p4
- inductor_range: - / 2.2e-06 / - H (typical application) p1

