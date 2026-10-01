# ADS5231IPAGT — TI dual 12-bit 40 MSPS pipeline ADC, parallel CMOS outputs, TQFP-64

Source: `ADS5231IPAGT.pdf` (SBAS295A, Jan 2007).

| Spec | Value |
|------|-------|
| Package | TQFP-64 10x10 mm (PAG) |
| AVDD / VDRV | 3.0–3.6 V each (|AVDD−VDRV| ≤ 0.3 V abs max) |
| Sample rate | PLL enabled (default): 20–40 MSPS; PLL disabled: 2–30 MSPS |
| Full scale | 2 Vpp differential, VCM = 1.5 V (CM pin, ±2 mA) |
| Power | VDRV 85.5 mW typ; Iq total ≈ 97 mA (MCP) |
| Temp | −40…+85 °C |

## Pinout (SKiDL names = symbol `dual_adc_usb:ADS5231IPAGT`)
| Pin | Name | Function |
|-----|------|----------|
| 1 | SEL | 0 = parallel pin mode; 1 = serial; low pulse resets serial regs |
| 2,47,48,49,55,58,59,61,64 | AGND | analog ground |
| 3,46,57 | AVDD | analog supply |
| 4,7,23,25,44 | GND | output-buffer ground |
| 5,8,40,43 | VDRV | output-buffer supply |
| 6 | OEB | ch B output enable, 0 = enabled |
| 9 / 39 | OVRB / OVRA | over-range |
| 10–21 | D0_B … D11_B | ch B data, D0 LSB (10), D11 MSB (21) |
| 22 / 26 | DVB / DVA | data valid |
| 24 | CLK | clock input |
| 27–38 | D0_A … D11_A | ch A data, D0 LSB (27), D11 MSB (38) |
| 41 | MSBI/SEN | SEL=0: 0 = offset binary (default) |
| 42 | OEA/SCLK | SEL=0: OEA, 0 = enabled |
| 45 | STPD/SDATA | SEL=0: STPD, 0 = normal |
| 50 / 51 | INA / ~{INA} | ch A input / complement |
| 52 | CM | common-mode output 1.5 V |
| 53 / 54 | REFT / REFB | reference bypass |
| 56 | INT/~{EXT} | 0 = external ref (DEFAULT); **force high for internal** |
| 60 | ISET | 56.2 kΩ to GND |
| 62 / 63 | ~{INB} / INB | ch B complement / input |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| REFT/REFB network (K9) | each pin → **2 Ω series → 0.1 µF ‖ 2.2 µF to GND** (caps on far side of 2 Ω) | Fig. 21 p.19 + pin table p.12 ("2 Ω in series with 0.1 µF") — **verified** |
| Internal ref selection | INT/EXT pin 56 high (tie to AVDD) | p.12, p.19 — **verified** |
| Internal VREFT / VREFB | 2.0 V (1.9–2.1) / 1.0 V (0.9–1.1) | elec. table p.4 — **verified** |
| ISET | 56.2 kΩ to GND (5 % acceptable) | p.19 — **verified** |
| Min clock | 20 MSPS with PLL enabled (default) | rec. op. cond. p.3 — **verified** |
| VDRV range | 3.0–3.6 V (outputs cannot run at 1.8 V) | p.3 — **verified** |
| Serial interface | SEL needs a low pulse after power-up only if serial mode used | p.12 — **verified** |
