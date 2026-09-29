# FNR3015S2R2MT — Changjiang 2.2 µH shielded power inductor, 3×3 mm  [L1, L2]

**No PDF** (LCSC link returned HTML; ordinary part). Values are from the JLC parametric field. Symbol `Device:L`. Footprint `Inductor_SMD:L_Changjiang_FNR3015S`.

| Spec | Value |
|------|-------|
| L | 2.2 µH ±20 % |
| DCR | 78 mΩ — UNVERIFIED (distributor) |
| Isat / Irated | 2 A / 2 A — UNVERIFIED (distributor) |

## Notes (numeric worklist)
- The margin is large: peak inductor current is ≤ ~0.35 A (V3V3D 191 mA max + ripple ≈ 0.6 A p-p at 1.5 MHz, 5 V → 3.3 V). Even a 2× error in Isat is harmless.
- The TI-recommended L is 2.2 µH ✓.
