# TPH2501-TR — Single Op-Amp, High Slew Rate (SK-filter/follower stages, U100-U102/U200-U202)

Datasheet obtained: `datasheets/TPH2501-TR.pdf` (3PEAK "TPH2501/TPH2502/TPH2503/TPH2504,
250-MHz, Precision, Rail-to-Rail I/O, CMOS Operational Amplifier", Rev. B.6, from
`static.3peak.com` — verified exact part match, TPH2501 is the single-channel/SOT-23-5
member of this datasheet's family). LCSC's own datasheet field URL for this part
(`lcsc.com/datasheet/...`) still returns an HTML page, not a PDF — confirmed failing again
this pass; the manufacturer's own `static.3peak.com` URL (found via one web search) is the
one that resolved.

| Spec | Value |
|------|-------|
| Package | SOT-23-5 (also available SOT-353/SC70-5, not used here) |
| Vcc / Vin range | Single 2.5–5.5 V, or dual ±1.35 V to ±2.75 V |
| Key output spec | 250 MHz unity-gain BW, 120 MHz gain-BW product, 180 V/µs slew rate, RRIO, 6.5 nV/√Hz noise |
| Max current / power | 6.5 mA quiescent, output current >100 mA (short-circuit current limit −160/160 mA abs max) |
| Operating temp | −40°C to +125°C |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | Out | Output |
| 2 | -VS | Negative power supply (normally GND) |
| 3 | +In | Non-inverting input |
| 4 | -In | Inverting input |
| 5 | +VS | Positive power supply |

**Verified** directly from the downloaded PDF, Table 2 "Pin Functions: TPH2501, TPH2503"
(p.5, "Pin Configuration and Functions" section) — cross-checked against `jlc_get_pinout`
(LCSC C126713), which independently reports the same 5 pins (spelled OUT/VS-/+IN/-IN/VS+ —
same electrical assignment, EasyEDA just moved the sign to a suffix on VS). **No SHDN/enable
pin exists on this 5-pin TPH2501 part** — the "Enable/shutdown function" line in JLC's part
spec is a family-level feature that belongs to the 6-pin TPH2503 variant (adds pin 5 = SHDN,
confirmed in the same datasheet's Table 2), not to TPH2501. Do not add or strap an EN pin for
this part.

## Notes
- 3x per analog-frontend channel (follower + 2 Sallen-Key stages), 6 total across both
  channels, per `sourced_bom.md`'s `analog_frontend` block.
- Power-supply pins: -VS is "normally tied to GND" per the datasheet; if not tied to GND
  (split-supply use), it must be bypassed with a 0.1 µF cap as close to the part as possible
  — same bypass requirement applies to +VS. This design appears single-supply (check
  `net_plan.md`); if so, tie pin 2 (-VS) to AGND directly.
- Absolute max supply differential (+VS)−(−VS) = 7.0 V — do not exceed.
- Symbol generated this pass: `dual_adc_usb:TPH2501-TR` in
  `symbols/dual_adc_usb.kicad_sym`, verified `EXACT` via `find-symbol.py`. Pin
  types/sides: Out=output/right, -VS=power_in/bottom, +In=input/left, -In=input/left,
  +VS=power_in/top.
