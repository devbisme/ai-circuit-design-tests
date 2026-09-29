# TYPE-C 16PIN 2MD(073) — USB-C Receptacle, USB 2.0-only (J1)

Datasheet obtained: `datasheets/TYPE-C-16PIN-2MD-073.pdf` (Shenzhen Shou Han "Specification
for Approval," 6 pages, verified — cover page confirms exact part number match). Page 6
has the mechanical outline + "RECOMMENDED PCB LAYOUT (TOP VIEW)" pad drawing + pin
assignment table.

| Spec | Value |
|------|-------|
| Package | SMD, right-angle, 16-pin |
| Vcc / Vin range | 5V, 3A rating |
| Key output spec | USB 2.0 only (Dp1/Dn1/Dp2/Dn2 present, no SuperSpeed TX/RX pairs — matches the 16-pin/USB2.0-only footprint choice) |
| Max current / power | 3A per VBUS pin group |
| Operating temp | −25°C to +85°C |

## Pinout (from datasheet page 6 pin-assignment table, matches `jlc_get_pinout` exactly)
| Pin | Name | Pin | Name |
|---|---|---|---|
| A1/B12 | GND | B1/A12 | GND |
| A4/B9 | VBUS | B4/A9 | VBUS |
| A5 | CC1 | B5 | CC2 |
| A6 | Dp1 | B6 | Dp2 |
| A7 | Dn1 | B7 | Dn2 |
| A8 | SBU1 | B8 | SBU2 |
| 13, 14 | EH (shield/mounting tabs) | | |

## Notes — mechanical footprint verification (RESOLVED 2026-09-22)

**CORRECTION — the earlier note in this file was wrong.** It read the drawing's callouts
as "mounting-tab holes Ø1.70mm(2x)/Ø1.80mm(2x)/Ø1.40mm(2x)", i.e. round holes. They are
not round. 1.70 and 1.40 are the *lengths of 0.60-wide plated oval slots*, and 2.10/1.80
are the corresponding pad lengths. Only the two Ø0.65 locating holes are round, and those
are NPTH. A downstream sourcing pass repeated the "round holes" reading from this file;
that claim is retracted here so it does not mislead a layout reviewer again.

- Page 6 geometry was extracted from the drawing's vector paths (`pdftocairo -svg`, per-path
  transforms applied), not from the text layer, which carries no dimensions. Scale 10.49
  pt/mm confirmed from three independent baselines agreeing to 0.2%; every derived number
  reproduces a dimensioned callout to <=0.02 mm.
- **The pad-by-pad comparison against the generic `Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A`
  has now been done.** All X coordinates are identical (contacts at +/-0.25/0.75/1.25/1.75/
  2.4/3.2, NPTH at +/-2.89, slots at +/-4.32) and, referenced to the inner pad edge, so are
  all Y. Exactly two real differences:
    1. **Rear shield slot: generic drills 0.6 x 1.2 mm, this part needs 0.6 x 1.4 mm.**
       The rear mounting tabs are 0.2 mm too long for the generic slot -- a genuine
       mechanical interference, and the reason the generic was replaced.
    2. Contact pads: generic 1.3 mm long, manufacturer recommends 1.15 mm. Benign.
  The earlier "oval slots at different offsets" concern was mistaken -- the offsets match.
- **Resolved by** `footprints/ProjectLocal.pretty/USB_C_Receptacle_TYPE-C-16P-2MD073.kicad_mod`,
  now referenced by `circuits/dual_adc_usb/usb_front.py`. All 17 symbol pin numbers have a
  matching pad; stacked pads share nets (GND, VBUS) so they cannot short.
- Still not encoded, and left to layout: paste apertures (drawing specifies none; paste is
  1:1 with copper), solder-mask expansion, thermal relief on the plated slots, and any
  board-edge overhang -- the side view governs that and this footprint does not carry it.
- Pin function assignments are standard and match `jlc_get_pinout` exactly — no pinout risk,
  only a mechanical (mounting-hole placement) risk remains.
