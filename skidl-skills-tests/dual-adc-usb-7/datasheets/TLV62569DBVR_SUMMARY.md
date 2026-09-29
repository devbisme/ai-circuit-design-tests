# TLV62569DBVR — 2A synchronous buck converter (power_tree, U10/U11)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 |
| Vcc / Vin range | 2.5–5.5V |
| Key output spec | Adjustable 0.6V–VIN, 1.5MHz PWM switching |
| Max current / power | 2A output |
| Operating temp | −40°C to +125°C (TJ) |

## Pinout
Standard 5-pin adjustable buck: VIN, GND, EN/PG, SW, FB (exact pin-1 location not re-derived
this pass — sourcing's existing symbol `Regulator_Switching:TLV62569DBV` is a confirmed match,
not regenerated).

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Feedback reference voltage VFB | **0.6V nominal (0.588–0.612V range)** | `TLV62569DBVR.pdf` p.4, electrical characteristics table, row "VFB — Feedback regulation voltage" — **verified**. Confirms sourcing's live-stock note and the architecture's assumed 0.6V used to size R72/R73 (3V3D, 180k/40.2k→3.287V) and R74/R75 (1V2, 100k/100k→1.2V). |

## Notes
- Existing symbol used (not regenerated): `Regulator_Switching:TLV62569DBV`.
- U10 sets P3V3D (FPGA VCCIO/VCCX, ADC VDRV, X1 supply); U11 sets P1V2 (FPGA VCC core).
- Datasheet: `datasheets/TLV62569DBVR.pdf` (TI SLVSDG1C).
