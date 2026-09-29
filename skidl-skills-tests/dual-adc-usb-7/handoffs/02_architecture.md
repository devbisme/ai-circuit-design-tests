---
phase: 02_architecture
agent: circuit-architect
circuit: dual_adc_usb
written: 2026-09-22T20:45:00Z
status: complete
revision: 3
next_phase: 03_sourcing
---

# Phase 2 handoff — Architecture (rev.3, final rework — cap reached)

## Decisions

1. **`ADC_SEL` is an FPGA-driven pin, not a strap. R402 stays deleted, permanently.** TI SBAS295A
   p.19 requires a low-going pulse on SEL to reset the ADS5231's serial registers ("may cause the
   device to malfunction" without it); the PLL's power-up default is *enabled*, and only the serial
   write disables it, which is the only path to 10 MSPS (SPEC F3, a `[USER]` number). A static
   strap cannot pulse. Rev.2's pin-budget gain here is reversed: **+1 pin**.
2. **Pin shortfall closed by retiring `ADC_OVRA`/`ADC_OVRB` (−2) and strapping `FIFO_SIWU_N`
   inactive-high through R67 (−1).** Demand 46, available 48 (BANK1 25 + BANK2 23), **margin +2**.
   Full table in `net_plan.md` § "Pin budget, rev.3"; option costing in `design_risks.md` R-12.
   Overrange appears in no SPEC line and clipping stays visible in firmware as code 0x000/0xFFF.
   SIWU# is a plain input with no reset requirement — unlike SEL, it straps safely.
3. **Option (c) — ADC data on BANK3 at 1.8 V — is ILLEGAL and discarded, no level shifters.**
   ADS5231 VDRV is specified **3.0–3.6 V** (SBAS295A p.3) and abs-max "Voltage Between AVDD and
   VDRV" is **±0.3 V**, so VDRV is pinned to AVDD = 3.3 V. Its outputs would drive 3.3 V into BANK3
   pins whose abs max is VCCIO3 + 0.3 = 2.1 V.
4. **R-13 CLOSED — the FPGA has on-die configuration Flash and boots itself. No config part, no
   dongle, no FT232H/MPSSE fallback.** DS117 §2: GW1NR-9 has 4 Mbit embedded Flash split into
   *configuration* Flash and user Flash. DS117 §2.12.2: configuration data transfers from that
   Flash to SRAM on every power-up — Gowin's "instant on". UG290 Table 5-1: MODE[2:0]=000 = AUTO
   BOOT from embedded Flash, exactly what **R54/R55 = 4.7 kΩ to GND already select — unchanged.**
   J3 is a one-time programming header, not a run-time dongle.
5. **U6 pins 37 (VCCA) and 38 (VCORE) are +1.8 V OUTPUTS of the FT232H's internal LDO.** Each gets
   one 100 nF to GND (C606, C608) on block-internal nets `FT_VCCA_1V8` / `FT_VCORE_1V8` and
   **nothing else**. Rev.2 line 16 tied VCORE to `FT_3V3`, back-driving that LDO; VCCA was absent.
   **Neither may feed `P1V8` or any FPGA rail.**
6. **`FT_3V3` is DRIVEN by U6 pin 39 (VCCD). No other block may source it.** U6 RESET# (34) ties
   **directly** to `FT_3V3`, no resistor (was absent from rev.2 entirely).
7. **The input clamp goes to BOTH rails (SPEC I3).** D101/D201 upper-diode cathode → `VA_POS`,
   lower-diode anode → `VA_NEG`. Rev.2's "clamp cathode-side" on `VA_NEG` alone would be
   permanently forward-biased. Fault current (50 − 5.7)/910 k = **48.7 µA** vs BAV199's 250 mA ✓.
8. **U1 (AD8066) gains C15 (100 nF on `VA_POS`) and C16 (100 nF on `VA_NEG`), at the pins.** Rev.2
   assigned U1 no HF decoupling anywhere — a defect on a 10 MSPS front end.
9. **ADS5231 serial pins are 41 = SEN, 42 = SCLK, 45 = SDATA, 1 = SEL, all FPGA-driven.** The
   rev.1/rev.2 static GND ties on 41/42 (`OEA`/`MSBI`) are **gone for good**; only `OEB#` (pin 6)
   ties to GND, and `INT/EXT#` (56) to `P3V3A`.
10. **Refdes collision resolved: R66 = EEPROM `EE_DO` pull-up (FTDI Table 3.3, alongside R64's
    2.2 kΩ series). The FIFO_SIWU_N tie-off moves to R67.** Both parts are real and both ship.
11. **Rev.2 gains that still hold, unchanged:** the `P1V8` rail and U14 (AP2127K-1.8TRG1, chosen on
    soft-start t_on ≥ 180 µs, not current or dropout — DS117 Table 3-3 caps VCCIO ramp at
    10 mV/µs); VCCIO3 = **pin 12 only**; R53 pull-up to `P1V8` (UG803 names the pin
    `IOL13B/RECONFIG_N`, i.e. **BANK3** — verified, so 3.3 V would exceed its 2.1 V abs max);
    R54/R55 MODE straps; the 5-pole anti-alias filter.
12. **Anti-alias filter re-verified from the shipped values**, 100 Ω–3.3 µH–680 pF–5.6 µH–680 pF per
    leg: 4 passive poles on **two distinct nodes split by L2** (no shared-node collapse) + 1 FDA
    feedback pole. Recomputed: **−3 dB 4.247 MHz, −0.68 dB at 4 MHz, −41.3 dB at 10 MHz** vs SPEC
    F8 (≥4 MHz, ≥40 dB at 10 MHz) ✓. Rev.2's 4.23 MHz / −41.8 dB were within rounding; use mine.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `architecture/net_plan.md` | Every net, type, connected refs + the rev.3 pin budget | Always — before writing any code |
| `architecture/ic_selection.md` | Candidates and the winner per block, incl. new §7b (config memory) | Choosing or substituting a part |
| `architecture/skeleton_bom.md` | function \| MPN \| package \| qty \| notes; 161 refs | Sourcing |
| `architecture/design_risks.md` | R-1 and R-13 closed; R-12 re-costed | Before layout, and before any substitution |
| `architecture/block_diagram.md` | Mermaid blocks and signal flow | Orientation |
| `architecture/power_budget.md` | Per-rail current against the USB ceiling | Sizing regulators |

## Block manifest

`function_signature` is **exact and final** — four block files are re-coded against it verbatim.
`afe_driver` and `afe_input` use **`ch`**, never `tag` (SKiDL's `@SubCircuit` consumes `tag=`).

| block_id | block_name | function_signature | interface_nets |
|---|---|---|---|
| `afe_input` | BNC + ÷11 divider + ±50 V clamp | `afe_input(v_att, va_pos, va_neg, gnd, ch)` | `CHA_ATT`/`CHB_ATT`, `VA_POS`, `VA_NEG`, `GND` |
| `afe_buffer` | AD8066 dual unity buffer | `afe_buffer(cha_att, chb_att, cha_buf, chb_buf, va_pos, va_neg, gnd)` | `CHA_ATT`, `CHB_ATT`, `CHA_BUF`, `CHB_BUF`, `VA_POS`, `VA_NEG`, `GND` |
| `afe_driver` | THS4521 FDA + 5-pole anti-alias | `afe_driver(v_buf, adc_inp, adc_inn, adc_cm, p3v3a, gnd, ch)` | `CHA_BUF`/`CHB_BUF`, `ADC_INAP`/`ADC_INBP`, `ADC_INAN`/`ADC_INBN`, `ADC_CM`, `P3V3A`, `GND` |
| `adc_dual` | ADS5231 dual 12-bit 10 MSPS | `adc_dual(inap, inan, inbp, inbn, cm, clk_adc, da, db, dva, sen, sclk, sdata, sel, p3v3a, p3v3d, gnd)` | `ADC_INAP`, `ADC_INAN`, `ADC_INBP`, `ADC_INBN`, `ADC_CM`, `CLK10_ADC`, `ADC_DA[0..11]`, `ADC_DB[0..11]`, `ADC_DVA`, `ADC_SEN`, `ADC_SCLK`, `ADC_SDATA`, `ADC_SEL`, `P3V3A`, `P3V3D`, `GND` |
| `clock_gen` | 10.000 MHz XO + source termination | `clock_gen(clk_adc, clk_fpga, p3v3d, gnd)` | `CLK10_ADC`, `CLK10_FPGA`, `P3V3D`, `GND` |
| `fpga_core` | GW1NR-9 + PSRAM + JTAG + LEDs | `fpga_core(clk_fpga, da, db, dva, sen, sclk, sdata, sel, fifo_d, rxf_n, txe_n, rd_n, wr_n, oe_n, fifo_clk60, p1v2, p1v8, p3v3d, gnd)` | `CLK10_FPGA`, `ADC_DA[0..11]`, `ADC_DB[0..11]`, `ADC_DVA`, `ADC_SEN`, `ADC_SCLK`, `ADC_SDATA`, `ADC_SEL`, `FIFO_D[0..7]`, `FIFO_RXF_N`, `FIFO_TXE_N`, `FIFO_RD_N`, `FIFO_WR_N`, `FIFO_OE_N`, `FIFO_CLK60`, `P1V2`, `P1V8`, `P3V3D`, `GND` |
| `usb_bridge` | FT232HL 245-sync-FIFO + USB-C + ESD | `usb_bridge(vbus, ft_3v3, fifo_d, rxf_n, txe_n, rd_n, wr_n, oe_n, fifo_clk60, pwren_n, gnd)` | `VBUS`, `FT_3V3`, `FIFO_D[0..7]`, `FIFO_RXF_N`, `FIFO_TXE_N`, `FIFO_RD_N`, `FIFO_WR_N`, `FIFO_OE_N`, `FIFO_CLK60`, `PWREN_N`, `GND` |
| `power_tree` | Load switch + 2 bucks + 2 LDOs + charge pump | `power_tree(vbus, vbus_sw, p3v3d, p1v8, p1v2, p3v3a, va_pos, va_neg, pwren_n, gnd)` | `VBUS`, `VBUS_SW`, `P3V3D`, `P1V8`, `P1V2`, `P3V3A`, `VA_POS`, `VA_NEG`, `PWREN_N`, `GND` |

Changes vs rev.2, all forced by the decisions above: `adc_dual`/`fpga_core` lose `ovra`/`ovrb`;
`fpga_core` loses `siwu_n`, gains `p1v8`; `usb_bridge` loses `siwu_n` (R67 is internal to it).
`da`/`db` are 12-bit `Bus`es, `fifo_d` an 8-bit `Bus`.

## Parts by block

| block_id | refs |
|---|---|
| `afe_input` | J1, J2, R101, R102, R201, R202, C101–C103, C201–C203, D101, D201 |
| `afe_buffer` | U1, C11–C14, **C15, C16** |
| `afe_driver` | U2, U3, R111–R118, R211–R218, L111–L114, L211–L214, C111–C119, C211–C219, D111, D112, D211, D212 |
| `adc_dual` | U4, R401, C401–C410 (**R402 deleted — do not re-add**) |
| `clock_gen` | X1, R31, R32, C31 |
| `fpga_core` | U5, J3, D51, D52, R51–R55, C501–C513 |
| `usb_bridge` | U6, U7, U8, J4, Y1, R61–R66, **R67**, C601–C609, **C610–C612** |
| `power_tree` | U9, U10, U11, U12, U13, **U14**, Q1, FB1, L71, L72, R71–R76, C71–C84, **C85, C86** |

## Next phase must

Addressed to **part-sourcer**. `handoffs/bom_pending_changes.md` is the queue; apply it with these:

1. **Source the rev.3 additions:** R67 (10 kΩ 0402), R66 (10 kΩ 0402, EEPROM `EE_DO` pull-up),
   C15, C16, C610, C611, C612 (100 nF X7R 0402). **Delete R402.** Keep U14, C85, C86, R54, R55.
2. **Refdes discipline: R66 belongs to the EEPROM pull-up; the SIWU tie-off is R67.** Nothing may
   collide with the existing set — 161 refs after this pass.
3. **Critical path, package fixed, do not substitute without escalating:** U4 (ADS5231IPAGT — the
   only dual-12-bit simultaneous part that fits the pin and power budget), U5 (GW1NR-LV9QN88PC6-I5
   QN88P — the 8 MB in-package PSRAM *is* SPEC F6, and the on-die config Flash *is* the R-13
   answer), U6 (FT232HL), U14 (**t_on ≥ 180 µs soft-start is the selection criterion**, not current
   or dropout — any alternate must have its t_on confirmed against that floor).
4. **Freely substitutable:** X1 (any 10.000 MHz CMOS XO, ≤±30 ppm, ≥3.3 V, with OE), all passives
   at the stated E-series values and tolerances, D51/D52, J1/J2, Y1.
5. **Vetted second sources:** U14 → RT9013-18GB or TLV73318PDBVR (t_on check first); U12 →
   RT9013-33GB family. No second source vetted for U4, U5 or U6 — flag them single-source (R4).
6. Apply the two symbol-cell corrections already queued (U7 → `Memory_EEPROM:93LCxxBxxOT`,
   Y1 → `Device:Crystal_GND24`, D101/D201 → `Diode:BAV99`). MPNs and footprints are unchanged —
   the BOM cell is the wrong side in all three.

## Carried forward

| Item | Resolution / why still open |
|---|---|
| SPEC open question 3 — 500 mA legacy A-to-C host | **Resolved by the architect:** the board does not fit in 500 mA and does not detect it. `PWREN_N` gates everything but U6 behind U9 until enumeration, so pre-enumeration draw stays under 150 mA (P3); after that the design assumes a Type-C source honouring the 5.1 kΩ Rp. On a legacy A-to-C cable the board will brown out rather than refuse. Accepted, documented, not fixed. |
| SPEC open questions 1, 2, 4 (D5 SNR, D6 burst, R3 cost) | Unchanged — user-level, not architecture-level. Burst capture is out of scope for this rework. |
| U5 symbol pin 12 mislabelled `VCCX_VCCO0` | Must read `VCCIO3`; still unfixed in `symbols/dual_adc_usb.kicad_sym` (owner: datasheet-librarian). **Do not wire U5 power until corrected.** |
| THS4521 PD (pin 7) polarity | Assumed active-low per TI convention, not confirmed from the electrical table. Wired to `P3V3A` (enabled) on that assumption — confirm before fab. |
| USBLC6-2SC6 junction capacitance | Phase 4's one open keystone fact; proceeded assuming 0.35 pF on D+/D−. Low consequence, USB HS only. |
| Sourcing constraint from risks | U14 must be a **soft-start** LDO (R-14). Nothing on this board needs AEC-Q100. |
| Pin margin | **+2, and final.** There is no third reduction available — every remaining signal is 3.3 V and BANK3 cannot carry any of it. Any new signal is a user escalation, not a rework. |

## Do not redo

- The GW1NR-9 bank/rail analysis (BANK3 = VCCIO3 = pin 12 = 1.8 V PSRAM bank), the 48-I/O count,
  the `P1V8` rail and U14 — all verified against UG803/DS117 and settled.
- R-13 (configuration memory) — closed against DS117 §2 / §2.12.2 / UG290 Table 5-1. Do not
  re-open it, do not add an SPI flash, do not implement the MPSSE fallback.
- The `ADC_SEL` static-strap idea — refuted against SBAS295A p.19. Do not re-propose it.
- Putting any 3.3 V signal on BANK3 — refuted against SBAS295A's VDRV limits.
- The FDA polarity crossing (`CHA_FDAP`-leg → `ADC_INAN`), the divider ratio, the filter values,
  and the `ch` parameter name.

## Receipt

- 8 blocks, 14 ICs, 161 refs. Pin budget **46 used / 48 available, +2 margin** — final.
- Pin shortfall closed: OVRA/OVRB retired (−2), FIFO_SIWU_N strapped to R67 (−1); ADC data on
  BANK3 discarded as illegal (ADS5231 VDRV 3.0–3.6 V, |AVDD−VDRV| ≤ 0.3 V).
- R-13 **closed**: GW1NR-9 has 4 Mbit on-die config Flash, AUTOBOOT via existing R54/R55. No part,
  no pins, no MPSSE fallback. R-1 closed. R-12 re-costed.
- 6 net_plan defects folded in; R66/R67 collision resolved; 7 refs added, R402 deleted.
- 4 signatures changed (`adc_dual`, `fpga_core`, `usb_bridge` lose pins; `fpga_core` gains `p1v8`).
- Unresolved risks: 3 (U5 symbol pin-12 label, THS4521 PD polarity, USBLC6 capacitance) — none
  block sourcing. Revision 3. **Architecture rework cap reached.**
