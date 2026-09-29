# LM2776DBVR — Switched-capacitor voltage inverter, −Vin output (SOT-23-6)

SOURCE: model knowledge (Texas Instruments LM2776, common charge-pump inverter). PDF not
downloaded this session (deferred). Pin table below is read directly from the installed
KiCad symbol `Regulator_SwitchedCapacitor:LM2776`, confirmed present in
`/usr/share/kicad/symbols/Regulator_SwitchedCapacitor.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Function | Unregulated switched-capacitor inverter: VOUT ≈ −VIN |
| Input range | 2.7 V–5.5 V |
| Output current | up to 60 mA (meets design's "≥60 mA" requirement) |
| EN pin | Active HIGH — **required**, per sourcing's `[CRIT]` flag; do not float |
| Switching frequency | Internal fixed-frequency oscillator (class-typical ~150–250 kHz range — not independently re-verified this session) |

## Pinout (from KiCad symbol `Regulator_SwitchedCapacitor:LM2776`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | VOUT | power out | Inverted output, ≈ −VIN |
| 2 | GND | power in | Ground |
| 3 | VIN | power in | Input supply |
| 4 | EN | input | Enable, active HIGH — tie to VIN for always-on, or to a power-sequencing signal |
| 5 | C1+ | passive | Flying capacitor positive terminal |
| 6 | C1− | passive | Flying capacitor negative terminal |

## Notes

- U3 in `power_analog`: VIN = +5V_A rail, VOUT → post-filter (L1, C12/C13) → −5V_A rail
  for the AD8066 buffer's negative supply.
- Flying cap (C8/C9, 1 µF X7R, per sourced BOM "must be ≥1 µF X7R") between C1+/C1−.
- Input/output bulk caps (C10/C11, 10 µF) at VIN/VOUT per standard charge-pump layout.
- **EN pin (4) must be tied**, not left floating — this is the `[CRIT]` item the sourcing
  phase carried forward. Tie to VIN (pin 3) for simple always-on operation unless the
  architecture calls for sequencing with Q1/PWREN_N (check `power_analog` block notes at
  coding time — not resolved in this datasheet pass).
