# TYPE-C 16PIN 2MD(073) — USB 2.0-only USB-C receptacle (J1)

| Spec | Value |
|------|-------|
| Package | SMD, 16 electrical pads + shield |
| Key spec | USB 2.0 signaling only (no SuperSpeed pairs bonded out) |

## Pinout (16 named pads + shield — from EasyEDA/JLC symbol data, cross-checked pad-by-pad
against the stock KiCad footprint file)

| Pad | Function |
|-----|----------|
| A1, A12, B1, B12 | GND |
| A4, A9, B4, B9 | VBUS |
| A5 | CC1 |
| B5 | CC2 |
| A6 | Dp1 (D+) |
| A7 | Dn1 (D−) |
| B6 | Dp2 (D+, redundant per USB-C flip) |
| B7 | Dn2 (D−, redundant) |
| A8 | SBU1 |
| B8 | SBU2 |
| S1 | Shield (4 mechanical legs, 1 electrical net) |

## Notes

- **Footprint confirmed correct**: `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`
  (the sourced BOM's choice) has exactly 16 named pads — A1,A4,A5,A6,A7,A8,A9,A12,B1,B4,B5,
  B6,B7,B8,B9,B12 — plus a shield pad "S1" (appearing 4 times, one electrical net across 4
  physical legs) and unnamed NPTH mechanical alignment holes. This is a **pin-for-pin match**
  to the MCP pinout data, despite the "-31-" in the KiCad footprint's own name (that refers
  to the manufacturer's part-numbering suffix, not a 31-pad count — verified by direct
  inspection of the `.kicad_mod` file, not assumed).
- **Symbol generated**: `dual_adc_usb:TYPE-C-16PIN-2MD-073` in
  `symbols/dual_adc_usb.kicad_sym` (17/17 pins incl. shield, `find-symbol.py` EXACT).
  Since only USB 2.0 lines are bonded out, D+/D− are electrically doubled on both A/B rows
  (per USB-C's flip-friendliness) — in SKiDL, tie A6+B6 to one net (`USB_DP`) and A7+B7 to
  one net (`USB_DM`), same as the 4 VBUS pads to one `+5V_IN` net and 4 GND pads to `GND`.
- Since this is USB2.0-only, CC1/CC2 (A5/B5) get simple 5.1kΩ pulldowns per architecture
  (R1/R2 in the sourced BOM) — do not wire CC to anything active (no PD controller in this
  design).
- Shield (S1) — tie to `GND` per architecture's single-GND-net decision (12).
