# THS4551IRGTR — Fully-Differential Amplifier (FDA), RGT-16 VQFN

Source: `datasheets/THS4551IRGTR.txt` (TI SBOS778D, full document, already extracted).

| Spec | Value |
|------|-------|
| Package | RGT0016C — 16-pin VQFN, 3.1×3.1mm body (2.9–3.1mm), 0.5mm pitch, 1.0mm max height |
| Vcc / Vin range | Single-supply 2.7V–5.4V (VS+ – VS– up to 5.5V abs max); architecture uses this as the ±4.2V-rail-referenced FDA (8.4V total exceeds the 5.5V abs max — **see Notes, this needs re-checking**) |
| Key output spec | Rail-to-rail output, adjustable VOCM pin, differential architecture with dedicated FB+/FB– feedback-sense pins |
| Max current / power | Not extracted — not the binding constraint here |
| Operating temp | Not extracted from this excerpt of the doc; TI industrial grade typical –40 to 125°C for THS4551 family |

## Pinout (RGT package, 16-pin VQFN, Table 6-1)

| Pin | Name | Function |
|-----|------|----------|
| 1 | FB– | Inverting output feedback (O) |
| 2 | IN+ | Non-inverting amplifier input (I) |
| 3 | IN– | Inverting amplifier input (I) |
| 4 | FB+ | Non-inverting output feedback (O) |
| 5, 6, 7, 8 | VS+ | Positive power supply |
| 9 | VOCM | Common-mode voltage input (I) — sets output common mode |
| 10 | OUT+ | Non-inverting amplifier output (O) |
| 11 | OUT– | Inverting amplifier output (O) |
| 12 | PD | Power-down: logic low = power off, logic high = normal operation |
| 13–16 | VS– | Negative power supply |
| EPAD (no pin #) | Exposed thermal pad | Electrically isolated from the die but **must** be connected to a power or ground plane, not floated (datasheet explicit note) |

## Notes

- **EP dimension confirmed — closes `03_sourcing.md` gap item #1 (THS4551 part).** Package
  drawing `RGT0016C` (mechanical section, PACKAGE OUTLINE, TI doc rev 4222419/E 07/2025):
  **exposed thermal pad = 1.68mm ± 0.07mm, square** (SYMM marks on both axes). Sourced
  footprint assumed `EP1.7x1.7mm` as "TI's typical value for this package family, not
  confirmed" — **now confirmed correct to within 0.02mm**, no footprint change needed.
- **PD (pin 12) must be tied to logic HIGH for normal operation** — do not leave floating; if
  no PD control signal is planned, tie directly to the amp's positive supply net.
- **VS+/VS– abs max is only 5.5V total.** The architecture routes this device between the
  ±4.2V analog rails per `02_architecture.md` block manifest (`analog_frontend` block, VPOS/
  VNEG = +4V2A/–4V2A), which is **8.4V total — exceeds the 5.5V absolute maximum by 2.9V.**
  This is a datasheet-vs-architecture conflict the sourcing phase did not catch (sourcing
  only verified stock/footprint, not supply-voltage compatibility). **Flagging this
  explicitly rather than silently resolving it** — see `## Decisions` in the phase handoff;
  the block coder must not wire THS4551 VS+/VS– directly to ±4.2V without the architect
  re-confirming the supply plan (e.g. a single-supply-referenced FDA topology, or a
  lower-voltage local rail) — this is now escalated, not fixed here.
- FB+/FB– are TI's Enhanced Feedback pins used for the MFB (multiple-feedback) filter
  topology — matches architecture's use of THS4551 as "a differential MFB section" (Decision
  4). Connect the MFB network's feedback resistor/cap directly to FB+/FB–, not OUT+/OUT–,
  per TI's application circuit (see datasheet §9, "Multiple Feedback Filter" discussion
  around line 2200+ of the extracted text, and the ADS127L01 interface example figure near
  the front of the document for the general filter-into-ADC pattern this design follows).
- VOCM pin: architecture uses THS4551 for "single-ended-to-differential conversion at gain
  1.10" (Decision 4) referencing the ADC's common-mode requirement — tie VOCM to the AD9235's
  VCM/CML reference per the `adc_pair` block's VCM divider, consistent with standard
  ADC-driver practice (this pairing is implied by the architecture, not restated verbatim in
  the THS4551 datasheet).
