# RT9013-33GB — 3.3V 500mA fixed LDO (power_tree, U12)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 |
| Vcc / Vin range | Up to 5.5V |
| Key output spec | 3.3V fixed output, 400mV dropout @500mA, PSRR 50dB@10kHz |
| Max current / power | 500mA |
| Operating temp | −40°C to +125°C (TJ) |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | VIN | Input (VBUS_SW) |
| 2 | GND | Ground |
| 3 | EN | Enable, active high |
| 4 | NC | No connect |
| 5 | VOUT | Output (P3V3A — analog rail for AD8066, THS4521, ADS5231 AVDD) |

Pinout via JLC/EasyEDA for this exact LCSC# (C47773); the downloaded datasheet
(`RT9013-33GB.pdf`, Richtek DS9013) has heavy watermark artifacts that make automated text
extraction unreliable, but the fragments recovered (VIN/GND/EN/NC/VOUT names, SOT-23-5
package) are consistent with this pinout and with Richtek's well-established standard
SOT-23-5 pin assignment for this family — no contradiction found.

## Notes
- Sets P3V3A, the low-noise analog rail feeding AD8066 (V+), THS4521 x2 (VS+), and ADS5231
  (AVDD). Keep this rail's local decoupling (C76/C77) close to U12.
- Generated symbol: `dual_adc_usb:RT9013-33GB` in `symbols/dual_adc_usb.kicad_sym` (5 pins,
  `find-symbol.py` reports `EXACT`).
- Datasheet: `datasheets/RT9013-33GB.pdf` (Richtek DS9013).
