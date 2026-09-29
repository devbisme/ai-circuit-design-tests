# X322512MSB4SI — 12.000 MHz crystal, ±30 ppm (3225, 4-pad)

SOURCE: model knowledge (common 3225 SMD crystal part-numbering convention). PDF not
downloaded this session (deferred — generic passive crystal). Pin table below is read
directly from the installed KiCad symbol `Device:Crystal`, confirmed present in
`/usr/share/kicad/symbols/Device.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | 3225 (3.2×2.5 mm) SMD, 4-pad (2 electrical + 2 case/ground pads) |
| Frequency | 12.000 MHz |
| Frequency tolerance | ±30 ppm (per sourced BOM) |
| Load capacitance (C_L) | Not independently confirmed this session — the sourced BOM's 27 pF load-cap choice (C25/C26) is consistent with an ~18–20 pF C_L crystal (standard formula: C_load,external ≈ 2×(C_L − C_stray), C_stray ≈ 3–5 pF board parasitic) |

## Pinout (from KiCad symbol `Device:Crystal`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | 1 | passive | Crystal terminal 1 |
| 2 | 2 | passive | Crystal terminal 2 |

(The 3225 package's other 2 physical pads are case-ground, typically tied to GND on the
footprint but not separately modeled as symbol pins.)

## Notes

- Y1 in `usb_bridge`: drives FT232H's crystal oscillator pins (XCSI/XCSO, pins 1/2) —
  sets the USB-side clock only; the ADC/FPGA sample-clock domain has its own independent
  10 MHz XO (X1) per architecture, deliberately not shared with this crystal.
- Load caps C25/C26 (27 pF C0G ±5%, per sourced BOM) — **verify this crystal's actual
  C_L spec against its real datasheet before finalizing**; 27 pF is a reasonable estimate
  but was not independently confirmed against this exact MPN's datasheet this session.
