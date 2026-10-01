---
phase: 05_blocks/fpga
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-10-01T04:00:00Z
status: complete
next_phase: 05_coding
---

# Block handoff - fpga

## Decisions
- Final signature (unchanged): `fpga(fpga_clk40, adc_da, adc_db, adc_sel, adc_msbi_sen, adc_oea_sclk, adc_stpd_sdata, adc_oeb, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_clkout, ft_oe_n, v1v2, v1v8, v3v3d, gnd)`.
- adc_da, adc_db: Bus width 12 (index 0 = LSB); ft_d: Bus width 8.
- U9 `Part('dual_adc_usb','GW1NR-LV9QN88PC6')` wired **by pin number** per net_plan.md rev 2 U9 pin map verbatim (bank 2: DB1-DB11, DA0-DA11; bank 1: DB0 48, ctrl 49-51/53/54, FT 52/55-57/68-77, LEDs 59/60, TRIG 61/62, FPGA_CLK40 63; bank 3: 4-9, 87, 88).
- Power: VCC 1,22,45,66 -> v1v2; VCCX/VCCO0 64,67,78 + VCCO1 58 + VCCO2 23,44 -> v3v3d; VCCO3 12 -> v1v8; VSS x6 + EP 89 -> gnd.
- Decoupling in block: C80-C83 100 nF + C84 10 uF (+1V2); C85-C90 100 nF + C92 10 uF (+3V3D); C91 100 nF + C93 10 uF (+1V8). No VCC ferrite.
- Straps: R80 4k7 RECONFIG_N->+1V8, R85 4k7 JTAGSEL_N->+1V8, R81 4k7 TCK->GND, R83/R84 1k MODE0/MODE1->GND (autoboot).
- J4 1x6: 1 +1V8 (VREF), 2 TCK, 3 TMS, 4 TDI, 5 TDO, 6 GND.
- LEDs: pin59 -> R86 1k -> D80 A, pin60 -> R87 1k -> D81 A; cathodes GND.
- J5 1x3: 1 TRIG_IN_EXT -> R88 100R -> pin 61; pin 62 -> R89 100R -> 2 TRIG_OUT_EXT; 3 GND.
- Direction: drives adc_sel, adc_msbi_sen, adc_oea_sclk, adc_stpd_sdata, adc_oeb, ft_rd_n, ft_wr_n, ft_oe_n; senses adc_da, adc_db, ft_rxf_n, ft_txe_n, ft_clkout, fpga_clk40; ft_d bidirectional. All U9 I/O pins are BIDIRECTIONAL in the symbol.
- Internal nets: LED0/1, LED0_A/LED1_A, TRIG_IN/OUT, TRIG_IN_EXT/OUT_EXT, FPGA_JTAGSEL_N, FPGA_RECONFIG_N, FPGA_MODE0/1, JTAG_TCK/TMS/TDI/TDO.

## Next phase must
- `from .fpga import fpga`, then:
  `fpga(fpga_clk40=FPGA_CLK40, adc_da=ADC_DA, adc_db=ADC_DB, adc_sel=ADC_SEL, adc_msbi_sen=ADC_MSBI_SEN, adc_oea_sclk=ADC_OEA_SCLK, adc_stpd_sdata=ADC_STPD_SDATA, adc_oeb=ADC_OEB, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_clkout=FT_CLKOUT, ft_oe_n=FT_OE_N, v1v2=V1V2, v1v8=V1V8, v3v3d=V3V3D, gnd=GND, tag='fpga')`
  with `ADC_DA=Bus('ADC_DA',12)`, `ADC_DB=Bus('ADC_DB',12)`, `FT_D=Bus('FT_D',8)`.
- `lib_search_paths[KICAD]` must include `<project>/symbols`.
- `.drive = POWER` on +1V2, +1V8, +3V3D, GND at top level if regulator blocks do not already drive them (this block only consumes).

## Carried forward
- U9 pins 3, 10, 11, 13-16, 79-86 (unused bank-3 LVCMOS18 user I/O) are `NC` intentionally.
- Assumptions (unverified keystone facts, not facts): K3 PSRAM IP >=40 MB/s (raw 664 MB/s); K5 VCC dynamic <=150 mA; K10 +1V8 load <=100 mA; EP (pin 89) = GND.
- Gateware: pins 53-62 are dual-purpose config pins; enable as regular I/O in Gowin settings. Bus bit order is per pin map; layout may permute data bits within a bank only.
- Smoke-test ERC in isolation: 0 errors, 44 single-pin warnings (all interface nets, resolved at assembly).
- U9 footprint is generic ArtInChip QFN-88 EP6.74 (sourcing flag: verify vs Gowin QN88P drawing at layout).

## Receipt
- block fpga: 28 parts (U9, 11 R, 2 D, 2 J, 14 C), 65 nets in smoke test.
- py_compile OK; smoke ERC 0 errors. Footprints from sourced BOM. Signature changed: no.
