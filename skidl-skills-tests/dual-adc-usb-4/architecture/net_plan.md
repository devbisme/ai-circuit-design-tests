# Net plan — dual_adc_usb

This is the coders' contract. Net names are exact; SKiDL buses `ADC_DA`, `ADC_DB`, `FT_D` expand to
`ADC_DA0…ADC_DA11`, `ADC_DB0…ADC_DB11`, `FT_D0…FT_D7`. "Ref.pin" gives a pin where it is fixed by this
architecture. Otherwise the block coder takes pin numbers from the datasheet summary.
A net marked **[IF]** crosses a block boundary; it is in the manifest signature.
Single ground net `GND` (one solid plane; AGND/DGND pins of every IC go to it).

## 1. Power nets

| Net | Type | Nominal | Connected refs | Notes |
|---|---|---|---|---|
| VBUS | power | 5 V raw | J1.VBUS(A4,A9,B4,B9), U1.VBUS, D1, FB1 | ≤ 10 µF total before U2 (P5) |
| VBUS_F | power | 5 V | FB1, C1 (4.7 µF), C2, U2.IN, U2.EN | block-local |
| **VBUS_SW** [IF] | power | 5 V switched | U2.OUT, C3, U3.IN, C5, U6.IN, U6.EN, C12, FB2, TP1 | soft-started, current-limited |
| **VD_3V3** [IF] | power | 3.3 V digital | U3.OUT, C6, C7, U4.VIN/EN, C8, U5.IN/EN, C10, R5, TP2, U13 (VREGIN, VCCD, VCCIO×3), FB8, U14.VCC, R61–R63, R65, R67, U15 (VCCX/VCCIO0 pins 64/67/78, VCCIO1 pin 58, VCCIO2 pins 23/44), C85–C93, U16.VCC, C96, J5.1 | ≈ 240 mA |
| **VD_1V8** [IF] | power | 1.8 V | U5.OUT, C11, TP3, U15.VCCIO3 (pin 12), C94, C95, R72, R74, J4.1 (VREF), U17.VCC, C97 | bank 3 + internal PSRAM |
| **VD_1V2** [IF] | power | 1.2 V | U4.VOUT, C9, TP4, U15.VCC (pins 1/22/45/66), C80–C84 | FPGA core, ripple ≤ 3 % |
| **VA_3V3** [IF] | power | 3.3 V analog | U6.OUT, C13, TP5, FB5, FB6, FB7, U9/U11 (VS+, PD), C37, C47 | low-noise LDO; FB5 feeds ADC_VDRV so AVDD and VDRV track (ADS5231 abs-max ±0.3 V) |
| **VA_P2V5** [IF] | power | +2.5 V | FB3, C20, TP7, U8/U10 V+, C32, C42, D2.2, D3.2 (clamp cathodes) | |
| **VA_N2V5** [IF] | power | −2.5 V | FB4, C21, TP8, U8/U10 V−, C33, C43, D2.1, D3.1 (clamp anodes) | |
| **GND** [IF] | ground | 0 V | every block; J1 GND pins, J2/J3 shells, U15 EPAD, U7 EP, TP6 | |
| ADC_AVDD | power | 3.3 V | FB6, U12.AVDD (3,46,57), U12.INT/EXT (56), C54–C57 | block-local (adc) |
| ADC_VDRV | power | 3.3 V | FB5 (from VA_3V3), U12.VDRV (5,8,40,43), C58–C62 | block-local (adc); NOT from VD_3V3 |
| OSC_VDD | power | 3.3 V | FB7, X1.VDD, X1.OE, C63, C64 | block-local (sample_clock) |
| CP_VIN | power | 5 V | FB2, C14, C15, U7.VIN, U7.EN+, U7.EN− | block-local (bipolar_supply) |
| VA_P2V5_R / VA_N2V5_R | power | ±2.5 V pre-filter | U7.VOUT+ / U7.VOUT−, R6/R8 (FB dividers), C18 / C19, FB3 / FB4 | block-local |
| FT_VCORE | power | 1.8 V (FT232H internal) | U13.VCORE (38), U13.VCCA (37), decoupling | block-local (usb_bridge) |
| FT_VPHY | power | 3.3 V filtered | FB8, U13.VPHY (3), U13.VPLL (8), decoupling | LC filter per DS_FT232H |

## 2. USB and power entry (block `usb_power_in`)

| Net | Type | Connected refs | Notes |
|---|---|---|---|
| **USB_DP** [IF] | diff-pair + | J1.A6, J1.B6, U1.I/O1 (pins 1 & 6), U13.DP (7) | 90 Ω differential, length-matched |
| **USB_DM** [IF] | diff-pair − | J1.A7, J1.B7, U1.I/O2 (pins 3 & 4), U13.DM (6) | |
| USB_CC1 / USB_CC2 | signal | J1.A5 / J1.B5, R1 / R2 (5.1 kΩ to GND) | UFP sink, default current |
| USB_SHIELD | chassis | J1 shell, R4 (1 MΩ), C4 (4.7 nF 100 V) to GND | |
| SW_ISET | analog | U2.ISET, R3 | R3 sets the limit to ≈ 0.8 A (datasheet formula) |
| — | — | J1.SBU1/SBU2 → NC | |

## 3. Front-end supply (block `bipolar_supply`)

U7 = LM27762: C16 (1 µF) flying cap between CP+ and CP−; C17 (2.2 µF) on the charge-pump output;
R6/R7 set VOUT+ = +2.50 V and R8/R9 set VOUT− = −2.50 V (datasheet feedback equations); nets CP_FBP, CP_FBN,
CP_FLYP, CP_FLYN, CP_NEG are block-local.

## 4. Analog front end (block `analog_front_end`, two identical channels)

Channel A refs are listed; channel B = same topology with J3, R20–R29, C40–C48, VC2, D3, U10, U11
and net prefix `AFE_B_` / `BNC_B` / `AIN_B_`. Offset rule: R(n) → R(n+10), C(n) → C(n+10).

| Net (ch A) | Type | Connected refs | Value / notes |
|---|---|---|---|
| BNC_A | analog in | J2.center, R10, C30, VC1 | the 1 MΩ ∥ ~20 pF input node |
| AFE_A_MID | analog | R10, R11 | R10 = R11 = 453 kΩ 1 % 1206 (≥ 200 V rating; 906 kΩ top) |
| AFE_A_TAP | analog | R11, R12, C30, VC1, C31, D2.3 (common), R13 | R12 = 100 kΩ 0.1 % (ratio 0.0994); C30 = 15 pF C0G ≥ 100 V; VC1 = 2–6 pF trimmer ≥ 100 V; C31 = 160 pF C0G |
| AFE_A_BUFIN | analog | R13, U8.+IN | R13 = 1 kΩ (clamp current limit) |
| AFE_A_BUF | analog | U8.OUT, U8.−IN, R14 | unity-gain buffer, ±2.5 V supply |
| AFE_A_FIP | analog | R14, R16, C34, U9.IN+ | R14 = Rg = 1.10 kΩ 0.1 % from the buffer |
| AFE_A_FIN | analog | R15, R17, C35, U9.IN− | R15 = Rg = 1.10 kΩ 0.1 % to GND |
| AFE_A_FON | analog | U9.OUT−, R16, C34, R19 | R16 = Rf = 1.00 kΩ 0.1 %, C34 = Cf = 22 pF C0G (OUT− → IN+) |
| AFE_A_FOP | analog | U9.OUT+, R17, C35, R18 | R17 = Rf = 1.00 kΩ, C35 = 22 pF (OUT+ → IN−) |
| **AIN_A_P** [IF] | analog diff + | R18, C36, U12.INA (50) | R18 = 49.9 Ω; C36 = 220 pF C0G across the pair |
| **AIN_A_N** [IF] | analog diff − | R19, C36, U12.INA̅ (51) | R19 = 49.9 Ω |
| **AIN_B_P** [IF] | analog diff + | R28, C46, U12.INB (63) | channel B, R28 = 49.9 Ω |
| **AIN_B_N** [IF] | analog diff − | R29, C46, U12.INB̅ (62) | channel B, R29 = 49.9 Ω |
| **ADC_VCM** [IF] | analog ref | U12.CM (52), C52, C53, U9.VOCM, C38, U11.VOCM, C48 | 1.5 V from ADS5231 |

Transfer: ±10 V at BNC → ±0.904 V differential at the ADC (≈ 89.5 % of the 2.02 Vpp FS); clips at ±11.2 V.
Poles: Rf·Cf = 7.2 MHz, (2·49.9 Ω)·220 pF = 7.2 MHz → −3 dB ≈ 4.6 MHz, 2nd order.
Polarity: Rg into IN+, feedback OUT− → IN+, so OUT+/AIN_x_P is in phase with the BNC.
D2 = BAV199: pin 1 (anode) → VA_N2V5, pin 2 (cathode) → VA_P2V5, pin 3 (common) → AFE_A_TAP. [VERIFY pinout]
U8 decoupling C32 (V+), C33 (V−); U9: VS+ = VA_3V3, VS− = GND, PD = VA_3V3 (enabled), C37 on VS+.

## 5. ADC (block `adc`)

| Net | Type | Connected refs | Notes |
|---|---|---|---|
| **ADC_CLK** [IF] | clock | R57, U12.CLK (24), TP9 | 20 MHz, point-to-point |
| ADC_DA_R0…11 | digital | U12.D0_A…D11_A (27…38), RN1–RN3 | block-local, ADC side of 33 Ω arrays |
| ADC_DB_R0…11 | digital | U12.D0_B…D11_B (10…21), RN4–RN6 | block-local |
| **ADC_DA0…ADC_DA11** [IF] | digital out | RN1 (DA0–3), RN2 (DA4–7), RN3 (DA8–11), U15 (pin map §8) | |
| **ADC_DB0…ADC_DB11** [IF] | digital out | RN4 (DB0–3), RN5 (DB4–7), RN6 (DB8–11), U15 | |
| **ADC_OVRA / ADC_OVRB / ADC_DVA** [IF] | digital out | U12.39 / U12.9 / U12.26 via RN7 elements 1/2/3, U15 | RN7 element 4 unused (both ends NC) |
| **ADC_SEL / ADC_SEN / ADC_SCLK / ADC_SDATA** [IF] | digital in | U12.1 / U12.41 / U12.42 / U12.45, R53–R56 (10 kΩ to GND), U15 | pull-downs = parallel mode, PLL on, SOB, outputs on, not powered down |
| ADC_ISET | analog | U12.ISET (60), R50 = 56.2 kΩ 1 % | |
| ADC_REFT / ADC_REFB | analog | U12.53 → R51 (2 Ω) → C50 (0.1 µF); U12.54 → R52 (2 Ω) → C51 (0.1 µF) | per datasheet pin table; nets ADC_REFT_C, ADC_REFB_C between R and C |
| — | — | U12.OEB (6) → GND; U12.DVB (22) → NC; INT/EXT (56) → ADC_AVDD | internal reference |

## 6. Sample clock (block `sample_clock`)

| Net | Type | Connected refs | Notes |
|---|---|---|---|
| OSC_OUT | clock | X1.OUT, R57, R58 | block-local; place R57/R58 at X1 |
| **ADC_CLK** [IF] | clock | R57 (33 Ω), U12.CLK, TP9 | |
| **ADC_CLK_FPGA** [IF] | clock | R58 (33 Ω), U15 pin 35 (GCLKT_4) | the same edge as the ADC; FPGA PLL reference |

## 7. USB bridge (block `usb_bridge`, U13 = FT232HL, sync 245 FIFO)

| Net | Type | Connected refs | Notes |
|---|---|---|---|
| **FT_D0…FT_D7** [IF] | bidir | U13.ADBUS0…7 (13–20), U15 | |
| **FT_RXF_N** [IF] | out | U13.ACBUS0 (21), U15 | |
| **FT_TXE_N** [IF] | out | U13.ACBUS1 (25), U15 | |
| **FT_RD_N** [IF] | in | U13.ACBUS2 (26), U15 | |
| **FT_WR_N** [IF] | in | U13.ACBUS3 (27), U15 | |
| **FT_SIWU_N** [IF] | in | U13.ACBUS4 (28), U15 | |
| FT_CLKOUT_R | clock | U13.ACBUS5 (29), R66 (33 Ω) | block-local |
| **FT_CLKOUT** [IF] | clock | R66, U15 pin 52 (GCLKT_3) | 60 MHz |
| **FT_OE_N** [IF] | in | U13.ACBUS6 (30), U15 | |
| FT_PWRSAV_N | in | U13.ACBUS7/PWRSAV# (31), R67 (10 kΩ to VD_3V3) | must be 1 for normal operation |
| FT_RESET_N | in | U13.RESET# (34), R65 (10 kΩ to VD_3V3), C79 (0.1 µF) | |
| FT_XIN / FT_XOUT | clock | U13.OSCI (1) / OSCO (2), Y1 (12 MHz), C65 / C66 (load caps, per Y1 CL) | |
| FT_REF | analog | U13.REF (5), R64 = 12 kΩ 1 % to GND | |
| FT_EECS / FT_EECLK / FT_EEDATA | digital | U13.45 / 44 / 43, U14 (CS / CLK / DI), R61 / R62 / R63 10 kΩ pull-ups; U14.DO → R60 (2.2 kΩ) → FT_EEDATA | per DS_FT232H pin 43 note |
| — | — | U13.TEST (42) → GND; ACBUS8/9 (32/33) → NC | |

## 8. FPGA (block `fpga_core`, U15 = GW1NR-LV9QN88P) — pin map

Bank voltages are fixed: **bank 1 & 2 = VD_3V3, bank 3 = VD_1V8 (PSRAM)**. Pins may be swapped *within a bank*
at layout, except the GCLK pins (35, 52), which are fixed.

| Bank | Pin → net |
|---|---|
| 2 (3.3 V) | 17 ADC_DA0, 18 ADC_DA1, 19 ADC_DA2, 20 ADC_DA3, 25 ADC_DA4, 26 ADC_DA5, 27 ADC_DA6, 28 ADC_DA7, 29 ADC_DA8, 30 ADC_DA9, 31 ADC_DA10, 32 ADC_DA11, 33 ADC_DB2, 34 ADC_DB3, **35 ADC_CLK_FPGA (GCLKT_4)**, 36 ADC_DB4, 37 ADC_DB5, 38 ADC_DB6, 39 ADC_DB7, 40 ADC_DB8, 41 ADC_DB9, 42 ADC_DB10, 47 ADC_DB11 |
| 1 (3.3 V) | 48 ADC_DB0, 49 ADC_DB1, 50 ADC_OVRB, 51 ADC_OVRA, **52 FT_CLKOUT (GCLKT_3)**, 53 FT_D0, 54 FT_D1, 55 FT_D2, 56 FT_D3, 57 FT_D4, 59 FT_D5, 60 FT_D6, 61 FT_D7, 62 FT_RXF_N, 63 FT_TXE_N, 68 FT_RD_N, 69 FT_WR_N, 70 FT_OE_N, 71 FT_SIWU_N, 72 ADC_DVA, 73 ADC_SEL, 74 ADC_SEN, 75 ADC_SCLK, 76 ADC_SDATA, 77 SPARE_B1 (→ TP10) |
| 3 (1.8 V) | 5 JTAG_TMS, 6 JTAG_TCK, 7 JTAG_TDI, 8 JTAG_TDO, 9 FPGA_RECONFIG_N, 4 FPGA_JTAGSEL_N, 87 FPGA_MODE1, 88 FPGA_MODE0, 79 LED_STAT_1V8, 80 LED_ACT_1V8, 81 TRIG_OUT_1V8, 82 GPIO_OUT_1V8, 83 TRIG_IN_1V8; unused → NC: 3, 10, 11, 13, 14, 15, 16, 84, 85, 86 |
| power | VCC (1, 22, 45, 66) = VD_1V2; VCCIO1 (58) = VD_3V3; VCCIO2 (23, 44) = VD_3V3; VCCX/VCCIO0 (64, 67, 78) = VD_3V3; VCCIO3 (12) = VD_1V8; VSS (2, 21, 24, 43, 46, 65) + EPAD = GND |

| Net | Type | Connected refs | Notes |
|---|---|---|---|
| JTAG_TMS / JTAG_TCK / JTAG_TDI / JTAG_TDO | 1.8 V digital | U15.5/6/7/8, J4 | R73 (4.7 kΩ) TCK → GND [VERIFY UG290] |
| FPGA_RECONFIG_N | 1.8 V | U15.9, R72 (10 kΩ → VD_1V8), J4.6 | |
| FPGA_JTAGSEL_N | 1.8 V | U15.4, R74 (10 kΩ → VD_1V8) | keeps JTAG enabled |
| FPGA_MODE0 / FPGA_MODE1 | 1.8 V | U15.88 / 87, R70 / R71 (4.7 kΩ → GND) | MODE2 = GND internally → MODE[2:0] = 000 = auto-boot from internal flash [VERIFY UG290] |
| SPARE_B1 | 3.3 V digital | U15.77, TP10 | debug/scope-trigger pad |
| J4 pinout | header 1×7 2.54 mm | 1 VD_1V8 (VREF), 2 JTAG_TMS, 3 JTAG_TCK, 4 JTAG_TDO, 5 JTAG_TDI, 6 FPGA_RECONFIG_N, 7 GND | 1.8 V-only; programmer must follow VREF |

Decoupling: C80–C83 (0.1 µF) + C84 (10 µF) on VD_1V2; C85–C87 (0.1 µF) + C88 (10 µF) on VCCX; C89 (0.1 µF) + C90
(4.7 µF) VCCIO1; C91, C92 (0.1 µF) + C93 (4.7 µF) VCCIO2; C94 (0.1 µF) + C95 (4.7 µF) VCCIO3.

## 9. I/O expansion (block `io_expansion`)

| Net | Type | Connected refs | Notes |
|---|---|---|---|
| **LED_STAT_1V8 / LED_ACT_1V8 / TRIG_OUT_1V8 / GPIO_OUT_1V8** [IF] | 1.8 V out | U15.79/80/81/82 → U16.1A/2A/3A/4A | U16 = SN74LV4T125 at VCC = VD_3V3; all 4 OE̅ → GND |
| LED_STAT / LED_ACT | 3.3 V | U16.1Y → R80 (1 kΩ) → LED2 → GND; U16.2Y → R81 → LED3 → GND | nets LED_STAT_K / LED_ACT_K between R and LED anode |
| EXT_TRIG_OUT | 3.3 V | U16.3Y → R82 (100 Ω) → J5.3 | |
| EXT_GPIO_OUT | 3.3 V | U16.4Y → R83 (100 Ω) → J5.4 | |
| EXT_TRIG_IN | input (≤ 5 V) | J5.2, R85 (100 kΩ → GND), R84 (1 kΩ) → U17.A | net EXT_TRIG_IN_R between R84 and U17 |
| **TRIG_IN_1V8** [IF] | 1.8 V in | U17.Y → U15.83 | U17 = SN74LV1T34 at VCC = VD_1V8 (5.5 V-tolerant input) |
| J5 pinout | header 1×6 2.54 mm | 1 VD_3V3, 2 EXT_TRIG_IN, 3 EXT_TRIG_OUT, 4 EXT_GPIO_OUT, 5 GND, 6 GND | |

## 10. Test points

TP1 VBUS_SW, TP2 VD_3V3, TP3 VD_1V8, TP4 VD_1V2, TP5 VA_3V3, TP6 GND, TP7 VA_P2V5, TP8 VA_N2V5, TP9 ADC_CLK, TP10 SPARE_B1.
