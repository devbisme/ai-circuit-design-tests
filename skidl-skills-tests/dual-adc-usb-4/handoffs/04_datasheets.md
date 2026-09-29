---
phase: 04_datasheets
agent: datasheet-librarian
circuit: dual_adc_usb
written: 2026-09-10T23:40:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 4 handoff — Datasheets

## Decisions
- **All 6 `⚠️ SYMBOL NEEDED` parts resolved by generation**, not by finding/reusing an
  existing library symbol: SY6280AAC, TPS7A2033PDBVR, BAV199, OPA354AIDBVR, ADS5231IPAGT,
  GW1NR-LV9QN88PC6/I5. All 6 verified `EXACT` via `find-symbol.py` against
  `symbols/dual_adc_usb.kicad_sym`. Pin counts verified against source data (5, 5, 3, 5, 64,
  89 respectively — GW1NR count includes the EP as its own pin).
- **U15 (GW1NR-9) `⚠️ CUSTOM FP NEEDED` resolved as CONFIRMED, not replaced.** Gowin's own
  UG119E package outline gives EP = 6.8×6.8mm nominal; the candidate KiCad footprint
  (`ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm`) is 6.74×6.74mm — a 60µm/side EP shrink,
  standard practice, not a defect. Body (10×10mm) and pitch (0.4mm) match exactly. **Use this
  footprint as-is; no custom footprint was built.** Full reasoning in
  `datasheets/GW1NR-LV9QN88PC6-I5_SUMMARY.md` Decisions.
- **U15 pin 12 corrected from `VCCX/VCCO0` (JLC/EasyEDA label) to `VCCIO3`** in the generated
  symbol, per Gowin's own UG119E Table 3-8. This is a real pin-name error in the third-party
  EasyEDA data, not a stylistic choice — see that summary for the full cross-check.
- **TPS7A2033PDBVR and OPA354AIDBVR pin orders independently VERIFIED** against real TI
  datasheets (SBVS338H p.4, SBOS233H Table 5-1) — both exactly match the JLC/EasyEDA data used
  to build the symbols. Sourcing's caution about not blindly trusting a lookalike symbol is
  resolved: the generated symbols are now datasheet-confirmed, not just EasyEDA-sourced.
- **ADS5231IPAGT's 64-pin table spot-checked** against TI SBAS295A p.10's pin diagram (pins
  1-7, 42-48, 64) — exact match, no corrections needed.
- **BAV199's series-pair topology confirmed** from the genuine Nexperia datasheet: pin1=A1
  (anode 1), pin2=K2 (cathode 2), pin3=K1/A2 (series junction, cathode-1/anode-2 common node).
  Neither `Diode:BAV19` nor `Diode:BAV99` was reused, per sourcing's explicit flag.
- **LM27762 FB-divider values computed** (resolves sourcing's `## Next phase must` #3):
  R6=107kΩ, R7=100kΩ → VOUT+≈2.484V; R8=105kΩ, R9=100kΩ → VOUT-≈-2.501V (both 1% E96, target
  ±2.50V). These are target values for the coder/next sourcing pass to place as 0402 1%
  Basic-tier resistors — exact LCSC MPNs were not looked up (out of this phase's scope).
- **SY6280AAC ISET formula recovered** (resolves sourcing's `## Next phase must` #4):
  ILIM(A) = 6800/R_ISET(Ω). R3 = 8.45kΩ (1% E96) → ILIM≈0.805A, matching the architecture's
  ≈0.8A target. Formula sourced from Silergy's AN_SY6280 application note (web search, PDF of
  the full datasheet was not obtainable) — not independently re-verified against a local PDF.
- **X1 jitter spec (≤5ps rms) could NOT be confirmed** — the only obtainable datasheet for
  SX3M20.000B10F20TNN is a 2-page generic family catalog with no jitter/phase-noise data at
  all. This is now a confirmed **gap**, not just an unverified assumption — see Carried forward.
- **X1's symbol/footprint pairing looks wrong**: `sourced_bom.md` lists symbol `Device:Crystal`
  (a 2-pin passive part) against a 4-pin **active** oscillator footprint
  (`Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm`). This was not caught by sourcing. Flagged for
  the coder to resolve before ERC — see Carried forward and
  `datasheets/SX3M20.000B10F20TNN_SUMMARY.md`.
- **Skipped generic/already-fully-specified parts** (no summary written, per scope rules):
  FB1-FB8 (ferrite beads — DCR/impedance already in `sourced_bom.md` notes), VC1/VC2 (trimmer
  caps — mechanical-drawing verification against SEHWA was flagged by sourcing but is a
  footprint/mechanical task, not a spec-lookup one; not resolved this phase, see Carried
  forward), J1-J5 (connectors), all resistors/capacitors identified only by value.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `datasheets/*_SUMMARY.md` (19 files) | Spec table + verified pinout + notes, one per significant part | Before writing any block that instantiates that part |
| `datasheets/*.pdf` (12 MPNs, 13 files) | Source datasheets for parts where a valid PDF was obtained | Cross-checking a summary claim or reading an application circuit figure |
| `symbols/dual_adc_usb.kicad_sym` | 6 generated symbols: SY6280AAC, TPS7A2033PDBVR, BAV199, OPA354AIDBVR, ADS5231IPAGT, GW1NR-LV9QN88PC6/I5 | Whenever the coder instantiates any of these 6 parts — `Part('dual_adc_usb', '<name>')` with `symbols/` on `KICAD9_SYMBOL_DIR` |

## Next phase must
1. **Use the generated symbols for the 6 flagged parts**, library name `dual_adc_usb`, exactly
   as named in the Artifacts row above. Add `symbols/` to `KICAD9_SYMBOL_DIR` (colon-separated,
   alongside the system path) per `rules/environment.md`.
2. **Resolve the X1 oscillator symbol mismatch** before ERC: `Device:Crystal` (2-pin) is wrong
   for a 4-pin active oscillator. Either source/generate a proper 4-pin oscillator symbol
   (OE/GND/OUT/VDD) or confirm how SKiDL should map the extra 2 pins — do not leave OE/VDD
   unconnected by accident. See `datasheets/SX3M20.000B10F20TNN_SUMMARY.md`.
3. **U15 GW1NR-9 pin assignment: do not use any Bank0/IOT-prefixed pin (68-88, except MODE0/
   MODE1 at 87/88) for user I/O** without first confirming against Figure 3-8 in
   `datasheets/GW1NR-9-UG119-package.pdf` p.15 (a graphic the librarian could not text-extract).
   Gowin's own quantity table gives Bank0 = 0 usable I/O (PSRAM-locked to 1.8V) despite the
   EasyEDA pin table showing ordinary-looking IOT* names for those pins. Budget the FPGA's I/O
   only from Banks 1-3 (71 total: 25/11/4, 23/11/11, 23/6/3 single-ended/diff-pair/LVDS).
4. **Tie U15 pin 89 (EP) to GND** in the SKiDL netlist — it is now a real pin in the generated
   symbol (per this phase's own generation rule for exposed pads), not implicit.
5. **Place R3 = 8.45kΩ, R6 = 107kΩ, R7 = 100kΩ, R8 = 105kΩ, R9 = 100kΩ** (all 1% E96, 0402,
   Basic-tier per the existing passive-sourcing pattern) to close the sourcing-phase's open
   resistor values. If a later phase needs different exact standard values, keep to the
   formulas in `datasheets/LM27762DSSR_SUMMARY.md` and `datasheets/SY6280AAC_SUMMARY.md`.
6. **PD polarity on THS4521IDGKR (pin 7) should be confirmed** from the full datasheet
   (`datasheets/THS4521IDGKR.pdf`) before the coder ties it to a fixed rail — not resolved this
   phase (see that summary).

## Carried forward
- **X1 jitter (≤5ps rms) is unconfirmed** — no obtainable datasheet contains jitter/phase-noise
  data for this exact MPN (SX3M20.000B10F20TNN). This is a real, still-open CP-spec risk, not
  just a documentation gap — carried unchanged from architecture/sourcing, now with more
  certainty that it cannot be closed by more datasheet reading (a family catalog sheet is all
  that exists for this manufacturer's public documentation).
- **X1 land pattern not independently re-verified** — the available datasheet PDF is
  graphics-only for pin tables and does not include a usable land-pattern drawing; the generic
  Abracon-pattern footprint remains unverified, carried unchanged from sourcing.
- **VC1/VC2 (STC3MA06-T1) mechanical-drawing verification against SEHWA's 4.5×3.2mm body was
  not performed this phase** — this is a footprint/mechanical check, not a datasheet-spec
  lookup, and fell outside this phase's explicit task scope (6 symbols + U15 footprint). Still
  open, carried unchanged from sourcing.
- **7 parts have no local PDF** (summary-only, built from MCP part data + pin data +, where
  used, one cross-referencing web search): USBLC6-2SC6, SY6280AAC, TLV75512PDBVR,
  TLV75518PDBVR, SMF5.0A, FT232HL-REEL... — correction, FT232H PDF *was* obtained; the accurate
  no-PDF list is: **USBLC6-2SC6, SY6280AAC, TLV75512PDBVR, TLV75518PDBVR, SMF5.0A,
  X322512MSB4SI** (6 parts). Each summary states why (anti-bot wall, wrong-part guard
  rejection, or budget not spent on a low-risk generic part) and the confidence level in the
  data used instead.
- **R6-R9 and R3 values are computed targets, not sourced LCSC parts.** The next sourcing/
  coding pass still needs to pick actual LCSC MPNs at these resistances (or the nearest
  in-stock 1% E96 neighbor) — this phase only closed the formula/value gap, not procurement.

## Do not redo
- Every MPN/LCSC#/footprint in `sourcing/sourced_bom.md` not touched by this handoff's
  Decisions is unchanged — use verbatim, per sourcing's own `## Do not redo`.
- U3 = genuine TI TLV1117LV33DCYR (455mV@1A dropout, confirmed again this phase from its own
  datasheet) — not the JSMSEMI clone. Final.
- U4 = TLV75512PDBVR (not AP2112K-1.2TRG1). Final.
- Y1 crystal = X322512MSB4SI, CL=20pF, C65/C66 = 22pF C0G. Final — and confirmed in this phase
  to be a genuine 2-pin passive part (unlike X1, which is a 4-pin active oscillator — don't
  confuse the two symbol situations).
- BAV199, TPS7A2033PDBVR, OPA354AIDBVR, SY6280AAC, ADS5231IPAGT, GW1NR-LV9QN88PC6/I5 symbols:
  generated and verified this phase — do not regenerate or substitute a lookalike library part.
- U15 footprint: `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` — confirmed
  this phase, use as-is.

## Summaries by block

| block_id | summary files |
|---|---|
| `usb_power_in` | `datasheets/USBLC6-2SC6_SUMMARY.md`, `datasheets/SMF5.0A_SUMMARY.md`, `datasheets/SY6280AAC_SUMMARY.md` |
| `power_rails` | `datasheets/TLV1117LV33DCYR_SUMMARY.md`, `datasheets/TLV75512PDBVR_SUMMARY.md`, `datasheets/TLV75518PDBVR_SUMMARY.md`, `datasheets/TPS7A2033PDBVR_SUMMARY.md` |
| `bipolar_supply` | `datasheets/LM27762DSSR_SUMMARY.md` |
| `analog_front_end` | `datasheets/OPA354AIDBVR_SUMMARY.md`, `datasheets/THS4521IDGKR_SUMMARY.md`, `datasheets/BAV199_SUMMARY.md` |
| `adc` | `datasheets/ADS5231IPAGT_SUMMARY.md` |
| `sample_clock` | `datasheets/SX3M20.000B10F20TNN_SUMMARY.md` |
| `usb_bridge` | `datasheets/FT232HL-REEL_SUMMARY.md`, `datasheets/93LC56BT-I-OT_SUMMARY.md`, `datasheets/X322512MSB4SI_SUMMARY.md` |
| `fpga_core` | `datasheets/GW1NR-LV9QN88PC6-I5_SUMMARY.md` |
| `io_expansion` | `datasheets/SN74LV4T125PWR_SUMMARY.md`, `datasheets/SN74LV1T34DCKR_SUMMARY.md` |

## Receipt
19 parts summarized (12 MPNs with a verified PDF on file, 6 summary-only after exhausting the
2-URL budget on lower-risk generic parts, 1 more — SX3M20.000B10F20TNN — with a PDF that turned
out to contain no jitter data). 6/6 flagged symbols generated and `EXACT`-verified in
`symbols/dual_adc_usb.kicad_sym` (171 total pins). U15 footprint CONFIRMED (not replaced). 1
real pin-label error caught and corrected (U15 pin 12). 1 symbol/footprint pin-count mismatch
caught and flagged, unresolved (X1). 2 open resistor formulas resolved with target values (R3,
R6-R9). Cache: disabled (blank-slate run, `use_cache: false`) — nothing read or written to
`part-cache.py`, skipping the publish step per its own blank-slate no-op behavior.
status: complete.
