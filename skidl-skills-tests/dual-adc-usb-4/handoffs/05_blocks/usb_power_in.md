---
phase: 05_blocks/usb_power_in
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T23:28:51Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 block handoff — usb_power_in

## Decisions
- Final signature, unchanged from work order: `usb_power_in(vbus_sw, usb_dp, usb_dm, gnd)`.
- **vbus_sw: DRIVEN** by U2.OUT (PWROUT); the block also sets `vbus_sw.drive = POWER`.
  **usb_dp / usb_dm: bidirectional** pass-through (J1 + U1 clamp only). **gnd: consumed.**
- U1 mapping follows net_plan §2: I/O1 (pins 1,6) = USB_DP, I/O2 (pins 3,4) = USB_DM. The
  USBLC6 is symmetric, so this differs harmlessly from the datasheet summary's "I/O1 = D-" note.
- U2.EN tied to VBUS_F (net_plan §1) — switch always on when VBUS present; no pull-down needed.
- D1 (Device:D_TVS) pin 1 = cathode (banded) -> VBUS, pin 2 -> GND, per SMF5.0A pinout.
- R3 = 8.45 kΩ 1% 0603 (BOM footprint is 0603, not the 0402 the datasheet note mentions):
  MPN 0603WAF8451T5E, LCSC C14892 (Extended; no Basic 8.45k exists). ILIM ≈ 0.805 A.
- Block-local nets: VBUS, VBUS_F (both `drive = POWER`, fed only by passive pins),
  USB_CC1, USB_CC2, USB_SHIELD, SW_ISET. J1 SBU1/SBU2 -> NC.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/usb_power_in.py` | @SubCircuit usb_power_in, 13 parts | Assembling the circuit |

## Next phase must
1. Call: `usb_power_in(vbus_sw=VBUS_SW, usb_dp=USB_DP, usb_dm=USB_DM, gnd=GND, tag='usb_power_in')`.
2. U2 is `Part('dual_adc_usb', 'SY6280AAC')` — `symbols/` must be on the symbol search path
   (e.g. `lib_search_paths[KICAD9].append(<abs path to symbols>)` in `__main__.py`).
3. VBUS_SW already gets drive=POWER here; GND needs `.drive = POWER` at top level.

## Carried forward
- ISET formula (6800/R) is from Silergy's app note, not a local datasheet PDF — re-check if
  the PDF becomes available.
- No decoupling expected from the assembler; C1/C2 (VBUS_F) and C3 (VBUS_SW) are in-block.
  Downstream VBUS_SW caps (C5, C12, C14) live in power_rails/bipolar_supply.

## Do not redo
- Part/footprint/MPN choices are verbatim from `sourcing/sourced_bom.md` § usb_power_in.

## Receipt
usb_power_in: 13 parts (J1 U1 U2 D1 FB1 R1-R4 C1-C4), 10 nets + NC. py_compile OK; standalone
smoke run with ERC: 0 errors/0 warnings. Footprints valid. Signature changed: no.
