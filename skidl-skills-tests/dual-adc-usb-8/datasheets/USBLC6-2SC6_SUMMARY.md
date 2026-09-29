# USBLC6-2SC6 (TECH PUBLIC, C2827654) — 2-line USB ESD array + VBUS clamp, SOT-23-6  [U1]

**No PDF** (LCSC link returned HTML; ordinary part, 2-attempt budget). Values are from the JLC parametric field. Symbol: KiCad `Power_Protection:USBLC6-2SC6`. Footprint: `Package_TO_SOT_SMD:SOT-23-6`.

| Spec | Value (JLC field — UNVERIFIED) |
|------|-------|
| VRWM | 5 V |
| VBR | 6 V |
| Clamp | 12 V |
| IPP / PPP | 6 A / 150 W |
| Line capacitance | "0.35 pF" — **suspect** |
| IR | 80 nA |

## Pinout (KiCad symbol = ST pinout)
| Pin | Name | Function |
|-----|------|----------|
| 1, 6 | I/O1 | line 1 (pass-through pair) |
| 2 | GND | ground |
| 3, 4 | I/O2 | line 2 |
| 5 | VBUS | supply clamp |

## Notes (numeric worklist)
- The line capacitance "0.35 pF" is ~7–10× lower than ST's own USBLC6-2SC6 (I/O–GND ~2.5 pF typ, 3.5 pF max). Treat it as **UNVERIFIED**. It matters only as USB HS D+/D– loading, where either figure is acceptable.
- VRWM of 5 V is below the USB VBUS maximum of 5.25 V (ST's part is rated 5.25 V). Expect µA-level leakage at 5.25 V, which is harmless. Pin compatibility with ST is assumed, not verified.
