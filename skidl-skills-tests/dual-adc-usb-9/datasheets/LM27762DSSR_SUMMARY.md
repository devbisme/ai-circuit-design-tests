# LM27762DSSR — TI ± low-noise charge pump + LDOs, WSON-12 3x2

Source: `LM27762DSSR.pdf` (TI ZHCSFJ0A, Chinese-language edition, Sept 2016; numeric tables unambiguous).

| Spec | Value |
|------|-------|
| VIN | 2.7–5.5 V |
| OUT± | ±1.5 … ±5 V, 250 mA each |
| VFB+ | 1.182 / 1.200 / 1.218 V |
| VFB– | −1.238 / −1.220 / −1.202 V |
| EN± VIH | 1.2 V; EN max = VIN |

## Pinout (KiCad `Regulator_SwitchedCapacitor:LM27762`: C1+ → `C+`, C1– → `C-`, thermal pad → `PAD` 13)
| Pin | Name | Function |
|-----|------|----------|
| 1 | PGOOD | open drain; **connect to GND if unused** |
| 2 | FB+ | divider OUT+→FB+→GND; never open |
| 3 | VIN | |
| 4 | GND | |
| 5 | CP | unregulated −VIN output, needs cap |
| 6 | OUT– | |
| 7 | FB– | divider OUT–→FB–→GND; never open |
| 8 | EN– | enables charge pump + negative LDO |
| 9 / 10 | C1– / C1+ | flying cap |
| 11 | OUT+ | |
| 12 | EN+ | positive LDO enable |
| EP | Thermal Pad | GND, do not leave unconnected |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| VFB± | as above | elec. table p.5 — **verified** |
| PGOOD unused → GND | yes | Pin Functions — **verified** |
