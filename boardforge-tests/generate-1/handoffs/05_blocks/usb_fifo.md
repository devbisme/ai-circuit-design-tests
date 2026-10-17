---
phase: 05_blocks/usb_fifo
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - usb_fifo

## Decisions
1. Signature unchanged: `usb_fifo(usb_dp, usb_dm, ft_d, ft_rxf_n, ft_txe_n, ft_rd_n, ft_wr_n, ft_oe_n, ft_clkout, v3v3, gnd)`.
2. `ft_d` is an 8-wide Bus, index 0 = LSB -> ADBUS0 (U901.13) ... ADBUS7 (U901.20).
3. Direction: drives ft_rxf_n, ft_txe_n, ft_clkout (via R910 22R); senses ft_rd_n, ft_wr_n, ft_oe_n (10k pull-ups R907/R908/R911 here); bidirectional ft_d, usb_dp, usb_dm. Consumes v3v3, gnd.
4. 3.3 V-only supply (FT_000288 Fig 6.3): VREGIN 40 + VCCD 39 + VCCIO 12/24/46 on +3V3; VCCCORE 38 -> C911, VCCA 37 -> C912 (local nets FT_VCORE/FT_VCCA, 1.8 V internal outputs).
5. VPHY 3 / VPLL 8 on local `+3V3_PHY` = +3V3 -> FB901 (BLM18KG601SN1D); C903 4.7u + C904/C905 100n. Net has `.drive = POWER` and a PWR_FLAG (`#FLG901`, power:PWR_FLAG, no footprint) for KiCad ERC.
6. U902 uses `Memory_EEPROM:93LCxxBxxOT` (SOT-23-6), connected by pin name. EECS 45 -> CS, EECLK 44 -> CLK, EEDATA 43 -> DI direct and DO via R903 2.2k; R904/R905/R906 10k pull-ups on EE_CS/EE_CLK/EE_DATA (per net plan).
7. ACBUS4 SIWU# R909 and ACBUS7 PWRSAV# R912 10k pull-ups to +3V3 (PWRSAV# high = never suspend even if option is set).

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/usb_fifo.py` | @SubCircuit usb_fifo, 29 BOM parts + 1 PWR_FLAG |

## Next phase must
- Emit: `usb_fifo(usb_dp=USB_DP, usb_dm=USB_DM, ft_d=FT_D, ft_rxf_n=FT_RXF_N, ft_txe_n=FT_TXE_N, ft_rd_n=FT_RD_N, ft_wr_n=FT_WR_N, ft_oe_n=FT_OE_N, ft_clkout=FT_CLKOUT, v3v3=P3V3, gnd=GND, tag='usb_fifo')` with `FT_D = Bus('FT_D', 8)`.
- `+3V3` and `GND` are only consumed here: `.drive = POWER` at top level if power_digital does not drive them.

## Carried forward
- Intentional NC: U901.32, U901.33 (ACBUS8/9).
- Y901 TXM12M0004252FBCEO00T: pinout ASSUMED 1/3 = crystal, 2/4 = GND (2520 convention, KiCad Crystal_GND24), CL 12 pF -> C901/C902 18 pF. No datasheet; unverified. Tol+stability ~40 ppm vs FTDI's 30 ppm figure.
- EEPROM DO has no dedicated 10k pull-up (datasheet p63 shows DO 10k to VCCD); it is pulled via R903 2.2k + R906 10k on EE_DATA, per net plan. Equivalent when DO tri-states.
- Decoupling all in-block: C906-C908 (VCCIO), C910 (VCCD/VREGIN), C913 (place at U902 VCC), C909 4.7u bulk. Assembler provides none.
- EEPROM option "suspend on ACBUS7 low" must stay off in FT_Prog config; FIFO mode 245 sync set in EEPROM (gateware/config, not hardware).
- Local nets: +3V3_PHY, FT_VCORE, FT_VCCA, FT_REF, FT_RESET_N, FT_XI, FT_XO, FT_SIWU_N, FT_CLKOUT_S, FT_PWRSAV_N, EE_CS, EE_CLK, EE_DATA, EE_DO.

## Do not redo
- MPNs/footprints/values verbatim from `sourcing/sourced_bom.csv`; FT232H pin numbers checked against the KiCad symbol pin table.

## Receipt
usb_fifo: 29 parts (U901, U902, Y901, FB901, 12 R, 13 C) + #FLG901; 11 interface args, 14 local nets; py_compile OK; footprints from CSV verbatim; signature changed: no.
