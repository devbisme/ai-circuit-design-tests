# KH-BNC50-3511 — Right-Angle BNC Jack, 50Ω (analog input connectors, J2/J3)

Datasheet obtained: `datasheets/KH-BNC50-3511.pdf` (Kinghelm mechanical drawing, 1 page,
verified). Custom footprint mechanical dimensions **captured** below (page 1 of 1) —
**the actual `.kicad_mod` footprint file was not built this pass**; that's a phase-5
(coding) task using these dimensions.

Symbol generated: `symbols/dual_adc_usb.kicad_sym:KH-BNC50-3511` (4 pins, EXACT) —
pin 1 = OUT (center signal contact), pins 2-4 = GND (shell/mounting-leg ground return).

| Spec | Value |
|------|-------|
| Package | THT, right-angle (elbow) board-mount BNC jack |
| Vcc / Vin range | N/A (RF connector) |
| Key output spec | 50Ω impedance, DC–3GHz, VSWR ≤1.3 |
| Max current / power | Working voltage 500V rms @ sea level |
| Operating temp | −55°C to +155°C |

## Mechanical dimensions (page 1, drawing KH-801-0038, Rev B)
- Center contact: through-hole, positioned per the front-view drawing.
- Two "fixed footrest" mounting/ground legs (material: Iron), providing mechanical
  retention + shield ground return.
- **PCB pad layout** (bottom-right detail view of the drawing):
  - Center signal pad: Ø0.90mm
  - Two mounting-leg holes: Ø2.00mm each
  - Leg spacing: 10.1mm (horizontal) × 5.05mm (offset), with a 2.5mm sub-offset and
    5.05mm reference dimension — see the drawing's dimensioned bottom-right view for exact
    hole centers.
  - Bushing through-hole: Ø9.5±0.1mm (front panel/bezel clearance, 1/2-28 UNEF-2A thread)
- Overall connector depth: 35.5mm (REF), body width 14.7±0.3mm, height 12.5mm.

## Notes
- Sourcing flagged this as architect-mandated custom footprint (no CSE/manufacturer
  `.kicad_mod` match found). The dimensions above are sufficient to build the footprint in
  phase 5; the coder (or a footprint-generation step) should create 1 round pad (Ø0.90mm,
  signal) + 2 round mounting/ground pads (Ø2.00mm) at the spacing given, plus a mechanical
  keepout for the Ø9.5mm bushing if the panel-mount clearance matters for this design's
  enclosure.
- Same part for J2 (CH1) and J3 (CH2).
