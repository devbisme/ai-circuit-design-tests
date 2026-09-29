# AD9235BCPZ-40 — 12-Bit, 20/40/65 MSPS 3V A/D Converter (KEYSTONE, qualified 2nd source for U150/U250)

Datasheet obtained: `datasheets/AD9235BCPZ-40.pdf` (chipsfind.com mirror of ADI's Rev. D
AD9235 datasheet — verified by `fetch-datasheet.py`). Uses the same 33-pin (incl. EP)
pinout as AD9237BCPZ-40; no separate symbol pin table needed beyond what's below. Symbol
generated: `symbols/dual_adc_usb.kicad_sym:AD9235BCPZ-40` (33 pins incl. EP, EXACT).

| Spec | Value |
|------|-------|
| Package | LFCSP-32, 5x5mm, exposed pad (pad = pin 33, "recommended... soldered to ground plane") |
| Vcc / Vin range | AVDD = DRVDD = 3.0 V nominal |
| Key output spec | SNR ≈ 70.6 dB (per JLC spec sheet); DNL = ±0.35 LSB |
| Max current / power | Iq ≈ 55 mA (per JLC spec sheet) |
| Operating temp | −40°C to +85°C |

## Pinout (32-lead LFCSP, from datasheet Table 6 "Pin Function Descriptions")
Same physical pin numbering as AD9237; only the mnemonics at pins 1/3/5/6 differ.
| Pin | Name | Function |
|-----|------|----------|
| 1, 3, 5, 6 | DNC | **Do Not Connect** — no elaboration given (see Load-bearing facts) |
| 2 | CLK | Clock Input |
| 4 | PDWN | Power-Down (active high) |
| 7–14, 17–20 | D0(LSB)–D11(MSB) | Data Output Bits |
| 15 | DGND | Digital ground |
| 16 | DRVDD | Digital output driver supply — decouple to DGND with ≥0.1 µF (0.1 µF ∥ 10 µF recommended) |
| 21 | OTR | Out-of-Range flag |
| 22 | MODE | Data format / DCS mode select |
| 23 | SENSE | Reference mode select |
| 24 | VREF | Voltage reference in/out |
| 25 | REFB | Differential reference (−) |
| 26 | REFT | Differential reference (+) |
| 27, 32 | AVDD | Analog power |
| 28, 31 | AGND | Analog ground |
| 29 | VIN+ | Analog input (+) |
| 30 | VIN− | Analog input (−) |
| 33 (EP) | EPAD | Exposed pad — explicitly documented: "recommended that the exposed paddle be soldered to the ground plane... increased reliability... maximum thermal capability" |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| DNC pin count/location | Pins 1, 3, 5, 6 = "Do Not Connect" | datasheet Table 6, Note 1 ("DNC = DO NOT CONNECT") — **verified** |
| DNC pin isolation/hazard note | **None given.** The datasheet states only "Do Not Connect" with no further qualifier (no statement that these pins are internally bonded to sensitive test/substrate nodes, and no statement that they are safely floating/unbonded either) | datasheet Table 6 — **verified absence of elaboration**, checked entire Table 6 and Figure 4 note block |
| 2nd-source pin-compatibility claim | AD9237's own datasheet states "The AD9237 is pin compatible to the AD9235" as a Product Highlight | AD9237BCPZ-40 datasheet p.1 — **verified**, manufacturer-endorsed |
| Corrected differing-pin count | Only 2 physically differing functional pins vs. AD9237 (pin 1 = MODE2 there, DNC here; pin 3 = OE there, DNC here). Pins 5 and 6 are DNC on **both** parts — not a difference at all, correcting `sourced_bom.md`'s claim of 3 differing pins (1/3/5) | Cross-checked both datasheets' Table 6 / Pin Function tables — **verified** |

## Verdict on the keystone question (sourcing's decision #2 / #4)

**This is UNVERIFIED, not a confirmed drop-in for pins 1 and 3.** Both AD9237's MODE2
(pin 1) and OE (pin 3) are pins that a real board must strap to a static DC level for
correct AD9237 operation (they are not left floating even on the primary part — see
`AD9237BCPZ-40_SUMMARY.md`). If those two nets are wired as direct PCB traces to a rail
(AVDD/AGND) on the shared footprint — which the AD9237 electrical test conditions imply is
the simplest/expected implementation — then populating AD9235 on the same footprint would
tie AD9235's DNC pins 1 and 3 to that same static rail. **Neither datasheet states whether
AD9235's DNC pins tolerate an externally-applied DC level.** The "Do Not Connect" label is
unqualified in both documents; ADI's own pin-compatibility claim is strong circumstantial
evidence this is safe (ADI markets it as a direct substitution path), but it is not an
explicit statement addressing this exact scenario.

**Recommendation for the coder:** route MODE2 (pin 1) and OE (pin 3) straps through
DNP-able 0 Ω resistors (or small series resistors) rather than direct copper traces, so
that if AD9235 is substituted, those two resistors can simply be left unpopulated —
leaving AD9235's DNC pins genuinely floating with zero risk, at the cost of 2 extra
0402 footprints. This turns an unverified assumption into a designed-in safe option. Do
not treat the second source as a "zero-change" drop-in without this mitigation, or without
sourcing obtaining ADI's explicit DNC-tolerance confirmation (not found in either datasheet
obtained this pass).

## Notes
- Pins 5 and 6 are DNC on both parts, so they carry no swap risk either way — leave
  floating regardless of which ADC is populated.
- All other facts (power, decoupling, EP grounding, VIN±/CLK/data bus/REF network) are
  identical between AD9235 and AD9237 per both datasheets' pin tables — the second source
  is a true drop-in for every pin except 1 and 3.
