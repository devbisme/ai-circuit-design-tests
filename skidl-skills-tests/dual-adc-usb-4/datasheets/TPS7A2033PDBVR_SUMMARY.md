# TPS7A2033PDBVR — 300mA Fixed 3.3V Low-Noise LDO (U6)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 (DBV) |
| Vcc / Vin range | 1.6V – 6.0V |
| Key output spec | Fixed 3.3V, 10µVrms noise, 65dB PSRR@100kHz |
| Max current / power | 300mA |
| Operating temp | -40°C to +125°C (Tj) |

## Pinout (DBV / SOT-23-5 package — VERIFIED against TI SBVS338H p.4 Pin Functions table)
| Pin | Name | Function |
|-----|------|----------|
| 1 | IN | Input supply |
| 2 | GND | Common ground |
| 3 | EN | Enable, active high (500kΩ internal pulldown, off by default) |
| 4 | N/C | No internal electrical connection |
| 5 | OUT | Regulated 3.3V output |

Symbol generated: `symbols/dual_adc_usb.kicad_sym`, part `TPS7A2033PDBVR` (EXACT match).

## Notes
- **This confirms sourcing's flagged risk was a non-issue for this design's symbol**: the
  generated symbol's pin order (IN/GND/EN/NC/OUT) was built from JLC/EasyEDA pinout data and
  is now cross-checked page-for-page against TI's own DBV (SOT-23-5) pin table in
  `datasheets/TPS7A2033PDBVR.pdf` p.4 — **exact match, no correction needed**. Do **not** reuse
  the library's existing `TPS7A20xxxDQN` (X2SON-5) symbol — its pin order differs (OUT=1,
  GND=2, EN=3, IN=4, Thermal Pad=5), confirmed by the same table.
- Datasheet: SBVS338H, TI, downloaded to `datasheets/TPS7A2033PDBVR.pdf`.
- EN has an internal 500kΩ pulldown — safe to leave floating if always-on is acceptable, but
  the architecture's decision to drive EN explicitly should be followed.
- Standard TI LDO application circuit: input/output ceramic caps per `sourced_bom.md` (already
  specified, no change needed).
