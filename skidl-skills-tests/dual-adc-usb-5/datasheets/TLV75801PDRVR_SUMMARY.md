# TLV75801PDRVR — Adjustable 500mA LDO (U2, generates +1V2_D)

| Spec | Value |
|------|-------|
| Package | WSON-6-EP (2×2mm) |
| Vcc / Vin range | 1.5–6.0V in, 0.55–5.5V adjustable out |
| Key output spec | **VFB = 0.55V** (feedback reference), 0.7% accuracy @25°C, 1% over temp |
| Max current / power | 500mA, dropout 130mV@500mA |
| Operating temp | −40°C to +125°C (Tj) |

## Pinout (WSON-6+EP, confirmed against TI's own TLV758P datasheet Table 4-1 — matches the
JLC/EasyEDA data used in the sourced BOM exactly)

| Pin | Name | Function |
|-----|------|----------|
| 1 | OUT | Regulated output |
| 2 | FB | Feedback — sets VOUT via external divider, see formula below |
| 3 | GND | Ground |
| 4 | EN | **Active HIGH** — drive above VEN(HI) to turn on, below VEN(LO) for shutdown |
| 5 | DNC | Do not connect (leave unconnected, do not tie to GND) |
| 6 | IN | Supply input — from `+3V3_D` |
| 7 | EP | Exposed thermal pad — tie to GND plane (mandatory, architecture item 6: thermal pad required) |

## Feedback-divider values for the design's 1.20V ±3% target (resolves sourcing's open item)

```
VOUT = VFB × (1 + R1/R2), VFB = 0.55V
1.20V = 0.55V × (1 + R1/R2)  →  R1/R2 = 1.1818
```

**R2 (FB to GND) = 10.0 kΩ, R1 (OUT to FB) = 11.8 kΩ** (both E96, 0.1–1% tolerance) gives
VOUT = 0.55×(1+11.8/10) = 1.199V — well inside ±3% of 1.20V. Use ≥0.1% or 1% resistors
consistent with the sourced BOM's other precision-divider parts (R8–R11) so accuracy is not
dominated by resistor tolerance.

Divider current-vs-FB-bias-error constraint: **R1+R2 ≤ VOUT/(IFB×100)**, IFB=10nA →
R1+R2 ≤ 1.2V/(1µA) = 1.2MΩ — the chosen 21.8kΩ total is far below this ceiling, no error
contribution from FB bias current.

## Notes

- **Output capacitor ≥0.47µF required for stability** (X5R/X7R ceramic; max recommended
  220µF) — matches the sourced BOM's decoupling allocation for U2, confirm ≥0.47µF is
  actually placed, not just "some decoupling."
- **EN (pin 4) must be driven** — tie directly to the rail it's enabled from (e.g. `+3V3_D`
  through the same enable logic as the rest of `digital_power`, or straight to `+3V3_D` if
  always-on) — do not leave floating.
- DNC (pin 5) — leave floating, do not connect to GND or any signal.
- Same TI DRV thermal-pad family as U3 (TLV75733PDRVR) per sourcing decision 2.
- Datasheet: TI's TLV758P family datasheet (`https://www.ti.com/lit/ds/symlink/tlv758p.pdf`,
  fetched and read directly in this pass but not saved to `datasheets/` — the automated
  fetch-and-validate step separately attempted the LCSC-hosted mirror and got an HTML
  anti-bot page, exhausting the 2-URL budget for the *cached copy*; the pin/formula data
  above was still confirmed against TI's real datasheet content via a manual read).
