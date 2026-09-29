# AD9237BCPZ-40 — 12-Bit, 20/40/65 MSPS 3V Low Power A/D Converter (KEYSTONE, primary ADC, U150/U250)

Datasheet obtained: `datasheets/AD9237BCPZ-40.pdf` (Farnell-hosted mirror of ADI's
"Preliminary Technical Data" AD9237 datasheet — verified by `fetch-datasheet.py` as the
correct part; this is the original/older AD9237 datasheet revision, not the current
analog.com-hosted PDF, which repeatedly timed out from this environment after 3 attempts
on 2 different URLs). Symbol generated: `symbols/dual_adc_usb.kicad_sym:AD9237BCPZ-40`
(33 pins incl. EP, verified EXACT against datasheet Table).

| Spec | Value |
|------|-------|
| Package | LFCSP-32, 5x5mm, exposed pad (pad = pin 33) |
| Vcc / Vin range | AVDD = DRVDD = 3.0 V nominal (single 3 V supply) |
| Key output spec | SNR = 66.5 dBc to Nyquist; ENOB = 10.5 bits; DNL = ±0.5 LSB |
| Max current / power | 90 mW @ 20 MSPS; 135 mW @ 40 MSPS; 190 mW @ 65 MSPS — **verified**, confirms architecture's ≤90 mW assumption at this design's ~10 MSa/s clock (below the 20 MSPS test point, so power is ≤90 mW) |
| Operating temp | −40°C to +85°C |

## Pinout (32-lead LFCSP, exactly as datasheet Table "PIN FUNCTION DESCRIPTIONS")
| Pin | Name | Function |
|-----|------|----------|
| 1 | MODE2 | SHA Gain Select and Power Control — **must be strapped**, see Notes |
| 2 | CLK | Clock Input |
| 3 | OE | Output Enable, **active low** — must be strapped, see Notes |
| 4 | PDWN | Power-Down (active high) |
| 5 | DNC | Do Not Connect |
| 6 | DNC | Do Not Connect |
| 7–14, 17–20 | D0(LSB)–D11(MSB) | Data Output Bits |
| 15 | DGND | Digital ground |
| 16 | DRVDD | Digital output driver supply |
| 21 | OTR | Out-of-Range flag |
| 22 | MODE | Output data format / DCS select — must be strapped |
| 23 | SENSE | Reference mode select |
| 24 | VREF | Voltage reference in/out |
| 25 | REFB | Differential reference (−) |
| 26 | REFT | Differential reference (+) |
| 27, 32 | AVDD | Analog power |
| 28, 31 | AGND | Analog ground |
| 29 | VIN+ | Analog input (+) |
| 30 | VIN− | Analog input (−) |
| 33 (EP) | EP | Exposed pad — **must be soldered to ground plane** (thermal/ground), added as its own pin in the generated symbol |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Power @ ≤20 MSPS | ≤90 mW (90 mW at 20 MSPS, less at this design's ~10 MSa/s) | datasheet p.1 Product Highlights — **verified**, confirms architecture's assumption |
| MODE2 pin function | Selects SHA gain (1x/2x) + auto power-control; 4 DC levels: AVDD / 2:3·AVDD / 1:3·AVDD / AGND | datasheet Table, Pin 1 — **verified**. NOT an optional/floating pin — must be strapped to one of these 4 levels |
| OE pin function | Output Enable, active low; tie low (AGND) to keep the parallel data bus permanently driven (this design uses one dedicated ADC per FPGA bus, not a shared/multiplexed bus) | datasheet Table, Pin 3, and Product Highlights #6 ("Output Enable pin to allow for multiplexing of the outputs") — **verified** |
| Pin 5/6 = DNC (not "GC") | Both pins 5 and 6 are DNC on AD9237 in this datasheet revision | datasheet Table — **verified**. Corrects `sourcing/sourced_bom.md` Decision #2, which cited an EasyEDA-tool pin label "GC" for pin 5 (gain control); no "GC" mnemonic appears anywhere in the ADI datasheet text. Treat "GC" as an EasyEDA labelling artifact, not a real AD9237 function — only **2** pins (1=MODE2, 3=OE) are genuinely AD9237-specific control pins, not 3 |
| ADI states pin-compatibility with AD9235 | "The AD9237 is pin compatible to the AD9235 ... This allows a simplified path for low power 12-bit systems." | datasheet p.1 Product Highlights #4 — **verified**, manufacturer-endorsed second-source path (see AD9235BCPZ-40 summary for the DNC-pin caveat this doesn't fully resolve) |
| Electrical test conditions strap MODE2 hard to 0V or AVDD | Table entries use "MODE2 = 0V" and "MODE2 = AVDD" (not a resistor-divider mid-level) for the two production test conditions | datasheet Electrical Characteristics table — **verified**. Suggests ADI's own test setup uses a direct trace tie, not a divider, for the simple case |

## Notes
- **MODE2 and OE are not optional strap-once-and-forget pins — they set operating mode.**
  The coder must pick and document one MODE2 level (AVDD/2:3·AVDD/1:3·AVDD/AGND — simplest
  is a direct tie to AVDD or AGND, matching the datasheet's own test conditions) and tie OE
  low (AGND) for this single-ADC-per-bus design.
- R150/R250 (`adc_channel` block, flagged unallocated in `sourced_bom.md`) are very
  plausibly one of these two straps — most likely a series/damping resistor on the MODE2
  or OE trace, since a hard tie normally needs no resistor at all. This is a hypothesis,
  not confirmed against `net_plan.md`; the coder must check which (if either) strap needs
  R150/R250 and leave the other as a direct trace, or flag both as genuinely spare.
- Exposed pad (pin 33 in generated symbol) must connect to the ground plane per the
  datasheet's own EPAD note (paraphrased from the pin-compatible AD9235's identical note,
  since AD9237's Table doesn't repeat it verbatim in this revision but describes the same
  LFCSP-32 package/pad).
- Decoupling: not itemized per-pin in this revision; follow standard ADI high-speed ADC
  practice — 0.1 µF close to every AVDD/DRVDD pin, per `sourced_bom.md`'s C150–C161 (CH1)
  /C250–C261 (CH2) decoupling rows.
- See `AD9235BCPZ-40_SUMMARY.md` for the second-source DNC-pin qualification verdict.
