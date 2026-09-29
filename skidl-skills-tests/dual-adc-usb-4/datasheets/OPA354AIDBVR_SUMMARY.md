# OPA354AIDBVR — 100MHz GBW Rail-to-Rail CMOS Op-Amp (U8/U10)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 (DBV) |
| Vcc / Vin range | 2.5V – 5.5V single supply (±1.25V to ±2.75V dual) |
| Key output spec | 100MHz GBW, 150V/µs slew rate, RRIO, 2mV Vos |
| Max current / power | 100mA output, 4.9mA quiescent |
| Operating temp | -40°C to +125°C |

## Pinout (DBV / SOT-23-5 package — VERIFIED against TI SBOS233H Table 5-1)
| Pin | Name | Function |
|-----|------|----------|
| 1 | OUT | Output |
| 2 | V- | Negative (lowest) supply |
| 3 | +IN | Non-inverting input |
| 4 | -IN | Inverting input |
| 5 | V+ | Positive (highest) supply |

Symbol generated: `symbols/dual_adc_usb.kicad_sym`, part `OPA354AIDBVR` (EXACT match).

## Notes
- **Confirms sourcing's flagged risk was a non-issue**: pin order (OUT/V-/IN+/IN-/V+) was
  built from JLC/EasyEDA pinout data and cross-checked against TI's own Figure 5-1 / Table 5-1
  in `datasheets/OPA354AIDBVR.pdf` — **exact match**. This is the standard TI 5-pin SOT-23
  op-amp pinout convention (same as most single TI op-amps in this package), so
  `Amplifier_Operational:OPA356xxDBV` (same family layout) would likely also have worked, but
  the generated symbol is now independently verified and should be used as-is.
- Datasheet: SBOS233H, downloaded to `datasheets/OPA354AIDBVR.pdf`.
- Used in the analog front end per channel; standard non-inverting/inverting gain-stage
  decoupling (0.1µF close to V+/V-) already specified in `sourced_bom.md`.
