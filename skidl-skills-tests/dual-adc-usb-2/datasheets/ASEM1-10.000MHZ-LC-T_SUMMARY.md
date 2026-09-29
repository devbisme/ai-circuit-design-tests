# ASEM1-10.000MHZ-LC-T — 10.000 MHz CMOS XO, ±25 ppm, low jitter (3225, 4-pad)

SOURCE: model knowledge (Abracon ASEM1 series, common low-jitter CMOS crystal
oscillator). PDF not downloaded this session (deferred). Pin table below is read
directly from the installed KiCad symbol `Oscillator:ASE-xxxMHz`, confirmed present in
`/usr/share/kicad/symbols/Oscillator.kicad_sym`.

| Spec | Value |
|------|-------|
| Package | 3225 (3.2×2.5 mm), 4-pad SMD |
| Frequency | 10.000 MHz |
| Frequency stability | ±25 ppm (per sourced BOM, `[FIXED SPEC][CRIT]` — ENOB-limiting, R-01) |
| Jitter | ≤5 ps RMS (per sourced BOM `[FIXED SPEC]`) |
| Supply | 3.3 V typical for this series |
| Output | CMOS square wave |
| EN pin | Present — internal pull-up typical for this series (floating usually defaults enabled), but tie explicitly, see Notes |

## Pinout (from KiCad symbol `Oscillator:ASE-xxxMHz`, standard 4-pad XO)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | EN | input | Enable/standby (tri-states output when low, on many parts in this class) |
| 2 | GND | power in | Ground |
| 3 | OUT | output | Clock output |
| 4 | Vdd | power in | Supply, 3.3 V (from V3V3_CLK, via FB6 ferrite bead) |

## Notes

- X1 in `clock_gen`: this is the master sample clock for both ADC channels — the
  single highest-risk part for the design's ENOB budget (R-01, per architecture).
- **EN pin (1) must be tied explicitly**, not left floating — tie to Vdd (pin 4) for
  always-on. Do not rely on an assumed internal pull-up without confirming against the
  datasheet; floating a control pin is an ERC risk regardless.
- Output (pin 3) feeds R10 (33 Ω series termination) before fanning out to the two
  74LVC1G34 buffers (U16/U17), which each drive one ADC channel's CLK pin through their
  own 33 Ω terminations (R11/R12).
- Decoupling: 100 nF (part of C22/C23) directly at Vdd, plus 1 µF bulk (C24).
- **Vetted drop-in alternates** (per sourcing, same jitter class): SiT8008BI-73-33S-
  10.000000, SG-8018CA-10M — verify footprint pin-compatibility before swapping (not
  independently confirmed pin-for-pin this session).
