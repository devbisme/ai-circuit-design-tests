# KH-BNC50-3511 — 50Ω BNC right-angle jack (afe_input, J1/J2)

| Spec | Value |
|------|-------|
| Package | Through-hole, right-angle ("Elbow" style), 9.5mm interface diameter |
| Key spec | 50Ω impedance, 3GHz rated frequency |
| Operating temp | −55°C to +155°C |

## Notes on footprint verification (sourcing flagged this as unverified)
Sourcing assigned `Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal` and asked for
dimensional confirmation against KH-BNC50-3511's own mechanical drawing. **The downloaded
datasheet (`KH-BNC50-3511.pdf`) is almost entirely a mechanical drawing rendered as vector
graphics — pdftotext extracted only two lines of text** ("BNC WHITE JACK CONNECTOR (12.5MM)",
part number reference), no machine-readable pin-spacing dimensions. Reading the drawing visually
was not done this phase (budget). **Carried forward: the coder/reviewer should visually compare
the drawing in `datasheets/KH-BNC50-3511.pdf` against the Amphenol 031-6575 footprint's pad
positions before layout.** Risk is low-to-moderate — right-angle through-hole BNC jacks are
fairly standardized in pin spacing across vendors, but this is not a verified match.
