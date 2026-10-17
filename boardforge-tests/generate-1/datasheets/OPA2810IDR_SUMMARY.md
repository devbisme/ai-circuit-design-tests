# OPA2810IDR - Dual 27 V RRIO FET-input op amp, GBW 70 MHz

Texas Instruments, datasheet OPA2810IDR.pdf, quality 90

Package: SOIC-8 (D), 8 pins, pitch 1.27 mm, thermal pad False

## Absolute maximum (min / typ / max)

- VS_max: - / - / 28 V (Total bipolar supply (±14 V)) p2
- VIN_diff: -7 / - / 7 V p2
- TJ_max: - / - / 150 °C p2
- Tstg: -65 / - / 125 °C p2

## Recommended operating (min / typ / max)

- VS: 4.75 / - / 27 V (Total supply) p2
- TA: -40 / 25 / 125 °C p2

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1 | VO1 | output |  | Amplifier 1 output |
| 2 | VIN1- | input |  | Amplifier 1 inverting input |
| 3 | VIN1+ | input |  | Amplifier 1 noninverting input |
| 4 | VS- | power_in | VS | Negative power supply |
| 5 | VIN2+ | input |  | Amplifier 2 noninverting input |
| 6 | VIN2- | input |  | Amplifier 2 inverting input |
| 7 | VO2 | output |  | Amplifier 2 output |
| 8 | VS+ | power_in | VS | Positive power supply |

## opamp

- opamp_topology: rail_to_rail_io
- channels: 2
- vsupply_range: 4.75 / - / 27 V (Total supply VS+ - VS-) p2
- vsupply_split_capable: True
- iq_per_amp: - / 0.0036 / - A p1
- gbw: - / 7e+07 / - Hz (G = 11, Vo = 20 mVpp, VS = ±5 V) p2
- slew_rate: - / 1.92e+08 / - V/s (G = 2, -2 V to 2 V step) p2
- vos: - / - / 0.0015 V p1
- ib: - / 2e-12 / - A p1
- unity_gain_stable: True

