# AD8066ARZ — Dual FastFET op-amp, 145 MHz (SOIC-8)

SOURCE: Analog Devices AD8065/AD8066 Data Sheet Rev. L (facts confirmed via WebSearch
synthesis quoting the datasheet's own pin diagram and feature list). PDF not retrieved
(analog.com host unreachable/timed out from this sandbox this session — same failure
mode as AD9235; see Phase 2 log). **No KiCad symbol exists for this part — this pin
table is the kipart input for the coding phase.** The sourcing handoff noted a
placeholder (`Amplifier_Operational:LM7332`) is usable for schematic capture since
standard dual-op-amp SOIC-8 pinout is universal — **confirmed below: AD8066's pinout
matches that universal convention exactly**, so the placeholder is pinout-safe if
`kipart` generation is deferred.

| Spec | Value |
|------|-------|
| Package | SOIC-8 (AD8066AR / "Z" = Pb-free) |
| Channels | 2 (dual), FET input |
| Supply | 5 V to 24 V (i.e. ±2.5 V to ±12 V dual supply, or single-supply 5–24 V) — this design runs it on the ±5 V rails (V5_A/−5V_A) |
| Bandwidth | 145 MHz (−3 dB, G=+1) |
| Input noise | 7.0 nV/√Hz voltage, 0.6 fA/√Hz current |
| Input bias current | Very low (FET input, sub-pA class — "exceptionally high input impedance" per datasheet) |
| Slew rate | High-speed FastFET class (not itself quoted this session — consistent with the 145 MHz GBW and the design's 5 MHz Butterworth filter requirement with ample margin) |
| Operating temp | Industrial range typical for the "A" grade (confirm exact limits against the full datasheet before extreme-environment use — not itself quoted this session) |

## Pinout (SOIC-8)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | OUT1 | output | Amplifier 1 output |
| 2 | −IN1 | input | Amplifier 1 inverting input |
| 3 | +IN1 | input | Amplifier 1 non-inverting input |
| 4 | −VS | power | Negative supply (shared) |
| 5 | +IN2 | input | Amplifier 2 non-inverting input |
| 6 | −IN2 | input | Amplifier 2 inverting input |
| 7 | OUT2 | output | Amplifier 2 output |
| 8 | +VS | power | Positive supply (shared) |

This is the standard/universal dual-op-amp SOIC-8 pin map (same as LM833, TL072, OPA2810,
NE5532, etc.) — pin 4 = V−, pin 8 = V+, both amplifiers mirror-imaged around the package.

## Notes

- This design uses AD8066 as the BNC-input buffer + Sallen-Key filter stage (U_a in
  `afe_channel`, per sourced BOM), running on the ±5 V analog rails (V5_A / −5V_A from
  `power_analog`).
- Decoupling: 3× 100 nF + 3× 1 µF (`C_dec` in sourced BOM, shared across the afe_channel
  block's two op-amps) — place 100 nF directly at pins 4 and 8, with the 1 µF as local
  bulk.
- **Vetted drop-in alternates** (per sourcing, same SOIC-8 dual pinout, no pin-table
  change needed): OPA2810IDR, OPA1656IDR — use only if AD8066 sourcing comes up short.
- Sourced BOM footprint: `Package_SO.pretty:SOIC-8_3.9x4.9mm_P1.27mm` — standard.
