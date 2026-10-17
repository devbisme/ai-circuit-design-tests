# Skeleton BOM — dual_adc_10msps (per board; qty 5 boards)

Passive defaults unless noted: resistors 0402 1 % thick film; decoupling 0.1 µF 0402 X7R
16 V; bulk X5R ≥ 10 V. Filter caps = C0G/NP0 **≤ ±2 %** (±1 % preferred; ±5 % keeps the HARD
stopband but SOFT flatness p99 rises to ~1 dB). AFE refs: channel A 1xx, channel B 2xx
(same values; qty column counts both channels).

## ICs, connectors, critical parts

| Function | Suggested MPN | Package | Qty | Refs | Notes |
|---|---|---|---|---|---|
| Dual 12-bit 40 MSPS ADC | ADS5231IPAGT | TQFP-64 10×10 | 1 | U301 | Critical; symbol to generate; C2670079 (152 stk) |
| FPGA | XC6SLX9-2TQG144C | TQFP-144 20×20 | 1 | U1001 | Critical; symbol FPGA_Xilinx_Spartan6:XC6SLX4-TQG144 |
| SPI config flash 32 Mbit | W25Q32JVSSIQ | SOIC-8 208 mil | 1 | U1002 | Any SPI NOR ≥ 4 Mbit supported by Spartan-6 |
| SDRAM 16 MB ×16 | W9812G6KH-6 | TSOP-II-54 | 1 | U801 | 2nd source W9825G6KH-6 (32 MB, pin 36 = A12) |
| USB HS FIFO bridge | FT232HL | LQFP-48 7×7 | 1 | U901 | Critical (sync FIFO) |
| EEPROM for FT232H | 93LC56BT-I/OT | SOT-23-6 | 1 | U902 | 16-bit org ("B") mandatory |
| Crystal 12 MHz | 12 MHz ±30 ppm, CL 8–12 pF | 3225 | 1 | Y901 | Load caps C901/C902 = 2 × (CL − 3 pF) |
| Dual FET op-amp | OPA2810IDR | SOIC-8 | 2 | U101, U201 | Buffer + SK_a |
| FET op-amp | OPA810IDBVR | SOT-23-5 | 2 | U102, U202 | SK_b (Q 2.28) — GBW 70 MHz is designed in |
| FDA | THS4551IRGTR | VQFN-16 3×3 | 2 | U103, U203 | FB± pins NC |
| Clamp diode pair | BAV199 | SOT-23 | 2 | D101, D201 | Low-leakage series pair |
| BNC female, right angle, 50 Ω, PCB | KH-BNC50-3511 | THT | 2 | J101, J201 | Through-hole (no SMD BNC) |
| Trimmer cap 2–6 pF 100 V | STC3MA06-T1 | SMD 4.5×3.2 | 2 | C102, C202 | Probe-comp trim; SPICE value "3.3p" (nominal setting) |
| ±4 V low-noise charge pump | LM27762DSSR | WSON-12 | 1 | U702 | |
| 3.3 V LDO analog | LP5907MFX-3.3/NOPB | SOT-23-5 | 1 | U701 | Cout total ≤ 10 µF |
| 3.3 V buck 2 A | TLV62569DBVR | SOT-23-5 | 1 | U601 | |
| 1.2 V LDO 1 A | TLV75712PDBVR | SOT-23-5 | 1 | U602 | |
| 10 MHz CMOS XO 3.3 V | SX3M10.000B10F20TNN | 3225 | 1 | Y401 | Jitter ≤ 5 ps rms |
| Dual buffer | SN74LVC2G34DBVR | SOT-23-6 | 1 | U401 | |
| USB-C receptacle USB2.0 16P | TYPE-C-31-M-12 | SMD | 1 | J501 | Symbol Connector:USB_C_Receptacle_USB2.0_16P |
| USB ESD | USBLC6-2SC6 | SOT-23-6 | 1 | U501 | |
| VBUS TVS 5 V | SMF5.0A | SOD-123F | 1 | D501 | |
| PTC fuse 0.75 A hold | e.g. SMD1206P075TF | 1206 | 1 | F501 | R ≤ 0.3 Ω |
| Ferrite 600 Ω@100 MHz, ≥ 0.5 A | e.g. GZ1608D601TF | 0603 | 4 | FB301, FB401, FB701, FB901 | FB701 carries ~0.15 A; DCR ≤ 0.15 Ω |
| Inductor 2.2 µH ≥ 1.5 A Isat | e.g. 4×4 mm shielded | SMD | 1 | L601 | |
| 33 Ω ×4 resistor array | 4D02WGJ0330TCE | 0402×4 | 6 | RN301–RN306 | ADC output series R |
| JTAG header 1×6 2.54 mm | generic | THT | 1 | J1001 | Digilent HS2 order |
| Trigger header 1×3 2.54 mm | generic | THT | 1 | J1002 | |
| LED green (power), 2× user | 0603 | 0603 | 3 | D601, D1002, D1003 | |

## AFE passives (×2 channels; refs for A, B = +100)

| Function | Value | Package | Qty | Refs (A) | Notes |
|---|---|---|---|---|---|
| Attenuator top R | 953 kΩ 1 % | **1206** (200 V) | 2 | R101 | sees 28.5 V at ±30 V input |
| Attenuator top C | 8.2 pF C0G **100 V** ±0.25 pF | 0603 | 2 | C101 | |
| Attenuator bottom R | 49.9 kΩ 1 % | 0603 | 2 | R102 | |
| Attenuator bottom C | 220 pF C0G ±5 % | 0603 | 2 | C103 | trim absorbs tolerance |
| Input series R | 1.00 kΩ | 0603 | 2 | R103 | |
| SK_a R1 / R2 | 887 Ω / 453 Ω | 0402 | 4 | R104 / R105 | |
| SK_a C1 (fb) / C2 (gnd) | 270 pF / 100 pF C0G ≤2 % | 0402/0603 | 4 | C104 / C105 | |
| SK_b R1 / R2 | 374 Ω / 232 Ω | 0402 | 4 | R106 / R107 | |
| SK_b C1 (fb) / C2 (gnd) | 1.8 nF / 82 pF C0G ≤2 % | 0603 | 4 | C106 / C107 | |
| MFB R1 (×2 sides) | 698 Ω | 0402 | 4 | R108, R109 | |
| MFB R2 (×2) | 1.27 kΩ | 0402 | 4 | R110, R111 | gain 1270/698 = 1.8195 |
| MFB R3 (×2) | 576 Ω | 0402 | 4 | R112, R113 | |
| MFB C1 (×2, to GND) | 330 pF C0G ≤2 % | 0402 | 4 | C108, C109 | |
| MFB C2 (×2, feedback) | 82 pF C0G ≤2 % | 0402 | 4 | C110, C111 | |
| ADC RC series R (×2) | 46.4 Ω | 0402 | 4 | R114, R115 | |
| ADC RC diff C | 1.2 nF C0G ≤2 % | 0603 | 2 | C112 | |
| Op-amp decoupling | 0.1 µF | 0402 | 8 | C113–C116 | |
| FDA decoupling | 0.1 µF + 1 µF | 0402 | 4 | C117, C118 | |
| VOCM bypass | 10 nF | 0402 | 2 | C119 | |
| ±4V0A local bulk | 2.2 µF 10 V | 0603 | 4 | C120, C121 | |

## Other blocks — passives

| Block | Refs | Values |
|---|---|---|
| usb_c_input | R501, R502; C501 | 5.1 kΩ 1 % ×2; 1 µF 10 V |
| power_digital | C601; C602, C603; R601; R602; C604; C605, C606; R604 | 4.7 µF 10 V; 10 µF 10 V ×2; 453 kΩ 1 %; 100 kΩ 1 %; 6.8 pF C0G; 1 µF ×2; 1 kΩ |
| power_analog | C702, C703; C705, C708, C709; C706; C707; R701; R702, R704; R703 | 1 µF ×2; 2.2 µF ×3; 1 µF (flying); 4.7 µF; 232 kΩ 1 %; 100 kΩ 1 % ×2; 226 kΩ 1 % |
| adc | R301; R302, R303; C301, C302; C303; C304; C305–C307; C308; C309–C312; C313; R304–R307 | 56.2 kΩ 1 %; 2.0 Ω ×2; 0.1 µF ×2; 0.1 µF; 1 µF; 0.1 µF ×3; 4.7 µF; 0.1 µF ×4; 4.7 µF; 10 kΩ ×4 |
| clock | C401, C402; C403; R401, R402 | 0.1 µF ×2; 4.7 µF; 33 Ω ×2 |
| sdram | C801–C807; C808; R801; R802, R803 | 0.1 µF ×7; 10 µF; 22 Ω; 10 kΩ ×2 |
| usb_fifo | C901, C902; R901; R902, R904–R909, R911, R912; R903; R910; C903, C909; C904–C908, C910–C913 | 18 pF C0G (per crystal CL) ×2; 12.0 kΩ 1 %; 10 kΩ ×10; 2.2 kΩ; 22 Ω; 4.7 µF ×2; 0.1 µF ×9 |
| fpga | R1001, R1004, R1005; R1002, R1003, R1015; R1006; R1008–R1010; R1012, R1013; R1014, R1016; C1001–C10nn | 4.7 kΩ ×3; 10 kΩ ×3; 330 Ω; 1 kΩ ×3; 1 kΩ ×2; 100 Ω ×2; 0.1 µF one per VCCINT/VCCAUX/VCCO pin (+ U1002) + 4.7 µF ×3 bulk (coder counts pins from the symbol) |

Cost estimate (qty 5, parts only): ICs ≈ $70 (ADC 29.8, FPGA 7.4, SDRAM 6.1, FT232H 9.5,
op-amps/FDAs 21, power 1.5, misc 3), connectors/trimmers ≈ $4, passives ≈ $6 → ≈ $80/board
+ JLC extended-part fees (≈ 30 unique × $3 per order, ≈ $18/board at qty 5) → ≈ $100 ≤ $150 SOFT.
