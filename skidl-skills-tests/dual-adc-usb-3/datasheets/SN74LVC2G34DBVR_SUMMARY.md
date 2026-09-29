# SN74LVC2G34DBVR — Dual Single-Ended Buffer/Driver, SOT-23-6

Source: `datasheets/SN74LVC2G34DBVR.txt` (TI datasheet, already extracted).

| Spec | Value |
|------|-------|
| Package | SOT-23-6 (DBV), 2.90mm × 1.60mm |
| Vcc / Vin range | 1.65V–5.5V — architecture uses `+3V3` |
| Key output spec | Y = A (non-inverting buffer), inputs accept up to 5.5V regardless of VCC |
| Max current / power | Standard CMOS logic-buffer drive; not the binding spec here |
| Operating temp | Not extracted from this excerpt |

## Pinout (SOT-23-6, Top View)

| Pin | Name | Function |
|-----|------|----------|
| 1 | 1A | Buffer Input 1 |
| 2 | GND | Ground |
| 3 | 2A | Buffer Input 2 |
| 4 | 2Y | Buffer Output 2 |
| 5 | VCC | Supply |
| 6 | 1Y | Buffer Output 1 |

## Notes

- Architecture uses this as the dual-fanout buffer for the SiT1602 10.000MHz XO output,
  feeding `CLK_ADC1` and `CLK_ADC2` to the two AD9235 dice from **one die** — this is what
  guarantees clock skew between the two ADC clocks (Decision 8, F10). Wire the XO output to
  **both** 1A and 2A (tied together), outputs 1Y → CLK_ADC1, 2Y → CLK_ADC2.
- Standard 0.1µF decoupling on VCC (pin 5) to GND (pin 2) — no special requirement called out.
