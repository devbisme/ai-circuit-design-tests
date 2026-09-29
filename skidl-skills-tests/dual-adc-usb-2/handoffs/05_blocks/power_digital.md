---
phase: 05_blocks/power_digital
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Wrote `circuits/dual_adc_usb/power_digital.py`: two cascaded fixed LDOs (U1
  AP7361C-33E-13 3.3 V/1 A, U2 AP2112K-1.2TRG1 1.2 V/600 mA) producing V3V3_D and V1V2
  from VBUS, plus a hardwired power-good LED (D3/R4).
- Compiles cleanly (`py_compile`); all 9 footprints validate (`validate-footprints.py`).
- Signature and interface net names used exactly as given in the work order — unchanged.

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/power_digital.py | `power_digital` SubCircuit (U1, U2, D3, R4, C3-C7) | skidl-assembler |

## Key facts for the next phase

- **Final signature (unchanged):** `def power_digital(vbus, gnd, v3v3_d, v1v2):`, `@subcircuit`.
- Nets: `VBUS` (input, consumed only — not driven here), `GND` (reference), `V3V3_D`
  and `V1V2` (outputs — this block sets `.drive = POWER` on both).
- U1 (AP7361C-33E) has no EN pin — always-on. U2 (AP2112K-1.2) EN tied internally to its
  own VIN (V3V3_D) — always-on, no external control needed.
- Rail budgets: V3V3_D 187 mA (U1 rated 1 A, SOT-223 fixed per R-11), V1V2 45 mA
  (U2 rated 600 mA, SOT-23-5).
- Pin names: U1 `VI`/`VO`/`GND`; U2 `VIN`/`EN`/`GND`/`NC`(pin4)/`VOUT`; LED D3 `A`/`K`.

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| DPow1 | Placement of the one sourced 100 nF cap (C7) — BOM has C3/C4 (1µF in), C5/C6 (10µF out), C7 (100nF, unassigned) for 2 ICs, not a full pair each | split each rail / both on V3V3_D / C7 on V1V2 | **C7 on V1V2** (with C6) | V1V2 is the lower-voltage, noise-sensitive FPGA core rail; V3V3_D already gets heavy extra decoupling downstream in `fpga_core` |
| DPow2 | U2 EN pin | leave for assembler / tie internally to VIN | **Tie internally** | No sequencing requirement per architecture; EN must not float (ERC); keeps assembler wiring simple |
| DPow3 | Decoupling cap ref naming vs. mandatory `C_DECOUP_<REF>` convention | rename / keep BOM refs C3-C7 | **Keep C3-C7** | Work order mandates using sourced BOM ref designators verbatim |

## Carried forward

- **VBUS drive**: this block only consumes VBUS (U1 VI, C3) — does not set
  `.drive = POWER` on it. Expected to already be driven by `usb_c_input`; if undriven at
  top level, assembler should set `vbus.drive = POWER` there.
- Assumed single global GND net (no AGND/DGND split) per net_plan.md.
- Assumed VBUS also feeds `power_analog` and a sense divider in `usb_bridge`
  independently — this block does not touch those paths.

## Do not redo

Parts/footprints (from `sourcing/sourced_bom.md`): U1 `AP7361C-33E-13` /
`Regulator_Linear:AP7361C-33E` / `Package_TO_SOT_SMD:SOT-223` (fixed, R-11); U2
`AP2112K-1.2TRG1` / `Regulator_Linear:AP2112K-1.2` / `Package_TO_SOT_SMD:SOT-23-5`;
D3 generic 0603 green LED / `Device:LED` / `LED_SMD:LED_0603_1608Metric`; R4 1kΩ 0402 /
`Device:R` / `Resistor_SMD:R_0402_1005Metric`; C3/C4 1µF 0603 / C5/C6 10µF 0805 / C7
100nF 0402, all `Device:C` with matching `Capacitor_SMD` footprints.

## Receipt (block metrics)

block_id: `power_digital` | part count: 9 (U1,U2,D3,R4,C3-C7) | net count: 4 (VBUS,GND,V3V3_D,V1V2) | compile: OK | footprints: OK (9/9)

## Escalation

none
