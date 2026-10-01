# TPS22918DBVR — TI 5.5 V 2 A 52 mΩ load switch, SOT-23-6

Source: `TPS22918DBVR.pdf` (SLVSD76, 2016–2017).

| Spec | Value |
|------|-------|
| VIN | 1–5.5 V |
| RON | 52 mΩ typ @5 V |
| IMAX | 2 A |
| ON thresholds | VIH 1.0 V min, VIL 0.5 V max (VIN 1–5.5 V); hysteresis 107 mV; ION leak 0.1 µA |
| Timing (VIN 5 V, CT 1000 pF) | tON 1950 µs, tR 2540 µs, tOFF 2 µs |
| Temp | −40…+105 °C |

## Pinout (symbol `dual_adc_usb:TPS22918DBVR`)
| Pin | Name | Function |
|-----|------|----------|
| 1 | VIN | switch input, bypass cap to GND |
| 2 | GND | ground |
| 3 | ON | active-high, do not float |
| 4 | CT | rise-time cap to GND (may float) |
| 5 | QOD | quick output discharge: tie to VOUT (internal R), via R, or float = disabled |
| 6 | VOUT | switch output |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| ON polarity / thresholds | active high; VIH ≥1.0 V, VIL ≤0.5 V | Pin Functions p.3, elec. table — **verified** |
| Rise time with CT = 1000 pF | 2540 µs @VIN 5 V | Switching table — **verified** |
