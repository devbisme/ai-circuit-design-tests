---
phase: 02_architecture
agent: circuit-architect
circuit: dual_adc_usb
written: 2026-09-10T18:40:00Z
status: complete
revision: 1
next_phase: 03_sourcing
---

# Phase 2 handoff — Architecture

## Decisions
- **ADC = ADS5231IPAGT** (TI dual 12-bit 40 MSPS, TQFP-64). It is the only *dual* 12-bit ADC stocked ≥ 100 at JLC
  (AD9238 has 0). One die gives simultaneous sampling and matched reference (F5). It costs $15/ch vs $25/ch for
  2×AD9235-40, and its SNR of 70.7 dB clears ENOB ≥ 10.
- **Run the ADC at 20 MSPS, PLL on (default mode); the FPGA decimates 2:1 to 10 MSPS/ch.** With the PLL on the
  minimum rate is 20 MSPS; 10 MSPS needs PLL-off via the serial interface. Oversampling moves the alias band to
  15–25 MHz. 10 MHz is a BOM-only fallback (swap X1; gateware writes the PLL-off register).
- **FPGA = GW1NR-LV9QN88PC6/I5.** It is the only stocked FPGA with ≥ 384 kbit RAM (16 k × 24 b HARD buffer →
  468 kbit BSRAM) *and* ≥ 44 I/O at 3.3 V. The 64 Mbit in-package PSRAM (8 MB ≈ 280 ms at 30 MB/s) is the
  streaming elastic buffer. iCE40UP5K lost on I/O (39); GW1N-4 lost on RAM (180 kbit).
- **QN88P bank 3 is fixed at 1.8 V** (it powers the PSRAM). JTAG is therefore 1.8 V (J4 VREF = VD_1V8).
  LEDs, trigger, and GPIO leave bank 3 through U16 SN74LV4T125 (1.8→3.3 V) and U17 SN74LV1T34 (5 V-tolerant → 1.8 V).
  Banks 1+2 (48 pins at 3.3 V) carry the ADC and FT232H: 47 used, 1 spare → TP10.
- **USB bridge = FT232HL** in 245 sync-FIFO mode (60 MHz, 8-bit, "up to 40 MB/s"). It needs 14 FPGA pins, where
  FX2LP needs about 24 (the pins do not exist), and no device firmware. Streaming at 30 MB/s packed is 75 % of its ceiling.
- **Front end:** a 906 kΩ (2×453 k 1206) / 100 kΩ compensated 10:1 divider **to ground**, which gives a true 1 MΩ ∥ ~20 pF
  to GND. A single-supply level shift would make the BNC float, so it was rejected. Then BAV199 clamps to ±2.5 V,
  an OPA354 unity buffer (RRIO, 150 V/µs; OPA356 lost on +CM range, OPA365 on slew), and a THS4521 FDA on 3.3 V
  (gain 0.909, SE→diff, VOCM from ADS5231 CM). Its 3.3 V rail keeps outputs inside the ADC abs-max range.
  ±10 V maps to ±0.904 V (89.5 % FS).
- **AAF:** Rf·Cf (1 k·22 p) and 2×49.9 Ω·220 p give 2 real poles at 7.2 MHz → −3 dB ≈ 4.6 MHz (F8 ✔).
- **±2.5 V = LM27762** (one IC, both rails LDO-regulated, 2 MHz fixed). TPS60403 + 2 LDOs lost on part count.
- **Power tree all-linear** (no in-band switchers): U3 TLV1117LV33 (SOT-223), U6 TPS7A2033 (VA_3V3),
  U4 AP2112K-1.2, U5 TLV75518. **AMS1117 is rejected**: its 1.1 V dropout fails the 4.4 V VBUS corner.
  Budget: 364 mA worst / 261 mA typ vs 450 mA HARD.
- **ADS5231 VDRV is fed from VA_3V3 via FB5, not VD_3V3.** The datasheet abs-max limits |AVDD − VDRV| to ≤ 0.3 V;
  one regulator makes the pins track.
- **Sample clock:** a 20 MHz 3.3 V CMOS XO drives the ADC directly (R57), with a second series-R branch (R58) to FPGA
  GCLKT_4 (pin 35). It never goes through the FPGA PLL (F12). X1 jitter must be ≤ 5 ps rms (budget ≈ 23 ps).
- **USB-C sink:** CC 5.1 kΩ ×2, USBLC6-2SC6 + SMF5.0A on VBUS, and an SY6280AAC current-limit/soft-start switch
  (≤ 10 µF ahead of it, P5).
- **Single GND net.** Buses: `ADC_DA`(12), `ADC_DB`(12), `FT_D`(8) expand to `ADC_DA0…11` etc.
- **9 blocks → modular mode.** `analog_front_end` holds both channels (fixed refs; the coder should build them with
  one helper called twice, not duplicated code).

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `architecture/ic_selection.md` | 2–5 candidates per block, winner, and loser reason, with stock/price | before sourcing any IC |
| `architecture/skeleton_bom.md` | every ref: function, MPN, package, qty, CP/PKG/SUB tag | sourcing: the row list to extend |
| `architecture/net_plan.md` | every net and its refs, component values, **FPGA pin map (§8)** | always, before writing code |
| `architecture/block_diagram.md` | mermaid block diagram, data rates, clock domains | orientation |
| `architecture/design_risks.md` | power budget, thermal, analog, timing, EMI, layout, sourcing risks | before substituting anything |

## Next phase must
1. **part-sourcer:** treat these as **critical path; do not substitute without escalating**: U12 ADS5231IPAGT,
   U15 GW1NR-LV9QN88PC6/I5 (the pin map binds to QN88P), U13 FT232HL-REEL, U9/U11 THS4521IDGKR, U7 LM27762DSSR.
2. **Packages fixed:** U3 SOT-223 (0.42 W); R10/R11/R20/R21 1206 with ≥ 200 V rating; C30/C40 C0G ≥ 100 V;
   VC1/VC2 trimmer 2–6 pF ≥ 100 V (STC3MA06-T1 C22468120); U15 QFN-88P.
3. **Spec-bound but substitutable:** X1 = 20.000 MHz 3.3 V CMOS XO with ≤ 5 ps rms jitter (confirm on the
   datasheet; the SCTF listing gives none). U8/U10 per `ic_selection.md` §4 limits. R12/R22 and Rg/Rf
   (R14–R17, R24–R27): 0.1 % preferred, ≤ 0.5 % acceptable.
4. **Vetted second sources:** SY6280AAC ↔ TPS2553DBVR; TPS7A2033 ↔ LP5907MFX-3.3; AP2112K-1.2 ↔ TLV75512;
   USBLC6-2SC6 ↔ TPD2E2U06; BAV199 ↔ BAV99; SMF5.0A ↔ SD05. SN74LV4T125 → SN74LVC2T45 ×2 needs an architect re-plan.
5. **Freely substitutable:** J1 (any 16P USB2 Type-C), J2/J3 (any PCB BNC), all ferrites, jellybean R/C, LEDs,
   headers, Y1 (12 MHz ±30 ppm; set C65/C66 to its CL), RN1–RN7 (4×33 Ω arrays), U14 (93LC56B any package).
6. Check **lifecycle (EOL/NRND)** for ADS5231, GW1NR-9, FT232H, and OPA354 via DigiKey/Mouser; stock-check has no
   lifecycle data. Quantity: buy ADS5231 and GW1NR for all 10 boards at once (stock 160–235 / 182).
7. Report KiCad-symbol status for every active part. These are known missing: ADS5231, GW1NR-9, OPA354, TPS7A2033,
   SY6280AAC. The BAV199 → `Diode:BAV19` match is **wrong** (single diode).
8. Keep every ref designator from § Parts by block unchanged; extend rows with MPN/LCSC/footprint only.

## Carried forward
- **Streaming (SOFT F13), resolved:** best effort. 30 MB/s packed vs the FT232H's 40 MB/s ceiling, with an 8 MB
  PSRAM FIFO. It works on hosts that sustain ≥ 32 MB/s bulk-in and is not guaranteed. Block capture (HARD): 16 k/ch
  in BSRAM, ≥ 2 M/ch in PSRAM.
- **Front-end supply topology, resolved:** ±2.5 V for the buffers only; the FDA and ADC run single-supply 3.3 V.
- **[DRIVER] numbers:** all accepted, with one **SOFT deviation**. F10 uncalibrated gain ≤ 2 % holds typically
  (±1 %) but not worst-case: ADS5231 reference error is ±3.5 % max. Per-board software calibration closes it,
  and 89.5 % FS headroom prevents clipping.
- **Pre-enumeration 100 mA:** not enforced (≈ 260 mA from power-on), which is the accepted risk from 01.
- **Gateware obligations (out of scope, but the schematic assumes them):** 2:1 half-band decimation;
  bank-3 IOs set to LVCMOS18; JTAG pins kept as JTAG; ADS5231 serial writes optional; FT245 sync-FIFO master;
  PSRAM controller (Gowin IP).
- **For the datasheet phase [VERIFY]:** GW1NR-9 MODE0/MODE1 = 4.7 k to GND gives auto-boot (UG290); TCK pull-down;
  BAV199 pinout; LM27762 FB resistors for ±2.50 V; SY6280 ISET for ≈ 0.8 A; FT232H decoupling/VPHY LC per
  DS_FT232H §6; THS4521 DGK pinout; the X1 jitter figure.
- **Sourcing-constraining risks** (`design_risks.md` §8): ADS5231 and GW1NR-9 are single-source (H); about 25 Extended parts.

## Do not redo
- Upstream: BNC, 1 MΩ input, USB 2.0 HS, bus power, 2 ch / 10 MSPS / 12 b, blank slate.
- ADC part and 20 MSPS/PLL-on mode; FPGA part and the bank/pin map in `net_plan.md` §8; FT232H sync FIFO;
  front-end topology and scaling (906k/100k, gain 0.909, 89.5 % FS); ±2.5 V via LM27762; all-linear power tree;
  VDRV from VA_3V3; net names and ref designators.

## Block manifest
| block_id | block_name | function_signature | interface_nets |
|---|---|---|---|
| `usb_power_in` | USB-C entry, ESD, load switch | `usb_power_in(vbus_sw, usb_dp, usb_dm, gnd)` | `VBUS_SW, USB_DP, USB_DM, GND` |
| `power_rails` | LDO rails 3V3D/1V8/1V2/3V3A | `power_rails(vbus_sw, vd_3v3, vd_1v8, vd_1v2, va_3v3, gnd)` | `VBUS_SW, VD_3V3, VD_1V8, VD_1V2, VA_3V3, GND` |
| `bipolar_supply` | ±2.5 V front-end supply | `bipolar_supply(vbus_sw, va_p2v5, va_n2v5, gnd)` | `VBUS_SW, VA_P2V5, VA_N2V5, GND` |
| `analog_front_end` | 2-ch BNC attenuator/buffer/driver | `analog_front_end(ain_a_p, ain_a_n, ain_b_p, ain_b_n, adc_vcm, va_3v3, va_p2v5, va_n2v5, gnd)` | `AIN_A_P, AIN_A_N, AIN_B_P, AIN_B_N, ADC_VCM, VA_3V3, VA_P2V5, VA_N2V5, GND` |
| `adc` | ADS5231 dual ADC | `adc(ain_a_p, ain_a_n, ain_b_p, ain_b_n, adc_vcm, adc_clk, adc_da, adc_db, adc_ovra, adc_ovrb, adc_dva, adc_sel, adc_sen, adc_sclk, adc_sdata, va_3v3, gnd)` | `AIN_A_P, AIN_A_N, AIN_B_P, AIN_B_N, ADC_VCM, ADC_CLK, ADC_DA0…ADC_DA11, ADC_DB0…ADC_DB11, ADC_OVRA, ADC_OVRB, ADC_DVA, ADC_SEL, ADC_SEN, ADC_SCLK, ADC_SDATA, VA_3V3, GND` |
| `sample_clock` | 20 MHz sample clock | `sample_clock(adc_clk, adc_clk_fpga, va_3v3, gnd)` | `ADC_CLK, ADC_CLK_FPGA, VA_3V3, GND` |
| `usb_bridge` | FT232H USB HS bridge | `usb_bridge(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_siwu_n, ft_clkout, vd_3v3, gnd)` | `USB_DP, USB_DM, FT_D0…FT_D7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N, FT_SIWU_N, FT_CLKOUT, VD_3V3, GND` |
| `fpga_core` | GW1NR-9 FPGA, config, JTAG | `fpga_core(adc_da, adc_db, adc_ovra, adc_ovrb, adc_dva, adc_sel, adc_sen, adc_sclk, adc_sdata, adc_clk_fpga, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_siwu_n, ft_clkout, led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8, trig_in_1v8, vd_3v3, vd_1v8, vd_1v2, gnd)` | `ADC_DA0…ADC_DA11, ADC_DB0…ADC_DB11, ADC_OVRA, ADC_OVRB, ADC_DVA, ADC_SEL, ADC_SEN, ADC_SCLK, ADC_SDATA, ADC_CLK_FPGA, FT_D0…FT_D7, FT_RXF_N, FT_TXE_N, FT_RD_N, FT_WR_N, FT_OE_N, FT_SIWU_N, FT_CLKOUT, LED_STAT_1V8, LED_ACT_1V8, TRIG_OUT_1V8, GPIO_OUT_1V8, TRIG_IN_1V8, VD_3V3, VD_1V8, VD_1V2, GND` |
| `io_expansion` | LEDs, ext trigger, level translation | `io_expansion(led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8, trig_in_1v8, vd_3v3, vd_1v8, gnd)` | `LED_STAT_1V8, LED_ACT_1V8, TRIG_OUT_1V8, GPIO_OUT_1V8, TRIG_IN_1V8, VD_3V3, VD_1V8, GND` |

## Parts by block
| block_id | refs |
|---|---|
| `usb_power_in` | J1, U1, U2, D1, FB1, R1, R2, R3, R4, C1, C2, C3, C4 |
| `power_rails` | U3, U4, U5, U6, LED1, R5, C5–C13, TP1–TP6 |
| `bipolar_supply` | U7, R6–R9, C14–C21, FB2, FB3, FB4, TP7, TP8 |
| `analog_front_end` | J2, J3, U8, U9, U10, U11, D2, D3, VC1, VC2, R10–R29, C30–C38, C40–C48 |
| `adc` | U12, R50–R56, RN1–RN7, C50–C62, FB5, FB6 |
| `sample_clock` | X1, R57, R58, C63, C64, FB7, TP9 |
| `usb_bridge` | U13, U14, Y1, R60–R67, C65–C79, FB8 |
| `fpga_core` | U15, J4, R70–R74, C80–C95, TP10 |
| `io_expansion` | U16, U17, LED2, LED3, R80–R85, C96, C97, J5 |

## Receipt
Architecture complete, revision 1. 9 blocks (modular), 17 ICs (U1–U17) + 1 XO; 10 test points.
Key parts: ADS5231 (20 MSPS, 2:1 decimation), GW1NR-LV9QN88P, FT232HL, OPA354 + THS4521, LM27762, all-LDO power.
Budget 364 mA worst / 450 mA; BOM ≈ $86/board. Unresolved risks: 2 H (single-source ADC, FPGA), 10 M.
One SOFT deviation (F10 worst-case gain, calibrated in software). No HARD constraint escalated.
