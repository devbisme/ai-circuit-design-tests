# FHW0805UF5R6JST — 5.6µH AAF inductor (afe_driver, L112/114/212/214)

| Spec | Value |
|------|-------|
| Package | 0805 |
| Key spec | 5.6µH ±5%, **SRF 70MHz**, Q=10@7.96MHz, DCR 2.3Ω, current rating 240mA |
| Operating temp | Not in MCP record for this listing |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Self-resonant frequency (SRF) | 70MHz | `jlc_get_part` specs for C393992 — **verified**, meets design_risks.md R-4's ≥30MHz requirement for this inductor position with margin |

## Notes
- Anti-alias filter L2 position. Stock is 602pcs — above the 100-unit floor but flagged by
  sourcing as the thinnest margin on the board; buy the full qty-5 build (20pcs) in one order.
- Datasheet: `datasheets/FHW0805UF5R6JST.pdf` (FH/Guangdong Fenghua).
