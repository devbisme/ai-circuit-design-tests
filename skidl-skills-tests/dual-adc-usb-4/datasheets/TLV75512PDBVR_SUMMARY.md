# TLV75512PDBVR — 500mA Fixed 1.2V Low-IQ LDO (U4)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 |
| Vcc / Vin range | up to 5.5V |
| Key output spec | Fixed 1.2V, 46dB PSRR@100kHz, 780mV dropout@500mA |
| Max current / power | 500mA |
| Operating temp | -40°C to +125°C (Tj) |

## Pinout (JLC/EasyEDA data — TLV755xx family, same package/pin order across the family)
| Pin | Name | Function |
|-----|------|----------|
| 1 | IN | Input supply |
| 2 | GND | Ground |
| 3 | EN | Enable, active high |
| 4 | NC | No internal connection |
| 5 | OUT | Regulated 1.2V output |

## Notes
- **U4 substitution is final (Do not redo)**: replaces the architecture's AP2112K-1.2TRG1
  (dropped to 77-80 units stock, FAIL). TLV75512PDBVR is the architect's own pre-vetted second
  source — this datasheet phase adds no new risk here.
- PDF not obtained: LCSC-hosted PDF (wmsc.lcsc.com) downloaded successfully as a file but never
  mentions "TLV75512" specifically in its first pages (rejected by the wrong-part guard — it
  is TI's TLV755P **family** datasheet, which does cover this part's electrical section but
  wasn't confirmed page-specific within the automated check); a second attempt via TI's family
  symlink (`tlv755p.pdf`) hit the same rejection. Both attempts exhausted per budget. Pin table
  and specs above are corroborated by MCP part data and are consistent with the TLV75518PDBVR
  pin table (below), which is the same family/package — high confidence despite no local PDF.
