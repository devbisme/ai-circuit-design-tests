# ADS5231IPAGT — Dual 12-Bit 20-40MSPS Pipeline ADC (U12)

| Spec | Value |
|------|-------|
| Package | TQFP-64 (10x10mm, 0.5mm pitch) |
| Vcc / Vin range | AVDD/DVDD 3.0V – 3.6V |
| Key output spec | 12-bit, 70.7dB SNR, 0.4LSB INL, dual simultaneous-sampling channels |
| Max current / power | Iq 97.3mA, sampling rate up to 40MHz |
| Operating temp | -40°C to +85°C |

## Pinout (64 pins — VERIFIED: JLC/EasyEDA pin table spot-checked against TI SBAS295A p.10
"PIN CONFIGURATION" Top View diagram; pins 1-7, 42-48, and 64 all matched exactly)
| Pin | Name | Function | Pin | Name | Function |
|-----|------|----------|-----|------|----------|
| 1 | SEL | Channel/mode select | 33 | D6_A | Channel A data bit 6 |
| 2 | AGND | Analog ground | 34 | D7_A | Channel A data bit 7 |
| 3 | AVDD | Analog supply | 35 | D8_A | Channel A data bit 8 |
| 4 | GND | Digital ground | 36 | D9_A | Channel A data bit 9 |
| 5 | VDRV | Digital output driver supply | 37 | D10_A | Channel A data bit 10 |
| 6 | OEB# | Output enable, active low | 38 | D11_A(MSB) | Channel A data bit 11 (MSB) |
| 7 | GND | Digital ground | 39 | OVRA | Channel A overrange flag |
| 8 | VDRV | Digital output driver supply | 40 | VDRV | Digital output driver supply |
| 9 | OVRB | Channel B overrange flag | 41 | MSBI/SEN | Mode select / serial enable |
| 10 | D0_B(LSB) | Channel B data bit 0 (LSB) | 42 | OEA#/SCLK | Output enable A / serial clock |
| 11 | D1_B | Channel B data bit 1 | 43 | VDRV | Digital output driver supply |
| 12 | D2_B | Channel B data bit 2 | 44 | GND | Digital ground |
| 13 | D3_B | Channel B data bit 3 | 45 | STPD/SDATA | Standby / serial data |
| 14 | D4_B | Channel B data bit 4 | 46 | AVDD | Analog supply |
| 15 | D5_B | Channel B data bit 5 | 47 | AGND | Analog ground |
| 16 | D6_B | Channel B data bit 6 | 48 | AGND | Analog ground |
| 17 | D7_B | Channel B data bit 7 | 49 | AGND | Analog ground |
| 18 | D8_B | Channel B data bit 8 | 50 | INA+ | Channel A analog input + |
| 19 | D9_B | Channel B data bit 9 | 51 | INA- | Channel A analog input - |
| 20 | D10_B | Channel B data bit 10 | 52 | CM | Common-mode reference |
| 21 | D11_B(MSB) | Channel B data bit 11 (MSB) | 53 | REFT | Top reference |
| 22 | DVB | Channel B digital supply | 54 | REFB | Bottom reference |
| 23 | GND | Digital ground | 55 | AGND | Analog ground |
| 24 | CLK | Sample clock input | 56 | INT/EXT# | Internal/external reference select |
| 25 | GND | Digital ground | 57 | AVDD | Analog supply |
| 26 | DVA | Channel A digital supply | 58 | AGND | Analog ground |
| 27 | D0_A(LSB) | Channel A data bit 0 (LSB) | 59 | AGND | Analog ground |
| 28 | D1_A | Channel A data bit 1 | 60 | ISET | Bias current set resistor |
| 29 | D2_A | Channel A data bit 2 | 61 | AGND | Analog ground |
| 30 | D3_A | Channel A data bit 3 | 62 | INB- | Channel B analog input - |
| 31 | D4_A | Channel A data bit 4 | 63 | INB+ | Channel B analog input + |
| 32 | D5_A | Channel A data bit 5 | 64 | AGND | Analog ground |

Symbol generated: `symbols/dual_adc_usb.kicad_sym`, part `ADS5231IPAGT` (EXACT match, 64 pins
verified with `find-symbol.py`).

## Notes
- **CP, single-source, WARN stock (160 units)** — buy full 10-board qty now per architecture
  instruction #6 (unchanged from sourcing).
- Full-scale/ISET current-set resistor is R50 = 56.2kΩ 1% (already sourced). REFT/REFB
  external components R51/R52 (2Ω 1%) already sourced per `sourced_bom.md`.
- SEL, INT/EXT#, MSBI/SEN, OEA#/SCLK, STPD/SDATA are mode/config pins with datasheet-defined
  strapping — see application figure (Fig. 12, per sourcing's original reference) before tying
  these to fixed levels.
- Datasheet: SBAS295A (TI, July 2004, rev Jan 2007), downloaded to
  `datasheets/ADS5231IPAGT.pdf`.
