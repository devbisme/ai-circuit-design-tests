# TLV75733PDRVR — Fixed 3.3V LDO (U3, generates +3V3_A)

| Spec | Value |
|------|-------|
| Package | WSON-6 (2×2mm) |
| Vcc / Vin range | up to 5.5V in, fixed 3.3V out |
| Key output spec | PSRR 45dB@100kHz (misses P8's ≥50dB alone — met with input π-filter per architecture) |
| Max current / power | 1A, dropout 425mV@1A |
| Operating temp | −40°C to +125°C (Tj) |

## Pinout (WSON-6+EP, from EasyEDA/JLC symbol data)

| Pin | Name | Function |
|-----|------|----------|
| 1 | OUT | Regulated 3.3V output |
| 2 | NC | No connect |
| 3 | GND | Ground |
| 4 | EN | Enable — **active HIGH per TI's standard convention for this LDO family** (same silicon family/pin layout as TLV75801PDRVR, confirmed active-high in that device's own datasheet; not independently re-confirmed against a TLV75733-specific PDF, see Notes) |
| 5 | NC | No connect |
| 6 | IN | Supply input — from `+5V_SW` |
| 7 | EP | Exposed thermal pad — tie to GND plane (mandatory, architecture item 6) |

## Symbol check — stock symbol confirmed usable, one naming caveat

`Regulator_Linear:TLV75733PDRV` (the sourcer's PREFIX match) **does exist** in the stock
KiCad library — confirmed by direct inspection, not just `find-symbol.py`'s report. It's a
derived symbol (`(extends "TLV75509PDRV")`), which is why a naive pin-counting script can
undercount it; its inherited pin list is 7 pins: `1=OUT, 2=NC, 3=GND, 4=EN, 5=NC, 6=IN,
7=GND`. **Caveat: the stock symbol names pin 7 "GND", not "EP"** (JLC's EasyEDA data and this
summary's table above call it EP for clarity, since it's physically the exposed pad — same
pin, different label). If the coder uses the stock symbol and references pins by name in
SKiDL, use `"GND"` for pin 7, not `"EP"` — or use the alternate symbol below.

A second, defensive symbol was also generated in this pass before this check completed:
`dual_adc_usb:TLV75733PDRVR` in `symbols/dual_adc_usb.kicad_sym` (7/7 pins, EP explicitly
named `EP`) — either symbol is correct and electrically equivalent; use whichever pin-naming
convention is more convenient in `analog_power_ref`'s block code.

## Notes

- **Fixed-output part — no FB divider needed** (unlike U2/TLV75801PDRVR, which is
  adjustable). This is the correct pin-count tell: TLV75733 has NC at pin 2 where
  TLV75801 has FB — confirms sourcing correctly picked the fixed-3.3V variant for the
  fixed-target analog rail.
- **PSRR insufficiency is a known, already-designed-around gap**: 45dB@100kHz alone misses
  the architecture's ≥50dB requirement (P8). The architecture's fix is the input π-filter
  (FB3 + bulk caps) ahead of this LDO — **do not drop FB3 or the input/output bulk caps**,
  they are load-bearing for the spec, not generic decoupling.
- No PDF obtained for this specific part number: the LCSC-hosted URL downloaded but
  `fetch-datasheet.py`'s validator rejected it as never mentioning "TLV75733" in the first 3
  pages (likely a mismatched/generic file on LCSC's side) — 1/2 URL attempts used; did not
  spend the second since MCP already supplied complete pin+spec data and EN polarity is a
  safe cross-family inference (same WSON-6 DRV package family as TLV75801, which does confirm
  active-high EN in its own real datasheet).
- Thermal pad mandatory (200mW dissipation per architecture) — same TI DRV family as U2.
