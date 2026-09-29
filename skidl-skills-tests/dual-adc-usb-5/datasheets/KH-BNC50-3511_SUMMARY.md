# KH-BNC50-3511 — Board-side elbow BNC jack, 50Ω (J2/J3)

| Spec | Value |
|------|-------|
| Package | Through-hole, board-side elbow |
| Key spec | 50Ω impedance, DC–3GHz, VSWR ≤1.3 |
| Rating | 500V rms @ sea level, insulation resistance ≥5000Ω |
| Operating temp | −55°C to +155°C |

## Footprint mismatch — do not use the sourcer's candidate footprint (resolved by direct
inspection, not just "unconfirmed")

Sourcing flagged `Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal` as "the closest stocked
match, not verified." **Direct inspection of both the stock KiCad footprint file and the
Kinghelm mechanical drawing (`datasheets/KH-BNC50-3511.pdf`, page 1) shows they are for
different pin structures:**

- **Stock KiCad footprint** (`BNC_Amphenol_031-6575_Horizontal.kicad_mod`): 4 numbered
  through-hole pads (drill 0.89mm) + 2 unnumbered mechanical mounting pads (oval, drill
  2.01mm).
- **KH-BNC50-3511 mechanical drawing**: a 3-terminal part — 1 center RF signal pin, plus 2
  ground/mounting legs at **⌀2.00mm** holes, with the signal pin offset from that pair by
  roughly 5.05mm/2.5mm per the drawing's dimension callouts (see below); a secondary "2-Ø0.90"
  callout on the same drawing suggests possibly 2 additional thinner pins, which if present
  would make it a 5-hole part closer in count to the Amphenol footprint's pattern — **this
  detail could not be disambiguated from the 2D drawing with full confidence.**

**The 2.00mm and 0.90mm hole sizes are suspiciously close to the Amphenol footprint's
2.01mm/0.89mm drills** (within tolerance), which argues the two parts may share a common
mechanical family — but the Amphenol footprint's pad *count* (4 numbered + 2 mechanical)
does not obviously match a straightforward 1-signal + 2-ground reading of the Kinghelm
drawing. **This is not resolved with full confidence — treat it as a real open risk, not a
confirmed-safe reuse.**

## Recommendation for the coder / layout reviewer

1. Before placing J2/J3, re-open `datasheets/KH-BNC50-3511.pdf` page 1 and compare the
   PCB-side hole pattern (bottom-right sub-drawing, labeled with "2-Ø2.00", "2-Ø0.90",
   "10.1", "5.05", "2.5") directly against
   `/usr/share/kicad/footprints/Connector_Coaxial.pretty/BNC_Amphenol_031-6575_Horizontal.kicad_mod`
   pad-by-pad (`(pad "1" ...)` through `(pad "4" ...)` plus the 2 unnumbered oval pads).
2. If they don't align, generate a custom footprint with `scripts/generate-footprint.py`
   using: body panel bushing ⌀9.5±0.1mm, overall footprint envelope ~14.7×12.5mm, mounting
   thread 1/2-28 UNEF-2A (panel-mount side, not PCB-side — doesn't affect the PCB footprint).
3. This is a board-edge part with **no room for a footprint mismatch to be fixed later**
   (sourcing's own words) — do not skip this check.

## Notes

- Symbol: generic connector symbol is fine (`Connector_Generic:Conn_01x03` sized to 3 pins,
  or a purpose-built 3-pin symbol) — this is a simple passive RF jack, no active pin functions
  to get wrong beyond the mechanical footprint above.
- Datasheet PDF: `datasheets/KH-BNC50-3511.pdf` (Kinghelm mechanical drawing KH-801-0038,
  verified — no numeric MPN stem to auto-check against, confirmed by visual inspection
  instead).
