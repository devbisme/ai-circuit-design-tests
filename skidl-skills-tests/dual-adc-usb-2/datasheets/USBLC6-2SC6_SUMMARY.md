# USBLC6-2SC6 — Dual-line USB ESD protection array (SOT-23-6)

SOURCE: model knowledge (ST Microelectronics USBLC6-2 family, extremely common USB D+/D−
ESD clamp; PDF not retrieved this session — not attempted, low incremental value versus
the well-known KiCad symbol/pin data below). Pin table below is read directly from the
installed KiCad symbol `Power_Protection:USBLC6-2SC6` (confirmed present in
`/usr/share/kicad/symbols/Power_Protection.kicad_sym`), not from the datasheet — treat
pin names as authoritative since they come from the actual symbol the coder will place.

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Function | Bidirectional TVS array, 2 protected lines + shared VBUS clamp |
| Standoff voltage | 5 V (matched to USB 2.0 D+/D−) |
| Line capacitance | Low (~3.5 pF typ per line) — safe for USB 2.0 HS signal integrity |
| Clamping | Steers ESD strikes on I/O1, I/O2, or VBUS to internal rails |

## Pinout (from KiCad symbol `Power_Protection:USBLC6-2SC6`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | I/O1 | passive | Protected line 1 (D+), dual-bonded with pin 6 |
| 2 | GND | passive | Ground |
| 3 | I/O2 | passive | Protected line 2 (D−), dual-bonded with pin 4 |
| 4 | I/O2 | passive | Protected line 2 (D−), same net as pin 3 |
| 5 | VBUS | passive | VBUS clamp |
| 6 | I/O1 | passive | Protected line 1 (D+), same net as pin 1 |

## Notes

- D1 in `usb_c_input`: pins 1/6 → USB D+ net, pins 3/4 → USB D− net, pin 5 → VBUS
  (post-fuse, pre-connector-side), pin 2 → GND. Place tight to J1 (USB-C receptacle) for
  effective ESD clamping — trace length from the connector matters more than from the
  D+/D− bus.
- No decoupling needed — this is a passive TVS array, not a powered IC.
