---
phase: 05_blocks/bipolar_supply
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T23:30:54Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 block handoff — bipolar_supply

## Decisions
- Final signature, unchanged from work order: `bipolar_supply(vbus_sw, va_p2v5, va_n2v5, gnd)`.
- **DRIVEN:** va_p2v5, va_n2v5 (`.drive = POWER` set in-block; they sit behind FB3/FB4, so
  only passive pins would drive them otherwise). **CONSUMED:** vbus_sw (via FB2), gnd.
- Topology: VBUS_SW -FB2-> CP_VIN (C14 10µF, C15 100nF, drive=POWER) -> U7 VIN/EN+/EN-.
  U7 C+/C- = CP_FLYP/CP_FLYN with C16 1µF; CP -> CP_NEG with C17 2.2µF.
  OUT+ -> VA_P2V5_R (C18 2.2µF) -FB3-> VA_P2V5 (C20 10µF); OUT- -> VA_N2V5_R (C19 2.2µF)
  -FB4-> VA_N2V5 (C21 10µF). Net names match net_plan §1/§3.
- Dividers (datasheets/LM27762DSSR_SUMMARY.md): R6 107k OUT+->FB+, R7 100k FB+->GND
  (VOUT+ = 2.484 V); R8 105k OUT-->FB-, R9 100k FB-->GND (VOUT- = -2.501 V). 0402 1%.
  MPNs picked here (were TBD): R6 RC0402FR-07107KL/C138070, R8 0402WGF1053TCE/C25742
  (both Extended — no Basic 107k/105k exists), R7/R9 0402WGF1003TCE/C25741 (Basic).
- U7 PGOOD -> GND (SNVSAF7C pin table: "Connect to ground if not used"); EP pin 13 (PAD) -> GND.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/bipolar_supply.py` | @SubCircuit bipolar_supply, 18 parts | Assembling the circuit |

## Next phase must
1. Call: `bipolar_supply(vbus_sw=VBUS_SW, va_p2v5=VA_P2V5, va_n2v5=VA_N2V5, gnd=GND,
   tag='bipolar_supply')`.
2. No top-level drive needed for VA_P2V5/VA_N2V5; GND needs `.drive = POWER` at top level.
3. Standalone ERC shows one expected warning (VBUS_SW has only FB2 when the block runs alone);
   it clears once usb_power_in and power_rails are on the same net.

## Carried forward
- The FB3/FB4 post-filters sit outside the LDO feedback loop, so VA_P2V5/VA_N2V5 sag by
  I×DCR of BLM21PG601SN1D (DCR not re-checked here). The front-end load is small
  (2×OPA354 + clamps), so this is likely negligible. Unverified.
- 2 more Extended-tier MPNs (R6, R8) add loading fees; sourcing may prefer to substitute.

## Do not redo
- U7 LM27762DSSR, caps, and FB2-FB4 are verbatim from `sourcing/sourced_bom.md` § bipolar_supply.

## Receipt
bipolar_supply: 18 parts (U7, R6-R9, C14-C21, FB2-FB4, TP7, TP8), 12 nets (4 interface, 8 local).
py_compile OK; standalone smoke ERC: 0 errors, 1 expected isolation warning. Footprints valid.
Signature changed: no.
