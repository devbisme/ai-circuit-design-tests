---
phase: 05_blocks/fpga_core
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T00:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — fpga_core

## Decisions
- Final signature, **unchanged** from the work order:
  `fpga_core(adc_da, adc_db, adc_ovra, adc_ovrb, adc_dva, adc_sel, adc_sen, adc_sclk, adc_sdata, adc_clk_fpga, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_siwu_n, ft_clkout, led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8, trig_in_1v8, vd_3v3, vd_1v8, vd_1v2, gnd)`
- `adc_da`, `adc_db` must be 12-wide buses and `ft_d` an 8-wide bus (indexed `[0]..[n-1]`, bit 0 = LSB).
- The U15 pin map follows `architecture/net_plan.md` §8 exactly. The driver ruling on UG119E Fig. 3-8 applies: pins 48–63/68–77 are bank 1, 3–11/13–16/79–88 are bank 3. U15 pins are connected by **number**, not name.
- Directions, from the FPGA's side. **Inputs** (this block only senses them): adc_da, adc_db, adc_ovra, adc_ovrb, adc_clk_fpga (GCLKT_4, pin 35), ft_rxf_n, ft_txe_n, ft_clkout (GCLKT_3, pin 52), trig_in_1v8.
  **Outputs** (FPGA drives them): adc_dva, adc_sel, adc_sen, adc_sclk, adc_sdata, ft_rd_n, ft_wr_n, ft_oe_n, ft_siwu_n, led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8.
  **Bidirectional:** ft_d. The symbol types every I/O as `bidirectional`, so ERC sees them all as BIDIR.
- Power **consumed only**: vd_1v2 → VCC 1/22/45/66. vd_3v3 → VCCX/VCCIO0 64/67/78, VCCIO1 58 and VCCIO2 23/44. vd_1v8 → VCCIO3 12 and J4 VREF. gnd → VSS 2/21/24/43/46/65 and **EP 89**.
- Block-local nets: JTAG_TMS, JTAG_TCK, JTAG_TDI, JTAG_TDO, FPGA_RECONFIG_N, FPGA_JTAGSEL_N, FPGA_MODE0, FPGA_MODE1, SPARE_B1.
- Straps: R70 and R71 (4.7k) pull MODE0/MODE1 down, R73 (4.7k) pulls TCK down, R72 (10k) pulls RECONFIG_N up to 1V8 and R74 (10k) pulls JTAGSEL_N up to 1V8.
- J4 (1×7): 1 VD_1V8, 2 TMS, 3 TCK, 4 TDO, 5 TDI, 6 RECONFIG_N, 7 GND. TP10 is on SPARE_B1 (U15.77).
- Refs are the work-order refs only. Decoupling caps use them (C80–C95), not the `C_DECOUP_U15` naming, because work-order refs are mandatory.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/fpga_core.py` | `@SubCircuit fpga_core` — U15, J4, R70–R74, C80–C95, TP10 | Assembling / reviewing this block |

## Next phase must
1. skidl-assembler: call it by keyword, exactly like this:
   `fpga_core(adc_da=ADC_DA, adc_db=ADC_DB, adc_ovra=ADC_OVRA, adc_ovrb=ADC_OVRB, adc_dva=ADC_DVA, adc_sel=ADC_SEL, adc_sen=ADC_SEN, adc_sclk=ADC_SCLK, adc_sdata=ADC_SDATA, adc_clk_fpga=ADC_CLK_FPGA, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_oe_n=FT_OE_N, ft_siwu_n=FT_SIWU_N, ft_clkout=FT_CLKOUT, led_stat_1v8=LED_STAT_1V8, led_act_1v8=LED_ACT_1V8, trig_out_1v8=TRIG_OUT_1V8, gpio_out_1v8=GPIO_OUT_1V8, trig_in_1v8=TRIG_IN_1V8, vd_3v3=VD_3V3, vd_1v8=VD_1V8, vd_1v2=VD_1V2, gnd=GND, tag='fpga_core')`
   with `ADC_DA = Bus('ADC_DA', 12)`, `ADC_DB = Bus('ADC_DB', 12)` and `FT_D = Bus('FT_D', 8)`.
2. Set `.drive = POWER` at top level on VD_3V3, VD_1V8, VD_1V2 and GND, unless power_rails already drives them. This block has only `power_in` pins on them.
3. Run with `symbols/` on `KICAD9_SYMBOL_DIR`. U15 comes from `Part('dual_adc_usb', 'GW1NR-LV9QN88PC6/I5')`.

## Carried forward
- 10 U15 pins are marked `NC` intentionally, per the net plan: 3, 10 (DONE), 11 (GCLKT_6), 13, 14, 15, 16, 84, 85, 86.
- Open, not acted on: `DONE` (pin 10) is left NC per the plan. Some Gowin reference designs pull DONE and READY up. Doing so adds a part and needs a ref, which the architect would have to assign.
- MODE0/MODE1 pull-downs (000 = auto-boot) and the TCK pull-down are still marked `[VERIFY UG290]` in the net plan. I did not re-verify them.
- VCCX/VCCIO0 goes to VD_3V3, per the plan. VCCX has a 2.375 V minimum, so those shared pins cannot be 1.8 V anyway.
- FT_D0–D7 sit on the MSPI dual-purpose pins 53–62. They are harmless in auto-boot mode, but if the boot mode ever changes to MSPI they would conflict with the FT232H.
- The assembler supplies no extra decoupling. All 16 FPGA decoupling caps are in this block.

## Do not redo
- The U15 pin map and bank assignment (driver ruling + net_plan §8).
- The U15 footprint `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm`. Its pad 89 is the EP and ties to GND.

## Receipt
- Block `fpga_core`: 24 parts (U15, J4, R70–R74, C80–C95, TP10).
- 65 nets touched: 56 interface bits (32 bus + 24 scalar) and 9 local.
- py_compile OK. Footprints valid (3/3 via validate-footprints.py).
- Test instantiation: every U15 pin except the 10 intentional NC pins is connected, and no passive pin floats.
- Signature changed: **no**.
