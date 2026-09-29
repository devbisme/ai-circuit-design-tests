---
phase: 04_datasheets
agent: datasheet-librarian
circuit: dual_adc_usb
written: 2026-09-20T12:40:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 4 handoff — Datasheets

## Decisions

1. **ADS5231's minimum clock is 20 MHz with the internal PLL enabled (default power-on
   state)** — confirmed from the datasheet's own electrical table (`ADCLK Input Sample
   Rate: PLL Enabled 20-40 MSPS`), not just JLC's parametric field. **The whole 20 MSPS +
   host-2:1-decimation architecture is legal exactly at the ADC's minimum, with zero margin
   below 20 MHz.** See `ADS5231IPAGT_SUMMARY.md` for a nuance carried forward (not acted on):
   the ADC can run as low as 2 MSPS with the PLL disabled, which the architecture did not
   know when it ruled out a direct-10-MSPS design — not re-decided here, flagged below.
2. **GW1NR-9C's rails are exactly what the architecture assumed: 1.2V core + 3.3V
   everywhere else.** Confirmed from Gowin's own DS117 (Table 4-2: VCC 1.14-1.26V for the LV
   variant; VCCX ≥2.375V; VCCOx 1.14-3.6V) and UG119E's per-package power-pin table for the
   exact QN88 package. No third rail needed, no board-exposed low-voltage bank exists (the
   in-package memory interface is not brought out to pins).
3. **Correction: the embedded memory is SDR SDRAM, not PSRAM.** Gowin's UG119E labels the
   QN88 package variant (this MPN) "SDRAM Embedded" and reserves "PSRAM Embedded" for QN88P.
   Documentation-only correction to architecture decision 2; no pin/rail/design impact.
4. **Correction: GW1NR-9C pin 12 is VCCIO3 (Bank 3), not a duplicate of the VCCX/VCCIO0 net**
   on pins 64/67/78. The EasyEDA/JLC pinout service mislabels pin 12; Gowin's own UG119E
   Table 3-7 is authoritative and used in the generated symbol. Both nets are 3.3V in this
   design so no electrical failure results, but they must stay separate SKiDL nets.
5. **X1 substituted: SX3M20.000B10F20TNN → OT252020MJBA4SL (LCSC C669067).** The originally
   sourced XO's datasheet publishes no jitter spec at all (checked directly, not just
   absence from JLC's parametric fields); the vetted second source specifies 0.7 ps RMS
   [12kHz-20MHz], 7x margin under the 5 ps budget. Package also shrinks from SMD3225-4P to
   SMD2520-4P — footprint updated accordingly. This executes architecture R-4's own
   pre-authorized fallback rule, not a new design decision.
6. **U8's ORG pin: tie to VCC for x16 organization**, required by FT232H's 245-sync-FIFO
   EEPROM template. No manufacturer datasheet exists for this specific Tudi-branded part;
   resolved via the universal, cross-manufacturer 93C46 ORG-pin convention.
7. **FT232H crystal load caps: 16-18pF for C13/C14** (not the ~27pF FTDI shows as a generic
   example for a different crystal) — computed from the sourced 12pF-load crystal's own spec,
   Cext ≈ 2×(CL−Cstray).
8. **U2 (TLV75801PDRVR) FB divider: R1(OUT-to-FB)=11.8kΩ, R2(FB-to-GND)=10.0kΩ** for a
   1.199V output (target 1.20V ±3%), using VFB=0.55V read directly from TI's TLV758P
   datasheet — resolves what sourcing left as "coder to specify."
9. **X2 crystal (SX32Y012000BC1T001) pins 2/4 are labeled "GND" in the manufacturer's own
   pin-connect table but are almost certainly the crystal's second oscillator terminal**
   (case-bonded, not literal circuit ground) — see `SX32Y012000BC1T001_SUMMARY.md` for the
   full reasoning and the explicit warning not to tie them to the GND net without hardware
   verification.
10. **KH-BNC50-3511's stocked candidate footprint (`BNC_Amphenol_031-6575_Horizontal`) does
    not clearly match the part's mechanical drawing** — direct inspection of both the
    `.kicad_mod` file and the Kinghelm drawing found similar hole sizes (2.0mm/0.9mm) but an
    ambiguous pad-count/topology match. Escalated as a real open risk, not confirmed-safe.
11. **STC3MA06-T1 trimmer: custom footprint generated** from measured drawing dimensions —
    `footprints/Capacitor_Trimmer_SEHWA.pretty/C_Trimmer_SEHWA_STC3MA-2Pin_4.5x3.2mm.kicad_mod`.
    Closes the `⚠️ CUSTOM FP NEEDED` flag.
12. **6 symbols generated** for `⚠️ SYMBOL NEEDED` parts (see table below), verified pin-count-
    exact against their datasheets/EasyEDA data, `find-symbol.py` reports all EXACT.
13. **TLV75733PDRVR's sourced PREFIX match (`Regulator_Linear:TLV75733PDRV`) is confirmed
    real and correctly sized (7 pins, inherited via `extends "TLV75509PDRV"`)** — an initial
    naive pin-counting check flagged it as missing; direct inspection showed it exists.
    One naming caveat: the stock symbol's pin 7 is named "GND", not "EP" — both refer to the
    same exposed pad. A defensive alternate symbol (`dual_adc_usb:TLV75733PDRVR`, pin 7 named
    `EP`) was generated before this was resolved; either is usable.
14. **Skipped formal summaries** for USBLC6-2SC6, BAV99, SMF5.0CA, generic LEDs/headers/
    resistor arrays: EXACT KiCad symbol matches with extremely well-documented, low-risk
    standard pinouts — MCP data already fully specifies them per this phase's Skip criteria.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `datasheets/*_SUMMARY.md` (18 files) | Per-part specs, exact pin tables, notes | Before wiring that part in any block |
| `datasheets/*.pdf` (8 files: ADS5231IPAGT, GW1NR-LV9QN88PC6-I5, OPA355NA_3K, HL2301A, SX32Y012000BC1T001, OT252020MJBA4SL, STC3MA06-T1, KH-BNC50-3511) | Verified-correct-part datasheets | Whenever a summary references a page/figure |
| `symbols/dual_adc_usb.kicad_sym` | 6 generated symbols (see table below) | Coding — put `symbols/` on `KICAD9_SYMBOL_DIR` |
| `footprints/Capacitor_Trimmer_SEHWA.pretty/C_Trimmer_SEHWA_STC3MA-2Pin_4.5x3.2mm.kicad_mod` | Custom trimmer footprint | Placing C_top1/C_top2 |

## Summaries by block

| block_id | summary files |
|---|---|
| `usb_c_input` | `datasheets/TYPE-C-16PIN-2MD-073_SUMMARY.md` |
| `digital_power` | `datasheets/SY8089A1AAC_SUMMARY.md`, `datasheets/TLV75801PDRVR_SUMMARY.md`, `datasheets/HL2301A_SUMMARY.md`, `datasheets/FNR3015S2R2MT_SUMMARY.md` |
| `analog_power_ref` | `datasheets/TLV75733PDRVR_SUMMARY.md`, `datasheets/TLV9062IDR_SUMMARY.md` |
| `afe_channel` (ch1 + ch2) | `datasheets/KH-BNC50-3511_SUMMARY.md`, `datasheets/OPA355NA_3K_SUMMARY.md`, `datasheets/THS4551IRGTR_SUMMARY.md`, `datasheets/STC3MA06-T1_SUMMARY.md` |
| `adc_dual` | `datasheets/ADS5231IPAGT_SUMMARY.md` |
| `clock_20m` | `datasheets/OT252020MJBA4SL_SUMMARY.md` (replaces X1), `datasheets/SX3M20.000B10F20TNN_SUMMARY.md` (why superseded — read once) |
| `fpga_core` | `datasheets/GW1NR-LV9QN88PC6-I5_SUMMARY.md` |
| `usb_bridge` | `datasheets/FT232HL-REEL_SUMMARY.md`, `datasheets/93C46CT-I-SN-TUDI_SUMMARY.md`, `datasheets/SX32Y012000BC1T001_SUMMARY.md` |

## Generated symbols (`symbols/dual_adc_usb.kicad_sym`, all `find-symbol.py` EXACT)

| MPN | SKiDL symbol name | Pins | Footprint |
|---|---|---|---|
| ADS5231IPAGT | `ADS5231IPAGT` | 64 | `Package_QFP:TQFP-64_10x10mm_P0.5mm` |
| GW1NR-LV9QN88PC6/I5 | `GW1NR-LV9QN88PC6-I5` (slash→dash) | 89 (incl. EP=89) | `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` |
| SY8089A1AAC | `SY8089A1AAC` | 5 | `Package_TO_SOT_SMD:SOT-23-5` |
| OT252020MJBA4SL (replaces X1) | `OT252020MJBA4SL` | 4 | `Oscillator:Oscillator_SMD_Kyocera_KC2520Z-4Pin_2.5x2.0mm` |
| TYPE-C 16PIN 2MD(073) | `TYPE-C-16PIN-2MD-073` | 17 (incl. shield S1) | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` |
| TLV75733PDRVR (defensive, optional — stock symbol also works, see Decision 13) | `TLV75733PDRVR` | 7 (incl. EP=7) | `Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm` |

Use in SKiDL: `Part('dual_adc_usb', '<symbol name>')`, with `symbols/` on `KICAD9_SYMBOL_DIR`
(`rules/environment.md`).

## Next phase must

Addressed to the **block coders**, per block:

1. **`adc_dual`**: wire ADS5231's control pins per the strapping table in
   `ADS5231IPAGT_SUMMARY.md` — SEL=0, INT/EXT=1 (internal reference, no external ref IC
   exists in the BOM), MSBI=0 (confirm against `fpga_core`'s expected data format), OEA=OE B=0,
   STPD=0. Do not leave any of these floating.
2. **`fpga_core`**: tie GW1NR-9C's MODE0/MODE1 (pins 88/87) to GND via pull-downs for
   AUTOBOOT-from-internal-flash — **confirm against Gowin's UG289 configuration guide or the
   Sipeed Tang Nano 9K reference schematic before finalizing**, this file could not extract
   the MODE truth table (image-only page). Add EP (pin 89) as its own pin, tie to GND. Route
   `FPGA_CLK` to a GCLK-capable pin (11, 35, or 36), not an arbitrary IO.
3. **`clock_20m`**: use X1 = OT252020MJBA4SL (not the sourced_bom.md's SX3M20...), footprint
   `Oscillator:Oscillator_SMD_Kyocera_KC2520Z-4Pin_2.5x2.0mm`. Pin 1 (Tri-state) tied high or
   direct to `+3V3_A`.
4. **`usb_bridge`**: C13/C14 = 16-18pF (not ~27pF). U8 ORG pin (6) tied to VCC. Confirm the
   X2 crystal's pin 2/4 wiring per the caution in its summary before finalizing — do not
   ground them without checking.
5. **`digital_power`**: U2's FB divider = R1(top)=11.8kΩ, R2(bottom)=10.0kΩ for 1.20V.
6. **`analog_power_ref`**: U3 pin 4 (EN) is active-high, tie to the same enable logic as the
   rest of `digital_power`/`analog_power_ref`'s power sequencing, not left floating.
7. **`afe_channel` (both channels)**: OPA355's ENABLE (pin 5) must be tied directly to
   `+3V3_A` — the datasheet states the pin cannot float. THS4551's PD (pin 12) is believed
   active-low (tie to `+3V3_A` for normal operation) but was not independently confirmed
   against this part's own PDF — verify before board spin. Use the generated custom
   footprint for C_top1/C_top2 (`Capacitor_Trimmer_SEHWA:C_Trimmer_SEHWA_STC3MA-2Pin_4.5x3.2mm`).
8. **J2/J3 placement (afe_channel)**: resolve the KH-BNC50-3511 footprint question (Decision
   10) before finalizing the board outline — board-edge part, no room to fix later.

## Carried forward

- **GW1NR-9C QN88 exposed-pad exact size (6.74×6.74mm) not independently verified** against
  Gowin's package outline drawing (image-only page in UG119E) — verify before layout.
- **GW1NR-9C MODE[1:0] boot-strap truth table not extracted** (image-only in Gowin's UG289) —
  tentatively GND/GND for AUTOBOOT per common practice and the Tang Nano 9K reference design
  using this exact part, but not confirmed from a primary source in this pass.
- **THS4551's PD pin polarity assumed active-low** from TI's general THS45xx FDA convention,
  not confirmed against this part's own PDF (no valid PDF obtained, budget exhausted).
- **KH-BNC50-3511 footprint compatibility unresolved** — flagged as a real risk (Decision 10),
  not a placeholder.
- **SX32Y012000BC1T001 pins 2/4 wiring ("GND" label ambiguity)** — flagged, not resolved with
  full certainty; recommended treatment given, hardware verification still owed.
- **ADS5231's PLL-disabled 10 MSPS-direct alternative** — a datasheet fact the architecture
  didn't have when it built the 20 MSPS + host-decimation scheme; not acted on, since
  re-opening the clocking topology is out of this phase's scope and the design is already
  sourced/symbol-generated around the current approach. Surfaced for whoever next reviews
  the architecture.
- **No PDF obtained** (2/2 or budget-limited attempts used, MCP/pinout data used instead) for:
  FT232HL-REEL, THS4551IRGTR, TLV75733PDRVR, TLV75801PDRVR (a real TI PDF was read manually
  via WebFetch and its facts are in the summary, but rejected by the automated validator so
  not cached to `datasheets/`), TLV9062IDR, SY8089A1AAC, FNR3015S2R2MT.
- **Everything the architecture and sourcing phases already carried forward still stands**
  unless explicitly corrected above (filter values provisional, F3 via host decimation, no
  AEC-Q100/Q200 requirement, firmware/USB descriptors out of scope, ±5% C0G substitution on
  C_bot/C_f, E96 resistor rounding).

## Do not redo

- The ADS5231 minimum-clock-frequency and GW1NR-9C supply-rail questions — both closed with
  primary-source datasheet citations (Decisions 1–2), do not re-derive.
- The X1 substitution (Decision 5) — executes architecture's own pre-authorized fallback
  rule, not open for re-litigation without new jitter data on the original part.
- The U2 FB-divider values (Decision 8) and U8 ORG-pin tie (Decision 6) — both closed with
  a formula/authoritative convention, not "coder to specify" anymore.
- The 6 generated symbols and their pin tables — verified pin-count-exact, do not regenerate.
- Skipped-summary decisions for EXACT-matched, well-documented discretes (Decision 14).

## Receipt

- **18 datasheet summaries written**, 8 real PDFs downloaded and validated (correct part),
  ~10 parts summarized from MCP/pinout data alone after exhausting the 2-URL-per-part budget
  or because the part is freely substitutable/non-critical.
- **6 KiCad symbols generated**, all pin-count-verified against datasheet/EasyEDA data,
  `find-symbol.py` reports 6/6 EXACT.
- **1 custom footprint generated** (STC3MA06-T1 trimmer), closing the sourcing phase's
  `⚠️ CUSTOM FP NEEDED` flag; KH-BNC50-3511's footprint question remains open (escalated,
  not closed).
- **1 part substitution** (X1, jitter-driven, pre-authorized by architecture R-4).
- **3 open architecture/sourcing questions fully closed** with primary-source citations: ADS5231
  min clock, GW1NR-9C rails, U8 ORG pin. **1 nuance surfaced but not acted on**: ADS5231's
  PLL-disabled low-clock mode.
- Cache: `use_cache: false` (blank-slate run) — nothing read from or written to the
  cross-project cache during lookups; publishing this run's summaries/PDFs/symbols to the
  cache is the last step, done after this handoff.
- status: complete
