# LM27762DSSR — TI ± low-noise LDO + charge-pump inverter, WSON-12 2×3 mm  [KEYSTONE, U7 VP_AFE/VN_AFE]

Source: `datasheets/LM27762DSSR.pdf` (TI, 2025 rev). Symbol: KiCad `Regulator_SwitchedCapacitor:LM27762` (13 pins incl. PAD=13). **The symbol names pins 9/10 `C-`/`C+`**, where the datasheet says C1–/C1+. Footprint: **CUSTOM needed** (WSON-12, DSS, 2×3 mm, 0.5 mm pitch + EP; drawing in the PDF's mechanical section).

| Spec | Value |
|------|-------|
| VIN | 2.7–5.5 V; abs max 5.8 V |
| OUT+ | +1.5…+5 V adj., 250 mA |
| OUT– | –1.5…–5 V adj., 250 mA |
| Noise | 22 µVrms each |
| Temp | TA –40…+85 °C |

## Pinout (Table 4-1)
| Pin | Datasheet name | KiCad symbol name | Function |
|-----|------|------|----------|
| 1 | PGOOD | PGOOD | open-drain, 0 = good; **connect to GND if unused** |
| 2 | FB+ | FB+ | + divider tap; do not leave open |
| 3 | VIN | VIN | supply |
| 4 | GND | GND | ground |
| 5 | CP | CP | unregulated negative output → 4.7 µF (C15) to GND |
| 6 | OUT– | OUT- | regulated negative out |
| 7 | FB– | FB- | – divider tap |
| 8 | EN– | EN- | enables CP + negative LDO, active high |
| 9 | C1– | **C-** | flying cap – |
| 10 | C1+ | **C+** | flying cap + |
| 11 | OUT+ | OUT+ | regulated positive out |
| 12 | EN+ | EN+ | enables positive LDO, active high |
| EP | Thermal pad | PAD (13) | GND, must be connected |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| VFB+ | 1.182 / 1.200 / 1.218 V | EC p.5 — **verified** |
| VFB– | –1.238 / –1.220 / –1.202 V | EC p.5 — **verified** |
| VOUT+ equation | 1.2 V × (R1+R2)/R2, **R2 ≥ 50 kΩ** | §7.2.2.1 — **verified** (R9 = 100 k ✓) |
| EN VIH / VIL | ≥1.2 V / ≤0.4 V | EC — **verified** |
| Typical caps | CIN 2.2 µF, C1 1 µF, CCP 4.7 µF, COUT± 2.2 µF | §7.2 table — **verified** (matches BOM) |
