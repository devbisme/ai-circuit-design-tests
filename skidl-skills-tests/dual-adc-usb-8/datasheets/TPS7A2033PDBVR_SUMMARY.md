# TPS7A2033PDBVR — TI 300 mA ultra-low-noise LDO, fixed 3.3 V, SOT-23-5  [KEYSTONE, U6 V3V3A]

Source: `datasheets/TPS7A2033PDBVR.pdf` (TI SBVS338H, Jul 2024). Symbol: generated `dual_adc_usb:TPS7A2033PDBVR`. KiCad's `TPS7A20xxxDQN` is the X2SON pinout, which is different, so it is not used. Footprint: `Package_TO_SOT_SMD:SOT-23-5`.

| Spec | Value |
|------|-------|
| VIN | 1.6–6.0 V |
| VOUT | 3.3 V fixed |
| IOUT | 300 mA |
| Noise | ~7 µVrms |
| Dropout (DBV, 2.5 ≤ VOUT < 5.5 V, 300 mA) | 145 mV max |
| Temp | TJ –40…+125 °C |

## Pinout (SOT-23 column, p.4)
| Pin | Name | Function |
|-----|------|----------|
| 1 | IN | input |
| 2 | GND | ground |
| 3 | EN | > VEN(HI) 0.9 V on, < 0.3 V off; internal 500 kΩ pull-down |
| 4 | N/C | no connection |
| 5 | OUT | output; internal 150 Ω discharge when off |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| θJA, DBV | **187.1 °C/W** (JEDEC) | §5.4 — **verified** (architecture assumed ≈200) |
| TJ at worst case | (5.25 – 3.3) V × 139.1 mA = 0.271 W → ΔT = 50.7 °C, so TJ ≈ 101 °C at TA 50 °C (< 125 °C) | derived |
| COUT | 1–200 µF, ESR ≤ 100 mΩ; CIN 1 µF nominal | ROC p.6 — **verified** |
| EN threshold | VEN(HI) 0.9 V | EC — **verified** |
| UVLO (DBV) | 1.17 / 1.35 / 1.59 V rising | EC — **verified** |
