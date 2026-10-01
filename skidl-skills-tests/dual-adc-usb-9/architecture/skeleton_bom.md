# dual_adc_usb — Skeleton BOM (rev 2)

**Rev 2 change column** (`Chg`): `ADDED` new ref; `MODIFIED-RESOURCE` MPN/value changed — must be re-sourced;
`MODIFIED-QTY` same MPN/value as an existing sourced row, refs/qty changed only; `MODIFIED-NET` same part,
only its connection changed (no sourcing action); `REMOVED`. Rows without a tag are unchanged — keep the
`sourcing/sourced_bom.csv` row verbatim. <!-- revised: escalation from 04_datasheets -->

Values are real E-series values; every one is used in the arithmetic in `net_plan.md`. "C0G" means
C0G/NP0 — mandatory wherever it appears (filter and divider accuracy). Passives 0402 unless noted;
0603 acceptable. Block refs are authoritative in `handoffs/02_architecture.md` § Parts by block.

| Refs | Function | Suggested MPN | Package | Qty | Notes | Chg |
|---|---|---|---|---|---|---|
| **usb_power_in** | | | | | | |
| J1 | USB-C receptacle, USB 2.0 (16-pin) | TYPE-C-31-M-12 | SMD | 1 | C165948 | |
| R1, R2 | CC Rd pull-downs | 5.1 kΩ 1 % | 0402 | 2 | | |
| U1 | USB ESD | USBLC6-2SC6 | SOT-23-6 | 1 | | |
| F1 | PTC, 0.75 A hold | SMD1206P075TF (or equiv.) | 1206 | 1 | not 0.5 A — derating | |
| D1 | VBUS TVS, 5 V standoff | SMF5.0A (or equiv.) | SOD-123F | 1 | | |
| U2 | Soft-start load switch | TPS22918DBVR | SOT-23-6 | 1 | | |
| R3 | ON pull-up to VBUS_F | 10 kΩ | 0402 | 1 | | |
| C1 | VBUS_F input | 4.7 µF 10 V X5R | 0603 | 1 | keep ≤ 10 µF upstream of U2 | |
| C2 | U2 CT | 1000 pF 16 V X7R | 0402 | 1 | tR 2.54 ms | |
| C3 | VBUS_SW bulk | 10 µF 10 V X5R | 0805 | 1 | | |
| **pwr_digital** | | | | | | |
| U3, U4, U12 | Buck 3V3D / 1V2 / **1V8** | TLV62569DBVR | SOT-23-5 | 3 | U12 added for +1V8 (VCCO3) | MODIFIED-QTY (U12 ADDED) |
| L1, L2, L3 | Buck inductor | 2.2 µH, ≥ 1.5 A Isat, DCR < 100 mΩ (sourced FHD4020S-2R2MT) | 2520/3015/4020 | 3 | | MODIFIED-QTY (L3 ADDED) |
| C4, C6, C9 | Buck inputs | 10 µF 10 V X5R | 0603 | 3 | same row as C63/C68/C84/C92 in sourced BOM | MODIFIED-QTY (C9 ADDED) |
| C5, C7, C17 | Buck outputs | 22 µF 6.3 V X5R | 0805 | 3 | | MODIFIED-QTY (C17 ADDED) |
| R5, R7 | FB top | 100 kΩ 1 % | 0402 | 2 | | |
| R14 | FB top 1V8 | **200 kΩ 1 %** | 0402 | 1 | → 1.800 V with R15; value fixed | ADDED (new value — source) |
| R6 | FB bottom 3V3D | 22 kΩ 1 % | 0402 | 1 | → 3.327 V | |
| R8, R15 | FB bottom 1V2 / 1V8 | 100 kΩ 1 % | 0402 | 2 | → 1.200 V / 1.800 V | MODIFIED-QTY (R15 ADDED) |
| R9, C8 | U3 EN delay | 100 kΩ / 100 nF X7R | 0402 | 1+1 | 3V3D after 1V2 | |
| **pwr_analog** | | | | | | |
| U5 | LDO +3V3A | TLV75733PDBVR | SOT-23-5 | 1 | | |
| C10 / C11 | LDO in / out | 1 µF / 2.2 µF X5R | 0402/0603 | 1+1 | | |
| U6 | ±AFE rails | LM27762DSSR | WSON-12 2×3 | 1 | | |
| C12, C15, C16 | VIN, OUT+, OUT– | 2.2 µF 10 V X5R | 0603 | 3 | | |
| C13 | Flying cap | 1 µF 10 V X5R | 0402 | 1 | | |
| C14 | CP reservoir | 4.7 µF 10 V X5R | 0603 | 1 | | |
| R10, R12 | FB tops | 180 kΩ 1 % | 0402 | 2 | | |
| R11, R13 | FB bottoms | 100 kΩ 1 % | 0402 | 2 | ≥ 50 kΩ rule | |
| **afe_ch_a** (×1) and **afe_ch_b** (×1, refs +20) | | | | | qty below is per channel | |
| J2 / J3 | BNC female, PCB right-angle | KH-BNC50-3511 | THT | 1 | | |
| R20 / R40 | Attenuator top | 910 kΩ 1 % ≥150 V | **1206** | 1 | | |
| C20 / C40 | Attenuator top cap | 18 pF C0G 100 V | 0603 | 1 | | |
| C21 / C41 | Comp trimmer | STC3MA06-T1 (2–6 pF 100 V) | 4.5×3.2 mm | 1 | | |
| R21 / R41 | Attenuator bottom | 100 kΩ 1 % | 0402 | 1 | | |
| C22 / C42 | Attenuator bottom cap | 200 pF C0G 50 V | 0402 | 1 | | |
| D20 / D40 | Rail clamp | BAV199 | SOT-23 | 1 | | |
| R22 / R42 | Buffer input series | 1.0 kΩ 1 % | 0402 | 1 | | |
| U20 / U40 | FET buffer | OPA810IDBVR | SOT-23-5 | 1 | | |
| C23, C24 / C43, C44 | Buffer decoupling | 100 nF X7R | 0402 | 2 | | |
| R23, R24 / R43, R44 | MFB input (R1) | 1.1 kΩ 0.1–1 % | 0402 | 2 | match pair | |
| R25, R26 / R45, R46 | MFB feedback (R2) | 1.0 kΩ 0.1–1 % | 0402 | 2 | match pair | |
| R27, R28 / R47, R48 | MFB R3 | 270 Ω 1 % | 0402 | 2 | | |
| C25, C26 / C45, C46 | MFB Csh | 100 pF C0G | 0402 | 2 | | |
| C27, C28 / C47, C48 | MFB Cfb | 12 pF C0G | 0402 | 2 | | |
| U21 / U41 | FDA | THS4521IDGKR | MSOP-8 | 1 | | |
| C29 / C49 | FDA decoupling | 100 nF X7R | 0402 | 1 | | |
| R29, R30 / R49, R50 | ADC isolation | 33 Ω 1 % | 0402 | 2 | | |
| C30 / C50 | ADC diff cap | 270 pF C0G | 0402 | 1 | | |
| C31 / C51 | VOCM decoupling | 100 nF X7R | 0402 | 1 | | |
| **adc_dual** | | | | | | |
| U7 | Dual 12-bit 40 MSPS ADC | ADS5231IPAGT | TQFP-64 10×10 | 1 | critical path | |
| C60–C62, C64–C67, C69, C71, C72 | Decoupling / ref bypass | 100 nF X7R | 0402 | 10 | | |
| C63, C68 | AVDD / VDRV bulk | 10 µF 6.3 V X5R | 0603 | 2 | | |
| C70, C73 | REFT / REFB bulk | 2.2 µF X5R | 0402 | 2 | | |
| R60, R61 | REFT / REFB series | 2.0 Ω 1 % | 0402 | 2 | | |
| R62 | ISET | 56.2 kΩ 1 % (E96) | 0402 | 1 | | |
| **clock_gen** | | | | | | |
| Y1 | 40 MHz 3.3 V CMOS XO | **OT322540MJBA4SL** (YXC YSO110TR, C2831396) | 3225-4P | 1 | 0.7 ps rms max 12 k–20 MHz (DS), 5 mA; pinout 1 OE/2 GND/3 OUT/4 VDD = old part. Free substitute only with a **published** jitter ≤ 5 ps (e.g. TAITIEN OXETGLJANF-40.000000MHZ C7470494, 1 ps max) | MODIFIED-RESOURCE |
| U8 | Clock buffer | SN74LVC1G34DCKR (or DBVR) | SC-70-5 | 1 | still on +3V3D | |
| R70, R71 | Series termination | 33 Ω | 0402 | 2 | | |
| C75, C76 | Decoupling | 100 nF | 0402 | 2 | | |
| **fpga** | | | | | | |
| U9 | FPGA + 64 Mb PSRAM | GW1NR-LV9QN88PC6/I5 | QFN-88 10×10 0.4 mm | 1 | critical path | |
| C80–C83, C85–C91 | Decoupling | 100 nF | 0402 | 11 | one per power pin; C91 now on VCCO3/+1V8 | MODIFIED-NET (C91) |
| C84, C92, C93 | Bulk 1V2 / 3V3 / **1V8** | 10 µF X5R | 0603 | 3 | | MODIFIED-QTY (C93 ADDED) |
| R80, R81, R85 | R80 RECONFIG_N / R85 JTAGSEL_N pull-ups to **+1V8**; R81 TCK pull-down to GND | 4.7 kΩ | 0402 | 3 | | MODIFIED-QTY + MODIFIED-NET |
| ~~R82~~ | ~~FPGA_DONE pull-up~~ | — | — | 0 | DONE/READY not bonded on QN88P | REMOVED |
| R83, R84 | MODE pull-downs | 1.0 kΩ | 0402 | 2 | keystone K4 | |
| R86, R87 | LED resistors | 1.0 kΩ | 0402 | 2 | | |
| D80, D81 | Status LEDs | green 0603 | 0603 | 2 | | |
| R88, R89 | Trigger I/O series | 100 Ω | 0402 | 2 | | |
| J4 | JTAG header | 1×6 2.54 mm | THT | 1 | pin 1 VREF = +1V8; programmer must support 1.8 V | MODIFIED-NET |
| J5 | Trigger header | 1×3 2.54 mm | THT | 1 | | |
| **usb_bridge** | | | | | | |
| U10 | USB 2.0 HS FIFO bridge | FT232HL-REEL | LQFP-48 | 1 | critical path | |
| U11 | Config EEPROM | 93LC56BT-I/OT | SOT-23-6 | 1 | | |
| Y2 | 12 MHz crystal | X322512MSB4SI | 3225 | 1 | Basic tier | |
| C110, C111 | Crystal load caps | **33 pF C0G 50 V** | 0402 | 2 | Y2 CL 20 pF: 16.5 + 3–5 pF stray = 19.5–21.5 pF | MODIFIED-RESOURCE |
| C100–C107, C109 | Decoupling | 100 nF | 0402 | 9 | | |
| C108 | Bulk | 4.7 µF X5R | 0603 | 1 | | |
| R100 | REF | 12 kΩ 1 % | 0402 | 1 | | |
| R101 | RESET# pull-up | 10 kΩ | 0402 | 1 | | |
| R102, R103 | EEPROM interface | 10 kΩ / 2.2 kΩ (DS_FT232H Table 3.3, verified) | 0402 | 2 | | |

## Rev 2 sourcing worklist <!-- revised -->
Re-source (new MPN/value): **Y1** OT322540MJBA4SL; **C110, C111** 33 pF C0G 0402; **R14** 200 kΩ 1 % 0402.
Add refs to existing sourced rows (no search): U12 → TLV62569DBVR row; L3 → FHD4020S-2R2MT row; C9, C93 →
10 µF 0603 row (CL10A106KP8NNNC); C17 → 22 µF 0805 row; R15 → 100 kΩ row.
Remove: R82 from the 4.7 kΩ row (qty 4 → 3; R81 stays, now a TCK pull-down).
No action: C91, J4, R80, R85, R81 (net-only changes), U8.
