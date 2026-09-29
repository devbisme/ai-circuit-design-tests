# STC3MA06-T1 — 2-6pF ceramic trimmer capacitor (C_top1/C_top2)

| Spec | Value |
|------|-------|
| Package | SMD, 4.5×3.2mm body, 1.5mm max seated height |
| Vcc / Vin range | N/A (passive); rated 100VDC, 220VDC withstand |
| Key spec | 2.0pF min – 6.0pF (+50/-0%) max, NP0±200ppm/°C |
| Max current / power | Q ≥500 @1MHz |
| Operating temp | −25°C to +85°C |

## Mechanical drawing — custom footprint generated (page 2 of `datasheets/STC3MA06-T1.pdf`,
"3. DIMENSIONS, PCB LAND PATTERNS", read visually since dimension numbers are embedded in a
vector diagram, not the PDF text layer)

**This part is a 2-terminal trimmer** (confirmed: part-numbering diagram + electrical table
both describe a single variable capacitance between 2 terminals; adjustment is via a
screwdriver slot on top, not a separate pin).

Measured from the manufacturer's own land-pattern drawing:
- Body: 4.50×3.20mm, 1.50mm max seated height (matches the JLC parametric spec exactly).
- **2 rectangular SMD pads, ~1.40×1.30mm each**, symmetric about the part center, pad
  envelope ~5.10mm wide × 2.60mm tall overall (pad centers at ±1.85mm from part center on
  the long axis).

**Custom footprint generated**: `footprints/Capacitor_Trimmer_SEHWA.pretty/
C_Trimmer_SEHWA_STC3MA-2Pin_4.5x3.2mm.kicad_mod` — use in SKiDL as
`footprint='Capacitor_Trimmer_SEHWA:C_Trimmer_SEHWA_STC3MA-2Pin_4.5x3.2mm'`. This closes the
sourcing-flagged `⚠️ CUSTOM FP NEEDED` item; the sourcer's candidate
(`Capacitor_SMD:C_Trimmer_Murata_TZB4-A`) is no longer needed as a fallback but is a
reasonable sanity-check reference if the generated footprint looks off during layout review.
Pad dimensions were read off the datasheet's printed drawing (not a caliper measurement of a
physical part) — spot-check against a physical sample before final production panelization.

This is a 2-pin part electrically — no symbol generation needed, use KiCad's generic
`Device:C_Trimmer` (2-pin variable capacitor symbol).

## Notes

- **Per architecture decision 10 and sourcing decision 5, this part must stay a trimmer** —
  it compensates ~7pF of unpredictable stray capacitance in the attenuator's bottom leg.
  Do not substitute a fixed capacitor to close out the footprint uncertainty; that would
  reopen the analog design risk (R-2), not just a sourcing convenience.
- Target capacitance ≈4.7pF sits mid-range of the 2–6pF trim range (sourcing's own
  calculation, unchanged).
- Datasheet PDF: `datasheets/STC3MA06-T1.pdf` (SEHWA, verified correct part — STC3MA06 6pF
  variant explicitly called out in the electrical spec table, TABLE-1, "STC3MA06 6pf" column).
