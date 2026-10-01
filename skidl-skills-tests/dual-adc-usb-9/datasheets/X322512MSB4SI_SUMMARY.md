# X322512MSB4SI — YXC 12 MHz crystal, 3225 4-pad (summary only, PDF not obtained)

Source: JLC/MCP data only (LCSC C9002).

| Spec | Value |
|------|-------|
| Frequency | 12 MHz |
| Load capacitance CL | 20 pF (MCP) |
| ESR | 80 Ω max (MCP) |
| Tolerance / stability | ±10 ppm / ±20 ppm |

## Pinout (standard 3225-4P; KiCad `Device:Crystal_GND24`)
| Pin | Function |
|-----|----------|
| 1, 3 | crystal |
| 2, 4 | GND (case) |

## Notes
- Load caps: C = 2·(CL − Cstray) ≈ 2·(20 − 4) = 32 pF → **33 pF C0G**, not the BOM's provisional 18 pF. CL is MCP-sourced (UNVERIFIED from YXC PDF).
