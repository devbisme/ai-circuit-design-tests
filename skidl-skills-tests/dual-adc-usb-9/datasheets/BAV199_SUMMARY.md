# BAV199 (HXY MOSFET, LCSC C5184419) — low-leakage series diode pair, SOT-23

Source: `BAV199.pdf` (HXY datasheet). Note the sourced part is **HXY**, not Nexperia.

| Spec | Value |
|------|-------|
| VR / VRM | 70 V |
| IR | **5 nA max @ VR 70 V** |
| CD | **2 pF max @ VR 0 V, 1 MHz** |
| VF | 0.90 V @1 mA, 1.00 V @10 mA, 1.10 V @50 mA, 1.25 V @150 mA (max) |
| IO / IFSM | 215 mA / 1 A (8.3 ms) |
| trr | 3 µs |
| PD | 200 mW |

## Pinout
| Pin | Function |
|-----|----------|
| 1 | anode of D1 (outer anode) |
| 2 | cathode of D2 (outer cathode) |
| 3 | common: cathode D1 = anode D2 |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Pin 3 = common node (K2) | yes; 1 → |> → 3 → |> → 2 | HXY datasheet p.1 diagram — **verified** |
| KiCad `Diode:BAV99` mapping | same numbering (1, 2, 3 = common). Symbol pin NAMES are unusable (1 "K", 3 "K", 2 "A") — **connect by number**: D20[1] → VAFE_N, D20[2] → VAFE_P, D20[3] → ATT_A | KiCad lib + HXY — **verified** |
| Leakage / capacitance | 5 nA max, 2 pF max | HXY electrical table — **verified** |
