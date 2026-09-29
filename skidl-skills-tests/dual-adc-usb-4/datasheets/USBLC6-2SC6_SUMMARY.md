# USBLC6-2SC6 — USB 2.0 Dual-Line ESD Protection Array (U1)

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Vcc / Vin range | N/A (passive TVS array), Vrwm 5V |
| Key output spec | Clamping 15V, 6A Ipp@8/20µs, 0.35/0.8pF junction cap (low-cap for Hi-Speed USB) |
| Max current / power | 150W Ppp @8/20µs |
| Operating temp | not separately given; standard commercial |

## Pinout (JLC/EasyEDA data — matches existing matched symbol `Power_Protection:USBLC6-2SC6`)
| Pin | Name | Function |
|-----|------|----------|
| 1 | I/O1 | Protected line 1 (D-) |
| 2 | GND | Ground |
| 3 | I/O2 | Protected line 2 (D+) |
| 4 | I/O2 | Protected line 2 (D+), duplicate pin |
| 5 | VBUS | Protected VBUS line |
| 6 | I/O1 | Protected line 1 (D-), duplicate pin |

## Notes
- Symbol already matched in `sourced_bom.md` (`Power_Protection:USBLC6-2SC6`) — no generation
  needed, this summary is for pin-function reference only.
- PDF not obtained: both LCSC-hosted URLs returned anti-bot HTML and the ST manufacturer URL
  timed out, exhausting the 2-attempt budget. MCP spec data above is comprehensive enough for
  placement/decoupling purposes (this is a standard, widely-used USB ESD array with a
  well-established pinout, independently corroborated by the matched KiCad symbol already in
  the system library).
- Standard usage: I/O1→D-, I/O2→D+, VBUS→VBUS, GND→GND, each pin pair diode-clamped to VBUS
  and GND internally.
