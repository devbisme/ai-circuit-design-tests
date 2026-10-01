---
phase: 05_blocks/afe_ch_b
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-10-01T03:16:18Z
status: complete
next_phase: 05_coding
---

# Block handoff - afe_ch_b

## Decisions
- Final signature (unchanged): `afe_ch_b(ain_p, ain_n, adc_vcm, vafe_p, vafe_n, v3v3a, gnd)`.
- File `circuits/dual_adc_usb/afe_ch_b.py` is a thin @SubCircuit wrapper over the shared helper
  `circuits/dual_adc_usb/_afe_common.py::build_afe_channel()` (plain function, not a block; shared by afe_ch_a/afe_ch_b).
- Topology exactly per `architecture/net_plan.md` §afe_ch_a (suffix _B): 910k/18pF/2-6pF trim over 100k/200pF,
  BAV199 clamp, 1k series, OPA810 follower, THS4521 MFB (1.1k/1k/270/100pF/12pF), 33R+33R+270pF diff to ADC.
- All IC/diode pins connected by number (OPA810 1=OUT; THS4521 4=VOUT+, 5=VOUT-; BAV99 1->VAFE_N, 2->VAFE_P, 3->ATT_B).
- Drives: ain_p, ain_n. Consumes only: adc_vcm (THS4521 VOCM), vafe_p, vafe_n, v3v3a, gnd. No bidirectional nets.
- Internal nets: BNC_B, ATT_B, BUF_IN_B, BUF_OUT_B, MFB_MS_B, MFB_MR_B, FDA_INP_B, FDA_INN_B, FDA_OUTP_B, FDA_OUTN_B.
- Every part carries MPN and LCSC fields from sourced_bom.csv.

## Next phase must
- Import: `from .afe_ch_b import afe_ch_b` (helper `_afe_common.py` must stay in the package dir).
- Call: `afe_ch_b(ain_p=ADC_AINB_P, ain_n=ADC_AINB_N, adc_vcm=ADC_VCM, vafe_p=VAFE_P, vafe_n=VAFE_N, v3v3a=V3V3A, gnd=GND, tag='afe_ch_b')`
  where V3V3A is the net named `+3V3A`.
- `.drive = POWER` at top level (or via the regulator blocks) for VAFE_P, VAFE_N, +3V3A, GND: this block only sinks them.
- ADC_VCM is driven by U7 CM in adc_dual; THS4521 VOCM is an input, so no ERC driver comes from here.

## Carried forward
- **J3 footprint `ProjectLocal:KH-BNC50-3511` does NOT exist** (footprint validator: library my_board.pretty not found).
  Used verbatim from sourced_bom as instructed. Footprint phase must create it from the KH-BNC50-3511 drawing
  (pin 1 = centre/In, pin 2 = shell/Ext), or change the string to ProjectLocal:<name> after generating.
- C41 trimmer footprint `Capacitor_SMD:C_Trimmer_Voltronics_JZ` is a stand-in; verify vs STC3MA06 land pattern at layout.
- No NC pins. THS4521 PD tied to +3V3A (always enabled). Decoupling inside block: C43/C44 (VAFE_P/N at U40), C49 (+3V3A at U41), C51 (ADC_VCM at U41).
- C50 270 pF sits across ain_p/ain_n; place close to U7 at layout.
- Assumes VAFE_P/VAFE_N are the bipolar rails from pwr_analog (OPA810 needs >=4.75 V total).

## Receipt
- block afe_ch_b: 27 parts (J3, U40, U41, D40, R40-R50, C40-C51), 17 nets (10 internal + 7 interface).
- py_compile OK; smoke instantiation with afe_ch_a+afe_ch_b: 54 parts, 0 unconnected pins.
- Footprints: all valid except J3 ProjectLocal:KH-BNC50-3511 (flagged, custom FP pending). Signature changed: no.
