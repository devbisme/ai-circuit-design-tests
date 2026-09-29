# XKB U262-16XN-4BVC11 — USB-C receptacle, USB 2.0-only, 16-pin SMD

SOURCE: model knowledge (generic USB-C receptacle pinout is standardized by the USB-C
spec regardless of manufacturer for the USB-2.0-only 16-pin variant) + the installed
KiCad symbol `Connector:USB_C_Receptacle_USB2.0_16P`, confirmed present in
`/usr/share/kicad/symbols/Connector.kicad_sym` — **pin table below is read directly from
that symbol, high confidence.** PDF/mechanical drawing not downloaded this session
(XKB Enterprise's own site was not queried — deferred; the sourcing handoff flagged this
part as "mechanically critical, unresolved... verify against a real part in hand before
layout," which this summary cannot substitute for).

| Spec | Value |
|------|-------|
| Package | SMD, 16-pin, USB 2.0-only receptacle (no SuperSpeed pins — matches the "USB 2.0 only" architecture requirement) |
| KiCad footprint | `Connector_USB.pretty:USB_C_Receptacle_XKB_U262-16XN-4BVC11` (confirmed present by sourcing) |
| Mounting | SMD receptacle, through-hole mechanical retention shield legs typical for this part class (not independently confirmed — verify against the real part) |

## Pinout (16-pin USB2.0-only variant, from KiCad symbol
`Connector:USB_C_Receptacle_USB2.0_16P`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| A1 | GND | passive | Ground |
| A4 | VBUS | passive | Bus power |
| A5 | CC1 | bidir | Configuration channel 1 — pull-down R1 (5.1 kΩ) per sourced BOM |
| A6 | D+ | bidir | USB D+ |
| A7 | D− | bidir | USB D− |
| A8 | SBU1 | bidir | Sideband use 1 (unused, USB2.0-only application — leave NC or per J1 footprint's own recommendation) |
| A9 | VBUS | passive | Bus power |
| A12 | GND | passive | Ground |
| B1 | GND | passive | Ground |
| B4 | VBUS | passive | Bus power |
| B5 | CC2 | bidir | Configuration channel 2 — pull-down R2 (5.1 kΩ) per sourced BOM |
| B6 | D+ | bidir | USB D+ (ties to A6, same net — USB-C's flip tolerance) |
| B7 | D− | bidir | USB D− (ties to A7, same net) |
| B8 | SBU2 | bidir | Sideband use 2 (unused) |
| B9 | VBUS | passive | Bus power |
| B12 | GND | passive | Ground |
| S1 | SHIELD | passive | Cable shield / chassis — ties through R3 (1 MΩ bleed) and C2 (4.7 nF/2 kV) to GND, per sourced BOM's single-point chassis tie |

## Notes

- J1 in `usb_c_input`. Both D+ pins (A6/B6) tie to one net, both D− pins (A7/B7) tie to
  one net (USB-C's orientation-flip redundancy) — do not treat A6/B6 or A7/B7 as separate
  signals.
- CC1/CC2 each need their own independent 5.1 kΩ pull-down (R1, R2) — this is the fixed
  USB-C sink advertisement per `[FIXED]` in the sourced BOM. Do not tie CC1/CC2 together.
- **Mechanically critical, unresolved (carried forward from sourcing):** this connector
  sits on the panel edge. The architect's original MPN suffix (`U262-161N-4BVC11`) had no
  matching footprint; the sourcing phase substituted `U262-16XN-4BVC11` on
  footprint-file-existence grounds alone, not a verified mechanical drawing. **Verify the
  physical part in hand against the KiCad footprint before layout — no mechanical
  dimension drawing was obtained in either the sourcing or datasheet phase.**
