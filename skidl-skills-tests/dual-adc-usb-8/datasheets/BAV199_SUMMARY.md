# BAV199 (HXY MOSFET) — low-leakage series diode pair, SOT-23  [D101/D201 input clamp]

Source: `datasheets/BAV199.pdf` (HXY/Huaxuanyang BAV199 datasheet, 4 pp). Symbol: generated `dual_adc_usb:BAV199` (pins A=1, K=2, COM=3). Do **not** use `Diode:BAV19` (single diode). Footprint: `Package_TO_SOT_SMD:SOT-23`.

| Spec | Value |
|------|-------|
| VR / V(BR) | 70 V |
| IO / IFM / IFSM | 215 mA / 500 mA / 1 A (8.3 ms) |
| Pd | 200 mW |

## Pinout (p.1 internal diagram)
| Pin | Symbol name | Function |
|-----|------|----------|
| 1 | A | anode of D1 |
| 3 | COM | cathode of D1 = anode of D2 (common) |
| 2 | K | cathode of D2 |

## Load-bearing facts (numeric worklist)
| Fact | Value | Source |
|------|-------|--------|
| Topology | series pair 1 → 3 → 2 | p.1 diagram — **verified**; net plan (1→VN_AFE, 2→VP_AFE, 3→A_DIV) is correct |
| Diode capacitance CD | **≤ 2 pF per diode at VR = 0, 1 MHz** (falls with VR, p.2 curve) | p.1 EC + p.2 curve — **verified** |
| Reverse leakage IR | ≤ 5 nA at VR = 70 V (25 °C) | p.1 — **verified** (→ ≤0.5 mV across R_B 100 k) |
| VF | ≤ 0.9 V at 1 mA; ≤ 1.0 V at 10 mA | p.1 — **verified** |
| trr | ≤ 3 µs | p.1 — **verified** |

## Notes
- The node A_DIV sees up to 2 × 2 pF = **≤4 pF** of clamp capacitance, less when biased: ~2–2.5 pF total at ±2–3 V reverse. That adds to C_B and has to be absorbed by the C104 trim range.
