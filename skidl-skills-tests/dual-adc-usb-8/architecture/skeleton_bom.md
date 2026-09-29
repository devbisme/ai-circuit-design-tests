# Skeleton BOM — dual_adc_usb (revision 1)

Every R and C value below is a real E-series value (E96 for 1 % resistors, E12/E24 for capacitors). Where the voltage rating, dielectric or tolerance is load-bearing, the Notes column says so.
Passives default to 0402 or 0603, X7R for decoupling, and C0G for anything in the signal path.
AFE ch B (2xx refs) is identical to ch A (1xx refs). Its quantities are included below.

## Active parts and connectors
| Function | Suggested MPN | Package | Qty | Refs | Notes |
|---|---|---|---|---|---|
| Dual 12-bit 40 MSPS ADC | ADS5231IPAGT | TQFP-64 10×10 | 1 | U8 | ★ critical. Single source (TI) |
| FPGA + 64 Mbit PSRAM | GW1NR-LV9QN88PC6/I5 | QFN-88 10×10 0.4 mm | 1 | U9 | ★ critical. Stock 182 (WARN) |
| USB 2.0 HS FIFO bridge | FT232HL-REEL | LQFP-48 | 1 | U10 | ★ critical |
| FT232H config EEPROM | 93LC56BT-I/OT | SOT-23-6 | 1 | U11 | Any 93LC56B/93C56 (x16) |
| Input buffer | OPA356AIDBVR | SOT-23-5 | 2 | U101, U201 | CM top (V+) − 1.5 V limits substitutes (see ic_selection §4) |
| FDA ADC driver | THS4551IRGTR | VQFN-16 3×3 | 2 | U102, U202 | |
| ± buffer rails | LM27762DSSR | WSON-12 2×3 | 1 | U7 | |
| 3.3 V analog LDO | TPS7A2033PDBVR | SOT-23-5 | 1 | U6 | Fixed 3.3 V, ≥ 300 mA |
| 3.3 V / 1.2 V bucks | TLV62569DBVR | SOT-23-5 | 2 | U3, U4 | VFB 0.600 V. Dividers depend on it |
| 1.8 V LDO | TLV75518PDBVR | SOT-23-5 | 1 | U5 | Fixed 1.8 V |
| VBUS load switch | TPS22919DCKR | SC-70-6 | 1 | U2 | Controlled rise limits inrush |
| USB ESD | USBLC6-2SC6 | SOT-23-6 | 1 | U1 | |
| 40 MHz XO | SX3M40.000B10F20TNN | 3225-4 | 1 | X1 | Needs ≤ 3 ps rms jitter and 45–55 % duty (verify) |
| 12 MHz crystal | X322512MSB4SI | 3225-4 | 1 | Y1 | Basic tier. Confirm CL |
| USB-C receptacle | TYPE-C-31-M-12 | SMD 16-pin | 1 | J1 | USB 2.0 only |
| BNC female, 50 Ω, PCB right-angle | KH-BNC50-3511 | THT | 2 | J2, J3 | HARD requirement |
| JTAG header 2×5 | 2.54 mm pin header | THT | 1 | J4 | VREF = 1.8 V |
| Aux header 1×6 | 2.54 mm pin header | THT | 1 | J5 | TRIG_IN/OUT, GPIO1/2, 3V3, GND |
| Clamp diode pair | BAV199 | SOT-23 | 2 | D101, D201 | Low leakage (pA) is required |
| LED | green 0603 | 0603 | 3 | D1, D2, D3 | |
| Ferrite bead | 600 Ω @ 100 MHz, ≥ 500 mA | 0603 | 2 | FB1, FB2 | FB1 feeds ADC VDRV, FB2 the XO |
| Inductor | 2.2 µH, Isat ≥ 1 A, DCR ≤ 0.1 Ω | 2.5×2.0 / 3×3 | 2 | L1, L2 | TLV62569 recommendation |
| Divider trimmer | LXRW19V330-050 (16.5–33 pF, 50 V) | SMD 1.3×0.9 | 2 | C104, C204 | Hand-trim at test |

## Signal-path passives (per channel; ×2)
| Function | Value | Package | Refs (ch A / ch B) | Notes |
|---|---|---|---|---|
| Divider top R_T | 909 kΩ 1 % | **1206** | R101 / R201 | 1206 for voltage rating (±30 V continuous) |
| Divider top C_T | 22 pF C0G **±1 %**, ≥ 100 V | 0805 | C101 / C201 | R_T·C_T = 909k × 22p → 20.0 µs |
| Divider bottom R_B | 100 kΩ 1 % | 0603 | R102 / R202 | |
| Divider bottom C_B1 | 150 pF C0G ±1 % | 0603 | C102 / C202 | |
| Divider bottom C_B2 | 15 pF C0G ±2 % (or ±0.25 pF) | 0603 | C103 / C203 | |
| Buffer series R_S | 1.00 kΩ 1 % | 0603 | R103 / R203 | Limits clamp current into the op-amp |
| Buffer input C_S | 8.2 pF C0G | 0603 | C105 / C205 | R_S·C_S pole = 19.4 MHz |
| MFB R1a / R1b | 1.00 kΩ 0.1 %–1 % | 0603 | R104, R105 / R204, R205 | Match the a/b halves (0.1 % preferred for CMRR) |
| MFB R2a / R2b | 909 Ω 1 % | 0603 | R106, R107 / R206, R207 | Gain 909/1000 → 0.909 |
| MFB R3a / R3b | 499 Ω 1 % | 0603 | R108, R109 / R208, R209 | |
| MFB C1 (differential) | 27 pF C0G ±5 % | 0603 | C108 / C208 | |
| MFB C2a / C2b | 12 pF C0G ±5 % | 0603 | C109, C110 / C209, C210 | |
| ADC series R | 49.9 Ω 1 % | 0402 | R110, R111 / R210, R211 | ≥ 25 Ω required by ADS5231 |
| ADC diff C | 56 pF C0G | 0402 | C113 / C213 | Place at the ADC pins |
| Decoupling | 0.1 µF X7R | 0402 | C106, C107, C111, C114 / C206, C207, C211, C214 | |
| Decoupling | 1 µF X7R | 0402 | C112 / C212 | |

Divider check: C_B total needed = R_T·C_T/R_B = 909k × 22p / 100k → 200.0 pF. That is made up of C_B1 150 + C_B2 15 → 165 pF, plus C_S 8.2 pF seen through R_S, plus ≈ 3 pF of parasitics, plus the trimmer. The trimmer therefore needs 200 − 165 − 8.2 − 3 → 23.8 pF, with 16.5–33 pF available. With the 1 % caps, tolerance adds ±5.8 pF of worst-case spread (Ct ±2.0, C_B1 ±1.5, C_B2 ±0.3, parasitics ±2), which the trimmer range covers.

## Power, reference and misc passives
| Function | Value | Refs | Notes |
|---|---|---|---|
| USB-C CC Rd | 5.1 kΩ 1 % | R1, R2 | |
| VBUS pre-switch cap | 4.7 µF 10 V X7R | C1 | Keeps pre-switch capacitance ≤ 10 µF (USB inrush) |
| V5 bulk / HF | 10 µF, 0.1 µF | C2, C3 | |
| Buck 3V3 in / out | 10 µF / 22 µF 10 V X7R/X5R | C4 / C5 | |
| Buck 3V3 FB top / bottom | 100 kΩ / 22.1 kΩ 1 % | R3 / R4 | 0.6 × (1 + 100/22.1) → 3.315 V |
| Buck 1V2 in / out | 10 µF / 22 µF | C6 / C7 | |
| Buck 1V2 FB top / bottom | 100 kΩ / 100 kΩ 1 % | R5 / R6 | 0.6 × 2 → 1.200 V |
| 1V8 LDO in / out | 1 µF / 1 µF | C8 / C9 | |
| Power LED R | 1 kΩ | R7 | (3.3 − 2.0)/1k → 1.3 mA |
| 3V3A LDO in / out / bulk | 1 µF / 1 µF / 10 µF | C10 / C11 / C12 | |
| LM27762 CIN / C1 / CP / COUT+ / COUT− | 2.2 µF / 1 µF / 4.7 µF / 2.2 µF / 2.2 µF, X7R ≥ 10 V | C13 / C14 / C15 / C16 / C17 | Per datasheet test conditions |
| LM27762 FB+ top / bottom | 174 kΩ / 100 kΩ 1 % | R8 / R9 | 1.2 × 274/100 → +3.288 V |
| LM27762 FB− top / bottom | 64.9 kΩ / 100 kΩ 1 % | R10 / R11 | −1.22 × 164.9/100 → −2.012 V |
| ADC ISET | 56.2 kΩ 1 % | R12 | Datasheet value |
| ADC REFT / REFB series | 2.0 Ω | R13 / R14 | Datasheet: 2 Ω + 0.1 µF |
| ADC REFT / REFB cap | 0.1 µF | C18 / C19 | |
| ADC CM caps | 0.1 µF, 1 µF | C20, C21 | |
| ADC AVDD decoupling | 0.1 µF ×3, 10 µF | C22, C23, C24, C25 | |
| ADC VDRV decoupling | 0.1 µF ×4, 10 µF | C26, C27, C28, C29, C30 | |
| ADC STPD pull-down | 10 kΩ | R15 | Default is not powered-down |
| XO decoupling | 0.1 µF, 1 µF | C31, C32 | |
| Clock series R | 33 Ω | R16, R17 | Source termination per branch |
| FPGA decoupling | 0.1 µF ×11 | C33–C43 | One per supply pin |
| FPGA bulk | 10 µF (V1V2), 10 µF (V3V3D), 4.7 µF (V1V8) | C44, C45, C46 | |
| FPGA MODE0/MODE1 pull-down | 10 kΩ | R18, R19 | Verify the AUTOBOOT code |
| FPGA RECONFIG_N pull-up | 10 kΩ → V1V8 | R20 | |
| LED resistors | 1 kΩ | R21, R22 | |
| Trigger series R | 100 Ω | R23, R24 | |
| FT232H crystal load caps | 33 pF C0G | C47, C48 | 2 × (20 − 3) → 34 → 33 pF |
| FT232H decoupling | 0.1 µF ×6, 4.7 µF ×2 | C49–C54, C55, C56 | |
| FT232H REF | 12.0 kΩ 1 % | R25 | FTDI requirement |
| FT232H RESET# pull-up | 10 kΩ | R26 | |
| EEPROM DO series | 2.2 kΩ | R27 | Verify against the FT232H DS |

Totals: U1–U11 (11) + U101, U102, U201, U202 (4) → **15 ICs**, plus 1 XO (X1), 1 crystal (Y1) and 5 connectors (J1–J5).
