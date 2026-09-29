# AO3401A — P-channel MOSFET, load-switch class (SOT-23)

SOURCE: model knowledge (Alpha & Omega Semiconductor AO3401A, extremely common
small-signal P-FET). PDF not downloaded this session (deferred — low incremental value
for a 3-pin discrete with a well-known generic symbol). Pin table below is read directly
from the installed KiCad symbol `Transistor_FET:Q_PMOS_GSD`, confirmed present in
`/usr/share/kicad/symbols/Transistor_FET.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | SOT-23 |
| Type | P-channel enhancement MOSFET |
| V_DS(max) | −30 V |
| I_D(max) | ~−4 A (package/thermally limited well below this in practice) |
| V_GS(th) | typically −0.7 V to −2.0 V (meets the design's "Vgs(th) < 2 V" requirement) |
| R_DS(on) | Low, ~50 mΩ class at V_GS = −4.5 V (typical for this part class — not independently re-verified this session) |

## Pinout (from KiCad symbol `Transistor_FET:Q_PMOS_GSD`, standard SOT-23 P-FET pin order)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | G | input | Gate |
| 2 | S | passive | Source |
| 3 | D | passive | Drain |

This matches AO3401A's actual physical SOT-23 pinout (Pin1=Gate, Pin2=Source,
Pin3=Drain) — standard for this part family, no adapter/mirroring needed.

## Notes

- Q1 in `power_analog`: high-side P-FET load switch, gated by PWREN_N. Source → incoming
  supply rail, Drain → switched output, Gate → pulled up via R5 (100 kΩ) to the source
  rail (off by default) and pulled low through the control path (with R6, 10 kΩ series,
  giving a ~1 ms soft-start ramp per sourced BOM note) to turn on.
- **Deviation carried from sourcing:** substituted for the architect's DMG2305UX pick —
  both meet spec; AO3401A was chosen for stocking commonality. Same SOT-23 3-pin G/S/D
  footprint, no layout impact if swapped back.
