---
phase: 05_blocks/power_analog
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Wrote `circuits/dual_adc_usb/power_analog.py`: Q1 (AO3401A) PWREN_N-gated P-FET load
  switch feeding two independent ferrite-bead rail entries (FB2->L2/C12->V5_A,
  FB3->U4 LP5907 LDO->V3V3_A); U3 (LM2776) generates VN5_A from V5_A (EN tied to VIN,
  so it is inherently PWREN_N-gated too); FB6 taps V3V3_A->V3V3_CLK; U5 (REF3025) +
  R7/R8 precision divider generates a shared ~0.500 V AFE offset bias fanned out to
  VREF_0V5_A (direct) and VREF_0V5_B (via isolation resistor R9).
  This satisfies binding constraint "Q1 gates V5_A, V3V3_A, and the LM2776 from
  PWREN_N" (A14/R-10) without adding extra EN wiring: V3V3_A and the LM2776's VIN both
  derive from the same Q1-switched node.
- Compiles cleanly (`py_compile`); all 28 footprints validate
  (`validate-footprints.py`); standalone ERC (Net() stand-ins for all 9 interface
  params) reports **0 errors, 5 warnings**, all expected/benign for an isolated block
  test (single-pin nets that connect elsewhere — PWREN_N, V3V3_CLK, VREF_0V5_B — plus
  the standard "insufficient drive current" note on an internal pre-LDO node, all
  flagged as expected in `.claude/rules/skidl-syntax.md`).
- Signature used exactly as given in the work order — unchanged.
- **Resolved the AD9235 VIN- 1.500 V strapping split** (per the datasheet phase's
  explicit instruction to state which side this block implements): this block builds
  ONLY the 0.5 V R7/R8 divider (VREF_0V5_A/_B). It does **not** build a VIN- 1.5 V
  divider and does **not** expose VREF_2V5 (REF3025's 2.5 V output stays internal to
  this file). See `## Carried forward` for what `adc_channel` must do instead.

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/power_analog.py | `power_analog` SubCircuit (U3, U4, U5, Q1, FB2, FB3, FB6, L1, L2, R5-R9, C8-C21) | skidl-assembler |

## Key facts for the next phase

- **Final signature (unchanged):** `def power_analog(vbus, gnd, pwren_n, v3v3_a, v3v3_clk, v5_a, vn5_a, vref_0v5_a, vref_0v5_b):`, decorated `@subcircuit`.
- Nets consumed only (not driven here): `vbus`, `gnd`, `pwren_n` — must already be
  driven by `usb_c_input` (VBUS), the single global GND, and `usb_bridge` (PWREN_N,
  FT232H ACBUS9) respectively.
- Nets **driven** by this block (`.drive = POWER` set at the bottom of the file):
  `v3v3_a`, `v3v3_clk`, `v5_a`, `vn5_a`, `vref_0v5_a`, `vref_0v5_b`. The last two are
  driven through a passive resistor divider (no active output pin on that net), which
  is why `.drive = POWER` is set explicitly rather than relying on a driver pin type.
- Pin names used: Q1 (`Q_PMOS_GSD`) `G`/`S`/`D`; U3 (LM2776) `VIN`/`GND`/`VOUT`/`EN`/
  `C1+`/`C1-`; U4 (LP5907MFX-3.3) `IN`/`GND`/`EN`/`NC`(pin4)/`OUT`; U5 (REF3025)
  `IN`/`OUT`/`GND`; FerriteBead/R/C/L all use numeric pins `1`/`2`.
- Rail budgets implemented: V3V3_A 105 mA (LP5907 rated 250 mA), V5_A 60 mA, VN5_A
  30 mA (LM2776 rated 60 mA), V3V3_CLK 20 mA (FB6 tap off V3V3_A) — all within the
  binding-constraint numbers.

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| DA1 | U3 (LM2776) EN pin source | tie to own VIN / drive directly from `pwren_n` | **Tie to VIN (=V5_A)** | `pwren_n` is a 3.3 V logic signal not referenced to LM2776's ~5 V VIN domain; V5_A is already Q1-gated, so tying EN=VIN achieves correct active-HIGH gating "for free" and satisfies the "LM2776 gated by PWREN_N" constraint indirectly but correctly |
| DA2 | R7/R8 divider topology vs. net_plan.md's literal "one 4.02k/1.00k divider per channel" (4 resistors) | 2 independent per-channel dividers (needs 4 resistors) / 1 shared divider (needs 2) | **1 shared divider (R7/R8) + R9 series isolation on channel B** | This block's ref budget is fixed at R5-R9 (5 total, per both `02_architecture.md` and `03_sourcing.md`) — R5/R6 consume 2 for Q1's gate network, leaving only 3, not the 4 a "2 full dividers" reading needs. A single shared REF3025-derived divider also gives both ADC channels the *same* 0.5 V offset, arguably better for inter-channel gain/offset matching than two independently-toleranced dividers. R9 (100Ω) gives channel B its own physical node for layout while adding <100 uV of series drop at the <1 uA load. |
| DA3 | AD9235 VIN- 1.500 V divider ownership (the datasheet-phase-mandated NEW divider, distinct from R7/R8) | build it here and add a `vref_2v5` net to the signature / build it here off an existing rail / leave it to `adc_channel` | **Leave to `adc_channel`** | No spare ref designators here (R7/R8/R9 already spoken for by DA2); `adc_channel`'s own ref range (R120-R133 / R220-R233) has exactly 2 unaccounted resistors beyond its 12 `R_damp`, sized for this; the AD9235 datasheet summary itself says precision doesn't matter for this DC bias node, so a local divider off V3V3_A (already an `adc_channel` input) is fully adequate and avoids widening this block's interface |
| DA4 | 1 µF bypass at each VREF_0V5_<X> node (called for in net_plan.md) | add here (no spare cap ref) / omit / flag for afe_channel to add at point of use | **Flag for `afe_channel`** | All 14 of this block's cap refs (C8-C21) are consumed by U3/U4/U5 decoupling; a bypass at the OPA836 input pin is also better practice (point-of-use) than one further back at the divider |
| DA5 | Decoupling cap ref naming vs. mandatory `C_DECOUP_<REF>` convention | rename / keep BOM refs C8-C21 | **Keep C8-C21** | Work order mandates using sourced BOM ref designators verbatim; inline comments document each cap's role instead |

## Carried forward

- **`adc_channel` must build its own AD9235 VIN- 1.500 V bias divider locally**, using
  2 of its own spare resistors (ref range suggests R132/R133 for channel A,
  R232/R233 for channel B — 12 of the 14 R1xx/R2xx resistors are `R_damp`, the
  remaining 2 are unaccounted for in `sourced_bom.md`'s table and are the natural fit).
  Recommended: divide off `v3v3_a` (this block's output, 3.3 V) rather than needing a
  new net from this block — e.g. ~1.2k/1.0k gives 1.5 V from 3.3 V. Per the AD9235
  datasheet summary, precision is not critical for this node (a static DC bias, not a
  gain-setting network), so this is a safe simplification versus routing REF3025's
  2.5 V output across the block boundary.
- **`afe_channel` should add the 1 µF bypass-to-GND called for at each VREF_0V5_<X>
  node** (net_plan.md §1) at its own point of use (the OPA836 non-inverting input),
  using its own C10x/C20x cap allocation — this block has no spare cap ref for it.
- **VBUS drive**: this block only consumes VBUS (Q1 source, R5) — does not set
  `.drive = POWER` on it. Expected to already be driven by `usb_c_input`.
- **PWREN_N drive**: this block only consumes PWREN_N (R6) — expected to be driven by
  `usb_bridge` (FT232H ACBUS9, EEPROM-configured as PWREN#).
- Assumed single global GND net (no AGND/DGND split) per net_plan.md.
- Assumed `afe_channel`'s two OPA836 instances (U11/U13 per net_plan.md) are the only
  consumers of VREF_0V5_A/_B, and `adc_channel`/`afe_channel` U10/U12 (AD8066) op-amps
  are the only consumers of V5_A/VN5_A.

## Do not redo

Parts/footprints (from `sourcing/sourced_bom.md` Block 3, `power_analog`):
Q1 `AO3401A` / `Transistor_FET:Q_PMOS_GSD` / `Package_TO_SOT_SMD:SOT-23`;
U3 `LM2776DBVR` / `Regulator_SwitchedCapacitor:LM2776` / `Package_TO_SOT_SMD:SOT-23-6`;
U4 `LP5907MFX-3.3/NOPB` / `Regulator_Linear:LP5907MFX-3.3` / `Package_TO_SOT_SMD:SOT-23-5`;
U5 `REF3025AIDBZR` / `Reference_Voltage:REF3025` / `Package_TO_SOT_SMD:SOT-23`;
FB2/FB3/FB6 `BLM18PG601SN1D` / `Device:FerriteBead` / `Inductor_SMD:L_0603_1608Metric`;
L1/L2 `Murata LQM2HPN100MGL` (10 µH) / `Device:L` / `Inductor_SMD:L_0805_2012Metric`;
R5 100k, R6 10k, R9 100Ω — generic 0402 `Device:R` / `Resistor_SMD:R_0402_1005Metric`;
R7 4.02k (Susumu RG1005N-4021-B-T5), R8 1.00k (Susumu RG1005N-1001-B-T5), 0.1%/25 ppm,
0402 `Device:R` / `Resistor_SMD:R_0402_1005Metric`;
C8/C9 1 µF 0603 (flying cap, paralleled), C10/C11 10 µF 0805 (U3 bulk),
C12/C13 22 µF 1206 (post-filter bulk), C14-C17 1 µF 0603 (U4/U5 in/out),
C18-C21 100 nF 0402 (per-pin) — all `Device:C` with matching `Capacitor_SMD` footprints.

## Receipt (block metrics)

block_id: `power_analog` | part count: 28 (U3,U4,U5,Q1,FB2,FB3,FB6,L1,L2,R5-R9,C8-C21) | net count: 9 interface + 9 internal | compile: OK | footprints: OK (28/28)

## Escalation

none
