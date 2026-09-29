# TLV62569DBVR — TI 2 A 1.5 MHz sync buck, SOT-23-5  [KEYSTONE, U3 V3V3D / U4 V1V2]

Source: `datasheets/TLV62569DBVR.pdf` (TI SLVSDG1C, 2016–2017). Symbol: KiCad `Regulator_Switching:TLV62569DBV` (pins checked against the datasheet ✓). Footprint: `Package_TO_SOT_SMD:SOT-23-5`.

| Spec | Value |
|------|-------|
| VIN | 2.5–5.5 V |
| VOUT | 0.6 V … VIN |
| IOUT | 2 A |
| fSW | 1.5 MHz |
| Temp | TJ –40…+125 °C |

## Pinout (SOT23-5, p.3)
| Pin | Name | Function |
|-----|------|----------|
| 1 | EN | high = on; do not float. VIH ≤ 1.2 V, VIL ≥ 0.4 V |
| 2 | GND | ground |
| 3 | SW | switch node → inductor |
| 4 | VIN | supply |
| 5 | FB | feedback divider tap |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Feedback reference VFB | 0.588 / 0.600 / 0.612 V | p.4 EC table — **verified** |
| VOUT equation | VOUT = 0.6 V × (1 + R1/R2), R1 top | p.13 — **verified** |
| Recommended L / COUT | 2.2 µH; COUT 10–47 µF; typical app 4.7 µF in, 10 µF out; optional 6.8 pF feed-forward | p.12–14 — **verified** |
| EN thresholds | VIH ≤ 1.2 V, VIL ≥ 0.4 V | p.4 — **verified** |

## Notes
- Follow the typical application figure (p.1 / Fig 11): 100 k top resistor, per the net plan.
- U3: 100 k/22.1 k gives 3.315 V. U4: 100 k/100 k gives 1.200 V.
