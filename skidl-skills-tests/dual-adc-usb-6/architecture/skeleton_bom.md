# Skeleton BOM (dual_adc_usb)

Qty is per board. Passive values marked **[calc]** are load-bearing — they were computed in
`ic_selection.md` and must not be substituted without redoing that arithmetic. Everything
else is a jellybean the part-sourcer may choose freely on stock/price.
All passive values below are real E24/E96 values.

| Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|
| **Analog front end (x2 instances)** |
| Analog input jack | KH-BNC50-3511 (C2837587) | BNC right-angle THT | 2 | **custom footprint needed**; 2nd src DOSIN-801-0050 |
| Attenuator top leg | 909 kΩ 1 % | 0805 | 2 | **[calc]** 0805 for 150 V working; with 90.9 k gives 999.9 kΩ |
| Attenuator bottom leg | 90.9 kΩ 1 % | 0603 | 2 | **[calc]** returns to `VREF_OFF`, not GND |
| Compensation cap, top | 22 pF C0G 100 V | 0603 | 2 | **[calc]** sets Cin = 20.0 pF; C0G mandatory |
| Compensation cap, bottom | 220 pF C0G | 0603 | 2 | **[calc]** τ match 20.0 µs both legs |
| Clamp series resistor | 1.00 kΩ 1 % | 0603 | 2 | limits clamp current to 35 µA at ±50 V |
| Input clamp diode | BAV199LT1G | SOT-23 | 2 | dual, 1 nA leakage — leakage is signal error here |
| Input ESD diode (rev.2) | **ESD9L5.0ST5G** (onsemi, C82326) — 2nd source MSKSEMI C7379964, same land pattern | **SOD-923** | 2 | <!-- revised: was ESD9B5.0ST5G/SOD-523 on the BNC node --> **Moved to `CHn_BUFIN`, not `CHn_BNC`.** Cj = **0.9 pF** max, Vrwm 5 V, VBR 5.4 V min, unidirectional (K→BUFIN, A→GND), IEC 61000-4-2 rated. The rev.1 part's real Cj is **15 pF**, not the 0.5 pF the BOM claimed; 15 pF on a 1 kΩ-driven node puts the chain's −3 dB at 3.83 MHz worst case and fails F8. Do **not** substitute a part with Cj > 2 pF. |
| Buffer + 2 filter amps | TPH2501-TR (C126713) | SOT-23-5 | 6 | RRIO **and** ≤1 pA bias are both mandatory |
| SK section A resistors | 147 Ω 1 % | 0402 | 4 | **[calc]** f0 4.443 MHz |
| SK section A caps | 270 pF / 220 pF C0G 5 % | 0603 | 2 + 2 | **[calc]** Q = 0.554 |
| SK section B resistors | 137 Ω 1 % | 0402 | 4 | **[calc]** f0 4.454 MHz |
| SK section B caps | 680 pF / 100 pF C0G 5 % | 0603 | 2 + 2 | **[calc]** Q = 1.304 |
| ADC driver (FDA) | THS4521IDR (C16092) | SOIC-8 | 2 | KiCad symbol: `Amplifier_Difference:THS4521ID` |
| FDA gain network | 1.00 kΩ / 1.10 kΩ 1 % | 0402 | 4 + 4 | **[calc]** G = 1.1 -> exactly 2 Vpp diff at FS |
| ADC kickback resistors | 33 Ω 1 % | 0402 | 4 | **[calc]** τ = 1.45 ns ≪ 50 ns track window |
| ADC kickback cap | 22 pF C0G | 0402 | 2 | **[calc]** differential, across VIN+/VIN− |
| **ADC (x2 instances)** |
| 12-bit ADC | AD9237BCPZ-40 (C514275) | LFCSP-32 5x5 | 2 | 211 in stock — **thin**; 2nd src AD9235BCPZ-40 (C653327, 139) |
| ADC decoupling | 100 nF X7R | 0402 | 12 | one per AVDD/DRVDD pin |
| ADC bulk / REFT / REFB | 10 µF X5R 6.3 V | 0805 | 6 | |
| **Clocking** |
| Sample-clock oscillator | SX3M10.000B10F20TNN (C5452682) | SMD3225-4P | 1 | 10.000 MHz, ±10 ppm, 3.3 V CMOS; **jitter spec unverified** |
| Clock isolation buffer | SN74LVC1G17DBVR | SOT-23-5 | 1 | FPGA leg only; ADC leg stays raw |
| Clock series terminations | 33 Ω / 100 Ω | 0402 | 3 | 33 Ω to ADCs, 100 Ω to buffer, 33 Ω buffer out |
| **FPGA** |
| FPGA | XC6SLX9-2TQG144C (C27408) | LQFP-144 | 1 | 102 I/O, 86 used; **custom symbol needed** |
| Config flash | W25Q32JVSSIQ | SOIC-8 | 1 | SPI master mode, M[1:0] = 01 |
| JTAG header | 2x3 1.27 mm SMD header | SMD | 1 | |
| Status LEDs + resistors | green/red 0603 + 1.0 kΩ | 0603 | 2 + 2 | |
| FPGA decoupling | 100 nF X7R / 4.7 µF X5R | 0402 / 0805 | 20 / 4 | one 100 nF per VCC pin pair |
| **Buffer memory** |
| SDRAM | W9825G6KH-6I (C97572) | TSOP-54 | 1 | 32 MB, x16, 166 MHz; **custom symbol needed** |
| SDRAM clock termination | 22 Ω | 0402 | 1 | |
| SDRAM decoupling | 100 nF X7R / 10 µF X5R | 0402 / 0805 | 8 / 1 | |
| **USB bridge** |
| USB 2.0 HS bridge | CY7C68013A-56LTXC (C14912) | QFN-56 8x8 | 1 | symbol `MCU_Cypress:CY7C68013A-56LTX` (PREFIX — verify package) |
| Bridge crystal | 24.000 MHz, 12 pF load | SMD3225 | 1 | + 2 x 12 pF C0G |
| Config EEPROM | 24LC64-I/SN | SOIC-8 | 1 | I2C, 2 x 2.2 kΩ pull-ups |
| Bridge decoupling | 100 nF X7R / 10 µF | 0402 / 0805 | 10 / 1 | |
| **USB front / power** |
| USB-C receptacle | TYPE-C 16PIN 2MD(073) (C2765186) | SMD 16P | 1 | USB 2.0 only; D+/D− doubled on A6/B6, A7/B7 |
| CC pulldowns | 5.1 kΩ 1 % | 0402 | 2 | **[calc]** sink-only, no CC sensing — P3 does not fire |
| USB ESD array | USBLC6-2SC6 | SOT-23-6 | 1 | symbol EXACT |
| Soft-start load switch | TPS22919DCKR (C2149796) | SC-70-6 | 1 | 118 mA inrush into 47 µF; 2nd src TPS22810DBVR |
| VBUS input cap | 10 µF X5R 10 V | 0805 | 1 | **USB 2.0 caps the unswitched VBUS bypass at 10 µF** |
| Bulk cap (switched) | 22 µF X5R 10 V | 0805 | 2 | 47 µF total, downstream of the load switch |
| Buck regulators | SY8089AAC (C5187495) | SOT-23-5 | 2 | 2.7–5.5 V in; **custom symbol needed** |
| Buck inductors | 2.2 µH, ≥1 A, shielded | 0630 / 4x4 mm | 2 | ripple 0.51 A p-p on the 3.3 V rail, 2.9 mV out |
| +3V3D feedback divider | 45.3 kΩ / 10.0 kΩ 1 % | 0402 | 1 + 1 | **[calc]** top=45.3 k (VOUT->FB), bottom=10.0 k (FB->GND) -> 3.318 V |
| +1V2 feedback divider | 10.0 kΩ / 10.0 kΩ 1 % | 0402 | 1 + 1 | **[calc]** -> 1.200 V |
| Buck output caps | 22 µF X5R 10 V | 0805 | 4 | |
| Analog LDOs | TPS73633DBVR (C28038) | SOT-23-5 | 2 | fixed 3.3 V, 30 µVrms |
| LDO in/out caps + noise-reduction | 1 µF / 10 µF X7R | 0603 / 0805 | 6 | |
| VREF_OFF divider | 10.0 kΩ / 12.1 kΩ 1 % | 0402 | 1 + 1 | **[calc]** -> 1.8068 V, RC-filtered 29 Hz |
| VCM_REF divider | 10.0 kΩ / 10.0 kΩ 1 % | 0402 | 2 | -> 1.650 V for both THS4521 VOCM pins |
| Reference filter caps | 1 µF X7R | 0603 | 2 | |
| Reference buffer | SGM8521XN5/TR or any µA RRIO single | SOT-23-5 | 1 | DC only — sourcer's choice |
| Buck EN sequencing RC | 100 kΩ + 100 nF | 0402 | 1 + 1 | **[calc]** 2.74 ms delay so +1V2 leads +3V3D |
| Ferrite beads (rail isolation) | 600 Ω @100 MHz, 1 A | 0603 | 4 | |

Approximate part count: **~230 placements, ~45 unique line items.**
Estimated BOM at qty 10: ICs ≈ ¥150 (~US$21) + connectors ≈ ¥2.1 + passives/magnetics
≈ US$8 -> **well under the US$100/board target (R2)**.
