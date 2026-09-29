# THS4521IDR — Fully Differential ADC Driver Amplifier (KEYSTONE, ADC driver, U103/U203)

Datasheet obtained: `datasheets/THS4521IDR.pdf` (TI SBOS458H, Rev. June 2015, via
`ti.com/lit/gpn/THS4521` redirect — verified, covers THS4521/THS4522/THS4524 family).

| Spec | Value |
|------|-------|
| Package | SOIC-8 (D package) |
| Vcc / Vin range | Single supply 2.5–5.5 V (or dual ±1.25 to ±2.75 V) |
| Key output spec | 95 MHz GBW, 490 V/µs slew rate, integrated ADC driver with adjustable output common-mode |
| Max current / power | 1.14 mA/amp quiescent; 55 mA output current |
| Operating temp | −40°C to +85°C |

## Pinout (SOIC-8, datasheet §6 "Pin Configuration and Functions")
| Pin | Name | Function |
|-----|------|----------|
| 1 | VIN− | Inverting amplifier input |
| 2 | VOCM | Common-mode voltage input — sets the output common-mode level (typically driven from the ADC's VCM reference or a resistor divider) |
| 3 | VS+ | Positive supply |
| 4 | VOUT+ | Non-inverting output |
| 5 | VOUT− | Inverting output |
| 6 | VS− | Negative supply (note: "VS− is tied together on multi-channel devices" — not relevant to this single-channel THS4521) |
| 7 | PD | Power-down, **active low**: "PD = logic low puts device into low-power mode. PD = logic high or open for normal operation." |
| 8 | VIN+ | Non-inverting amplifier input |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| PD pin polarity | Active-low power-down; **leave open or tie high for normal operation** (no external pull required — datasheet explicitly allows "open") | datasheet p.4, Table pin 7 — **verified** |
| VOCM pin | Must be driven to set output common-mode — typically tied to the ADC's reference (VCM_REF, per `sourced_bom.md`'s R16/R17 VCM_REF divider in the `power` block) or a fixed voltage within the amp's input common-mode range | datasheet p.4 — **verified pin function**; exact net assignment to VCM_REF is an inference from `sourced_bom.md`'s block list, not confirmed in `net_plan.md` |
| Rf/Rg gain-setting resistors | External, per `sourced_bom.md`'s R107-R110 (1.00 kΩ / 1.10 kΩ, gain = Rf/Rg = 1.1) — not internal to the part | Cross-checked against `sourced_bom.md`'s `[calc]` precision resistor rows — consistent with a standard FDA gain network |

## Notes
- U103 (CH1) / U203 (CH2) — same part, same pinout, two instances.
- PD left floating is safe (defaults to normal operation) — but best practice is an
  explicit tie-high to VS+ if not driven by logic, to avoid relying on the "open" default
  under noise.
- Application figure: not extracted from this pass (page budget spent on pin table +
  PD/VOCM facts); if the coder needs the exact feedback-network topology figure, it's in
  §8 "Detailed Description" of the downloaded PDF (not read this pass).
