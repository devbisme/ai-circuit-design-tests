---
phase: 05_blocks/afe_channel
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - afe_channel

## Decisions
1. Signature unchanged: `afe_channel(ch, vin, ain_p, ain_n, adc_cm, vp4a, vn4a, v3v3a, gnd)`.
   `ch` must be the string "A" (refs 1xx, local nets `*_A`) or "B" (refs 2xx, `*_B`); anything else raises ValueError.
2. Topology and values exactly per `architecture/net_plan.md` Block 4 (matches `architecture/afe_nominal.cir`).
3. Drives: `ain_p`, `ain_n` (THS4551 OUT+/OUT- via 46.4R, 1.2 nF across). Senses only: `vin` (BNC centre),
   `adc_cm` (THS4551 VOCM input, driven by ADC CM). Consumed: `vp4a`, `vn4a`, `v3v3a`, `gnd`.
4. Pin handling: OPA2810 by symbol names (VIN1+/VO1/...); OPA810, THS4551, BAV99 by pin number
   (BAV99: 1 -> -4V0A, 2 -> +4V0A, 3 -> BUFIN, per librarian). Polarity: SKB -> MFX_P -> IN+, feedback to OUT-.
5. Every part has `fields["MPN"]` from sourced_bom.csv; footprints verbatim (C110/C111 0603).

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/afe_channel.py` | @SubCircuit afe_channel, 41 parts per instance |

## Next phase must
- Emit exactly:
  `afe_channel(ch="A", vin=VIN_A, ain_p=AIN_AP, ain_n=AIN_AN, adc_cm=ADC_CM, vp4a=P4V0A, vn4a=N4V0A, v3v3a=P3V3A, gnd=GND, tag='afe_ch_a')`
  `afe_channel(ch="B", vin=VIN_B, ain_p=AIN_BP, ain_n=AIN_BN, adc_cm=ADC_CM, vp4a=P4V0A, vn4a=N4V0A, v3v3a=P3V3A, gnd=GND, tag='afe_ch_b')`
  (net names `+4V0A`, `-4V0A`, `+3V3A`, `GND`, `ADC_CM`, `VIN_A`... are created at top level).
- `+4V0A`, `-4V0A`, `+3V3A`, `GND` are only consumed here (power_in pins) -> driven by power_analog
  regulator outputs; set `.drive = POWER` at top level if ERC flags them.
- `ADC_CM` is driven by ADC U301 CM; THS4551 VOCM is an input. `VIN_A/B` driven only by the BNC (passive) - expect no ERC driver issue.

## Carried forward
- Intentional NC: U103/U203 pin 1 (FB-) and pin 4 (FB+) (output-typed internal taps; BOM decision, not confirmed by datasheet text).
- THS4551 ~PD (pin 12) tied to +3V3A (always on); EP pin 17 and VS- 13-16 to GND (single 3.3 V supply).
- Decoupling included in block: C113/C115 (0.1u) + C120 (2.2u) on +4V0A, C114/C116 + C121 on -4V0A,
  C117 (0.1u) + C118 (1u) on +3V3A, C119 10 nF on ADC_CM (ADC block owns C303/C304 on ADC_CM).
- Trimmer C102/C202 rotor pad unknown (librarian): layout should put rotor on the ATT side if identified.
- BAV199 uses `Diode:BAV99` symbol (names K/A/K misleading; pin numbers are authoritative).

## Do not redo
- Values/MPNs/footprints taken verbatim from sourced_bom.csv; filter values must not be rounded.

## Receipt
afe_channel: 41 parts/instance (82 total), 15 local + 8 interface nets/instance; py_compile OK;
footprints from CSV verbatim (hook raised no error); signature changed: no.
