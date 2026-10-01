# OPA810IDBVR — TI 27 V RRIO FET-input op amp, 70 MHz GBW, SOT-23-5

Source: `OPA810IDBVR.pdf` (SBOS799E, Aug 2024).

| Spec | Value |
|------|-------|
| Supply | 4.75–27 V total (±14 V abs max) |
| GBW / SR | 70 MHz / 200 V/µs |
| IB | 2 pA typ, 20 pA max |
| Differential Cin | 0.5 pF |
| Input range | VS− −0.5 … VS+ +0.5 V abs max; II ±10 mA continuous |
| Iq | 3.7 mA |

## Pinout (DBV)
| Pin | Datasheet name | KiCad `OPA810xDBV` name |
|-----|------|----------|
| 1 | VO | `~` (use pin number 1) |
| 2 | VS– | `V-` |
| 3 | VIN+ | `+` |
| 4 | VIN– | `-` |
| 5 | VS+ | `V+` |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| DBV pinout (K1) | 1 OUT, 2 V−, 3 IN+, 4 IN−, 5 V+ | Table 5-1 / Fig 5-2 p.3 — **verified** |
| Unity-gain stable | yes (follower OK) | Features p.1 — **verified** |
