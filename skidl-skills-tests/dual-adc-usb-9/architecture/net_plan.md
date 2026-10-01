# dual_adc_usb — Net plan (rev 2)

The coders' contract. Net names are exact (SKiDL `Net("...")` names). `ref.PIN` uses the datasheet
pin **name** (exact SKiDL names for U7/U9/U2/U10 are in `datasheets/*_SUMMARY.md`); pin numbers are
given where the datasheet was read. Single ground net `GND` (solid plane; analog/digital separation
by placement, not by a split — see design_risks.md L1).

Types: `pwr` power rail, `gnd`, `ana` analog, `clk` clock, `dig` digital, `bus` digital bus, `usb` USB pair.

Rev 2 changes (escalation from `handoffs/04_datasheets.md`): new **+1V8** rail for GW1NR VCCO3;
bank-3 config pull-ups and J4 reference on +1V8; ADC_DVA/DVB/OVRA/OVRB and FT_SIWU_N removed from
the FPGA (I/O budget 48/48); FPGA pin map fixed; READY/DONE removed (R82 deleted, R81 repurposed as
TCK pull-down); Y1 → YXC OT322540MJBA4SL; Y2 load caps 33 pF; REFT/REFB network per ADS5231 Fig. 21.

## 1. Interface nets (cross-block — these appear in the Block manifest)

| Net | Type | Connected refs | Notes |
|---|---|---|---|
| GND | gnd | all blocks | J1/J2/J3 shells, all EPs (U6 PAD, U9 EP — **assumption: U9 EP = GND**, see handoff) |
| VBUS_SW | pwr | U2.VOUT, U2.QOD, C3 · U3.VIN, U4.VIN, U4.EN, U12.VIN, U12.EN, C4, C6, C9, R9 · U5.IN, U5.EN, C10 · U6.VIN, U6.EN+, U6.EN–, C12 | 4.40–5.25 V switched, soft-started VBUS <!-- revised: U12/C9 added --> |
| +3V3D | pwr | pwr_digital (U3 out) → U7.VDRV(5,8,40,43); Y1.VDD/OE, U8.VCC; U9.VCCX/VCCO0(64,67,78), VCCO1(58), VCCO2(23,44); U10 VREGIN/VCCD/VCCIO/VPLL/VPHY + ACBUS4; U11.VCC; R101, R102 | 0.6×(1+100k/22k) = **3.327 V**. **VCCO3 (12) is NOT on this rail** <!-- revised: VCCO3 moved to +1V8; SIWU# tie --> |
| +1V2 | pwr | pwr_digital (U4 out) → U9.VCC(1,22,45,66) | 0.6×(1+100k/100k) = **1.200 V** |
| +1V8 | pwr | pwr_digital (U12 out) → U9.VCCO3(12), C91, C93; R80, R85 (pull-ups); J4.1 (JTAG VREF) | 0.6×(1+200k/100k) = **1.800 V**; bank 3 = in-package PSRAM bank, VCCO3 1.71–1.89 V <!-- revised: new rail --> |
| +3V3A | pwr | pwr_analog (U5.OUT) → U7.AVDD(3,46,57), U7.INT/~{EXT}(56); U21.VS+, U21.PD; U41.VS+, U41.PD | fixed 3.3 V LDO, analog only |
| VAFE_P | pwr | pwr_analog (U6.OUT+) → U20.V+, D20.2, U40.V+, D40.2 | 1.2×(180k+100k)/100k = **+3.360 V** |
| VAFE_N | pwr | pwr_analog (U6.OUT–) → U20.V–, D20.1, U40.V–, D40.1 | –1.22×(180k+100k)/100k = **–3.416 V** |
| USB_DP | usb | U1.IO (D+ pair), J1.DP1+DP2 (A6,B6) → U10.DP | 90 Ω diff pair |
| USB_DM | usb | U1.IO (D– pair), J1.DN1+DN2 (A7,B7) → U10.DM | 90 Ω diff pair |
| ADC_AINA_P | ana | R29.2, C30.1, U7.INA(50) | ch A + input |
| ADC_AINA_N | ana | R30.2, C30.2, U7.~{INA}(51) | ch A – input |
| ADC_AINB_P | ana | R49.2, C50.1, U7.INB(63) | ch B + input |
| ADC_AINB_N | ana | R50.2, C50.2, U7.~{INB}(62) | ch B – input |
| ADC_VCM | ana | U7.CM(52), C71 · U21.VOCM(2), C31 · U41.VOCM(2), C51 | 1.5 V (1.4–1.6), ±2 mA drive; FDA VOCM bias ≤ ±8 µA each |
| ADC_CLK | clk | R70.2, U7.CLK(24) | 40 MHz CMOS, point-to-point from XO, ≤ 25 mm |
| FPGA_CLK40 | clk | R71.2 → U9.IOR5A/RPLL_T_in (63) | buffered copy of XO; feeds right PLL for phase-shifted ADC capture <!-- revised: pin fixed --> |
| ADC_DA[0..11] | bus | U7.D0_A..D11_A (27..38) → U9 bank 2 (§2 fpga pin map) | D11 = MSB; offset binary (MSBI=0) |
| ADC_DB[0..11] | bus | U7.D0_B..D11_B (10..21) → U9 bank 2 (DB1..11) + bank 1 (DB0) | |
| ADC_SEL | dig | U9 → U7.SEL(1) | 0 = parallel pin mode; 1 = serial (test patterns for capture-phase calibration) |
| ADC_MSBI_SEN | dig | U9 → U7.MSBI/SEN(41) | |
| ADC_OEA_SCLK | dig | U9 → U7.OEA/SCLK(42) | |
| ADC_STPD_SDATA | dig | U9 → U7.STPD/SDATA(45) | |
| ADC_OEB | dig | U9 → U7.OEB(6) | reserve: tie to GND to free one 3.3 V FPGA pin if ever needed |
| FT_D[0..7] | bus | U10.ADBUS0..7 ↔ U9 bank 1 | 245 sync-FIFO data |
| FT_RXF_N | dig | U10.ACBUS0 (RXF#) → U9 | |
| FT_TXE_N | dig | U10.ACBUS1 (TXE#) → U9 | |
| FT_RD_N | dig | U9 → U10.ACBUS2 (RD#) | |
| FT_WR_N | dig | U9 → U10.ACBUS3 (WR#) | |
| FT_CLKOUT | clk | U10.ACBUS5 (CLKOUT, 60 MHz) → U9.IOR17A/GCLKT_3 (52) | |
| FT_OE_N | dig | U9 → U10.ACBUS6 (OE#) | |

**Removed in rev 2** <!-- revised: FPGA I/O budget (48 × 3.3 V I/O) -->: `ADC_DVA`, `ADC_DVB`, `ADC_OVRA`, `ADC_OVRB`
(U7 pins 26, 22, 39, 9 are outputs → mark NC), `FT_SIWU_N` (U10.ACBUS4 tied to +3V3D inside
usb_bridge, as DS_FT232H permits for unused SIWU#). Option analysis in `ic_selection.md` §2a.

ACBUS map verified against DS_FT232H Table 3.7 (K6, phase 4).

## 2. Block-internal nets (names fixed so reviewers can trace the arithmetic)

### usb_power_in (J1 U1 U2 F1 D1 R1–R3 C1–C3)
| Net | Type | Connected | Notes |
|---|---|---|---|
| VBUS | pwr | J1.VBUS (A4,A9,B4,B9), F1.1 | raw |
| VBUS_F | pwr | F1.2, D1.1 (K), U1.VBUS, C1 (4.7 µF), U2.VIN, R3.1 | only ≤10 µF upstream of switch (USB attach rule) |
| USB_ON | dig | R3.2 (10 kΩ), U2.ON | ON = VBUS_F − 0.1 µA×10 kΩ ≈ VBUS_F ≥ 4.4 V > VIH 1.0 V → on; VBUS absent → 0 V < VIL 0.5 V → off |
| USB_CT | ana | U2.CT, C2 (1000 pF) | tR = 2.54 ms @ VIN 5 V (datasheet test cond., CT=1000 pF) |
| CC1 / CC2 | dig | J1.CC1(A5)–R1 5.1 kΩ–GND; J1.CC2(B5)–R2 5.1 kΩ–GND | UFP Rd, never tie CCs together |
| — | — | U1.GND, D1.2 (A), J1.GND/shell → GND | |

Inrush <!-- revised: C9 adds 10 µF -->: C_downstream ≈ 45 µF × 4 V / 2.54 ms → **71 mA**.

### pwr_digital (U3 U4 U12 L1 L2 L3 C4–C9 C17 R5–R9 R14 R15)
| Net | Type | Connected | Notes |
|---|---|---|---|
| SW_3V3 | pwr | U3.SW, L1.1 (2.2 µH) | |
| FB_3V3 | ana | U3.FB, R5.2, R6.1 | R5 = 100 kΩ top (to +3V3D), R6 = 22 kΩ bottom (to GND). VFB 0.588–0.612 V → 3.261–3.394 V |
| EN_3V3 | dig | U3.EN, R9.2 (100 kΩ from VBUS_SW), C8.1 (100 nF to GND) | delays 3V3D after 1V2/1V8: t = −10 ms·ln(1−VIH/VIN): 1.2/4.4 → 3.18 ms; 0.95/5.25 → 2.00 ms; both > 0.8 ms soft-start of U4/U12. EN low when VBUS_SW = 0 |
| SW_1V2 | pwr | U4.SW, L2.1 (2.2 µH) | |
| FB_1V2 | ana | U4.FB, R7.2, R8.1 | R7 = 100 kΩ top (to +1V2), R8 = 100 kΩ bottom → 1.200 V (1.176–1.224 V vs GW1NR LV 1.14–1.26 V ✓) |
| SW_1V8 | pwr | U12.SW, L3.1 (2.2 µH) | <!-- revised: new --> |
| FB_1V8 | ana | U12.FB, R14.2, R15.1 | **R14 = 200 kΩ top (+1V8 → FB), R15 = 100 kΩ bottom (FB → GND)**. 0.600×(1+200k/100k) = 1.800 V; worst case 0.588×(1+198k/101k) = 1.741 V … 0.612×(1+202k/99k) = 1.861 V ⊂ VCCO3 1.71–1.89 V ✓ <!-- revised: new --> |
| +3V3D | pwr | L1.2, C5 (22 µF), R5.1 | |
| +1V2 | pwr | L2.2, C7 (22 µF), R7.1 | U4.EN tied to VBUS_SW: VIH 1.2 V max < 4.4 V ✓ |
| +1V8 | pwr | L3.2, C17 (22 µF), R14.1 | U12.EN tied to VBUS_SW: VIH 1.2 V max < 4.4 V ✓ on; 0 V < VIL 0.4 V off ✓. Duty 1.8/5.25 = 34 % → on-time 229 ns at 1.5 MHz ✓ <!-- revised: new --> |
| — | — | C4 (10 µF U3 in), C6 (10 µF U4 in), C9 (10 µF U12 in) on VBUS_SW | |

**GW1NR sequencing (UG284-1.8E p.2, DS117 Table 3-3)** <!-- revised: +1V8 added -->: VCC and VCCO3 are the
device's POR supplies; power-on time must be 0.2–2 ms, and only if a rail takes >2 ms must VCC precede
VCCX/VCCIO. Here: +1V2 and +1V8 both start with VBUS_SW (tSS 800 µs each, TLV62569**DBV**, K7 verified);
+3V3D (VCCX, VCCO0–2) starts 2.0–3.2 ms later. Ramps: VCC 1.2 V/0.8 ms = 1.50 mV/µs (0.6–6 ✓);
VCCO3 1.8 V/0.8 ms = 2.25 mV/µs (0.1–10 ✓); VCCX 3.327 V/0.8 ms = 4.16 mV/µs (0.6–10 ✓). All power-on
times 0.8 ms ∈ 0.2–2 ms ✓, and VCC is up before VCCX/VCCIO1/2 regardless.

### pwr_analog (U5 U6 C10–C16 R10–R13) — unchanged
| Net | Type | Connected | Notes |
|---|---|---|---|
| +3V3A | pwr | U5.OUT, C11 (2.2 µF) | U5.EN = VBUS_SW: VHI 1.0 V < 4.4 V ✓ |
| LM_C1P / LM_C1N | pwr | U6.C1+(10)–C13 (1 µF)–U6.C1–(9) | flying cap |
| LM_CP | pwr | U6.CP(5), C14 (4.7 µF to GND) | unregulated ≈ −VIN |
| FB_AFEP | ana | U6.FB+(2), R10.2, R11.1 | R10 = 180 kΩ top (OUT+→FB+), R11 = 100 kΩ bottom (FB+→GND, ≥50 kΩ rule ✓). VFB+ 1.182–1.218 → +3.310…+3.410 V |
| FB_AFEN | ana | U6.FB–(7), R12.2, R13.1 | R12 = 180 kΩ top (OUT–→FB–), R13 = 100 kΩ bottom (FB–→GND). VFB– −1.202…−1.238 → −3.366…−3.466 V |
| VAFE_P / VAFE_N | pwr | U6.OUT+(11)/C15 2.2 µF; U6.OUT–(6)/C16 2.2 µF | |
| — | — | U6.EN+(12), EN–(8) = VBUS_SW (VIH 1.2 V ✓); U6.PGOOD(1) → GND; U6.GND(4) + PAD(13) → GND; C12 2.2 µF on VIN(3) | headroom: OUT+ 4.40−3.36 = 1.04 V ≫ 45 mV; CP ≈ −4.37 V vs −3.416−0.03 ✓ |

### afe_ch_a (J2 R20–R30 C20–C31 D20 U20 U21) — afe_ch_b identical, refs +20 (J3, R40–R50, C40–C51, D40, U40, U41), net suffix `_B` — unchanged
| Net | Type | Connected | Value / working |
|---|---|---|---|
| BNC_A | ana | J2.center, R20.1, C20.1, C21.1 | R20 = 910 kΩ 1 % 1206 (top), C20 = 18 pF C0G 100 V, C21 = 2–6 pF 100 V trimmer, C20∥C21 across R20 |
| ATT_A | ana | R20.2, C20.2, C21.2, R21.1, C22.1, D20.3 (common), R22.1 | R21 = 100 kΩ 1 % (bottom, to GND), C22 = 200 pF C0G (to GND). Ratio 100k/(910k+100k) = **0.09901**; Rin = **1.010 MΩ** |
| BUF_IN_A | ana | R22.2 (1.0 kΩ), U20.IN+ | limits input-ESD current; ≤ 50.6 µA at 50 V anyway |
| BUF_OUT_A | ana | U20.OUT (pin 1), U20.IN–, R23.1 | unity-gain follower |
| MFB_MS_A | ana | R23.2, R25.1, R27.1, C25.1 | R23 = 1.1 kΩ (R1 in), C25 = 100 pF to GND (Csh) |
| FDA_INP_A | ana | R27.2, C27.1, U21.VIN+(8) | R27 = 270 Ω (R3), C27 = 12 pF (Cfb) |
| FDA_OUTN_A | ana | U21.VOUT–(5), R25.2, C27.2, R30.1 | R25 = 1.0 kΩ (R2 feedback to signal-side M) |
| MFB_MR_A | ana | R24.2, R26.1, R28.1, C26.1 | R24 = 1.1 kΩ from GND (ref-leg R1), C26 = 100 pF to GND |
| FDA_INN_A | ana | R28.2, C28.1, U21.VIN–(1) | R28 = 270 Ω, C28 = 12 pF |
| FDA_OUTP_A | ana | U21.VOUT+(4), R26.2, C28.2, R29.1 | R26 = 1.0 kΩ |
| ADC_AINA_P/N | ana | R29 = R30 = 33 Ω → C30 = 270 pF C0G differential → U7 | 3rd pole |
| — | — | U21.VOCM(2) = ADC_VCM, C31 100 nF; U21.PD(7) = +3V3A (3.3 V > 2.1 V enable ✓); U21.VS+(3) = +3V3A, VS–(6) = GND; C29 100 nF; U20 V+/V– = VAFE_P/VAFE_N, C23/C24 100 nF; J2 shell → GND | |

D20 = BAV199 (series pair, connect by number): 1 (anode) → VAFE_N, 2 (cathode) → VAFE_P, 3 (common) → ATT_A.

**Polarity:** signal enters the side whose amp input is VIN+ and whose feedback comes from VOUT–, so
Vod = VOUT+ − VOUT– = +0.909 × V(BUF_OUT): a positive BNC voltage raises the ADC code. Do not swap.

### adc_dual (U7 C60–C73 R60–R62)
| Net | Type | Connected | Notes |
|---|---|---|---|
| +3V3A | pwr | U7.AVDD(3,46,57) with C60–C62 100 nF each + C63 10 µF; U7.INT/~{EXT}(56) | INT/EXT high = internal reference (default 0 = external — must be tied high) |
| +3V3D | pwr | U7.VDRV(5,8,40,43) with C64–C67 100 nF each + C68 10 µF | |
| ADC_REFT | ana | U7.REFT(53), R60.1 | <!-- revised: K9 verified, ADS5231 Fig. 21 --> R60 = 2 Ω series from the pin |
| ADC_REFT_F | ana | R60.2, C69 100 nF, C70 2.2 µF (both to GND) | caps on the far side of the 2 Ω |
| ADC_REFB | ana | U7.REFB(54), R61.1 | R61 = 2 Ω series |
| ADC_REFB_F | ana | R61.2, C72 100 nF, C73 2.2 µF (both to GND) | |
| ADC_ISET | ana | U7.ISET(60), R62 56.2 kΩ 1 % (E96) → GND | |
| ADC_VCM | ana | U7.CM(52), C71 100 nF | interface net (see §1) |
| GND | gnd | U7.AGND(2,47–49,55,58,59,61,64), U7.GND(4,7,23,25,44) | one plane |
| NC | — | U7.DVA(26), DVB(22), OVRA(39), OVRB(9) | outputs, left open <!-- revised: I/O budget --> |

Control drive check (FPGA LVCMOS33 → ADS5231, VIH 2.2 V / VIL 0.6 V): VOH ≥ 2.4 V > 2.2 ✓, VOL ≤ 0.4 V < 0.6 ✓. ADC_CLK from XO: VOH ≥ 0.9×3.261 = 2.93 V > 2.2 ✓, VOL ≤ 0.1×3.394 = 0.34 V < 0.6 ✓. Power-on default wanted: SEL=0, MSBI=0, OEA=0, STPD=0, OEB=0 (FPGA drives these after config).

**Capture without DV** <!-- revised: DVA/DVB dropped -->: ADS5231 @40 MSPS PLL on: tDV 13.5–18.5 ns (CLK↑→DV↓), t1 ≥ 3.7 ns, t2 ≥ 11.5 ns
→ data stable from 18.5−3.7 = **14.8 ns** to 13.5+11.5 = **25.0 ns** after CLK↑ → **10.2 ns** window. Minus U8 tpd spread
(≈3.2 ns, LVC1G34 @3.3 V — assumed, confirm in the TI DS) and FPGA tSU+tH (≈2 ns, assumed) → ≈5 ns margin. Gateware samples with the right-PLL
clock shifted ≈ +20 ns (≈ 288°) from FPGA_CLK40, calibrated at bring-up with the ADC serial-mode test pattern.

### clock_gen (Y1 U8 R70 R71 C75 C76)
| Net | Type | Connected | Notes |
|---|---|---|---|
| XO_OUT | clk | Y1.OUT(3), R70.1 (33 Ω), U8.A(2) | U8 input stub ≤ 5 mm from Y1 |
| ADC_CLK | clk | R70.2 → U7.CLK | interface |
| FPGA_CLK40 | clk | U8.Y(4) → R71 (33 Ω) → U9 pin 63 | interface |
| +3V3D | pwr | Y1.VDD(4), Y1.OE(1) (tie high: enable ≥ 0.7×VDD = 2.33 V ✓), U8.VCC, C75 (Y1) / C76 (U8) 100 nF | <!-- revised: Y1 = OT322540MJBA4SL, same 4-pin 3225 pinout 1 OE / 2 GND / 3 OUT / 4 VDD --> |

### fpga (U9 C80–C93 R80 R81 R83–R89 D80 D81 J4 J5)
| Net | Type | Connected | Notes |
|---|---|---|---|
| +1V2 | pwr | U9.VCC(1,22,45,66), C80–C83 100 nF, C84 10 µF | UG284 ferrite bead **not** used: buck ripple ≈10 mV = 0.8 % < 3 % VCC ripple limit |
| +3V3D | pwr | U9.VCCX/VCCO0(64,67,78), VCCO1(58), VCCO2(23,44); C85–C90 100 nF (one per pin), C92 10 µF | banks 0–2 LVCMOS33 <!-- revised: pin 12 removed --> |
| +1V8 | pwr | U9.VCCO3(12), C91 100 nF, C93 10 µF | bank 3 LVCMOS18 + in-package PSRAM <!-- revised: new --> |
| FPGA_RECONFIG_N | dig | U9.IOL13B/RECONFIG_N (9), R80 4.7 kΩ → **+1V8** | <!-- revised: was +3V3D --> |
| JTAG_TCK | dig | U9.IOL11B/TCK (6), J4.2, **R81 4.7 kΩ → GND** | UG284 Fig. 2 TCK pull-down; R81 repurposed from FPGA_READY <!-- revised --> |
| FPGA_MODE0 / FPGA_MODE1 | dig | U9.IOT5A/MODE0 (88) → R83, U9.IOT6B/MODE1 (87) → R84 (1 kΩ → GND each) | MODE=000 AUTO BOOT (K4 verified) |
| FPGA_JTAGSEL_N | dig | U9.IOL5A/JTAGSEL_N/LPLL_T_in (4), R85 4.7 kΩ → **+1V8** | <!-- revised: was +3V3D --> |
| JTAG_TMS/TDI/TDO | dig | U9 TMS(5)/TDI(7)/TDO(8) ↔ J4 | J4 1×6 2.54 mm: **1 = +1V8 (VREF)**, 2 TCK, 3 TMS, 4 TDI, 5 TDO, 6 GND <!-- revised: VREF 1.8 V --> |
| LED0 / LED1 | dig | U9 pins 59 / 60 → R86 / R87 (1.0 kΩ) → D80 / D81 anode; cathode → GND | (3.3−2.0)/1k = 1.3 mA. R86+D80 on pin 59 (MCLK) also serves as UG284's MCLK pull-down |
| TRIG_IN / TRIG_OUT | dig | J5.1 → R88 (100 Ω) → U9 pin 61; U9 pin 62 → R89 (100 Ω) → J5.2; J5.3 = GND | 3.3 V LVCMOS, not 5 V tolerant |

Deleted <!-- revised -->: FPGA_READY, FPGA_DONE nets and R82 — READY/DONE are not bonded on QN88P (UG803).

**FPGA I/O budget** <!-- revised -->: 3.3 V-capable I/O = bank 1 (25) + bank 2 (23) = **48**. Used: ADC 24 data + 5 ctrl = 29;
FT245 8 D + RXF/TXE/RD/WR/OE + CLKOUT = 14; FPGA_CLK40 1; LED 2; TRIG 2 → **48 of 48** (0 spare; reserve: tie ADC_OEB low → 1).
Bank 3 (1.8 V): 23 I/O − 8 config/JTAG = 15 free user I/O at LVCMOS18 (pins 3, 10, 11, 13–16, 79–86) for debug/future.

**U9 pin map (fixed; layout may permute data bits within the same bank, never across banks or onto the clock pins):**

| Bank | Pin → net |
|---|---|
| 2 (VCCO2, 3.3 V) | 17 ADC_DB1, 18 DB2, 19 DB3, 20 DB4, 25 DB5, 26 DB6, 27 DB7, 28 DB8, 29 DB9, 30 DB10, 31 DB11, 32 ADC_DA0, 33 DA1, 34 DA2, 35 DA3, 36 DA4, 37 DA5, 38 DA6, 39 DA7, 40 DA8, 41 DA9, 42 DA10, 47 DA11 |
| 1 (VCCO1, 3.3 V) | 48 ADC_DB0, 49 ADC_SEL, 50 ADC_MSBI_SEN, 51 ADC_OEA_SCLK, 52 FT_CLKOUT (GCLKT_3), 53 ADC_STPD_SDATA, 54 ADC_OEB, 55 FT_RD_N, 56 FT_WR_N, 57 FT_OE_N, 59 LED0, 60 LED1, 61 TRIG_IN, 62 TRIG_OUT, 63 FPGA_CLK40 (RPLL_T_in), 68–75 FT_D0..FT_D7, 76 FT_RXF_N, 77 FT_TXE_N |
| 3 (VCCO3, 1.8 V) | 4 JTAGSEL_N, 5 TMS, 6 TCK, 7 TDI, 8 TDO, 9 RECONFIG_N, 87 MODE1, 88 MODE0; others unconnected |

Pins 53–62 are dual-purpose config pins (DOUT, DIN, SSPI, MSPI); in AUTO BOOT they are free, and gateware must
enable them as regular I/O in the Gowin dual-purpose-pin settings.

### usb_bridge (U10 U11 Y2 C100–C111 R100–R103)
| Net | Type | Connected | Notes |
|---|---|---|---|
| +3V3D | pwr | U10.VREGIN, VCCD, VCCIO(12,24,46), VPLL, VPHY; **U10.ACBUS4 (SIWU#, pin 28)**; U11.VCC; C100–C107 100 nF + C108 4.7 µF | VREGIN 3.3 V mode (K6 verified). SIWU# tied high = unused (DS_FT232H) <!-- revised --> |
| FT_VCCCORE | pwr | U10.VCCCORE(38), U10.VCCA(37), C109 100 nF | 1.8 V internal-LDO output drives both pins (DS_FT232H §6.2.1); do not load |
| FT_XI / FT_XO | clk | U10.XCSI(1)/XCSO(2) ↔ Y2 12 MHz, **C110/C111 33 pF C0G** to GND | CL = 33·33/66 + 3…5 pF stray = 19.5–21.5 pF vs Y2 CL 20 pF ✓ <!-- revised: was 18 pF --> |
| FT_REF | ana | U10.REF(5), R100 12 kΩ 1 % → GND | |
| FT_RESET_N | dig | U10.~{RESET}(34), R101 10 kΩ → +3V3D | |
| FT_EECS / FT_EECLK | dig | U10.EECS(45)/EECLK(44) → U11.CS/CLK | EEPROM programmed once to "245 FIFO" mode |
| FT_EEDATA | dig | U10.EEDATA(43) → U11.DI directly, and → R103 2.2 kΩ → U11.DO | |
| FT_EEDO | dig | U11.DO, R103.2, R102 10 kΩ → +3V3D (VCCD) | DS_FT232H Table 3.3 (verified) |
| — | — | U10.TEST(42) → GND; U10.AGND/GND → GND | |

## 3. Arithmetic (each line: inputs → result)

- Channel gain: 0.09901 × (R25/R23 = 1000/1100 = 0.9091) = **0.09001** → ±10 V → ±0.900 V diff.
- ADC FS 2.02 Vpp diff (internal ref) → FS at BNC = 1.01/0.09001 = **±11.22 V**; worst case (gain err −3.5 %, R −1 %) ±10.72 V > 10 V ✓. LSB at BNC = 22.44 V/4096 = **5.48 mV**.
- FDA input CM (DC): Vx = VOUT+ × R23/(R23+R25) = (1.5 ± 0.45) × 1100/2100 = **0.550–1.021 V** within THS4521 @3.3 V range −0.1…1.8 V ✓. Outputs 1.05–1.95 V within 0.15…3.15 V swing ✓.
- MFB: f0 = 1/(2π√(R25·R27·C27·C25)) = **8.84 MHz**; Q = **0.990**.
- Output pole: 1/(2π·(2×33 Ω)·270 pF) = **8.93 MHz**.
- **Order = 3** (nodes: MFB_MS (C25), FDA_INP (C27), ADC_AIN pair (C30)). Nodal solve: **−3 dB 8.80 MHz; −0.16 dB @5 MHz; −35.8 dB @35 MHz**.
- Compensation: C_top needed 21.2–24.0 pF; C20+C21 spans 19.1–24.9 pF ✓. Cin at BNC = **20.3 pF**.
- Overload: (50 − 3.36 − 0.6)/910 kΩ = **50.6 µA** into clamp; R20 2.7 mW.
- +1V8: 0.600 × (1 + 200k/100k) = **1.800 V** (1.741–1.861 V worst case) <!-- revised -->.
- Y1 jitter <!-- revised -->: OT322540MJBA4SL 0.7 ps rms max (12 kHz–20 MHz) → SNR_j = −20·log(2π·5 MHz·0.7 ps) = **93.2 dB**; with ADC 70.7 dB → **70.68 dB** (ENOB 11.45). Budget was ≤5.04 ps (SNR_j ≥ 76 dB).
- Y2 load: 33 pF ‖ 33 pF series = 16.5 pF + 3–5 pF stray = **19.5–21.5 pF** ≈ CL 20 pF ✓ <!-- revised -->.
- Power budget: `design_risks.md` P1.
