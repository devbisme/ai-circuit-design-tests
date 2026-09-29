# OPA355NA/3K — 200MHz CMOS-input unity-gain buffer

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Vcc / Vin range | Single supply 2.7–5.5V, or ±1.25 to ±2.75V split |
| Key output spec | 3 pA input bias current (CMOS), GBW 200MHz, rail-to-rail OUTPUT only (input is NOT rail-to-rail) |
| Max current / power | 8.3mA quiescent, 60mA output |
| Operating temp | −40°C to +125°C |

## Pinout (SOT-23-6, confirmed against the actual TI datasheet, page with "Pin Functions:
OPA355" table)

| Pin | Name | Function |
|-----|------|----------|
| 1 | OUT | Output |
| 2 | V− | Negative supply (GND in single-supply use) |
| 3 | +IN | Non-inverting input |
| 4 | −IN | Inverting input |
| 5 | ENABLE | **Amplifier power-down. Low = disabled, high = normal operation — this pin MUST be driven, it cannot float.** |
| 6 | V+ | Positive supply |

## Notes

- **ENABLE (pin 5) must be tied directly to V+ (or driven high) — the datasheet explicitly
  states "pin must be driven."** Leaving it floating is undefined/unreliable, not a safe
  default. Tie directly to `+3V3_A`, no pull resistor needed for an always-on buffer.
- **Critical path — CMOS input mandatory** (architecture decision 6, sourcing item 3): do not
  substitute a bipolar-input amplifier regardless of speed. Input common-mode range does NOT
  reach the rails (rail-to-rail output only) — verify the divider's DC bias point (`VBIAS`)
  stays within OPA355's specified input common-mode range (check the datasheet's "Input
  Common-Mode Voltage Range" spec, page ~5, before finalizing R_top/R_bot values — this was
  not independently re-verified in this pass since the divider design predates this phase).
- PREFIX-matched KiCad symbol `Amplifier_Operational:OPA355NA` — pin table above confirms it
  against the live TI PDF (`datasheets/OPA355NA_3K.pdf`), matches the EasyEDA pin data used
  for the sourced BOM. No corrections needed.
- Stock 489 at sourcing time (WARN <500) — second source OPA355UA/2K5 (SOIC-8, different
  pinout — 8-pin, not 6-pin — do not swap footprints blindly if ever substituted).
