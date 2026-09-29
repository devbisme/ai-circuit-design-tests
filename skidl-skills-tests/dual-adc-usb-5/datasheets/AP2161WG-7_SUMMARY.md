# AP2161WG-7 — 1 A current-limited high-side power switch, ACTIVE-LOW enable (U9)

Replaces Q1 (HL2301A P-FET) as of architecture revision 2. Primary source:
`datasheets/AP2161WG-7.pdf` — Diodes Inc. DS31564 Rev. 9, "AP2161/AP2171".

| Spec | Value |
|------|-------|
| Package | SOT25 = **SOT-23-5** (`Package_TO_SOT_SMD:SOT-23-5`) |
| Vin range | 2.7–5.5 V |
| Rds(on) | 95 mΩ (Vin = 5 V, Iout = 1 A, 25 °C) |
| Over-load current limit | **1.1 / 1.5 / 1.9 A** (min/typ/max, −40…+85 °C) |
| Short-circuit current limit | 1.2 A typ |
| Recommended max continuous load | **1.0 A** |
| Turn-on rise time | 0.6 ms typ (controlled slew — this is the inrush control) |
| EN polarity | **Active LOW (AP2161).** AP2171 is the pin-identical ACTIVE-HIGH twin |
| EN thresholds | VIH **2.0 V min** to Vin · VIL **0.8 V max** · leakage 1 µA max |
| FLG | Open-drain fault flag, active low, 7 ms deglitch |
| Other | Reverse-current blocking, UVLO, thermal limiting, 4 kV HBM |
| Temp | −40 °C to +85 °C |

## Pinout (SOT-23-5) — matches `Power_Management:AP2161W` exactly

| Pin | Symbol name | Net in `digital_power` |
|-----|-------------|-----------------------|
| 1 | `OUT` | `+5V_SW` |
| 2 | `GND` | `GND` |
| 3 | `~{FLG}` (open collector) | `NC` — no consumer; available for a fault LED later |
| 4 | `~{EN}` (input, active low) | `PWREN_N` |
| 5 | `IN` (power_in) | `+5V_IN` |

**Wire by pin NUMBER.** The symbol's pin names carry KiCad overbar markup (`~{EN}`,
`~{FLG}`), so name lookup is fragile; numbers are not.

## Why this part (architecture decision 13)

FT232H PWREN# is **active-low** and swings 0 ↔ 3.3 V. This part's EN is active-low and
**GND-referenced**, so PWREN# drives it directly: 3.3 V > VIH 2.0 V = **off**, 0 V <
VIL 0.8 V = **on**. No inverter, no level shifter, no polarity trap. The predecessor P-FET
could not turn off at all (its source sat at 5 V, so 3.3 V on the gate gave Vgs = −1.7 V,
past a −0.4…−1.0 V threshold).

`usb_bridge`'s existing 10 kΩ pull-up to 3V3 on `PWREN_N` (`R_pwren`) is what holds EN high
= switch OFF at plug-in and through FT232H reset. **No separate gate pull-up is needed —
rev 1's R3 (100 k to `+5V_IN`) is deleted.** R6, the DNP 0 Ω from `PWREN_N` to GND, still
works as the bring-up escape (`design_risks.md` R-9): populating it pulls EN low = ON.

## Sourcing

C176957, Extended tier, stock 8 848, $0.211 @1 / $0.165 @50. Second source
WS4612EBB-5/TR (C42404603, 1 A, 60 mΩ, active-low, stock 8 657) — electrically fine but
**has no KiCad symbol**, so it costs a symbol-generation step. **Never substitute AP2171W**:
same pins, active-HIGH enable, and it silently re-breaks SPEC P4.
