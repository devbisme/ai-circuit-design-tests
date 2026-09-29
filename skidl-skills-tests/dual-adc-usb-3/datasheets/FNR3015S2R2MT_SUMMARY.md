# FNR3015S2R2MT — CJIANG FNR Series Wire-Wound SMD Power Inductor, 2.2µH (buck inductors L1, L2)

Source: `datasheets/FNR3015S2R2MT.pdf` (CJIANG "Wire Wound SMD Power Inductors – FNR
Series" catalog, 19 pages, **scanned/image-only PDF, no embedded text** — read directly via
page images, not text-extracted). Covers the whole FNR series (multiple body sizes); this
part is the FNR3015S body/case (3.0×3.0mm, 1.5mm max height) at the 2.2µH value.

| Spec | Value |
|------|-------|
| Package | FNR3015S — 3.0×3.0mm body (A=B=3.0±0.2mm), 1.5mm max height (C), shielded (magnetic-resin) wire-wound, no standard KiCad footprint — **custom footprint built this phase, see Notes** |
| Vcc / Vin range | N/A (passive inductor) |
| Key output spec | Inductance 2.2µH (catalog row **FNR3015S2R2NT**, ±30% — see Notes on MT/NT tolerance-suffix mismatch); DCR max 0.078Ω / typ 0.060Ω; self-resonant freq min 86MHz |
| Max current / power | Saturation current (Isat) max 1.60A / typ 2.00A; heat-rating current (Irms, temp-rise) max 1.60A / typ 1.90A |
| Operating temp | –40°C to +125°C (including self-heating), per catalog cover page |

## Pinout

2-terminal passive part, no polarity (wire-wound inductor, not a coupled/polarized part) —
either pad may connect to either net.

| Pin | Name | Function |
|-----|------|----------|
| 1 | — | Terminal A |
| 2 | — | Terminal B |

## Notes

- **Custom KiCad footprint built this phase — closes `03_sourcing.md` gap item #2.**
  `footprints/Inductor_SMD_Custom.pretty/L_FNR3015S_3.0x3.0mm.kicad_mod`. SKiDL footprint
  string: `'Inductor_SMD_Custom:L_FNR3015S_3.0x3.0mm'` (project-local library — user must add
  it in KiCad under Preferences → Manage Footprint Libraries → Project Specific Libraries,
  nickname `Inductor_SMD_Custom`, path `${KIPRJMOD}/footprints/Inductor_SMD_Custom.pretty`,
  per `rules/kicad-footprints.md`). Built from catalog p.2 "Shape and Dimensions" table,
  FNR3015S row (Fig.2 shape): body A=B=3.0±0.2mm, height C=1.5mm Max, D=2.5±0.2mm,
  E=0.75±0.2mm, F=1.5±0.2mm; **recommended land pattern (same table, "Typ" columns): pad
  gap (a) = 1.5mm, pad width (b) = 0.8mm, pad length (C) = 2.7mm.** Footprint places two
  0.8×2.7mm SMD pads centered at X=±1.15mm (= gap/2 + width/2), courtyard 3.3×3.3mm.
- **MT vs. NT tolerance-suffix mismatch.** The sourced/BOM part number is
  `FNR3015S2R2MT` (M = ±20% per the Product Identification key, catalog p.1), but the
  FNR3015S series spec table (p.5) only lists a 2.2µH row as **`FNR3015S2R2NT`** (N = ±30%)
  — no `...2R2MT` row appears in this catalog. Package/footprint/electrical performance
  (DCR, Isat, SRF) are identical either way — **only the inductance tolerance band differs
  (±20% claimed vs. ±30% catalogued)**. Likely a distributor-specific tolerance-binned SKU
  not broken out in the general catalog (same is true of several other values in this
  series, e.g. 2.7µH is also only cataloged as NT). Not a footprint or pinout risk; flagged
  for the coder/BOM only in case ±20% tolerance is load-bearing for the buck converter's
  output ripple/inductor-current-ripple margin — if so, verify the actual purchased reel's
  tolerance marking against LCSC's listing rather than this general catalog page.
- 2.2µH / Isat 1.6–2.0A comfortably covers a typical buck converter's peak inductor current
  at the currents implied by this design's +3V3/+1V2 rails (low-current digital rails, not
  a high-current power stage) — no saturation-margin concern expected, but the block coder
  should confirm against TLV6256x's actual output current budget from
  `datasheets/TLV62569DBVR_SUMMARY.md` / `TLV62568DBVR_SUMMARY.md` if not already checked
  there.
