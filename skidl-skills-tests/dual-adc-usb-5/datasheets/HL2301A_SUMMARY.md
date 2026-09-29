# HL2301A — P-channel MOSFET load switch (Q1)

| Spec | Value |
|------|-------|
| Package | SOT-23 |
| Vds max | 20V |
| Key spec | Rds(on) 90mΩ typ @ Vgs=−4.5V,Id=−2.8A; 110mΩ @ Vgs=−2.5V,Id=−2A |
| Vgs(th) | −0.4 to −1.0V (typ −0.7V) |
| Max current | Id 2.3A continuous, Pd 700mW |
| Operating temp | −55°C to +150°C |

## Pinout (SOT-23, from EasyEDA/JLC symbol data — standard P-MOSFET SOT-23 pin order,
confirmed consistent with the datasheet's electrical table conventions; the pin diagram page
itself is a graphic and did not extract as searchable text in this pass)

| Pin | Name | Function |
|-----|------|----------|
| 1 | G | Gate — driven by FT232H PWREN# per architecture decision 9 |
| 2 | S | Source — to `+5V_IN` |
| 3 | D | Drain — to `+5V_SW` |

## Notes

- **Rds(on) confirmed against the real datasheet electrical table** (`datasheets/HL2301A.pdf`):
  90mΩ typ at the exact bias point (Vgs=−4.5V) sourcing cited, meets the architecture's
  ≤100mΩ spec with margin. At the lighter Vgs=−2.5V bias, Rds(on) rises to 110mΩ — if PWREN#
  or the gate-pull network doesn't fully swing gate-to-source voltage to ~4.5V, on-resistance
  degrades; verify the gate-drive swing in `digital_power` reaches at least −4.5V Vgs.
- Q1's gate is driven by FT232H PWREN# (open-drain style, active during USB attach before
  enumeration completes) — architecture's SPEC-P4 compliance path (decision 9). The sourced
  BOM's R6 "DNP 0Ω gate-to-GND escape resistor" (R-9 risk) must not be omitted — it's a board
  bring-up safety net, not decoration.
- Preferred tier, stock 90,589+ at sourcing/datasheet time — no supply risk.
