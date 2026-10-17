# ADS5231IPAGT - Dual 12-bit 40 MSPS 3.3 V ADC

Texas Instruments, datasheet ADS5231IPAGT.pdf, quality 61

Package: TQFP-64 (PAG), 64 pins, pitch 0.5 mm, thermal pad False

## Absolute maximum (min / typ / max)

- AVDD_max: -0.3 / - / 3.8 V p2
- VDRV_max: -0.3 / - / 3.8 V p2
- AVDD_VDRV_diff: -0.3 / - / 0.3 V (Voltage between AVDD and VDRV) p2
- VAIN: -0.3 / - / 3.3 V (Analog input pins; lower of 3.3 V or AVDD+0.3 V) p2
- TJ_max: - / - / 105 °C p2
- Tstg: -65 / - / 150 °C p2

## Recommended operating (min / typ / max)

- AVDD: 3 / 3.3 / 3.6 V p3
- VDRV: 3 / 3.3 / 3.6 V p3
- fs_pll_disabled: 2e+06 / - / 3e+07 Hz (ADCLK sample rate, PLL disabled) p3
- fs_pll_enabled: 2e+07 / - / 4e+07 Hz (ADCLK sample rate, PLL enabled (default)) p3
- VIL_CLK: - / - / 0.6 V p3
- VIH_CLK: 2.2 / - / - V p3
- TA: -40 / - / 85 °C p3

## Pinout

| Pin | Name | Type | Domain | Function |
|---|---|---|---|---|
| 3,46,57 | AVDD | power_in | AVDD | Analog supply |
| 5,8,40,43 | VDRV | power_in | VDRV | Output buffer supply |
| 2,47,48,49,55,58,59,61,64 | AGND | power_in |  | Analog ground |
| 4,7,23,25,44 | GND | power_in |  | Output buffer ground |
| 50 | INA+ | input |  | Analog input channel A (datasheet: INA) |
| 51 | INA- | input |  | Complementary analog input channel A (datasheet: INA overbar) |
| 63 | INB+ | input |  | Analog input channel B (datasheet: INB) |
| 62 | INB- | input |  | Complementary analog input channel B |
| 52 | CM | output |  | Common-mode voltage output (1.5 V typ) |
| 53 | REFT | bidirectional |  | Top reference/bypass: 2 ohm in series with 0.1 uF to ground |
| 54 | REFB | bidirectional |  | Bottom reference/bypass: 2 ohm in series with 0.1 uF to ground |
| 60 | ISET | passive |  | Bias current setting resistor 56.2 kohm to ground |
| 56 | INT/EXT | input |  | Reference select: 0 = external (default), 1 = internal |
| 24 | CLK | input |  | Clock input (CMOS, single-ended) |
| 1 | SEL | input |  | Serial interface select; 1 = serial enabled; low-going pulse after power-up resets registers |
| 41 | MSBI/SEN | input |  | SEL=0: MSB invert; SEL=1: serial write enable |
| 42 | OEA/SCLK | input |  | SEL=0: output enable A (0=enabled); SEL=1: serial clock |
| 45 | STPD/SDATA | input |  | SEL=0: power-down (1=PD); SEL=1: serial data |
| 6 | OEB | input |  | Output enable channel B (0 = enabled, default) |
| 39 | OVRA | output |  | Over-range channel A |
| 9 | OVRB | output |  | Over-range channel B |
| 26 | DVA | output |  | Data valid channel A |
| 22 | DVB | output |  | Data valid channel B |
| 27 | D0_A | tri_state |  | Data bit D0 channel A (LSB) |
| 28 | D1_A | tri_state |  | Data bit D1 channel A |
| 29 | D2_A | tri_state |  | Data bit D2 channel A |
| 30 | D3_A | tri_state |  | Data bit D3 channel A |
| 31 | D4_A | tri_state |  | Data bit D4 channel A |
| 32 | D5_A | tri_state |  | Data bit D5 channel A |
| 33 | D6_A | tri_state |  | Data bit D6 channel A |
| 34 | D7_A | tri_state |  | Data bit D7 channel A |
| 35 | D8_A | tri_state |  | Data bit D8 channel A |
| 36 | D9_A | tri_state |  | Data bit D9 channel A |
| 37 | D10_A | tri_state |  | Data bit D10 channel A |
| 38 | D11_A | tri_state |  | Data bit D11 channel A (MSB) |
| 10 | D0_B | tri_state |  | Data bit D0 channel B (LSB) |
| 11 | D1_B | tri_state |  | Data bit D1 channel B |
| 12 | D2_B | tri_state |  | Data bit D2 channel B |
| 13 | D3_B | tri_state |  | Data bit D3 channel B |
| 14 | D4_B | tri_state |  | Data bit D4 channel B |
| 15 | D5_B | tri_state |  | Data bit D5 channel B |
| 16 | D6_B | tri_state |  | Data bit D6 channel B |
| 17 | D7_B | tri_state |  | Data bit D7 channel B |
| 18 | D8_B | tri_state |  | Data bit D8 channel B |
| 19 | D9_B | tri_state |  | Data bit D9 channel B |
| 20 | D10_B | tri_state |  | Data bit D10 channel B |
| 21 | D11_B | tri_state |  | Data bit D11 channel B (MSB) |

