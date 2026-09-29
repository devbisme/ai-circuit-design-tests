# SY6280AAC — 2.4-5.5V 2A High-Side Load Switch (VBUS power path switch, U2)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 |
| Vcc / Vin range | 2.4V – 5.5V |
| Key output spec | RDS(on) 80mΩ, active-high EN, output discharge on disable |
| Max current / power | 2A continuous, adjustable current limit via ISET |
| Operating temp | -40°C to +125°C |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | OUT | Switch output to load |
| 2 | GND | Ground |
| 3 | ISET | Current-limit set (resistor to GND) |
| 4 | EN | Enable, active high |
| 5 | IN | Switch input (VBUS) |

Symbol generated: `symbols/dual_adc_usb.kicad_sym`, part `SY6280AAC` (EXACT match via
find-symbol.py). Pin names/numbers from JLC/EasyEDA pinout data; a downloadable PDF could not
be obtained within the 2-URL budget (both `www.lcsc.com/datasheet/...` and
`datasheet.lcsc.com/lcsc/...` returned anti-bot HTML pages, not the file) — this summary is
built from MCP part data plus the ISET formula recovered via web search below.

## Notes
- **ISET formula (from Silergy's AN_SY6280 application note, cross-checked across multiple
  mirrors):** ILIM(A) = 6800 / R_ISET(Ω). For the architecture's ≈0.8A target:
  R_ISET = 6800/0.8 = 8.5kΩ. Nearest 1% E96 value: **R3 = 8.45kΩ** → ILIM ≈ 0.805A (closest
  standard value below/at target; 8.66kΩ gives 0.785A if a lower limit is preferred). This
  resolves sourcing's `## Next phase must` #4 — R3 should be sourced as 8.45kΩ 1% 0402,
  UNI-ROYAL 0402WGF Basic-tier family to match the rest of the design's passives.
  **Not independently verified against the full datasheet** (PDF unobtainable) — cross-check
  this formula if a PDF becomes available before layout freeze.
- EN is active-high with no internal pulldown noted in MCP data — confirm R1/R2 (5.1kΩ
  pull-downs per `sourced_bom.md`) hold EN low by default until VBUS presence logic drives it.
- Datasheet URL on file (HTML-walled, not downloaded): https://www.lcsc.com/datasheet/lcsc_datasheet_1810121532_Silergy-Corp-SY6280AAC_C55136.pdf
