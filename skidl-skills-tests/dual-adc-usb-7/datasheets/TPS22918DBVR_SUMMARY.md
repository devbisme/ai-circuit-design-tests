# TPS22918DBVR — 5.5V 2A load switch (power_tree, U9)

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Vcc / Vin range | 1–5.5V |
| Key output spec | RON 53–54mΩ, configurable rise time (CT pin), quick output discharge (QOD pin) |
| Max current / power | 2A continuous |
| Operating temp | −40°C to +105°C |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | VIN | Input (VBUS) |
| 2 | GND | Ground |
| 3 | ON | Control input, active high (R71=100kΩ pull-up to FT_3V3 per net_plan) |
| 4 | CT | Rise-time set (C71=1nF, LS_CT net) |
| 5 | QOD | Quick output discharge (leave per app circuit) |
| 6 | VOUT | Output (VBUS_SW) |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| V_IH (ON pin) | **≥1.0V minimum guaranteed logic-high** (spec range 1V to VIN); V_IL ≤0.5V | `TPS22918DBVR-FULL.pdf` p.4/electrical characteristics table, rows "VIH,ON" and "VIL,ON" — **verified**. Note: the first PDF obtained (`TPS22918DBVR.pdf`) is TI's older "PRODUCT PREVIEW" revision (SLVSD76, Feb 2016) and lacks this numeric table — a second fetch got the current production datasheet, `TPS22918DBVR-FULL.pdf` (SLVSDG1x), which has it. |

## Notes
- `[CRIT]` load switch (sourcing) gating VBUS_SW to the buck regulators and LDO.
- `PWREN_N` from the FT232H (via net_plan) drives Q1's gate, not directly this part's ON pin — confirm the ON-pin drive path against `net_plan.md`'s power-sequencing section before layout.
- Generated symbol: `dual_adc_usb:TPS22918DBVR` in `symbols/dual_adc_usb.kicad_sym` (6 pins, `find-symbol.py` reports `EXACT`).
- Datasheets: `datasheets/TPS22918DBVR.pdf` (preview rev, kept for reference) and `datasheets/TPS22918DBVR-FULL.pdf` (**use this one** — current production rev with the full electrical table).
