---
phase: 02_architecture
agent: circuit-architect
circuit: dual_adc_usb
written: 2026-09-09T00:00:00Z
status: complete
revision: 1
next_phase: 03_sourcing
---

# Phase 2 handoff — Architecture

Autonomous mode held: every open choice was decided here, with the rejected options and the
reason each lost recorded in `architecture/ic_selection.md`. Nothing was read from
`../dual-adc-usb-1`, `../dual-adc-usb-2`, or any other design in this tree.

**The `pcbparts` MCP was not connected.** Stock, price and tier figures below come from the
open JLCPCB parts mirror (`jlcsearch.tscircuit.com`) and LCSC/JLCPCB product pages, pulled
2026-09-09. They are why each part won — the part-sourcer must re-verify all of them.

## Decisions

1. **Digitizer: 2 × AD9235BCPZ-40** (LFCSP-32), parallel CMOS, both CLK pins driven from one
   SN74LVC2G34 die. Pin-strapped, so the netlist alone determines behaviour — no SPI state
   for firmware to get wrong. One 3.0 V analog supply, common mode AVDD/2 = 1.50 V.
   Same-footprint alternates: AD9235BCPZ-20, AD9235BCPZ-65. TSSOP-28 grades are **not** a
   footprint swap. Rejected: AD9629 (needs a 1.8 V analog rail and SPI-set output format for
   $10/board on a budget 45 % unused); AD9238 dual (7 in stock); AD9226 (475 mW each, blows P2).
2. **Capture engine: GW1NR-LV9QN88PC6/I5** — Gowin GW1N-9 with **64 Mbit PSRAM in package**.
   The PSRAM costs zero user I/O, which is the only reason a 71-pin package works here, and
   it is the F12a burst buffer: **2.80 Mpt/channel = 280 ms at 10 MSPS**. Embedded config
   Flash, so no config PROM. Rejected: FX2LP alone (4 kB FIFO, cannot repack 20 MS/s — fails
   requirements 10 and 11 together); GW1N-4 + external SDRAM (same cost, but 39 SDRAM pins
   push the total to 89 against 71 available); STM32H7 (≤1 MB SRAM ≈ 330 kpt/ch, plus a
   software-packing gamble, plus it still needs a ULPI PHY); FX3 (BGA-121 0.65 mm violates
   the hard X4 rule); iCE40UP5K (128 kB SPRAM = 4.2 ms burst).
   **The "P" suffix means PSRAM at 1.8 V** — this is where `+1V8` in the power tree comes from.
3. **USB: CY7C68013A-56LTXC in 8-bit slave FIFO mode.** The 8051 is not in the data path.
   8 bits × 48 MHz IFCLK = 48 MB/s against a 30 MB/s payload; 8-bit rather than 16-bit saves
   8 FPGA pins that the 1.8 V PSRAM bank may cost us (see R1). 0–70 °C grade matches X5.
4. **Front end per channel:** 909 k/90.9 k compensated ÷11 divider (1 MΩ ∥ ~18 pF at the
   BNC) → 1 kΩ + BAV199 clamp to the ±4.2 V rails → **AD8066ARZ-R7** unity buffer →
   AD8066 second amp as a Sallen-Key AAF section → **THS4551IRGTR** as a differential MFB
   section plus single-ended-to-differential conversion at gain 1.10. AAF is 4th-order
   Butterworth split across those two stages, fc ≈ 3.9 MHz.
   AD8066 won on slew rate: ±0.909 V at 4 MHz needs 22.8 V/µs, and OPA1656 (a third the
   price, 4877 in stock) has only 24 V/µs. OPA2810 was better on every axis — 35 in stock.
5. **Signal plan is exact, not approximate:** ±10 V ÷ 11 = ±0.909 V, × 1.10 = ±1.000 V per
   side = **2.0 Vpp differential**, which is precisely the AD9235's span with its internal
   1.0 V reference (SENSE → GND). Do not change the divider or the FDA gain independently.
6. **Bipolar rails: LM27762DSSR, ±4.2 V.** It satisfies P5 by construction — the LDO
   post-regulator is on the die for *both* polarities, so this block cannot be built with a
   switching rail accidentally exposed to the ADC. Its 2 MHz switching fundamental lands
   **above** the 10 Hz–1 MHz band P5 is measured in; do not substitute a slower converter.
   ±4.2 V rather than ±5/±6 V is a deliberate SOFT deviation from requirement 9 (LM27762 VIN
   max is 5.5 V and its positive rail is an LDO from VBUS) — the largest signal anywhere is
   ±0.909 V, so the headroom is never used. Recorded as risk R7.
7. **Power split for P3:** `+3V3_AON` (AP2112K LDO, always on) feeds only the FX2LP island —
   **~70 mA pre-enumeration**. Everything else (TLV62569 +3V3, TLV62568 +1V2, LP5907 +1V8,
   LM27762) is gated by `PWR_EN` from FX2LP PA0. **`PWR_EN` needs a 100 kΩ pulldown** —
   PORTA is high-Z after reset and a floating enable violates P3 on every power-up (R8).
8. **Sample clock: dedicated SiT1602 10.000 MHz XO + SN74LVC2G34 fanout**, ~2.5 ps rms total
   against a 20 ps bar. Rejected an FPGA-PLL clock: tens of ps p-p, on a die with 24 I/O
   switching at 10 MHz, to save $1.25. Both ADC clocks come from the same package, which is
   what guarantees F10 skew. Lower sample rates are done by decimation in fabric.
9. **One `GND` net in the netlist.** The analog/digital plane split and its single tie point
   under the ADCs is a layout instruction (R12). Do not add an `AGND` net.
10. **Not fitted, deliberately:** switchable input range (needs a $5.20 bipolar analog switch
    per channel; "range" is exposed as host-side scaling instead), shared external voltage
    reference (F8 already specifies host-side calibration), AC coupling, probe-ratio sensing,
    calibration DAC.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `architecture/net_plan.md` | Every net, type, connected refs; bus declarations; signal-level and filter values | Always — before writing any code |
| `architecture/ic_selection.md` | 2–5 candidates per block with live stock/price, the winner, and why each loser lost | Before substituting **any** part |
| `architecture/skeleton_bom.md` | function \| suggested MPN \| package \| qty \| notes, per-board | Sourcing, start here |
| `architecture/block_diagram.md` | Mermaid signal-flow and power-tree diagrams | To understand what talks to what |
| `architecture/design_risks.md` | Current budget, USB throughput arithmetic, jitter budget, 17-item risk register | Before sourcing (R2/R3), before coding (R8/R12), before layout (R10/R11/R14) |

## Block manifest

Nine blocks → **modular coding mode**. `function_signature` and `interface_nets` agree with
`architecture/net_plan.md` and are used verbatim by the block coders.

| block_id | block_name | function_signature | interface_nets |
|---|---|---|---|
| `usb_c_port` | USB-C receptacle, ESD, VBUS entry | `usb_c_port(vbus, gnd, usb_dp, usb_dm)` | `VBUS, GND, USB_DP, USB_DM` |
| `power_digital` | Digital rails +3V3_AON/+3V3/+1V2/+1V8 | `power_digital(vbus, gnd, pwr_en, v3v3_aon, v3v3, v1v2, v1v8)` | `VBUS, GND, PWR_EN, +3V3_AON, +3V3, +1V2, +1V8` |
| `power_analog` | ±4.2 V bipolar rails + AVDD 3.0 V | `power_analog(vbus, gnd, pwr_en, vpos, vneg, avdd)` | `VBUS, GND, PWR_EN, +4V2A, -4V2A, +3V0A` |
| `analog_frontend` | Attenuator, clamp, buffer, AAF, FDA | `analog_frontend(bnc_in, adc_p, adc_n, vcm, vpos, vneg, gnd)` | `CH1_IN, CH1_ADC_P, CH1_ADC_N, VCM, +4V2A, -4V2A, GND` |
| `adc_pair` | 2× AD9235, refs, VCM divider, DRVDD ferrite | `adc_pair(ch1_p, ch1_n, ch2_p, ch2_n, clk_adc1, clk_adc2, adc1_d, adc2_d, adc1_otr, adc2_otr, avdd, v3v3, vcm, gnd)` | `CH1_ADC_P, CH1_ADC_N, CH2_ADC_P, CH2_ADC_N, CLK_ADC1, CLK_ADC2, ADC1_D[11:0], ADC2_D[11:0], ADC1_OTR, ADC2_OTR, +3V0A, +3V3, VCM, GND` |
| `clock_gen` | 10 MHz XO + dual fanout buffer | `clock_gen(v3v3, gnd, clk_adc1, clk_adc2, clk_fpga)` | `+3V3, GND, CLK_ADC1, CLK_ADC2, CLK_FPGA` |
| `fpga_capture` | GW1NR-9, decoupling, JTAG header | `fpga_capture(v3v3, v1v2, v1v8, gnd, clk_fpga, adc1_d, adc2_d, adc1_otr, adc2_otr, fd, ifclk, slwr_n, slrd_n, sloe_n, fifoadr, flaga, flagb, flagc, pktend_n, fpga_rst_n, trig_io, led_cap_n)` | `+3V3, +1V2, +1V8, GND, CLK_FPGA, ADC1_D[11:0], ADC2_D[11:0], ADC1_OTR, ADC2_OTR, FD[7:0], IFCLK, SLWR_N, SLRD_N, SLOE_N, FIFOADR[1:0], FLAGA, FLAGB, FLAGC, PKTEND_N, FPGA_RST_N, TRIG_IO, LED_CAP_N` |
| `usb_controller` | CY7C68013A, 24 MHz crystal, EEPROM, reset | `usb_controller(v3v3_aon, gnd, usb_dp, usb_dm, fd, ifclk, slwr_n, slrd_n, sloe_n, fifoadr, flaga, flagb, flagc, pktend_n, pwr_en, fpga_rst_n)` | `+3V3_AON, GND, USB_DP, USB_DM, FD[7:0], IFCLK, SLWR_N, SLRD_N, SLOE_N, FIFOADR[1:0], FLAGA, FLAGB, FLAGC, PKTEND_N, PWR_EN, FPGA_RST_N` |
| `aux_io` | Ext trigger header + ESD, status LEDs | `aux_io(v3v3, v3v3_aon, gnd, trig_io, led_cap_n)` | `+3V3, +3V3_AON, GND, TRIG_IO, LED_CAP_N` |

**`analog_frontend` is one block file instantiated twice** by the assembler — once with
`CH1_IN / CH1_ADC_P / CH1_ADC_N`, once with `CH2_IN / CH2_ADC_P / CH2_ADC_N`. Write it once.
Do not create `analog_frontend_ch1` and `_ch2`; duplicated block code is exactly the failure
mode the net plan is written to avoid.

## Parts by block

Ref designators are indicative — SKiDL auto-numbers, and the `analog_frontend` refs appear
twice, once per instance. The sourcer extends this table with real MPNs.

| block_id | refs |
|---|---|
| `usb_c_port` | J1, R1, R2, D1, D2, FB1, C1–C3, TP1 |
| `power_digital` | U1, U2, U3, U4, L1, L2, R3–R8, C4–C20, TP2–TP5 |
| `power_analog` | U5, U6, R9–R12, FB2, FB3, C21–C33, TP6–TP9 |
| `analog_frontend` (×2 instances) | J2, U7, U8, R13–R27, C34–C47, CT1, D3 |
| `adc_pair` | U9, U10, R28–R31, FB4, C48–C70, TP10–TP13 |
| `clock_gen` | Y1, U11, R32–R34, C71, C72 |
| `fpga_capture` | U12, J3, R35, R36, C73–C90, TP14 |
| `usb_controller` | U13, U14, Y2, R37–R42, FB5, C91–C105, TP15 |
| `aux_io` | J4, D4, D5, D6, R43–R46, TP16–TP19 |

## Next phase must

Addressed to **part-sourcer**:

1. Re-verify every stock/price/tier figure in `architecture/ic_selection.md` — they were
   read from an open JLCPCB mirror, not from the `pcbparts` MCP, which was not connected.
   Warn if that MCP is still unavailable.
2. **Critical path, escalate rather than substitute:** `GW1NR-LV9QN88PC6/I5` (single-source,
   102 in stock — the lowest-stock keystone; vetted escalation part is
   `GW2AR-LV18QN88C8/I7`, 168 in stock, believed pin-compatible, verify) and
   `AD9235BCPZ-40` (170 in stock; same-footprint pool with the -20 and -65 grades is 202).
   Changing either changes the power tree or the whole front-end signal plan.
3. **Packages fixed and not substitutable:** GW1NR-9 QFN-88 (only variant stocked; note it is
   0.4 mm pitch — finer than the SOFT X4 preference, but QFN, so the HARD no-BGA-below-0.8 mm
   rule holds); AD9235 LFCSP-32 (TSSOP grades are a different footprint); THS4551 QFN-16-EP
   (the ADA4940-1ARZ second source is SOIC-8 — a layout change, not a BOM change);
   CY7C68013A QFN-56-EP (the SSOP-56 second source is a different footprint).
4. **Freely substitutable** on equivalent specs: all four regulators, the clock buffer, the
   EEPROM, the USB-C receptacle, the ESD array, the TVS, the BNC jacks, all passives.
   Constraints that must survive a substitution:
   - Bipolar rail converter: must have **integrated LDO post-regulation on both polarities**
     and switch at **≥2 MHz** (P5). Dropping either breaks the analog noise requirement.
   - Both bucks: must have an **EN pin** (P3) and a soft-start giving a monotonic ramp inside
     0.2–2 ms for +1V2 and 0.33–5.5 ms for +3V3 (Gowin ramp-rate limits, R6).
   - Op amps: **≥100 V/µs slew and ≥100 MHz GBW**; ±0.909 V at 4 MHz needs 22.8 V/µs bare.
   - FDA: **rail-to-rail output** and an adjustable VOCM pin.
   - XO: **≤10 ps rms integrated jitter**, 3.3 V LVCMOS, 10.000 MHz.
   - Crystal: 24.000 MHz, CL 12 pF, ±100 ppm — an FX2LP hard requirement.
5. **Voltage-rating trap:** the 909 kΩ attenuator top leg carries ~45 V continuously (F9).
   Source an 0805/1206 rated **≥100 V working**, or two 453 kΩ 0603 in series. Its power
   dissipation is 2.75 mW, so a purely-by-wattage pick will get this wrong (R14).
6. Attempt a **6–30 pF SMD trimmer capacitor** for the attenuator compensation. If it is not
   stocked, fall back to a fixed 150 pF C0G ±2 % and note it — **do not escalate for this**.
   It costs HF flatness, not the ±2 % DC accuracy F8 specifies (R5).
7. Filter and divider tolerances are load-bearing: ±0.1 % on the attenuator and FDA gain
   resistors, ±1 % on the Sallen-Key resistors, **±2 % C0G** on every filter capacitor. The
   AAF has only 2.7 dB of stopband margin at 10 MHz (R4).
8. No AEC-Q100/Q200 requirement anywhere — X6 sets no regulatory bar. Do not pay for it.
9. Everything in this design is JLCPCB **Extended** tier except the SMAJ5.0A (Preferred).
   That is expected: a 12-bit 10 MSPS front end has no Basic-tier parts. Flag it once, do not
   treat it as a failure.
10. Estimated BOM is **≈$104/board** against the $180 SOFT target (N3), 42 % under. The ADC
    pair and the FPGA are 64 % of it. There is no cost pressure — pick for stock and
    correctness, not price.

## Carried forward

**Requirement questions resolved here (from `01_requirements.md` `## Carried forward`):**

- **AC coupling** — remains not fitted, DC-only as specified. Reconfirmed: the front end is
  bipolar-railed and DC-coupled end to end; adding AC coupling later means a relay and a film
  capacitor per channel *ahead* of the attenuator, which would change the input capacitance
  and require recompensation. Not a drop-in retrofit; noted so nobody assumes it is.
- **Probe attenuation sensing** — not implemented, as specified. The BNC jack chosen
  (KH-BNC50-3511) has no ring contact, so this closes the option at the connector level, not
  just in firmware. Host must be told the probe ratio manually.
- **On-board calibration source** — considered and **not fitted**. A shared external 1.0 V
  reference (ADR510, $3.78) would have matched the two channels' gains in hardware; rejected
  because F8 already specifies a one-time host-side calibration, which corrects per-channel
  gain regardless. Both ADCs use their internal 1.0 V references (SENSE → GND). Risk R15.
- **Firmware out of scope, hardware must not preclude it** — honoured: CAT24C128 EEPROM
  fitted at I²C address 0xA2 (I9), 2×3 JTAG header fitted (I11), `FPGA_RST_N` from FX2LP PA3
  to RECONFIG_N so the host can force a reconfiguration. Risk R17.
- **Enclosure / BNC ground referencing** — both BNC shells tie to `GND`. Channels are not
  isolated and this architecture cannot be adapted to isolate them. Risk R16.
- **N1/N3/X1/X5 are driver assumptions** — none of them bind this design. Cost lands 42 %
  under target, the board fits ≤100 × 80 mm comfortably at 9 blocks, and every part is
  0–70 °C or wider.

**Constraints from `design_risks.md` that bind sourcing:**

- R2: GW1NR-9 is single-source at 102 units — the sourcing decision most likely to escalate.
- R3: AD9235BCPZ-40 has a 202-unit same-footprint pool; a different converter family is an
  architecture change, not a substitution.
- R5: the compensation trimmer may not be sourceable; the fallback is defined and does not
  need an escalation.
- R6: regulator soft-start times must land inside Gowin's ramp-rate window.
- R14: 909 kΩ needs ≥100 V working voltage.
- No AEC-Q100 requirement on any part, gate driver or otherwise.

**Still open, for the datasheet phase (03 → 04):**

- **R1 is the design's biggest unknown.** Obtain Gowin **UG803 (GW1NR-9 Pinout)** and
  determine which I/O bank the 1.8 V PSRAM occupies and how many 3.3 V-capable user I/O the
  QN88P actually leaves. The pin budget is ~49 signals + 4 JTAG against a probable 52. The
  mitigation ladder, in order: 8-bit FIFO (already taken), drop `ADC1_OTR`/`ADC2_OTR`, drop
  the trigger output direction, drop `LED_CAP_N`.
- Confirm AD8066 is free of output phase reversal when the clamp drives its input to +4.7 V
  on a +50 V overload (R9).
- Confirm TLV62568/TLV62569 soft-start ramps land in Gowin's window (R6).
- Confirm GW2AR-18 QN88 is genuinely pin-compatible with GW1NR-9 QN88 before relying on it
  as the escalation part (R2).

## Do not redo

- Everything under `## Do not redo` in `handoffs/01_requirements.md` still stands: channel
  count, ±10 V, 10 MSPS, 12 bits, USB 2.0 bus power, BNC + 1 MΩ ∥ ≤25 pF, no auxiliary power
  jack, no requirements interview, no reading of sibling design directories.
- The FPGA-between-ADC-and-USB topology. It is forced by requirements 10 and 11 together;
  every single-chip alternative was evaluated in `ic_selection.md` §2 and fails one or both.
- The exact ÷11 / ×1.10 signal plan. The attenuator ratio and the FDA gain are matched to the
  AD9235's 2 Vpp internal-reference span. Changing one without the other silently loses range
  or clips.
- The single `GND` net. Adding `AGND` produces a floating net at ERC and does not describe
  what the board needs.
- 8-bit slave FIFO. 16-bit buys nothing (48 MB/s already gives 60 % headroom over 30 MB/s)
  and costs 8 pins the FPGA may not have.
- The dedicated sample-clock oscillator. Taking the ADC clock from the FPGA PLL was
  considered and rejected on jitter for a $1.25 saving.
- ±4.2 V analog rails. The deviation from requirement 9's "e.g. ±5 V/±6 V" is deliberate,
  justified in R7, and the headroom is demonstrably never used.

## Receipt

- 9 blocks (modular coding mode); `analog_frontend` is one file instantiated twice.
- 17 active devices: 2 ADCs, 1 FPGA, 1 USB controller, 4 amplifiers, 6 power ICs, 1 XO,
  1 clock buffer, 1 EEPROM. Estimated BOM ≈ $104/board against a $180 target.
- Budgets recorded for downstream inheritance: 327 mA of 450 mA VBUS (27 % margin), ~70 mA
  pre-enumeration of 100 mA, 30.0 MB/s packed payload vs 35–43 MB/s practical USB 2.0 HS,
  2.80 Mpt/ch burst depth, 2.5 ps rms clock jitter against a 20 ps bar.
- 17 risks registered; **2 HIGH** — GW1NR-9 pin budget against the 1.8 V PSRAM bank (R1) and
  GW1NR-9 single-source at 102 units (R2). Neither blocks sourcing.
- All 6 requirement questions carried forward from phase 1 resolved and recorded; 4 new items
  raised for the datasheet phase.
- `pcbparts` MCP unavailable — all stock figures need re-verification in phase 3.
- Status: complete → `03_sourcing`. Revision 1.
