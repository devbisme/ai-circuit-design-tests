# Verification pass — dual_adc_usb — 2026-09-21

Scope: four pin-level facts that reached the finished code resting on secondary sources
(EasyEDA, JLC catalogue fields, or a KiCad symbol alone). Closed against primary
manufacturer documents, in priority order. `circuits/` was not touched — this is a
verification-only pass; findings are recorded here and in the affected
`datasheets/*_SUMMARY.md` files.

## Summary table

| # | Part | Fact | Result | Primary source |
|---|------|------|--------|-----------------|
| 1 | W9825G6KH-6I (U40) SDRAM | Full 54-pin pinout | **VERIFIED — exact match, 0 mismatches** | Winbond "W9825G6KH" datasheet, Rev. A03, Jun. 01, 2016, §4/§5, p.3-4 |
| 2 | XC6SLX9-2TQG144C (U30) | Pin 124 name/bank/clock-capability | **VERIFIED — exact match** | Xilinx UG385, v2.3, May 12, 2014, Table 2-2, p.30 |
| 2 | XC6SLX9-2TQG144C (U30) | Pin 56 name/bank/clock-capability | **VERIFIED — exact match** | Xilinx UG385, v2.3, May 12, 2014, Table 2-2, p.32 |
| 3 | TPS22919DCKR (U2) | `ON` pin polarity | **VERIFIED — active-high, as assumed** | TI SLVSEN5B, Rev. B, May 2019, §5, p.3 |
| 3 | TPS22919DCKR (U2) | `QOD` unconnected legitimacy | **VERIFIED — leaving QOD floating is a documented, valid configuration** | TI SLVSEN5B, Rev. B, May 2019, §5, p.3 |
| 4 | SN74LVC1G17DBVR (U8) | SOT-23-5 pin assignment | **VERIFIED — exact match** | TI SCES351Y, Rev. Y, Oct. 2025, §4, p.3 |

**No mismatches found. No code changes required.** All four facts, as they exist in
`circuits/dual_adc_usb/*.py` today, are correct against primary sources.

---

## 1. W9825G6KH-6I SDRAM (U40) — highest priority

Phase 4 could not obtain a Winbond PDF (LCSC's field URL is a JS-rendered React page that
returns HTML, not a PDF, to a plain HTTP fetch — same failure this pass hit again on the
first two attempts). Found by pulling the actual asset URL
(`https://datasheet.lcsc.com/datasheet/pdf/5a4279e684dc4dd98192d31e6bb13fca.pdf`) out of
the LCSC page's embedded Next.js SSR JSON rather than following the page's own canonical
`.pdf` URL. Downloaded and validated via `fetch-datasheet.py`; saved as
`datasheets/W9825G6KH-6I.pdf` (Winbond "W9825G6KH" datasheet, **Rev. A03, Jun. 01, 2016**,
42 pp — the base part number covering the -5/-5I/-6/-6I/-6J/-6L/-75 speed-grade family,
which is the correct document for the -6I grade used here).

Diffed §4 "Pin Configuration" (p.3) and §5 "Pin Description" (p.4) against the
`W9825G6KH-6I` symbol in `symbols/dual_adc_usb.kicad_sym`, pin by pin, all 54 pins:

**Result: every pin number and name matches exactly.** The only surface difference is that
`pdftotext` drops the overbar glyph Winbond draws over `CS`, `RAS`, `CAS`, `WE` (renders as
bare text) where the symbol spells them `CS#`, `RAS#`, `CAS#`, `WE#` — confirmed to be the
same active-low signals via Winbond's own §5 function descriptions ("Row Address Strobe",
"Column Address Strobe", "Write Enable", "Chip Select"), not a naming discrepancy.

This was the one keystone part resting wholly on a secondary source. It is now backed by a
verified primary datasheet with zero pin discrepancies — the highest-value close of this
pass.

## 2. XC6SLX9-2TQG144C (U30), pins 124 and 56

The two Xilinx PDFs already on disk (`XC6SLX9-2TQG144C.pdf` = DS160 "Family Overview", 11
pp; `XC6SLX9-2TQG144C_DS162.pdf` = DS162 "DC and Switching Characteristics", 55 pp) were
checked first, per instructions, before fetching anything else. **Confirmed neither
contains a per-pin table** — `grep`-ing both extracted texts for `GCLK`, `TQG144`, `Pin
Name` turns up only aggregate I/O-count tables and a footnote in DS162 explicitly deferring
to "UG385: Spartan-6 FPGA Packaging and Pinout Specification" for per-pin data. This matches
the caveat phase 4's own `XC6SLX9-2TQG144C_SUMMARY.md` already flagged. Since neither
on-disk document could answer the question and the two assignments (CLK_FPGA, IFCLK) are
flagged unrecoverable-if-wrong, fetched UG385 (v2.3, May 12, 2014, 364 pp; genuine document,
confirmed by title page, revision history table, and full table of contents) as the one
additional primary source needed.

Table 2-2 "TQG144 Package—LX4 and LX9" (p.30-33):

| Pin | Datasheet Pin Description | Bank | BUFIO2 region |
|-----|---------------------------|------|----------------|
| P124 | `IO_L37P_GCLK13_0` | 0 | TR |
| P56 | `IO_L30P_GCLK1_D13_2` | 2 | BR |

Both match the symbol's pin names exactly. Both contain `_GCLKn_`, and UG385's own pin-type
glossary (p.16) states: *"GCLK — These clock pins connect to global clock buffers... These
pins become regular user I/Os when not needed for clocks"* — confirming pin 124
(`CLK_FPGA`, the ADC/FPGA sample-clock input) **is a genuine global-clock-capable input, not
a plain I/O**. The capture-clock path is sound as wired. Pin 56 (`IFCLK`, the FX2LP→FPGA
FIFO strobe) is also GCLK-capable, which is incidental here since it's not routed through a
DCM/PLL in this design, but is not a problem either.

UG385 was not placed in `datasheets/` — `fetch-datasheet.py`'s right-part guard correctly
rejected it (it's a 364-page, 9-package family document that doesn't mention "XC6SLX9" by
name in its first pages), so the verified excerpt is recorded in the summary/here instead of
the raw file.

## 3. TPS22919DCKR (U2), `ON` polarity and `QOD`

No primary datasheet was on disk; the active-high assumption rested on two JLC catalogue
fields. Fetched the TI datasheet directly (`https://www.ti.com/lit/ds/symlink/tps22919.pdf`
succeeded on the first try — no LCSC JS-wall problem for this one); saved as
`datasheets/TPS22919DCKR.pdf` (TI SLVSEN5B, **Rev. B, Oct 2018 / rev. May 2019**).

§5 "Pin Configuration and Functions" (p.3), Pin Functions table:
- Pin 3, `ON`: **"Active high switch control input. Do not leave floating."** — confirms
  the assumed polarity exactly. (A "Smart ON pin pull down", RPD ≈ 530 kΩ typ, holds ON low
  — switch off — until deliberately driven high, then disconnects to save power; documented
  in §1 Features.)
- Pin 5, `QOD`: description lists three valid configurations, one of which is **"Disabling
  QOD by leaving pin floating."** Confirmed in code: `circuits/dual_adc_usb/usb_front.py`
  line 140 does `U2['QOD'] += NC` — the design already uses exactly this documented
  configuration. Consequence: VOUT is not actively discharged by the internal 24 Ω FET when
  U2 turns off; it decays through the load's own leakage instead. No functional problem for
  this design, just worth knowing if a fast power-cycle requirement appears later.

Both facts verified, no code change needed.

## 4. SN74LVC1G17DBVR (U8)

No primary datasheet was on disk; pin mapping came from the local generic
`74xGxx:74LVC1G17` KiCad symbol alone. Fetched
`https://www.ti.com/lit/ds/symlink/sn74lvc1g17.pdf` (succeeded first try); saved as
`datasheets/SN74LVC1G17DBVR.pdf` (TI SCES351Y, **Rev. Y, Jul 2001 / rev. Oct 2025**).

§4 "Pin Configuration and Functions" (p.3), DBV package (SOT-23-5), top view:

| Pin | Name | Function |
|-----|------|----------|
| 1 | N.C. | Not connected |
| 2 | A | Input |
| 3 | GND | Ground |
| 4 | Y | Output |
| 5 | VCC | Power |

Matches the local `74xGxx:74LVC1G17` symbol exactly, and matches how the code already uses
it: `circuits/dual_adc_usb/clocking.py` does `clk_buf += U8[2]` (A/in), `clk_out += U8[4]`
(Y/out), `vdd += U8[5]` (VCC), `gnd += U8[3]` (GND). No mismatch, no code change needed.

---

## Files touched this pass

- `datasheets/W9825G6KH-6I.pdf` (new — Winbond primary source)
- `datasheets/TPS22919DCKR.pdf` (new — TI primary source)
- `datasheets/SN74LVC1G17DBVR.pdf` (new — TI primary source)
- `datasheets/W9825G6KH-6I_SUMMARY.md` (updated — pinout marked VERIFIED, Load-bearing
  facts section added)
- `datasheets/XC6SLX9-2TQG144C_SUMMARY.md` (updated — pins 124/56 marked VERIFIED,
  Load-bearing facts and Notes extended; rest of the 144-pin table remains unverified
  pin-by-pin, only these two pins were in scope)
- `datasheets/TPS22919DCKR_SUMMARY.md` (rewritten — ON polarity and QOD behavior marked
  VERIFIED with a new Load-bearing facts section)
- `datasheets/SN74LVC1G17DBVR_SUMMARY.md` (rewritten — pinout marked VERIFIED with a new
  Load-bearing facts section)
- `circuits/` — **not touched**, per instructions (another agent reviewing it concurrently)
- `handoffs/` — **not touched**, per instructions

Xilinx UG385 (Spartan-6 packaging/pinout spec) was read for fact #2 but is not saved in
`datasheets/` — it's a multi-package family document that fails `fetch-datasheet.py`'s
right-part check (doesn't mention "XC6SLX9" in its first pages). Its relevant excerpt
(Table 2-2, p.30-33) is transcribed into `XC6SLX9-2TQG144C_SUMMARY.md` instead.
