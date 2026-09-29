# BAV199LT1G — Dual Series-Connected Small-Signal Diode (clamp, D100/D200)

MCP data only — PDF not obtained (JLC field URL returned HTML on the one fallback attempt).
Pinout from `jlc_get_pinout` (EasyEDA-sourced). Symbol generated:
`symbols/dual_adc_usb.kicad_sym:BAV199LT1G` (3 pins, EXACT).

| Spec | Value |
|------|-------|
| Package | SOT-23 |
| Vcc / Vin range | N/A (passive diode) |
| Key output spec | Vf = 1.25V @150mA, Vr = 70V, "1 Pair Series Connection" topology |
| Max current / power | 215 mA rectified, 2A surge |
| Operating temp | −65°C to +150°C (Tj) |

## Pinout (SOT-23, EasyEDA-sourced)
| Pin | Name | Function |
|-----|------|----------|
| 1 | A | Anode |
| 2 | C | Cathode |
| 3 | C/A | Common node (shared cathode/anode of the series-connected pair — verify polarity orientation against the schematic's clamp topology before wiring) |

## Notes
- **This is the part sourcing flagged as having no usable local symbol stand-in** — do not
  substitute `Diode:BAV19` (wrong topology, THT single) or `Diode:BAV199DW` (wrong pin
  count, quad SOT-363). The 3-pin symbol generated this pass is topology-correct (2 series
  diodes, common node), matching the part's "1 Pair Series Connection" spec.
- Pin 3's exact identity (which end of the series pair) was not independently verified
  against a manufacturer pin diagram — EasyEDA-sourced only. Used for ADC input clamp
  protection per `analog_frontend` block; if RF-polarity matters for the clamp orientation,
  verify against an onsemi BAV199 pin diagram before finalizing.
