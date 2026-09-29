---
phase: datasheets
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Wrote 22 `datasheets/<MPN>_SUMMARY.md` files covering every significant IC/connector
  across all 9 blocks in `sourcing/sourced_bom.md`, including complete pin-number/pin-name
  tables for the four `[GEN]` parts that have no KiCad symbol (AD9235BRUZ-20,
  IS61WV25616BLL-10TLI, AD8066ARZ, OPA836IDBVR) — these tables are the `kipart` input for
  the coding phase.
- For every part that already has a KiCad symbol, pin names/numbers in the summary were
  read **directly from the installed `.kicad_sym` files** (not guessed, not OCR'd),
  including following `(extends "...")` base-symbol references where the sourced MPN is
  an alias (AP7361C-33E, AP2112K-1.2, LP5907MFX-3.3, REF3025, USBLC6-2SC6).
- Resolved the deferred **AD9235 SENSE/REFT/REFB strapping** open item: SENSE→AGND
  (VREF=1.0 V internal, confirmed twice independently from datasheet text → 2.0 V p-p
  span), REFT/REFB/VREF each get dedicated 0.1 µF bypass and must not be driven or
  loaded externally, and VIN− (1.500 V) must come from a **new, dedicated** resistor
  divider off REF3025 — explicitly **not** the existing R7/R8 (0.5 V) divider, which is
  committed to a different node (the AFE's OPA836 offset-summing input). Full detail in
  `datasheets/AD9235BRUZ-20_SUMMARY.md`.
- Downloaded 4 real PDFs (IS61WV25616BLL-10TLI, LM2776DBVR, LP5907MFX-3.3-NOPB,
  OPA836IDBVR). Most other PDF hosts (analog.com, diodes.com, ftdichip.com,
  microchip.com, digikey.com, amphenolrf.com) either timed out or returned HTTP 403 to
  automated fetch from this sandbox — expected per the phase's network-may-be-unavailable
  guidance; summaries were written from model knowledge + local KiCad symbol data in
  those cases and marked accordingly.
- **Two stray invalid files exist in `datasheets/`**: `iCE40HX4K-TQ144.pdf` and
  `REF3025AIDBZR.pdf` are actually HTML (JS-gated download pages saved with a `.pdf`
  extension by a failed curl), not real PDFs. A sandbox file-protection hook blocked
  deleting/overwriting them — **they must be manually removed**, they are not listed
  under `## Artifacts` below and must not be opened as datasheets.

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| datasheets/AD9235BRUZ-20_SUMMARY.md | Full pin table (kipart input) + SENSE/REFT/REFB/VIN− strapping resolution | coding (adc_channel) |
| datasheets/IS61WV25616BLL-10TLI_SUMMARY.md | Full pin table (kipart input) | coding (sram_buffer) |
| datasheets/IS61WV25616BLL-10TLI.pdf | Real datasheet PDF (19 pp) | coding (sram_buffer) |
| datasheets/AD8066ARZ_SUMMARY.md | Full pin table (kipart input) | coding (afe_channel) |
| datasheets/OPA836IDBVR_SUMMARY.md | Full pin table (kipart input) | coding (afe_channel) |
| datasheets/OPA836IDBVR.pdf | Real datasheet PDF (10 pp) | coding (afe_channel) |
| datasheets/USBLC6-2SC6_SUMMARY.md | Pin table + application note | coding (usb_c_input) |
| datasheets/PESD5V0S1BA_SUMMARY.md | Specs + pin table | coding (usb_c_input) |
| datasheets/XKB_U262-16XN-4BVC11_SUMMARY.md | 16-pin USB-C receptacle pin table | coding (usb_c_input) |
| datasheets/AP7361C-33E-13_SUMMARY.md | Pin table + specs | coding (power_digital) |
| datasheets/AP2112K-1.2TRG1_SUMMARY.md | Pin table + specs | coding (power_digital) |
| datasheets/AO3401A_SUMMARY.md | Pin table + specs | coding (power_analog) |
| datasheets/LM2776DBVR_SUMMARY.md | Pin table + specs | coding (power_analog) |
| datasheets/LM2776DBVR.pdf | Real datasheet PDF (10 pp) | coding (power_analog) |
| datasheets/LP5907MFX-3.3-NOPB_SUMMARY.md | Pin table + specs | coding (power_analog) |
| datasheets/LP5907MFX-3.3-NOPB.pdf | Real datasheet PDF (10 pp) | coding (power_analog) |
| datasheets/REF3025AIDBZR_SUMMARY.md | Pin table + specs | coding (power_analog) |
| datasheets/ASEM1-10.000MHZ-LC-T_SUMMARY.md | Pin table + specs | coding (clock_gen) |
| datasheets/74LVC1G34GW-125_SUMMARY.md | Pin table + specs | coding (clock_gen) |
| datasheets/BAV99_SUMMARY.md | Pin table + clamp-topology flag | coding (afe_channel, fpga_core) |
| datasheets/Amphenol_031-6575_SUMMARY.md | BNC pin table; mechanical dims NOT obtained | coding (afe_channel) |
| datasheets/FT232HL_SUMMARY.md | Full 48-pin table | coding (usb_bridge) |
| datasheets/93LC46BT-I-OT_SUMMARY.md | Pin table + specs | coding (usb_bridge) |
| datasheets/X322512MSB4SI_SUMMARY.md | Pin table + specs | coding (usb_bridge) |
| datasheets/iCE40HX4K-TQ144_SUMMARY.md | Key-pin table (144-pin symbol has the rest) | coding (fpga_core) |
| datasheets/W25Q32JVSSIQ_SUMMARY.md | Pin table + specs | coding (fpga_core) |

## Summaries by block

| block_id | summary files |
|----------|---------------|
| `usb_c_input` | `datasheets/XKB_U262-16XN-4BVC11_SUMMARY.md`, `datasheets/USBLC6-2SC6_SUMMARY.md`, `datasheets/PESD5V0S1BA_SUMMARY.md` |
| `power_digital` | `datasheets/AP7361C-33E-13_SUMMARY.md`, `datasheets/AP2112K-1.2TRG1_SUMMARY.md` |
| `power_analog` | `datasheets/AO3401A_SUMMARY.md`, `datasheets/LM2776DBVR_SUMMARY.md`, `datasheets/LP5907MFX-3.3-NOPB_SUMMARY.md`, `datasheets/REF3025AIDBZR_SUMMARY.md` |
| `clock_gen` | `datasheets/ASEM1-10.000MHZ-LC-T_SUMMARY.md`, `datasheets/74LVC1G34GW-125_SUMMARY.md` |
| `afe_channel` (×2) | `datasheets/Amphenol_031-6575_SUMMARY.md`, `datasheets/AD8066ARZ_SUMMARY.md`, `datasheets/OPA836IDBVR_SUMMARY.md`, `datasheets/BAV99_SUMMARY.md` |
| `adc_channel` (×2) | `datasheets/AD9235BRUZ-20_SUMMARY.md` |
| `sram_buffer` | `datasheets/IS61WV25616BLL-10TLI_SUMMARY.md` |
| `usb_bridge` | `datasheets/FT232HL_SUMMARY.md`, `datasheets/93LC46BT-I-OT_SUMMARY.md`, `datasheets/X322512MSB4SI_SUMMARY.md` |
| `fpga_core` | `datasheets/iCE40HX4K-TQ144_SUMMARY.md`, `datasheets/W25Q32JVSSIQ_SUMMARY.md`, `datasheets/BAV99_SUMMARY.md` |

## Key facts for the next phase

- **The 4 `[GEN]` parts (AD9235BRUZ-20, IS61WV25616BLL-10TLI, AD8066ARZ, OPA836IDBVR)
  all have complete, high-confidence pin tables** (number → name → type) in their
  summaries, ready for `kipart` symbol generation. IS61WV25616BLL-10TLI's table was
  transcribed directly from a fetched image of the real ISSI datasheet's pin diagram
  (highest confidence of the four). AD9235's table is corroborated by two independent
  datasheet-text extractions. AD8066/OPA836 tables come from WebSearch-quoted datasheet
  pin diagrams (standard, well-known package conventions for both) — flagged
  medium-high confidence, not independently double-sourced.
- **AD9235 reference strapping (resolves the architecture's deferred open item):**
  SENSE (pin 3) → AGND; REFT (pin 6)/REFB (pin 5)/VREF (pin 4) each get their own 0.1 µF
  bypass to AGND and must not be driven or loaded; VIN− (pin 10) needs a **new** 1.500 V
  divider off REF3025 (U5) — do not reuse the existing R7/R8 0.5 V divider, which feeds a
  different node in the AFE's OPA836 stage. Full component-by-component detail in the
  AD9235 summary.
- **iCE40HX4K-TQ144:** CBSEL0/CBSEL1 (pins 63/64) → tie GND for single-image SPI-master
  boot. VPP_2V5 (pin 108) must be connected to 2.5 V even without NVCM use. W25Q32's
  ~WP/~HOLD pins need pull-ups the sourced BOM's passive count did not itemize — coder
  must add 2 resistors during `fpga_core` coding.
- **FT232HL:** REF pin (5) needs R13 (12 kΩ) or USB will not enumerate. ACBUS9 (pin 33)
  must be EEPROM-configured as PWREN#. TEST (pin 42) → GND. VCCA/VCCCORE (pins 37/38)
  are regulator *outputs* — decouple only, never drive.
- **BAV99 clamp topology flag:** the KiCad symbol's pin typing is common-anode (pin 2 =
  shared A, pins 1/3 = K). Verify the intended dual-±5V-rail clamp behavior against this
  before wiring D_clamp/D7 — a single common-anode part may not achieve a symmetric
  ±5 V clamp; see the BAV99 summary's Notes.

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| DS1 | Pin-data source for parts with an existing KiCad symbol | Trust WebSearch/datasheet text / parse the installed `.kicad_sym` files directly | **Parse local symbol files** | Authoritative — it's the exact data SKiDL will place; also network-independent and faster given ~20 parts to cover |
| DS2 | AD9235 SENSE strap for 2 Vpp span | SENSE=AGND (2 Vpp) / SENSE=VREF (1 Vpp, insufficient) / SENSE=AVDD (external ref, unneeded complexity) | **SENSE=AGND** | Only strap reaching the required 2.0 V p-p span; confirmed twice from datasheet text (VREF=1.0V mode → 2Vpp) |
| DS3 | AD9235 VIN− 1.500V bias source | Tap REFT/REFB directly / reuse R7-R8's 0.5V divider / new dedicated divider off REF3025 | **New dedicated divider** | Tapping REFT/REFB loads and unbalances the reference ladder (degrades linearity); R7/R8 already committed to a different (0.5V, AFE-offset) node — reusing it would be wrong voltage AND wrong function |
| DS4 | iCE40 CBSEL0/1 strap | Tie GND (single SPI image) / resistor-strap for multi-image select | **Tie GND** | Design has one external flash with one bitstream — simplest default, matches Lattice's standard single-image SPI master boot |
| DS5 | 93LC46B ORG pin | Tie VCC (×16) / tie GND (×8) | **Tie VCC (×16)** | Matches FTDI's standard EEPROM-image convention for FT232H companion EEPROMs |
| DS6 | Stray invalid `.pdf` files (iCE40HX4K-TQ144.pdf, REF3025AIDBZR.pdf, actually HTML) | Delete / overwrite with retry / leave and flag | **Leave and flag** | A sandbox hook blocks delete/overwrite in `datasheets/`; documented here and in Carried forward instead |

## Carried forward

- **PDF not retrieved** (summary written from model knowledge + local KiCad symbol data
  instead, each file's SOURCE line says so explicitly): AD9235BRUZ-20, AD8066ARZ,
  AP7361C-33E-13, AP2112K-1.2TRG1, REF3025AIDBZR, ASEM1-10.000MHZ-LC-T,
  74LVC1G34GW-125, BAV99, USBLC6-2SC6, PESD5V0S1BA, AO3401A, FT232HL, 93LC46BT-I/OT,
  X322512MSB4SI, iCE40HX4K-TQ144, W25Q32JVSSIQ, XKB U262-16XN-4BVC11 (J1),
  Amphenol 031-6575 (J2/J3).
- **Two stray files in `datasheets/` are invalid** (HTML saved with a `.pdf` extension,
  not real PDFs, could not be removed due to a sandbox write-protection hook on the
  `datasheets/` directory): `iCE40HX4K-TQ144.pdf`, `REF3025AIDBZR.pdf`. **Recommend the
  user or next phase manually delete these two files** — do not open them as datasheets.
- **Mechanically unresolved, carried from sourcing** (no dimensional drawing obtained in
  this phase either): J1 (XKB U262-16XN-4BVC11 USB-C receptacle) and J2/J3 (Amphenol
  031-6575 BNC jack) — both panel-edge parts; verify physical part against the KiCad
  footprint before layout.
- **Low-confidence pins/facts, flagged explicitly in their summaries (not silently
  resolved):** OPA836 PD pin active-high/active-low polarity; AD9235 MODE pin's exact
  multi-level strap table (AGND=default assumed, not independently re-verified); iCE40
  VPP_FAST tie-off value; BAV99 common-anode-vs-desired-clamp-topology mismatch;
  X322512MSB4SI crystal load-capacitance value (27 pF chosen by inference, not confirmed
  against this exact MPN's own datasheet).
- Every summary's SOURCE line states exactly what was and wasn't independently verified
  this session — read it before trusting a spec number that isn't in a pin table.

## Escalation

none
