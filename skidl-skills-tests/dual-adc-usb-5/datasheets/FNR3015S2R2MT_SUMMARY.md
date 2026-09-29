# FNR3015S2R2MT — 2.2µH shielded power inductor (L1, buck output)

| Spec | Value |
|------|-------|
| Package | SMD, 3×3mm, magnetically shielded |
| Inductance | 2.2µH ±20% |
| Saturation current (Isat) | 2A |
| DCR | 78mΩ |

## Notes

- 2-terminal passive, no pinout ambiguity — standard 2-pad shielded power inductor footprint.
- Meets U1 (SY8089A1AAC buck)'s 2A output rating with matching saturation current — no
  derating margin beyond the buck's own rated output, acceptable for this 5V→3.3V,
  low-duty-cycle rail per architecture (freely substitutable part, item 10).
- No PDF fetched (LCSC-hosted URL returned an HTML anti-bot page; not chased further — this
  is a freely-substitutable jellybean power inductor with all relevant specs already in the
  MCP parametric record).
