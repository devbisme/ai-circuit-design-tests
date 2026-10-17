# USBLC6-2SC6 - Very-low-capacitance ESD protection for USB 2.0 (2 lines + VBUS)

STMicroelectronics, datasheet USBLC6-2SC6.pdf, quality 78

Package: SOT23-6L, 6 pins, pitch 0.95 mm, thermal pad False

## Absolute maximum (min / typ / max)

- Tj_max: - / - / 125 °C p2

## Recommended operating (min / typ / max)

- VBUS: - / - / 5.25 V (VRM, leakage specified) p2

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1,6 | I/O1 | passive |  | Protected line 1 (pins 1 and 6 internally connected, flow-through) |
| 2 | GND | power_in |  | Ground |
| 3,4 | I/O2 | passive |  | Protected line 2 (pins 3 and 4 internally connected) |
| 5 | VBUS | power_in | VBUS | VBUS rail (TVS reference) |

## diode

- diode_type: tvs
- breakdown_voltage: 6 / - / - V (VBUS-GND, IR = 1 mA) p2
- ir: - / 1e-08 / 1.5e-07 A (VRM = 5.25 V) p2
- cd: - / 2.5e-12 / 3.5e-12 F (I/O to GND, VR = 1.65 V) p2

