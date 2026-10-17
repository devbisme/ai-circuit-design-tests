# Net plan — dual_adc_10msps (the coders' contract)

Rules for every block coder:
- One ground net, **`GND`** (ADC AGND/GND pins, BNC shells, USB shield, every return). Analog vs
  digital separation is done by placement on the 4-layer board, not by split nets.
- Rail names are exactly: `VBUS`, `+5V`, `+5VA`, `+3V3`, `+1V2`, `+3V3A`, `+4V0A`, `-4V0A`, plus
  local ferrite-fed sub-rails `+3V3_ADCIO`, `+3V3_CLK`, `+3V3_PHY` (boardforge reads the voltage
  from the name — do not rename).
- Interface nets (column "I/F") are created at top level by the assembler and passed into the
  block; all other nets are block-local. Constraint nets: `VIN_A`, `VIN_B`, `AIN_AP`, `AIN_AN`,
  `AIN_BP`, `AIN_BN` — renaming one silently disables a review check.
- Buses: `DA0..DA11`, `DB0..DB11`, `SD_DQ0..SD_DQ15`, `SD_A0..SD_A11`, `SD_BA0..SD_BA1`, `FT_D0..FT_D7`.
- Pin numbers given here are from the datasheets/KiCad symbols as read in phase 2; the
  datasheet librarian confirms every one marked (v).
- Passive values are fixed by the architecture (filter values come from an optimisation that
  includes the op-amp GBW — do not "round" them). Filter caps C104–C112 / C204–C212 are C0G,
  ≤ ±2 %.

## Block 1 — `usb_c_input(v5, usb_dp, usb_dm, gnd)` refs 5xx

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| VBUS | power | – | J501 VBUS (A4,A9,B4,B9), U501.5 (VBUS), D501 cathode, F501.1, C501.1 |
| +5V | power | v5 | F501.2 → (power_digital U601 VIN, power_analog FB701) |
| USB_DP | diff 90 Ω | usb_dp | J501 A6 + B6, U501.1 + U501.6 (I/O1) → U901 DP |
| USB_DM | diff 90 Ω | usb_dm | J501 A7 + B7, U501.3 + U501.4 (I/O2) → U901 DM |
| CC1 | signal | – | J501 A5, R501.1 (5.1 kΩ → GND) |
| CC2 | signal | – | J501 B5, R502.1 (5.1 kΩ → GND) |
| GND | ground | gnd | J501 GND (A1,A12,B1,B12) + shield, U501.2, D501 anode, R501.2, R502.2, C501.2 |

J501 SBU1/SBU2: no-connect. Sink-only (Rd = 5.1 kΩ on each CC): default USB power, no PD.
**VBUS-domain capacitance budget ≤ 10 µF nominal total** (USB attach inrush): C501 1 µF +
C601 4.7 µF + C702 1 µF + C705 2.2 µF = 8.9 µF. Do not add bulk caps on VBUS/+5V/+5VA.

## Block 2 — `power_digital(v5, v3v3, v1v2, gnd)` refs 6xx

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| +5V | power | v5 | U601 VIN, U601 EN, C601.1 (4.7 µF) |
| SW_3V3 | switch node | – | U601 SW, L601.1 (2.2 µH) |
| +3V3 | power | v3v3 | L601.2, C602.1, C603.1 (10 µF each), R601.1, C604.1, U602 IN, U602 EN, C605.1, R604.1 |
| FB_3V3 | analog | – | U601 FB, R601.2 (453 kΩ), C604.2 (6.8 pF), R602.1 (100 kΩ) |
| +1V2 | power | v1v2 | U602 OUT, C606.1 (1 µF) |
| LED_PWR | signal | – | R604.2 (1 kΩ), D601 anode |
| GND | ground | gnd | U601 GND, U602 GND, C601–C606 .2, R602.2, D601 cathode |

Divider (top R601 = 453 k, bottom R602 = 100 k, TLV62569 VFB = 0.600 V, 0.588–0.612):
0.6 × (1 + 453/100) = **3.318 V** (3.252–3.385 V) — inside Spartan-6 VCCAUX 3.135–3.45 V.

## Block 3 — `power_analog(v5, v3v3a, vp4a, vn4a, gnd)` refs 7xx

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| +5V | power | v5 | FB701.1 |
| +5VA | power | – | FB701.2, U701 IN (1), U701 EN (3), C702.1 (1 µF), U702 VIN (3), U702 EN+ (12), U702 EN− (8), C705.1 (2.2 µF) |
| +3V3A | power | v3v3a | U701 OUT (5), C703.1 (1 µF) |
| LM_C1P / LM_C1N | power | – | U702 C1+ (10) / C1− (9), C706 (1 µF flying) |
| LM_CP | power | – | U702 CP (5), C707.1 (4.7 µF) |
| +4V0A | power | vp4a | U702 OUT+ (11), C708.1 (2.2 µF), R701.1 |
| LM_FBP | analog | – | U702 FB+ (2), R701.2 (232 kΩ top), R702.1 (100 kΩ bottom) |
| -4V0A | power | vn4a | U702 OUT− (6), C709.1 (2.2 µF), R703.1 |
| LM_FBN | analog | – | U702 FB− (7), R703.2 (226 kΩ top), R704.1 (100 kΩ bottom) |
| GND | ground | gnd | U701 GND (2), U702 GND (4), U702 PAD (13), U702 PGOOD (1, unused → GND per DS), C702/C703/C705/C707/C708/C709 .2, R702.2, R704.2 |

Dividers (LM27762 own VREFs: VFB+ = 1.200 V, VFB− = −1.220 V; R2, R4 ≥ 50 k ✓):
+: 1.2 × (232 + 100)/100 = **+3.984 V** (3.924–4.044 V); −: −1.22 × (226 + 100)/100 = **−3.977 V**
(−3.919…−4.036 V). +3V3A total capacitance must stay ≤ 10 µF (C703 1 + C308 4.7 + C118/C218
1 + 1 + 0.1 µF decouplers ≈ 8.5 µF).

## Block 4 — `afe_channel(ch, vin, ain_p, ain_n, adc_cm, vp4a, vn4a, v3v3a, gnd)` refs 1xx (A) / 2xx (B)

`ch` = "A" → refs 101…, nets suffixed `_A`, I/F `VIN_A`, `AIN_AP`, `AIN_AN`;
`ch` = "B" → refs 201… (same numbering + 100), suffix `_B`, I/F `VIN_B`, `AIN_BP`, `AIN_BN`.
Shown for channel A. U101 = OPA2810IDR (SOIC-8: 1 OUTA, 2 −INA, 3 +INA, 4 V−, 5 +INB, 6 −INB,
7 OUTB, 8 V+ (v)); U102 = OPA810IDBVR (SOT-23-5: 1 VO, 2 VS−, 3 VIN+, 4 VIN−, 5 VS+);
U103 = THS4551IRGTR (VQFN-16: 1 FB−, 2 IN+, 3 IN−, 4 FB+, 5–8 VS+, 9 VOCM, 10 OUT+, 11 OUT−,
12 PD, 13–16 VS−, 17 EP).

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| VIN_A | analog in | vin | J101 centre (1), R101.1 (953 kΩ 1206), C101.1 (8.2 pF C0G 100 V), C102.1 (trimmer 2–6 pF, value "3.3p") |
| ATT_A | analog | – | R101.2, C101.2, C102.2, R102.1 (49.9 kΩ), C103.1 (220 pF C0G), R103.1 (1.00 kΩ) |
| BUFIN_A | analog | – | R103.2, D101.3 (BAV199 common), U101.3 (+INA) |
| BUF_A | analog | – | U101.1 (OUTA), U101.2 (−INA), R104.1 |
| SKA1_A | analog | – | R104.2 (887 Ω), R105.1, C104.1 (270 pF) |
| SKA2_A | analog | – | R105.2 (453 Ω), C105.1 (100 pF → GND), U101.5 (+INB) |
| SKA_A | analog | – | U101.7 (OUTB), U101.6 (−INB), C104.2, R106.1 |
| SKB1_A | analog | – | R106.2 (374 Ω), R107.1, C106.1 (1.8 nF) |
| SKB2_A | analog | – | R107.2 (232 Ω), C107.1 (82 pF → GND), U102.3 (VIN+) |
| SKB_A | analog | – | U102.1 (VO), U102.4 (VIN−), C106.2, R108.1 |
| MFX_P_A | analog | – | R108.2 (698 Ω), C108.1 (330 pF → GND), R110.1 (1.27 kΩ), R112.1 (576 Ω) |
| MFX_N_A | analog | – | R109.2 (698 Ω, R109.1 → GND), C109.1 (330 pF → GND), R111.1 (1.27 kΩ), R113.1 (576 Ω) |
| FDA_INP_A | analog | – | R112.2, C110.1 (82 pF), U103.2 (IN+) |
| FDA_INN_A | analog | – | R113.2, C111.1 (82 pF), U103.3 (IN−) |
| FDA_OUTN_A | analog | – | U103.11 (OUT−), R110.2, C110.2, R115.1 (46.4 Ω) |
| FDA_OUTP_A | analog | – | U103.10 (OUT+), R111.2, C111.2, R114.1 (46.4 Ω) |
| AIN_AP | analog diff | ain_p | R114.2, C112.1 (1.2 nF C0G across pair) → U301.50 (INA) |
| AIN_AN | analog diff | ain_n | R115.2, C112.2 → U301.51 (INA complement) |
| ADC_CM | analog ref | adc_cm | U103.9 (VOCM), C119.1 (10 nF) → U301.52 (CM) |
| +4V0A | power | vp4a | U101.8, U102.5, D101.2 (upper cathode), C113, C115 (0.1 µF), C120 (2.2 µF) |
| -4V0A | power | vn4a | U101.4, U102.2, D101.1 (lower anode), C114, C116 (0.1 µF), C121 (2.2 µF) |
| +3V3A | power | v3v3a | U103.5–8 (VS+), U103.12 (PD, tie high = on), C117 (0.1 µF), C118 (1 µF) |
| GND | ground | gnd | J101 shell (2), R102.2, C103.2, R109.1, C105.2, C107.2, C108.2, C109.2, U103.13–16 (VS−), U103.17 (EP), C113–C121 .2 |

U103.1 (FB−) and U103.4 (FB+) are **no-connect**: they are internal taps of OUT−/OUT+ and
are typed `output` in the KiCad symbol, so tying them to the OUT nets is an ERC conflict;
feedback parts go to the OUT pins' nets as listed. D101 BAV199 pinning (v): 1 = anode of
lower diode (→ −4V0A), 3 = common (→ BUFIN_A), 2 = cathode of upper diode (→ +4V0A).

Stage arithmetic (inputs → result; pole count by **nodes**: SK_a 2 (SKA1, SKA2), SK_b 2
(SKB1, SKB2), MFB 2 per DM half (MFX, FDA_IN via feedback C), RC 1 (one C across the pair) =
**7 poles**; the compensated attenuator is a pole-zero pair that cancels):
- Attenuator: 49.9k/(953k+49.9k) = 0.049756 (DC); (8.2+3.3)p/(8.2+3.3+220)p = 0.049676 (HF) →
  −0.014 dB step; R_in = 1.0029 MΩ, C_in = 11.5p·220p/231.5p = 10.9 pF (+ ~3–5 pF BNC/trace).
- SK_a: f0 = 1/(2π√(887·453·270p·100p)) = 1.528 MHz, Q = √(R1R2C1C2)/(C2(R1+R2)) = 0.777.
- SK_b: f0 = 1/(2π√(374·232·1.8n·82p)) = 1.406 MHz, Q = 2.277.
- MFB: f0 = 1/(2π√(330p·82p·1270·576)) = 1.131 MHz, Q = 0.593, G = 1270/698 = 1.8195.
- RC: 1/(2π·2·46.4·1.2n) = 1.429 MHz.
- SK values are pre-distorted for 70 MHz op-amp GBW (OPA2810/OPA810); with that GBW the
  cascade is a 7-pole Butterworth-like response, −3 dB at 1.354 MHz.
- Whole path (ngspice, `architecture/afe_nominal.cir`): 1 kHz −20.87 dB; 1 MHz −0.01 dB rel.;
  passband ripple +0.013/−0.011 dB (1 kHz–1 MHz); 5 MHz −80.9 dB rel.; 10 MHz −123.3 dB rel.
- Protection: +30 V at VIN → ATT = 30 × 0.049756 = 1.49 V; clamp D101 conducts only above
  4.0 + 0.6 = 4.6 V at BUFIN ⇒ VIN > 92 V; OPA2810 abs-max input ±4.5 V on ±4 V rails ✓.
  Unpowered: (30 − 0.6 V)/953 k = 31 µA into the op-amp ESD diode (limit 10 mA) ✓.

## Block 5 — `adc(ain_ap, ain_an, ain_bp, ain_bn, adc_cm, adc_clk, da, db, adc_dva, adc_ovra, adc_ovrb, adc_sel, adc_sen, adc_sclk, adc_sdata, v3v3a, v3v3, gnd)` refs 3xx

U301 = ADS5231IPAGT (TQFP-64; symbol generated in phase 4 from the pin table).

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| AIN_AP / AIN_AN | analog | ain_ap / ain_an | U301.50 (INA) / U301.51 (INA complement) |
| AIN_BP / AIN_BN | analog | ain_bp / ain_bn | U301.63 (INB) / U301.62 (INB complement) |
| ADC_CM | analog ref | adc_cm | U301.52 (CM out, 1.5 V), C303 (0.1 µF), C304 (1 µF) |
| ADC_REFT / ADC_REFB | analog | – | U301.53 → R302 (2.0 Ω) → C301 (0.1 µF) → GND; U301.54 → R303 (2.0 Ω) → C302 (0.1 µF) → GND (nets ADC_REFT, REFT_RC, ADC_REFB, REFB_RC) |
| ADC_ISET | analog | – | U301.60, R301 (56.2 kΩ 1 % → GND) |
| ADC_CLK | clock | adc_clk | U301.24 (CLK) |
| DA_ADC0..11 | digital | – | U301.27..38 (D0_A..D11_A) → RN301–RN303 (4× 33 Ω arrays) inputs |
| DA0..DA11 | digital | da | RN301–RN303 outputs → FPGA |
| DB_ADC0..11 | digital | – | U301.10..21 (D0_B..D11_B) → RN304–RN306 inputs |
| DB0..DB11 | digital | db | RN304–RN306 outputs → FPGA |
| ADC_DVA | clock | adc_dva | U301.26 (DVA) |
| ADC_OVRA / ADC_OVRB | digital | adc_ovra / adc_ovrb | U301.39 / U301.9 |
| ADC_SEL | digital | adc_sel | U301.1, R304 (10 kΩ → GND) |
| ADC_SEN | digital | adc_sen | U301.41 (MSBI/SEN), R305 (10 kΩ → GND) |
| ADC_SCLK | digital | adc_sclk | U301.42 (OEA/SCLK), R306 (10 kΩ → GND) |
| ADC_SDATA | digital | adc_sdata | U301.45 (STPD/SDATA), R307 (10 kΩ → GND) |
| +3V3A | power | v3v3a | U301.3, .46, .57 (AVDD), U301.56 (INT/EXT = 1 → internal ref), C305–C307 (0.1 µF), C308 (4.7 µF) |
| +3V3_ADCIO | power | – | FB301.2, U301.5, .8, .40, .43 (VDRV), C309–C312 (0.1 µF), C313 (4.7 µF) |
| +3V3 | power | v3v3 | FB301.1 |
| GND | ground | gnd | U301 AGND 2, 47, 48, 49, 55, 58, 59, 61, 64; GND 4, 7, 23, 25, 44; U301.6 (OE_B = 0, enabled); all caps .2; R301, R304–R307 .2 |

U301.22 (DVB): no-connect. Pull-downs R304–R307 hold the ADC in parallel mode with outputs
enabled while the FPGA is unconfigured.

## Block 6 — `clock(v3v3, adc_clk, clk10_fpga, gnd)` refs 4xx

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| +3V3 | power | v3v3 | FB401.1 |
| +3V3_CLK | power | – | FB401.2, Y401 VDD + OE/EN, U401 VCC (5), C401, C402 (0.1 µF), C403 (4.7 µF) |
| XO_OUT | clock | – | Y401 OUT, U401.1 (1A), U401.3 (2A) |
| CLKB1 / CLKB2 | clock | – | U401.6 (1Y) → R401.1 (33 Ω) / U401.4 (2Y) → R402.1 (33 Ω) |
| ADC_CLK | clock | adc_clk | R401.2 → U301.24 |
| CLK10_FPGA | clock | clk10_fpga | R402.2 → U1001 GCLK input |
| GND | ground | gnd | Y401 GND, U401.2, C401–C403 .2 |

## Block 7 — `sdram(sd_dq, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n, sd_we_n, sd_ldqm, sd_udqm, v3v3, gnd)` refs 8xx

U801 = W9812G6KH-6 (Memory_RAM:W9812G6KH-6, TSOP-II-54).

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| SD_DQ0..15 | bidir | sd_dq | U801 .2, .4, .5, .7, .8, .10, .11, .13, .42, .44, .45, .47, .48, .50, .51, .53 |
| SD_A0..A9 | out | sd_a | U801 .23, .24, .25, .26, .29, .30, .31, .32, .33, .34 |
| SD_A10 / SD_A11 | out | sd_a | U801 .22 (A10/AP) / .35 |
| SD_BA0 / SD_BA1 | out | sd_ba | U801 .20 / .21 |
| SD_CLK | clock | sd_clk | R801.1 (22 Ω, at FPGA end) |
| SD_CLK_M | clock | – | R801.2, U801 .38 |
| SD_CKE | out | sd_cke | U801 .37, R802 (10 kΩ → GND) |
| SD_CS_N | out | sd_cs_n | U801 .19, R803 (10 kΩ → +3V3) |
| SD_RAS_N / SD_CAS_N / SD_WE_N | out | … | U801 .18 / .17 / .16 |
| SD_LDQM / SD_UDQM | out | sd_ldqm / sd_udqm | U801 .15 / .39 |
| +3V3 | power | v3v3 | U801 .1, .3, .9, .14, .27, .43, .49; C801–C807 (0.1 µF, one per pin), C808 (10 µF), R803.2 |
| GND | ground | gnd | U801 .6, .12, .28, .41, .46, .52, .54; caps .2, R802.2 |

U801 .36 and .40: no-connect (pin 36 is A12 on the 32 MB W9825G6KH second source — if that
part is substituted, route an FPGA spare I/O as SD_A12 to pin 36).

## Block 8 — `usb_fifo(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_clkout, v3v3, gnd)` refs 9xx

U901 = FT232HL (Interface_USB:FT232H, LQFP-48), 3.3 V-only supply configuration (v).

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| USB_DP / USB_DM | diff 90 Ω | usb_dp / usb_dm | U901.7 (DP) / U901.6 (DM) |
| FT_D0..7 | bidir | ft_d | U901.13–20 (ADBUS0–7) |
| FT_RXF_N | in to FPGA | ft_rxf_n | U901.21 (ACBUS0) |
| FT_TXE_N | in to FPGA | ft_txe_n | U901.25 (ACBUS1) |
| FT_RD_N | out from FPGA | ft_rd_n | U901.26 (ACBUS2), R907 (10 kΩ → +3V3) |
| FT_WR_N | out from FPGA | ft_wr_n | U901.27 (ACBUS3), R908 (10 kΩ → +3V3) |
| FT_SIWU_N | local | – | U901.28 (ACBUS4), R909 (10 kΩ → +3V3) |
| FT_CLKOUT_S | clock | – | U901.29 (ACBUS5), R910.1 (22 Ω) |
| FT_CLKOUT | clock 60 MHz | ft_clkout | R910.2 → U1001 GCLK input |
| FT_OE_N | out from FPGA | ft_oe_n | U901.30 (ACBUS6), R911 (10 kΩ → +3V3) |
| FT_PWRSAV_N | local | – | U901.31 (ACBUS7), R912 (10 kΩ → +3V3) |
| FT_XI / FT_XO | xtal | – | U901.1 / U901.2, Y901 (12 MHz), C901 / C902 (load caps → GND) |
| FT_REF | analog | – | U901.5, R901 (12.0 kΩ 1 % → GND) |
| FT_RESET_N | local | – | U901.34, R902 (10 kΩ → +3V3) |
| EE_CS / EE_CLK / EE_DATA | local | – | U901.45 / .44 / .43 → U902 CS / CLK / DI; R904–R906 (10 kΩ → +3V3) |
| EE_DO | local | – | U902 DO, R903 (2.2 kΩ) → EE_DATA |
| +3V3_PHY | power | – | FB901.2, U901.3 (VPHY), U901.8 (VPLL), C903 (4.7 µF), C904, C905 (0.1 µF) |
| +3V3 | power | v3v3 | FB901.1, U901.12, .24, .46 (VCCIO), U901.40 (VREGIN), U901.39 (VCCD), U902 VCC, C906–C908, C910, C913 (0.1 µF), C909 (4.7 µF), pull-ups |
| FT_VCORE / FT_VCCA | power (1.8 V out) | – | U901.38 → C911 (0.1 µF); U901.37 → C912 (0.1 µF) |
| GND | ground | gnd | U901 .4, .9, .41 (AGND), .10, .11, .22, .23, .35, .36, .47, .48 (GND), .42 (TEST), U902 GND, caps |

U901.32, .33 (ACBUS8/9): no-connect. U902 = 93LC56BT-I/OT (16-bit organisation, required by FTDI).

## Block 9 — `fpga(clk10_fpga, da, db, adc_dva, adc_ovra, adc_ovrb, adc_sel, adc_sen, adc_sclk, adc_sdata, sd_dq, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n, sd_we_n, sd_ldqm, sd_udqm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_clkout, v3v3, v1v2, gnd)` refs 10xx

U1001 = XC6SLX9-2TQG144C on symbol `FPGA_Xilinx_Spartan6:XC6SLX4-TQG144` (LX4/LX9 TQG144
share one pinout (v)); set value/MPN to XC6SLX9-2TQG144C. All VCCO banks at 3.3 V.

| Net | Type | I/F | Connected refs |
|---|---|---|---|
| CLK10_FPGA, FT_CLKOUT, ADC_DVA | clock in | yes | U1001 **IO_Lxx_GCLKn** pins (one GCLK each; CLK10 and DVA on the same half-bank as the ADC bits) |
| DA0..11, DB0..11, ADC_OVRA/B | in | yes | U1001 user I/O (group by bank) |
| ADC_SEL/SEN/SCLK/SDATA | out | yes | U1001 user I/O |
| SD_* (38 nets) | SDRAM bus | yes | U1001 user I/O, kept on adjacent banks; SD_CLK on a pin usable with ODDR2 |
| FT_D0..7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N | FIFO | yes | U1001 user I/O in the same bank as FT_CLKOUT |
| CFG_CCLK / CFG_MOSI / CFG_DIN / CFG_CS_N | config SPI | – | U1001 CCLK, MOSI, DIN, CSO_B → U1002 CLK / DI / DO / CS#; R1001 (4.7 kΩ CS# → +3V3) |
| FL_WP_N / FL_HOLD_N | local | – | U1002 /WP, /HOLD → R1002, R1003 (10 kΩ → +3V3) |
| JTAG_TCK/TMS/TDI/TDO | debug | – | U1001 TCK/TMS/TDI/TDO → J1001 (1 VREF=+3V3, 2 GND, 3 TCK, 4 TDO, 5 TDI, 6 TMS) |
| CFG_PROG_N / CFG_INIT_N / CFG_DONE | config | – | U1001 PROGRAM_B (R1004 4.7 kΩ ↑), INIT_B (R1005 4.7 kΩ ↑), DONE (R1006 330 Ω ↑) |
| CFG_M0 / CFG_M1 | strap | – | M0 → R1009 (1 kΩ → +3V3), M1 → R1008 (1 kΩ → GND): Master SPI (M[1:0] = 01) (v) |
| CFG_HSWAPEN | strap | – | HSWAPEN → R1010 (1 kΩ → +3V3): pre-config pull-ups off (v) |
| LED_ARMED / LED_TRIG | out | – | U1001 I/O → R1012 / R1013 (1 kΩ) → D1002 / D1003 → GND |
| TRIG_IN_F / TRIG_IN | in | – | U1001 I/O ← R1014 (100 Ω) ← J1002.1; R1015 (10 kΩ → GND) on TRIG_IN |
| TRIG_OUT_F / TRIG_OUT | out | – | U1001 I/O → R1016 (100 Ω) → J1002.2; J1002.3 = GND |
| +1V2 | power | v1v2 | all VCCINT pins, one 0.1 µF each + 4.7 µF bulk |
| +3V3 | power | v3v3 | all VCCAUX and VCCO_0..3 pins, one 0.1 µF each + 2× 4.7 µF; U1002 VCC + 0.1 µF |
| GND | ground | gnd | all GND pins, SUSPEND (→ GND) (v), straps, LEDs, caps |

FPGA I/O budget: ADC 31 + SDRAM 38 + FIFO 14 + CLK10 1 + LEDs 2 + trigger 2 = 88 user I/O
+ 4 SPI config pins (dual-purpose) = 92 of 102 (HSWAPEN, M0, M1, INIT_B excluded) → 6 spare.
Pin-to-signal assignment is the fpga block coder's; respect the GCLK rule above.

## Top-level net ↔ argument map (assembler)

| Top net(s) | Blocks |
|---|---|
| +5V | usb_c_input.v5, power_digital.v5, power_analog.v5 |
| +3V3 | power_digital.v3v3, adc.v3v3, clock.v3v3, sdram.v3v3, usb_fifo.v3v3, fpga.v3v3 |
| +1V2 | power_digital.v1v2, fpga.v1v2 |
| +3V3A | power_analog.v3v3a, afe_channel(A,B).v3v3a, adc.v3v3a |
| +4V0A / -4V0A | power_analog.vp4a / vn4a, afe_channel(A,B).vp4a / vn4a |
| VIN_A, AIN_AP, AIN_AN | afe_channel("A") vin, ain_p, ain_n; adc ain_ap, ain_an |
| VIN_B, AIN_BP, AIN_BN | afe_channel("B") vin, ain_p, ain_n; adc ain_bp, ain_bn |
| ADC_CM | afe_channel(A,B).adc_cm, adc.adc_cm |
| ADC_CLK / CLK10_FPGA | clock ↔ adc / fpga |
| DA[0:11], DB[0:11], ADC_DVA, ADC_OVRA, ADC_OVRB, ADC_SEL, ADC_SEN, ADC_SCLK, ADC_SDATA | adc ↔ fpga |
| SD_* | sdram ↔ fpga |
| FT_D[0:7], FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N, FT_CLKOUT | usb_fifo ↔ fpga |
| USB_DP, USB_DM | usb_c_input ↔ usb_fifo |
| GND | all |
