# BAV99 — Dual small-signal switching diode (SOT-23)

SOURCE: model knowledge (extremely common dual-diode part, multi-sourced by all major
manufacturers). PDF not downloaded this session (deferred — generic jellybean-class
discrete). Pin table below is read directly from the installed KiCad symbol
`Diode:BAV99`, confirmed present in `/usr/share/kicad/symbols/Diode.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | SOT-23 |
| Type | Dual small-signal switching diode |
| Max reverse voltage | 70–100 V class (manufacturer-dependent, not itself re-verified this session) |
| Max forward current | 200 mA class |

## Pinout (from KiCad symbol `Diode:BAV99` — confirmed common-anode configuration)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | K | passive | Cathode of diode 1 |
| 2 | A | passive | Anode — **common to both diodes** |
| 3 | K | passive | Cathode of diode 2 |

**Note the symbol reports pin 2 as the shared Anode** (common-anode configuration: both
diode cathodes point outward to pins 1 and 3, both anodes tied together at pin 2). This
is the actual KiCad symbol's pin typing, read directly — do not assume common-cathode
(some BAV99-family parts/second-sources use common-cathode instead; this symbol's
electrical pin types say common-anode). Confirm against the exact MPN's own datasheet
before finalizing rail connections if the clamp topology depends on polarity (it does,
see Notes).

## Notes

- `D_clamp` in `afe_channel`: input clamp to the ±5 V rails, conducts only beyond
  ≈±100 V (i.e. essentially only in a fault/ESD event, not normal operation) — per
  sourced BOM note.
- `D7` in `fpga_core`: EXT_TRIG input clamp, with 1 kΩ series resistor (R25).
- **Coding-phase action:** because pin 2 is the common anode, the correct dual-rail-clamp
  wiring is: pin 2 (common A) → signal node; pin 1 (K) → the MORE POSITIVE clamp rail
  (conducts when signal exceeds that rail + Vf); pin 3 (K) → the more positive of the
  *other* direction is NOT achievable with a common-anode pair alone for a symmetric
  ±rail clamp — a common-anode BAV99 naturally clamps signal-to-single-rail twice (both
  cathodes to two different positive-going references), not signal between two opposite-
  polarity rails. **Flag for the coder:** verify the actual desired clamp behavior
  (typically: one leg to +5V rail cathode-out, other leg needs the opposite polarity,
  which a common-anode single BAV99 cannot provide symmetrically) against the AFE
  application circuit before wiring — this may need pin 2 to GND/mid-rail with pins 1/3
  to +5V and a *second* diode of opposite orientation for the −5V side, or confirm the
  intended design only clamps positive excursions with this part.
