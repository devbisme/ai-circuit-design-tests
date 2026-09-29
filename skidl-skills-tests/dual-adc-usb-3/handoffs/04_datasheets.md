---
phase: 04_datasheets
agent: datasheet-librarian
circuit: dual_adc_usb
written: 2026-09-10T00:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 4 handoff — Datasheets

This is the completed handoff for a run that was resumed twice: the first death was an HTTP
429 after downloading PDFs but before writing any summary; the second was a context-budget
stop after closing the four sourcing gap items but before finishing the last three part
summaries and this document's block/receipt tables. Both prior sessions' work is preserved
and built on, not redone. No sibling design directory (`../dual-adc-usb-1`,
`../dual-adc-usb-2`) was read at any point across all three sessions.

## Decisions

1. **`AD9235BCPZ-40.pdf` on disk is the wrong part (AD9238 dual-ADC datasheet).** Use
   `AD9235BCPZ-40_try2.pdf` instead — confirmed this session to actually be the **full
   32-page** genuine AD9235 datasheet (an earlier pass of this summary wrongly called it a
   "4-page excerpt"; `pdfinfo` and a direct read of its Mode-Selection table and Outline
   Dimensions page both confirm all 32 pages are present and usable). EP dimension and MODE
   truth table were pulled from it this session, closing out that part's remaining gaps.
2. **THS4551 VS+/VS– absolute maximum is 5.5V; architecture wires it across the ±4.2V analog
   rails (8.4V total) — a datasheet-vs-architecture conflict, not resolved here.** See
   `datasheets/THS4551IRGTR_SUMMARY.md` Notes. **Escalate to the architect before the coder
   wires THS4551's VS+/VS– pins** — this is the single highest-severity open item this whole
   phase produced.
3. **`datasheets/` is delete/overwrite-protected this session (hook-enforced, confirmed by
   direct test, not assumed)** — every `rm` attempt on a stale/duplicate file in this
   directory was blocked. The cleanup the driver asked for (delete `_DRIVER_NOTE_partial_
   progress.md`, `UG803_raw.txt`, `AD9235BCPZ-40_try2.pdf/.txt`, `CAT24C128WI-GT3_v2.pdf`,
   surplus SiT1602 files) **could not be executed** — same constraint the very first session
   hit trying to replace the bad `AD9235BCPZ-40.pdf`. Instead, every stale/duplicate file is
   named explicitly below so the coder/next phase knows exactly which ones to ignore. This
   is a directory-hygiene debt, not a data-correctness one — no summary depends on a stale
   file.
4. **Two more mis-downloaded/dead files were found and worked around this session, following
   the same pattern as Decision 1:**
   - `datasheets/CAT24C128WI-GT3.pdf` and `datasheets/CAT24C128WI-GT3_v2.pdf` are both an
     **LCSC product page saved as HTML with a `.pdf` extension** (identical content,
     confirmed with `file`), not the real datasheet. The real PDF was recovered by scraping
     a `datasheet.lcsc.com` link out of that HTML and downloading it fresh —
     `datasheets/CAT24C128WI-GT3_real.pdf` is the one actually used for the summary.
   - `datasheets/SiT1602BI-22-33E-10.000000.pdf` and `datasheets/SiT1602BI.pdf` are both
     SiTime's "Page Not Found" HTML error page saved as `.pdf`. A third attempt (an
     LCSC-hosted PDF link for a *different* frequency variant, found via web search) also
     came back as an HTML anti-bot page and was discarded without being saved. **No usable
     SiT1602 PDF exists anywhere on disk** — `datasheets/SiT1602BI-22-33E-10.000000_SUMMARY.md`
     is written from family/package metadata only, with its pin table explicitly flagged
     low-confidence. Per the driver's explicit instruction, no further download attempts
     were made on this part.
5. **`LP5907MFX-1.8_NOPB_SUMMARY.md` covers both `LP5907MFX-1.8/NOPB` (U4) and
   `LP5907MFX-3.0` (U6)** — one datasheet (TI SNVS798Q), one die/pinout, only the
   factory-trimmed output voltage differs between the two BOM lines. Downloaded fresh from
   `ti.com` this session (valid, 52-page PDF).
6. **`X322524MOB4SI` (Y2, the clock_gen crystal) was not summarized this session** — it was
   not in the driver's explicit remaining-work list, and the coordinator's final message
   said "don't hunt further" / limited remaining work to SiT1602BI, CAT24C128WI-GT3, and
   LP5907. A PDF (`datasheets/X322524MOB4SI.pdf`, encrypted but valid, 1 page) already exists
   on disk, unread. Carried forward — see below.

## Summaries by block

| block_id | summary files |
|---|---|
| `usb_c_port` | `datasheets/TYPE-C_16PIN_2MD-073_SUMMARY.md` (J1 — footprint **confirmed match**, full 16-pin table); D1/D2 (`USBLC6-2SC6`) skipped, simple ESD array per sourcing note |
| `power_digital` | `datasheets/TLV62569DBVR_SUMMARY.md` (+3V3: R1=453k/R2=100k), `datasheets/TLV62568DBVR_SUMMARY.md` (+1V2: R1=R2=100k), `datasheets/LP5907MFX-1.8_NOPB_SUMMARY.md` (U4, +1V8, EN driven by `PWR_EN`), `datasheets/FNR3015S2R2MT_SUMMARY.md` (L1/L2 buck inductors — custom footprint built); U1 `AP2112K-3.3TRG1` skipped, simple fixed-3.3V LDO |
| `power_analog` | `datasheets/LM27762DSSR_SUMMARY.md` (FB+ R1=249k/R2=100k → +4.19V, FB– R3=243k/R4=100k → –4.18V), `datasheets/LP5907MFX-1.8_NOPB_SUMMARY.md` (U6 `LP5907MFX-3.0`, AVDD +3V0A, EN tied always-on — see Next phase must) |
| `analog_frontend` | `datasheets/AD8066ARZ-R7_SUMMARY.md` (R9 phase-reversal resolved: none within supply), `datasheets/THS4551IRGTR_SUMMARY.md` (EP confirmed 1.68mm; **VS+/VS– conflict, see Decisions #2**), `datasheets/KH-BNC50-3511_SUMMARY.md` (J2 ×2 — footprint **confirmed mismatch, not fixed**, see Next phase must); D3 (`BAV199`) skipped, simple clamp |
| `adc_pair` | `datasheets/AD9235BCPZ-40_SUMMARY.md` (SENSE/MODE/DNC/pinout + EP now confirmed 3.10×3.10mm) |
| `clock_gen` | `datasheets/SN74LVC2G34DBVR_SUMMARY.md`, `datasheets/SiT1602BI-22-33E-10.000000_SUMMARY.md` (**no usable datasheet — pin table low-confidence, see Carried forward**); `X322524MOB4SI` (Y2) not summarized, see Carried forward |
| `fpga_capture` | `datasheets/GW1NR-LV9QN88PC6-I5_SUMMARY.md` (R1 resolved: 71 I/O available, Bank3=PSRAM/+1V8, EP now confirmed 6.8×6.8mm) |
| `usb_controller` | `datasheets/CY7C68013A-56LTXC_SUMMARY.md` (full 56-QFN pin map, 8-bit slave FIFO), `datasheets/CAT24C128WI-GT3_SUMMARY.md` (full 8-pin SOIC table, A0/A1/A2/WP handling) |
| `aux_io` | — (`PESD3V3L1BA` skipped, simple ESD diode per sourcing note) |

## Next phase must

**Sourcing gap closure (from `03_sourcing.md` `## Next phase must` #1–4):**

1. **EP dimensions — CLOSED, all three.** AD9235 CP-32: **3.10×3.10mm** nominal
   (2.95–3.25mm range) — sourced footprint's EP3.45×3.45mm is too large, **build a corrected
   footprint before layout**. GW1NR-9 QN88P: **6.8×6.8mm** — sourced footprint's
   EP6.74×6.74mm is close but not exact, **build a corrected footprint**. THS4551 RGT-16:
   **1.68mm±0.07mm SQ** — sourced footprint's EP1.7×1.7mm confirmed correct to within
   0.02mm, no change needed.
2. **FNR3015S2R2MT custom footprint — CLOSED, built.**
   `footprints/Inductor_SMD_Custom.pretty/L_FNR3015S_3.0x3.0mm.kicad_mod` (2-pad SMD, pads
   0.8×2.7mm at X=±1.15mm). SKiDL footprint string:
   `'Inductor_SMD_Custom:L_FNR3015S_3.0x3.0mm'` — project-local library, user must add it in
   KiCad (Preferences → Manage Footprint Libraries → Project Specific Libraries, nickname
   `Inductor_SMD_Custom`, path `${KIPRJMOD}/footprints/Inductor_SMD_Custom.pretty`).
3. **BNC / USB-C land pattern confirmation — CLOSED, mixed result.** USB-C: **confirmed
   match**, sourced footprint is correct as-is (pad names, mounting-hole size, and pitch
   groups all match the datasheet exactly). BNC: **confirmed mismatch, not fixed** — real
   part uses 10.1mm hole spacing / Ø2.00mm+Ø0.90mm holes, nothing like the sourced
   footprint's 2.54/5.08mm grid; exact hole *count* is ambiguous from the one drawing view
   available, so **no custom footprint was built** (see `datasheets/KH-BNC50-3511_SUMMARY.md`
   for the safe-minimum pad assumption — 1× signal THT pad ~0.9–1.0mm drill + 2× Ø2.0mm
   ground/mount THT pads at 10.1mm pitch — the layout stage must still build and verify this
   footprint before Gerbers).
4. **8 feedback-divider resistor values — CLOSED.** TLV62569 (+3V3): R1=453k/R2=100k
   (`0402WGF4533TCE`/`0402WGF1003TCE`) → 3.318V. TLV62568 (+1V2): R1=R2=100k
   (`0402WGF1003TCE` ×2) → 1.200V exact. LM27762 FB+ (+4.2V): R1=249k/R2=100k
   (`0402WGF2493TCE`/`0402WGF1003TCE`) → 4.188V. LM27762 FB– (–4.2V): R3=243k/R4=100k
   (`0402WGF2433TCE`/`0402WGF1003TCE`) → –4.185V. Also resolves R6 (soft-start ramp): both
   bucks land comfortably inside Gowin's required windows.

**Per-IC pin-level facts the block coders need most:**

- **AD9235BCPZ-40 (U9/U10, `adc_pair`):** SENSE→AGND (selects internal 1.0V ref = 2Vpp
  span). MODE→AGND for offset-binary/DCS-off (matches internal 20kΩ pulldown default; tie
  explicitly, don't float). DNC pins (1,3,5,6) left truly unconnected. DRVDD (pin 16) needs
  its own 0.1µF+10µF decoupling, separate from AVDD. CLK is single-ended (not diff pair).
- **GW1NR-LV9QN88PC6/I5 (U12, `fpga_capture`):** VCCIO3→+1V8 (PSRAM bank), VCCIO1/2→+3V3,
  EPAD→GND (recommended, not mandatory). RECONFIG_N wired to FX2LP PA3. MODE0/1/2 strap for
  self-boot per DS117E (not restated in UG119E — confirm at code time if boot mode matters).
- **THS4551IRGTR (U8 ×2, `analog_frontend`):** PD (pin 12) tied HIGH for normal operation —
  do not float. FB+/FB– (not OUT+/OUT–) take the MFB filter network. **Do not wire VS+/VS–
  to ±4.2V until the architect resolves Decision #2.**
- **AD8066ARZ-R7 (U7 ×2, `analog_frontend`):** no phase reversal within supply range
  confirmed — R9 assumption from architecture holds.
- **LM27762DSSR (U5, `power_analog`):** FB+/FB– resistor values above; standard
  charge-pump cap count/placement per datasheet, ~4 flying/reservoir caps already in BOM.
- **TLV62569DBVR / TLV62568DBVR (U2/U3, `power_digital`):** feedback resistors above; both
  EN pins gated by `PWR_EN` (FX2LP PA0) per `net_plan.md`.
- **LP5907MFX-1.8/NOPB (U4, `power_digital`) / LP5907MFX-3.0 (U6, `power_analog`):** SOT-23-5
  pinout IN(1)/GND(2)/EN(3)/NC(4)/OUT(5). **EN defaults OFF if floating** (1MΩ internal
  pulldown) — U4's EN is driven by `PWR_EN` per `net_plan.md` (already gated, wire it
  there); **U6's EN is not listed in `net_plan.md`'s `PWR_EN` fan-out, so tie U6 EN directly
  to its own IN (+4V2A, always-on)** — it's already downstream of U5's gating, no separate
  enable net exists for it. Both need 1µF ceramic on IN and OUT (not optional).
- **CAT24C128WI-GT3 (U14, `usb_controller`):** SOIC-8, A0/A1/A2→GND for address 0x50 (if
  sole I2C device), WP tie explicitly (HIGH=protect, GND/float=writable — internal
  pulldown makes float safe but not recommended for production). SDA/SCL need external
  2.2–4.7kΩ pull-ups to VCC (check `sourced_bom.md` R37/R38 per `net_plan.md` line 16).
- **SiT1602BI-22-33E-10.000000 (U11, `clock_gen`):** **low-confidence pin table** (no
  primary datasheet obtained) — standard SMD3225-4P convention assumed: 1-OE/NC, 2-GND,
  3-OUT, 4-VDD. **Tie pin 1 to VDD if no OE control net exists** (no OE net appears in
  `net_plan.md`). **Physically confirm the pin-1 dot against this table before board
  bring-up** — this is the single lowest-confidence pin assignment in this whole phase.
- **CY7C68013A-56LTXC / SN74LVC2G34DBVR / GW1NR-9 / AD9235:** all fully confirmed, no
  additional flags beyond what's already in their individual summaries.

## Carried forward

- **THS4551 VS+/VS– vs. ±4.2V rail conflict — unresolved, escalate to architect.** See
  Decisions #2. Do not wire until resolved.
- **KH-BNC50-3511 (J2) footprint — confirmed wrong, not corrected.** See Next phase must #3.
  The layout stage must build a custom footprint using the dimensions in
  `datasheets/KH-BNC50-3511_SUMMARY.md`; the exact hole count (2 vs. possibly 4 board
  contact points) needs a physical sample or vendor DXF to fully resolve.
- **SiT1602BI-22-33E-10.000000 — no datasheet obtained, pin table unconfirmed.** Assume
  standard SMD3225-4P pinout (1-OE, 2-GND, 3-OUT, 4-VDD) per
  `datasheets/SiT1602BI-22-33E-10.000000_SUMMARY.md`, but physically verify pin 1 before
  committing to fab.
- **`X322524MOB4SI` (Y2, clock_gen crystal) — not summarized this session, out of explicit
  scope.** `datasheets/X322524MOB4SI.pdf` exists on disk (valid, 1 page, encrypted/print-only)
  but was not read. It's a plain 2-terminal crystal in the same SMD3225-4Pin footprint
  family as the SiT1602 oscillator; 12pF load caps are already in `sourced_bom.md`
  (`0402CG120J500NT`). Low risk (simple 2-pin part, standard crystal practice), but the
  coder should pull this datasheet before finalizing Y2's footprint/load-cap values if not
  already confident in them.
- **Stale/duplicate files in `datasheets/` — could not be deleted (directory is
  delete/overwrite-protected this session, confirmed by direct test). Ignore these; do not
  open them as the real datasheet:**
  - `AD9235BCPZ-40.pdf` — wrong part (AD9238). Use `AD9235BCPZ-40_try2.pdf`.
  - `CAT24C128WI-GT3.pdf`, `CAT24C128WI-GT3_v2.pdf` — both an LCSC HTML page, not a PDF. Use
    `CAT24C128WI-GT3_real.pdf`.
  - `SiT1602BI.pdf`, `SiT1602BI-22-33E-10.000000.pdf`, `SiT1602BI.txt` (empty) — all dead
    HTML/empty scratch. No valid SiT1602 PDF exists.
  - `_DRIVER_NOTE_partial_progress.md`, `UG803_raw.txt` — leftover scratch from the first
    (429-killed) session, not used by any summary.
  - `AD9235BCPZ-40_try2.txt`, `AD9235BCPZ-40.txt`, `AD8066ARZ-R7.txt`, `CY7C68013A-56LTXC.txt`,
    `LM27762DSSR.txt`, `SN74LVC2G34DBVR.txt`, `THS4551IRGTR.txt`, `TLV62568DBVR.txt`,
    `TLV62569DBVR.txt`, `UG803_GW1NR9_Pinout.txt` — raw `pdftotext` extraction scratch from
    earlier sessions, harmless but superseded by the `_SUMMARY.md` files; safe to ignore.
  - `UG803_GW1NR9_Pinout.pdf` — **not stale**, still a legitimate secondary source
    (cross-checked the GW1NR-9 PSRAM-bank claim), keep.

## Do not redo

- Every "Confirmed exact match" row in `sourcing/sourced_bom.md` — do not re-source.
- The critical-path/no-substitution calls on `GW1NR-LV9QN88PC6/I5` and `AD9235BCPZ-40`.
- The single `GND` net, 8-bit slave FIFO, ±4.2V rails, ÷11/×1.10 signal plan, FPGA-between-
  ADC-and-USB topology — carried from `02_architecture.md` and untouched here.
- All 4 sourcing gap items and all EP/footprint confirmations above — re-deriving any of
  these wastes a phase; the dimensions and the reasoning are recorded in the individual
  `_SUMMARY.md` files, cite them rather than re-reading the source PDFs.
- No sibling design directory read this phase (any of the three sessions).

## Receipt

- **15 summary files written**, covering **16 BOM part lines** (`LP5907MFX-1.8_NOPB_SUMMARY.md`
  covers both U4 and U6).
- **With a valid PDF obtained and read (14):** AD9235BCPZ-40, AD8066ARZ-R7,
  GW1NR-LV9QN88PC6-I5, CY7C68013A-56LTXC, THS4551IRGTR, LM27762DSSR, TLV62568DBVR,
  TLV62569DBVR, SN74LVC2G34DBVR, CAT24C128WI-GT3, LP5907MFX-1.8/NOPB (+ LP5907MFX-3.0),
  FNR3015S2R2MT, KH-BNC50-3511, TYPE-C_16PIN_2MD-073.
- **Summary-only, no usable PDF (1):** SiT1602BI-22-33E-10.000000 — 3 download attempts
  across 2 sessions all returned dead/anti-bot HTML; summary written from family/package
  metadata, pin table explicitly low-confidence.
- **Deliberately skipped, simple parts per scope rule (5):** AP2112K-3.3TRG1 (fixed LDO,
  U1), USBLC6-2SC6 (ESD array, D1/D2), SMAJ5.0A (TVS, FB1), BAV199 (clamp diode, D3 ×2),
  PESD3V3L1BA (ESD diode, aux_io).
- **Out of explicit scope, not attempted (1):** X322524MOB4SI (Y2 crystal) — see Carried
  forward.
- **Custom KiCad footprints built (1):** `L_FNR3015S_3.0x3.0mm.kicad_mod`.
- **Footprints confirmed correct as sourced (2):** TYPE-C_16PIN_2MD-073, THS4551 EP.
- **Footprints confirmed wrong, corrected footprint recommended but not built (1):**
  KH-BNC50-3511 (hole-count ambiguity, see Carried forward).
- **Footprints confirmed wrong, corrected dimensions given for layout to apply (2):**
  AD9235BCPZ-40 (EP), GW1NR-LV9QN88PC6/I5 (EP).
- **1 datasheet-vs-architecture conflict escalated, not resolved:** THS4551 VS+/VS– vs.
  ±4.2V rails.
- **Directory cleanup requested by the driver could not be executed** (hook-blocked); every
  stale file is named in Carried forward instead so nothing is silently trusted.

**Status: complete.**
