---
phase: 05_blocks/power_digital
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-26T12:40:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — power_digital

## Decisions
- Final signature (unchanged): `power_digital(v5, v3v3d, v1v2, v1v8, gnd)`.
- **Consumes** v5. **Produces** v3v3d (U3+L1), v1v2 (U4+L2), v1v8 (U5.OUT, PWROUT).
- v3v3d and v1v2 reach the rail through inductors (passive pins) — no PWROUT pin on those nets from this block.
- Dividers per net plan: R3 100k / R4 22.1k → 3.315 V; R5 100k / R6 100k → 1.200 V (VFB 0.600 V).
- U5 IN and EN on v3v3d (net plan). U3/U4 EN on v5.
- Local nets: SW33, FB33, SW12, FB12, PWR_LED.
- No sizing assumes FT232H load on V3V3D (it now runs from V5, per driver).
- No optional 6.8 pF feed-forward caps (not in BOM).

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/power_digital.py` | block @SubCircuit | Assembly |

## Next phase must
1. skidl-assembler: `power_digital(v5=V5, v3v3d=V3V3D, v1v2=V1V2, v1v8=V1V8, gnd=GND, tag='power_digital')`.
2. **Set `V3V3D.drive = POWER` and `V1V2.drive = POWER` at top level** (inductor-fed; otherwise ERC flags undriven power-in pins downstream). Also `GND.drive = POWER`. V1V8 is driven by U5.OUT.
3. FB33/FB12 nets contain only INPUT + passive pins; an ERC "no driver" warning on them is a false positive.

## Carried forward
- NC intentionally: U5 pin 4 (NC).
- Symbols/footprints/values match BOM rows verbatim (`Regulator_Switching:TLV62569DBV`, `Regulator_Linear:TLV75518PDBV`, `Device:L/R/C/LED`).
- L1/L2 DCR/Isat unverified (distributor data); margin large per datasheet summary.

## Do not redo
- Pin names verified against KiCad symbols by instantiating the block (17 parts, all pins connected or NC).

## Receipt
- Block power_digital: 17 parts (U3–U5, L1, L2, D1, R3–R7, C4–C9), 10 nets (5 local), py_compile OK, footprints 11/11 resolve, signature changed: no.
