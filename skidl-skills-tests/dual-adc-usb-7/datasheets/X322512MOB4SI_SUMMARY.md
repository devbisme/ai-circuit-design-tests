# X322512MOB4SI — 12MHz crystal (usb_bridge, Y1)

| Spec | Value |
|------|-------|
| Package | SMD3225-4P |
| Vcc / Vin range | N/A (passive crystal) |
| Key output spec | 12MHz, **12pF load capacitance**, ESR 80Ω, ±10ppm freq tolerance, ±20ppm stability |
| Max current / power | N/A |
| Operating temp | −40°C to +85°C |

## Notes
- Beats the architecture's ±30ppm stability spec (this part: ±20ppm).
- Load caps C601/C602 (12pF, per sourced_bom) match this crystal's rated 12pF load capacitance
  exactly — confirmed against `jlc_get_part` specs for this exact LCSC# (C70565).
- Datasheet PDF not obtained (1 attempt, ordinary-part budget; direct lcsc.com link returned an
  HTML page, no alternate manufacturer URL found in one search) — MCP parametric data is
  complete enough (frequency, load cap, ESR, stability) that no PDF is needed for this passive
  crystal per scope.
- Existing symbol used: `Device:Crystal` — standard part, not regenerated.
