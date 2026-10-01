---
phase: 02_architecture
agent: circuit-architect
circuit: dual_adc_usb
written: 2026-09-30T23:59:00Z
status: complete
revision: 2
next_phase: 03_sourcing
---

# Phase 2 handoff — Architecture (rev 2, escalation from 04_datasheets)

## Decisions
Rev 2 resolves the `handoffs/04_datasheets.md` blockers. Every rev 1 decision not named here still stands.
- **New +1V8 rail = third TLV62569DBVR (U12) from VBUS_SW**, 200k/100k on VFB 0.600 V → 1.800 V (1.741–1.861 V ⊂ VCCO3 1.71–1.89 V). It won over a TLV75718P LDO from +3V3D because the LDO puts 100 mA through the 3V3D buck and pushes the budget to 541 mA (with ×1.25 margin, at 4.4 V), over the 500 mA limit. The buck gives 496 mA. It is also the same MPN as U3/U4.
- **Sequencing (UG284):** U12.EN = VBUS_SW, the same as U4, so VCC and VCCO3 (the POR supplies) ramp together in 0.8 ms (tSS, K7). +3V3D stays EN-delayed by 2.0–3.2 ms. All three rails come up in 0.2–2 ms, so UG284 imposes no order, and VCC still precedes VCCX/VCCO1/2. Ramps: 1.50 mV/µs, 2.25 mV/µs and 4.16 mV/µs, all in spec. Working is in net_plan §2 pwr_digital.
- **On +1V8 now:** U9.VCCO3 (12), C91, C93 (new 10 µF), R80 (RECONFIG_N pull-up), R85 (JTAGSEL_N pull-up) and J4 pin 1 (JTAG VREF). MODE0/1 keep their 1 kΩ pull-downs to GND.
- **READY/DONE are not bonded:** R82 is deleted. R81 is repurposed as the 4.7 kΩ **TCK pull-down to GND** (UG284 Fig. 2).
- **FPGA I/O, 53 → 48 of 48 at 3.3 V:**
  - Dropped: ADC_DVA/DVB (capture on the phase-shifted FPGA_CLK40) and ADC_OVRA/OVRB (over-range = saturated codes in gateware). U7 pins 26/22/39/9 are NC.
  - FT_SIWU_N is gone: U10.ACBUS4 is tied to +3V3D, which DS_FT232H permits.
  - Reserve: tie ADC_OEB low to free 1 pin.
  - Rejected: moving CLK40/LEDs/trigger to bank 3, translators, and a bigger package. The table is in ic_selection §2a.
  - **The U9 pin map is now fixed** in net_plan §2 fpga. FPGA_CLK40 goes to pin 63 (RPLL_T_in), FT_CLKOUT to pin 52 (GCLKT_3).
- **Capture without DV:** the ADS5231 data window is 14.8–25.0 ns after CLK↑ (10.2 ns). After U8 skew and FPGA setup/hold that leaves ≈5 ns margin. The right PLL phase-shifts the capture clock by ≈ +20 ns, calibrated with the ADC serial test pattern. This is why SEL/SEN/SCLK/SDATA stay on the FPGA.
- **Y1 → YXC OT322540MJBA4SL** (C2831396, stock 10 567): **0.7 ps rms max (12 k–20 MHz), published** → SNR_j 93.2 dB, combined 70.68 dB (ENOB 11.45), against a budget of ≤5.04 ps. Pinout is the same (1 OE, 2 GND, 3 OUT, 4 VDD), and it draws 5 mA vs 20 mA. K8 is closed.
- **Power budget re-run** (P1), using FT232H at 112 mA max and +1V8 at 100 mA:
  - At 4.4 V: 396 mA, 1.74 W; with ×1.25 margin, 496 mA < 500 mA.
  - At 5.25 V: 1.84 W < 2.25 W.
  - The USB-C power trigger is still not fired.
  - Margin is now 1 %, so the budget depends on K5 and K10 (below).
- **Y2 load caps C110/C111 = 33 pF C0G:** 16.5 pF plus 3–5 pF stray = 19.5–21.5 pF, against CL 20 pF.
- Folded in from phase 4 (verified facts, no new parts):
  - REFT/REFB per ADS5231 Fig. 21: 2 Ω from the pin, then 0.1 µF ‖ 2.2 µF. New nets ADC_REFT_F/ADC_REFB_F.
  - FT232H VCCA (37) and VCCCORE (38) are joined on FT_VCCCORE with C109.
  - R102 = 10 kΩ and R103 = 2.2 kΩ are confirmed.
  - The UG284 VCC ferrite bead is **not** added: buck ripple is ≈0.8 %, under the 3 % limit.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `architecture/net_plan.md` | Every net, U9 pin map, sequencing, all arithmetic (rev 2 edits marked `<!-- revised -->`) | Always — before coding |
| `architecture/skeleton_bom.md` | Refs/MPN/qty with a `Chg` column + rev 2 sourcing worklist at the end | Sourcing |
| `architecture/ic_selection.md` | Trades; new §2a I/O options, +1V8 regulator trade, XO trade | Before substituting an IC |
| `architecture/design_risks.md` | P1 budget, P3 sequencing, P7 +1V8 load, A8 jitter, T4 capture, T7 I/O, L6 JTAG 1.8 V | Sourcing, layout, bring-up |
| `architecture/block_diagram.md` | Mermaid diagram (now with U12 +1V8) | Orientation |
| `datasheets/OT322540MJBA4SL.pdf` | YXC YSO110TR datasheet (image-only; jitter p.1, pinout p.2) | Verifying Y1 |

## Next phase must
1. part-sourcer: **re-source only the rows tagged in `skeleton_bom.md` `Chg`**. Keep every untagged `sourced_bom.csv` row verbatim.
   - **MODIFIED-RESOURCE** (new search):
     - Y1 → OT322540MJBA4SL (C2831396).
     - C110/C111 → 33 pF C0G 50 V 0402.
   - **ADDED, new value:** R14 200 kΩ 1 % 0402.
   - **ADDED / MODIFIED-QTY on existing rows** (append refs, no search):
     - U12 → TLV62569DBVR (qty 3).
     - L3 → FHD4020S-2R2MT (qty 3).
     - C9, C93 → 10 µF 0603 CL10A106KP8NNNC.
     - C17 → 22 µF 0805 row.
     - R15 → 100 kΩ row.
   - **REMOVED:** R82, so the 4.7 kΩ row becomes R80, R81, R85 (qty 3).
   - **MODIFIED-NET (no action):** C91, R80, R81, R85, J4.
2. Y1 substitutes must have a **published** rms jitter ≤5 ps (12 k–20 MHz) and pinout 1 OE/2 GND/3 OUT/4 VDD. Second source: TAITIEN OXETGLJANF-40.000000MHZ (C7470494, 1 ps max). Verify that the `Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm` land pattern fits YXC 3225.
3. Critical-path parts are unchanged and must be bought as named: U7 ADS5231IPAGT, U9 GW1NR-LV9QN88PC6/I5, U10 FT232HL-REEL.
4. Values fixed (do not change): R14/R15 (+1V8 divider), C110/C111 33 pF C0G, and all rev 1 fixed values (AFE R/C, R5–R13, R62, R100, C2).
5. Package-fixed parts are unchanged: R20/R40 1206 ≥150 V, C20/C40 100 V, U9 QFN-88 0.4 mm, U7 TQFP-64.
6. Datasheet phase (delta only): add `datasheets/OT322540MJBA4SL_SUMMARY.md`. The symbol is the same `Oscillator:ASE-xxxMHz` class: EN = pin 1, tie high. Nothing else needs re-summarising.
7. Coders:
   - Use the U9 pin map in net_plan §2 fpga verbatim.
   - Mark U7 DVA/DVB/OVRA/OVRB as NC.
   - U10 ACBUS4 → +3V3D.

## Carried forward
- **Named assumptions (unverified keystone facts; the design proceeds on them):**
  - **K3:** the Gowin PSRAM IP sustains ≥40 MB/s. The device's raw rate is 664 MB/s (verified). Close with IPUG943.
  - **K5:** GW1NR VCC (+1V2) ≤150 mA dynamic. DS117 gives only 3.5 mA static. Close with a Gowin Power Analyzer run.
  - **K10 (new):** +1V8 load ≤100 mA, assuming VCCO3 also powers the in-package PSRAM (2 × 40 mA active + ≈11 mA bank-3 drivers). Close with GPA.
  - **EP = GND:** U9 exposed pad (symbol pin 89) to GND. UG119 says only "exposed pad", so this rests on industry practice. Close with a newer Gowin hardware guide or UG284 revision.
- **K5 + K10 now set the USB 2.0 margin** (496 of 500 mA with ×1.25, at 4.4 V). If GPA exceeds 150/100 mA, the first lever is gateware holding ADC STPD=1 until the host opens the device (−55 mA). After that, re-architect.
- 48/48 3.3 V FPGA I/O are used. Any added 3.3 V signal needs ADC_OEB tied low (frees 1 pin) or an architecture change. Bank 3 has 15 free 1.8 V I/O for debug.
- The JTAG programmer must support 1.8 V VREF (Gowin GWU2X does). 3.3 V-only FT2232 clone cables will overdrive bank 3 (design_risks L6).
- Assumed, not in a datasheet I read: U8 (LVC1G34 @3.3 V) tpd spread ≈3.2 ns and FPGA tSU+tH ≈2 ns, in the capture-margin arithmetic. The PLL phase calibration absorbs both.
- Gateware obligations:
  - 4:1 FIR, PSRAM controller, FT245 sync FIFO.
  - Over-range flagged from codes 0x000/0xFFF.
  - Capture-phase calibration via the ADC test pattern.
  - Dual-purpose bank-1 pins (53–62) set as regular I/O.
  - FT232H EEPROM set to 245-FIFO mode at bring-up.
- Rev 1 carried items still open: USB-C chosen though the trigger did not fire (micro-B is the fallback). ADS5231/GW1NR are single-source with stock <500 (S1/S2). Everything is Extended tier.

## Do not redo
- All rev 1 trades: capture engine, ADC, FPGA part, bridge, sample strategy, AAF, attenuator, gain chain, rail dividers R5–R13.
- Rev 2 trades: +1V8 by buck, the I/O shedding set (DV/OVR/SIWU#), the U9 pin map, the Y1 choice. Also K4/K6/K7/K8/K9, which are now closed.

## Block manifest
| block_id | block_name | function_signature | interface_nets |
|---|---|---|---|
| `usb_power_in` | USB-C input, ESD, PTC, soft-start | `usb_power_in(vbus_sw, usb_dp, usb_dm, gnd)` | `VBUS_SW, USB_DP, USB_DM, GND` |
| `pwr_digital` | 3V3D + 1V2 + 1V8 bucks | `pwr_digital(vbus_sw, v3v3d, v1v2, v1v8, gnd)` | `VBUS_SW, +3V3D, +1V2, +1V8, GND` |
| `pwr_analog` | 3V3A LDO + ±AFE rails | `pwr_analog(vbus_sw, v3v3a, vafe_p, vafe_n, gnd)` | `VBUS_SW, +3V3A, VAFE_P, VAFE_N, GND` |
| `afe_ch_a` | Ch A BNC→attenuator→buffer→AAF/FDA | `afe_ch_a(ain_p, ain_n, adc_vcm, vafe_p, vafe_n, v3v3a, gnd)` | `ADC_AINA_P, ADC_AINA_N, ADC_VCM, VAFE_P, VAFE_N, +3V3A, GND` |
| `afe_ch_b` | Ch B (identical, refs +20) | `afe_ch_b(ain_p, ain_n, adc_vcm, vafe_p, vafe_n, v3v3a, gnd)` | `ADC_AINB_P, ADC_AINB_N, ADC_VCM, VAFE_P, VAFE_N, +3V3A, GND` |
| `adc_dual` | ADS5231 + refs/decoupling | `adc_dual(aina_p, aina_n, ainb_p, ainb_n, adc_vcm, adc_clk, adc_da, adc_db, adc_sel, adc_msbi_sen, adc_oea_sclk, adc_stpd_sdata, adc_oeb, v3v3a, v3v3d, gnd)` | `ADC_AINA_P, ADC_AINA_N, ADC_AINB_P, ADC_AINB_N, ADC_VCM, ADC_CLK, ADC_DA[0..11], ADC_DB[0..11], ADC_SEL, ADC_MSBI_SEN, ADC_OEA_SCLK, ADC_STPD_SDATA, ADC_OEB, +3V3A, +3V3D, GND` |
| `clock_gen` | 40 MHz XO + FPGA buffer | `clock_gen(adc_clk, fpga_clk40, v3v3d, gnd)` | `ADC_CLK, FPGA_CLK40, +3V3D, GND` |
| `fpga` | GW1NR-9, config, JTAG, LEDs, trigger | `fpga(fpga_clk40, adc_da, adc_db, adc_sel, adc_msbi_sen, adc_oea_sclk, adc_stpd_sdata, adc_oeb, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_clkout, ft_oe_n, v1v2, v1v8, v3v3d, gnd)` | `FPGA_CLK40, ADC_DA[0..11], ADC_DB[0..11], ADC_SEL, ADC_MSBI_SEN, ADC_OEA_SCLK, ADC_STPD_SDATA, ADC_OEB, FT_D[0..7], FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_CLKOUT, FT_OE_N, +1V2, +1V8, +3V3D, GND` |
| `usb_bridge` | FT232H + EEPROM + 12 MHz | `usb_bridge(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_clkout, ft_oe_n, v3v3d, gnd)` | `USB_DP, USB_DM, FT_D[0..7], FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_CLKOUT, FT_OE_N, +3V3D, GND` |

Changed in rev 2: `pwr_digital` (+v1v8), `adc_dual` (−ovra/ovrb/dva/dvb), `fpga` (−ovr/dv/siwu, +v1v8), `usb_bridge` (−ft_siwu_n).

## Parts by block
| block_id | refs |
|---|---|
| `usb_power_in` | J1, U1, U2, F1, D1, R1, R2, R3, C1, C2, C3 |
| `pwr_digital` | U3, U4, U12, L1, L2, L3, R5, R6, R7, R8, R9, R14, R15, C4, C5, C6, C7, C8, C9, C17 |
| `pwr_analog` | U5, U6, R10, R11, R12, R13, C10, C11, C12, C13, C14, C15, C16 |
| `afe_ch_a` | J2, U20, U21, D20, R20–R30, C20–C31 |
| `afe_ch_b` | J3, U40, U41, D40, R40–R50, C40–C51 |
| `adc_dual` | U7, R60, R61, R62, C60–C73 |
| `clock_gen` | Y1, U8, R70, R71, C75, C76 |
| `fpga` | U9, R80, R81, R83–R89, D80, D81, J4, J5, C80–C93 |
| `usb_bridge` | U10, U11, Y2, R100–R103, C100–C111 |

## Receipt
dual_adc_usb architecture rev 2: status complete. 9 blocks, 12 distinct IC MPNs, 16 IC placements (+U12).
- BOM delta: 3 rows to re-source (Y1, C110/C111, R14 200k), 6 refs added to existing rows, R82 removed.
- FPGA I/O 48/48 at 3.3 V. Budget 496 mA (×1.25, 4.4 V) < 500 mA; this depends on K5/K10.
- 4 named assumptions open (K3, K5, K10, EP=GND); K8 closed.
