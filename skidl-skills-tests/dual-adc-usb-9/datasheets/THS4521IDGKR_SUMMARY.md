# THS4521IDGKR — TI low-power RRO fully differential amplifier, VSSOP-8

Source: `THS4521IDGKR.pdf` (SBOS458H, Jun 2015).

| Spec | Value |
|------|-------|
| Supply | 2.5–5.5 V |
| GBW / SR | 95 MHz / 490 V/µs |
| Iq | 1.14 mA |
| PD | enable ≥2.1 V, disable ≤0.7 V; open = enabled |

## Pinout (DGK)
| Pin | Datasheet name | KiCad `Amplifier_Difference:THS4521IDGK` name |
|-----|------|----------|
| 1 | VIN– | `-` |
| 2 | VOCM | `V_{OCM}` |
| 3 | VS+ | `V_{S+}` |
| 4 | VOUT+ | *(blank — use pin number 4)* |
| 5 | VOUT– | *(blank — use pin number 5)* |
| 6 | VS– | `V_{S-}` |
| 7 | PD | `~{PD}` |
| 8 | VIN+ | `+` |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Pinout | as above | Pin Functions p.4 — **verified** |
| PD thresholds | on >2.1 V, off <0.7 V | elec. table — **verified** |
