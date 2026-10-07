# Design changelog

Append-only, newest first. One entry per committed copperhead run.

## 2026-10-06 — create pipeline stage: part-selection

- Change: part-selection-bom
- Files: docs/BOM.md, docs/DECISIONS.md
- Verification: ERC not required

## 2026-10-06 — create pipeline stage: architecture

- Change: architecture-subsystems
- Files: docs/SUBSYSTEMS.md, docs/SPEC.md, docs/CHANGELOG.md, docs/DECISIONS.md
- Verification: ERC not required

## 2026-10-06 — create pipeline stage: architecture

- Change: architecture-subsystems
- Files: docs/SUBSYSTEMS.md (new), docs/SPEC.md (§6 open items), docs/DECISIONS.md, docs/CHANGELOG.md, .copperhead/constraints.json
- Summary:
  - Two power domains: always-on 3V3_AON (FT232H, 93LC56 and bus switch only) and a gated VBUS_SW behind a soft-start load switch driven by PWREN_N.
  - Steady state ≈342 mA, pre-configuration ≈61 mA, suspend ≤1.6 mA, ≤9 µF ungated capacitance.
  - ADC clock goes XO → fanout → ADC, never through the FPGA (≈1.5 ps RSS).
  - Front end: ÷5 compensated 1 MΩ divider, then clamps, buffer, FDA, 5th-order LC anti-alias filter.
  - No MCU (FPGA only), by design.
  - AT RISK: dc_accuracy offset budget has no margin and needs an ADC offset ≤0.9 mV.
- Verification: ERC not required (no schematic yet)

## 2026-10-06 — create pipeline stage: spec-seed

- Change: spec-seed-dual-adc-usb
- Files: docs/SPEC.md, docs/DECISIONS.md
- Verification: ERC not required
