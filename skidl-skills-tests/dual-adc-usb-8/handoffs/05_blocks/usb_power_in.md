---
phase: 05_blocks/usb_power_in
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-26T12:30:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — usb_power_in

## Decisions
- Final signature (unchanged): `usb_power_in(v5, usb_dp, usb_dn, gnd)`.
- **Drives** v5 (U2.VOUT, PWROUT). **Bidirectional** usb_dp/usb_dn (connector + ESD only). gnd consumed.
- Local nets: `VBUS` (drive=POWER set in-block; connector pins are passive), `CC1`, `CC2`.
- **J1 symbol = `Connector:USB_C_Receptacle_USB2.0_16P`**, not the BOM's `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` (that is a footprint name; no such symbol exists). Pin numbers A1..B12/S1 match the HRO footprint pads 1:1.
- U2 uses generated `dual_adc_usb:TPS22919DCKR`. U1 I/O1 (1,6) = D+, I/O2 (3,4) = D-, VBUS(5) on raw VBUS.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/usb_power_in.py` | block @SubCircuit | Assembly |

## Next phase must
1. skidl-assembler: `usb_power_in(v5=V5, usb_dp=USB_DP, usb_dn=USB_DN, gnd=GND, tag='usb_power_in')`.
2. `GND.drive = POWER` at top level. V5 is driven by U2.VOUT; setting V5.drive=POWER at top is harmless.
3. Run with `symbols/` on the KiCad 9 symbol path (U2 is a generated symbol).
4. **part-sourcer / driver:** BOM `symbol` cells to fix so validate-bom passes — J1 → `Connector:USB_C_Receptacle_USB2.0_16P`; U2 → `dual_adc_usb:TPS22919DCKR`.

## Carried forward
- NC intentionally: J1 A8/B8 (SBU1/SBU2), U2 pin 4 (NC).
- ESD clamp capacitance of TECH PUBLIC USBLC6 unverified (datasheet summary) — harmless for USB HS.
- VBUS > 6 V transients exceed U2 abs max; U1 is the only clamp (datasheet note, not re-decided).

## Do not redo
- Pin mapping verified by instantiating the block: 8 parts, all pins connected or NC.

## Receipt
- Block usb_power_in: 8 parts (J1,U1,U2,R1,R2,C1–C3), 7 nets (3 local), py_compile OK, footprints 8/8 resolve, signature changed: no.
