# OT252020MJBA4SL — 20MHz XO — **replaces X1 (SX3M20.000B10F20TNN)**

| Spec | Value |
|------|-------|
| Package | SMD2520-4P (2.5×2.0mm) |
| Vcc / Vin range | 1.8–3.3V (wide voltage) |
| Key output spec | CMOS, **Phase Jitter [12kHz–20MHz] = 0.7 ps Max** |
| Max current / power | 4 mA @1.8V / up to 12mA@3.3V for 41-54MHz band (this part is 20MHz: ≤4mA typ) |
| Operating temp | −40°C to +85°C |

## Why this part

Architecture R-4 requires ADC clock jitter ≤5 ps RMS for F11/F14 to hold. The originally
sourced X1 (SX3M20.000B10F20TNN) has no published jitter spec at all (see its summary).
**This part (YXC brand, `datasheets/OT252020MJBA4SL.pdf` page 1, symbol `tpj`) specifies
0.7 ps RMS max over 12kHz–20MHz — 7× margin under budget.** This was the sourcing-flagged
"vetted second source" (LCSC C669067); the datasheet-phase check confirmed it should be used
in preference to the originally sourced part per architecture's own pre-authorized fallback
rule ("confirm ≤5ps or substitute the vetted second source if it does not").

## Pinout (4-pin, confirmed from manufacturer's own "Pin Assignments" diagram, page 2)

| Pin | Name | Function |
|-----|------|----------|
| 1 | Tri-state | Output enable: **High or floating = enabled (70% VDD min)**, Low = disabled (30% VDD max, high-Z output) |
| 2 | GND | Ground |
| 3 | OUT | CMOS clock output — drive `ADC_CLK` net |
| 4 | VDD | Supply, 1.8–3.3V — tie to `+3V3_A` |

## Notes

- **Symbol generated**: `dual_adc_usb:OT252020MJBA4SL` in `symbols/dual_adc_usb.kicad_sym`
  (4/4 pins, `find-symbol.py` EXACT).
- **Footprint**: use `Oscillator:Oscillator_SMD_Kyocera_KC2520Z-4Pin_2.5x2.0mm` (confirmed
  present in the stock KiCad library; `Oscillator_SMD_ECS_2520MV-xxx-xx-4Pin_2.5x2.0mm` is an
  equally valid alternate if pad shape needs adjusting for JLC assembly).
- **BOM update needed**: replace X1 = SX3M20.000B10F20TNN (C5452685) with X1 =
  OT252020MJBA4SL (C669067) in `sourcing/sourced_bom.md`'s `clock_20m` block. Price impact is
  trivial ($0.47→$0.56 typical unit price at low qty). Stock 7,835 at sourcing-run time,
  clears the >100 floor easily.
- Tri-state pin (pin 1) should be tied high or left open per the design (always-enabled
  output) — do not leave adjacent to a floating trace with no defined pull if noise
  immunity matters; a direct tie to `+3V3_A` or a pull-up is the safer choice.
- Datasheet PDF: `datasheets/OT252020MJBA4SL.pdf` (YXC "YSO110TR Wide Voltage" family sheet,
  covers this exact 2.5×2.0mm/20MHz configuration).
