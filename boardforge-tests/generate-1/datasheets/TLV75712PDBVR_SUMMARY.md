# TLV75712PDBVR - 1 A low-IQ LDO, 1.2 V fixed, active discharge (P)

Texas Instruments, datasheet TLV75712PDBVR.pdf, quality 84

Package: SOT-23-5 (DBV), 5 pins, pitch 0.95 mm, thermal pad False

## Absolute maximum (min / typ / max)

- VIN_max: -0.3 / - / 6 V p4
- VEN_max: -0.3 / - / 6 V p4
- TJ_max: - / - / 150 °C p4

## Recommended operating (min / typ / max)

- VIN: 1.45 / - / 5.5 V p4
- TJ: -40 / - / 125 °C p4

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1 | IN | power_in | VIN | Input; >= 1 uF |
| 2 | GND | power_in |  | Ground |
| 3 | EN | input |  | Enable; drive > VHI to turn on (no internal pull stated) |
| 4 | NC | not_connected |  | No internal connection |
| 5 | OUT | power_out |  | Output; >= 1 uF |

## regulator

- topology: ldo
- vin_range: 1.45 / - / 5.5 V p4
- vout_range: - / 1.2 / - V (xx = 12) p22
- iout_max: - / - / 1 A p4
- enable_pin: 3
- cin_min: 1e-06 / - / - F p4
- cout_min: 1e-06 / - / 0.0002 F p4
- dropout: - / 1 / 1.1 V (1.2 V <= VOUT < 1.5 V, IOUT = 1 A, DBV) p5

