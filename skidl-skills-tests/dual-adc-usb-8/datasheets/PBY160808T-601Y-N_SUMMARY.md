# PBY160808T-601Y-N — Chilisin 600 Ω @100 MHz ferrite bead, 0603  [FB1 ADC VDRV, FB2 XO supply]

**No PDF** (LCSC link returned HTML; ordinary part). Values are from the JLC parametric field. Symbol `Device:FerriteBead`. Footprint `Inductor_SMD:L_0603_1608Metric`.

| Spec | Value |
|------|-------|
| Z @ 100 MHz | 600 Ω ±25 % |
| DCR | 200 mΩ max — UNVERIFIED (distributor) |
| Irated | 1 A — UNVERIFIED |

## Notes (numeric worklist)
- FB1 drop: 33 mA × 0.2 Ω = 6.6 mV, well inside the ADS5231 \|AVDD–VDRV\| ≤ 0.3 V limit.
- FB2 drop: 20 mA × 0.2 Ω = 4 mV.
