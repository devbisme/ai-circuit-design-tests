# Net plan — dual_adc_usb (revision 1)

This is the coders' contract. Net names are exact: use them verbatim. Refs are defined in
`handoffs/02_architecture.md` § Parts by block. There is a single ground net, `GND`, with no AGND/DGND split.
Pin numbers given here come from datasheets read in phase 2 (ADS5231 SBAS295A; GW1NR-9 UG803). Any pin
marked *(verify)* must be confirmed in phase 4 before it is coded.

## 1. Interface nets (cross block boundaries)

| Net | Type | Connected refs (block) |
|---|---|---|
| GND | ground | every block |
| V5 | power 5 V (switched VBUS, 4.40–5.25 V) | U2.VOUT, C2, C3 (usb_power_in); U3, U4, C4, C6 (power_digital); U6, U7, C10, C13 (power_analog) |
| V3V3D | power 3.315 V digital | U3/L1 output, C5, R3 (power_digital); U5.IN, U5.EN, D1/R7; U9 VCCX/VCCIO0/1/2, J5 (fpga); U10 VCCIO/VPHY/VPLL/VREGIN, U11 (usb_bridge) |
| V1V2 | power 1.200 V FPGA core | U4/L2, C7, R5 (power_digital); U9.VCC ×4 (fpga) |
| V1V8 | power 1.8 V PSRAM bank | U5.OUT, C9 (power_digital); U9.VCCIO3, R20, J4.VREF (fpga) |
| V3V3A | power 3.3 V analog | U6.OUT, C11, C12 (power_analog); U8.AVDD, U8.INT/EXT, FB1 (adc); U102/U202 VS+ and PD, C111/C112, C211/C212 (afe_ch_a/b); FB2 (clock) |
| VP_AFE | power +3.288 V buffer rail | U7.OUT+, C16, R8 (power_analog); U101/U201 V+, D101/D201 pin 2, C106/C206 (afe) |
| VN_AFE | power −2.012 V buffer rail | U7.OUT−, C17, R10 (power_analog); U101/U201 V−, D101/D201 pin 1, C107/C207 (afe) |
| VCM | analog 1.5 V reference (ADC CM out) | U8.CM (pin 52), C20, C21 (adc); U102.VOCM, C114 (afe_ch_a); U202.VOCM, C214 (afe_ch_b) |
| AIN_A_P | analog diff + | R110, C113 (afe_ch_a); U8.INA (pin 50) (adc) |
| AIN_A_N | analog diff − | R111, C113 (afe_ch_a); U8.INA̅ (pin 51) (adc) |
| AIN_B_P | analog diff + | R210, C213 (afe_ch_b); U8.INB (pin 63) (adc) |
| AIN_B_N | analog diff − | R211, C213 (afe_ch_b); U8.INB̅ (pin 62) (adc) |
| ADC_CLK | clock 40 MHz 3.3 V CMOS | R16 (clock); U8.CLK (pin 24) (adc) |
| FPGA_CLK | clock 40 MHz 3.3 V CMOS | R17 (clock); U9 GCLKT_4 = pin 35, bank 2 (fpga) |
| DA0…DA11 (bus `da`) | digital out 3.3 V | U8 D0_A…D11_A = pins 27…38 (adc); U9 bank 1/2 I/O (fpga) |
| DB0…DB11 (bus `db`) | digital out 3.3 V | U8 D0_B…D11_B = pins 10…21 (adc); U9 bank 1/2 I/O (fpga) |
| ADC_DVA | digital out 3.3 V (data-valid A) | U8.DVA (pin 26) (adc); U9 I/O (fpga) |
| ADC_STPD | digital in 3.3 V, high = power-down | U8.STPD/SDATA (pin 45), R15 10k to GND (adc); U9 I/O (fpga) |
| FT_D0…FT_D7 (bus `ft_d`) | bidir 3.3 V | U10 ADBUS0…7 (usb_bridge); U9 bank 1 I/O (fpga) |
| FT_RXF_N | out from U10 (ACBUS0) | U10, U9 |
| FT_TXE_N | out from U10 (ACBUS1) | U10, U9 |
| FT_RD_N | in to U10 (ACBUS2) | U10, U9 |
| FT_WR_N | in to U10 (ACBUS3) | U10, U9 |
| FT_SIWU_N | in to U10 (ACBUS4) | U10, U9 |
| FT_CLKOUT | clock 60 MHz out of U10 (ACBUS5) | U10, U9 GCLKT_3 bank 1 *(verify pin 52)* |
| FT_OE_N | in to U10 (ACBUS6) | U10, U9 |
| USB_DP | USB 2.0 HS D+ (90 Ω diff) | J1 A6+B6, U1 (usb_power_in); U10.DP (usb_bridge) |
| USB_DN | USB 2.0 HS D− (90 Ω diff) | J1 A7+B7, U1 (usb_power_in); U10.DM (usb_bridge) |

## 2. Internal nets by block

### usb_power_in
| Net | Type | Refs |
|---|---|---|
| VBUS | power 4.40–5.25 V (raw) | J1 A4/B4/A9/B9, U1.VBUS, C1 (4.7 µF — keeps pre-switch capacitance < 10 µF), U2.VIN, U2.ON |
| CC1 / CC2 | Type-C config | J1.A5 → R1 5.1 kΩ → GND; J1.B5 → R2 5.1 kΩ → GND (Rd = sink, default USB power) |
| — | | J1 shell, A1/B1/A12/B12 → GND; SBU1/SBU2 no-connect; U2.QOD → V5 |

U2.ON is tied straight to VBUS. On: VBUS 4.40–5.25 V → it is ≥ VIH 1.0 V and ≤ 5.5 V abs → on. Off: not required (the board is dead without VBUS).

### power_digital
| Net | Type | Refs |
|---|---|---|
| SW33 | switch node | U3.SW, L1 (2.2 µH) |
| FB33 | feedback | U3.FB; R3 100 kΩ (top, to V3V3D); R4 22.1 kΩ (bottom, to GND) |
| SW12 | switch node | U4.SW, L2 (2.2 µH) |
| FB12 | feedback | U4.FB; R5 100 kΩ (top, to V1V2); R6 100 kΩ (bottom, to GND) |
| PWR_LED | LED | V3V3D → R7 1 kΩ → D1 anode; D1 cathode → GND (1.3 mA) |

- U3/U4.EN → V5. On: V5 ≥ 4.40 V against VIH ≤ 1.2 V. VIN range 2.5–5.5 V is fine.
- V3V3D: 0.6 × (1 + 100/22.1) → 3.315 V. The VFB spread 0.588–0.612 V plus 1 % resistors gives 3.196–3.437 V.
- V1V2: 0.6 × (1 + 100/100) → 1.200 V. With the same tolerances that is 1.164–1.236 V, inside the GW1NR VCC window of 1.14–1.26 V.
- U5 (TLV75518P): IN and EN → V3V3D. EN = 3.2 V against VHI ≥ 1 V → on. OUT → V1V8, a fixed 1.8 V part that needs no divider.

### power_analog
| Net | Type | Refs |
|---|---|---|
| LM_C1P / LM_C1N | flying cap | U7.C1+ / C1−, C14 1 µF |
| LM_CP | charge-pump out | U7.CP, C15 4.7 µF → GND |
| LM_FBP | feedback + | U7.FB+; R8 174 kΩ (top, to VP_AFE); R9 100 kΩ (bottom, to GND) |
| LM_FBN | feedback − | U7.FB−; R10 64.9 kΩ (top, to VN_AFE); R11 100 kΩ (bottom, to GND) |

- U6 (TPS7A2033, fixed 3.3 V): IN and EN → V5, OUT → V3V3A, with C10 1 µF in, C11 1 µF out and C12 10 µF.
- U7 (LM27762): VIN, EN+ and EN− → V5. On: 4.40 V ≥ VIH 1.2 V. PGOOD → GND, as the datasheet directs when it is unused. Thermal pad → GND.
- VP_AFE = 1.2 × (174 + 100)/100 → **3.288 V**. VFB+ 1.182–1.218 V plus 1 % resistors gives 3.198–3.380 V. R9 = 100 kΩ ≥ 50 kΩ ✓.
- VN_AFE = −1.22 × (64.9 + 100)/100 → **−2.012 V**. The spread is −1.967 to −2.058 V. R11 = 100 kΩ ≥ 50 kΩ ✓.
- OPA356 total supply: 3.380 + 2.058 → at most 5.438 V, which is ≤ 5.5 V specified ✓. CM top = VP_AFE − 1.5 V ≥ 3.198 − 1.5 → 1.698 V, which clears the 1.111 V peak ✓.

### afe_ch_a (ch B identical: replace `A_` with `B_`, 1xx with 2xx, J2 with J3, AIN_A with AIN_B)
| Net | Type | Refs |
|---|---|---|
| A_BNC | analog in ±10 V (±30 V survive) | J2 centre; R101 909 kΩ 1206 (top); C101 22 pF C0G ≥100 V |
| A_DIV | divider node | R101, C101, R102 100 kΩ (bottom → GND), C102 150 pF, C103 15 pF, C104 trimmer 16.5–33 pF (all → GND), D101 pin 3 (common), R103 |
| A_BUF_IN | buffer + in | R103 1.00 kΩ (from A_DIV), C105 8.2 pF → GND, U101 +IN |
| A_BUF_OUT | buffer out | U101 OUT and −IN (unity follower), R104 |
| A_XP | MFB node (driven side) | R104 1.00 kΩ (from A_BUF_OUT), R108 499 Ω, R106 909 Ω, C108 27 pF |
| A_XN | MFB node (grounded side) | R105 1.00 kΩ (from GND), R109 499 Ω, R107 909 Ω, C108 |
| A_FIP | FDA IN+ | R108 (from A_XP), C109 12 pF, U102 IN+ |
| A_FIN | FDA IN− | R109 (from A_XN), C110 12 pF, U102 IN− |
| A_FON | FDA OUT− (feedback to driven side) | U102 OUT−/FB−, R106 (to A_XP), C109 (to A_FIP), R111 |
| A_FOP | FDA OUT+ | U102 OUT+/FB+, R107 (to A_XN), C110 (to A_FIN), R110 |
| AIN_A_P / AIN_A_N | ADC pins | R110 49.9 Ω from A_FOP; R111 49.9 Ω from A_FON; C113 56 pF C0G across |

- J2 shell → GND.
- D101 (BAV199): pin 1 → VN_AFE and pin 2 → VP_AFE *(verify pin 1 = anode of D1, pin 2 = cathode of D2)*.
- U101 (OPA356, SOT-23-5: 1 OUT, 2 V−, 3 +IN, 4 −IN, 5 V+ *(verify)*): V+ → VP_AFE, V− → VN_AFE. The part has no enable pin.
- U102 (THS4551): VS+ and PD → V3V3A, VS− → GND, VOCM → VCM.
- Decoupling: C106 0.1 µF on VP_AFE and C107 0.1 µF on VN_AFE (U101); C111 0.1 µF and C112 1 µF on V3V3A, plus C114 0.1 µF on VCM (U102).
- **Polarity:** a rise at A_BNC raises A_XP and so A_FIP, which drives OUT+ up and OUT− down. Feedback from OUT− goes to the driven side, so the loop is negative. Result: V(AIN_A_P) − V(AIN_A_N) = +0.09009 × V(A_BNC).

### adc (U8 = ADS5231, TQFP-64, parallel mode)
| Net | Type | Refs |
|---|---|---|
| ADC_VDRV | 3.3 V output-driver supply | FB1 (from V3V3A), U8 VDRV pins 5, 8, 40, 43; C26–C29 0.1 µF; C30 10 µF |
| ADC_ISET | bias | U8.ISET pin 60 → R12 56.2 kΩ → GND |
| ADC_REFT / ADC_REFT_C | reference | U8.REFT pin 53 → R13 2.0 Ω → C18 0.1 µF → GND |
| ADC_REFB / ADC_REFB_C | reference | U8.REFB pin 54 → R14 2.0 Ω → C19 0.1 µF → GND |

- AVDD pins 3, 46, 57 → V3V3A, each with its own 0.1 µF (C22, C23, C24), plus C25 10 µF.
- AGND pins 2, 47, 48, 49, 55, 58, 59, 61, 64 → GND. Driver GND pins 4, 7, 23, 25, 44 → GND.
- INT/EXT pin 56 → V3V3A selects the internal reference.
- These pins tie to GND:
  - SEL pin 1, which selects parallel-pin mode.
  - MSBI/SEN pin 41, which selects straight offset binary.
  - OEA/SCLK pin 42 and OEB pin 6, which enable the outputs.
- DVB pin 22, OVRA pin 39 and OVRB pin 9 → no-connect. They are short of FPGA pins, and over-range can be decoded from codes 0 and 4095.
- VDRV comes from V3V3A through FB1, so AVDD and VDRV share one source. |AVDD − VDRV| stays below the 0.3 V absolute maximum even while the rails ramp.

### clock
| Net | Type | Refs |
|---|---|---|
| XO_VDD | clean 3.3 V | FB2 (from V3V3A), C31 0.1 µF, C32 1 µF, X1.VDD, X1.OE/ST (pin 1, tie high = enabled) *(verify pin 1 function)* |
| XO_OUT | 40 MHz CMOS | X1.OUT; R16 33 Ω → ADC_CLK; R17 33 Ω → FPGA_CLK |

- The clock must not pass through the FPGA.
- The ADC_CLK trace should be ≤ 15 mm and routed over solid GND.
- The XO swings from 0.33 V (VOL) to 2.97 V (VOH) at VDD 3.3 V. Against the ADC CLK input, VIH 2.2 V and VIL 0.6 V are both met.

### fpga (U9 = GW1NR-LV9QN88PC6/I5)
| Net | Type | Refs |
|---|---|---|
| JTAG_TCK/TMS/TDI/TDO | 1.8 V (bank 3) | U9 pins 6/5/7/8 *(verify)*; J4 2×5 2.54 mm; J4.VREF → V1V8 |
| FPGA_RECONFIG_N | 1.8 V | U9 pin 9; R20 10 kΩ → V1V8; J4 |
| FPGA_MODE0 / FPGA_MODE1 | strap | U9 pins 88 / 87 → R18 / R19 10 kΩ → GND *(verify AUTOBOOT = 000)* |
| LED_ACT / LED_TRIG | 3.3 V out | U9 bank 1 → R21 / R22 1 kΩ → D2 / D3 anode, cathode → GND (1.3 mA each) |
| TRIG_IN / TRIG_OUT | 3.3 V | U9 bank 1 ↔ R23 / R24 100 Ω ↔ J5 pins 1 / 2 (header side nets TRIG_IN_H / TRIG_OUT_H) |
| GPIO1 / GPIO2 | 3.3 V spare | U9 bank 1 ↔ J5 pins 3 / 4; J5.5 → V3V3D, J5.6 → GND |

- VCC pins 1, 22, 45, 66 → V1V2.
- VCCX/VCCIO0 pins 64, 67, 78 → V3V3D. VCCIO1 pin 58 and VCCIO2 pins 23, 44 → V3V3D.
- **VCCIO3 pin 12 → V1V8.** Bank 3 powers the in-package PSRAM and runs at 1.71–1.89 V.
- VSS and the exposed pad → GND.
- Decoupling: 0.1 µF on each supply pin (C33–C43), plus bulk C44 10 µF (V1V2), C45 10 µF (V3V3D) and C46 4.7 µF (V1V8).

**Bank rule, which is binding:** every 3.3 V signal above goes on banks 1 or 2. Bank 3 carries only JTAG, RECONFIG_N and MODE.

Use this allocation: bank 2 (23 I/O) takes FPGA_CLK (pin 35 GCLKT_4), DA0–DA11 and DB0–DB9. Bank 1 (25 I/O) takes DB10, DB11, ADC_DVA, ADC_STPD, FT_* (15), FT_CLKOUT on a GCLK pin, LED_ACT, LED_TRIG, TRIG_IN, TRIG_OUT, GPIO1 and GPIO2. That uses 44 of about 48 3.3 V I/O. Phase 4 produces the exact pin map from UG803.

### usb_bridge (U10 = FT232HL, LQFP-48)
| Net | Type | Refs |
|---|---|---|
| FT_XCSI / FT_XCSO | 12 MHz crystal | Y1; C47 / C48 33 pF → GND (2 × (20 − 3) → 34 → 33 pF, which gives CL = 19.5 pF for a 20 pF crystal) *(verify Y1 CL)* |
| FT_REF | PHY bias | U10.REF → R25 12.0 kΩ 1 % → GND |
| FT_RESET_N | reset | U10.RESET# → R26 10 kΩ → V3V3D |
| FT_EECS / FT_EECLK / FT_EEDATA | EEPROM | U11 (93LC56B) CS/CLK/DI; DO → R27 2.2 kΩ → FT_EEDATA *(verify per FT232H DS)* |
| FT_VCORE | 1.8 V internal regulator out | U10 VCCCORE/VCCD pins, C55 4.7 µF + C54 0.1 µF *(verify pin names)* |

- U10 VCCIO, VPHY, VPLL and VREGIN → V3V3D. Use the FT232H "3.3 V-only" power configuration *(verify)*.
- TEST → GND.
- Decoupling: C49–C53 0.1 µF, plus C56 4.7 µF on V3V3D.
- ACBUS7–9 are no-connect.
- The EEPROM must be programmed for "245 FIFO". Software then selects sync FIFO mode (bit mode 0x40).
