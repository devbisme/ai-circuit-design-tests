# Net Plan — dual_adc_usb

Net-by-net connection plan. `<X>` = channel instance suffix, `A` or `B`.
Buses are written `NAME[msb:lsb]` and should be created as SKiDL `Bus` objects.

## 1. Power nets

| Net | Type | Nominal | Max current | Connected parts / pins |
|-----|------|---------|-------------|------------------------|
| `VBUS` | power | 4.40–5.25 V | 500 mA (fused 500 mA hold) | J1 VBUS pins → F1 → C_bulk 10 µF → U1(AP7361C-33E) IN, U_ls(P-FET) source, U6(FT232H) VBUS-sense via divider |
| `V3V3_D` | power | 3.30 V ±2% | 190 mA | U1 OUT → U9 (iCE40 VCCIO_0/1/2/3, VCC_SPI), U8 (SRAM VDD), U6 (FT232H VCCIO/VPHY/VPLL via FB), U7 (EEPROM), U2 (AP2112K-1.2 IN), LED anodes |
| `V1V2` | power | 1.20 V ±3% | 45 mA | U2 OUT → U9 VCC (core) ×N, U9 VCCPLL |
| `V5_A` | power | 4.4–5.25 V (unregulated, filtered) | 60 mA | P-FET drain → FB2 → L1/C → A1/A2 op-amp V+ (U10, U12), U3(LM2776) IN |
| `VN5_A` | power | −4.6 to −5.0 V | 30 mA | U3 OUT → L2/C post-filter → A1/A2 op-amp V− (U10, U12) |
| `V3V3_A` | power | 3.30 V ±2%, low noise | 105 mA | U4 (LP5907MFX-3.3) OUT → U14/U15 AVDD+DRVDD (AD9235), U11/U13 (OPA836 V+), U5 (REF3025 IN), FB6 → `V3V3_CLK` |
| `V3V3_CLK` | power | 3.30 V | 20 mA | FB6 from V3V3_A → X1 (XO VDD), U16/U17 (74LVC1G34 VCC) |
| `VREF_2V5` | analog ref | 2.500 V ±0.2% | 1 mA | U5 (REF3025) OUT → divider R→ `VREF_0V5_A`, `VREF_0V5_B` |
| `VREF_0V5_<X>` | analog ref | 0.500 V | <1 µA | 4.02 k / 1.00 k divider from VREF_2V5, 1 µF to GND → A3 (OPA836) non-inverting input |
| `GND` | power | 0 V | — | **single global ground net**; every part's GND/AGND/DGND/EPAD, J1 shell, J2/J3 BNC shells |
| `PWREN_N` | control (open-drain, active low) | 3V3_D logic | — | U6 FT232H ACBUS9 (EEPROM-configured PWREN#) → gate network of P-FET load switch Q1, EN pin of U4 (LP5907), EN/nSHDN of U3 (LM2776) |

## 2. USB nets

| Net | Type | Connected parts |
|-----|------|-----------------|
| `USB_DP` | USB2 HS differential (90 Ω diff, matched ±0.15 mm) | J1 DP1+DP2 → FB1 (common-mode choke) → D1 (USBLC6-2SC6) → U6 (FT232H) DP |
| `USB_DM` | USB2 HS differential | J1 DM1+DM2 → FB1 → D1 → U6 DM |
| `CC1` | analog | J1 CC1 → R1 5.1 kΩ 1% → GND |
| `CC2` | analog | J1 CC2 → R2 5.1 kΩ 1% → GND |
| `SHIELD` | chassis | J1 shield → R3 1 MΩ ∥ C 4.7 nF → GND (single-point) |

## 3. Analog signal nets (per channel `<X>` ∈ {A, B})

| Net | Type | Level | Connected parts |
|-----|------|-------|-----------------|
| `BNC_<X>_SIG` | analog input | ±10 V full scale, ±40 V survivable | J2/J3 BNC center pin → R_top1 (475 kΩ) |
| `ATTN_<X>_MID` | analog | ±20 V | R_top1 → R_top2 (series pair, voltage-coefficient splitting) |
| `ATTN_<X>` | analog | ±0.500 V, Zth 47.5 kΩ | R_top2 + C_trim → node; R_bot 50 kΩ + C_bot to GND; → R_ser 1 kΩ → clamp |
| `AFE_<X>_BUFIN` | analog | ±0.5 V (±5 V under fault) | R_ser 1 kΩ → D_clamp (BAV99: anode-common to VN5_A, cathode-common to V5_A) → A1 `+` input |
| `AFE_<X>_1` | analog | ±0.500 V | A1 output (unity buffer) → A2 Sallen-Key input network |
| `AFE_<X>_2` | analog | ±0.500 V | A2 output (SK 2nd order, fc 5 MHz, gain +1) → A3 MFB input resistor |
| `AFE_<X>_OUT` | analog | 0.500–2.500 V, CM 1.500 V | A3 output → R_s 33 Ω → `ADC_<X>_IN` |
| `ADC_<X>_IN` | analog | 0.5–2.5 V | R_s 33 Ω + C 22 pF to GND → U14/U15 `VIN+` |
| `ADC_<X>_VINN` | analog bias | 1.500 V | U14/U15 `VIN−`, tied to `ADC_<X>_CML` (AD9235 CML/AVDD÷2 node) with 0.1 µF + 1 µF to GND at the pin |
| `ADC_<X>_REFT` / `_REFB` | ADC internal ref | ~2.0 / ~1.0 V | 0.1 µF + 10 µF differential and to GND, per AD9235 datasheet |
| `ADC_<X>_VREF` | ADC ref out | 1.0 V | 0.1 µF to GND; `SENSE` pin strapped for 2 V p-p span (**datasheet phase must confirm exact strap**) |

**Polarity note:** A3 is inverting, so `ADC_<X>_IN` falls as `BNC_<X>_SIG` rises. The FPGA
packer restores polarity: `code_out = 4095 − code_raw`. This is free in fabric and must
not be "fixed" in hardware.

## 4. Clock nets

| Net | Type | Freq | Connected parts |
|-----|------|------|-----------------|
| `CLK_10M_XO` | CMOS clock | 10.000 MHz, ≤5 ps RMS jitter | X1 OUT → R 33 Ω → fan to U16 IN, U17 IN, and (via R 33 Ω) `CLK_10M` |
| `CLK_ADC_A` | CMOS clock | 10 MHz | U16 (74LVC1G34) OUT → R 33 Ω → U14 `CLK` |
| `CLK_ADC_B` | CMOS clock | 10 MHz | U17 (74LVC1G34) OUT → R 33 Ω → U15 `CLK` — **route CLK_ADC_A and CLK_ADC_B matched to ±2 mm** |
| `CLK_10M` | CMOS clock | 10 MHz | → U9 (iCE40) global buffer input pin (GBIN) |
| `CLK60` | CMOS clock | 60.000 MHz | U6 FT232H ACBUS5 (CLKOUT) → U9 GBIN pin |

## 5. ADC → FPGA parallel buses

| Net | Type | Connected parts |
|-----|------|-----------------|
| `ADCA_D[11:0]` | 12-bit CMOS bus, 3V3 | U14 D0–D11 → 100 Ω series damping at the ADC → U9 bank 2 I/O |
| `ADCA_OTR` | CMOS out | U14 OTR → U9 I/O (over-range flag, forwarded in status frames) |
| `ADCA_PDWN` | CMOS in | U9 I/O → U14 PDWN (drive low = active; allows low-power idle) |
| `ADCB_D[11:0]` | 12-bit CMOS bus | U15 D0–D11 → 100 Ω series → U9 bank 2 I/O |
| `ADCB_OTR` | CMOS out | U15 OTR → U9 I/O |
| `ADCB_PDWN` | CMOS in | U9 I/O → U15 PDWN |
| — | tie-offs | U14/U15 `OEB` → GND (outputs always enabled) |

## 6. SRAM bus

| Net | Type | Connected parts |
|-----|------|-----------------|
| `SRAM_A[17:0]` | 18-bit address | U9 → U8 A0–A17 |
| `SRAM_D[15:0]` | 16-bit bidirectional data | U9 ↔ U8 IO0–IO15 |
| `SRAM_CE_N` | control | U9 → U8 nCE |
| `SRAM_OE_N` | control | U9 → U8 nOE |
| `SRAM_WE_N` | control | U9 → U8 nWE |
| `SRAM_UB_N` | control | U9 → U8 nUB (upper byte) |
| `SRAM_LB_N` | control | U9 → U8 nLB (lower byte) |

## 7. FT245 synchronous FIFO bus (FT232H channel, 60 MHz)

| Net | Type | Direction | Connected parts |
|-----|------|-----------|-----------------|
| `FIFO_D[7:0]` | 8-bit bidirectional | both | U6 ADBUS0–7 ↔ U9 bank 1 I/O |
| `FIFO_RXF_N` | status | FT232H → FPGA | U6 ACBUS0 → U9 (low = host data available to read) |
| `FIFO_TXE_N` | status | FT232H → FPGA | U6 ACBUS1 → U9 (low = space available to write) |
| `FIFO_RD_N` | strobe | FPGA → FT232H | U9 → U6 ACBUS2 |
| `FIFO_WR_N` | strobe | FPGA → FT232H | U9 → U6 ACBUS3 |
| `FIFO_OE_N` | bus turnaround | FPGA → FT232H | U9 → U6 ACBUS6 |
| — | tie-off | — | U6 ACBUS4 (SIWU) → 10 kΩ pull-up to V3V3_D; ACBUS7 (PWRSAV#) → 10 kΩ pull-up |

## 8. FPGA configuration & housekeeping

| Net | Type | Connected parts |
|-----|------|-----------------|
| `SPI_SCK` | config | U9 → U18 (W25Q32JVSS) CLK; also J4 pin |
| `SPI_SI` | config | U9 SPI_SI ↔ U18 DI; J4 pin |
| `SPI_SO` | config | U18 DO → U9 SPI_SO; J4 pin |
| `SPI_SS_N` | config | U9 SPI_SS_B → U18 nCS, 10 kΩ pull-up to V3V3_D; J4 pin |
| `CDONE` | config status | U9 CDONE → 470 Ω → LED D4 (config-done) → V3V3_D; J4 pin |
| `CRESET_N` | config reset | U9 CRESET_B, 10 kΩ pull-up to V3V3_D, 100 nF to GND; J4 pin |
| `EXT_TRIG` | input | J5 (2-pin header or SMA) → 1 kΩ + BAV99 clamp to V3V3_D/GND → U9 I/O |
| `LED_USB_N` | output | U9 I/O → 1 kΩ → D5 (green) → V3V3_D |
| `LED_CAP_N` | output | U9 I/O → 1 kΩ → D6 (amber) → V3V3_D |
| `LED_PWR` | — | V3V3_D → 1 kΩ → D3 (green) → GND (hardwired) |

## 9. FT232H housekeeping

| Net | Type | Connected parts |
|-----|------|-----------------|
| `FT_RESET_N` | reset | U6 nRESET, 10 kΩ pull-up to V3V3_D |
| `FT_REF` | bias | U6 REF → 12.0 kΩ ±1% → GND (**mandatory FT232H bias resistor**) |
| `FT_VREGIN` / `FT_VREGOUT` | internal 1.8 V core LDO | U6 VREGIN ← V3V3_D; VREGOUT → 100 nF + 4.7 µF to GND, → VCORE pins |
| `FT_OSCI` / `FT_OSCO` | crystal | Y1 12.000 MHz ±30 ppm + 2× 27 pF (value per crystal CL) |
| `EE_CS` / `EE_SK` / `EE_DI` / `EE_DO` | EEPROM | U6 ↔ U7 (93LC46B): CS, CLK, DI, DO; DO with 2.2 kΩ pull-up to V3V3_D |
| `FT_VBUS_SENSE` | input | VBUS → 10 kΩ/10 kΩ divider → U6 VBUS_SENSE (nominal 2.5 V) |

## 10. Decoupling census (minimum; coder must place all)

| Node | Caps |
|------|------|
| Each AD9235 (U14, U15) | 1× 10 µF + 4× 100 nF (AVDD), 1× 100 nF + 1 µF (DRVDD), REFT/REFB/VREF/CML per §3 |
| iCE40HX4K (U9) | 1× 10 µF + 8× 100 nF on V3V3_D banks; 1× 10 µF + 4× 100 nF on V1V2; VCCPLL via 100 Ω + 100 nF |
| FT232H (U6) | 100 nF per supply pin (VCCIO ×2, VPHY, VPLL, VCORE ×2) + 4.7 µF bulk; VPHY/VPLL each fed via a ferrite bead |
| SRAM (U8) | 1× 10 µF + 2× 100 nF |
| Op-amps (U10–U13) | 100 nF + 1 µF per supply pin, at the pin |
| X1 XO | 100 nF + 1 µF, fed through FB6 |
| Each LDO | per datasheet (typ. 1 µF in, 10 µF out; LP5907 needs 1 µF/1 µF + 10 nF NR cap) |
| LM2776 | 1 µF flying cap C_FLY, 1 µF in, 10 µF out, then L 10 µH + 22 µF post-filter |
