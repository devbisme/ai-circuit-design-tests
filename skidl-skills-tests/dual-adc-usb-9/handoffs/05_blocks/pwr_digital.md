---
phase: 05_blocks/pwr_digital
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-10-01T04:10:00Z
status: complete
next_phase: 05_coding
---

# Block handoff - pwr_digital

## Decisions
- Final signature (unchanged): `pwr_digital(vbus_sw, v3v3d, v1v2, v1v8, gnd)`.
- Three `Regulator_Switching:TLV62569DBV` (TLV62569DBVR) bucks, VIN = vbus_sw, L = FHD4020S 2.2 uH:
  - U3 -> L1 -> v3v3d; FB R5 100k (top) / R6 22k (bottom) -> 3.327 V; EN = EN_3V3 from R9 100k (vbus_sw) + C8 100 nF to GND (2.0-3.2 ms delay after +1V2/+1V8).
  - U4 -> L2 -> v1v2; FB R7 100k / R8 100k -> 1.200 V; EN = vbus_sw.
  - U12 -> L3 -> v1v8; FB R14 200k (top) / R15 100k (bottom) -> 1.800 V; EN = vbus_sw (ramps with VCC, UG284).
- Input caps C4/C6/C9 10 uF (vbus_sw); output caps C5/C7/C17 22 uF.
- Drives v3v3d, v1v2, v1v8: each is set `.drive = POWER` inside the block, because the regulator's PWROUT pin is SW and reaches the rail only through the passive inductor. Consumes vbus_sw, gnd.
- Internal nets: SW_3V3, FB_3V3, EN_3V3, SW_1V2, FB_1V2, SW_1V8, FB_1V8.

## Next phase must
- `from .pwr_digital import pwr_digital`, then
  `pwr_digital(vbus_sw=VBUS_SW, v3v3d=V3V3D, v1v2=V1V2, v1v8=V1V8, gnd=GND, tag='pwr_digital')`
  where V3V3D = Net('+3V3D'), V1V2 = Net('+1V2'), V1V8 = Net('+1V8').
- No `.drive` needed at top level for +3V3D/+1V2/+1V8 (set in block). VBUS_SW is driven by usb_power_in (U2.VOUT).

## Carried forward
- Assumption K10 (unverified, accepted): +1V8 load (VCCO3 + PSRAM) <= 100 mA; U12 is 2 A capable so no part change if wrong, only the USB budget.
- TLV62569DBV has no PG pin; sequencing relies on the R9/C8 EN delay only.
- L1-L3 footprint is the same-vendor FNR4020S; verify pads vs FHD4020S at layout (sourcing flag).
- C4/C6/C9 10 uF 0603 10 V on 5 V derate to ~5 uF effective; acceptable per sourcing.

## Do not redo
- Divider values and EN delay arithmetic: architecture/net_plan.md section 2 pwr_digital.

## Receipt
- block pwr_digital: 20 parts, 12 nets (5 interface + 7 internal).
- py_compile OK; smoke instantiation + ERC: 0 errors, 0 warnings; connectivity dump checked.
- Footprints valid (SOT-23-5, L_Changjiang_FNR4020S, R_0402, C_0402/0603/0805). Signature changed: no.
