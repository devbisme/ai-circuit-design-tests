---
phase: 05_blocks/power_analog
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - power_analog

## Decisions
1. Signature unchanged: `power_analog(v5, v3v3a, vp4a, vn4a, gnd)`.
2. Consumes `v5`. Drives `v3v3a` (U701 OUT), `vp4a` (U702 OUT+), `vn4a` (U702 OUT-): all `power_out` pins in the KiCad symbols, so no flags are needed on them.
3. Local `+5VA` = FB701 output (passive): block sets `.drive = POWER` + `#FLG701` PWR_FLAG. It feeds U701 IN/EN, U702 VIN/EN+/EN-, C702 1u, C705 2.2u.
4. U701 LP5907-3.3: OUT -> +3V3A, C703 1u (rail total <= 10 uF incl. consumer caps).
5. U702 LM27762 (symbol names): C+/C- -> `LM_C1P`/`LM_C1N` with C706 1u flying; CP -> `LM_CP` with C707 4.7u; OUT+ -> +4V0A (C708 2.2u), OUT- -> -4V0A (C709 2.2u); FB+ `LM_FBP` R701 232k top / R702 100k bottom -> +3.984 V; FB- `LM_FBN` R703 226k top / R704 100k bottom -> -3.977 V. GND, PAD(13) -> GND; PGOOD(1, unused) -> `LM_PGOOD` -> R705 100k -> +4V0A (rev 2).

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.
- Rev 2: U702 PGOOD (pin 1, open drain) no longer tied to GND (clashed with GND `#FLG001`). DS says 'connect to ground if not used' but does not permit floating, so PGOOD -> local net `LM_PGOOD` -> **new R705 100k (0402WGF1003TCE / C25741, 0402) -> +4V0A**. R705 is NOT yet in sourcing/sourced_bom.csv: add it to the `R602,R702,R704` row.

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/power_analog.py` | block |

## Next phase must
- Call: `power_analog(v5=V5, v3v3a=V3V3A, vp4a=VP4A, vn4a=VN4A, gnd=GND, tag='power_analog')` with nets `+5V`, `+3V3A`, `+4V0A`, `-4V0A`, `GND`.
- No top-level `.drive` needed for `+3V3A`/`+4V0A`/`-4V0A` (driven here); `+5V` is driven by usb_c_input.

## Carried forward
- U701 pin 4 (N/C) left unconnected intentionally.
- BOM reconciliation: R705 (100k, 0402WGF1003TCE, C25741) added in rev 2; sourced_bom.csv row `R602,R702,R704` needs R705. DS recommends 10k to VIN for a used PGOOD; 100k to +4V0A per fix work order (pin unused, value non-critical).
- C702 + C705 count toward the VBUS-domain <= 10 uF budget; no extra bulk on +5VA.
- Sequencing of +3V3A vs +3V3 for ADS5231 AVDD/VDRV (+/-10 ms) not enforced here.

## Do not redo
- MPNs/footprints verbatim from sourced_bom.csv; divider values from net plan.

## Receipt
power_analog (rev 2): 16 parts (+1 PWR_FLAG), 12 nets (+5V, +5VA, +3V3A, +4V0A, -4V0A, LM_C1P, LM_C1N, LM_CP, LM_FBP, LM_FBN, LM_PGOOD, GND); LCSC fields set; compile OK; footprints from BOM; signature changed: no.
