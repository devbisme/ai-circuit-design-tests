# AD9235BCPZ-40 — 12-Bit, 20/40/65 MSPS 3V A/D Converter (used at 40 MSPS grade, LFCSP-32)

Source: `datasheets/AD9235BCPZ-40_try2.pdf` (ADI AD9235 datasheet Rev. B — **correction: this
is the full 32-page document, not a 4-page excerpt as an earlier pass of this summary
claimed**; confirmed via `pdfinfo` and by reading the Mode Selection table (p.17) and Outline
Dimensions (p.31) below, both of which are present.) A second file on disk,
`datasheets/AD9235BCPZ-40.pdf`, was mis-downloaded as the **AD9238** (dual-channel)
datasheet by an earlier URL attempt — **do not use it**, it is the wrong part; delete-protect
prevented removing it this session, it is left on disk as dead weight only.

| Spec | Value |
|------|-------|
| Package | 32-lead LFCSP (CP-32), also available 28-lead TSSOP (not this BOM's grade) |
| Vcc / Vin range | AVDD 2.7–3.6V (3.0V nom), DRVDD 2.25–3.6V (architecture uses 3.0V for both, from `+3V0A`/AVDD split — DRVDD wiring not yet confirmed, see Notes) |
| Key output spec | 12-bit, differential input, VREF-selectable full-scale span: 1Vpp (VREF=0.5V) or **2Vpp (VREF=1.0V)** — architecture uses the 2Vpp span (Decision 5) |
| Max current / power | IAVDD 100 mA max (40/65 MSPS row), IDRVDD 7 mA max; AVDD/DRVDD abs max –0.3 to +3.9V |
| Operating temp | –40°C to +85°C (Z-grade, matches `BCPZ` Pb-free/industrial ordering suffix) |

## Pinout (32-Lead LFCSP, exactly as datasheet Table)

| Pin | Name | Function |
|-----|------|----------|
| 1, 3, 5, 6 | DNC | Do Not Connect |
| 2 | CLK | Clock Input Pin |
| 4 | PDWN | Power-Down Function Selection (Active High) |
| 7 (LSB) – 14 | D0–D7 | Data Output Bits (D0 = LSB) |
| 15 | DGND | Digital Output Ground |
| 16 | DRVDD | Digital Output Driver Supply. Decouple to DGND with min 0.1µF; recommended 0.1µF ∥ 10µF |
| 17–20 | D8–D11 (MSB) | Data Output Bits (D11 = MSB) |
| 21 | OTR | Out-of-Range Indicator |
| 22 | MODE | Data Format and Clock Duty Cycle Stabilizer (DCS) Mode Selection |
| 23 | SENSE | Reference Mode Selection |
| 24 | VREF | Voltage Reference Input/Output |
| 25 | REFB | Differential Reference (–) |
| 26 | REFT | Differential Reference (+) |
| 27, 32 | AVDD | Analog Power Supply |
| 28, 31 | AGND | Analog Ground |
| 29 | VIN+ | Analog Input Pin (+) |
| 30 | VIN– | Analog Input Pin (–) |
| EPAD | — | Exposed paddle — "recommended that the exposed paddle be soldered to the ground plane" for reliability/thermal (datasheet ordering-guide note); no separate pin number |

## Notes

- **SENSE → GND selects internal 1.0V reference** (per architecture Decision 5, "both ADCs
  use their internal 1.0V references, SENSE → GND"), which per this table sets VREF = 1.0V →
  **2Vpp differential input span** — matches the FDA's ±1.000V/side output exactly. Do not
  float SENSE; tie it to AGND.
- **MODE pin truth table (Table II, p.17), multilevel input, internally pulled down to AGND
  by a 20kΩ resistor (default = AGND if left unconnected):**

  | MODE Voltage | Data Format | Duty Cycle Stabilizer |
  |---|---|---|
  | AVDD | Twos Complement | Disabled |
  | 2/3 AVDD | Twos Complement | Enabled |
  | 1/3 AVDD | Offset Binary | Enabled |
  | AGND (default) | Offset Binary | Disabled |

  Simplest coder-time choice: **tie MODE directly to AGND** for offset-binary output with
  DCS disabled (matches the internal pull-down default, so this is also safe if left
  unconnected — but tie it explicitly rather than floating, per ADI's own recommendation to
  strap all mode/logic pins). If DCS is wanted, a resistor divider off AVDD is required
  (2/3 or 1/3 AVDD) — not needed unless clock duty cycle is known to be off from 50%.
- **DNC pins (1, 3, 5, 6) must be left unconnected** — do not tie to ground or route through;
  ADI explicitly reserves these.
- DRVDD (pin 16) needs local 0.1µF + 10µF decoupling to DGND, called out explicitly by ADI —
  distinct from AVDD decoupling. Confirm `adc_pair` block's C48–C70 range budgets a DRVDD pair
  per ADC (2 total) in addition to AVDD decoupling.
- CLK (pin 2) is single-ended in this package (not CLK_A/CLK_B — that pinout belongs to the
  dual AD9238, not this part). Matches architecture's single `CLK_ADC1`/`CLK_ADC2` per-chip
  wiring from the SN74LVC2G34 fanout buffer.
- **EP dimension confirmed — closes `03_sourcing.md` gap item #1 (AD9235 part).** Outline
  Dimensions, "32-Lead Lead Frame Chip Scale Package [LFCSP] (CP-32)", p.31, compliant to
  JEDEC MO-220-VHHD-2: body 5.00mm BSC SQ, pitch 0.50mm BSC, 32 leads (matches the sourced
  footprint's body/pitch) — **exposed pad = 3.10mm SQ nominal, range 2.95mm (min) to 3.25mm
  (max)**. The sourced footprint
  (`Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm`) assumed **EP3.45×3.45mm, which is
  too large — even the drawing's max (3.25mm) falls short of 3.45mm.** Build/select a
  corrected footprint with **EP = 3.10×3.10mm** (nominal) before layout; body outline, pitch,
  and pin count are otherwise correct.
