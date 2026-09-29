# OPA836IDBVR — Single voltage-feedback op-amp, 205 MHz, 3.3V single-supply (SOT-23-6)

SOURCE: Texas Instruments OPA836 Data Sheet (facts confirmed via WebSearch synthesis
quoting the datasheet's own DBV pin diagram and feature/spec summary). Attempted PDF
download deferred to Phase 2 (`https://www.ti.com/lit/ds/symlink/opa836.pdf`). **No
KiCad symbol exists for this part, and — per the sourcing handoff's explicit warning —
this SOT-23-6 single-op-amp pinout is vendor-specific, NOT a safe generic placeholder.
This pin table below IS the kipart input; do not substitute a different SOT-23-6
op-amp's pinout.**

| Spec | Value |
|------|-------|
| Package | SOT-23-6 (DBV) |
| Channels | 1 (single), voltage-feedback (VFB) topology |
| Supply | 2.5 V–5.5 V single supply, or ±1.25 V–±2.75 V dual supply — this design uses **single-supply 3.3 V** (this is the ADC's over-voltage protection stage, must stay 3.3 V single-supply per architecture — do not substitute a ±5 V-only part) |
| Quiescent current | ~1 mA/channel (ultra-low-power class) |
| Unity-gain bandwidth | 205 MHz |
| Output | Rail-to-rail output; **negative-rail input** (input common-mode range includes the negative supply rail — important for this design's level-shift/summing topology) |
| Operating temp | Industrial (confirm exact limits against full datasheet before extreme-environment use — not itself quoted this session) |

## Pinout (SOT-23-6, DBV package)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | VOUT | output | Amplifier output |
| 2 | VS− | power | Negative supply (tie to GND for single-supply 3.3 V operation) |
| 3 | VIN+ | input | Non-inverting input |
| 4 | VIN− | input | Inverting input |
| 5 | PD | input | Power-down (amplifier disable) — active-low per typical TI PD convention on this family; **tie to VS+ (3.3 V) for normal always-on operation.** Confirm active-high vs active-low polarity against the datasheet before board spin — polarity was not itself quoted this session, only the pin's existence and function. |
| 6 | VS+ | power | Positive supply, 3.3 V in this design |

## Notes

- This design uses OPA836 as U_b in `afe_channel`: the MFB (multiple-feedback) filter +
  level-shift stage that takes the ±5 V AD8066 buffer's output and re-references it into
  the AD9235's 3.3 V-compatible, 1.5 V-centered, 2 V p-p single-ended input range. Gain =
  −2 per the architecture (`A3 gain = −2`).
- **PD pin (5):** if left unused, tie firmly to VS+ (3.3 V) rather than floating — even if
  the internal pull state defaults to "enabled," an unterminated CMOS-level control input
  is an ERC/floating-pin risk. Do not leave NC.
- Decoupling: shares the `afe_channel` block's C_dec budget (100 nF + 1 µF) with U_a
  (AD8066) — place a dedicated 100 nF directly at pin 6 (VS+) for this op-amp specifically
  given its high (205 MHz) bandwidth; do not rely solely on the AD8066's decoupling network
  three pins away.
- VS− (pin 2): tie directly to the local analog/AFE ground plane (single-supply operation
  — this is NOT the −5 V rail; do not confuse with AD8066's −VS pin in the same block).
- **Confidence flag:** the pin table (names/positions 1–6) is corroborated directly from
  the TI datasheet's own pin-diagram text as returned by search, and is high confidence.
  The PD pin's active-high/active-low polarity is a specific claim not independently
  re-verified this session — flagged explicitly per the "no silent guessing" instruction;
  verify against the OPA836 datasheet's Pin Functions table before finalizing the PD tie.
