# SY8089A1AAC — 2A synchronous buck converter, adjustable (U1)

| Spec | Value |
|------|-------|
| Package | SOT-23-5 |
| Vcc / Vin range | 2.5–5.5V |
| Key output spec | 1.5MHz switching, adjustable output, synchronous rectification |
| Max current / power | 2A output, 50µA quiescent |
| Operating temp | −40°C to +125°C |

## Pinout (SOT-23-5, from EasyEDA/JLC symbol data)

| Pin | Name | Function |
|-----|------|----------|
| 1 | EN | Enable — tie to `+5V_SW` (or a pull-up) for always-on; standard Silergy convention is active high |
| 2 | GND | Ground |
| 3 | LX | Switch node — to inductor L1 |
| 4 | IN | Supply input — from `+5V_SW` |
| 5 | FB | Feedback — external divider (R3–R6 per sourced BOM) sets VOUT for `+3V3_D` |

## Notes

- **Freely substitutable per architecture item 10** — this is not a critical-path part.
- **VFB RESOLVED — architecture revision 2.** `datasheets/SY8089A1AAC.pdf` (Silergy
  AN_SY8089A1) is now on disk. Pin 5's description gives `VOUT = 0.6 x (1 + RH/RL)`, the
  block diagram shows a 0.6 V reference, and the electrical table gives
  **VREF = 591 / 600 / 609 mV** (min/typ/max at IOUT = 0.5 A, CCM) — i.e. 0.600 V +/-1.5%.
  The earlier "0.6 V is an assumption, do not treat as authoritative" flag is **closed**.
- **FB divider as built is correct and must not change**: R4 = 45.3 k (OUT->FB),
  R5 = 10.0 k (FB->GND) -> 0.600 x 5.53 = **3.318 V**, spanning 3.268-3.368 V over VREF
  tolerance alone. Inside the ADC's 3.0-3.6 V and the FPGA's I/O window. The 0.8 V scenario
  that would have produced 4.4 V is ruled out.
- Other verified numbers from the same PDF: Vin 2.5-5.5 V, UVLO 2.5 V (150 mV hyst),
  IQ 50 uA typ / 70 uA max, ISHDN 0.1 uA typ, top/bottom FET RDS(on) 130/85 mOhm,
  LX discharge 50 Ohm, EN active high (VEN,H 1.2 V).
- The LCSC-hosted URL still returns an HTML anti-bot page; the PDF came from the Octopart
  mirror of the Silergy document.
- Output = `+3V3_D`, feeds the digital rail tree per architecture decision 9.
