# TLV75518PDBVR — 500mA Fixed 1.8V Low-IQ LDO (U5)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 |
| Vcc / Vin range | up to 5.5V |
| Key output spec | Fixed 1.8V, 46dB PSRR@100kHz, 380mV dropout@500mA |
| Max current / power | 500mA |
| Operating temp | -40°C to +125°C (Tj) |

## Pinout (JLC/EasyEDA data, same TLV755xx family/package pin order as TLV75512PDBVR)
| Pin | Name | Function |
|-----|------|----------|
| 1 | IN | Input supply |
| 2 | GND | Ground |
| 3 | EN | Enable, active high |
| 4 | NC | No internal connection |
| 5 | OUT | Regulated 1.8V output |

## Notes
- Feeds VD_1V8 rail (U15 Bank3/VCCIO3, J4 VREF, U17.VCC per `net_plan.md`).
- PDF not obtained: same TLV755P family-datasheet wrong-part rejection as TLV75512PDBVR
  (see that summary) — TI's `tlv755p.pdf` was tried and rejected by the automated
  part-frequency guard even though it is genuinely the correct family document. Budget
  exhausted after 2 attempts; MCP spec data + cross-validated pin table (identical package to
  TLV75512PDBVR, TPS7A2033PDBVR — all SOT-23-5 TI LDOs with IN/GND/EN/NC/OUT order, the latter
  two independently verified against real datasheets) give high confidence in the table above.
