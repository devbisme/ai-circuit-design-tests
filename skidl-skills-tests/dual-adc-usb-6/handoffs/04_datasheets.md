---
phase: 04_datasheets
agent: datasheet-librarian
circuit: dual_adc_usb
written: 2026-09-21T00:00:00Z
status: partial
revision: 3
next_phase: 05_coding
---

# Phase 4 handoff — Datasheets

`use_cache = false` for this run — no cache reads/writes were performed (per explicit
instruction); every fact below was derived fresh this pass.

## Revision 2 — two closures (narrow re-invocation, all other summaries/symbols untouched)

This revision addressed exactly two items from revision 1; nothing else in this handoff or
in `datasheets/`/`symbols/` was re-derived or re-checked.

1. **CY7C68013A + 24LC64 boot-EEPROM address/strap — now VERIFIED from two primary
   sources, not community-sourced.** Read `datasheets/CY7C68013A-56LTXC.pdf` (already on
   disk from revision 1) directly for its own boot-EEPROM section: Document Number
   38-08032 Rev. AD, printed page 16 of 74, section "I2C Interface Boot Load Access" and
   **Table 8, "Strap Boot EEPROM Address Lines to These Values"**, which names "24LC64"
   explicitly as its 8K-byte example part and lists the required strap as **A2=0, A1=0,
   A0=1**. Cross-checked against `datasheets/24LC64-I-SN.pdf` (also already on disk), DS21189T
   p.7 §5.0 "Device Addressing" / Figure 5-1, whose control-byte format (`1010 A2 A1 A0
   R/W`) confirms this strap gives I2C address **0x51 (7-bit) / 0xA2 (8-bit write)**. **This
   exactly matches the community-sourced answer reported in revision 1** (A0=1→VCC,
   A1=0→GND, A2=0→GND) — the community answer was correct, and is now backed by the
   CY7C68013A's own datasheet table plus the 24LC64's own control-byte format, not a
   developer-forum/AN50963 reference. AN50963 itself was not needed — the primary datasheet
   already on disk contained the answer. Both `datasheets/CY7C68013A-56LTXC_SUMMARY.md` and
   `datasheets/24LC64-I-SN_SUMMARY.md` are updated with the verified load-bearing facts and
   citations. This closes the corresponding row in Unverified keystone facts (below).
2. **TPH2501-TR datasheet obtained and symbol generated.** LCSC's datasheet field URL
   still returns HTML (retried, still fails, as in revision 1); one web search surfaced the
   manufacturer's own document server (`static.3peak.com/res/doc/ds/Datasheet_TPH2501-TPH2502-
   TPH2503-TPH2504.pdf`), which downloaded as a valid 26-page PDF —
   `datasheets/TPH2501-TR.pdf`. Its Table 2 "Pin Functions: TPH2501, TPH2503" (p.5) gives the
   5-pin SOT-23-5 pinout: 1=Out, 2=-VS, 3=+In, 4=-In, 5=+VS — exact electrical match to what
   `jlc_get_pinout` independently reported (OUT/VS-/+IN/-IN/VS+, same assignment, EasyEDA just
   suffixes the sign on VS). Confirmed **no SHDN/enable pin** on this 5-pin part (that's the
   6-pin TPH2503 variant in the same datasheet family). Generated symbol
   `dual_adc_usb:TPH2501-TR` in `symbols/dual_adc_usb.kicad_sym` (kipart merge into the
   existing library, now 10 parts / 20 symbol blocks), verified `EXACT` via
   `find-symbol.py TPH2501-TR`. `datasheets/TPH2501-TR_SUMMARY.md` rewritten with the full
   verified pinout, bypass-cap notes, and absolute-max supply differential (7.0 V).
   `HX PZ1.27-2x3P TP` intentionally **not** touched this pass (told to skip it — coder uses
   a generic connector symbol).

## Revision 3 — SY8089AAC replaced by AP62200TWU-7 (sourcer re-source), summary/symbol written

Between revision 2 and this pass, the `power` block's buck regulator (U3/U4, +3V3D and
+1V2) was re-sourced by the sourcer: `SY8089AAC` failed SPEC R4 (NRND at manufacturer, no
datasheet obtainable — exactly the gap flagged as a genuine keystone risk in revisions 1–2)
and was replaced with **AP62200TWU-7** (Diodes Incorporated, LCSC C2895288). The sourcer
downloaded its full datasheet to `datasheets/AP62200TWU-7.pdf` (DS41957 Rev. 6-2, 23pp);
this pass read it in full and:

1. **Wrote `datasheets/AP62200TWU-7_SUMMARY.md`** to the standard format — full 6-pin
   TSOT26 pinout (verified from the datasheet's own Pin Descriptions table, p.3), the
   VFB/EN/BST load-bearing facts below, and the FB-divider values for both instances
   cross-checked against the datasheet's own Eq. 8.
2. **Verified from the primary datasheet what could not be verified before**: **VFB =
   0.763 V typ** (0.747–0.778 V full temp range; this is the AP62200**T** sub-variant —
   the base AP62200/AP62201 in the same datasheet family is 0.800 V, a distinct number not
   to be confused with this part's), and **EN is active-high**, 1.20 V typ turn-on
   threshold, with an **internal 1.5 µA pull-up current source from VCC to EN** that
   auto-enables the device if EN is left floating (datasheet p.13 §3 "Enable", quoted
   verbatim in the summary). These replace the two now-moot SY8089AAC rows in `##
   Unverified keystone facts` (dropped below — the part they concerned is no longer in the
   design).
3. **Generated symbol `AP62200TWU-7`** into `symbols/dual_adc_usb.kicad_sym` (kipart
   merge; library now 11 parts / 22 symbol blocks) — verified `EXACT` via
   `find-symbol.py AP62200TWU-7`. Pins: 1=GND(power_in), 2=SW(output), 3=VIN(power_in),
   4=FB(input), 5=EN(input), 6=BST(passive) — matches the datasheet's TSOT26 column exactly.
4. **EN auto-enable vs. rail sequencing**: `handoffs/02_architecture.md` decision #12
   already commits to a specific sequencing (`+1V2` EN tied directly to VBUS_SW, no delay;
   `+3V3D` EN driven through an R18(100kΩ)/C22(100nF) RC ≈2.74 ms delay — i.e. FPGA core
   leads I/O rail). Because neither instance's EN is left floating, the part's auto-enable
   behavior does not by itself break that ordering. However, the internal 1.5 µA EN
   pull-up adds current onto the +3V3D instance's RC delay node in addition to R18/C22's
   own charging current, so the **real delay will be somewhat shorter than the 2.74 ms
   figure computed without accounting for that internal source** — flagged as a note in the
   new summary for phase 5 to account for, not recomputed exactly here (topology
   confirmation against `net_plan.md` needed first). The `+1V2` instance's direct
   VBUS_SW-to-EN tie is unaffected by the pull-up (low-impedance drive dominates).

## Decisions

1. **R2 (oscillator jitter) — SETTLED. X1 supersedes `sourced_bom.md`'s MPN.**
   `SX3M10.000B10F20TNN` (LCSC C5452682) was downloaded and read in full (9 pages) — it
   publishes **no RMS phase-jitter or period-jitter figure at all**, confirmed absent, not
   merely unfound. Replacement: **TAITIEN OXETDLJANF-10.000000 (LCSC C17609541)**, same
   SMD3225-4P footprint, in stock (50 pcs, 5x margin), datasheet-published **RMS Phase
   Jitter (12kHz–20MHz) ≤ 1 ps** — 7x inside the ~7 ps RMS budget. Update `X1`'s MPN in the
   BOM to this part; footprint and 4-pin pinout are unchanged (OE/GND/OUT/VDD). See
   `datasheets/OXETDLJANF-10.000000_SUMMARY.md`.
2. **AD9235BCPZ-40 second source — NOT a fully-verified drop-in for pins 1/3.** Both
   datasheets were obtained and read. Corrected sourcing's pin-diff count: only 2 pins
   (1=MODE2, 3=OE) are genuinely AD9237-specific control pins — pin 5 is DNC on **both**
   parts (sourcing's "GC" label at pin 5 is an EasyEDA artifact, not a real ADI mnemonic).
   AD9237's MODE2/OE must be strapped to a static DC level for normal operation (not left
   floating even on the primary part). Neither datasheet states whether AD9235's DNC pins
   1/3 tolerate an externally-applied DC tie. **Recommendation: route MODE2/OE through
   DNP-able resistors, not direct traces**, so AD9235 can be substituted with those two
   pins genuinely floating. See `datasheets/AD9235BCPZ-40_SUMMARY.md` for the full
   reasoning — this is now a designed-in mitigation, not an open question, but the
   underlying DNC-tolerance fact itself remains unverified (see Unverified keystone facts).
3. **XC6SLX9 VCCAUX resolved: tie to +3V3D, not a separate 2.5V rail.** Xilinx DS162
   (exact-MPN mirror) Table 2 lists VCCAUX=3.3V as an equally-valid Recommended Operating
   Condition alongside 2.5V. This design's power block only has +3V3D/+1V2 — no missing
   rail. **The coder must explicitly tie all VCCAUX pins to +3V3D.**
4. **CY7C68013A + 24LC64 boot-address pairing — flagged as the highest-risk pin-strap
   question in this design**, matching the exact failure class the task background
   warns about. FX2LP needs the boot EEPROM at I2C address 0x51 (0xA2), requiring
   24LC64's A0=1 (pull to VCC), A1=0, A2=0 (pull to GND) — NOT the common default of
   all-address-pins-to-GND. `sourced_bom.md`'s R52–R55 (4 unallocated resistors in
   `usb_bridge`) fit this requirement almost exactly (3 address straps + 1 WP pull).
   **VERIFIED in revision 2** directly from the CY7C68013A datasheet's own Table 8 and the
   24LC64 datasheet's own control-byte format — see Revision 2 section above and
   `CY7C68013A-56LTXC_SUMMARY.md` / `24LC64-I-SN_SUMMARY.md`. No longer in Unverified
   keystone facts.
5. **SY8089AAC — no datasheet obtainable. SUPERSEDED in revision 3.** Manufacturer's own
   site marked it NRND ("不推薦用於新設計"). 7+ URL attempts across JLC/lcsc.com/silergy.com
   all failed to surface a PDF. This was flagged as a genuine keystone gap in revisions 1–2
   and has since been resolved the correct way — by re-sourcing, not by further searching
   for an undiscoverable document. The sourcer replaced it with **AP62200TWU-7** (see
   Revision 3 section above); `SY8089AAC` is no longer part of this design.
   `datasheets/SY8089AAC_SUMMARY.md` and its generated symbol are left in place as
   historical record but should not be used by the coder.
6. **11 KiCad symbols generated** across revisions 1–3 (all verified `EXACT` via
   `find-symbol.py`): `AD9237BCPZ-40`, `AD9235BCPZ-40`, `TPS22919DCKR`, `SY8089AAC`
   (superseded, see #5), `BAV199LT1G`, `OXETDLJANF-10.000000`, `KH-BNC50-3511`,
   `W9825G6KH-6I`, `XC6SLX9-2TQG144C` (revision 1), `TPH2501-TR` (revision 2),
   **`AP62200TWU-7`** (revision 3, see Revision 3 section above) — all in
   `symbols/dual_adc_usb.kicad_sym`. AD9237/AD9235 include the exposed pad as pin 33
   (`EP`, passive). One part remains `⚠️ SYMBOL NEEDED`, deliberately not generated:
   `HX PZ1.27-2x3P TP` (generic 2x3 header — the coder uses a generic connector symbol per
   explicit instruction, not worth budget here).
7. **KH-BNC50-3511 mechanical dimensions captured** (page 1 of 1, full drawing) —
   center pad Ø0.90mm, 2x mounting/ground holes Ø2.00mm, 10.1mm×5.05mm spacing. Footprint
   `.kicad_mod` itself not built this pass (that's a phase-5 task using these dimensions).
8. **USB-C connector (J1) mechanical PDF obtained and reviewed** (6-page manufacturer
   doc, confirmed exact part match on the cover page, pin table cross-checked against
   `jlc_get_pinout` — identical). The pad-by-pad numeric diff against the generic
   `Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A` footprint was **not** performed
   (time prioritized on keystone facts) — carried forward.
9. **24LC64-I/SN pinout independently verified from its own PDF** (not assumed from
   convention): A0(1)/VCC(8), A1(2)/WP(7), A2(3)/SCL(6), VSS(4)/SDA(5).
10. Considered ECS-2033-100-BN as an alternate oscillator candidate for R2 — rejected,
    its datasheet (obtained, read) publishes no jitter spec at all.

## Artifacts

| File | Contains | Read it when |
|---|---|---|
| `datasheets/*_SUMMARY.md` (22 files) | Per-part specs, verified pinouts, load-bearing facts | Always — before writing any code for that part. **Ignore `SY8089AAC_SUMMARY.md`** — superseded, part no longer in design |
| `symbols/dual_adc_usb.kicad_sym` | 11 generated KiCad symbols (see Decisions #6) | Whenever SKiDL code instantiates one of those 11 parts — set `KICAD9_SYMBOL_DIR` to include `symbols/`. **Use `AP62200TWU-7`, not `SY8089AAC`, for U3/U4** |
| `datasheets/xc6slx9_kipart.csv` | Full 144-pin FPGA table (bank, name, type) backing the generated symbol | Building `fpga_core` block, or re-checking a specific pin |
| `datasheets/sdram_kipart.csv` | Full 54-pin SDRAM table backing the generated symbol | Building `buffer_memory` block |
| `datasheets/*.pdf` (15 files) | Primary-source datasheets, where obtained (13 from revision 1 + `TPH2501-TR.pdf` from revision 2 + `AP62200TWU-7.pdf` from revision 3, downloaded by the sourcer) | Whenever a summary's claim needs re-checking against the original |

## Summaries by block

| block_id | summary files |
|---|---|
| `usb_front` | `datasheets/TYPE-C-16PIN-2MD-073_SUMMARY.md`, `datasheets/USBLC6-2SC6_SUMMARY.md`, `datasheets/TPS22919DCKR_SUMMARY.md` |
| `power` | `datasheets/AP62200TWU-7_SUMMARY.md` (U3/U4 — supersedes `SY8089AAC_SUMMARY.md`, revision 3), `datasheets/TPS73633DBVR_SUMMARY.md`, `datasheets/TLV2372IDR_SUMMARY.md` |
| `analog_frontend` (CH1+CH2) | `datasheets/TPH2501-TR_SUMMARY.md`, `datasheets/THS4521IDR_SUMMARY.md`, `datasheets/BAV199LT1G_SUMMARY.md`, `datasheets/ESD9B5.0ST5G_SUMMARY.md`, `datasheets/KH-BNC50-3511_SUMMARY.md` |
| `adc_channel` (CH1+CH2) | `datasheets/AD9237BCPZ-40_SUMMARY.md`, `datasheets/AD9235BCPZ-40_SUMMARY.md` |
| `clocking` | `datasheets/OXETDLJANF-10.000000_SUMMARY.md` (supersedes SX3M — see Decisions #1), `datasheets/SN74LVC1G17DBVR_SUMMARY.md` |
| `fpga_core` | `datasheets/XC6SLX9-2TQG144C_SUMMARY.md`, `datasheets/W25Q32JVSSIQ_SUMMARY.md` |
| `buffer_memory` | `datasheets/W9825G6KH-6I_SUMMARY.md` |
| `usb_bridge` | `datasheets/CY7C68013A-56LTXC_SUMMARY.md`, `datasheets/24LC64-I-SN_SUMMARY.md`, `datasheets/DSX321G-24MHz_SUMMARY.md` |

## Next phase must

Addressed to **skidl-block-coder** / the driver splitting block work orders:

1. **Update X1's MPN** to `OXETDLJANF-10.000000` (LCSC C17609541) per Decision #1 — same
   footprint/pinout as the BOM's original SX3M part, just swap the symbol/value.
2. **AD9237 (U150/U250): strap MODE2 (pin 1) and OE (pin 3)** — MODE2 to one of
   AVDD/2:3·AVDD/1:3·AVDD/AGND (pick a level, simplest is AGND or AVDD direct tie per the
   datasheet's own test conditions), OE tied low (AGND) for continuous output enable.
   Route both through DNP-able resistors per Decision #2 if AD9235 second-sourcing is a
   live possibility for this build.
3. **XC6SLX9 (U30): tie all VCCAUX pins to +3V3D** (not a separate rail — Decision #3).
   Tie all VCCO_BANK0-3 pins to +3V3D unless a specific I/O standard needs otherwise. Tie
   VCCINT to +1V2.
4. **24LC64 (U51): strap A0=VCC(1), A1=GND(0), A2=GND(0)** for FX2LP "large EEPROM" boot
   at I2C address 0x51 — do NOT default all three to GND. Tie WP low to allow programming.
   **This is now a verified requirement (revision 2), confirmed from the CY7C68013A
   datasheet's own Table 8 and the 24LC64 datasheet's own control-byte format** — not an
   assumption. This directly resolves what R52–R55 are for (Decision #4) — reassign them
   from the 10kΩ placeholder to this specific function (3x address straps to VCC/GND as
   appropriate + 1x WP pull to GND; A2/A1/A0 need no resistor value beyond a solid DC tie,
   since they are static straps, not pull-ups on a signal — 0Ω links or direct copper ties
   are appropriate; only WP needs to function as an actual pull if a jumper/override is
   wanted).
5. **R150/R250 (adc_channel):** very likely one of AD9237's MODE2/OE straps (see #2) —
   confirm against the final schematic before accepting the 10kΩ placeholder.
6. **R30, R34–R39 (fpga_core):** likely Spartan-6 config-mode pins (M0/M1 boot-mode select,
   PROGRAM_B/INIT_B/DONE pull-ups, HSWAPEN strap) — **UG380 Configuration User Guide not
   obtained this pass**; the coder must source that document (or accept these as an open
   question flagged to the driver) before finalizing values — do not silently keep 10kΩ.
7. **TLV2372IDR (U7): tie the unused second op-amp channel as a unity-gain follower**
   (output to inverting input, non-inverting input to a valid reference) — required to
   avoid a floating unused half.
8. **TPH2501-TR symbol generated (revision 2)** — `Part('dual_adc_usb', 'TPH2501-TR')`
   with `symbols/` on `KICAD9_SYMBOL_DIR`; pins are `Out`(1, output), `-VS`(2, power_in),
   `+In`(3, input), `-In`(4, input), `+VS`(5, power_in) — pass these exact strings to
   SKiDL. No SHDN/enable pin exists on this part; do not add one. `HX PZ1.27-2x3P TP`
   remains ungenerated by explicit instruction — use a generic 2x3 connector symbol for it
   instead.
9. **AP62200TWU-7 (U3/U4, `power` block) — use this part, not SY8089AAC (revision 3).**
   `Part('dual_adc_usb', 'AP62200TWU-7')` with pins `GND`(1, power_in), `SW`(2, output),
   `VIN`(3, power_in), `FB`(4, input), `EN`(5, input), `BST`(6, passive) — pass these exact
   strings to SKiDL. Required per-instance wiring: (a) 100 nF cap BST→SW (330 nF for the
   +3V3D instance since VOUT>3V, 100 nF is fine for +1V2); (b) FB divider
   **+3V3D: R_top=33.2 kΩ/R_bot=10.0 kΩ**, **+1V2: R_top=5.76 kΩ/R_bot=10.0 kΩ** —
   `sourced_bom.md`'s existing R10–R13 values are stale SY8089A-era (VFB=0.6V) figures and
   **must be updated** to these before coding, not left as-is; (c) EN wiring per
   `handoffs/02_architecture.md` decision #12 — `+1V2` EN direct to VBUS_SW, `+3V3D` EN
   through the existing R18/C22 RC network (confirm topology against `net_plan.md`); do
   **not** leave either EN floating even though the part auto-enables when floating — the
   architecture's sequencing decision requires an active EN drive on both instances.

## Carried forward

- **SY8089AAC (U3/U4) — RESOLVED in revision 3 by re-sourcing, not further searching.**
  Replaced with AP62200TWU-7; see Revision 3 section and Decision #5. No longer a carried-
  forward gap.
- **R10–R13 in `sourced_bom.md` still hold stale SY8089A-era FB-divider values (assumed
  VFB=0.6V) — must be updated to AP62200TWU-7's values before coding the `power` block**:
  +3V3D → R_top=33.2 kΩ/R_bot=10.0 kΩ; +1V2 → R_top=5.76 kΩ/R_bot=10.0 kΩ (both verified
  against the datasheet's Eq. 8 this pass — see `AP62200TWU-7_SUMMARY.md`). This is a
  required fix, not optional, flagged in `Next phase must` #9.
- **AP62200TWU-7's +3V3D EN turn-on delay (R18/C22 RC, architecture's 2.74 ms figure) does
  not account for the part's internal 1.5 µA EN pull-up current**, which will make the real
  delay somewhat shorter. Not recomputed this pass (needs the RC topology confirmed against
  `net_plan.md` first) — flagged in `AP62200TWU-7_SUMMARY.md` Notes and Revision 3 §4 above.
- **AD9235's DNC-pin tolerance to a driven/strapped condition — unverified**, silent in
  both datasheets obtained. Mitigation designed in (Decision #2); underlying fact stays
  open.
- **XC6SLX9 per-pin table is EasyEDA-sourced**, cross-checked only in aggregate (matches
  DS160's 102-I/O total exactly) — individual pin *names* (which GCLK routes where) not
  independently checked against Xilinx's own UG385 pinout spec, which was not obtained.
  If a specific net's exact pin assignment matters (e.g. global clock input routing),
  re-verify before finalizing.
- **XC6SLX9 config-mode pins (M0/M1 boot select, PROGRAM_B/INIT_B/DONE pulls, HSWAPEN)
  — UG380 not obtained.** R30/R34-R39's exact function is a well-reasoned hypothesis, not
  confirmed (see Next phase must #6).
- **USB-C connector (J1) footprint — mechanical PDF obtained, pad-by-pad numeric diff
  against the assigned generic KiCad footprint not performed.** Pin function itself is
  fully verified and matches exactly; only mounting-hole placement risk remains open.
- **HX PZ1.27-2x3P TP — no symbol generated (intentional, revision 2 instruction).** Use a
  generic 2x3 connector symbol from the standard KiCad connector library instead; this is
  a low-priority generic header per sourcing's own note, not worth datasheet/symbol budget.
- **KH-BNC50-3511 `.kicad_mod` footprint file not built** — mechanical dimensions
  captured in the summary (page 1) for phase-5 to build from.

## Unverified keystone facts

| Part | Fact | Best available answer | What would close it |
|---|---|---|---|
| `AD9235BCPZ-40` | Whether DNC pins (1,3,5,6) tolerate an externally-applied static DC tie (as would occur if AD9237's MODE2/OE strap traces land on the same footprint) | Unknown — both AD9235 and AD9237 datasheets label these "Do Not Connect" with no elaboration on internal bonding or hazard. ADI's own "pin compatible" marketing claim is suggestive but not an explicit safety statement | A direct answer from Analog Devices (support ticket) confirming DNC-pin tolerance, or empirical verification on a built board. Mitigated in the design via DNP-able strap resistors (Decision #2) regardless. **Deliberately left open per explicit instruction** — carried into coding as a named assumption with the DNP-resistor mitigation; correct disposition for a second-source-only fact |

**Closed in revision 2:** `CY7C68013A-56LTXC` / `24LC64-I/SN` boot-EEPROM I2C address
(0x51/0xA2) and A2/A1/A0 strap (0/0/1) — previously listed here as community-sourced, now
**verified** directly from the CY7C68013A datasheet's own Table 8 and the 24LC64 datasheet's
own control-byte format (Figure 5-1). See Revision 2 section above.

**Closed in revision 3 (moot, not verified):** `SY8089AAC` feedback reference voltage and
EN polarity — the part these facts concerned is no longer in the design (replaced by
AP62200TWU-7; see Revision 3 section above). AP62200TWU-7's equivalent facts (VFB=0.763V,
EN active-high with internal auto-enable pull-up) **are verified** directly from its own
datasheet — see `AP62200TWU-7_SUMMARY.md` Load-bearing facts, not repeated here since they
were never in doubt for this part.

## Do not redo

- Every part's live JLC stock/tier/price figures — already confirmed in `sourced_bom.md`,
  not re-verified this pass (datasheets phase doesn't re-check stock).
- AD9237BCPZ-40 as primary ADC, AD9235BCPZ-40 as qualified 2nd source (pin-compatible,
  with the DNC caveat above) — architecture/sourcing decisions, not re-litigated.
- The 8-block/10-instance modular structure and all `[calc]` precision-passive values.
- TLV2372IDR substitution for the DC reference buffer, ferrite bead 0603→0805 package
  change, and every other sourcing decision not explicitly revised above.

## Receipt

**Revisions 1 + 2 + 3 combined:**

- 22 parts summarized (of ~23 covered/significant parts; `HX PZ1.27-2x3P TP` generic
  header intentionally left minimal per sourcing's own low-priority flag, no separate
  summary file written for it). TPH2501-TR's summary upgraded from MCP-only to
  PDF-verified in revision 2. `AP62200TWU-7_SUMMARY.md` written new in revision 3,
  superseding (not deleting) `SY8089AAC_SUMMARY.md`.
- 15 PDFs obtained and read (11 BOM parts + 1 evaluated-and-superseded oscillator +
  1 evaluated-and-rejected oscillator alternative + `TPH2501-TR.pdf` in revision 2 +
  `AP62200TWU-7.pdf` in revision 3, the latter downloaded by the sourcer); 6 parts
  summary-only (no PDF) — one fewer than revision 2 since SY8089AAC (the one PDF-less
  keystone part) is no longer in the design.
- Keystone parts: **8 of 8 with a verified primary-source PDF** as of revision 3 (AD9237,
  AD9235, XC6SLX9, CY7C68013A, oscillator/OXETDLJANF, TPS73633, THS4521, and now
  **AP62200TWU-7** in place of the PDF-less SY8089AAC). Every keystone part in the current
  BOM now has a primary-source PDF read in full.
- 11 KiCad symbols generated, all verified `EXACT` via `find-symbol.py`
  (`symbols/dual_adc_usb.kicad_sym`): 9 in revision 1 + `TPH2501-TR` in revision 2 +
  `AP62200TWU-7` in revision 3 (the stale `SY8089AAC` symbol remains in the library as
  historical record but should not be used). 1 part (`HX PZ1.27-2x3P TP`) intentionally
  left `⚠️ SYMBOL NEEDED` — coder uses a generic connector symbol.
- **1 unverified keystone fact remaining** (AD9235 DNC-pin tolerance — deliberately left
  open per explicit instruction, carried into coding as a named assumption with the
  DNP-resistor mitigation) — still forces `status: partial`. The CY7C68013A/24LC64
  boot-address fact was closed in revision 2; the two SY8089AAC facts are moot as of
  revision 3 (part replaced, not verified) — AP62200TWU-7's equivalent facts (VFB, EN
  polarity/auto-enable) **are verified** from its own datasheet and are not open questions.
- Cache: not used (`use_cache = false` per instruction, all revisions) — 0 hits, 0 writes.
- R2 (oscillator jitter) — **closed** with a verified substitution (revision 1). R3
  (AD9237 stock, from architecture) — untouched, already addressed by sourcing.
- Revision 2 call/URL budget: CY7C68013A/24LC64 closure used 0 new URL fetches (both PDFs
  already on disk from revision 1; closure was a re-read of existing primary sources).
  TPH2501-TR used 2 URL attempts (LCSC field URL retried and failed again as HTML; 3PEAK's
  own document-server URL, found via 1 web search, succeeded) — within the 2-URL/3-call
  ordinary-part budget.
- Revision 3 call/URL budget: 0 new URL fetches — `AP62200TWU-7.pdf` was already on disk,
  downloaded by the sourcer before this handoff was reopened. This pass's work was reading
  that PDF, writing the summary, and generating the symbol.
