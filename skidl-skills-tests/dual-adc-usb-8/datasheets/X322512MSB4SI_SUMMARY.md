# X322512MSB4SI — YXC 12 MHz crystal, 3225 4-pad  [Y1, FT232H clock]

**No datasheet PDF.** LCSC's `lcsc.com/datasheet` links return HTML, and no manufacturer copy was found. Values below come from JLCPCB/LCSC parametric data only.
Symbol: `Device:Crystal` (2-pin; pads 2 and 4 of the 3225 footprint are case/GND by footprint convention). Footprint: `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm`.

| Spec | Value |
|------|-------|
| Frequency | 12.000 MHz |
| Load capacitance CL | 20 pF — **UNVERIFIED** (distributor field; the X3225…"S" code is consistent) |
| ESR | 80 Ω max (distributor) |
| Tolerance / stability | ±10 ppm / ±20 ppm |
| Temp | –40…+85 °C |

## Pinout (KiCad footprint convention for 3225 4-pad crystals — UNVERIFIED for YXC)
| Pin | Name | Function |
|-----|------|----------|
| 1 | X1 | crystal |
| 2 | GND | case |
| 3 | X2 | crystal |
| 4 | GND | case |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| CL | 20 pF → C47 = C48 = 33 pF (2 × (20 – ~3.5 pF stray)) | **UNVERIFIED** — JLC/LCSC parametric field (two distributor sources agree) |
| Pin 1/3 = crystal, 2/4 = case | — | **UNVERIFIED** — footprint convention |
