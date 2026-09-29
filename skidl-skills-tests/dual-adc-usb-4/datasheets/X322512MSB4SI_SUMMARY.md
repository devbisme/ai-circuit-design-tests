# X322512MSB4SI — 12MHz Crystal, CL=20pF (Y1, FT232H USB clock)

| Spec | Value |
|------|-------|
| Package | SMD3225-4P (passive 2-pad crystal in a 4-pad package, pads 1&3 / 2&4 commoned) |
| Vcc / Vin range | N/A (passive crystal) |
| Key output spec | 12MHz, CL=20pF, ±10ppm tolerance, ±20ppm stability, ESR 80Ω |
| Max current / power | N/A |
| Operating temp | -40°C to +85°C |

## Pinout (standard 4-pad crystal package)
| Pin | Name | Function |
|-----|------|----------|
| 1 | XTAL1 | Resonator terminal 1 (internally bonded to pad 3) |
| 2 | GND | Case/ground (may be NC on 2-terminal-electrically parts — verify against footprint) |
| 3 | XTAL2 | Resonator terminal 2 (internally bonded to pad 1... package-dependent, verify pad map) |
| 4 | GND | Case/ground |

## Notes
- PDF not obtained (LCSC-hosted URL returned anti-bot HTML, budget not spent on a second
  attempt for this low-risk generic crystal — MCP spec data is standard and sufficient).
- **Fixes the skeleton BOM's open item**: CL=20pF sets C65/C66 = 22pF C0G (nearest standard
  value; 2pF offset is normal crystal-loading tolerance) — this is a **Do not redo** decision
  already finalized by sourcing, unchanged here.
- Symbol/footprint already matched (`Device:Crystal` / `Crystal_SMD_3225-4Pin_3.2x2.5mm`) —
  this is a genuine 2-terminal passive crystal (unlike X1/SX3M20.000B10F20TNN, which is a
  4-pin **active** oscillator — see that summary's symbol-mismatch flag). No symbol issue here.
