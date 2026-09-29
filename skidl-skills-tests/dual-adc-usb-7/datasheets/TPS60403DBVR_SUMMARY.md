# TPS60403DBVR — 60mA inverting charge pump (power_tree, U13)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 |
| Vcc / Vin range | 1.8–5.25V |
| Key output spec | Fixed 250kHz switching, unregulated inverted output (−VIN) |
| Max current / power | 60mA output |
| Operating temp | −40°C to +125°C |

## Pinout (standard TPS6040x, per Figure 9-1 typical application)
IN, OUT, GND, CFLY+/CFLY- — existing symbol `Regulator_SwitchedCapacitor:TPS60403DBV` used,
not regenerated.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Required external capacitors | **Three 1µF ceramic caps**: CI (input bypass), C(fly) (flying cap, C78 in BOM), CO (output, C79 in BOM) | `TPS60403DBVR.pdf` p.13, §9.2.1.2 "Detailed Design Procedure" and Figure 9-1 — **verified** |
| Input bypass cap (CI) sizing rule | "When the inverter is loaded from OUT to GND [our case — R76+C80 load the output], use a large bypass capacitor (e.g. equal to C(fly)) if the supply has high AC impedance. A 0.1µF bypass is sufficient only when loaded IN-to-OUT." | `TPS60403DBVR.pdf` p.13, §9.2.1.2.2 "Input Capacitor (CI)" — **verified** |

## Resolves C82 (unattributed placeholder, sourcing flagged)
`net_plan.md`'s power_tree cap list accounts for C71–C81 and C83 but never mentions C82. TI's
own application note calls for **three** external caps (CI, C(fly), CO); the sourced BOM only
assigns two to this part's function (C78=flying, C79=output) — **CI, the VIN-side bypass cap,
was never assigned a ref designator.** C82 (currently a 100nF 0402 placeholder) is the natural
fit for CI, on the `VA_POS` net at U13's IN pin. TI recommends CI ≈1µF (same as C(fly)) for our
loading configuration (output loaded to GND) — **the current 100nF placeholder is undersized
relative to that recommendation**; recommend bumping C82 to ≥1µF X5R if board area allows,
though R76+C80's downstream 37dB filter (R-2 mitigation) already absorbs most of the resulting
ripple margin loss. This refdes attribution (C82=CI) is inferred from cross-referencing the
TPS60403 datasheet against the BOM's otherwise-complete cap accounting — not read directly
off a schematic, since no schematic yet exists at this phase.

## Notes
- Feeds VA_NEG_RAW (≈−4.80V) → R76+C80 filter → VA_NEG (≈−4.74V, AD8066 negative rail).
- 250kHz switching frequency confirmed live (sourcing decision 5) — R-2 in design_risks.md
  (37dB ripple attenuation at 250kHz) stands as specified.
- Datasheet: `datasheets/TPS60403DBVR.pdf` (TI SBVS-series, TPS6040x family).
