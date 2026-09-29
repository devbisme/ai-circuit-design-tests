---
phase: 05_blocks/fpga_core
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-20T15:20:00Z
status: complete
revision: 1
next_phase: 05_assembly
---

# Phase 5 handoff — block `fpga_core`

## Decisions

1. **Signature unchanged from the work order** — no parameter was renamed:
   `fpga_core(adc_d1, adc_d2, adc_oe_n, adc_pdwn, fpga_clk, fifo_d, fifo_rxf_n, fifo_txe_n,
   fifo_rd_n, fifo_wr_n, fifo_oe_n, fifo_siwu, fifo_clk, v3v3_d, v1v2_d, gnd)`
2. **Direction per net** — driven by U6: `ADC_OE_N`, `ADC_PDWN`, `FIFO_RD_N`, `FIFO_WR_N`,
   `FIFO_OE_N`, `FIFO_SIWU`. Sensed only: `FPGA_CLK`, `FIFO_CLK`, `FIFO_RXF_N`, `FIFO_TXE_N`,
   `ADC_D1[11:0]`, `ADC_D2[11:0]`. Bidirectional: `FIFO_D[7:0]`. Consumed only (this block
   never drives them): `+3V3_D`, `+1V2_D`, `GND`.
3. **MODE[1:0] = 0/0 for AUTOBOOT — CONFIRMED from a primary source**, closing handoff 04's
   carried-forward item. Gowin **UG284-1.9.7E** "GW1N/GW1NR series of FPGA Products Schematic
   Manual", **Table 6 "Mode Selection": `AUTO BOOT` = `MODE[2:0] = 000`**, "FPGA reads data
   from embedded Flash for configuration". Table 6 note [1]: unbonded MODE pins (MODE2 on
   QN88) are internally grounded or tied to the supply. Note [2]: JTAG configuration is
   independent of the MODE value, so a hard strap does not block programming. Table 5: MODE
   pins have **internal weak pull-ups**, so they must be actively held low.
4. **MODE0/MODE1 tied directly to GND, not through UG284's recommended 1 kΩ pull-down** —
   no ref designator was allocated for MODE straps (R13, R15–R18 all have other net-plan
   roles). Consequence: pins 87/88 can never be remuxed as GPIO and the mode cannot be
   overridden at the strap. Both are acceptable (Gowin's own guidance is to avoid using
   MODE0/1 and DONE as I/O), but it is a deliberate deviation.
5. **`FPGA_CLK` → pin 11 (IOL15A/GCLKT_6)**, a dedicated global-clock pin per handoff 04
   item 2. **`FIFO_CLK` → pin 52 (IOR17A/GCLKT_3)** — also GCLK-capable (Bank 1, FT232H side
   of the package) and chosen over 35/36 for layout; 35/36 are left spare.
6. **Pin 12 wired as VCCIO3** (Gowin UG119E Table 3-7, not the EasyEDA label) with its own
   dedicated 100 nF (C34). Handoff 04 decision 4 asked that pin 12 stay a *separate SKiDL
   net* from pins 64/67/78 — **not done, and cannot be**: this design has exactly one 3.3V
   digital rail and the signature exposes exactly one `v3v3_d`, so every bank supply lands on
   it. The intent is honoured structurally (pin 12 is treated as its own bank with its own
   local cap), not as a distinct net. Revisit only if a future revision splits bank voltages.
7. **R13 is NOT instantiated by this block.** Sourcing's block table lists R13 under
   `fpga_core`, but `architecture/net_plan.md` gives it one role only — the 2.2 kΩ pull-up on
   `EEDATA`, a net internal to `usb_bridge` (U7↔U8 Microwire). Placing it here would either
   duplicate the ref or strand it on a net this block cannot see. **See "Next phase must"
   item 3 — this is an open gap the assembler must close.**
8. **`RECONFIG_N` is not brought out to J4.** The net plan wants it on J4, but J4 is a 1×6
   header already fully consumed by programmer VREF + GND + the four JTAG signals. It gets
   its 4.7 kΩ pull-up (R15) and is reachable over JTAG. Change J4 to a 1×7 if a hardware
   reconfig pin is wanted.
9. **R15 = 4.7 kΩ, not the sourced "generic 10 kΩ"** — UG284 Figure 5 specifies 4.7 kΩ for
   RECONFIG_N/DONE/READY pull-ups, ±5% or better. Same jellybean 0603 part, value only.
10. **J4 pinout** (document it on the silkscreen): 1 = `+3V3_D`, 2 = `JTAG_TMS`,
    3 = `JTAG_TCK`, 4 = `JTAG_TDI`, 5 = `JTAG_TDO`, 6 = `GND`.
    **J5 pinout**: 1 = trigger in, 2 = `GND`.
11. **Trigger chain order**: `J5[1]` → `TRIG_RAW`; R17 (10 kΩ) from `TRIG_RAW` to GND;
    R16 (1 kΩ) from `TRIG_RAW` to `TRIG_IN` → U6 pin 74. Pull-down sits at the connector, not
    after the series R, so R16/R17 do not form a divider at the FPGA input.
12. **Decoupling (C23–C40, 18 caps, all used)**: 100 nF 0402 (CL05B104KO5NNNC) one per supply
    pin — C23–C26 on VCC 1/22/45/66, C28–C30 on 64/67/78, C31 on 58, C32/C33 on 23/44,
    C34 on 12; plus C38 (+1V2_D) and C39/C40 (+3V3_D) as distributed HF caps. 10 µF 0805
    (CL21A106KAYNNNE) bulk: C27 + C36 on `+1V2_D`, C35 + C37 on `+3V3_D`.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/fpga_core.py` | The block — `@SubCircuit fpga_core(...)` | Assembling the circuit |

## Next phase must

Addressed to **skidl-assembler**:

1. **Call it with keywords, exactly this:**
   ```python
   fpga_core(adc_d1=ADC_D1, adc_d2=ADC_D2, adc_oe_n=ADC_OE_N, adc_pdwn=ADC_PDWN,
             fpga_clk=FPGA_CLK, fifo_d=FIFO_D, fifo_rxf_n=FIFO_RXF_N,
             fifo_txe_n=FIFO_TXE_N, fifo_rd_n=FIFO_RD_N, fifo_wr_n=FIFO_WR_N,
             fifo_oe_n=FIFO_OE_N, fifo_siwu=FIFO_SIWU, fifo_clk=FIFO_CLK,
             v3v3_d=V3V3_D, v1v2_d=V1V2_D, gnd=GND)
   ```
   `adc_d1`/`adc_d2` must be `Bus(...,12)`, `fifo_d` must be `Bus(...,8)`.
2. **Set `.drive = POWER` at top level on `+3V3_D`, `+1V2_D` and `GND`** — this block only
   consumes all three and drives none of them.
3. **Place R13 (2.2 kΩ, `Device:R`, `Resistor_SMD:R_0603_1608Metric`) as the `EEDATA`
   pull-up to `+3V3_D` inside or alongside `usb_bridge`** — sourcing assigned the ref to
   `fpga_core` but the net plan's only role for it is in `usb_bridge`, whose ref list omits
   it. Without this, the 93C46's open-drain DO line has no pull-up. This is the one real
   cross-block gap from this block.
4. **`KICAD9_SYMBOL_DIR` must include the project `symbols/` directory** — U6 is
   `Part('dual_adc_usb', 'GW1NR-LV9QN88PC6-I5')`.
5. Expect ERC "unconnected/no-drive" notes on nothing from U6 — 20 unused pins are
   explicitly `NC` (verified: they land on SKiDL's `NCNet __NOCONNECT`, none floating).

### FPGA pin assignment (U6, GW1NR-LV9QN88PC6/I5, QN88)

| Signal | U6 pins (in bus order, LSB first) |
|---|---|
| `ADC_D1[0:11]` | 17, 18, 19, 20, 25, 26, 27, 28, 29, 30, 31, 32 (Bank 2) |
| `ADC_D2[0:11]` | 33, 34, 37, 38, 39, 40, 41, 42, 47 (Bank 2), 13, 14, 15 (Bank 3) |
| `ADC_OE_N` / `ADC_PDWN` | 16 / 3 |
| `FPGA_CLK` / `FIFO_CLK` | 11 (GCLKT_6) / 52 (GCLKT_3) |
| `FIFO_D[0:7]` | 79, 80, 81, 82, 83, 84, 85, 86 (Bank 0) |
| `FIFO_RXF_N`, `TXE_N`, `RD_N`, `WR_N`, `OE_N`, `SIWU` | 68, 69, 70, 71, 72, 73 |
| `TRIG_IN` / `LED_CAP` | 74 / 75 |
| JTAG TMS, TCK, TDI, TDO | 5, 6, 7, 8 |
| `RECONFIG_N` | 9 (R15 4.7 kΩ pull-up) |
| MODE1 / MODE0 → GND | 87 / 88 |
| `+1V2_D` (VCC) | 1, 22, 45, 66 |
| `+3V3_D` (VCCX/VCCIO0, VCCIO1, VCCIO2, VCCIO3) | 64, 67, 78, 58, 23, 44, 12 |
| `GND` (VSS + EP) | 2, 21, 24, 43, 46, 65, 89 |
| `NC` (20 pins) | 4, 10, 35, 36, 48, 49, 50, 51, 53–57, 59–63, 76, 77 |

## Carried forward

- **DONE (pin 10) left NC — recommend adding a 4.7 kΩ pull-up to `+3V3_D`** (Gowin UG284
  Figure 5 shows READY/RECONFIG_N/DONE each pulled up with 4.7 kΩ, plus an optional
  status LED). No ref designator was available in this block's allocation, so it was not
  placed. Board-bring-up nicety, not a functional requirement for AUTOBOOT — DONE has an
  internal weak behaviour and AUTOBOOT does not gate on an external pull-up. Decide before
  layout, since it is a single 0603 next to the package.
- **JTAGSEL_N (pin 4) left NC — correct and confirmed**: UG284 Table 7 gives it an internal
  weak pull-up, and "the JTAG configuration functions are always available if no JTAG pin
  multiplexing is set". Only needed if the JTAG pins are ever remuxed as GPIO.
- **No ESD protection on the JTAG header.** UG284 recommends an SP3003-04XTG array on the
  four JTAG lines. Not in the BOM; not added (no ref, no sourcing). Bench-only header, so
  the risk is accepted, but note it if J4 is ever cabled outside the enclosure.
- **No series termination on `TRIG_IN` beyond R16**, and no ESD diode on J5 — an externally
  cabled input. R16 (1 kΩ) plus the FPGA's internal clamps is the whole protection story.
- **EP size (6.74 × 6.74 mm) in the footprint still unverified** against Gowin's package
  outline drawing — inherited from handoff 04, unchanged, still owed before layout.
- **Decoupling placement is the layout step's job**: C23–C26 and C38 must sit hard against
  the four VCC pins on the same side as the core plane; C28–C34 each belong at their own
  bank pin, not pooled.
- **The trigger input's logic level is unspecified** — 3.3V CMOS assumed (Bank 0 VCCIO is
  3.3V). Feeding J5 from a 5V source needs a divider that does not exist on this board.

## Do not redo

- **The MODE[1:0] = 0/0 AUTOBOOT strap** — closed with a primary-source citation
  (UG284-1.9.7E Table 6), not common practice. Do not re-open.
- **The FPGA pin assignment table above.** It is arbitrary but committed: the FPGA is
  programmable, so any reshuffle costs nothing in silicon and everything in downstream
  rework (constraints file, layout, this handoff). Change it only for a routing reason.
- **Pin 12 = VCCIO3** and the UG119E power map generally — settled in handoff 04.
- **R15 = 4.7 kΩ** (UG284 Figure 5), not the sourced BOM's generic 10 kΩ.
- **JTAGSEL_N and DONE left NC** — reasoned above, both confirmed against UG284.

## Receipt

- Block `fpga_core` → `circuits/dual_adc_usb/fpga_core.py`, **signature unchanged**.
- 26 parts (U6, J4, J5, D5, R15–R18, C23–C40), 55 nets at instantiation; U6 89/89 pins
  accounted for — 69 connected, 20 explicit `NC`, 0 floating.
- `py_compile` OK; SKiDL instantiation smoke test OK; `validate-footprints.py` 7/7 valid,
  exit 0. ERC not run (assembler's job).
- R13 intentionally not placed — cross-block gap, flagged for the assembler (item 3).
- status: complete
