# KH-BNC50-3511 — Kinghelm BNC White Jack Connector, 12.5mm, Right-Angle THT (J2 ×2)

Source: `datasheets/KH-BNC50-3511.pdf` (Kinghelm mechanical drawing, product no. KH-801-0038
Rev B, 1 page — full mechanical drawing + specifications table, no separate datasheet
document exists for this part beyond this drawing).

| Spec | Value |
|------|-------|
| Package | Right-angle (elbow) THT BNC jack, 12.5mm body, panel/PCB mount via 1/2-28 UNEF-2A threaded bushing |
| Vcc / Vin range | N/A (RF/coax connector) — Working voltage 500V rms @ sea level |
| Key output spec | Impedance 50Ω, frequency range DC–3GHz, VSWR ≤1.3 max |
| Max current / power | Not specified (connector, not power-rated); insulation resistance 5000Ω min |
| Operating temp | –55°C to +155°C |

## Pinout

2-terminal RF connector (signal + ground/shield), no IC-style numbered pinout:

| Pin | Name | Function |
|-----|------|----------|
| — | Center contact | Signal (brass, Au 1µ" plated) |
| — | Body / fixed footrest legs | Ground / shield / mechanical mount (zinc body, iron legs, Ni 80–120µ" plated) |

## Notes

- **Land-pattern confirmation: MISMATCH CONFIRMED, not resolved — closes half of
  `03_sourcing.md` gap item #3 as "checked, found wrong," the other half (corrected
  footprint) is left open, see below.** The datasheet's own "PCB" bottom-view drawing (p.1,
  bottom-right) gives real hole geometry: **2× Ø2.00mm holes spaced 10.1mm apart** (fixed
  footrest/ground legs) plus a smaller hole/pin region called out **"2-0.90"** (Ø0.90mm,
  quantity ambiguous — see below) offset **5.05mm** from the Ø2.00mm row and **2.5mm** from
  centerline, consistent with the connector's 12.5mm body diameter (Ø12.8mm max envelope)
  and right-angle leg layout (body length 35.50mm REF, thread 1/2-28 UNEF-2A). The
  currently-assigned KiCad footprint (`Connector_Coaxial:BNC_Win_364A2x95_Horizontal`) was
  checked directly against `/usr/share/kicad/footprints/Connector_Coaxial.pretty/` — its pads
  sit on a **2.54mm/5.08mm grid with 1.6mm round/oval pads**, nothing close to this part's
  **10.1mm hole spacing / Ø2.00mm+Ø0.90mm holes**. **Confirmed: the assigned footprint does
  not match this part's real land pattern** — do not route/place J2 against it as-is.
- **Not fixed this phase — pin/hole count is ambiguous from this single drawing view at the
  resolution available.** The BOM table (p.1) lists 3 distinct board-contacting items:
  "Center contact" (item 2, brass, the RF signal pin), "Lead" (item 3, iron), and "Fixed
  footrest" (item 4, iron, the mechanical/ground legs) — but the PCB-view callout reads as
  "2-Ø2.00" (2 ground/footrest holes) and "2-0.90" (possibly 2 more holes, possibly 1 with a
  duplicated dimension leader — not cleanly resolvable from the rendered drawing without
  risking a wrong guess). **Rather than build a custom footprint on an ambiguous hole count
  (the exact failure mode this role exists to prevent — a wrong footprint here is a
  mechanical short/no-fit, not a caught ERC error), this is left for the coder/layout stage
  to resolve by either (a) measuring a physical sample, (b) requesting the vendor's DXF, or
  (c) treating the safe minimum as 1× center-signal THT pad (~0.9–1.0mm drill) + 2× Ø2.0mm
  ground/mount THT pads at 10.1mm pitch**, which is consistent with every number actually
  read off the drawing even under the hole-count ambiguity.
- Electrically simple (2-node RF connector, 50Ω/DC–3GHz/VSWR 1.3) — no decoupling or
  application-circuit needed. J2 connects to the `analog_frontend` block per
  `02_architecture.md`/`03_sourcing.md`.
