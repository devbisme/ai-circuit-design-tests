---
phase: 02_architecture
agent: circuit-architect
circuit: dual_adc_10msps
written: 2026-10-17T03:40:00Z
status: complete
revision: 1
next_phase: 03_sourcing
---

# Phase 2 handoff — Architecture

## Decisions
1. Data path = **FPGA + SDR SDRAM + FT232H sync FIFO**, capture-then-upload (40 MB/s is at the USB HS limit). MCU (STM32H7+ULPI: DCMI ≤ 14 bit, bus contention) and FX2LP streaming rejected — see `block_diagram.md`.
2. ADC **ADS5231IPAGT** (dual 12-bit, one CLK pin → simultaneous, CM output feeds both FDAs) over 2× AD9235BCPZ-40 (two packages, $48.7) and LTC2225/AD9238 (stock < 100). Runs at 10 MSPS only with its PLL **disabled** via serial reg (gateware).
3. FPGA **XC6SLX9-2TQG144C** (1678 stk, $7.37, symbol `FPGA_Xilinx_Spartan6:XC6SLX4-TQG144`, pin-compatible) over LCMXO2-4000HC (no symbol, 139 stk, ¼ RAM) and ICE40HX4K (32 stk). Needs +1V2 core + SPI flash W25Q32JVSSIQ; config Master SPI; JTAG 1×6 header.
4. Memory **W9812G6KH-6** 16 MB (exact symbol) → 4 M samples/ch = 0.42 s ≥ 0.1 s; 40 MB/s vs 160 MB/s peak at 80 MHz. W9825G6KH-6 is the vetted drop-in second source.
5. USB **FT232HL** (sync FIFO 60 MHz, no firmware) + 93LC56B EEPROM over FT2232HL (ch B dead in sync mode) / FX2LP (firmware, not stocked).
6. Front end per channel: BNC → **÷20.10 compensated attenuator** (953 k ∥ 8.2 p + 2–6 p trimmer / 49.9 k ∥ 220 p; 1.003 MΩ ∥ 10.9 pF) → 1 k + BAV199 clamp → OPA2810 buffer → SK_a (OPA2810 B) → SK_b (OPA810) → THS4551 MFB (G 1.8195, SE→diff) → 2×46.4 Ω + 1.2 nF → ADC. ÷20 (not ÷10) keeps the OPA810 input under V+ − 2.5 V (peak 1.11 V vs 1.5 V limit).
7. Anti-alias = **7-pole Butterworth-type**, −3 dB 1.354 MHz, values pre-distorted for 70 MHz op-amp GBW. Nominal (ngspice): gain −20.87 dB, ripple ±0.013 dB to 1 MHz, −80.9 dB at 5 MHz, −123 dB at 10 MHz. MC worst-case 78.7 dB at 5 MHz (HARD 72 dB ✓). Chose over 5-pole Chebyshev 0.1 dB (Q 3.28 stage: SOFT flatness failed on ~50 % of MC boards).
8. Alias edge is fs/2 = 5 MHz as the requirements state — no correction needed. ≥ 72 dB is applied at 5 and 10 MHz (HARD) and 40 MHz (ASSUMED).
9. Total gain 0.049756 × 1.8195 = 0.0905: ±10 V → ±0.905 V = 90 % of ADS5231 2.02 Vpp; full scale ±11.16 V. ±30 V input → 1.49 V at the buffer; clamps conduct only above 92 V.
10. Power: USB-C sink (Rd 5.1 k ×2, no PD), PTC 0.75 A, TLV62569 → +3V3 (453 k/100 k, VFB 0.6 V → 3.318 V), TLV75712 → +1V2, LP5907-3.3 → +3V3A, LM27762 → +4V0A/−4V0A (232 k/100 k → +3.984 V with VFB+ 1.200 V; 226 k/100 k → −3.977 V with VFB− −1.220 V). Worst-case VBUS 0.43 A ≤ 0.5 A → **Decision 7 resolved: 500 mA default USB power suffices**; USB-C kept per Decision 8.
11. ADC clock from a dedicated 10 MHz XO + 74LVC2G34 fan-out (ADC, FPGA GCLK); never via FPGA PLL (32 ps jitter budget at 1 MHz).
12. One ground net `GND`; **4 copper layers** (SIG/GND/PWR/SIG): TQFP-144 escape, 80 MHz SDRAM bus, 90 Ω USB pair, unbroken ground under the AFE.
13. Triggering: software + level trigger on either channel in gateware (zero hardware cost) + TRIG_IN/TRIG_OUT 3.3 V header J1002.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `architecture/net_plan.md` | Every net, type, refs/pins, block signatures, top-level map, stage arithmetic | Always — before writing any code |
| `architecture/skeleton_bom.md` | function / MPN / package / qty / refs, all passive values | Sourcing; coding |
| `architecture/ic_selection.md` | 2–5 candidates per block with stock, price, why the loser lost | Before any substitution |
| `architecture/block_diagram.md` | Mermaid diagram, data-path arithmetic, architecture options, implied gateware | Orientation |
| `architecture/design_risks.md` | 31 risks (analog, PI, layout, timing, sourcing) with arithmetic | Sourcing, layout, review |
| `architecture/afe_nominal.cir` | Reproducible ngspice testbench of one AFE channel (gate-equivalent models) | Review / any filter change |
| `constraints.json` | 12 ac_gain + 5 rail_current checks (validated by boardforge loader) | Review gate |

## Next phase must
1. part-sourcer: source every row of `skeleton_bom.md`, keeping refs. Critical path: U301 ADS5231IPAGT (single source, 152 stk — WARN), U1001 XC6SLX9-2TQG144C, U901 FT232HL, U101/U201 OPA2810IDR, U102/U202 OPA810IDBVR, U103/U203 THS4551IRGTR, U801 W9812G6KH-6.
2. Do **not** substitute the OPA2810/OPA810 (filter is pre-distorted for their 70 MHz GBW) or the THS4551 (3.3 V-rail FDA protects the ADC). Second sources: W9825G6KH-6 for U801; XC6SLX4-2TQG144C for U1001; 2× AD9235BCPZ-40 for U301 only via architecture rework.
3. Filter caps C104–C112, C204–C212: C0G ≤ ±2 % (±1 % preferred). R101/R201: 1206, ≥ 200 V. C101/C201: C0G 100 V. C102/C202: 2–6 pF 100 V trimmer (STC3MA06-T1 or equal), BOM value "3.3p".
4. Fixed packages (symbol pin numbers depend on them): ADS5231 PAG TQFP-64, XC6SLX9 TQG144, W9812G6KH TSOP-II-54, FT232HL LQFP-48, THS4551 RGT, OPA810 DBV, OPA2810 D (SOIC-8).
5. Freely substitutable (same value/rating): all other passives, XO (3.3 V CMOS 10 MHz, ≤ 5 ps jitter, 45–55 % duty), LVC2G34 maker, BAV199 maker (low-leakage series pair), TVS, PTC, ferrites, USB-C 16P, BNC, headers, LEDs, SPI NOR flash (≥ 4 Mbit, 3.3 V), 12 MHz crystal (update C901/C902 = 2(CL − 3 pF)). EEPROM must be a 16-bit-org 93x56 ("B").
6. Pass the keystone list in `## Carried forward` to the datasheet librarian in your handoff.

## Carried forward
- Requirements open items, resolved here: (a) passband 1 MHz / ENOB 10 bit kept — achievable without an unreasonable filter (7 poles, ENOB ≈ 11.2 est.); (b) trigger beyond software → level trigger in gateware + TRIG header; (c) host software out of scope → implied gateware/host listed in `block_diagram.md`.
- Unverified keystone facts (librarian must confirm, I proceeded on them): XC6SLX4/LX9 TQG144 identical pinout; Spartan-6 strap pins (M0/M1 dual-purpose, HSWAPEN high = pull-ups off, SUSPEND → GND, CMPCS_B/VFS handling); OPA2810 SOIC-8 standard dual pinout; **OPA2810/OPA810 gbw_hz = 70e6 in the extraction** (not 105 MHz or 35 MHz — the review gate's filter result depends on it); BAV199 pins 1/2/3; FT232H 3.3 V-only supply wiring, EEPROM 2.2 k/10 k network, ACBUS7 = PWRSAV#; LP5907 max Cout 10 µF; ADS5231 PLL-disable register and power-up order; TLV62569DBV pin order.
- SOFT flatness is tolerance-limited (MC p99 0.61 dB with ±2 % caps); per-board software calibration is the fallback.
- VBUS budget margin is 14 % at worst case; capacitance on VBUS/+5V/+5VA capped at 10 µF (8.9 µF used).
- AFE layout constraints (short high-Z nodes, channel separation, stopband feedthrough) in `design_risks.md` §18–23 bind the physical phase.

## Do not redo
- Architecture choice (FPGA + SDRAM + FT232H), ADC/FPGA/USB/memory selections, filter order and all AFE values, attenuator ratio, rail voltages and dividers, 4-layer stack-up, USB power decision.

## Block manifest
| block_id | block_name | function_signature | interface_nets |
|---|---|---|---|
| `usb_c_input` | USB-C entry + protection | `usb_c_input(v5, usb_dp, usb_dm, gnd)` | `+5V, USB_DP, USB_DM, GND` |
| `power_digital` | 3.3 V buck + 1.2 V LDO | `power_digital(v5, v3v3, v1v2, gnd)` | `+5V, +3V3, +1V2, GND` |
| `power_analog` | ±4 V CP/LDO + 3.3 V analog LDO | `power_analog(v5, v3v3a, vp4a, vn4a, gnd)` | `+5V, +3V3A, +4V0A, -4V0A, GND` |
| `afe_channel` | Analog front end (×2: ch "A" refs 1xx, "B" refs 2xx) | `afe_channel(ch, vin, ain_p, ain_n, adc_cm, vp4a, vn4a, v3v3a, gnd)` | A: `VIN_A, AIN_AP, AIN_AN`; B: `VIN_B, AIN_BP, AIN_BN`; both: `ADC_CM, +4V0A, -4V0A, +3V3A, GND` |
| `adc` | ADS5231 dual ADC | `adc(ain_ap, ain_an, ain_bp, ain_bn, adc_cm, adc_clk, da, db, adc_dva, adc_ovra, adc_ovrb, adc_sel, adc_sen, adc_sclk, adc_sdata, v3v3a, v3v3, gnd)` | `AIN_AP, AIN_AN, AIN_BP, AIN_BN, ADC_CM, ADC_CLK, DA0..DA11, DB0..DB11, ADC_DVA, ADC_OVRA, ADC_OVRB, ADC_SEL, ADC_SEN, ADC_SCLK, ADC_SDATA, +3V3A, +3V3, GND` |
| `clock` | 10 MHz XO + fan-out | `clock(v3v3, adc_clk, clk10_fpga, gnd)` | `+3V3, ADC_CLK, CLK10_FPGA, GND` |
| `sdram` | 16 MB SDRAM | `sdram(sd_dq, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n, sd_we_n, sd_ldqm, sd_udqm, v3v3, gnd)` | `SD_DQ0..15, SD_A0..11, SD_BA0..1, SD_CLK, SD_CKE, SD_CS_N, SD_RAS_N, SD_CAS_N, SD_WE_N, SD_LDQM, SD_UDQM, +3V3, GND` |
| `usb_fifo` | FT232H sync FIFO bridge | `usb_fifo(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_clkout, v3v3, gnd)` | `USB_DP, USB_DM, FT_D0..7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N, FT_CLKOUT, +3V3, GND` |
| `fpga` | Spartan-6 + config flash + JTAG + LEDs + trigger | `fpga(clk10_fpga, da, db, adc_dva, adc_ovra, adc_ovrb, adc_sel, adc_sen, adc_sclk, adc_sdata, sd_dq, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n, sd_we_n, sd_ldqm, sd_udqm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_clkout, v3v3, v1v2, gnd)` | all `adc`↔fpga, `sdram`, `usb_fifo` FIFO nets + `CLK10_FPGA, +3V3, +1V2, GND` |

## Parts by block
| block_id | refs |
|---|---|
| `usb_c_input` | J501, U501, D501, F501, R501, R502, C501 |
| `power_digital` | U601, U602, L601, C601–C606, R601, R602, R604, D601 |
| `power_analog` | U701, U702, FB701, C702, C703, C705–C709, R701–R704 |
| `afe_channel` | A: J101, U101–U103, D101, R101–R115, C101–C121; B: J201, U201–U203, D201, R201–R215, C201–C221 |
| `adc` | U301, FB301, R301–R307, RN301–RN306, C301–C313 |
| `clock` | Y401, U401, FB401, R401, R402, C401–C403 |
| `sdram` | U801, R801–R803, C801–C808 |
| `usb_fifo` | U901, U902, Y901, FB901, R901–R912, C901–C913 |
| `fpga` | U1001, U1002, J1001, J1002, D1002, D1003, R1001–R1006, R1008–R1010, R1012–R1016, C1001–C10nn (one 0.1 µF per supply pin + bulk; coder counts) |

## Receipt
Architecture complete, revision 1. 9 blocks (afe_channel instantiated ×2 → modular coding), 18 ICs (U-refs, incl. flash, EEPROM, USB ESD array), 4-layer board.
constraints.json: 17 entries (12 ac_gain, 5 rail_current), loader-validated; AFE verified in ngspice (−80.9 dB at 5 MHz nominal, 78.7 dB MC worst).
Unresolved: 0 blocking; 11 keystone facts for the librarian; ADS5231 single-source WARN (152 stk).
