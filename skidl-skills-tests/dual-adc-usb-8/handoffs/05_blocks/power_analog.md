---
phase: 05_blocks/power_analog
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-26T12:50:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — power_analog

## Decisions
- Final signature (unchanged): `power_analog(v5, v3v3a, vp_afe, vn_afe, gnd)`.
- **Consumes** v5. **Drives** v3v3a (U6.OUT), vp_afe (U7.OUT+), vn_afe (U7.OUT-) — all PWROUT pins.
- U6 = generated `dual_adc_usb:TPS7A2033PDBVR`; IN+EN on v5, N/C pin 4 → NC.
- U7 LM27762 wired by pin number (symbol names contain +/-): VIN/EN+/EN- → v5, GND/PAD(13)/PGOOD → gnd.
- Dividers: R8 174k/R9 100k → +3.288 V; R10 64.9k/R11 100k → -2.012 V.
- **U7 footprint = stock `Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65`**. Its KiCad descr cites the LM27762 datasheet, and pads 1–12 + EP pad 13 match the symbol (PAD = 13). This replaces the BOM's `CUSTOM_FP_NEEDED`; no custom footprint generated.
- Local nets: LM_C1P, LM_C1N, LM_CP, LM_FBP, LM_FBN.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/power_analog.py` | block @SubCircuit | Assembly |

## Next phase must
1. skidl-assembler: `power_analog(v5=V5, v3v3a=V3V3A, vp_afe=VP_AFE, vn_afe=VN_AFE, gnd=GND, tag='power_analog')`.
2. `GND.drive = POWER` at top. V3V3A/VP_AFE/VN_AFE are driven here; no extra drive needed.
3. **part-sourcer / driver — BOM cells to fix** so validate-bom passes: U7 footprint → `Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65`; U6 symbol → `dual_adc_usb:TPS7A2033PDBVR`. Retires U7's `⚠️ CUSTOM FP NEEDED`.
4. LM_FBP/LM_FBN contain only INPUT + passive pins; an ERC "no driver" warning there is a false positive.

## Carried forward
- NC intentionally: U6 pin 4 (N/C).
- U7 footprint pad geometry was not re-measured against the DSS drawing (trusted the KiCad footprint that cites the LM27762 datasheet); a layout reviewer may confirm the EP 1.0×2.65 land.
- TPS7A2033 TJ ≈ 101 °C worst case at TA 50 °C (datasheet summary) — within 125 °C.

## Do not redo
- Pin mapping verified by instantiating the block (14 parts, all pins connected or NC).

## Receipt
- Block power_analog: 14 parts (U6, U7, R8–R11, C10–C17), 10 nets (5 local), py_compile OK, footprints 11/11 resolve, signature changed: no.
