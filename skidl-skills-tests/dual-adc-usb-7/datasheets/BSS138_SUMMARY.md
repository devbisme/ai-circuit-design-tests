# BSS138 — N-channel MOSFET (power_tree, Q1)

| Spec | Value |
|------|-------|
| Package | SOT-23 |
| Vcc / Vin range | VDS 50V |
| Key output spec | Vgs(th) = 1.2V (meets architecture's ≤1.5V requirement), RDS(on) 1.1Ω@10V / 1.2Ω@4.5V |
| Max current / power | ID 340mA continuous, Pd 350mW |
| Operating temp | −55°C to +150°C |

## Notes
- Confirmed Vgs(th)=1.2V from jlc_get_part electrical specs (C7420339), meeting the
  architecture's ≤1.5V requirement for the level-shift/switch application at Q1.
- Existing symbol used: `Transistor_FET:BSS138` — standard part, not regenerated.
- Datasheet: `datasheets/BSS138.pdf` (hongjiacheng).
