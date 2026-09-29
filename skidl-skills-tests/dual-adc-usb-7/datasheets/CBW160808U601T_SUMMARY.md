# CBW160808U601T — Ferrite bead (power_tree, FB1)

| Spec | Value |
|------|-------|
| Package | 0603 (package-substituted from 0805 per sourcing `[FREE]` tag) |
| Key spec | **600Ω@100MHz**, current rating **1A**, DCR 300mΩ, ±25% tolerance |
| Operating temp | −55°C to +125°C |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Impedance @ 100MHz and current rating | 600Ω@100MHz, 1A | `jlc_get_part` specs for C139183 — **verified**, matches sourcing's stated substitution rationale exactly (no 0805 part hit both 600Ω@100MHz and ≥1A; this 0603 part does) |

## Notes
- Filters VBUS_SW → VA_POS (analog +5V rail feeding AD8066/TPS60403).
- Datasheet obtained via FH's family PDF (`fenghua.com/pdf/inductor/CBW.pdf`, covers the CBW
  160808 size series) rather than a single-part datasheet — confirmed the family document
  covers this exact impedance/current grade.
