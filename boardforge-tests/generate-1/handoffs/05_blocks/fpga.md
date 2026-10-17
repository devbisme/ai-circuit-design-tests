---
phase: 05_blocks/fpga
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - fpga

## Decisions
1. Signature unchanged: `fpga(clk10_fpga, da, db, adc_dva, adc_ovra, adc_ovrb, adc_sel, adc_sen, adc_sclk, adc_sdata, sd_dq, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n, sd_we_n, sd_ldqm, sd_udqm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_clkout, v3v3, v1v2, gnd)`.
2. Buses (indexable, index 0 = LSB): `da`/`db` 12, `sd_dq` 16, `sd_a` 12, `sd_ba` 2, `ft_d` 8.
3. U1001 symbol `FPGA_Xilinx_Spartan6:XC6SLX4-TQG144`, value/MPN XC6SLX9-2TQG144C; wired by pin number, all 144 pins assigned exactly once (script-checked).
4. Bank plan: bank 3 = CLK10 (P15 GCLK21), ADC_DVA (P22 GCLK25), DA0-11 (P1,2,5-12,14,16), DB0-11 (P17,21,23,24,26,27,29,30,32-35). Bank 2 = FT_CLKOUT (P51 GCLK31), FT_D0-7 (P43-48,50,55), RXF/TXE/RD/WR/OE (P57,58,59,61,62), OVRA/OVRB (P40/41). Bank 0 = SD_DQ0-15 (P111,112,114-121,123,124,126,127,131,132), SD_CLK 133, CKE 134, CS 137, RAS 138, CAS 139, WE 140, LDQM 141, UDQM 142, BA0 143. Bank 1 = SD_A0-11 (P105,104,102-97,95-92), BA1 88, ADC SEL/SEN/SCLK/SDATA 87/85/84/83, LED_ARMED 82, LED_TRIG 81, TRIG_IN_F 80, TRIG_OUT_F 79. Gateware UCF must use these pins.
5. Direction: senses clk10_fpga, ft_clkout, da, db, adc_dva, adc_ovra/b, ft_rxf_n, ft_txe_n; drives adc_sel/sen/sclk/sdata, sd_a, sd_ba, sd_clk, sd_cke, sd_cs_n, sd_ras_n, sd_cas_n, sd_we_n, sd_ldqm, sd_udqm, ft_rd_n, ft_wr_n, ft_oe_n; bidirectional sd_dq, ft_d. Consumes v3v3, v1v2, gnd. (All FPGA pins are `bidirectional` in the symbol.)
6. Config: Master SPI (M1 P60 -> R1008 1k GND, M0 P69 -> R1009 1k +3V3), HSWAPEN P144 -> R1010 1k +3V3, PROGRAM_B R1004 4.7k, INIT_B R1005 4.7k, DONE R1006 330 pull-ups, SUSPEND P73 -> GND, CMPCS_B P72 NC. CCLK/MOSI/DIN/CSO_B -> U1002 CLK(6)/DI(5)/DO(2)/CS(1); R1001 4.7k CS pull-up, R1002/R1003 10k on /WP, /HOLD.
7. Trigger naming: J1002.1 = TRIG_IN (connector side, R1015 10k to GND) -> R1014 100R -> TRIG_IN_F (FPGA); FPGA TRIG_OUT_F -> R1016 100R -> TRIG_OUT = J1002.2; J1002.3 GND. LEDs: I/O -> R1012/R1013 1k -> D1002/D1003 anode, cathode GND (1k kept per BOM; ~0.2 mA, dim).

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/fpga.py` | @SubCircuit fpga, 45 parts |

## Next phase must
- Emit: `fpga(clk10_fpga=CLK10_FPGA, da=DA, db=DB, adc_dva=ADC_DVA, adc_ovra=ADC_OVRA, adc_ovrb=ADC_OVRB, adc_sel=ADC_SEL, adc_sen=ADC_SEN, adc_sclk=ADC_SCLK, adc_sdata=ADC_SDATA, sd_dq=SD_DQ, sd_a=SD_A, sd_ba=SD_BA, sd_clk=SD_CLK, sd_cke=SD_CKE, sd_cs_n=SD_CS_N, sd_ras_n=SD_RAS_N, sd_cas_n=SD_CAS_N, sd_we_n=SD_WE_N, sd_ldqm=SD_LDQM, sd_udqm=SD_UDQM, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_oe_n=FT_OE_N, ft_clkout=FT_CLKOUT, v3v3=P3V3, v1v2=P1V2, gnd=GND, tag='fpga')`
  with `SD_DQ = Bus('SD_DQ', 16)`, `SD_A = Bus('SD_A', 12)`, `SD_BA = Bus('SD_BA', 2)`, `FT_D = Bus('FT_D', 8)`, `DA/DB = Bus(..., 12)`, `P1V2 = Net('+1V2')`.
- `+3V3`, `+1V2`, `GND` are only consumed here: `.drive = POWER` at top level if the power blocks do not drive them.

## Carried forward
- Intentional NC: U1001 P72 (CMPCS_B), spare user I/O P56, P66, P67, P74, P75, P78 (6 spare, matches net-plan budget).
- Cap refs used match sourcing exactly: C1001-C1005 VCCINT (+1V2), C1006-C1010 VCCAUX, C1011-C1021 VCCO (21 supply pins), C1022 U1002 VCC, C1023 4.7u on +1V2, C1024/C1025 4.7u on +3V3. No CSV reconciliation needed.
- All U1001/U1002 decoupling is in-block; assembler provides none.
- FT_RD_N/WR_N/OE_N pull-ups are in usb_fifo; SD_CKE pull-down / SD_CS_N pull-up and SD_CLK 22R series in sdram; ADC control pull-downs in adc.
- Local nets: CFG_PROG_N, CFG_INIT_N, CFG_DONE, CFG_M0, CFG_M1, CFG_HSWAPEN, CFG_CCLK, CFG_MOSI, CFG_DIN, CFG_CS_N, FL_WP_N, FL_HOLD_N, JTAG_TCK/TDO/TDI/TMS, LED_ARMED(_A), LED_TRIG(_A), TRIG_IN, TRIG_IN_F, TRIG_OUT, TRIG_OUT_F.

## Do not redo
- MPNs/footprints/symbols verbatim from `sourcing/sourced_bom.csv`; pin map checked against the KiCad symbol pin table (144/144).

## Receipt
fpga: 45 parts (U1001, U1002, J1001, J1002, D1002, D1003, 14 R, 25 C), 31 interface args, 24 local nets; py_compile OK; footprints from CSV verbatim; signature changed: no.
