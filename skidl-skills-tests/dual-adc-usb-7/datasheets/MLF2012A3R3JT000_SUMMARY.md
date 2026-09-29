# MLF2012A3R3JT000 — 3.3µH AAF inductor (afe_driver, L111/113/211/213)

| Spec | Value |
|------|-------|
| Package | 0805 |
| Key spec | 3.3µH ±5%, **SRF 60MHz**, Q=45@10MHz, DCR 280mΩ, current rating 50mA |
| Operating temp | Not in MCP record for this listing |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Self-resonant frequency (SRF) | 60MHz | `jlc_get_part` specs for C275371 — **verified**, meets design_risks.md R-4's ≥40MHz requirement for this inductor position with margin |

## Notes
- Anti-alias filter L1 position (per sourced_bom naming). ±5% tolerance is inside the R-4 Monte
  Carlo bound (worst case −2.24dB@4MHz / 40.6dB@10MHz with L±5%, C0G±2%).
- Datasheet: `datasheets/MLF2012A3R3JT000.pdf` (TDK).
