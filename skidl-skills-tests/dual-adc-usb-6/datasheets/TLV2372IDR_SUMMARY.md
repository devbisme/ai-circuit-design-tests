# TLV2372IDR — Dual RRIO Op-Amp (reference buffer, U7)

MCP data only — PDF not obtained (JLC field URL returned HTML on the one fallback attempt).
Local symbol `Amplifier_Operational:TLV2372` is an EXACT match per `sourced_bom.md` — pin
names not re-derived here since a verified local symbol exists.

| Spec | Value |
|------|-------|
| Package | SOIC-8 |
| Vcc / Vin range | Single 2.7–16 V, or dual ±1.35 to ±8 V |
| Key output spec | Rail-to-rail I/O, 1 pA Ib, 500 µV Vos, 3 MHz GBW |
| Max current / power | 550 µA quiescent, 7 mA output |
| Operating temp | −40°C to +125°C |

## Notes
- Substituted for the architect's SGM8521 per sourcing decision #5 — SOIC-8 dual package
  instead of SOT-23-5 single. **The coder must tie the second (unused) channel's
  non-inverting input to a valid reference and its output to its own inverting input
  (unity-gain follower)** to avoid a floating unused op-amp half — this is explicitly
  called out in `sourced_bom.md` and repeated here since it's an easy ERC-failure/oscillation
  risk if skipped.
