---
phase: 05_blocks/usb_bridge
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-30T12:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---

# Block handoff - usb_bridge (rev 2: M1 fix, VREGIN 5 V mode)

## Decisions
- **SIGNATURE CHANGED: new param `vbus_sw`** (before v3v3d):
  `usb_bridge(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_clkout, ft_oe_n, vbus_sw, v3v3d, gnd)`.
- U10 now in VREGIN 5 V mode per DS_FT232H §6 Fig 6.1 + Table 3.1 note: VREGIN -> VBUS_SW (4.40-5.25 V, inside 3.6-5.5 V). M1 closed: VREGIN no longer depends on the +3V3D tolerance.
- VCCD (pin 39) = internal 3.3 V LDO **output** on new internal net FT_VCCD; NOT tied to +3V3D. Symbol pin overridden to PWROUT in-block.
- VPLL, VPHY -> FT_VCCD (Fig 6.1: "LDO 3.3 V supplies VCCIOs, VPLL and VPHY through VCCD"). Keeps PHY/PLL on the FT232H's own regulated rail.
- VCCIO x3 stay on +3V3D (FIFO talks to 3.3 V FPGA bank; 2.97-3.63 V spec vs 3.21-3.45 V rail OK).
- U11 EEPROM VCC and R102 10k EEDO pull-up -> FT_VCCD (Table 3.3: "pull Data-Out ... to VCCD"). EEPROM is thus powered with U10, before +3V3D comes up.
- Decoupling remap (same refs/values/MPNs): C100 100 nF + C108 4.7 uF (16 V) on VBUS_SW at VREGIN; C101 VCCD, C105 VPLL, C106 VPHY, C107 U11 on FT_VCCD; C102-C104 VCCIO on +3V3D; C109 FT_VCCCORE unchanged.
- Unchanged: 245 FIFO pin map, ACBUS4 SIWU# -> +3V3D, R100 12k REF, R101 10k RESET# -> +3V3D, R103 2.2k, Y2/C110/C111, VCCA PWRIN and EECS/EECLK OUTPUT overrides.
- Direction: drives ft_rxf_n, ft_txe_n, ft_clkout; senses ft_rd_n, ft_wr_n, ft_oe_n; bidirectional ft_d, usb_dp, usb_dm. Consumes vbus_sw, v3v3d, gnd.
- Internal nets: FT_VCCD (new), FT_VCCCORE, FT_XI, FT_XO, FT_REF, FT_RESET_N, FT_EECS, FT_EECLK, FT_EEDATA, FT_EEDO.

## Next phase must
- Assembler: update the call (keyword `vbus_sw` is new):
  `usb_bridge(usb_dp=USB_DP, usb_dm=USB_DM, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_clkout=FT_CLKOUT, ft_oe_n=FT_OE_N, vbus_sw=VBUS_SW, v3v3d=V3V3D, gnd=GND, tag='usb_bridge')`
- FT_D is `Bus('FT_D', 8)`. VBUS_SW, +3V3D, GND are driven elsewhere (U2 / U3); block only consumes them.
- Architect: update net_plan VBUS_SW row (add U10.VREGIN, C100, C108), +3V3D row (drop U10 VREGIN/VCCD/VPLL/VPHY, U11, R102, C100/C101/C105-C108), add FT_VCCD; VBUS_SW load +~54 mA Ireg + PHY (was on +3V3D).
- ERC gate: re-check U10 power pins; FT_VCCD driven by U10 VCCD (PWROUT).

## Carried forward
- No new parts or values; no BOM change for part-sourcer (C100/C108 only move rails; CL10A475KO8NNNC is 16 V, fine at 5.25 V).
- Fig 6.1 shows a ferrite bead VBUS->VREGIN and LC filters (+10 nF) on VPLL/VPHY; not in BOM, tied direct (as rev 1). Optional at layout.
- Sequencing: U10 core/VCCD up with VBUS_SW, VCCIO (+3V3D) ~2-3 ms later via EN_3V3. RESET# pull-up is on +3V3D, so U10 is held in reset until VCCIO is up. Accepted, not verified against an FTDI sequencing spec (none given).
- ACBUS7/8/9 NC intentionally. USB ESD in usb_power_in. EEPROM must be programmed to 245 FIFO (FT_Prog).

## Receipt
- block usb_bridge rev 2: 19 parts (unchanged refs), 30 nets in smoke test.
- py_compile OK. Smoke ERC: 0 errors, 16 warnings (single-pin interface nets only).
- Footprints unchanged/valid. Signature changed: YES (+vbus_sw).
