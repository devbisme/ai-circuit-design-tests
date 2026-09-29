# USBLC6-2SC6 — Dual USB ESD Protection Array (U1)

MCP data only (JLC field's `.pdf` URL returned an HTML anti-bot page on the one fallback
attempt; ordinary-part budget spent, not pursued further per SOT-23-6 being a
well-standardized, industry-common ESD-array pinout).

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Vcc / Vin range | N/A (passive TVS array) |
| Key output spec | Clamping voltage 15V, Ipp 6A @8/20µs, Vrwm 5V, Vbr 6V |
| Max current / power | Ppp 150W @8/20µs |
| Operating temp | not in JLC parametric data |

## Pinout
Local symbol `Power_Protection:USBLC6-2SC6` is an EXACT match per `sourced_bom.md` — use
its pin names directly; not re-derived here since a verified local symbol already exists.

## Notes
- Industry-standard pin-compatible part (9 JLC manufacturers stock equivalents per
  sourcing decision) — low design risk.
- Placed on the USB D+/D− lines per `sourced_bom.md`'s `usb_front` block.
