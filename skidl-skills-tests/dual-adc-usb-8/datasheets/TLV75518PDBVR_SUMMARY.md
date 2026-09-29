# TLV75518PDBVR — TI 500 mA LDO, fixed 1.8 V, active discharge, SOT-23-5  [KEYSTONE, U5 V1V8]

Source: `datasheets/TLV75518PDBVR.pdf` = TI SBVS320D, the TLV755P family datasheet covering TLV75518P. `fetch-datasheet.py` rejected the family PDF because it never names "TLV75518"; it was checked by hand and copied in. Symbol: KiCad `Regulator_Linear:TLV75518PDBV` (pins match ✓). Footprint: `Package_TO_SOT_SMD:SOT-23-5`.

| Spec | Value |
|------|-------|
| VIN | 1.45–5.5 V |
| VOUT | 1.8 V fixed |
| IOUT | 500 mA |
| Dropout | ≤ 380 mV typ at 500 mA (1.8 V ≤ VOUT < 2.5 V: 325 typ / 380 max mV at 85 °C) |
| IGND | 33 µA |
| θJA (DBV) | 231.1 °C/W (JEDEC); 100.8 on EVM |

## Pinout (DBV, Table 4-1)
| Pin | Name | Function |
|-----|------|----------|
| 1 | IN | input, ≥1 µF |
| 2 | GND | ground |
| 3 | EN | VHI ≥ 1 V on, VLO ≤ 0.3 V off |
| 4 | NC | no internal connection |
| 5 | OUT | output, ≥1 µF |

## Notes
- IN and EN → V3V3D, per the net plan. UVLO is 1.21–1.44 V (rising).
