# SX32Y012000BC1T001 — 12.000MHz AT-cut crystal, 12pF load (FT232H reference)

| Spec | Value |
|------|-------|
| Package | 3225 (3.2×2.5×0.7mm), 4-pad |
| Vcc / Vin range | N/A (passive crystal, no supply) |
| Key spec | 12.000000 MHz, **CL = 12pF exactly**, fundamental mode AT-cut |
| Max current / power | ESR ≤100Ω, Drive Level ≤100µW |
| Operating temp | −40°C to +85°C, ±10ppm tol / ±30ppm stability, ±3ppm/yr aging |

## Pinout / land pattern (from `datasheets/SX32Y012000BC1T001.pdf` page 6, "PIN CONNECT" table)

| Pin | Function |
|-----|----------|
| 1, 3 | Crystal terminal A (shorted together, diagonal pads) |
| 2, 4 | Labeled "GND" in the manufacturer's table — **see caution below, do not tie to system GND without verification** |

## Caution — "2,4: GND" label is ambiguous, do not blindly ground it

TKD's own pin-connect table literally reads `1,3 → Crystal`, `2,4 → GND`. The datasheet's
equivalent-circuit diagram (page 7) shows a standard **2-terminal** crystal model (series
C1-R1-L1 with shunt C0, two external nodes) — a genuine 2-terminal AT-cut crystal needs
**both** terminals driven independently by the oscillator IC (FT232H's XCSI/XCSO), each with
its own load cap to ground; neither terminal is normally tied directly to system ground in a
Pierce oscillator, because doing so kills the loop gain and the oscillator will not start.

**Most likely explanation**: pins 2/4 are the crystal's second electrode, which happens to
also be bonded internally to the conductive metal lid/case for shielding — TKD's table calls
that pad group "GND" because of the case bond, not because it should be wired to the board's
GND net. **Recommended treatment: wire pins 2/4 to FT232H's XCSO pin (with its own load cap
to true GND), exactly like a normal second crystal terminal — do not short pins 2/4 directly
to the GND net.** This is carried forward as unverified — confirm with a continuity check
against a physical sample, or against TKD's application note, before committing to
production. Getting this wrong means the FT232H's crystal oscillator will not start (dead
USB bridge, R-9-class failure).

## Notes

- **Confirms the 12pF load capacitance already used in the FT232HL_REEL crystal-cap
  recompute** (`FT232HL-REEL_SUMMARY.md`): Cext ≈ 16-18pF each for C13/C14.
- Standard part, EXACT-class symbol not needed for this passive 2-terminal crystal — use
  KiCad's generic `Device:Crystal` (2-pin) or `Device:Crystal_GNDC` symbol; footprint
  `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` already matches this 4-pad package (per sourced
  BOM), just be sure the SKiDL wiring only drives 2 electrical nets (A: pins 1+3, B: pins
  2+4), and connects B to XCSO/load-cap, not to GND, per the caution above.
- Datasheet PDF: `datasheets/SX32Y012000BC1T001.pdf` (TKD, verified correct part).
