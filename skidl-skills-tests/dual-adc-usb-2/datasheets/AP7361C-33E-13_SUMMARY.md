# AP7361C-33E-13 — 3.3 V, 1 A fixed LDO (SOT-223)

SOURCE: model knowledge (Diodes Inc. AP7361C family — datasheet URL confirmed present
inside the installed KiCad symbol's own `Datasheet` property:
`https://www.diodes.com/assets/Datasheets/AP7361C.pdf`; diodes.com returned HTTP 403 to
a direct fetch this session — bot-blocked — so the PDF itself was not retrieved). Pin
table below is read directly from the installed KiCad symbol's base definition
(`Regulator_Linear:SPX2920M3-3.3_SOT223`, which `AP7361C-33E` `extends`), confirmed
present in `/usr/share/kicad/symbols/Regulator_Linear.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | SOT-223 (3-pin, tab = pin 2/GND) — **fixed package per sourcing R-11, do not shrink** (0.37 W dissipation at 1 A) |
| Output | 3.3 V fixed, ±2% typical |
| Max current | 1 A |
| Dropout | Low-dropout class (~400 mV typ at 1 A, standard for this family — not independently re-verified this session) |
| Input range | ~2.5 V–6.5 V typical for this LDO family (not independently re-verified — flagged) |
| EN pin | **None** — this part is always-on once VIN is applied (confirmed: only 3 pins in the symbol, no EN) |
| Operating temp | Industrial, −40 °C to +85 °C typical for this family |

## Pinout (from KiCad symbol base `SPX2920M3-3.3_SOT223`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | VI | power in | Input voltage (from USB VBUS, post-fuse/TVS) |
| 2 | GND | power in | Ground (also the SOT-223 tab) |
| 3 | VO | power out | Regulated 3.3 V output |

## Notes

- U1 in `power_digital`: VBUS → VI, VO → 3V3_D rail (feeds FT232H VCCIO, iCE40 I/O
  banks via further regulation, LED D3, etc.).
- Decoupling per sourced BOM: 1 µF on VI (part of C3/C4), 10 µF on VO (part of C5/C6),
  standard LDO practice — place VO cap close to pin 3.
- No EN pin means this LDO is not part of any power-sequencing/enable chain — it powers
  up as soon as USB VBUS is present (through F1/D2).
- **Confidence flag:** input voltage range and dropout numbers are general
  Diodes-Inc-LDO-family knowledge, not pulled from this exact datasheet this session
  (diodes.com blocked automated fetch). Pin table itself is high confidence (from the
  actual KiCad symbol, not from a guess).
