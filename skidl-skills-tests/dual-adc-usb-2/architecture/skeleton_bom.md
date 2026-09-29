# Skeleton BOM — dual_adc_usb

Function-level BOM with suggested MPNs. **Quantities are per board.** The part-sourcer
replaces "suggested MPN" with a verified in-stock MPN + LCSC# + tier, keeping the
constraints in the Notes column.

Reference designators below are the architect's scoping allocation (they map to
`## Parts by block` in the handoff). SKiDL will assign final designators; treat these as
an indication of *how many* of each and *which block owns them*.

Legend: **[FIXED]** = do not substitute without escalating · **[CRIT]** = critical path,
verify stock first · **[GEN]** = KiCad symbol must be generated with `kipart`

---

## Block 1 — `usb_c_input`

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|-----|----------|---------------|---------|-----|-------|
| J1 | USB-C receptacle, USB 2.0 only, 16-pin | U262-161N-4BVC11 | SMD 16P | 1 | [CRIT] Symbol `Connector:USB_C_Receptacle_USB2.0_16P` ✓. Alt: TYPE-C-31-M-12 |
| F1 | PPTC, 500 mA hold / 1 A trip | MF-MSMF050-2 | 1206 | 1 | Must hold 500 mA at 50 °C |
| D1 | USB D+/D− ESD array | USBLC6-2SC6 | SOT-23-6 | 1 | Symbol ✓ |
| D2 | VBUS TVS, 6 V standoff | SMAJ6.0A / PESD5V0S1BA | SOD-323 | 1 | |
| FB1 | USB2 common-mode choke, 90 Ω @ 100 MHz | DLW21SN900HQ2L | 0805 | 1 | Optional for function, recommended for FCC |
| R1, R2 | CC1 / CC2 pull-down | 5.1 kΩ ±1% | 0402 | 2 | [FIXED] value — USB-C sink advertisement |
| R3 | Shield-to-GND bleed | 1 MΩ | 0402 | 1 | Parallel with C2 |
| C1 | VBUS bulk | 10 µF X5R 16 V | 0805 | 1 | [FIXED] ≤10 µF total on VBUS — USB inrush limit |
| C2 | Shield-to-GND | 4.7 nF 2 kV | 0603 | 1 | Single-point chassis tie |

## Block 2 — `power_digital`

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|-----|----------|---------------|---------|-----|-------|
| U1 | 3.3 V LDO, 1 A, low dropout | AP7361C-33E | **SOT-223** | 1 | [FIXED PACKAGE] 0.37 W dissipation — SOT-23-5 will overheat. Symbol ✓ |
| U2 | 1.2 V LDO, 600 mA (iCE40 core) | AP2112K-1.2TRG1 | SOT-25 | 1 | 0.095 W. Symbol ✓ |
| D3 | Power LED, green | 0603 LED | 0603 | 1 | Hardwired to 3V3_D |
| R4 | LED series | 1 kΩ | 0402 | 1 | ~2 mA |
| C3–C7 | LDO in/out caps + bulk | 1 µF ×2, 10 µF ×2, 100 nF ×1 | 0603/0805 | 5 | Per LDO datasheets |

## Block 3 — `power_analog`

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|-----|----------|---------------|---------|-----|-------|
| Q1 | P-channel load switch for +5V_A, ≥500 mA, Vgs(th) < 2 V | DMG2305UX / AO3401A | SOT-23 | 1 | Gated by PWREN_N; add soft-start RC |
| R5 | Q1 gate pull-up | 100 kΩ | 0402 | 1 | |
| R6 | Q1 gate series (soft start) | 10 kΩ | 0402 | 1 | With C to gate, ~1 ms ramp |
| U3 | −5 V switched-capacitor inverter, ≥60 mA | LM2776DBVR | SOT-23-6 | 1 | [CRIT] Needs enable pin. Symbol ✓. Alt: TPS60403 (higher Zout) |
| U4 | 3.3 V low-noise LDO, ≥150 mA, **with EN** | LP5907MFX-3.3 | SOT-23-5 | 1 | [CRIT] 6.5 µV RMS noise; feeds both ADC AVDD + XO. Symbol ✓ |
| U5 | 2.5 V voltage reference, 30 ppm/°C | REF3025AIDBZR | SOT-23-3 | 1 | Sets AFE level-shift offset. Symbol ✓ |
| FB2, FB3 | Ferrite bead, 600 Ω @ 100 MHz, 1 A | BLM18PG601SN1D | 0603 | 2 | V5_A and V3V3_A entry |
| FB6 | Ferrite bead for V3V3_CLK | BLM18PG601SN1D | 0603 | 1 | Isolates the XO's switching from ADC AVDD |
| L1 | −5 V post-filter inductor | 10 µH, ≥100 mA, ≤0.5 Ω DCR | 0805 | 1 | With C forms >90 dB attenuation at f_sw |
| L2 | +5 V post-filter inductor | 10 µH, ≥200 mA | 0805 | 1 | |
| R7, R8 | VREF_2V5 → VREF_0V5 dividers (2 ch) | 4.02 kΩ + 1.00 kΩ ±0.1% | 0402 | 4 | Two dividers, one per channel |
| C8–C21 | Flying/bulk/decoupling for U3, U4, U5, LC filters | 1 µF ×4, 10 µF ×3, 22 µF ×2, 100 nF ×4, 10 nF ×1 | 0603/0805 | 14 | LM2776 C_FLY must be ≥1 µF X7R |

## Block 4 — `clock_gen`

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|-----|----------|---------------|---------|-----|-------|
| X1 | 10.000 MHz CMOS XO, ±25 ppm | ASEM1-10.000MHZ-LC-T | 3225 4-pad | 1 | **[FIXED SPEC] ≤5 ps RMS phase jitter (12 kHz–20 MHz).** This is the ENOB-limiting part. Symbol `Oscillator:ASE-xxxMHz` ✓ |
| U16, U17 | Single non-inverting buffer | 74LVC1G34GW | SOT-23-5 | 2 | Symbol ✓. Alt: one 74AUC2G34 dual |
| R10–R12 | Series terminations, 33 Ω | 33 Ω ±1% | 0402 | 3 | XO out, and each ADC clock |
| C22–C24 | Decoupling | 100 nF ×2, 1 µF ×1 | 0402/0603 | 3 | |

## Block 5 — `afe_channel` (**×2 instances: A and B — quantities below are PER CHANNEL**)

| Ref | Function | Suggested MPN | Package | Qty/ch | Notes |
|-----|----------|---------------|---------|--------|-------|
| J2 / J3 | BNC jack, PCB mount, right angle | Amphenol 031-5431-10RFX | THT R/A | 1 | [CRIT][FIXED] Mechanically panel-critical; footprint must match the exact MPN. Symbol `Connector:BNC` ✓ |
| R_top1, R_top2 | Attenuator top leg, 475 kΩ ±0.1% | thin-film 475 kΩ 0.1% 25 ppm | **0805** | 2 | [FIXED] Two in series = 950 kΩ. 0805 for working-voltage rating and low voltage coefficient — **do not shrink to 0402** |
| R_bot | Attenuator bottom leg, 50.0 kΩ ±0.1% | thin-film 49.9 kΩ 0.1% 25 ppm | 0603 | 1 | [FIXED] Ratio sets gain accuracy directly |
| C_trim | Attenuator HF compensation trimmer | 2–10 pF trimmer, C0G | SMD trimmer | 1 | Production trim step — see design_risks R-05 |
| C_bot | Attenuator bottom-leg capacitance | 180 pF C0G ±2% | 0603 | 1 | R_top·C_top = R_bot·C_bot |
| R_ser | Buffer input series limiter | 1 kΩ | 0402 | 1 | Limits clamp current |
| D_clamp | Input clamp to ±5 V rails | BAV99 | SOT-23 | 1 | Symbol ✓. Conducts only beyond ≈±100 V input |
| D_esd | Optional low-cap TVS at the BNC | ESD9L12ST5G (<2 pF) | SOD-923 | 1 | **Footprint populated, part optional** — must be <2 pF and ≥45 V standoff, else it loads the input or clips over-range. Leave DNP unless ESD testing demands it |
| U_a | Dual op-amp, A1 buffer + A2 SK filter, ±5 V | AD8066ARZ | SOIC-8 | 1 | [CRIT][GEN] FET input required. Drop-in alt: OPA2810IDR, OPA1656IDR |
| U_b | Single op-amp, A3 MFB + level shift, **+3.3 V** | OPA836IDBVR | SOT-23-6 | 1 | [CRIT][GEN][FIXED] **Must be a 3.3 V single-supply part — this is the ADC's over-voltage protection.** Alt: ADA4891-1ARJZ |
| R_filt | Sallen-Key + MFB network resistors | 1% thin film, values TBD by filter synthesis | 0402 | 8 | 4th-order Butterworth, fc = 5.0 MHz; A3 gain = −2 (Rf = 2·Rin) |
| C_filt | Sallen-Key + MFB network caps | C0G ±2%, values TBD | 0402 | 5 | **C0G/NP0 mandatory** — X7R's voltage coefficient would distort the passband |
| R_s | ADC series damping | 33 Ω | 0402 | 1 | |
| C_s | ADC input charge-kickback | 22 pF C0G | 0402 | 1 | |
| C_dec | Op-amp decoupling | 100 nF ×3, 1 µF ×3 | 0402/0603 | 6 | At every supply pin |

## Block 6 — `adc_channel` (**×2 instances — quantities PER CHANNEL**)

| Ref | Function | Suggested MPN | Package | Qty/ch | Notes |
|-----|----------|---------------|---------|--------|-------|
| U_adc | 12-bit, 20 MSPS, parallel CMOS ADC | **AD9235BRUZ-20** | **TSSOP-28 (RU)** | 1 | [CRIT][GEN][FIXED PACKAGE] Drop-in speed grades: −40, −65 (see ic_selection power warning). LFCSP variant is a different footprint |
| FB_drv | DRVDD isolation ferrite | BLM18PG601SN1D | 0603 | 1 | Digital output return current stays in the digital zone |
| R_damp | ADC data-line series damping, 100 Ω | 100 Ω ±5% array or discrete | 0402 | 12 | Placed at the ADC end; reduces the biggest digital aggressor |
| C_avdd | AVDD decoupling | 100 nF ×4, 10 µF ×1 | 0402/0805 | 5 | One 100 nF per AVDD pin, at the pin |
| C_drvdd | DRVDD decoupling | 100 nF ×1, 1 µF ×1 | 0402/0603 | 2 | |
| C_ref | REFT/REFB/VREF/CML network | 100 nF ×3, 1 µF ×2, 10 µF ×1 | 0402/0603/0805 | 6 | **Exact topology per AD9235 datasheet — datasheet phase must supply it** |

## Block 7 — `sram_buffer`

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|-----|----------|---------------|---------|-----|-------|
| U8 | 256K × 16 async SRAM, 10 ns, 3.3 V | IS61WV25616BLL-10TLI | TSOP-II-44 | 1 | [CRIT][GEN][FIXED SPEC] **≤15 ns is binding.** Alts: CY7C1041GN30-10ZSXI, AS7C34098A-10TCN. Free upgrade: IS61WV51216BLL-10TLI (1 MB, doubles burst depth) |
| C41–C46 | Decoupling | 100 nF ×4, 10 µF ×1, 1 µF ×1 | 0402/0805 | 6 | |

## Block 8 — `usb_bridge`

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|-----|----------|---------------|---------|-----|-------|
| U6 | USB 2.0 HS bridge, FT245 sync FIFO | **FT232HL** | LQFP-48 | 1 | [CRIT][FIXED] Symbol `Interface_USB:FT232H` ✓. **ACBUS9 must be EEPROM-set to PWREN#** |
| U7 | Config EEPROM, 93LC46B | 93LC46BT-I/OT | SOT-23-6 | 1 | Symbol `Memory_EEPROM:93CxxC` ✓ (pin-compatible) |
| Y1 | 12.000 MHz crystal, ±30 ppm | X322512MSB4SI | 3225 | 1 | Sets the USB clock; also the ADC rate reference indirectly? **No** — the ADC has its own XO |
| R13 | **FT232H REF bias, 12.0 kΩ ±1%** | 12 kΩ 1% | 0402 | 1 | [FIXED] Mandatory FT232H bias resistor — easy to omit, board will not enumerate |
| R14, R15 | VBUS sense divider | 10 kΩ ±1% | 0402 | 2 | |
| R16 | nRESET pull-up | 10 kΩ | 0402 | 1 | |
| R17 | EEPROM DO pull-up | 2.2 kΩ | 0402 | 1 | |
| R18, R19 | SIWU / PWRSAV# pull-ups | 10 kΩ | 0402 | 2 | |
| FB4, FB5 | VPLL / VPHY isolation ferrites | BLM18PG601SN1D | 0603 | 2 | Per FTDI reference design |
| C25–C40 | Crystal load caps, VREGOUT, per-pin decoupling, bulk | 27 pF ×2, 100 nF ×8, 1 µF ×2, 4.7 µF ×2, 10 µF ×1 | 0402/0603/0805 | 15 | 100 nF at every supply pin |

## Block 9 — `fpga_core`

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|-----|----------|---------------|---------|-----|-------|
| U9 | FPGA, 3520 LUT, 107 I/O | **iCE40HX4K-TQ144** | TQFP-144 | 1 | [CRIT][FIXED] Symbol `FPGA_Lattice:ICE40HX4K-TQ144` ✓ (5 units). **TQ144 fixed by the 86-pin need — no TQFP-100 substitute** |
| U18 | SPI config flash, ≥1 Mbit | W25Q32JVSSIQ | SOIC-8 | 1 | Symbol `Memory_Flash:W25Q32JVSS` ✓. Any ≥1 Mbit 3.3 V SPI NOR works |
| J4 | Programming header, 2×5 1.27 mm or 1×8 2.54 mm | generic | THT/SMD | 1 | SPI + CRESET_B + CDONE + 3V3 + GND |
| J5 | External trigger input | 2-pin 2.54 mm header | THT | 1 | Optional; keep the footprint |
| D4 | CDONE LED (blue) | 0603 LED | 0603 | 1 | |
| D5 | USB-active LED (green) | 0603 LED | 0603 | 1 | |
| D6 | Capture-armed LED (amber) | 0603 LED | 0603 | 1 | |
| D7 | EXT_TRIG clamp | BAV99 | SOT-23 | 1 | With a 1 kΩ series resistor |
| R20–R26 | LED series (×3), CRESET pull-up, SPI_SS pull-up, EXT_TRIG series | 1 kΩ ×3, 10 kΩ ×2, 1 kΩ ×1, 470 Ω ×1 | 0402 | 7 | |
| C47–C64 | FPGA decoupling: 3V3_D banks, 1V2 core, VCCPLL, CRESET | 100 nF ×12, 1 µF ×2, 10 µF ×2, 100 nF (PLL) ×1, 100 Ω (PLL) ×1 | 0402/0805 | 18 | ≥8 × 100 nF on VCCIO, ≥4 on VCC core, at the pins |

---

## Board totals (estimate)

| Category | Count |
|---|---|
| ICs (U) | 15 (2 ADC, 4 op-amp pkgs, 1 FPGA, 1 SRAM, 1 FT232H, 1 EEPROM, 1 flash, 2 buffers, 4 power ICs — counted per block above) |
| Connectors (J) | 5 (USB-C, 2× BNC, JTAG, trigger) |
| Discrete semis (D, Q) | 12 |
| Passives (R, C, L, FB) | ≈150 |
| **Distinct line items** | ≈70 |
| **Estimated BOM cost @ qty 5–10** | **$85–115/board** — inside the assumed ≤$150 target |

## Power budget (the tightest constraint in this design)

| Rail | Load | Current | Sourced from |
|---|---|---|---|
| 3V3_D | iCE40HX4K (VCCIO + 1V2 LDO input) 90 mA, FT232H 55 mA, SRAM 35 mA, flash 1 mA, LEDs 6 mA | **187 mA** | VBUS via AP7361C-33E |
| 1V2 | iCE40 core + PLL | 45 mA | 3V3_D via AP2112K-1.2 (already counted in 3V3_D) |
| 3V3_A | 2× AD9235 80 mA, 2× OPA836 2 mA, REF3025 0.1 mA, XO 15 mA, clock buffers 3 mA | **100 mA** | VBUS via LP5907 (PWREN# gated) |
| 5V_A | 4 op-amps (2× AD8066 dual) 26 mA + LM2776 input ≈32 mA | **58 mA** | VBUS via P-FET (PWREN# gated) |
| −5V_A | 4 op-amps | 26 mA | +5V_A via LM2776 |
| **Total from VBUS** | | **≈345 mA** | **31% margin under the 500 mA ceiling** |
| Pre-enumeration (PWREN# low) | FT232H unconfigured + iCE40 static + SRAM standby + LEDs | **≈65–80 mA** | Inside the 100 mA pre-configuration limit ✓ |
| LDO dissipation total | 0.37 W (3V3_D) + 0.20 W (3V3_A) + 0.10 W (1V2) | **0.67 W** | Fine on 4 layers with pours |
