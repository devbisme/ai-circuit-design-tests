# TLV62569DBVR — 2A Synchronous Step-Down Buck Converter, SOT-23-5 (used for +3V3 rail)

Source: `datasheets/TLV62569DBVR.txt` (TI datasheet, full document, already extracted).

| Spec | Value |
|------|-------|
| Package | SOT-23-5 (DBV) — this BOM's grade (no PG pin on 5-pin variant) |
| Vcc / Vin range | 2.5V–5.5V input (VBUS-derived, per `power_digital` block) |
| Key output spec | Adjustable 0.6V to VIN via external FB divider; this design sets **+3.3V** |
| Max current / power | 2A rated switch current; 1.5 MHz switching (architect's design_risks.md notes 3 switchers share the board at 1.5/1.5/2MHz — already accounted for) |
| Operating temp | –40°C to 125°C |

## Pinout (SOT23-5, Top View)

| Pin | Name | Function |
|-----|------|----------|
| 1 | EN | Enable, active high. **Do not leave floating.** Architecture: gated by `PWR_EN` (Decision 7). |
| 2 | GND | Ground |
| 3 | SW | Switch node — connect to inductor (L2 or L1, per net plan) |
| 4 | VIN | Power supply input |
| 5 | FB | Feedback — external resistor divider |

## Notes — closes 2 of 8 feedback-divider values (`03_sourcing.md` gap item #4)

`VOUT = VFB × (1 + R1/R2) = 0.6V × (1 + R1/R2)`, **R2 max 200kΩ** (datasheet §8.2.2.2, "use a
maximum of 200kΩ for R2" — larger R2 hurts noise sensitivity/accuracy, smaller increases
quiescent current).

Target +3.3V → R1/R2 = 4.5. Using **R2 = 100kΩ, R1 = 453kΩ** (both E96, `0402WGFxxxxTCE`
family already used throughout `sourced_bom.md` — R2=100kΩ is literally the part already in
the BOM as `0402WGF1003TCE`; R1=453kΩ would be `0402WGF4533TCE`, same family/vendor,
**not independently stock-checked this phase**, pcbparts MCP unavailable) gives
VOUT = 0.6 × 5.53 = **3.318V** (+0.55% vs. 3.3V target — acceptable, and R2=100kΩ is TI's own
worked example value in this exact datasheet).

- **TI recommends a 6.8pF feed-forward capacitor (C3) in parallel with R1 when R2 = 100kΩ**
  (§8.2.2.2) — improves loop bandwidth/transient response. Optional but TI's own default
  for this exact divider configuration; add if board space and BOM discipline allow, not a
  hard requirement.
- **Soft-start (R6) resolved:** `tSS = 800µs` typical for the DBV (SOT-23-5) package
  specifically (datasheet Electrical Characteristics table splits tSS by package: DBV=800µs,
  DDC/DRL variants=900µs). Falls inside the architecture's required 0.33–5.5ms monotonic-ramp
  window for +3V3 (`skeleton_bom.md` / R6) — **no soft-start conflict.**
- EN tied to `PWR_EN`, matching architecture's whole-board power-gating scheme (Decision 7).
