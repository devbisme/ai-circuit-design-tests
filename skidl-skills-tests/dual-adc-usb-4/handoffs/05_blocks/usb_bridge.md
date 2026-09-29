---
phase: 05_blocks/usb_bridge
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T23:30:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — usb_bridge

## Decisions
- Final signature is **unchanged** from the work order:
  `usb_bridge(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_siwu_n, ft_clkout, vd_3v3, gnd)`
- `ft_d` must be an 8-wide bus. It is indexed `ft_d[0]..ft_d[7]` and mapped to ADBUS0..7 (bit 0 = LSB).
- Directions (from U13): **driven** ft_rxf_n (ACBUS0), ft_txe_n (ACBUS1), ft_clkout (ACBUS5 → R66 33 Ω source termination); **sensed** ft_rd_n (ACBUS2), ft_wr_n (ACBUS3), ft_siwu_n (ACBUS4), ft_oe_n (ACBUS6); **bidirectional** ft_d, usb_dp, usb_dm. The symbol types all ACBUS/ADBUS pins BIDIR.
- Power is **consumed only** on vd_3v3: VREGIN 40, VCCD 39, VCCIO 12/24/46, U14, the pull-ups, and FB8. This is the 3.3 V-only supply configuration from the net plan.
- Local nets: FT_VCORE (VCORE 38 + VCCA 37), FT_VPHY (FB8 → VPHY 3, VPLL 8; `.drive = POWER` set in-block), FT_CLKOUT_R, FT_PWRSAV_N, FT_RESET_N, FT_XIN, FT_XOUT, FT_REF, FT_EECS, FT_EECLK, FT_EEDATA, FT_EEDO.
- **Symbol correction, U14:** `Memory_EEPROM:93LCxxBxxOT`, not the BOM's `93LCxxB`. The 8-pin `93LCxxB` (1 = CS) would put CS on the SOT-23-6 DO pad; `xxOT` is 1 DO, 2 GND, 3 DI, 4 CLK, 5 CS, 6 VCC, matching the summary. MPN/LCSC/footprint unchanged.
- **Symbol correction, Y1:** `Device:Crystal_GND24`, not `Device:Crystal`. The 3225-4Pin footprint has the resonator on diagonal pads 1/3 and case on 2/4; `Device:Crystal` pin 2 would land on case pad 2 and leave pad 3 unnetted. Y1.1 = FT_XIN, Y1.3 = FT_XOUT, Y1.2/4 = GND. MPN/footprint unchanged.
- **U13 pin 37 (VCCA) retyped** from power_out to power_in (`u13[37].func = Pin.types.PWRIN`). KiCad types it power_out, but DS_FT232H feeds VCCA from VCORE. Without this, ERC reports a POWER-OUT/POWER-OUT conflict on FT_VCORE.
- Cap allocation (BOM gave quantities only): C65/C66 22 pF load; C67 100 nF + C75 4.7 µF VREGIN; C68 VCCD; C69–C71 VCCIO 12/24/46; C72/C73 VPHY/VPLL + C77 4.7 µF; C74 100 nF + C76 4.7 µF VCORE/VCCA; C78 U14 VCC; C79 RESET# RC.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/usb_bridge.py` | `@SubCircuit usb_bridge`: U13, U14, Y1, R60–R67, C65–C79, FB8 | Assembling or reviewing this block |

## Next phase must
1. skidl-assembler: call it by keyword, exactly as follows:
   `usb_bridge(usb_dp=USB_DP, usb_dm=USB_DM, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_oe_n=FT_OE_N, ft_siwu_n=FT_SIWU_N, ft_clkout=FT_CLKOUT, vd_3v3=VD_3V3, gnd=GND, tag='usb_bridge')`
   Use `FT_D = Bus('FT_D', 8)`, the same object passed to fpga_core.
2. Set `.drive = POWER` at top level on VD_3V3 and GND, unless power_rails already drives them. This block has only power_in or passive pins on them.

## Carried forward
- **Driver amendment (post-handoff):** VCORE/VCCD bulk-cap question resolved against `datasheets/FT232HL-REEL.pdf` (now on disk) Fig 6.3 p.53 — C76 (4.7 µF) moved from FT_VCORE to VD_3V3 (VCCD bulk); VCORE keeps C74 (0.1 µF) only.
- ACBUS8 and ACBUS9 (pins 32 and 33) are `NC` on purpose, per net_plan §7.
- **Datasheet PDF missing.** `datasheets/FT232HL-REEL.pdf` is not on disk, although the summary says it was downloaded.
  - Decoupling placement and the 3.3 V-only VREGIN+VCCD tie are therefore from recollection of DS_FT232H §6 and the net plan. They are not checked against the PDF.
  - The one real uncertainty is 4.7 µF on VCORE versus 4.7 µF on VCCD. Check it against the datasheet before layout.
- FIFO mode depends on EEPROM contents. U14 must be programmed with FT_PROG for 245 FIFO. Sync mode additionally needs a D2XX `SetBitMode(0x40)` from host software. Both are firmware/software obligations, not schematic ones.
- R66 (and R57/R58 in the BOM) uses 0402WGF330**J**TCE. The "J" suffix normally means 5 % tolerance, although the BOM says 1 %. This is harmless for a series termination. Noted only.
- The ERC test instantiation gave 0 errors and 17 warnings. All 17 are single-pin interface nets that close once fpga_core and usb_power_in are assembled.

## Do not redo
- The FT245 sync pin map: ACBUS0..7 = RXF#, TXE#, RD#, WR#, SIWU#, CLKOUT, OE#, PWRSAV#.
- The Y1 and U14 symbol corrections above. They are geometry-driven, so do not revert them to the BOM symbols.

## Receipt
- Block `usb_bridge`: 27 parts (U13, U14, Y1, R60–R67, C65–C79, FB8).
- 31 nets: 19 interface bits (8 bus + 11 scalar) and 12 local.
- py_compile OK. Footprints valid (4/4 via validate-footprints.py).
- Test ERC: 0 errors, and every U13 pin is connected except the intentional NC pins 32 and 33.
- Signature changed: **no**.
