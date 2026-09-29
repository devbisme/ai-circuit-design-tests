# BAV199 — Dual series switching diode (afe_input, D101/D201)

| Spec | Value |
|------|-------|
| Package | SOT-23 |
| Vcc / Vin range | VR 70V |
| Key output spec | Vf=1.25V@150mA, reverse leakage 5nA@75V |
| Max current / power | 215mA rectified, 1A non-repetitive surge |
| Operating temp | −55°C to +150°C |

## Notes
- Front-end overload clamp per design_risks.md R-10: at ±55V input clamp, the divider node
  reaches ±5.0V; current through the 910kΩ top resistor is limited to 55µA, carried by D101/D201.
- Symbol is a prefix match (`Diode:BAV19`, drops the trailing `9` — dual series-connected
  pinout family, correct for BAV199) — sourcing decision, not regenerated.
- Datasheet: `datasheets/BAV199.pdf` (HXY MOSFET).
