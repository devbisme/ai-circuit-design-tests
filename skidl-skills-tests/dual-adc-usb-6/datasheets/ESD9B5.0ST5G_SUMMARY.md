# ESD9B5.0ST5G — Bidirectional TVS Diode (ESD protection, D101/D201)

MCP data only — PDF not obtained (URL attempts not spent; local symbol already EXACT per
`sourced_bom.md`, so a PDF was judged low value for this ordinary part).

| Spec | Value |
|------|-------|
| Package | SOD-523 |
| Vcc / Vin range | N/A (passive TVS) |
| Key output spec | Vrwm 5V, Vbr 7.8V, clamping 15V, bidirectional |
| Max current / power | 15 pF junction capacitance (≤0.5 pF differential per `sourced_bom.md`'s note — verify against the exact onsemi variant selected) |
| Operating temp | −55°C to +150°C (Tj) |

## Notes
- Local symbol `Diode:ESD9B5.0ST5G` is an EXACT match — use its pin names directly.
- Low-capacitance ESD protection on the analog input path, per `analog_frontend` block.
