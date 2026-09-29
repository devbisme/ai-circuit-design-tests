# Skeleton BOM — dual_adc_usb

Refs match `net_plan.md` and the handoff's § Parts by block. Tier legend: **CP** = critical path, fixed
(escalate to the architect before substituting); **PKG** = package fixed (thermal/layout); **SUB** = freely
substitutable if it meets the stated spec. Passive packages default to 0402 (decoupling) / 0603 (signal)
unless stated otherwise.

## usb_power_in

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| J1 | USB-C receptacle, 16P, USB 2.0 | TYPE-C-31-M-12 (C165948) | SMD RA | 1 | SUB (any 16P USB2 Type-C) |
| U1 | USB ESD, D+/D−/VBUS | USBLC6-2SC6 | SOT-23-6 | 1 | SUB: ≤ 4 pF, HS-rated |
| D1 | VBUS TVS, 5 V standoff | SMF5.0A | SOD-123FL | 1 | SUB |
| U2 | Current-limited load switch, soft start | SY6280AAC | SOT-23-5 | 1 | SUB: TPS2553DBVR |
| FB1 | VBUS ferrite, ≥ 1 A, ≤ 0.1 Ω DCR | e.g. 600 Ω@100 MHz 0805 | 0805 | 1 | SUB |
| R1, R2 | CC pull-down 5.1 kΩ 1 % | — | 0603 | 2 | |
| R3 | SY6280 ISET (≈ 0.8 A limit) | per datasheet | 0603 | 1 | value from datasheet formula |
| R4 | shield bleed 1 MΩ | — | 0603 | 1 | |
| C1 | VBUS bulk 4.7 µF 10 V X5R | — | 0603 | 1 | total ≤ 10 µF before U2 (P5) |
| C2 | 0.1 µF | — | 0402 | 1 | |
| C3 | VBUS_SW 10 µF 10 V | — | 0805 | 1 | |
| C4 | shield 4.7 nF 100 V | — | 0603 | 1 | |

## power_rails

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| U3 | 3.3 V LDO, 1 A, low dropout | TLV1117LV33DCYR | SOT-223 | 1 | **PKG** (0.46 W). SUB only with dropout ≤ 0.6 V @ 300 mA; **not** AMS1117 |
| U4 | 1.2 V LDO (from 3.3 V) | AP2112K-1.2TRG1 | SOT-23-5 | 1 | SUB: TLV75512 |
| U5 | 1.8 V LDO (from 3.3 V) | TLV75518PDBVR | SOT-23-5 | 1 | SUB |
| U6 | 3.3 V low-noise analog LDO | TPS7A2033PDBVR | SOT-23-5 | 1 | SUB: noise ≤ 10 µVrms, ≥ 200 mA (LP5907MFX-3.3) |
| LED1 | power LED, green | — | 0603 | 1 | |
| R5 | LED1 1 kΩ | — | 0603 | 1 | |
| C5, C6 | 10 µF 10 V | — | 0805 | 2 | |
| C7 | 0.1 µF | — | 0402 | 1 | |
| C8–C13 | 1 µF 10 V | — | 0402 | 6 | |
| TP1–TP6 | test point | — | pad | 6 | |

## bipolar_supply

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| U7 | ±2.5 V charge pump + LDOs | LM27762DSSR | WSON-12 2×3 | 1 | **CP** (sets front-end rails) |
| R6–R9 | FB dividers (+2.50 / −2.50 V) | 1 % | 0402 | 4 | values per datasheet |
| C14 | CP_VIN 10 µF | — | 0603 | 1 | |
| C15 | 0.1 µF | — | 0402 | 1 | |
| C16 | flying 1 µF 10 V X7R | — | 0402 | 1 | |
| C17–C19 | 2.2 µF 10 V X7R | — | 0603 | 3 | |
| C20, C21 | 10 µF 10 V | — | 0603 | 2 | post-filter |
| FB2–FB4 | ferrite 600 Ω@100 MHz | — | 0603 | 3 | |
| TP7, TP8 | test point | — | pad | 2 | |

## analog_front_end (per channel ×2; channel A refs, B = +10)

| Ref (A / B) | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| J2 / J3 | BNC female, RA, PCB, 50 Ω | BNC-KWE-6 (C20415789) | THT | 2 | SUB (any PCB BNC) |
| R10, R11 / R20, R21 | 453 kΩ 1 %, ≥ 200 V | — | 1206 | 4 | **PKG** (voltage/creepage at ±50 V) |
| R12 / R22 | 100 kΩ 0.1 % 25 ppm | — | 0603 | 2 | sets gain; 0.1 % matters |
| R13 / R23 | 1 kΩ | — | 0603 | 2 | |
| R14, R15 / R24, R25 | Rg 1.10 kΩ 0.1 % | — | 0603 | 4 | matched |
| R16, R17 / R26, R27 | Rf 1.00 kΩ 0.1 % | — | 0603 | 4 | matched |
| R18, R19 / R28, R29 | 49.9 Ω 1 % | — | 0402 | 4 | |
| C30 / C40 | 15 pF C0G ≥ 100 V | — | 0603 | 2 | |
| VC1 / VC2 | trimmer 2–6 pF ≥ 100 V | STC3MA06-T1 (C22468120) | SMD 4.5×3.2 | 2 | SUB: range covering 2–6 pF, ≥ 100 V |
| C31 / C41 | 160 pF C0G 5 % | — | 0603 | 2 | |
| C32, C33 / C42, C43 | 0.1 µF | — | 0402 | 4 | |
| C34, C35 / C44, C45 | Cf 22 pF C0G | — | 0402 | 4 | |
| C36 / C46 | Cdiff 220 pF C0G | — | 0402 | 2 | |
| C37, C38 / C47, C48 | 0.1 µF | — | 0402 | 4 | |
| D2 / D3 | low-leakage clamp pair | BAV199 | SOT-23 | 2 | SUB: BAV99 (higher leakage) |
| U8 / U10 | CMOS RRIO buffer | OPA354AIDBVR | SOT-23-5 | 2 | SUB per `ic_selection.md` §4 |
| U9 / U11 | FDA ADC driver | THS4521IDGKR | VSSOP-8 | 2 | **CP** |

## adc

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| U12 | dual 12-bit 40 MSPS ADC | ADS5231IPAGT (C2670079) | TQFP-64 10×10 | 1 | **CP, single source** |
| R50 | ISET 56.2 kΩ 1 % | — | 0603 | 1 | |
| R51, R52 | 2 Ω | — | 0402 | 2 | REFT/REFB |
| R53–R56 | 10 kΩ pull-downs | — | 0402 | 4 | |
| RN1–RN7 | 4× 33 Ω array | 4D03WGJ0330T5E (C25508) | 0603×4 | 7 | SUB |
| C50–C52, C54–C56, C58–C61 | 0.1 µF | — | 0402 | 10 | |
| C53 | 1 µF | — | 0402 | 1 | |
| C57, C62 | 10 µF 10 V | — | 0603 | 2 | |
| FB5, FB6 | ferrite 600 Ω@100 MHz | — | 0603 | 2 | both fed from VA_3V3 (FB5 → VDRV, FB6 → AVDD) |

## sample_clock

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| X1 | 20.000 MHz 3.3 V CMOS XO, jitter ≤ 5 ps rms | SX3M20.000B10F20TNN (C5452685) | 3225-4P | 1 | **CP spec** (jitter); SUB within spec. BOM-only fallback: 10 MHz (see `ic_selection.md` §1) |
| R57, R58 | 33 Ω | — | 0402 | 2 | |
| C63 | 0.1 µF | — | 0402 | 1 | |
| C64 | 1 µF | — | 0402 | 1 | |
| FB7 | ferrite | — | 0603 | 1 | |
| TP9 | test point | — | pad | 1 | |

## usb_bridge

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| U13 | USB 2.0 HS FIFO bridge | FT232HL-REEL (C51997) | LQFP-48 | 1 | **CP** |
| U14 | 93C56 EEPROM | 93LC56BT-I/OT | SOT-23-6 | 1 | SUB: 93LC56B any pkg |
| Y1 | 12 MHz crystal ±30 ppm | — | 3225-4P | 1 | SUB |
| C65, C66 | crystal load caps (per Y1 CL) | C0G | 0402 | 2 | |
| C67–C76 | FT232H decoupling (0.1 µF ×8, 4.7 µF ×2) | — | 0402/0603 | 10 | per DS_FT232H §6 |
| C77 | 4.7 µF VPHY/VPLL bulk | — | 0603 | 1 | |
| C78, C79 | 0.1 µF (U14, RESET#) | — | 0402 | 2 | |
| FB8 | VPHY/VPLL ferrite | — | 0603 | 1 | |
| R60 | 2.2 kΩ | — | 0402 | 1 | |
| R61–R63, R65, R67 | 10 kΩ | — | 0402 | 5 | |
| R64 | 12 kΩ 1 % REF | — | 0402 | 1 | |
| R66 | 33 Ω | — | 0402 | 1 | |

## fpga_core

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| U15 | FPGA, 8.6k LUT, 64 Mbit PSRAM | GW1NR-LV9QN88PC6/I5 (C5799578) | QFN-88 10×10 | 1 | **CP, single source, fixed** (bank/pin plan depends on it) |
| J4 | JTAG header 1×7 2.54 mm | — | THT | 1 | |
| R70, R71, R73 | 4.7 kΩ | — | 0402 | 3 | MODE0/1, TCK |
| R72, R74 | 10 kΩ | — | 0402 | 2 | RECONFIG_N, JTAGSEL_N |
| C80–C83, C85–C87, C89, C91, C92, C94 | 0.1 µF | — | 0402 | 11 | |
| C84, C88 | 10 µF | — | 0603 | 2 | |
| C90, C93, C95 | 4.7 µF | — | 0603 | 3 | |
| TP10 | test point | — | pad | 1 | |

## io_expansion

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| U16 | quad 1.8→3.3 V buffer | SN74LV4T125PWR | TSSOP-14 | 1 | SUB: SN74LVC2T45 ×2 (re-plan) |
| U17 | 5 V-tolerant → 1.8 V buffer | SN74LV1T34DCKR | SC-70-5 | 1 | SUB |
| LED2, LED3 | status LEDs | — | 0603 | 2 | |
| R80, R81 | 1 kΩ | — | 0402 | 2 | |
| R82, R83 | 100 Ω | — | 0402 | 2 | |
| R84 | 1 kΩ | — | 0402 | 1 | |
| R85 | 100 kΩ | — | 0402 | 1 | |
| C96, C97 | 0.1 µF | — | 0402 | 2 | |
| J5 | header 1×6 2.54 mm | — | THT | 1 | |

**Cost estimate (qty 10, parts only):** ADC $30 + FPGA $22 + FT232H $11.3 + front-end ICs $4.7 + BNC $5.5 +
power ICs $1.8 + other ICs $1.9 + passives/connectors ≈ $8 → **≈ $86/board**, under the $120 target (Q3).
JLC Extended-part loading fees (~25 unique Extended parts × $3 per order) add ≈ $7.5/board at qty 10.
