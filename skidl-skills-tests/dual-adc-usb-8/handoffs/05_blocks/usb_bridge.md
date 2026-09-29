---
phase: 05_blocks/usb_bridge
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-26T14:30:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — usb_bridge

## Decisions
- Final signature (as ordered): `usb_bridge(usb_dp, usb_dn, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_siwu_n, ft_clkout, ft_oe_n, v5, gnd)`. It takes **v5, not v3v3d** (driver decision). `ft_d` is an 8-net bus with index 0 = D0 = ADBUS0.
- Power follows the Adafruit 5 V-in config:
  - VREGIN ← V5. VCCD is the internal 3.3 V regulator output, on local net **FT_3V3** (`.drive = POWER` is set in the block).
  - FT_3V3 supplies VCCIO×3, U11 VCC, the R26 RESET# pull-up, and FB3→FT_VPHY and FB4→FT_VPLL (both nets also `.drive = POWER`).
  - FT_VCORE = VCCCORE only. FT_VCCA is its own net.
- Direction:
  - **Drives:** FT_RXF_N (ACBUS0), FT_TXE_N (1), FT_CLKOUT (5).
  - **Senses:** FT_RD_N (2), FT_WR_N (3), FT_SIWU_N (4), FT_OE_N (6).
  - **Bidirectional:** FT_D, USB_DP, USB_DN.
  - **Consumes:** V5.
- Decoupling map (every cap is in-block):
  - C49 → VREGIN/V5 (0.1 µF). C50–C52 → VCCIO. C53 → VCCA. C54 + C55 → VCCCORE.
  - C56 4.7 µF → FT_3V3 (VCCD output bulk).
  - C57/C58 → VPHY, C59/C60 → VPLL.
  - **This differs from the BOM note.** The BOM puts C49 on VCCD, but with VREGIN on 5 V, VREGIN needs its own 0.1 µF, and VCCD is covered by C56 plus C50–C52 on the same net.
- Other fixed wiring:
  - R25 12.0 k REF→GND. TEST, AGND and GND → GND.
  - EEPROM: DI = EEDATA, DO → R27 2.2 k → EEDATA, CS/CLK direct.
  - Y1 case pads 2/4 → GND.
- Local nets: FT_3V3, FT_VPHY, FT_VPLL, FT_VCORE, FT_VCCA, FT_REF, FT_RESET_N, FT_XCSI, FT_XCSO, FT_EECS, FT_EECLK, FT_EEDATA, FT_EEDO.

## Next phase must
1. skidl-assembler: emit this call:

   `usb_bridge(usb_dp=USB_DP, usb_dn=USB_DN, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_siwu_n=FT_SIWU_N, ft_clkout=FT_CLKOUT, ft_oe_n=FT_OE_N, v5=V5, gnd=GND, tag='usb_bridge')`

   `FT_D` is the same `Bus('FT_D', 8)` that is passed to `fpga`.
2. V5 and GND must be driven, either by usb_power_in or with `.drive = POWER` at top. VREGIN is power-in.
3. Expected ERC warnings (not errors):
   - FT_EECS and FT_EECLK: "No drivers". The KiCad `Interface_USB:FT232H` symbol types EECS/EECLK as INPUT, although they are FT232H outputs. This is a false positive.
   - Single-pin warnings on the interface nets, until the fpga and usb_power_in blocks are attached.

## Carried forward
- **Intentional NC:** U10 ACBUS7, ACBUS8, ACBUS9 (unused in sync-245 mode).
- **UNVERIFIED keystones:**
  - The sync-245 ACBUS mapping (0 RXF#, 1 TXE#, 2 RD#, 3 WR#, 4 SIWU#, 5 CLKOUT, 6 OE#) is from FTDI family convention. It is set in the module constants at the top of the file, so it is easy to fix.
  - Y1 CL = 20 pF → C47/C48 = 33 pF.
  - The 3225 pads 1/3 = crystal and 2/4 = case follow footprint convention.
  - A x16 93LC56B works with the FT232H.
  - Current is 60/80 mA (note only).
  - The VCCD regulator must also supply the 93LC56 and the pull-up, a few mA, as in the Adafruit design.
- The FT232H I/O ring is FT_3V3, not V3V3D. Both are 3.3 V nominal, and FPGA bank 1 is at V3V3D. There is no level issue.
- R26 is 10 k (the reference design uses 12 k; they are equivalent).
- **BOM cell corrections (route to part-sourcer):**
  - Y1 symbol `Device:Crystal` → **`Device:Crystal_GND24`**, so the case pads 2/4 get a GND net.
  - The C49–C54 note: C49 is on VREGIN, not VCCD. C56 is the FT_3V3 (VCCD) bulk cap.
  - The U11 symbol is already correct in the CSV (`dual_adc_usb:93LC56BT-I_OT`).
- `net_plan.md` is superseded for this block: VREGIN = V5, VCCD = FT_3V3 (not FT_VCORE, not V3V3D).
- DS_FT232H §3/§4/§6 should still be checked by a human before layout.

## Receipt
- Block usb_bridge: 22 parts (U10, U11, Y1, R25–R27, C47–C60, FB3, FB4). 33 nets (13 local + 20 interface).
- py_compile OK. Footprints are all stock KiCad strings (6 distinct).
- Trial ERC with the block alone and V5/GND driven: 0 errors, 23 warnings (17 single-pin interface nets, 6 EECS/EECLK symbol-typing).
- Signature changed: no, it matches the work order (v5).
