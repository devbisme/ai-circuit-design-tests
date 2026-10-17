# OPA810IDBVR - Single 27 V RRIO FET-input op amp, GBW 70 MHz

Texas Instruments, datasheet OPA810IDBVR.pdf, quality 88

Package: SOT-23-5 (DBV), 5 pins, pitch 0.95 mm, thermal pad False

## Absolute maximum (min / typ / max)

- VS_max: - / - / 28 V (Total bipolar supply (±14 V)) p2
- TJ_max: - / - / 150 °C p2

## Recommended operating (min / typ / max)

- VS: 4.75 / - / 27 V (Total supply) p2
- TA: -40 / 25 / 125 °C p2

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1 | VO | output |  | Output |
| 2 | VS- | power_in | VS | Negative power supply |
| 3 | VIN+ | input |  | Noninverting input |
| 4 | VIN- | input |  | Inverting input |
| 5 | VS+ | power_in | VS | Positive power supply |

## opamp

- opamp_topology: rail_to_rail_io
- channels: 1
- vsupply_range: 4.75 / - / 27 V (Total supply VS+ - VS-) p2
- vsupply_split_capable: True
- iq_per_amp: - / 0.0037 / - A p1
- gbw: - / 7e+07 / - Hz (G = 11, Vo = 20 mVpp, VS = ±5 V) p2
- slew_rate: - / 2e+08 / - V/s (G = 2, -2 V to 2 V step) p2
- vos: - / - / 0.0015 V p1
- ib: - / 2e-12 / - A p1
- unity_gain_stable: True

