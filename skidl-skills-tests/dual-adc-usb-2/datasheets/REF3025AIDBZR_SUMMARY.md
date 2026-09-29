# REF3025AIDBZR — 2.5 V precision voltage reference, 30 ppm/°C (SOT-23-3)

SOURCE: model knowledge (Texas Instruments REF30xx family, common precision bandgap
reference — 30 ppm/°C drift spec already carried in the sourced BOM). PDF not downloaded
this session (deferred). Pin table below is read directly from the installed KiCad
symbol base `Reference_Voltage:REF3012` (which `REF3025` `extends`), confirmed present
in `/usr/share/kicad/symbols/Reference_Voltage.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | SOT-23-3 |
| Output | 2.5 V fixed |
| Initial accuracy | Typically ±0.05%–0.2% class for the "A" grade (family-typical, not independently re-verified this session) |
| Temp drift | 30 ppm/°C (per sourced BOM, matches REF30xx "A" grade) |
| Quiescent current | Low-power class, ~45–65 µA typical for this family |
| No EN pin | 3-pin part — always-on once IN is powered |

## Pinout (from KiCad symbol base `REF3012`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | IN | power in | Input voltage |
| 2 | OUT | power out | Regulated 2.5 V reference output |
| 3 | GND | power in | Ground |

## Notes

- U5 in `power_analog`: sets the AFE level-shift offset. Output (2.5 V) feeds the R7/R8
  precision divider (4.02 kΩ/1.00 kΩ, 0.1%/25 ppm Susumu resistors) to derive the ~0.5 V
  offset-setting node used by the AFE's OPA836 MFB stage (per AD9235 summary's strapping
  section — this 0.5 V node is distinct from the ADC's own VIN− 1.5 V bias, which needs
  its own separate divider off this same REF3025 output).
- Decoupling: small output bypass cap recommended for stability/noise — shares the C14–
  C17 (1 µF) and C18–C21 (100 nF) groups with U3/U4 per sourced BOM. Place the bypass cap
  directly at OUT (pin 2).
- No EN pin — always on once IN is powered from the +5V_A or 3V3_A rail (confirm exact
  source rail at coding time from the `power_analog` net plan).
