---
phase: 05_blocks/power_rails
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T23:29:56Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 block handoff — power_rails

## Decisions
- Final signature, unchanged from work order:
  `power_rails(vbus_sw, vd_3v3, vd_1v8, vd_1v2, va_3v3, gnd)`.
- **DRIVEN:** vd_3v3 (U3), vd_1v2 (U4), vd_1v8 (U5), va_3v3 (U6) — each gets
  `.drive = POWER` inside the block. **CONSUMED:** vbus_sw (U3.VI, U6.IN/EN), gnd.
- Topology per net_plan §1: U3 VBUS_SW->VD_3V3; U4 and U5 fed from VD_3V3 (IN and EN);
  U6 VBUS_SW->VA_3V3 (IN and EN). All regulators always enabled.
- U3 uses KiCad `Regulator_Linear:TLV1117-33` (3 pins; SOT-223-3_TabPin2 tab = pad 2 = OUT),
  value/MPN TLV1117LV33DCYR. U6 uses generated `dual_adc_usb:TPS7A2033PDBVR`.
- TLV755xx / TPS7A20 NC pin (pin 4) -> NC.
- Caps: C5 10µF (VBUS_SW, U3 in), C6 10µF + C7 100nF (VD_3V3), C8/C9 1µF (U4 in/out),
  C10/C11 1µF (U5 in/out), C12/C13 1µF (U6 in/out).
- LED1 + R5: VD_3V3 -> R5 1k -> LED1 A->K -> GND (block-local unnamed net).
- TP1 VBUS_SW, TP2 VD_3V3, TP3 VD_1V8, TP4 VD_1V2, TP5 VA_3V3, TP6 GND (net_plan §10).

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/power_rails.py` | @SubCircuit power_rails, 21 parts | Assembling the circuit |

## Next phase must
1. Call: `power_rails(vbus_sw=VBUS_SW, vd_3v3=VD_3V3, vd_1v8=VD_1V8, vd_1v2=VD_1V2,
   va_3v3=VA_3V3, gnd=GND, tag='power_rails')`.
2. U6 needs `symbols/` on the symbol search path (generated `dual_adc_usb` library).
3. No extra drive needed for the four output rails; VBUS_SW is driven by usb_power_in;
   GND needs `.drive = POWER` at top level.

## Carried forward
- IC decoupling for consumer ICs on these rails is the consumer blocks' job; this block only
  holds each regulator's own in/out caps.
- LED1 current with a 1k resistor and a 520 nm green LED (Vf ≈ 2.6-2.9 V) is only ~0.5-0.7 mA
  — likely dim. BOM value left as sourced; reduce R5 (e.g. 330 Ω) if brightness matters.
  Unverified: the LED's Vf at sub-mA current was not checked against its datasheet.

## Do not redo
- U3 genuine TI TLV1117LV33DCYR, U4 TLV75512PDBVR — final per sourcing/datasheets.

## Receipt
power_rails: 21 parts (U3-U6, LED1, R5, C5-C13, TP1-TP6), 6 interface nets + 1 local.
py_compile OK; standalone smoke ERC: 0 errors/0 warnings. Footprints valid. Signature changed: no.
