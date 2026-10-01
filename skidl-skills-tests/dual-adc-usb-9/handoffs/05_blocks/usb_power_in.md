---
phase: 05_blocks/usb_power_in
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-10-01T04:00:00Z
status: complete
next_phase: 05_coding
---

# Block handoff - usb_power_in

## Decisions
- Final signature (unchanged): `usb_power_in(vbus_sw, usb_dp, usb_dm, gnd)`.
- J1 `Connector:USB_C_Receptacle_USB2.0_16P`: VBUS x4 -> VBUS; GND x4 + SHIELD -> gnd; A5 CC1 / B5 CC2 -> R1/R2 5.1k -> gnd (UFP Rd); A6+B6 -> usb_dp; A7+B7 -> usb_dm; A8/B8 SBU -> NC.
- VBUS -> F1 PTC 0.75 A -> VBUS_F. VBUS_F: D1 SMF5.0A (pin 1 K, pin 2 A -> gnd), U1 USBLC6 VBUS, C1 4.7 uF, U2.VIN, R3.
- U1 USBLC6-2SC6 flow-through: pins 1,6 (I/O1) -> usb_dp; pins 3,4 (I/O2) -> usb_dm; GND -> gnd.
- U2 TPS22918: ON <- R3 10k from VBUS_F (net USB_ON); CT -> C2 1 nF (USB_CT, tR 2.54 ms); QOD tied to VOUT; VOUT -> vbus_sw; C3 10 uF on vbus_sw.
- Drives: vbus_sw (U2.VOUT is a PWROUT pin). Bidirectional passthrough: usb_dp, usb_dm. Consumes: gnd.
- `vbus_f.drive = POWER` is set inside the block (VBUS arrives via passive J1/F1; internal net the top level cannot reach).
- Internal nets: VBUS, VBUS_F, USB_ON, USB_CT, CC1, CC2.

## Next phase must
- `from .usb_power_in import usb_power_in`, then
  `usb_power_in(vbus_sw=VBUS_SW, usb_dp=USB_DP, usb_dm=USB_DM, gnd=GND, tag='usb_power_in')`
- Do NOT set `.drive` on VBUS_SW (U2.VOUT drives it). GND needs `.drive = POWER` at top level.

## Carried forward
- J1 SBU1/SBU2 NC intentionally (USB 2.0 only).
- C3 10 uF 0603 10 V X5R on 5 V: effective ~4-5 uF after DC bias; acceptable (bulk on VBUS_SW also from C4/C6/C9/C10/C12 in power blocks).
- Inrush budget per net_plan (~45 uF downstream, 71 mA) assumes downstream caps as sourced.
- Footprints: USB_C_Receptacle_HRO_TYPE-C-31-M-12, Fuse_1206_3216Metric, D_SOD-123F, SOT-23-6 (U1,U2), R_0402, C_0402/0603 — all present in KiCad lib.

## Do not redo
- D1 pinout by number (1 = K, 2 = A) per datasheets handoff; KiCad SMF5V0A names are A1/A2.

## Receipt
- block usb_power_in: 11 parts, 10 nets (4 interface + 6 internal).
- py_compile OK; smoke instantiation + ERC: 0 errors, 0 warnings.
- Footprints valid. Signature changed: no.
