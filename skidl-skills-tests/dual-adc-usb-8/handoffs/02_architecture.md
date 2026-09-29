---
phase: 02_architecture
agent: circuit-architect
circuit: dual_adc_usb
written: 2026-09-26T03:40:00Z
status: complete
revision: 1
next_phase: 03_sourcing
---

# Phase 2 handoff — Architecture

## Decisions
- **ADC = ADS5231IPAGT** (dual 12-bit 40 MSPS, one die). Options were ADS5231, 2×AD9235-40, 2×AD9237-40 and AD9238-65. It won on inherent simultaneous sampling, the lowest per-board cost ($30 vs $50–65), and stock ≥ 100.
- **Oversample 40 MSa/s, decimate ×4 in the FPGA to 10 MSa/s.** The ADS5231 minimum rate is 20 MSPS with its PLL on. Also, a 5 MHz band sampled at 10 MSa/s cannot be anti-aliased: the alias edge sits at 5 MHz. At 40 MSa/s the alias edge moves to 35 MHz, where the analog filter gives −32.1 dB.
- **Capture engine = GW1NR-LV9QN88PC6/I5 FPGA.** Its in-package 2×32 Mbit PSRAM gives 8 MiB, i.e. 0.21 s at 10 MSa/s (≥ 0.1 s ✓). Rejected:
  - GW2AR-18: 2.4× the cost.
  - ECP5 + SDRAM: BGA, an external SDRAM and a flash.
  - MCU DCMI: at most 14 bits wide, and 24 are needed.
- **USB bridge = FT232HL** in sync 245 FIFO mode (≈35 MB/s, no firmware). Capture-to-buffer, then upload: 4 MB takes 0.114 s. Rejected:
  - FX2LP: needs firmware and more pins.
  - FT601: needs 32 data pins.
- **Front end per channel:**
  - Compensated divider R_T 909 kΩ (top) / R_B 100 kΩ (bottom) → 0.09911, giving 1.009 MΩ ‖ 19.8 pF (+ BNC parasitics ≈ 22 pF).
  - OPA356 unity buffer, then a THS4551 FDA wired as a 2-pole MFB (gain 0.909, f0 9.28 MHz, Q 0.767), then a 49.9 Ω / 56 pF RC.
  - Overall gain 0.09009 V/V → FS ±11.21 V, LSB 5.47 mV.
  - Response: −0.58 dB at 5 MHz, −3 dB at 8.86 MHz, −32.1 dB at 35 MHz. Working is in `design_risks.md` §2.
- **Buffer rails are asymmetric: VP_AFE +3.288 V, VN_AFE −2.012 V**, from an LM27762. Its FB+ divider is 174k/100k and its FB− divider is 64.9k/100k.
  - Why: the OPA356 input CM tops out at (V+) − 1.5 V. On ±2.5 V rails that is 1.02 V, which is less than the 1.111 V peak and fails. On +3.288 V it is ≥ 1.698 V.
  - The total supply is ≤ 5.438 V, against the 5.5 V limit.
- **OPA356 over OPA357.** The OPA357's RRIO crossover region can start 0.087 V above the peak signal. The OPA356 is also a third of the price and has 3× the stock.
- **The ADC clock comes straight from a 40 MHz XO** (budget ≤ 3 ps rms → 80.5 dB SNRj). The same XO feeds the FPGA through a separate 33 Ω branch. The FPGA PLL is never in the ADC clock path.
- **ADS5231 runs in parallel-pin mode:**
  - SEL, MSBI, OEA and OEB go to GND.
  - INT/EXT goes to V3V3A, which selects the internal reference.
  - STPD is FPGA-driven with a 10k pull-down.
  - VDRV is fed from V3V3A through FB1. The |AVDD − VDRV| ≤ 0.3 V absolute maximum forbids feeding it from V3V3D.
- **Power:** one USB-C input feeds a TPS22919 soft-start switch, which produces V5. From V5:
  - 2× TLV62569 bucks make V3V3D (3.315 V; 100k/22.1k) and V1V2 (1.200 V; 100k/100k). VFB is 0.600 V per the TI datasheet.
  - A TLV75518P LDO makes V1V8 for the FPGA's PSRAM bank 3.
  - A TPS7A2033 LDO makes V3V3A for the ADC, FDAs and XO.
- **USB power rule — USB-C.** The budget is 1.22 W typical and 2.03 W worst case, which exceeds the ~2.0 W threshold. So the board uses a USB-C receptacle (TYPE-C-31-M-12), USB 2.0 data only, with Rd 5.1 kΩ on CC1 and CC2. The worst-case current is 404 mA (< 500 mA), so the board still works from a legacy USB 2.0 port.
- **Trigger scheme (open item, resolved).** The host starts a capture in software. The FPGA also provides a digital level/edge trigger on either channel and an external TRIG_IN/TRIG_OUT (3.3 V, 100 Ω series) on aux header J5. There is no analog trigger comparator: the FPGA has no spare pins for one, and the digital trigger is enough at 12 bits.
- **SMD-only (SOFT) is relaxed** for the BNCs (KH-BNC50-3511, THT) and the headers, because mechanical retention needs through-hole. Everything else is SMD. Use a 4-layer board.
- Single GND net and plane, with no AGND split.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `architecture/block_diagram.md` | Mermaid diagram, signal-flow/rate table | Orientation |
| `architecture/net_plan.md` | Every interface and internal net, pin-level ADC/FPGA power map, bank rules | Always — before writing any code |
| `architecture/ic_selection.md` | 2–4 candidates per block with stock/price and why each loser lost | Before substituting any IC |
| `architecture/skeleton_bom.md` | Function, MPN, package, qty, refs, every passive value with arithmetic | Sourcing |
| `architecture/design_risks.md` | Power budget, filter response, jitter, thermal, layout, FPGA bank risks | Sourcing, coding, review |

## Block manifest
| block_id | block_name | function_signature | interface_nets |
|---|---|---|---|
| `usb_power_in` | USB-C input, ESD, load switch | `usb_power_in(v5, usb_dp, usb_dn, gnd)` | `V5, USB_DP, USB_DN, GND` |
| `power_digital` | 3.3 V/1.2 V bucks, 1.8 V LDO | `power_digital(v5, v3v3d, v1v2, v1v8, gnd)` | `V5, V3V3D, V1V2, V1V8, GND` |
| `power_analog` | 3.3 V analog LDO, ± AFE rails | `power_analog(v5, v3v3a, vp_afe, vn_afe, gnd)` | `V5, V3V3A, VP_AFE, VN_AFE, GND` |
| `afe_ch_a` | Channel A front end (BNC→ADC) | `afe_ch_a(ain_p, ain_n, vcm, v3v3a, vp_afe, vn_afe, gnd)` | `AIN_A_P, AIN_A_N, VCM, V3V3A, VP_AFE, VN_AFE, GND` |
| `afe_ch_b` | Channel B front end (BNC→ADC) | `afe_ch_b(ain_p, ain_n, vcm, v3v3a, vp_afe, vn_afe, gnd)` | `AIN_B_P, AIN_B_N, VCM, V3V3A, VP_AFE, VN_AFE, GND` |
| `adc` | ADS5231 dual ADC | `adc(ain_a_p, ain_a_n, ain_b_p, ain_b_n, vcm, adc_clk, da, db, adc_dva, adc_stpd, v3v3a, gnd)` | `AIN_A_P, AIN_A_N, AIN_B_P, AIN_B_N, VCM, ADC_CLK, DA0…DA11, DB0…DB11, ADC_DVA, ADC_STPD, V3V3A, GND` |
| `clock` | 40 MHz XO + fan-out | `clock(adc_clk, fpga_clk, v3v3a, gnd)` | `ADC_CLK, FPGA_CLK, V3V3A, GND` |
| `fpga` | GW1NR-9 capture engine | `fpga(fpga_clk, da, db, adc_dva, adc_stpd, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_siwu_n, ft_clkout, ft_oe_n, v3v3d, v1v2, v1v8, gnd)` | `FPGA_CLK, DA0…DA11, DB0…DB11, ADC_DVA, ADC_STPD, FT_D0…FT_D7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_SIWU_N, FT_CLKOUT, FT_OE_N, V3V3D, V1V2, V1V8, GND` |
| `usb_bridge` | FT232H USB 2.0 HS FIFO | `usb_bridge(usb_dp, usb_dn, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_siwu_n, ft_clkout, ft_oe_n, v3v3d, gnd)` | `USB_DP, USB_DN, FT_D0…FT_D7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_SIWU_N, FT_CLKOUT, FT_OE_N, V3V3D, GND` |

`da`, `db` are 12-net buses (index 0 = LSB) and `ft_d` is an 8-net bus. Nine blocks puts this in modular mode.

## Parts by block
| block_id | refs |
|---|---|
| `usb_power_in` | J1, U1, U2, R1, R2, C1, C2, C3 |
| `power_digital` | U3, U4, U5, L1, L2, D1, R3, R4, R5, R6, R7, C4, C5, C6, C7, C8, C9 |
| `power_analog` | U6, U7, R8, R9, R10, R11, C10, C11, C12, C13, C14, C15, C16, C17 |
| `afe_ch_a` | J2, U101, U102, D101, R101–R111, C101–C114 |
| `afe_ch_b` | J3, U201, U202, D201, R201–R211, C201–C214 |
| `adc` | U8, FB1, R12, R13, R14, R15, C18–C30 |
| `clock` | X1, FB2, R16, R17, C31, C32 |
| `fpga` | U9, J4, J5, D2, D3, R18–R24, C33–C46 |
| `usb_bridge` | U10, U11, Y1, R25, R26, R27, C47–C56 |

## Next phase must
1. part-sourcer: treat these as **critical-path** parts, and confirm lifecycle, not just stock:
   - U8 ADS5231IPAGT: 235 in stock, single source (TI), no pin-compatible second source. Fallback is 2×AD9235BCPZ-40, which means an architecture escalation.
   - U9 GW1NR-LV9QN88PC6/I5: 182 in stock (WARN). The package is fixed: QN88**P**, which carries the PSRAM. A plain QN88 has SDRAM and a different bank-voltage map, so it is **not** a substitute.
   - U10 FT232HL-REEL.
   - X1: must meet ≤ 3 ps rms jitter and 45–55 % duty.
2. These have **constrained substitutes**:
   - U101/U201 must keep input CM ≥ 1.111 V below V+ (see `ic_selection.md` §4).
   - U102/U202 FDA must accept input CM 0.52–1.05 V and VOCM 1.5 V on 3.3 V.
   - U3/U4 dividers assume VFB = 0.600 V. Any substitute buck needs its divider recomputed.
   - U7 dividers assume 1.2 V / −1.22 V references.
3. **Freely substitutable** (same function and package): U1, U2, U5, U6 (fixed 3.3 V, ≥ 300 mA, low-noise), U11, D1–D3, FB1/FB2, J4/J5, all 0.1–22 µF decoupling.
4. Fixed-spec passives:
   - R101/R201 must be **1206** (voltage).
   - C101/C201 22 pF must be C0G ±1 %, ≥ 100 V.
   - C102/C202 150 pF must be C0G ±1 %.
   - C104/C204: LXRW19V330-050 trimmer (16.5–33 pF). A substitute needs a mid-range near 24 pF, otherwise recompute C_B1/C_B2.
   - R104/R105, R106/R107, R108/R109 (and 2xx) are matched pairs.
5. Use the E-series values in `skeleton_bom.md` exactly. Do not round any divider value.
6. Record LCSC# and KiCad footprints. Symbols are **missing** for ADS5231, GW1NR-9, OPA356, TPS7A2033 and TPS22919; flag them for phase 4 generation.

## Carried forward
- Resolved without the user (the driver chose these SOFT items):
  - (a) Bandwidth: ≥ 5 MHz at Nyquist is not physically compatible with anti-aliasing. It is revised to analog −3 dB 8.86 MHz, and at the 10 MSa/s output a digital passband of 0–4 MHz with −3 dB ≈ 4.5 MHz. A raw 40 MSa/s mode delivers the full analog band.
  - (b) The trigger scheme is as in Decisions.
  - (c) The connector is USB-C, per the power rule.
  - (d) THT BNCs and headers.
- **Unverified keystone facts** (phase 4 must confirm them before coding). The assumption made for each:
  - GW1NR-9 QN88P pin numbers beyond the power pins, the ≈ 48 3.3 V I/O count on banks 1 and 2, the JTAG pins 5–8, and GCLK pin 52. **Assumed** per UG803 parsing.
  - MODE0/MODE1 pulled down = AUTOBOOT from internal flash.
  - FT232H "3.3 V-only" power-pin wiring, its HS current (assumed 60/80 mA), and the EEPROM DO 2.2 kΩ wiring.
  - GW1NR core, IO and PSRAM currents are estimates. **Run the Gowin power estimator**: if the worst case rises further it is still USB-C, but the 3V3D buck or LDO sizing must be rechecked.
  - Y1 CL = 20 pF (which sets C47/C48 = 33 pF). X1 pin 1 = OE (tied high). The BAV199, OPA356 and THS4551 FB-pin pinouts.
  - TPS7A2033 θJA ≈ 200 °C/W gives TJ ≈ 104 °C. If worse, move X1 to V3V3D.
- Risk that constrains sourcing: the aliasing floor at 35–40 MHz is −32 to −35 dB. It is accepted and documented.

## Do not redo
- ADC/FPGA/USB-bridge choices, the 40 MSa/s oversampling architecture, and the front-end topology and values (`net_plan.md`, `skeleton_bom.md`).
- The USB-C decision (worst case 2.03 W > 2.0 W).
- The asymmetric AFE rails +3.288/−2.012 V.

## Receipt
Architecture complete, rev 1: 9 blocks, 15 ICs + XO + crystal, 5 connectors, modular mode. Power is 1.22 W typ / 2.03 W worst case, so USB-C (404 mA max).
Seven unverified keystone facts are carried forward, and 5 parts need KiCad symbols generated. Critical parts are single-source ADS5231 (235 stock) and GW1NR-9 QN88P (182 stock).
