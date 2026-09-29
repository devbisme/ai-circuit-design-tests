# DSX321G 24MHz — Passive Crystal, FX2 reference clock (Y1)

MCP data only — PDF not fetched this pass (passive 2-terminal crystal, generic symbol
`Device:Crystal` already assigned and correct per `sourced_bom.md`; low marginal value for
a passive part with no pinout ambiguity).

| Spec | Value |
|------|-------|
| Package | SMD3225-4P |
| Key output spec | 24 MHz, ±30 ppm, 12 pF load capacitance |
| Operating temp | not in JLC parametric data |

## Notes
- Load capacitors C92/C93 (12 pF C0G, matching the crystal's 12pF load spec) already
  correctly sized per `sourced_bom.md` — no action needed.
- Drives CY7C68013A's external oscillator input per the `usb_bridge` block.
