---
phase: 05_blocks/fpga
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-26T13:40:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — fpga

## Decisions
- Final signature (unchanged): `fpga(fpga_clk, da, db, adc_dva, adc_stpd, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_siwu_n, ft_clkout, ft_oe_n, v3v3d, v1v2, v1v8, gnd)`.
- `da`/`db` are 12-net buses (index 0 = LSB), and `ft_d` is an 8-net bus. U9 pins are referenced by number only.
- All U9 I/O pins are BIDIRECTIONAL in the symbol. Logically:
  - **Senses:** fpga_clk, da, db, adc_dva, ft_rxf_n, ft_txe_n, ft_clkout.
  - **Drives:** adc_stpd, ft_rd_n, ft_wr_n, ft_siwu_n, ft_oe_n.
  - **Bidirectional:** ft_d.
  - **Consumes:** v1v2, v3v3d, v1v8, gnd.
- Clocks: FPGA_CLK is on pin 35 (GCLKT_4, bank 2). **FT_CLKOUT is on pin 52 (GCLKT_3, bank 1, 3.3 V).**
- The 48 3.3 V I/O (banks 1+2) are **all used**. The net plan's "44" was a miscount: the listed signals total 48. There is no spare 3.3 V pin left.
- Bank 3 (1.8 V) carries only JTAG 5–8, RECONFIG_N 9 and MODE1/0 87/88.
- Full pin table: `circuits/dual_adc_usb/fpga_pinmap.md`.
- Local nets: FPGA_MODE0/1, FPGA_RECONFIG_N, JTAG_TCK/TMS/TDI/TDO, LED_ACT(_A), LED_TRIG(_A), TRIG_IN(_H), TRIG_OUT(_H), GPIO1, GPIO2.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/fpga.py` | the block @SubCircuit; the pin map is in module constants | Assembly |
| `circuits/dual_adc_usb/fpga_pinmap.md` | pin → net → direction table and J4 pinout | Writing the HDL .cst file |

## Next phase must
1. skidl-assembler: emit this call:

   `fpga(fpga_clk=FPGA_CLK, da=DA, db=DB, adc_dva=ADC_DVA, adc_stpd=ADC_STPD, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_siwu_n=FT_SIWU_N, ft_clkout=FT_CLKOUT, ft_oe_n=FT_OE_N, v3v3d=V3V3D, v1v2=V1V2, v1v8=V1V8, gnd=GND, tag='fpga')`

   Use `FT_D = Bus('FT_D', 8)` and the same `DA`/`DB` buses passed to `adc`.
2. V1V2, V3V3D, V1V8 and GND must be driven, either by power_digital or with `.drive = POWER` at top. U9 supply pins are power-in.
3. Trial ERC (block alone, rails driven): 0 errors. The 42 warnings are all single-pin interface nets whose other ends live in adc, clock and usb_bridge.
4. HDL: in Gowin IDE, set "SSPI/MSPI as regular IO". Pins 53–62 are dual-purpose config pins.

## Carried forward
- **Intentional NC:** U9 bank-3 I/O 3, 4 (JTAGSEL_N, internal pull-up), 10, 11, 13–16 and 79–86. Also J4 pins 7 and 8.
- DONE/READY are unbonded, so they are not wired.
- **Assumption (keystone, unverified):**
  - PSRAM sits on bank 3, so VCCIO3 (12) = V1V8.
  - MODE2 is unbonded and reads 0, so R18/R19 1 k pull-downs give AUTOBOOT.
  - Both come from the Tang Nano 9K reference design.
- **Assumption:** the J4 layout follows the Altera USB-Blaster 10-pin pattern (1 TCK, 2 GND, 3 TDO, 4 VREF, 5 TMS, 6 RECONFIG_N, 9 TDI, 10 GND). This is **not verified against the Gowin cable**, and the architect/driver should confirm it. The JTAG header runs at 1.8 V (VREF = V1V8), so the programmer must support 1.8 V.
- R20 is 10 k per the BOM. UG284 shows 4.7 k, but either works alongside the internal pull-up.
- All decoupling is in-block:
  - C33–C36 0.1 µF on V1V2, C37–C42 0.1 µF on V3V3D, C43 0.1 µF on V1V8.
  - Bulk: C44 10 µF (V1V2), C45 10 µF (V3V3D), C46 4.7 µF (V1V8).
- The ADC_STPD pull-down (R15) lives in the adc block.
- Dynamic power is unknown (static only), which is a note, not a wiring issue.
- **BOM cell corrections:**
  - U9 symbol `SYMBOL_NEEDED` → `dual_adc_usb:GW1NR-LV9QN88PC6`.
  - `net_plan.md` still says R18/R19 are 10 k. The BOM (1 k) is correct.

## Receipt
- Block fpga: 26 parts (U9, J4, J5, D2, D3, R18–R24, C33–C46), 63 nets (17 local)
- py_compile OK; footprints 7/7 resolve; trial ERC 0 errors
- Signature changed: no. U9: 73/89 pins connected, and the other 16 are explicit NC.
