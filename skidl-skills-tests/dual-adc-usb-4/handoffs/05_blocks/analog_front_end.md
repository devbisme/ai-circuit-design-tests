---
phase: 05_blocks/analog_front_end
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-11T00:20:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 block handoff — analog_front_end

## Decisions
- **Signature unchanged:** `analog_front_end(ain_a_p, ain_a_n, ain_b_p, ain_b_n, adc_vcm, va_3v3, va_p2v5, va_n2v5, gnd)`.
- **Drives:** AIN_A_P/N, AIN_B_P/N (via THS4521 outputs, 49.9 Ω/220 pF). **Loads only:** ADC_VCM (U9/U11 VOCM + C38/C48;
  driven by U12.CM in `adc`). **Consumes:** VA_3V3, VA_P2V5, VA_N2V5, GND. Nothing bidirectional.
- **THS4521 PD (pin 7) is active LOW, tied to VA_3V3 (enabled).** Source: `datasheets/THS4521IDGKR.pdf` p.4 pin table ("PD = logic
  low puts device into low-power mode. PD = logic high or open for normal operation"); enable threshold 2.1 V. Closes 04's item #6.
- **THS4521 wired by pin number** (the KiCad symbol names pins `+`, `-`, `~{PD}` and leaves outputs 4/5 unnamed): 1 VIN−, 2 VOCM,
  3 VS+, 4 VOUT+, 5 VOUT−, 6 VS−=GND, 7 PD, 8 VIN+. Rg into IN+, OUT−→IN+ feedback, so AIN_x_P is in phase with the BNC.
- **FOOTPRINT DEVIATION FROM sourced_bom.md (J2/J3):** the BOM's `Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal` is a *dual*
  isolated BNC (pads 1–4 = two jacks), so each channel would have placed two jacks and left pads 3/4 with no net. BNC-KWE-6 is a single
  5-pin elbow bulkhead jack. I replaced it with **`ProjectLocal:BNC_cntitle_BNC-KWE-6_Horizontal`**, generated from the maker's
  PCB pattern (cntitle CT3.660.861: center + 4 legs on SQ8.1 mm, Ø1.5 mm holes). Pad 1 = center, the four legs are all pad 2 = shield.
  No stock KiCad BNC matches: TE 1478035 has its legs on a 10.05 mm square.
- **FOOTPRINT DEVIATION (VC1/VC2):** replaced `Capacitor_SMD:C_Trimmer_Sprague-Goodman_SGC3` (4.75 mm outer extent) with
  **`ProjectLocal:C_Trimmer_SEHWA_STC3M`**, built to SEHWA STC3M-SP-15 rev 4.1 p.3: pads 1.25×1.40 mm, outer 5.10 mm, gap 2.60 mm.
  This closes the VC1/VC2 mechanical check carried open since sourcing.
- Every other MPN/LCSC/footprint/value is verbatim from `sourcing/sourced_bom.md`. Each part carries `MPN` and `LCSC` fields.
  They are set via `part.fields[...]`: a new key passed as a `Part()` kwarg becomes an attribute, not a netlist field (SKiDL 3.0.0).

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/analog_front_end.py` | The block; one `_afe_channel()` helper called twice (A idx 0, B idx 1) | Assembling |
| `footprints/ProjectLocal.pretty/BNC_cntitle_BNC-KWE-6_Horizontal.kicad_mod` | J2/J3 footprint | Footprint path setup / layout |
| `footprints/ProjectLocal.pretty/C_Trimmer_SEHWA_STC3M.kicad_mod` | VC1/VC2 footprint | Footprint path setup / layout |

## Next phase must
1. skidl-assembler: call exactly
   `analog_front_end(ain_a_p=AIN_A_P, ain_a_n=AIN_A_N, ain_b_p=AIN_B_P, ain_b_n=AIN_B_N, adc_vcm=ADC_VCM, va_3v3=VA_3V3, va_p2v5=VA_P2V5, va_n2v5=VA_N2V5, gnd=GND, tag='analog_front_end')`.
2. Set `.drive = POWER` at top level on VA_3V3, VA_P2V5, VA_N2V5, GND if their supply blocks don't: this block only consumes them.
   ADC_VCM's driver is U12.CM (`adc` block). If ERC flags ADC_VCM as undriven, the fix belongs there, not here.
3. Put `footprints/` on the footprint search path (`KICAD9_FOOTPRINT_DIR` / fp-lib-table nickname `ProjectLocal`) or the J2/J3/VC1/VC2
   footprints won't resolve at export.
4. `validate-footprints.py` reports "0 checked" for this file because the footprint strings sit in BOM constants, not literal
   `footprint='...'` args. All 10 unique strings were verified by hand to resolve to `.kicad_mod` files. Validate the assembled netlist instead.
5. Driver: `sourcing/sourced_bom.md` rows J2/J3 and VC1/VC2 still list the old footprints. Update them so the BOM and netlist agree.

## Carried forward
- No pins left NC. The smoke instantiation found 0 unconnected pins across 48 parts.
- Local decoupling is 100 nF only (C32/C33/C37 and C42/C43/C47, per BOM). No refs are allotted for 10 µF, so bulk is assumed from
  C20/C21 (`bipolar_supply`) and C13 (`power_rails`). The `C_DECOUP_<IC_REF>` naming rule is not applied because refdes are pre-assigned.
- BNC-KWE-6 barrel and nut extend about 24 mm forward of the 10×10 mm housing. The courtyard covers only the housing, so place the
  jack at the board edge. The 2.5 mm annular pads are my choice; the maker gives only hole sizes.
- Not determined: which STC3M terminal is the rotor (adjust screw). Prefer rotor-to-BNC_x at layout. Low confidence; the drawing doesn't say.
- Unchanged from design_risks: no primary BNC TVS, THS4521 input pulled below NRI during clamp, one-time VC trim with a 1 kHz square wave.

## Do not redo
- THS4521 PD polarity (active low → VA_3V3), BAV199 orientation (A1→VA_N2V5, K2→VA_P2V5, K1_A2→AFE_x_TAP), OPA354 pin map.
- The two ProjectLocal footprints above: built from the manufacturers' own drawings.

## Receipt
Block `analog_front_end`: 48 parts (J2–3, U8–11, D2–3, VC1–2, R10–29, C30–38, C40–48), 27 nets (9 interface + 18 local).
py_compile OK; scratch instantiation 0 unconnected pins; footprints 10/10 resolve (2 generated ProjectLocal). Signature changed: no.
status: complete.
