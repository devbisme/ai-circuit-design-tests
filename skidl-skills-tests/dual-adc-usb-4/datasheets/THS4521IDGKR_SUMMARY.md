# THS4521IDGKR — Low-Power Fully Differential ADC-Driver Amplifier (U9/U11)

| Spec | Value |
|------|-------|
| Package | VSSOP-8 (listed MSOP-8 by JLC; footprint used is VSSOP-8_3x3mm_P0.65mm) |
| Vcc / Vin range | 2.7V – 5.4V single supply (±1.25 to ±2.75V dual) |
| Key output spec | 95MHz GBW, 490V/µs slew, 100dB CMRR/PSRR, adjustable output common-mode |
| Max current / power | 35mA output, 1.14mA quiescent per amp |
| Operating temp | -40°C to +85°C |

## Pinout (JLC/EasyEDA data)
| Pin | Name | Function |
|-----|------|----------|
| 1 | VIN- | Inverting input |
| 2 | VOCM | Output common-mode set |
| 3 | VS+ | Positive supply |
| 4 | VOUT+ | Positive differential output |
| 5 | VOUT- | Negative differential output |
| 6 | VS- | Negative supply |
| 7 | PD | Power-down, active low typical for TI PD pins — confirm polarity in full datasheet before tying |
| 8 | VIN+ | Non-inverting input |

Symbol already matched: `Amplifier_Difference:THS4521IDGK` — confirmed **CP** per sourcing,
no generation needed.

## Notes
- Datasheet: downloaded to `datasheets/THS4521IDGKR.pdf` (TI, THS452x family sheet).
- Single-ended-to-differential ADC driver for the ADS5231's INA+/INA-/INB+/INB- inputs — this
  is exactly the "Integrated ADC driver" feature called out in TI's MCP spec data. Follow TI's
  standard THS452x ADC-driver application circuit (gain-setting resistor network + VOCM
  reference) for R14-R19/R24-R29 (already sourced) and C30-C38/C40-C48 filter caps.
- PD (pin 7): verify active-high vs active-low in the full PDF before the coder ties it to a
  fixed rail — TI's differential-amp family is not perfectly consistent on this pin's polarity
  across parts.
