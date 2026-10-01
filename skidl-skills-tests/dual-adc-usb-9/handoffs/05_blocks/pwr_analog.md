---
phase: 05_blocks/pwr_analog
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-10-01T04:15:00Z
status: complete
next_phase: 05_coding
---

# Block handoff - pwr_analog

## Decisions
- Final signature (unchanged): `pwr_analog(vbus_sw, v3v3a, vafe_p, vafe_n, gnd)`.
- U5 `Regulator_Linear:TLV75733PDBV`: IN(1) + EN(3) = vbus_sw, GND(2), NC(4) -> NC, OUT(5) -> v3v3a. C10 1 uF in, C11 2.2 uF out.
- U6 `Regulator_SwitchedCapacitor:LM27762`: VIN(3), EN+(12), EN-(8) = vbus_sw; PGOOD(1), GND(4), PAD(13) -> gnd.
  C+(10)/C-(9) = LM_C1P/LM_C1N with C13 1 uF flying; CP(5) = LM_CP with C14 4.7 uF to gnd; C12 2.2 uF on VIN.
  OUT+(11) -> vafe_p, FB+(2) = FB_AFEP: R10 180k top / R11 100k bottom -> +3.360 V; C15 2.2 uF.
  OUT-(6) -> vafe_n, FB-(7) = FB_AFEN: R12 180k top / R13 100k bottom -> -3.416 V; C16 2.2 uF.
- Drives v3v3a, vafe_p, vafe_n directly from PWROUT pins (U5.OUT, U6.OUT+, U6.OUT-); no `.drive` needed. Consumes vbus_sw, gnd.
- Internal nets: LM_C1P, LM_C1N, LM_CP, FB_AFEP, FB_AFEN.

## Next phase must
- `from .pwr_analog import pwr_analog`, then
  `pwr_analog(vbus_sw=VBUS_SW, v3v3a=V3V3A, vafe_p=VAFE_P, vafe_n=VAFE_N, gnd=GND, tag='pwr_analog')`
  where V3V3A = Net('+3V3A'), VAFE_P = Net('VAFE_P'), VAFE_N = Net('VAFE_N').
- No top-level `.drive` on +3V3A / VAFE_P / VAFE_N. VBUS_SW is driven by usb_power_in.

## Carried forward
- U5 pin 4 NC intentionally (symbol NC pin).
- LM27762 PGOOD tied to GND (unused, per datasheet). Thermal PAD to GND plane; footprint without thermal vias chosen per BOM.
- TLV75733P pinout from KiCad symbol only (no PDF obtained; non-keystone).

## Do not redo
- Divider values and headroom arithmetic: architecture/net_plan.md section 2 pwr_analog.

## Receipt
- block pwr_analog: 13 parts, 10 nets (5 interface + 5 internal).
- py_compile OK; smoke instantiation + ERC: 0 errors, 0 warnings.
- Footprints valid (SOT-23-5, WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65, R_0402, C_0402/0603). Signature changed: no.
