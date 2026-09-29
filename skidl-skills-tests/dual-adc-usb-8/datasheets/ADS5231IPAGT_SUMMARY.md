# ADS5231IPAGT — dual 12-bit 40 MSPS pipeline ADC (TI)  [KEYSTONE, U8]

Source: `datasheets/ADS5231IPAGT.pdf` = TI SBAS295A (Jul 2004, rev Jan 2007), read in full for the rows below.
Symbol: generated `dual_adc_usb:ADS5231IPAGT` (64 pins, names exactly as the datasheet pin table). Footprint: `Package_QFP:TQFP-64_10x10mm_P0.5mm`.

| Spec | Value |
|------|-------|
| Package | TQFP-64 (PAG), 10×10 mm, 0.5 mm pitch |
| AVDD / VDRV | 3.0–3.6 V (3.3 typ); abs max 3.8 V; **\|AVDD–VDRV\| ≤ 0.3 V abs max** |
| Sample rate | **20–40 MSPS PLL on (default)**; 2–30 MSPS PLL off |
| Clock | CMOS, VIH ≥ 2.2 V, VIL ≤ 0.6 V; duty 45–55 % (PLL on) |
| Power (int. ref) | AVDD 235.5 typ / 271 max mW; VDRV 85.5 / 109 mW; total 321 / 380 mW |
| Operating temp | –40…+85 °C; TJ max 105 °C; θJA 42.8 °C/W |

## Pinout (p.11–12)
| Pin | Name | Function |
|-----|------|----------|
| 2, 47, 48, 49, 55, 58, 59, 61, 64 | AGND | analog ground |
| 3, 46, 57 | AVDD | analog supply |
| 4, 7, 23, 25, 44 | GND | output-buffer ground |
| 5, 8, 40, 43 | VDRV | output-buffer supply |
| 1 | SEL | 0 = parallel-pin mode (41/42/45 = MSBI/OEA/STPD) |
| 6 | OEB | 0 = ch B outputs enabled (default) |
| 9 / 39 | OVRB / OVRA | over-range out |
| 10…21 | D0_B…D11_B | ch B data, D0 = LSB (pin 10), D11 = MSB (pin 21) |
| 22 / 26 | DVB / DVA | data-valid outputs |
| 24 | CLK | clock input |
| 27…38 | D0_A…D11_A | ch A data, D0 = LSB (pin 27), D11 = MSB (pin 38) |
| 41 | MSBI/SEN | SEL=0: 0 = straight offset binary (default), 1 = 2's complement |
| 42 | OEA/SCLK | SEL=0: 0 = ch A outputs enabled |
| 45 | STPD/SDATA | SEL=0: 0 = normal, 1 = power-down |
| 50 / 51 | INA / ~{INA} | ch A input / complementary input |
| 63 / 62 | INB / ~{INB} | ch B input / complementary input |
| 52 | CM | common-mode voltage out |
| 53 / 54 | REFT / REFB | reference bypass: 2 Ω in series with 0.1 µF to ground each |
| 56 | INT/EXT | 0 = external ref (default), **1 = internal** |
| 60 | ISET | 56.2 kΩ to ground |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Minimum sample rate, PLL on | 20 MSPS | p.3 ROC — **verified** |
| CLK VIH / VIL | ≥2.2 V / ≤0.6 V | p.3 and p.4 — **verified** |
| Clock duty cycle | 45–55 % (PLL on) | p.3 — **verified** |
| \|AVDD – VDRV\| abs max | ±0.3 V | p.2 — **verified** |
| Analog input abs max | –0.3 V to min(3.3 V, AVDD+0.3 V); add ≥25 Ω series if input can exceed 3.3 V | p.2 note 2 — **verified** (the 49.9 Ω R110/R111 satisfy this) |
| VCM (CM pin) | 1.4 / 1.5 / 1.6 V, ±2 mA drive for ±50 mV | p.4 — **verified** |
| Input common-mode range | VCM ±50 mV | p.3 — **verified** |
| Internal REFT / REFB | 2.0 V / 1.0 V (±0.1) | p.4 — **verified** |
| Aperture jitter | 1.0 ps rms typ | p.6 timing — **verified** |
| Output timing, 40 MSPS PLL on | setup t1 ≥ 3.7 ns and hold t2 ≥ 11.5 ns (both vs DV); latency 6 clocks; DV duty 30–55 % | p.6 — **verified** |
| Digital out VOH / VOL | ≥2.4 V / ≤0.4 V at 50 µA | p.5 — **verified** |
| Control pins' internal pull-downs | default states (SEL, OE, MSBI, STPD = 0) come from internal pull-downs | p.23 text — **verified** |
| Power-down with clock running | 83 mW | p.4 — **verified** |

## Notes
- Tie SEL, MSBI/SEN, OEA/SCLK and OEB to GND explicitly. Do not rely on the internal pull-downs.
- VDRV must track AVDD within 0.3 V at all times, so feed it from V3V3A through FB1. FB1's DCR is 0.2 Ω, so 33 mA gives a 6.6 mV drop.
- In SKiDL, reference the complementary inputs by pin number (51, 62) or by the literal names `~{INA}` / `~{INB}`.
