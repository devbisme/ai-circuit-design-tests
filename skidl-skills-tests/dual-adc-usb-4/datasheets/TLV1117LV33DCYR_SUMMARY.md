# TLV1117LV33DCYR — 1A Fixed 3.3V LDO, genuine TI (U3)

| Spec | Value |
|------|-------|
| Package | SOT-223 (SOT-223-3_TabPin2 footprint) |
| Vcc / Vin range | up to 5.5V |
| Key output spec | Fixed 3.3V, 65dB PSRR@1kHz, 455mV dropout @1A |
| Max current / power | 1A |
| Operating temp | -40°C to +125°C (Tj) |

## Pinout (SOT-223, JLC/EasyEDA data)
| Pin | Name | Function |
|-----|------|----------|
| 1 | GND | Ground |
| 2 | OUT | Regulated 3.3V output |
| 3 | IN | Input supply |
| 4 | OUT | Tab, same net as pin 2 (matches footprint name `SOT-223-3_TabPin2`) |

## Notes
- **Genuine TI part, confirmed 455mV@1A dropout** — matches the sourcing decision to reject
  the cheaper JSMSEMI clone (1.2V@1A dropout, fails the architecture's ≤0.6V requirement to
  clear the 4.4V VBUS corner). No further action needed; this is a **Do not redo** item per
  sourcing.
- Datasheet: TI datasheet for TLV1117LV, downloaded to `datasheets/TLV1117LV33DCYR.pdf`
  (fetched from TI's own symlink after the LCSC-hosted URL was blocked).
- Standard LDO application circuit: input/output capacitors per `sourced_bom.md` (10µF class
  already specified — TLV1117LV needs no minimum load, unlike some 1117 variants).
