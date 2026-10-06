# BOM: Dual-Channel ±10 V, 12-bit, 10 MSPS USB ADC Board

Status: stage 3 (part selection). Derived from docs/SPEC.md and docs/SUBSYSTEMS.md.

**Conventions**
- **One row per refdes.**
- **Value** holds only the component value. All explanation is in **Rationale**.
- **New MPNs:** every MPN introduced here is marked **UNVERIFIED**, together with the datasheet figure that must be checked.
- **Symbol status:**
  - `SYM✓` means search_symbols and symbol_pins were both run in stage 3.
  - `SYM?` means the symbol was found by search_symbols but its pins were not checked, or the symbol was not searched at all. Stage 4 must run search_symbols/symbol_pins for every `SYM?` row before drawing it. If the symbol is missing, substitute a part from the same family.
- **Iq / leakage:** every part on 3V3_AON or raw VBUS has its suspend contribution checked against `power.aon_suspend_allocation_mA` (≤1.75 mA) and `power.suspend_current_mA` (≤2.5 mA).

## Open issues raised by this stage (must be resolved by recorded decision, not silently accepted)

1. **BLOCKER: `analog.dc_accuracy` vs the only installed dual 12-bit ≥10 MSPS ADC symbol.**
   - **Why the LTC2290 is the choice.** The AD9238 has no installed symbol. The installed alternatives (AD9280/AD9283, ADC122Sxxx, ADC1283) are 8-bit or ≤1 MSPS. That leaves the LTC2290, symbol `Analog_ADC:LTC2290xUP`.
   - **Offset.** The LTC2290 datasheet offset is expected to be about ±2 mV typ and ±12 mV max. That is above the ≤0.9 mV ADC allocation in SUBSYSTEMS §7.6, and gives up to about 126 mV referred to input (RTI).
   - **Gain error.** Its internal-reference gain error is expected to be about ±1.5 % FS. That is above the ≤0.5 % allocation (UNVERIFIED).
   - **What this means.** The *uncalibrated* ≤1 % / ±20 mV ASSUMED limit cannot be met. On-board calibration constants (SUBSYSTEMS §10) would correct it after calibration. The user must decide between two options:
     - (a) Revise the ASSUMED `analog.dc_accuracy` so it applies after calibration.
     - (b) Install a different ADC symbol library.
   - No stage may proceed on dc_accuracy until that decision is recorded.
2. **Rail change (SUBSYSTEMS §2.1 and §8 need updating).** The LTC2290 runs from VDD = 2.7–3.4 V, so `1V8_A` is replaced by `3V3_ADC`, a low-noise LDO from VBUS_SW.
   - **Load allocation.** About 45 mA at 10 MSPS (UNVERIFIED). Moving this load from 3V3_D (LDO input, 60 mA) to VBUS_SW (linear, 45 mA) lowers the VBUS total.
   - **`1V8_D` is kept.** It feeds LTC2290 OVDD (0.5–3.6 V) and FPGA bank VCCIO, so the ADC↔FPGA bank stays at 1.8 V as before.
3. **PWREN_N polarity.** The TPS22917 ON pin is active-high, so PWREN_N drives it through P-FET Q1 with a pull-down on ON.
   - **Why a P-FET.** In suspend (PWREN_N high) Q1 is off, so the pull-down conducts 0 µA.
   - **Why not an N-FET with a pull-up to 3V3_AON.** That arrangement would conduct about 33 µA in suspend, which violates the SUBSYSTEMS §2.4 rule "no conducting pull on 3V3_AON".
4. **Bus switch.** No 16-bit CBT symbol is installed, so two 10-bit 74CBTLV3861 are used.
   - Their combined ICC (2 × ≤10 µA, UNVERIFIED) exactly uses the ≤0.02 mA allocation, with no margin.

## BOM

| Refdes | Value | Footprint | MPN | Rationale |
|--------|-------|-----------|-----|-----------|
| J1 | USB_C_Receptacle_USB2.0_16P | Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal | USB4105-GF-A (UNVERIFIED: check 16-pin USB2.0 pinout A5/B5 CC, A6/B6 D+, A7/B7 D-) | SYM✓ Connector:USB_C_Receptacle_USB2.0_16P. USB-C sink, USB 2.0 HS data, no PD (SPEC §4.5). Passive, 0 µA. |
| J2 | BNC | Connector_Coaxial:BNC_Amphenol_031-5431 | 031-5431 (UNVERIFIED: right-angle PCB BNC, shell to GND) | SYM? Connector:Conn_Coaxial. CH1 input, mates scope probes (SPEC §4.1). |
| J3 | BNC | Connector_Coaxial:BNC_Amphenol_031-5431 | 031-5431 (UNVERIFIED: same as J2) | SYM? Connector:Conn_Coaxial. CH2 input. |
| J4 | Conn_02x05_Odd_Even | Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical | generic 2x5 1.27 mm header | SYM? Connector_Generic:Conn_02x05_Odd_Even. SPI flash programming plus CRESET_B (SUBSYSTEMS §10). |
| U1 | FT232H | Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm | FT232HQ-REEL (UNVERIFIED: datasheet ICC operating ≤60 mA, suspend ≤1.2 mA; check DC table) | SYM✓ Interface_USB:FT232H. USB bridge, sync 245 FIFO (SPEC §4.6). Its suspend current is the largest item in the 1.75 mA AON allocation; preconfig ~61 mA ≤100 mA. |
| U2 | 93LC56B | Package_SO:SOIC-8_3.9x4.9mm_P1.27mm | 93LC56BT-I/SN (UNVERIFIED: x16 org, standby ≤1 µA at 3.3 V) | SYM✓ Memory_EEPROM:93LCxxB (93LC56 has no exact symbol). FT232H config plus cal constants on 3V3_AON. ~1 µA ≤0.01 mA allocation. |
| U3 | 74CBTLV3861 | Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm | SN74CBTLV3861PWR (UNVERIFIED: ICC ≤10 µA, Ioff spec for partial power-down) | SYM✓ 74xx:74CBTLV3861. FIFO bus switch bits 1-10, VCC on 3V3_AON, ~OE = BUS_OE_N. Default off prevents back-powering the FPGA (SUBSYSTEMS §2.7). |
| U4 | 74CBTLV3861 | Package_SO:TSSOP-24_4.4x7.8mm_P0.65mm | SN74CBTLV3861PWR (UNVERIFIED: as U3) | SYM✓ 74xx:74CBTLV3861. FIFO bus switch bits 11-15 (5 spare channels tied to GND on both sides). Together with U3, 20 µA = the full 0.02 mA allocation. |
| U5 | MCP1700-3302E | Package_TO_SOT_SMD:SOT-23 | MCP1700T-3302E/TT (UNVERIFIED: Iq 1.6 µA typ / 4 µA max, VIN max 6 V, 250 mA) | SYM✓ Regulator_Linear:MCP1700x-330xxTT. 3V3_AON LDO. Iq ≤4 µA ≤0.1 mA allocation, 250 mA ≥61 mA, 6 V ≥5.25 V. |
| U6 | TPS22917 | Package_TO_SOT_SMD:SOT-23-6 | TPS22917DBVR (UNVERIFIED: VIN 1-5.5 V, 2 A, shutdown leakage ≤1 µA, CT slew rate) | SYM✓ Power_Management:TPS22917DBV. VBUS→VBUS_SW soft-start switch. CT (C30) sets ≥3 ms rise. Off-leakage ~0.5 µA ≤0.01 mA allocation. |
| U7 | iCE40HX4K-TQ144 | Package_QFP:TQFP-144_20x20mm_P0.5mm | ICE40HX4K-TQ144 (UNVERIFIED: 107 user I/O, 1.2 V core, VCCIO per bank) | SYM✓ FPGA_Lattice:ICE40HX4K-TQ144 (5 units). Capture/control, no MCU (SUBSYSTEMS §4). Bank for ADC on 1V8_D, others on 3V3_D. Gated, 0 µA in suspend. |
| U8 | MT48LC16M16A2P-6A | Package_SO:TSOP-II-54_22.2x10.16mm_P0.8mm | MT48LC16M16A2P-6A:G (UNVERIFIED: 256 Mbit x16, 3.3 V, IDD avg vs 70 mA allocation) | SYM✓ Memory_RAM:MT48LC16M16A2P. 32 MB buffer ≥4 MB, ~0.84 s/ch ≥0.1 s. On 3V3_D (gated). |
| U9 | W25Q32JV | Package_SO:SOIC-8_5.23x5.23mm_P1.27mm | W25Q32JVSSIQ (UNVERIFIED: 32 Mbit ≥ iCE40HX4K bitstream, 3.3 V, standby ≤50 µA) | SYM? Memory_Flash:W25Q32JVSS. FPGA config flash on 3V3_D (gated, so standby is irrelevant to suspend). |
| U10 | LTC2290 | Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP7.15x7.15mm | LTC2290CUP#PBF (UNVERIFIED: dual 12-bit 10 MSPS, VDD 2.7-3.4 V, OVDD 0.5-3.6 V, offset/gain error, SNR ~71 dB, aperture jitter) | SYM✓ Analog_ADC:LTC2290xUP. The only installed dual simultaneous 12-bit ≥10 MSPS symbol. 2 Vpp diff (SENSE=VDD), VCMA 1.5 V → FDA VOCM. Offset/gain likely violate the §7.6 allocation: BLOCKER, see Open issue 1. |
| U11 | TLV62084 | Package_SON:WSON-6-1EP_2x2mm_P0.65mm_EP1x1.6mm | TLV62084ADSGR (UNVERIFIED: VIN 2.5-6 V, 2 A, η ≥88 % at 200 mA, Iq ~17 µA) | SYM? Regulator_Switching:TLV62084ADSGx (seen in search, pins not checked). 3V3_D buck from VBUS_SW. Gated, so its Iq does not count in suspend. |
| U12 | MCP1700-1202E | Package_TO_SOT_SMD:SOT-23 | MCP1700T-1202E/TT (UNVERIFIED: 1.2 V, VIN 2.3-6 V, 250 mA) | SYM? Regulator_Linear:MCP1700x-120xxTT (family confirmed). 1V2_FPGA from 3V3_D, 30 mA allocation. |
| U13 | MCP1700-1802E | Package_TO_SOT_SMD:SOT-23 | MCP1700T-1802E/TT (UNVERIFIED: 1.8 V, 250 mA) | SYM? Regulator_Linear:MCP1700x-180xxTT (family confirmed). 1V8_D for LTC2290 OVDD and FPGA ADC bank, 15 mA. |
| U14 | TPS7A2033 | Package_TO_SOT_SMD:SOT-23-5 | TPS7A2033PDBVR (UNVERIFIED: 300 mA, noise ~6 µVrms, PSRR ≥40 dB at 1-2 MHz) | SYM? Symbol not searched. 3V3_ADC low-noise LDO from VBUS_SW for LTC2290 VDD (replaces 1V8_A, ~45 mA). |
| U15 | TPS7A2033 | Package_TO_SOT_SMD:SOT-23-5 | TPS7A2033PDBVR (UNVERIFIED: as U14) | SYM? Symbol not searched. 3V3_CLK low-noise LDO for XO and fanout, noise ≤10 µVrms requirement (SUBSYSTEMS §6). |
| U16 | TPS65131 | Package_DFN_QFN:VQFN-24-1EP_4x4mm_P0.5mm_EP2.45x2.45mm | TPS65131RGER (UNVERIFIED: VIN 2.7-5.5 V, ±6 V out, η ≥75 % at 20 mA, separate ENP/ENN) | SYM? Regulator_Switching:TPS65131RGE (seen in search, pins not checked). ±6V_RAW from VBUS_SW, ENP/ENN = AFE_EN. |
| U17 | TPS7A4901 | Package_SO:MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm | TPS7A4901DGNR (UNVERIFIED: adj positive LDO, VIN to 36 V, low noise) | SYM? Symbol not searched. +5V_A from +6V_RAW, 20 mA. |
| U18 | TPS7A3001 | Package_SO:MSOP-8-1EP_3x3mm_P0.65mm_EP1.68x1.88mm | TPS7A3001DGNR (UNVERIFIED: adj negative LDO, low noise) | SYM? Symbol not searched. -5V_A from -6V_RAW, 15 mA. |
| U19 | 10MHz | Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm | ASFLMB-10.000MHZ (UNVERIFIED: 3.3 V CMOS, phase jitter ≤1 ps rms 12 kHz-5 MHz) | SYM? Symbol not searched (generic Oscillator symbol expected). ADC/FPGA reference clock; XO budget 1.0 ps (SUBSYSTEMS §6). |
| U20 | LMK1C1102 | Package_SON:WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm | LMK1C1102DQFR (UNVERIFIED: 1:2 LVCMOS fanout, additive jitter ≤0.3 ps) | SYM? Symbol not searched. Out A → LTC2290 CLKA/CLKB, out B → FPGA GBIN. |
| U21 | OPA810 | Package_TO_SOT_SMD:SOT-23-5 | OPA810IDBVR (UNVERIFIED: GBW 70 MHz, SR 192 V/µs, Ib ≤20 pA, Vos ≤0.5 mV, Iq ~3.7 mA) | SYM✓ Amplifier_Operational:OPA810xDBV. CH1 buffer, G=+1 on ±5V_A (SUBSYSTEMS §7.3). |
| U22 | OPA810 | Package_TO_SOT_SMD:SOT-23-5 | OPA810IDBVR (UNVERIFIED: as U21) | SYM✓ Amplifier_Operational:OPA810xDBV. CH2 buffer. |
| U23 | THS4551 | Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm | THS4551IRGTR (UNVERIFIED: Iq ~1.4 mA, output offset, HD2/HD3 ≤-80 dBc at 1 MHz) | SYM✓ Amplifier_Difference:THS4551xRGT (2 units). CH1 FDA, G=0.475, VOCM = LTC2290 VCMA (1.5 V), single +5V_A. |
| U24 | THS4551 | Package_DFN_QFN:VQFN-16-1EP_3x3mm_P0.5mm_EP1.68x1.68mm | THS4551IRGTR (UNVERIFIED: as U23) | SYM✓ Amplifier_Difference:THS4551xRGT. CH2 FDA, VOCM = LTC2290 VCMB. |
| Q1 | BSS84 | Package_TO_SOT_SMD:SOT-23 | BSS84 (UNVERIFIED: Vgs(th) ≤-2 V, Idss ≤1 µA) | SYM? Symbol not searched. PWREN_N → TPS22917 ON inverter, P-FET from 3V3_AON. Off in suspend, so the pull-down R4 draws 0 µA (Open issue 3). |
| Q2 | BSS138 | Package_TO_SOT_SMD:SOT-23 | BSS138 (UNVERIFIED: Vgs(th) ≤1.5 V, Idss ≤1 µA) | SYM? Symbol not searched. Pulls BUS_OE_N low when PG_3V3D is high. Off in suspend, so pull-up R5 draws 0 µA. |
| D1 | BAV199 | Package_TO_SOT_SMD:SOT-23 | BAV199 (UNVERIFIED: reverse leakage ≤5 nA at 5 V, series pair) | SYM? Symbol not searched. CH1 tap clamp to ±5V_A (SUBSYSTEMS §7.2). |
| D2 | BAV199 | Package_TO_SOT_SMD:SOT-23 | BAV199 (UNVERIFIED: as D1) | SYM? Symbol not searched. CH2 tap clamp. |
| D3 | USBLC6-2SC6 | Package_TO_SOT_SMD:SOT-23-6 | USBLC6-2SC6 (UNVERIFIED: ≤1 pF/line? check, leakage ≤1 µA, VBUS clamp) | SYM? Symbol not searched. D+/D- ESD and VBUS TVS on raw VBUS; leakage counts in the 0.05 mA ESD allocation. |
| D4 | LED_Green | LED_SMD:LED_0603_1608Metric | generic 0603 green | SYM? Device:LED. LED_PWR on 3V3_D (gated). No LED on 3V3_AON, intentional (suspend budget). |
| D5 | LED_Yellow | LED_SMD:LED_0603_1608Metric | generic 0603 yellow | SYM? Device:LED. LED_ARM on 3V3_D. |
| D6 | LED_Red | LED_SMD:LED_0603_1608Metric | generic 0603 red | SYM? Device:LED. LED_OVR on 3V3_D. |
| Y1 | 12MHz | Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm | ABM8-12.000MHZ-B2-T (UNVERIFIED: CL per FT232H datasheet) | SYM? Device:Crystal_GND24. FT232H reference crystal. |
| L1 | 1uH | Inductor_SMD:L_1210_3225Metric | XFL3012-102ME (UNVERIFIED: Isat ≥1 A) | SYM? Device:L. TLV62084 buck inductor. |
| L2 | 4.7uH | Inductor_SMD:L_1210_3225Metric | XFL3012-472ME (UNVERIFIED: Isat ≥0.8 A) | SYM? Device:L. TPS65131 boost inductor. |
| L3 | 4.7uH | Inductor_SMD:L_1210_3225Metric | XFL3012-472ME (UNVERIFIED: as L2) | SYM? Device:L. TPS65131 inverter inductor. |
| L4 | 2.2uH | Inductor_SMD:L_0805_2012Metric | LQM21PN2R2 (UNVERIFIED: nominal; final value from elliptic synthesis in stage 4) | SYM? Device:L. CH1 AA filter, + leg. |
| L5 | 2.2uH | Inductor_SMD:L_0805_2012Metric | LQM21PN2R2 (UNVERIFIED: as L4) | SYM? Device:L. CH1 AA filter, - leg. |
| L6 | 2.2uH | Inductor_SMD:L_0805_2012Metric | LQM21PN2R2 (UNVERIFIED: as L4) | SYM? Device:L. CH2 AA filter, + leg. |
| L7 | 2.2uH | Inductor_SMD:L_0805_2012Metric | LQM21PN2R2 (UNVERIFIED: as L4) | SYM? Device:L. CH2 AA filter, - leg. |
| R1 | 5.1k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. CC1 Rd; current comes from host Rp, not VBUS. |
| R2 | 5.1k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. CC2 Rd (separate from R1, required for orientation). |
| R3 | 100k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. PWREN_N pull-up to 3V3_AON. Node is high in suspend, so 0 µA. |
| R4 | 100k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. TPS22917 ON pull-down. Q1 is off in suspend, so 0 µA. |
| R5 | 100k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. BUS_OE_N pull-up to 3V3_AON. Q2 is off in suspend, so 0 µA. |
| R6 | 12k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. FT232H REF (RREF) per datasheet. |
| R7 | 10k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. FT232H ~RESET pull-up to 3V3_AON. Node is high, so 0 µA. |
| R8 | 1M | Resistor_SMD:R_0603_1608Metric | generic | Device:R. USB shield to GND (with C9). |
| R9 | 10k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. PG_3V3D / FPGA ~CRESET pull-up to 3V3_D (gated). |
| R10 | 2.2k | Resistor_SMD:R_0402_1005Metric | generic | Device:R. LED_PWR series, ~1 mA. |
| R11 | 2.2k | Resistor_SMD:R_0402_1005Metric | generic | Device:R. LED_ARM series. |
| R12 | 2.2k | Resistor_SMD:R_0402_1005Metric | generic | Device:R. LED_OVR series. |
| R13 | 200k | Resistor_SMD:R_1206_3216Metric | TNPW1206200KBEEA (UNVERIFIED: 0.1 %, 200 V rating) | Device:R. CH1 R_top segment 1 of 4 (4×200k = 800k, each segment ≤7.5 V at a 30 V fault). |
| R14 | 200k | Resistor_SMD:R_1206_3216Metric | TNPW1206200KBEEA (UNVERIFIED: as R13) | Device:R. CH1 R_top segment 2. |
| R15 | 200k | Resistor_SMD:R_1206_3216Metric | TNPW1206200KBEEA (UNVERIFIED: as R13) | Device:R. CH1 R_top segment 3. |
| R16 | 200k | Resistor_SMD:R_1206_3216Metric | TNPW1206200KBEEA (UNVERIFIED: as R13) | Device:R. CH1 R_top segment 4. |
| R17 | 200k | Resistor_SMD:R_0603_1608Metric | TNPW0603200KBEEA (UNVERIFIED: 0.1 %) | Device:R. CH1 R_bot; R_in = 1.000 MΩ. |
| R18 | 1k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. CH1 series R from tap to U21 +IN (limits ESD-diode current). |
| R19 | 1k | Resistor_SMD:R_0402_1005Metric | TNPW04021K00BEED (UNVERIFIED: 0.1 %) | Device:R. CH1 FDA Rg, + side. |
| R20 | 1k | Resistor_SMD:R_0402_1005Metric | TNPW04021K00BEED (UNVERIFIED: 0.1 %) | Device:R. CH1 FDA Rg, - side (to GND). |
| R21 | 475 | Resistor_SMD:R_0402_1005Metric | TNPW0402475RBEED (UNVERIFIED: 0.1 %) | Device:R. CH1 FDA Rf, +; G = 0.475. |
| R22 | 475 | Resistor_SMD:R_0402_1005Metric | TNPW0402475RBEED (UNVERIFIED: 0.1 %) | Device:R. CH1 FDA Rf, -. |
| R23 | 200k | Resistor_SMD:R_1206_3216Metric | TNPW1206200KBEEA (UNVERIFIED: as R13) | Device:R. CH2 R_top segment 1 of 4. |
| R24 | 200k | Resistor_SMD:R_1206_3216Metric | TNPW1206200KBEEA (UNVERIFIED: as R13) | Device:R. CH2 R_top segment 2. |
| R25 | 200k | Resistor_SMD:R_1206_3216Metric | TNPW1206200KBEEA (UNVERIFIED: as R13) | Device:R. CH2 R_top segment 3. |
| R26 | 200k | Resistor_SMD:R_1206_3216Metric | TNPW1206200KBEEA (UNVERIFIED: as R13) | Device:R. CH2 R_top segment 4. |
| R27 | 200k | Resistor_SMD:R_0603_1608Metric | TNPW0603200KBEEA (UNVERIFIED: 0.1 %) | Device:R. CH2 R_bot. |
| R28 | 1k | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. CH2 series R to U22 +IN. |
| R29 | 1k | Resistor_SMD:R_0402_1005Metric | TNPW04021K00BEED (UNVERIFIED: 0.1 %) | Device:R. CH2 FDA Rg, +. |
| R30 | 1k | Resistor_SMD:R_0402_1005Metric | TNPW04021K00BEED (UNVERIFIED: 0.1 %) | Device:R. CH2 FDA Rg, -. |
| R31 | 475 | Resistor_SMD:R_0402_1005Metric | TNPW0402475RBEED (UNVERIFIED: 0.1 %) | Device:R. CH2 FDA Rf, +. |
| R32 | 475 | Resistor_SMD:R_0402_1005Metric | TNPW0402475RBEED (UNVERIFIED: 0.1 %) | Device:R. CH2 FDA Rf, -. |
| R33 | 100 | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. CH1 AA filter termination at LTC2290 AINA (absorbs kickback, limits back-feed current). |
| R34 | 100 | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. CH2 AA filter termination at AINB. |
| R35 | 33 | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. Fanout out A series termination to ADC clock. |
| R36 | 33 | Resistor_SMD:R_0402_1005Metric | generic 1 % | Device:R. Fanout out B series termination to FPGA GBIN. |
| C1 | 1uF | Capacitor_SMD:C_0603_1608Metric | generic X7R 10 V | Device:C. U5 input on raw VBUS (counts toward ≤2.2 µF). |
| C2 | 1uF | Capacitor_SMD:C_0603_1608Metric | generic X7R 10 V | Device:C. U6 input on raw VBUS. Total direct VBUS = 2.0 µF ≤2.2 µF. |
| C3 | 1uF | Capacitor_SMD:C_0603_1608Metric | generic X7R 10 V | Device:C. U5 output, 3V3_AON. |
| C4 | 2.2uF | Capacitor_SMD:C_0603_1608Metric | generic X7R 10 V | Device:C. FT232H VREGIN. 3V3_AON total ≈4.6 µF ≤6.8 µF. |
| C5 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. FT232H VCCIO pin 12. |
| C6 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. FT232H VCCIO pin 24. |
| C7 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. FT232H VCCIO pin 46. |
| C8 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. FT232H VCCA pin 37. |
| C9 | 4.7nF | Capacitor_SMD:C_0603_1608Metric | generic X7R 50 V | Device:C. USB shield to GND (with R8). |
| C10 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. FT232H VCCCORE pin 38. |
| C11 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. FT232H VPHY/VPLL. |
| C12 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U2 VCC. |
| C13 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U3 VCC. |
| C14 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U4 VCC. |
| C15 | 18pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. Y1 load. |
| C16 | 18pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. Y1 load. |
| C17 | 22uF | Capacitor_SMD:C_0805_2012Metric | generic X5R 10 V | Device:C. VBUS_SW bulk (gated; total gated bulk ≤100 µF). |
| C18 | 22uF | Capacitor_SMD:C_0805_2012Metric | generic X5R 10 V | Device:C. 3V3_D buck output. |
| C19 | 10uF | Capacitor_SMD:C_0805_2012Metric | generic X5R 16 V | Device:C. +6V_RAW. |
| C20 | 10uF | Capacitor_SMD:C_0805_2012Metric | generic X5R 16 V | Device:C. -6V_RAW. |
| C21 | 10uF | Capacitor_SMD:C_0805_2012Metric | generic X5R 10 V | Device:C. +5V_A out (≤10 µF per rail, SUBSYSTEMS §2.7). |
| C22 | 10uF | Capacitor_SMD:C_0805_2012Metric | generic X5R 10 V | Device:C. -5V_A out (≤10 µF). |
| C23 | 4.7uF | Capacitor_SMD:C_0603_1608Metric | generic X5R | Device:C. 3V3_ADC out. |
| C24 | 4.7uF | Capacitor_SMD:C_0603_1608Metric | generic X5R | Device:C. 3V3_CLK out. |
| C25 | 1uF | Capacitor_SMD:C_0603_1608Metric | generic X7R | Device:C. 1V2_FPGA out. |
| C26 | 1uF | Capacitor_SMD:C_0603_1608Metric | generic X7R | Device:C. 1V8_D out. |
| C27 | 22pF | Capacitor_SMD:C_0603_1608Metric | generic C0G 100 V | Device:C. CH1 C_top (∥ 800k); C_in ≈20 pF. |
| C28 | 82pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. CH1 C_bot fixed part (with trimmer C29 and parasitics ≈100 pF). |
| C29 | 5-30pF | Capacitor_THT:C_Trimmer_Murata_TZB4-A | TZB4Z300AB10 (UNVERIFIED) | SYM? Device:C_Trim. CH1 divider compensation trimmer. |
| C30 | 10nF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U6 CT, sets VBUS_SW rise ≥3 ms (check TPS22917 slew table). |
| C31 | 22pF | Capacitor_SMD:C_0603_1608Metric | generic C0G 100 V | Device:C. CH2 C_top. |
| C32 | 82pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. CH2 C_bot fixed. |
| C33 | 5-30pF | Capacitor_THT:C_Trimmer_Murata_TZB4-A | TZB4Z300AB10 (UNVERIFIED) | SYM? Device:C_Trim. CH2 compensation trimmer. |
| C34 | 330pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. CH1 AA filter shunt 1 (diff), nominal; final from synthesis. |
| C35 | 680pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. CH1 AA filter shunt 2 (diff). |
| C36 | 330pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. CH1 AA filter shunt 3 at ADC (absorbs kickback). |
| C37 | 330pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. CH2 AA filter shunt 1. |
| C38 | 680pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. CH2 AA filter shunt 2. |
| C39 | 330pF | Capacitor_SMD:C_0402_1005Metric | generic C0G | Device:C. CH2 AA filter shunt 3. |
| C40 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U10 VDD. |
| C41 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U10 OVDD. |
| C42 | 2.2uF | Capacitor_SMD:C_0603_1608Metric | generic X5R | Device:C. U10 REFHA-REFLA (per datasheet). |
| C43 | 2.2uF | Capacitor_SMD:C_0603_1608Metric | generic X5R | Device:C. U10 REFHB-REFLB. |
| C44 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U21 V+. |
| C45 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U21 V-. |
| C46 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U22 V+. |
| C47 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U22 V-. |
| C48 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U23 VS+. |
| C49 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U24 VS+. |
| C50 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U8 SDRAM VDD/VDDQ (more per-pin caps placed in stage 4). |
| C51 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U7 FPGA VCC/VCCIO (more per-pin caps placed in stage 4). |
| C52 | 0.1uF | Capacitor_SMD:C_0402_1005Metric | generic X7R | Device:C. U19/U20 clock supply. |

## Power budget check (stage-3 part values)

| Budget | Calculation | Result |
|--------|-------------|--------|
| Suspend AON allocation ≤1.75 mA | FT232H ≤1.2 (UNVERIFIED) + D+ pull-up 0.20 + U5 0.004 + U3/U4 0.020 + U2 0.001 + U6 off 0.001 + Q1/Q2 Idss 0.002 + D3 ≤0.001 + R3/R4/R5/R7 0 | ≈1.43 mA ✓ (≤2.5 mA) |
| Preconfig ≤100 mA | FT232H ≤60 + U2 + U3/U4 + U5 Iq | ≈61 mA ✓ |
| Ungated capacitance ≤10 µF | VBUS 2.0 µF (C1, C2) + 3V3_AON ≈4.6 µF (C3-C8, C10-C16) | ≈6.6 µF ✓ |
| Steady state ≤450 mA | SUBSYSTEMS §2.2 with 1V8_A (60 mA via buck ≈51 mA VBUS) replaced by 3V3_ADC linear ≈45 mA | ≈336 mA ✓ (SUBSYSTEMS update pending) |
| dc_accuracy (uncalibrated) | LTC2290 offset/gain expected above allocation | ✗ BLOCKER, Open issue 1 |
