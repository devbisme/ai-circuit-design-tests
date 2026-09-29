# TPS22919DCKR — TI 5.5 V 1.5 A 90 mΩ load switch, SC-70-6  [U2]

Source: `datasheets/TPS22919DCKR.pdf` (TI SLVSEN5B). Symbol: generated `dual_adc_usb:TPS22919DCKR`. Footprint: `Package_TO_SOT_SMD:SOT-363_SC-70-6`.

| Spec | Value |
|------|-------|
| VIN | 1.6–5.5 V operating; 6 V abs max (VIN, VOUT, ON, QOD) |
| RON | ≈90 mΩ |
| IMAX | 1.5 A continuous |
| tON / tR (VIN 3.6 V) | 1750 µs / 1100 µs typ (controlled slew) |
| Temp | –40…+125 °C |

## Pinout (p.3)
| Pin | Name | Function |
|-----|------|----------|
| 1 | IN | switch input |
| 2 | GND | ground |
| 3 | ON | active-high enable; do not float. VIH 1.0–5.5 V, VIL ≤ 0.35 V; smart pull-down 530 kΩ when low |
| 4 | NC | leave floating |
| 5 | QOD | quick output discharge. Tie to VOUT for internal 24 Ω, via R for slower, or float to disable |
| 6 | VOUT | switch output |

## Notes
- ON tied to VBUS (4.4–5.25 V) is within VIH 1.0–5.5 V ✓. QOD → V5 (VOUT), as in the net plan ✓.
- VBUS transients above 6 V exceed abs max. U1 USBLC6 on VBUS is the only clamp.
