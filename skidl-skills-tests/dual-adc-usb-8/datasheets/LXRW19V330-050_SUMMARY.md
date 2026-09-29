# LXRW19V330-050 — Murata voltage-TUNED variable capacitor (NOT a mechanical trimmer), 1.3×0.9 mm 5-pad  [C104/C204]

Source: `datasheets/LXRW19V330-050.pdf` (Murata spec, Jul 2018, 17 pp).

| Spec | Value |
|------|-------|
| Capacitance | **33 pF at VT = 0 V; 16.5 pF at VT = 3 V** (f = 1 MHz); continuous curve p.5 |
| Tuning voltage VT | 3.2 V max continuous |
| RF rated voltage | 50 Vp-p |
| Temp | –30…+85 °C |
| Size | L 1.3 ± 0.1 × W 0.9 ± 0.1 × T 0.6 max; pad dims a 0.20, b 0.25, c 0.28, d 0.50 (p.2); reference land pattern p.9 |

## Pinout (§4-2, p.3)
| Pin | Name | Function |
|-----|------|----------|
| 1 | GND | ground |
| 2 | Vt | tuning-voltage input |
| 3 | Port1 | RF port |
| 4 | Port2 | RF port |
| 5 | NC | no connect |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Device type | electrically tuned capacitor ("adjust capacitance by the tuning voltage") | §2 p.1 — **verified** |
| C vs VT | 33 → 16.5 pF over VT 0 → 3 V | §7-2 — **verified** |
| Capacitor terminals | variable C is between Port1 (pin 3) and Port2 (pin 4); GND (1) and Vt (2) are the bias terminals | §6 equivalent circuit p.4 — **verified**. For a shunt-to-GND trim: Port1 → A_DIV, Port2 → GND |

## Notes — ARCHITECTURE ISSUE
- The skeleton BOM treats C104 as a hand-trimmed 16.5–33 pF trimmer, "hand-trim to 23.8 pF". This part has **no mechanical adjustment**. It needs a DC bias on Vt (roughly 1.5–2 V for ~24 pF, read off the p.5 curve) and a clean, stable source for that bias.
- A voltage-tuned (ferroelectric/BST-class) capacitor on the divider node may also vary with the signal voltage (±1.1 V at A_DIV), which is a linearity risk.
- This needs an architect decision: either substitute a true mechanical trimmer, or add a Vt bias network and accept the linearity risk.
