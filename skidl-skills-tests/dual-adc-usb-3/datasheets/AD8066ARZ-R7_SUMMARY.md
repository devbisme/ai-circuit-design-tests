# AD8066ARZ-R7 — Dual, High Performance 145 MHz FastFET Op Amp (SOIC-8)

Source: `datasheets/AD8066ARZ-R7.pdf` (ADI AD8065/AD8066 combined datasheet, Rev. I,
28 pages, DigiKey mirror — full document).

| Spec | Value |
|------|-------|
| Package | 8-Lead SOIC_N (R-8) — this BOM's grade. Also available SOT-23-5 (AD8065 only) / MSOP-8. |
| Vcc / Vin range | Wide supply: 5V to 24V total (dual-supply e.g. ±4.2V architecture use is within range) |
| Key output spec | 145 MHz −3dB BW (G=+1), 180 V/µs slew rate (G=+2, typ) / 130 V/µs min — architecture needs 22.8 V/µs bare, ample margin. **No phase reversal.** |
| Max current / power | 6.4 mA/amplifier typical supply current; output sources/sinks up to 30 mA, rail-to-rail-output capable within 0.5V of either supply |
| Operating temp | –40°C to +85°C |

## Pinout (AD8066, 8-Lead SOIC, TOP VIEW)

| Pin | Name | Function |
|-----|------|----------|
| 1 | VOUT1 | Output, Amplifier 1 |
| 2 | –IN1 | Inverting Input, Amplifier 1 |
| 3 | +IN1 | Non-inverting Input, Amplifier 1 |
| 4 | –VS | Negative Supply |
| 5 | +IN2 | Non-inverting Input, Amplifier 2 |
| 6 | –IN2 | Inverting Input, Amplifier 2 |
| 7 | VOUT2 | Output, Amplifier 2 |
| 8 | +VS | Positive Supply |

(Note: this is the **AD8066** dual pinout, distinct from the single-channel AD8065 pinout
also shown on the same datasheet page — do not mix them up if referencing the PDF directly.)

## Notes

- **Phase-reversal risk (R9) — resolved.** Datasheet states explicitly: *"The amplifiers
  operate as if they have a rail-to-rail input and exhibit no phase reversal behavior for
  common-mode voltages within the power supply."* Architecture's clamp (1kΩ series + BAV199
  to the ±4.2V rails) keeps the op-amp's input pin within (or only ~0.5V beyond, clamped by
  the diode) the ±4.2V supply during a +50V input fault — squarely inside "within the power
  supply," so **no phase-reversal risk under the fault condition R9 was worried about.**
  Input Overdrive Recovery Time (G=+1, ±5.5V step) is 175 ns typ — fast, not a design blocker.
- **Application:** this design uses one AD8066 die per channel for two functions per
  Architecture Decision 4 — a unity-gain buffer stage and a second stage configured as a
  Sallen-Key anti-alias filter section (both halves of the same dual package, per
  `analog_frontend` block, refs U7×2 instances → 2 physical AD8066 packages total, one per
  channel). Confirm buffer uses Amp A (pins 1–4) and Sallen-Key uses Amp B (pins 5–8), or
  vice versa, per whichever layout minimizes crossing in `net_plan.md`.
- Decoupling: standard practice per datasheet's own test circuits — 4.7µF bulk + 0.1µF local
  on both +VS and –VS.
- Slew-rate margin: architecture's floor requirement is 22.8 V/µs (±0.909V at 4MHz); this
  part's 130 V/µs min (G=+2) / 180 typ is 5.7–7.9× that floor — comfortable.
