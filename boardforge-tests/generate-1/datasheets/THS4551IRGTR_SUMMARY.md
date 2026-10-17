# THS4551IRGTR - Low-noise precision 150 MHz FDA

Texas Instruments, datasheet THS4551IRGTR.pdf, quality 90

Package: VQFN-16 (RGT) 3x3 mm, EP 1.68x1.68 mm (pad 17), 17 pins, pitch 0.5 mm, thermal pad True

## Absolute maximum (min / typ / max)

- VS_max: - / - / 5.5 V ((VS+) - (VS-)) p2
- VIN_diff: -1 / - / 1 V p2
- TJ_max: - / - / 150 °C p2

## Recommended operating (min / typ / max)

- VS: 2.7 / 5 / 5.4 V (Total supply (VS+ - VS-)) p2
- TA: -40 / 25 / 125 °C p2

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 1 | FB- | output |  | Inverting output feedback |
| 2 | IN+ | input |  | Noninverting input |
| 3 | IN- | input |  | Inverting input |
| 4 | FB+ | output |  | Noninverting output feedback |
| 5,6,7,8 | VS+ | power_in | VS | Positive supply |
| 9 | VOCM | input |  | Common-mode voltage input |
| 10 | OUT+ | output |  | Noninverting output |
| 11 | OUT- | output |  | Inverting output |
| 12 | PD | input |  | Power down: low = off, high = normal (do not float) |
| 13,14,15,16 | VS- | power_in | VS | Negative supply |
| 17 | EP | passive |  | Exposed thermal pad; isolated from die; connect to power or ground plane, never float |

## opamp

- opamp_topology: rail_to_rail_output
- channels: 1
- vsupply_range: 2.7 / 5 / 5.4 V p2
- vsupply_split_capable: True
- gbw: - / 1.35e+08 / - Hz (G = 100, Vout = 20 mVpp) p7
- slew_rate: - / 2.2e+08 / - V/s p7
- unity_gain_stable: True

