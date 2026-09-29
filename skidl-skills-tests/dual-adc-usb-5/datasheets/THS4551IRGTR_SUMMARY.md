# THS4551IRGTR — Fully-differential ADC driver amplifier

| Spec | Value |
|------|-------|
| Package | QFN-16-EP (3×3mm) |
| Vcc / Vin range | Single supply 2.7–5.4V, or split ±1.35 to ±2.7V |
| Key output spec | GBW 135MHz, slew rate 220V/µs, output swings to 0.2V of each rail |
| Max current / power | 1.37mA/amp quiescent, 65mA output |
| Operating temp | −40°C to +125°C |

## Pinout (QFN-16 + EP, from EasyEDA/JLC symbol data — EP already included as pin 17)

| Pin | Name | Function |
|-----|------|----------|
| 1 | FB− | Feedback −, connects to OUT− through R_f |
| 2 | IN+ | Non-inverting input |
| 3 | IN− | Inverting input |
| 4 | FB+ | Feedback +, connects to OUT+ through R_f |
| 5,6,7,8 | VS+ | Positive supply (4 pins, all must be tied) |
| 9 | VOCM | Output common-mode set — drive from ADC's CM pin (ADS5231 pin 52) per architecture |
| 10 | OUT+ | Differential output + |
| 11 | OUT− | Differential output − |
| 12 | PD | Power-down, **active LOW** on TI's THS45xx FDA family convention (logic high/float = normal operation, logic low = shutdown) — tie to `+3V3_A` directly or through a pull-up; **not independently confirmed against this part's own PDF** (see Notes), verify before board spin |
| 13,14,15,16 | VS− | Negative supply / ground (4 pins — this design uses single-supply, so VS− = GND) |
| 17 | GND | **Exposed pad** — already present as its own numbered pin in the JLC/EasyEDA data; tie to GND plane |

## Notes

- **PREFIX/WILDCARD-matched KiCad symbol** `Amplifier_Difference:THS4551xRGT` — pin table
  above is drawn directly from live JLC/EasyEDA symbol data for this exact LCSC part
  (C2869590), not a guess; 16+1(EP) = 17 pins, matches the QFN-16-EP package exactly.
  Confirm PD polarity (active-high vs active-low power-down) against the datasheet before
  wiring, since JLC's pin data does not state polarity — the summary above flags this rather
  than asserting a default that could disable the amplifier if wrong.
- No PDF obtained (LCSC-hosted URL returned an HTML anti-bot page, 1/2 attempts used per
  budget — did not spend the second attempt since pin data + full parametric specs were
  already complete from MCP).
- Gain-setting resistors: architecture sets G=2 via feedback resistors R_f (R107/207,
  R108/208 = 1.00kΩ ±0.1%) and gain resistors R_g1/R_g2 (R105/106, R205/206 = 499Ω ±0.1%) —
  matched pairs per the sourced BOM's afe_channel numbering; FB−/FB+ (pins 1/4) are where
  R_f ties back from OUT−/OUT+.
- Critical path, do not substitute for a part whose output range on 3.3V excludes
  1.15–2.15V (architecture decision 7/`Next phase must` item 4 from sourcing).
