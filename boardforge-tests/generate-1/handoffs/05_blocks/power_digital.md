---
phase: 05_blocks/power_digital
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - power_digital

## Decisions
1. Signature unchanged: `power_digital(v5, v3v3, v1v2, gnd)`.
2. Consumes `v5`. Drives `v3v3` (buck output through L601, a passive: block sets `v3v3.drive = POWER` + `#FLG601` PWR_FLAG) and `v1v2` (U602 OUT is a `power_out` pin; no flag needed).
3. U601 TLV62569DBV: VIN+EN -> +5V, SW -> `SW_3V3` -> L601 -> +3V3, FB -> `FB_3V3`. Divider R601 453k / R602 100k -> 3.318 V; C604 6.8 pF across R601. C601 4.7u input, C602/C603 10u output.
4. U602 TLV75712: IN+EN -> +3V3, OUT -> +1V2; C605 1u in, C606 1u out.
5. D601 power LED: +3V3 -> R604 1k -> `LED_PWR` -> D601 A, K -> GND (1k kept per BOM, ~0.2 mA, dim).
6. **L601 saturation check (TMS252012ALM-2R2MTAA, Isat 2.8 A):** ripple dI = 3.3 x (1 - 3.3/5) / (2.2 uH x 1.5 MHz) = 0.34 A pp; worst-case +3V3 load 0.36 A (design_risks #11) -> peak 0.53 A, 5x margin to Isat. TLV62569DBV ILIM = 3 A typ (SLVSDT3 EC table, no min/max): inductor can saturate only in an output-short/overload; acceptable (current limit still terminates the pulse). PASS for normal operation.

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/power_digital.py` | block |

## Next phase must
- Call: `power_digital(v5=V5, v3v3=V3V3, v1v2=V1V2, gnd=GND, tag='power_digital')` with nets `+5V`, `+3V3`, `+1V2`, `GND`.
- `+5V` is driven/flagged by usb_c_input; `+3V3`, `+1V2` driven here - no top-level `.drive` needed for them.

## Carried forward
- U602 pin 4 (NC, no_connect in symbol) left unconnected intentionally.
- C601 4.7 uF counts toward the VBUS-domain <= 10 uF budget; do not add bulk on +5V.
- Layout: hot loop C601-U601-L601 tight, buck far from AFE.
- Power sequencing vs +3V3A (ADS5231 AVDD/VDRV within +/-10 ms) is not enforced here.

## Do not redo
- MPNs/footprints verbatim from sourced_bom.csv; L601 Isat check done above.

## Receipt
power_digital: 13 parts (+1 PWR_FLAG), 7 nets (+5V, SW_3V3, FB_3V3, +3V3, +1V2, LED_PWR, GND); compile OK; footprints from BOM; signature changed: no.
