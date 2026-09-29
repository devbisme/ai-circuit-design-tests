# WIP201610P-2R2ML — 2.2µH shielded buck inductor (power_tree, L71/L72)

| Spec | Value |
|------|-------|
| Package | 0806 (INPAQ 201610 size code, shielded wirewound) |
| Key spec | 2.2µH ±20%, **Isat 1.71A**, current rating 1.7A, DCR 135mΩ |
| Operating temp | Not in MCP record for this listing |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Saturation current | 1.71A | `jlc_get_part` specs for C315717 — **verified**, meets the architecture's ≥1.5A / shielded requirement |
| Body / land pattern | Body 2.0×1.6×1.0mm; INPAQ's recommended land pattern: pad A=1.6mm, pad B=0.9mm, span 2.0mm | `WIP201610P-2R2ML.pdf` §3.2/3.3 (Construction & Dimensions, Recommended Land Pattern) — **verified** |

## Notes on the assigned footprint (sourcing flagged this as unverified)
The assigned KiCad footprint is `Inductor_SMD:L_Murata_DFE201610P` — a **different
manufacturer's** part in the same "201610" industry-standard body/pad size class. INPAQ's own
datasheet dimensions (2.0×1.6mm body, 1.6mm pad span, 0.9mm pad width) are consistent with the
DFE201610P footprint family's known envelope, but I did not pull the actual `.kicad_mod` pad
coordinates to diff them numerically against INPAQ's table (would require inspecting the KiCad
footprint library file, out of this phase's PDF-reading scope). **Carried forward: the coder
should do a direct pad-by-pad comparison before fab** — risk is low (same size class, same
generic shielded-wirewound-inductor land pattern convention across vendors) but not
zero-verified.
- Datasheet: `datasheets/WIP201610P-2R2ML.pdf` (INPAQ).
