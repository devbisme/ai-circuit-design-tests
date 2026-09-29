---
phase: 03_sourcing
agent: part-sourcer
circuit: dual_adc_usb
written: 2026-09-22T00:00:00Z
status: complete
revision: 7
next_phase: export
escalated_from: handoffs/06_erc.md
---

# Phase 3 handoff — Sourcing (revision 7 — final BOM reconciliation before netlist/BOM export)

**Scope of this revision: make `sourced_bom.md` right, not re-open engineering.** The
phase-6 ERC gate has PASSED (`erc_report.md` rev.2, 0 errors, 2 pre-classified-benign
warnings) and `circuits/dual_adc_usb/*.py` is final — **no file under `circuits/` was
touched this pass**. This was a document-only pass: close the gate's three named LOW/MEDIUM
BOM findings, then walk every row in `sourced_bom.md` against what the code actually
instantiates and fix whatever disagrees. Found and fixed 3 named items + 6 more the sweep
turned up on its own (one of them — C103/C203 silently losing its MPN identity as a
side-effect of the C101/C201 value change — would have shipped a wrong-value cap if missed).

## Decisions (this revision)

1. **C101/C201 220 pF → 200 pF, plus NEW rows C116/C216 (10 pF), per `erc_report.md`
   MEDIUM-1.** `analog_frontend.py` already builds the bottom leg's 210 pF fixed total as
   200 pF ‖ 10 pF (verified in code, not re-derived here) to compensate the ~9.4 pF of
   CHn_BUFIN clamp-node capacitance R102 does not isolate at the 8.8 kHz corner — without
   this, `tau_bot` runs 4.27 % long and the resulting gain shelf misses SPEC F12 (±2 %)
   across the whole plausible C_node range.
   - **C101/C201 → 0603CG201J500NT (Fenghua), LCSC C1649, 200 pF C0G 50 V, live stock
     43,493, Extended, ¥0.0127.** Sourced fresh, not derived from the old 220 pF part's
     listing. Note the voltage rating drops from the retired part's 100 V to 50 V — correct,
     not a regression: this node is CHn_ATT/VREF_OFF, downstream of the divider, not the
     ±50 V-rated BNC node C100/C_att_t sits on.
   - **Tolerance choice, as asked.** A ±2 % alternative exists (`CSA0603C0G201G500JT`, HRE,
     LCSC C54824737, 200 pF, 50 V, live stock 900, Extended, ¥0.0078 — cheaper *and*
     tighter than C1649). **Picked C1649 (±5 %) anyway.** Reasons: (a) this node's dominant
     error source is C_node's own uncertainty (±4–6 pF swings the shelf by ±1.6–1.7 % per
     `erc_report.md`), which a tighter MLCC tolerance does nothing to reduce — a ±5 %
     tolerance on 200 pF is ±10 pF, comparable to but not dominant over that; (b) SPEC F12 is
     explicitly SOFT and "before host-side calibration," so any residual gets calibrated out
     regardless of which part is here; (c) C1649 has a pullable manufacturer datasheet, 48×
     the live stock (43,493 vs. 900), and the same Extended tier/no assembly-fee difference.
     900 pcs still clears the >100-unit sourcing threshold by 45× for this 20-pcs-per-run
     need, so C54824737 is recorded as a documented, verified fallback, not a rejection on
     stock grounds.
   - **C116/C216 → CL10C100JB8NNNC (Samsung), LCSC C1634, 10 pF C0G 50 V, live stock
     1,467,159, Basic, ¥0.0076.** These are the intended trim point if C_node measures off
     nominal on the built boards (SPEC I2's "trimmable compensation cap").
   - **Both C101/C201 and C116/C216 marked `[calc]` — do not substitute by value.**
   - **C103/C203 caught by the sweep, not by inspection of this decision alone**: it was
     `[same MPN as C101]` in the BOM because both happened to be 220 pF GCM1885C2A221JA16D
     before this pass. C103/C203 is a *different* function (Sallen-Key-A feedback-to-GND
     cap, unrelated to the attenuator) and stays at 220 pF — only the stale "same MPN as
     C101" note was wrong; C103/C203 keeps GCM1885C2A221JA16D/C388907 as its own row. This
     is exactly the kind of silent-value-error the full sweep (item 4) exists to catch.

2. **Row 46 (D101/D201) `Device:D_TVS` → `Device:D_Zener`, per `erc_report.md` LOW-2.**
   `analog_frontend.py` deliberately uses `Device:D_Zener` (pin 1 = K/cathode, pin 2 =
   A/anode — a real symbol in the standard library) instead of `Device:D_TVS` (bidirectional
   glyph, pins A1/A2) because D101/D201's polarity is load-bearing (unidirectional TVS,
   cathode on signal) and `D_TVS`'s glyph misrepresents that to a schematic reviewer. Pin
   numbers are identical either way, so this was never a netlist error — only a stale BOM
   cell. Corrected, no other change to the row.

3. **Row 26 (J1) — two stale claims corrected, per `erc_report.md` LOW-3.** (a) Footprint
   column changed from "⚠️ CUSTOM FP NEEDED ... (to be generated)" to the resolved,
   in-use `ProjectLocal:USB_C_Receptacle_TYPE-C-16P-2MD073` — the file exists
   (`footprints/ProjectLocal.pretty/USB_C_Receptacle_TYPE-C-16P-2MD073.kicad_mod`) and
   `usb_front.py` instantiates it verbatim. (b) The note's mechanical reasoning corrected
   against `datasheets/TYPE-C-16PIN-2MD-073_SUMMARY.md`'s own retraction: the drawing's
   1.70/1.40 mm callouts are the *lengths of 0.60 mm-wide plated oval slots*, not round-hole
   diameters (only the two Ø0.65 mm locating holes are round, and those are NPTH); the real,
   verified reason the generic `Connector_USB:...HCTL...` footprint was rejected is a rear
   shield-slot interference (generic 0.6×1.2 mm vs. this part's required 0.6×1.4 mm), found
   by the completed pad-by-pad comparison, not the earlier "different offsets" guess.

4. **C30/C31's rev.5 "clocking.py not yet updated" warning was itself stale — removed, not
   carried forward again.** `clocking.py` already instantiates both at 100 nF/0402
   (`_c0402(ref='C30', value='100nF')` / `...ref='C31'...`), matching the BOM exactly.
   Verified by reading the code, not assumed.

5. **R19's rev.6 "populate-conditional / may stay DNP" note is obsolete — updated to
   "populated."** `power.py` instantiates `R19 = _r0402(ref='R19', value='22R')`
   unconditionally, and `erc_report.md` MEDIUM-6 independently confirmed the placement is
   correct (RNULL against a 300 nF load, TI SLOS270F §8.3.2/Fig. 34). This ref designator is
   populated on every board, full stop.

6. **Nine BOM cells said `⚠️ SYMBOL NEEDED` (or, for J4, effectively so) for symbols phase 4
   already generated and phase 5 already uses.** Updated to the actual `Lib:Symbol` each row
   resolves to, cross-checked against `symbols/dual_adc_usb.kicad_sym` (which symbol names
   are actually present) and the matching `Part(...)` call in code: U2 (TPS22919DCKR), U3/U4
   (AP62200TWU-7), U30 (XC6SLX9-2TQG144C), U40 (W9825G6KH-6I), J2/J3 (KH-BNC50-3511),
   D100/D200 (BAV199LT1G), U100–102/U200–202 (TPH2501-TR), U150/U250 (AD9237BCPZ-40) — all
   `dual_adc_usb:<MPN>`, confirmed present in the project symbol library and instantiated
   as such. J4 resolves to a **standard** KiCad symbol, `Connector_Generic:Conn_02x03_Odd_
   Even` — it was never actually a generation task, just an unresolved BOM flag.

7. **J2/J3's `⚠️ CUSTOM FP NEEDED` footprint already exists and is in use.** Same
   resolution pattern as #3/#6: `ProjectLocal:BNC_KH-BNC50-3511_Horizontal` is on disk
   (`footprints/ProjectLocal.pretty/BNC_KH-BNC50-3511_Horizontal.kicad_mod`) and
   `analog_frontend.py` uses it verbatim.

## Full BOM-vs-code sweep — what was checked, what was found

Walked all nine `circuits/dual_adc_usb/*.py` files against every row in `sourced_bom.md`
(ref by ref: every `Part(...)` call's `ref=`, `value=`, and `footprint=` argument, plus every
`dest=TEMPLATE` factory's footprint). Confirmed matching, beyond the 7 decisions above:
J1 pinout/power/GND mapping; U1 (USBLC6-2SC6) footprint+symbol; U3/U4 FB-divider resistors
R10–R13 (rev.4 values, unchanged); L1/L2 MPNs and footprints (`Inductor_SMD:L_Changjiang_
FNR4030S`/`FNR4020S`, exact); U5/U6 (TPS73633DBV) footprint+symbol; U7 (TLV2372) footprint+
symbol; U8 (SN74LVC1G17) footprint+symbol, pin map; Y1 (`Device:Crystal_GND24`, 4-pad,
confirmed correct — this was already fixed rev.5, re-verified not re-broken); C92/C93 (12 pF,
Y1 load caps); R52 (100 kΩ, FX2 reset RC, confirmed rev.5, re-verified not re-broken); U31
package/footprint (`SOIC-8_5.3x5.3mm_P1.27mm`, confirmed rev.6, re-verified not re-broken);
U50 (CY7C68013A) footprint, RESERVED-pin-to-GND, WAKEUP-pin-to-VDD; U51 (24LC64) footprint,
I2C address-strap logic (R53–R55, function now documented — see Decisions is folded into the
sweep, not a separate item); U40 (W9825G6KH-6I) footprint, pin-name traps (BS0/BS1, A10/AP);
R40 (22 Ω SDR clock termination); U30 (XC6SLX9) footprint, VCCINT/VCCAUX/VCCO mapping, all
config straps (R30/R34–R39 values), J4, D30/D31 LEDs; all `adc_channel` decoupling/reference
caps (C150–C161/C250–C261) and R150/R250 (function now documented). **Zero additional
value/package/footprint mismatches found beyond the 7 above.** The C103/C203 stale-MPN-note
catch (Decisions #1) is the one that would have mattered most if missed — it's a genuine
value ambiguity, not just a documentation gap, and the kind of thing this sweep exists for.

## Artifacts (this revision)

| File | Contains | Read it when |
|---|---|---|
| `sourcing/sourced_bom.md` | Rev.7 changes: C101/C201 value fix + NEW C116/C216 rows, D101/D201 symbol fix, J1 footprint/note fix, 6 more stale-note corrections from the sweep | Always — this is the BOM export reads from |
| `erc_report.md` | The passed gate (rev.2, 0 errors) this revision reconciles the BOM against | Before trusting any "as-built" claim in this handoff |
| `datasheets/TYPE-C-16PIN-2MD-073_SUMMARY.md` | The retraction this revision's J1 fix is built from (Notes section, "RESOLVED 2026-09-22") | If re-touching the J1 row ever again |

## Parts by block (rev.7 — updates `analog_frontend` only; all other blocks unchanged from rev.6)

| block_id | refs | MPNs |
|---|---|---|
| `usb_front` | J1, U1, U2, R1, R2, R3, C1, C2, C3 | TYPE-C 16PIN 2MD(073) (footprint confirmed generated+in-use, rev.7), USBLC6-2SC6, TPS22919DCKR (symbol confirmed resolved, rev.7), 0402WGF5101TCE(x2), 0402WGF1003TCE, CL21A106KAYNNNE, CL21A226MAQNNNE(x2) |
| `power` | U3, U4, U5, U6, U7, L1, L2, R10–R19, C10–C29, C32–C36, FB1–FB4 | AP62200TWU-7(x2, symbol confirmed resolved rev.7), TPS73633DBVR(x2), TLV2372IDR, FNR4030S3R3MT (L1), FNR4020S2R2MT (L2), assorted E96 1% resistors, 100nF/1µF/10µF/22µF caps, BST/feedforward caps, BLM21PG601SN1D(x4), **R19 = 0402WGF220JTCE, 22Ω, confirmed populated (rev.7, was "populate-conditional")** |
| `analog_frontend` (CH1) | J2, U100–U103, R100–R112, C100–C116, D100, D101 | KH-BNC50-3511 (symbol+footprint confirmed resolved, rev.7), TPH2501-TR(x3, symbol confirmed resolved, rev.7), THS4521IDR, WR08X9093FTL, 0603WAF9092T5E, **C101 = 0603CG201J500NT/C1649, 200pF (rev.7, was 220pF)**, **C116 = NEW, CL10C100JB8NNNC/C1634, 10pF (rev.7)**, C103 = GCM1885C2A221JA16D/C388907 220pF (own row again, rev.7 — see Decisions #1), BAV199LT1G, ESD9L5.0ST5G/C82326 (symbol = `Device:D_Zener`, rev.7 fix) |
| `analog_frontend` (CH2) | J3, U200–U203, R200–R212, C200–C216, D200, D201 | same MPNs as CH1 (**C201 = 200pF + NEW C216 = 10pF, D201 symbol = `Device:D_Zener`, all rev.7**) |
| `adc_channel` (CH1) | U150, R150, C150–C161 | AD9237BCPZ-40 (symbol confirmed resolved, rev.7), R150 = 10k MODE2+OE strap (function resolved, rev.7), 100nF/10µF decoupling |
| `adc_channel` (CH2) | U250, R250, C250–C261 | same pattern as CH1 |
| `clocking` | X1, U8, R21, R22, R23, C30, C31 | OXETDLJANF-10.000000, SN74LVC1G17DBVR, 0402WGF330JTCE(x2), jellybean 100Ω, CL05B104KB54PNC(x2) — **C30/C31 BOM-vs-code match confirmed, rev.7, rev.5's warning was stale** |
| `fpga_core` | U30, U31, J4, D30, D31, R30–R39, C40–C69 | XC6SLX9-2TQG144C (symbol confirmed resolved, rev.7), W25Q32JVSSIQ, HX PZ1.27-2x3P TP (symbol = standard `Connector_Generic:Conn_02x03_Odd_Even`, rev.7), LED green/red, R30/R34/R36/R37=4.7k, R35=330R, R38/R39=10k, 100nF/4.7µF caps |
| `buffer_memory` | U40, R40, C70–C78 | W9825G6KH-6I (symbol confirmed resolved, rev.7), 0402WGF220JTCE, 100nF(x8)/10µF(x1) |
| `usb_bridge` | U50, U51, Y1, R50–R55, C80–C93 | CY7C68013A-56LTXC, 24LC64-I/SN, DSX321G 24MHz, `Device:Crystal_GND24`, R53–R55 = I2C address straps (function resolved, rev.7), resistor/cap mix per `sourced_bom.md` |

## Next phase must

Addressed to **whoever runs export (phase 8, main thread)**:

1. **No datasheet or coding work is needed before export.** Every part this revision
   touched (C101/C201's new MPN, C116/C216) is a jellybean C0G MLCC using the generic
   `Device:C` symbol and a standard `Capacitor_SMD:C_0603_1608Metric` footprint — nothing
   here meets the "needs a datasheet" bar (ICs, FETs, magnetics, crystals, or a part whose
   pinout/application circuit a coder needs). `next_phase: export` reflects this — do not
   route back through `datasheet-librarian` or a coder on this handoff's account.
2. **Export straight from `sourcing/sourced_bom.md` and the gate-passed `circuits/`
   tree.** The ERC gate (`erc_report.md` rev.2) already verified the as-built circuit,
   including the C101/C201+C116/C216 change (code timestamp postdates the gate report by 5
   minutes; the change matches exactly what the gate's own MEDIUM-1 finding recommended, and
   is a passive-value-only change with no topology or connectivity impact — re-running full
   ERC over a 0603 cap value edit was judged unnecessary, but re-run it first if that
   judgment is worth a second opinion before committing to fab).
3. **BOM part count is 243** — verify the exported BOM's line-item/placement count
   reconciles to that (see Receipt).

## Carried forward (current, supersedes revision 6's list — most of rev.6's list is now
resolved, not carried; only genuinely open items remain below)

- **D101/D201's substitution constraint is still binding**: Cj ≤ 2 pF, Ir ≤ 1 µA @ 5 V/85 °C,
  unidirectional, SOD-923. Do not re-source this pair on stock or price alone. Second source
  verified: C7379964 (MSKSEMI, 0.5 pF, same footprint/polarity, 18,153 in stock).
- **C101/C201's tighter-tolerance alternative is a documented, verified fallback, not a
  rejection**: `CSA0603C0G201G500JT`/C54824737, ±2 %, 900 in stock (still 45× this run's
  need). If a future higher-volume run wants ±2 % τ-matching margin, this is pre-vetted.
- **BAV199LT1G pin-3 identity is EasyEDA-sourced, not independently manufacturer-verified**
  (`analog_frontend.py`'s own comment flags this) — unchanged from earlier revisions, not
  re-derived this pass. Low risk (rev.5 already cross-checked pin 1/2 against the primary
  onsemi datasheet; only pin 3's *label* in the EasyEDA-derived symbol is unverified, not the
  physical pinout, which matches the code's wiring either way).
- **X1 (OXETDLJANF-10.000000) — 50 pcs, single LCSC listing.** Accepted single-source risk,
  unchanged. Re-verify or qualify a 2nd source before any run larger than this one.
- **AP62200T's VIN margin against USB VBUS droop is 0.2 V.** Unchanged, recorded not fixed —
  no action needed unless VBUS droop assumptions change.
- **FB1–FB4 are 0805, not the spec-nominal 0603** (no 600 Ω/0603 combo in stock at sourcing
  time) — unchanged, re-check stock if this BOM is ever re-run for a future build.

## Do not redo

- **Everything in revision 6/5/4/3/2's "Do not redo" lists that this revision did not touch**
  — AP62200TWU-7 selection, X1 selection, R52/R30–R39 values, C100/C200 spec (22 pF/0603/
  100 V — untouched, this is the *top*-leg cap on the ±50 V BNC node, not C101/C201), Y1
  symbol, L2 MPN, BAV199LT1G orientation, D101/D201 = ESD9L5.0ST5G/C82326, U31 package/
  footprint, J1 = project-local footprint (now also confirmed generated+in-use, not just
  named).
- **C101/C201 = 0603CG201J500NT/C1649, 200 pF, and C116/C216 = CL10C100JB8NNNC/C1634, 10 pF
  — both `[calc]`.** Do not revert to a single 220 pF part; do not substitute either by value
  without re-deriving the τ-match arithmetic in `erc_report.md` MEDIUM-1 first.
- **Row 46's symbol is `Device:D_Zener`, not `Device:D_TVS`.** Do not "fix" it back —
  `D_TVS`'s bidirectional glyph is the wrong one for a unidirectional, polarity-load-bearing
  part.
- **C103/C203 = GCM1885C2A221JA16D/C388907, 220 pF — independent of C101/C201's value.**
  Do not collapse these back into "same MPN as C101" bookkeeping; they diverged this
  revision and must be tracked separately from here on.
- **The nine symbol-resolution and two footprint-resolution corrections in Decisions #6/#7
  are confirmed against both the symbol library file and the instantiating code** — not
  re-flag these as `⚠️ SYMBOL NEEDED`/`⚠️ CUSTOM FP NEEDED` without first checking whether
  the referenced file has actually regressed.

## Receipt

- **Revision 7 (this pass):** 3 gate-named BOM findings closed (C101/C201 value +
  NEW C116/C216 rows; D101/D201 symbol; J1 footprint/note) + 6 more found and fixed by the
  full sweep (C103/C203's silently-diverged MPN note — the one that mattered most; C30/C31's
  and R19's stale carried-forward warnings; 9 cells' worth of stale `⚠️ SYMBOL NEEDED` across
  8 rows; J2/J3's stale `⚠️ CUSTOM FP NEEDED`; R53–R55/R150/R250 function notes).
- 0 new sourcing failures; `sourcing/sourcing_failures.md` not written.
- Tier impact: **none.** C101/C201 stays Extended (Fenghua 200 pF, same tier as the retired
  220 pF part); C116/C216 is **Basic** (Samsung, adds 0 assembly-fee exposure, actually
  improves the BOM's Basic/Extended mix slightly). 2 new placements, 0 new Extended-tier
  exposure.
- **243 total placements**, verified against the gate-passed circuit (241 at the phase-6
  gate + C116/C216, +2) — every ref designator in `circuits/dual_adc_usb/*.py` accounted
  for in exactly one `sourced_bom.md` row.
- **Live-verified this pass:** C1649 (43,493 stock), C54824737 (900 stock, alternate), C1634
  (1,467,159 stock) — all three via `jlc_get_part`, not carried from a prior snapshot.
- Footprints: all 63 `footprint=` strings in `circuits/dual_adc_usb/*.py` re-validated with
  `validate-footprints.py` — **0 unresolved**, matching the gate's own 25/25 (this run
  checks all placements, not just the previously-flagged custom ones).
- Status: **complete.** No open sourcing failures, no unresolved symbol/footprint flags, no
  known BOM-vs-code disagreements remain. Next: **export** (phase 8, main thread) — no
  datasheet or coding phase needed on this handoff's account, see Next phase must.

---

# Revision 6 (preserved below, unchanged)

# Phase 3 handoff — Sourcing (revision 6 — ERC-escalation fix: D101/D201, U31, J1, R19 + audit)

**Scope of this revision: the 4 sourcing items the ERC escalation named, plus a targeted
audit the coordinator added.** `handoffs/02_architecture.md` rev.2 (D-r2.2) already decided
*which* part replaces the input TVS and *why*; this phase's job was to verify that part is
real (live stock, correct spec, correct polarity) and record it so the 30x-wrong capacitance
error the old row carried can't recur. Also fixed U31's package cell (the coder is fixing the
footprint independently; the BOM now agrees instead of contradicting it), made a binding call
on J1's land pattern instead of re-flagging it a sixth time, sourced a conditional 22 Ω line
for R19, and audited D100/D200/C100–C101/R100–R102 against live datasheet data. **No file
under `circuits/` was touched this pass** — a block coder is working there concurrently.

## Decisions (this revision)

1. **D101/D201 — re-sourced: ESD9B5.0ST5G → ESD9L5.0ST5G (onsemi), per architecture D-r2.2.
   Live-verified, not carried on trust.**
   - **LCSC C82326, onsemi, SOD-923, 92,164 in stock (live), ¥0.0552 (¥0.0429 @100+),
     Extended tier.** Datasheet-confirmed specs pulled live via `jlc_get_part`:
     **Cj = 0.9 pF max** (not the old row's "≤0.5 pF," which was wrong by 30x for the
     ESD9B part and is the reason the clamp-placement defect survived four phases),
     **Vrwm 5 V, Vbr 5.4 V min, clamping 9.8 V, Ir ≤1 µA @ Vrwm, IEC 61000-4-2,
     unidirectional.**
   - **Second source verified live and drop-in on the same land pattern: C7379964**
     (MSKSEMI, same `ESD9L5.0ST5G` part number, SOD-923, **0.5 pF**, Vrwm 5 V, Vbr 7.8 V,
     unidirectional, 18,153 in stock, ¥0.0334) — both parts clear the ≤2 pF /
     ≤1 µA-leakage / unidirectional / SOD-923 constraint below.
   - **Polarity recorded correctly this time.** The old ESD9B5.0ST5G was bidirectional and
     orientation-free; ESD9L5.0ST5G is **unidirectional** — cathode (pin 1) → `CHn_BUFIN`,
     anode (pin 2) → GND, per architecture. Reversing it forward-biases the diode straight
     to ground. This is now stated in the BOM row itself, not left implicit.
   - **Symbol: no generation needed.** `find-symbol.py ESD9L5.0ST5G` reports `MISSING` by
     MPN, but architecture already specifies the fix: `Device:D_TVS` (generic 2-pin passive
     TVS symbol) with `value='ESD9L5.0ST5G'`. Confirmed `D_TVS` exists in the standard
     `Device.kicad_sym`. This does not re-open phase 4 for this part.
   - **Footprint validated to resolve:** `Diode_SMD:D_SOD-923` — confirmed present in
     `Diode_SMD.pretty` (`D_SOD-923.kicad_mod`). This also closes ERC finding HIGH-4 for
     the new part (the old row's `D_SOD-523` was wrong for either part).
   - **Binding substitution constraint recorded in the BOM row, not just here:** per
     architecture D-r2.2/D-r2.3, **a substitute with Cj > 2 pF or worse than 1 µA leakage
     at 5 V/85 °C is not safe on this node** — it's a HARD-requirement (F8) node, and the
     part sits on an 82.6 kΩ Thevenin source where 1 µA of leakage alone is already 4.5 %
     of full scale (risk R12). Revision 1's "ESD parts are freely substitutable" note is
     explicitly overturned for this ref pair; anyone re-sourcing D101/D201 on stock or
     price alone without checking this constraint is repeating the exact class of error
     that caused the escalation.
   - LCSC number and live stock are now both present — closes the SPEC R3 breach
     (`sourced_bom.md`'s old row had neither).

2. **U31 — package/footprint cell corrected, not just flagged.** Live `jlc_get_part` on
   `W25Q32JVSSIQ`/C179173 confirms `SOIC-8-208mil` (5.3×5.3 mm body). The BOM's Package
   column said plain "SOIC-8" and its footprint column carried
   `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` — the 150-mil narrow-body pattern every *other*
   SOIC-8 in this design correctly uses (U51, U103/U203, U7), but wrong for this part.
   Corrected to `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm`, validated against
   `Package_SO.pretty` (resolves). This is the BOM half of ERC finding HIGH-3; the block
   coder is independently fixing `fpga_core.py`'s footprint string — the BOM now agrees
   with the code instead of being the thing that would mislead the *next* person to touch
   this file.

3. **J1 — resolved to a project-local footprint, not re-flagged as "unverified" a sixth
   time.** Every sourcing revision since rev.2 has carried
   `Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A` forward as "pad count matches,
   mounting holes unconfirmed." This pass actually did the dimension check against
   SHOU HAN's own drawing (`datasheets/TYPE-C-16PIN-2MD-073.pdf` p.6, already on disk from
   phase 4): overall envelope matches well (8.94 mm width in both), but the
   generic footprint is a **different manufacturer's part** ("HCTL," 5 A VBUS rating vs.
   SHOU HAN's 3 A) and its shield/mounting attachment geometry does not match — SHOU HAN
   specifies **round** holes, Ø1.70 mm (2x) + Ø1.80 mm (2x) + Ø0.65 mm (2x) NPTH; the
   generic footprint's shield tabs are **oval slots** (0.6×2.1 mm and 0.6×1.6 mm) at
   different offsets. Pin function/pitch is not the risk (already confirmed exact against
   `jlc_get_pinout` in rev.2) — the mechanical mounting feature is a genuine mismatch, not
   a confirmed-equivalent.
   **Decision: specify a project-local `.kicad_mod`** (`ProjectLocal:USB_C_Receptacle_
   TYPE-C-16P-2MD073`), generated from page 6's dimensioned drawing, the same resolution
   already used for J2/J3 (`ProjectLocal:BNC_KH-BNC50-3511_Horizontal`). Given this design
   has now had two footprint defects reach ERC on exactly the "pad-count-matches-but-
   package-differs" pattern (D101/D201, U31), continuing to carry an unconfirmed generic
   footprint from a different manufacturer forward a sixth revision is not defensible — a
   definitive fix is worth more than another "flagged for phase 4" note. Generation is
   datasheet-librarian/coder work (`generate-footprint.py`), not sourcing's; marked
   `⚠️ CUSTOM FP NEEDED` in the BOM with the exact dimensions needed.

4. **R19 — sourced as populate-conditional, not resolved to a fixed function.** Per the
   coordinator: R19 may become a 22 Ω isolation resistor on U7A's (TLV2372) output if the
   `power` block coder concludes one is needed for reference-buffer stability against the
   300 nF capacitive load ERC flagged as MEDIUM-6 (not simulated, not asserted as a proven
   defect — see `handoffs/06_erc.md` Decision 6) — or it may legitimately stay spare.
   Sourced **22 Ω 1% 0402, `0402WGF220JTCE`, LCSC C25092, 3,963,115 in stock (live),
   **Basic** tier, ¥0.0029** — same MPN already used for R40 (SDRAM clock termination), so
   no new line item enters the design. Row exists in the BOM either way so the ref
   designator isn't orphaned regardless of which way the coder decides; marked
   populate-conditional rather than committed, per the coordinator's framing.

## Audit (this revision, coordinator-requested — item 5): re-check capacitance, voltage
rating and package on the other analog-input-node parts against live datasheet data

**Scope: D100/D200 (BAV199LT1G), C100/C200, C101/C201, R100–R102/R200–R202.** None of these
are `[calc]` values (per the instruction, those are not re-derived) — this checks the BOM
*cells* against the manufacturer's own published specs, the same class of check that would
have caught the ESD9B5.0ST5G capacitance error if it had been done at the time.

- **C100/C200 (`GCM1885C2A220JA16D`, C408549):** live `jlc_get_part` confirms **22 pF, C0G,
  100 V, 0603** — exact match to the BOM row (this is the rev.5 fix; re-confirmed, not
  re-opened). **No mismatch.**
- **C101/C201 (`GCM1885C2A221JA16D`, C388907):** live-confirmed **220 pF, C0G, 100 V,
  0603** — exact match to the BOM row's "220 pF C0G ... 100 V rating" note. **No mismatch.**
- **R100/R200 (`WR08X9093FTL`, C170980):** live-confirmed **909 kΩ, ±1%, 0805, 150 V max
  working voltage** — matches the BOM's stated value and the architecture's own stated
  reason for keeping it 0805 ("150 V working voltage," `handoffs/02_architecture.md`
  Do not redo). **No mismatch** (voltage rating isn't itemized as its own BOM cell, but
  nothing in the row contradicts it).
- **R101/R201 (`0603WAF9092T5E`, C23129):** live-confirmed **90.9 kΩ, ±1%, 0603, 75 V**.
  Matches. **No mismatch.**
- **R102/R202 (`0603WAF1001T5E`, C21190):** live-confirmed **1.00 kΩ, ±1%, 0603, Basic
  tier, 75 V**. Matches the BOM's value and tier. **No mismatch.**
- **D100/D200 (`BAV199LT1G`, C145516) — one real finding, does not change the HARD-
  requirement verdict.** Fetched the primary onsemi datasheet directly
  (`BAV199LT1/D`, Rev. 13) since the local `_SUMMARY.md` only had MCP data. Two things:
  1. **Pinout/topology (out-of-band item from rev.5) re-confirmed against the actual
     datasheet page, not just cited from it:** Case 318 SOT-23 Style 11 —
     pin 1 = Anode, pin 2 = Cathode, pin 3 = Cathode/Anode (series midpoint). Matches
     rev.5's verification exactly and matches `analog_frontend.py`'s wiring. No change.
  2. **New finding: architecture D-r2.2's "~1.5 pF/junction, ~3 pF total" estimate for
     BAV199's contribution to `C_node` is optimistic against the datasheet's own numbers,
     though the conclusion it feeds still holds.** The datasheet specifies **per-diode**
     capacitance as `CD ≤ 2.0 pF max` (`VR = 0 V, f = 1 MHz`, "EACH DIODE" — table
     heading, page 2) — not ~1.5 pF. More importantly, D-r2.2's arithmetic treats the two
     junctions as contributing in series (matching Figure 3's "Total Capacitance" curve,
     which is measured pin-1-to-pin-2 and drops from ~1.2 pF at 0 V to ~0.5 pF at higher
     reverse bias) — but that is the wrong topology for this circuit. **From the signal
     node's viewpoint (pin 3, the series midpoint), the two junction capacitances are in
     *parallel*** (each junction's C appears from node 3 to a different AC-grounded rail —
     GND via D_low, AVDD via D_high through its own decoupling), not in series. Worst case
     at low reverse bias (`BUFIN` only swings 0.734–2.552 V, so each junction sees only a
     volt or two of reverse bias — close to the steep, high-capacitance part of the
     datasheet's own Figure 3 curve): up to **2 × 2.0 pF = 4.0 pF**, not the ~3 pF assumed.
     **Recomputed impact:** this raises `C_node` from D-r2.2's 8.4 pF to **~9.4 pF**
     (0.9 pF TVS + ~4.0 pF BAV199 worst-case + ~3 pF TPH2501 + ~1.5 pF trace). Architecture
     already checked a 12 pF sensitivity case and found the rev.2 part still lands at
     4.33 MHz (`handoffs/02_architecture.md`, Carried forward) — 9.4 pF is comfortably
     inside that, so **F8/F9 margins are unaffected and no HARD requirement is at risk.**
     This is a correction to an assumption's arithmetic, not a defect — flagged for the
     architecture's risk log (R11/R13 already track this node's capacitance budget) rather
     than acted on here, since it doesn't change any sourced part or BOM value. **Package
     and voltage rating (SOT-23, Vr 70 V, matches the BOM row) — no mismatch.**

**Net result of the audit: 1 finding (BAV199 capacitance-topology arithmetic, informational,
margin-neutral), 0 BOM cell errors.** The ESD9B5.0ST5G-class mistake — a wrong spec cell
that nothing downstream re-derives — was not repeated on any of these five rows.

## Out-of-band verification carried from revision 5 (unchanged, re-confirmed this pass)

- BAV199LT1G pin orientation — re-confirmed directly against the primary onsemi datasheet
  (fetched this pass, not just cited): pin 1 = Anode, pin 2 = Cathode, pin 3 = Cathode/Anode
  midpoint. Matches `analog_frontend.py`'s wiring exactly. No change.

## Artifacts (this revision)

| File | Contains | Read it when |
|---|---|---|
| `sourcing/sourced_bom.md` | Rev.6 changes: D101/D201 (full re-source), U31 (package/footprint cell fix), J1 (footprint resolved to project-local, not re-flagged), R19 (sourced, populate-conditional) | Always — before writing or reviewing any code |
| `datasheets/TYPE-C-16PIN-2MD-073.pdf` p.6 | SHOU HAN's own mechanical drawing — dimensions needed to generate J1's project-local footprint | Datasheet-librarian, next |

## Parts by block (rev.6 — updates `analog_frontend`, `fpga_core`, `usb_front`, `power` refs only)

| block_id | refs | MPNs |
|---|---|---|
| `usb_front` | J1, U1, U2, R1, R2, R3, C1, C2, C3 | TYPE-C 16PIN 2MD(073) (**J1 footprint resolved rev.6 — project-local `.kicad_mod` to be generated, see Decisions #3**), USBLC6-2SC6, TPS22919DCKR, 0402WGF5101TCE(x2), 0402WGF1003TCE, CL21A106KAYNNNE, CL21A226MAQNNNE(x2) |
| `power` | U3, U4, U5, U6, U7, L1, L2, R10–R19, C10–C29, C32–C34, C35, C36, FB1–FB4 | AP62200TWU-7(x2), TPS73633DBVR(x2), TLV2372IDR, FNR4030S3R3MT (L1), FNR4020S2R2MT (L2), assorted E96 1% resistors, 100nF/1µF/10µF/22µF caps, BST/feedforward caps, BLM21PG601SN1D(x4), **R19 = 0402WGF220JTCE, 22Ω, populate-conditional (new rev.6, see Decisions #4)** |
| `analog_frontend` (CH1) | J2, U100–U103, R100–R112, C100–C115, D100, D101 | KH-BNC50-3511, TPH2501-TR(x3), THS4521IDR, WR08X9093FTL, 0603WAF9092T5E, precision network (all audited rev.6, no mismatch — see Audit), BAV199LT1G (pinout re-confirmed rev.6), **D101 = ESD9L5.0ST5G/C82326, re-sourced rev.6, see Decisions #1** |
| `analog_frontend` (CH2) | J3, U200–U203, R200–R212, C200–C215, D200, D201 | same MPNs as CH1 (**D201 = ESD9L5.0ST5G, rev.6**) |
| `adc_channel` (CH1) | U150, R150, C150–C161 | AD9237BCPZ-40, placeholder 10k (R150 unresolved), 100nF/10µF decoupling |
| `adc_channel` (CH2) | U250, R250, C250–C261 | AD9237BCPZ-40, placeholder 10k (R250 unresolved), 100nF/10µF decoupling |
| `clocking` | X1, U8, R21, R22, R23, C30, C31 | OXETDLJANF-10.000000, SN74LVC1G17DBVR, 0402WGF330JTCE(x2), jellybean 100Ω, CL05B104KB54PNC(x2) |
| `fpga_core` | U30, U31, J4, D30, D31, R30–R39, C40–C69 | XC6SLX9-2TQG144C, **W25Q32JVSSIQ (package/footprint corrected rev.6, see Decisions #2)**, HX PZ1.27-2x3P TP, LED green/red, R30/R34/R36/R37=4.7k, R35=330R, R38/R39=10k, 100nF/4.7µF caps |
| `buffer_memory` | U40, R40, C70–C78 | W9825G6KH-6I, 0402WGF220JTCE, 100nF(x8)/10µF(x1) |
| `usb_bridge` | U50, U51, Y1, R50–R55, C80–C93 | CY7C68013A-56LTXC, 24LC64-I/SN, DSX321G 24MHz, `Device:Crystal_GND24`, resistor/cap mix per `sourced_bom.md` |

## Next phase must

Addressed to **datasheet-librarian**:

1. **Generate `ProjectLocal:USB_C_Receptacle_TYPE-C-16P-2MD073`** for J1, from
   `datasheets/TYPE-C-16PIN-2MD-073.pdf` p.6 (already on disk). Key dimensions: 0.50 mm
   signal-pad pitch, 16-pad standard USB-C pinout (already pin-verified, no pinout risk),
   shield pads 5.68×5.35 mm and 4.18 mm, mounting holes Ø1.70 mm (2x) + Ø1.80 mm (2x) +
   Ø0.65 mm (2x) NPTH. Same tooling/precedent as J2/J3's
   `ProjectLocal:BNC_KH-BNC50-3511_Horizontal` (`generate-footprint.py`).
2. **Generate a KiCad symbol for AP62200TWU-7** (U3/U4) — still the only open AP62200T
   item, unchanged from rev.4/5. Pin table: GND(1)/SW(2)/VIN(3)/FB(4)/EN(5)/BST(6), from
   `datasheets/AP62200TWU-7.pdf` p.3.
3. **D101/D201 need no symbol-generation work** — `Device:D_TVS` (generic, already in the
   standard library) covers it. Do not spend phase-4 budget here.
4. Every other item from revision 2–5's "Next phase must" lists (AD9235 DNC pins, XC6SLX9
   VCCAUX, FX2/24LC64 boot address, remaining ⚠️ SYMBOL NEEDED rows, C30/C31 and C35/C36
   BOM-vs-code gaps for whoever next has `circuits/` write access) still stands unchanged
   — not re-litigated this pass.

## Carried forward (current, supersedes revision 5's list where noted)

- **J1's footprint is now a committed target, not an open question** — but the
  `.kicad_mod` file itself does not exist yet. `ProjectLocal:USB_C_Receptacle_
  TYPE-C-16P-2MD073` needs generating before this part can go to layout. Until then,
  `usb_front.py`'s existing footprint string (the generic HCTL one) is known-wrong on
  mechanicals, not just unconfirmed — treat it as blocking for fab, not merely a note.
- **BAV199's capacitance-topology arithmetic (this revision's audit finding)** — informs
  `C_node`'s true worst case (~9.4 pF vs. D-r2.2's 8.4 pF assumption); margin-neutral
  (still well inside the 12 pF case architecture already checked) but worth folding into
  `design_risks.md` R11/R13 next time that file is touched, so the number in the risk log
  matches the number a primary datasheet actually supports.
- **D101/D201's substitution constraint is now binding and stated in the BOM row itself**
  (Cj ≤ 2 pF, Ir ≤ 1 µA @ 5 V/85 °C, unidirectional, SOD-923) — do not re-source this pair
  on a stock or price argument alone without re-checking against
  `handoffs/02_architecture.md` D-r2.2/D-r2.3 first.
- **AP62200TWU-7 (U3/U4) — ⚠️ SYMBOL NEEDED**, unchanged, still the only open AP62200T
  item.
- **AP62200T's VIN margin against USB VBUS droop is 0.2V** — unchanged, recorded not
  fixed.
- **X1 (OXETDLJANF-10.000000) — 50 pcs, single LCSC listing.** Accepted single-source
  risk, unchanged.
- **BOM/code mismatch, still open from revision 5: C30/C31** (BOM says 100 nF 0402, code
  still instantiates 1 µF 0603 in `clocking.py`) and **C35/C36** (in BOM, not yet in
  `power.py`) — both untouched this pass, `circuits/` was off-limits; whoever next edits
  those files should pick these up.
- Every item in revision 4/3/2's "Carried forward" sections not explicitly superseded
  above (AD9235 DNC-pin tolerance, CY7C68013A+24LC64 boot address, XC6SLX9 pin
  table/config-mode pins, TPH2501-TR/HX header symbols, KH-BNC50-3511 `.kicad_mod`,
  R53–R55/R150/R250 unresolved placeholders) is unchanged and still open.

## Do not redo

- Everything in revision 4/3/2/5's "Do not redo" lists — unchanged and not reopened this
  pass (AP62200TWU-7 selection, X1 selection, R52/R30–R39 values, C100/C200 spec, Y1
  symbol, L2 MPN, BAV199LT1G orientation).
- **D101/D201 = ESD9L5.0ST5G (C82326), SOD-923, unidirectional, cathode→`CHn_BUFIN`,
  anode→GND** — matches `handoffs/02_architecture.md` D-r2.2 exactly. Do not revert to
  ESD9B5.0ST5G or any bidirectional part; do not substitute on stock/price without
  re-checking the Cj ≤ 2 pF / Ir ≤ 1 µA constraint first.
- **U31 = `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm`** — matches live JLC package data and the
  block coder's independent footprint fix. Do not revert to the 150-mil pattern.
- **J1 = project-local `.kicad_mod`, not the generic HCTL footprint** — the generic part is
  now a documented mechanical mismatch (different manufacturer, round-hole vs. oval-slot
  shield attachment), not merely unconfirmed. Do not re-adopt it as a "good enough"
  placeholder.
- **BAV199's capacitance audit finding is informational only** — it does not change any
  sourced part, BOM value, or HARD-requirement verdict. Do not treat it as a defect to fix.

## Receipt

- **Revision 6 (this pass):** 4 BOM rows resolved per the ERC escalation (D101/D201 fully
  re-sourced; U31 package/footprint cell corrected; J1 footprint resolved to a named
  project-local target instead of re-flagged; R19 sourced as populate-conditional) + 1
  five-row audit (D100/D200, C100/C200, C101/C201, R100–R102/R200–R202) against live
  datasheet data, finding 1 informational, margin-neutral arithmetic correction and 0 BOM
  cell errors.
- 0 new sourcing failures; `sourcing/sourcing_failures.md` not written.
- Tier impact: D101/D201 stays Extended (was already Extended); R19's new line is Basic
  (reuses R40's MPN) — no new assembly-fee exposure.
- **SPEC R3 breach closed:** D101/D201 now carries a real LCSC number (C82326) and
  live-verified stock (92,164) — the old row had neither.
- **1 binding substitution constraint newly recorded in the BOM itself** (D101/D201: Cj ≤
  2 pF, Ir ≤ 1 µA @ 5 V/85 °C, unidirectional) — supersedes rev.1's "ESD parts are freely
  substitutable" for this ref pair specifically.
- **1 footprint resolved from "carried forward, unconfirmed" (5 revisions) to a named,
  justified target** (J1) — not yet generated; that's phase 4's job, flagged in Next phase
  must.
- Status: **partial** — same structurally open items as rev.5 (AP62200TWU-7 symbol
  generation, several unresolved placeholder resistors, C30/C31 and C35/C36 BOM-vs-code
  gaps) plus one new generation task (J1's project-local footprint). Next:
  `datasheet-librarian` → `handoffs/04_datasheets.md`, then re-gate with `erc-reviewer`
  once the block coder currently in `circuits/` finishes the `analog_frontend` /
  `fpga_core` changes this revision's BOM now matches.

---

# Revision 5 (preserved below, unchanged)

# Phase 3 handoff — Sourcing (revision 5 — BOM-maintenance sync with block-coder-resolved values)

**Scope of this revision: narrow BOM-maintenance pass.** The block coders resolved several
placeholder values directly from primary datasheets while writing `circuits/` code (R52,
R30/R34-R39, Y1's symbol); this revision brings the corresponding `sourced_bom.md` rows up
to date, plus re-sources three rows the coordinator flagged independently (C100/C200,
C30/C31, L2) and adds two new dedicated VIN bulk caps for U3/U4. **No file under `circuits/`
was touched this pass** — a review agent was working there concurrently, and this revision's
brief was explicit about staying out of it. One row (C30/C31) now states a BOM value the
code does not yet match; that gap is documented, not silently left for someone to discover
at ERC time. All work below is scoped to exactly the 8 items the coordinator listed, plus
one out-of-band verification (BAV199LT1G pin function) that was requested as report-only.

## Decisions (this revision)

1. **R52 — 10 kΩ → 100 kΩ, `0402WGF1002TCE`/C25744 → `0402WGF1003TCE`/C25741.** Confirmed
   live: 9,667,613 in stock, Basic tier, ¥0.0025 — same MPN already used for R3 and R18
   elsewhere in this BOM, so no new part enters the design. R52 is the FX2LP `~RESET` RC
   resistor (with C89, 100 nF), not a write-protect pull as the old placeholder note implied.
   CY7C68013A datasheet 38-08032 Rev. AD p.8 Table 5 requires ~5 ms after VCC reaches 3.0 V
   for crystal+PLL stabilization before releasing reset; 10 kΩ/100 nF only gives 0.93 ms to
   VIH, 100 kΩ gives 9.3 ms — inside spec with margin. `usb_bridge.py` already implements
   100 kΩ; only the BOM row was stale.
2. **R30/R34/R36/R37 → 4.7 kΩ 0402; R35 → 330 Ω 0402; R38/R39 stay 10 kΩ**, per Xilinx UG380
   v2.11. Split the old single "R30, R34–R39, 10 kΩ placeholder" bucket row into three rows
   with real functions:
   - R30 (PROGRAM_B), R34 (INIT_B), R36 (CSO_B/SPI_CS_N), R37 (CMPCS_B): **4.7 kΩ 1%**,
     `0402WGF4701TCE` (C25900, 16,779,143 in stock, **Basic**).
   - R35 (DONE pull-up): **330 Ω 1%**, `0402WGF3300TCE` (C25104, 1,386,471 in stock,
     **Basic**) — UG380 Fig. 2-12 note 11 requires this for iMPACT indirect flash
     programming; leaving DONE at 10 kΩ (the old placeholder) would have been a real
     programming-path defect, not just an inaccurate value.
   - R38, R39: **unchanged at 10 kΩ** — these are the W25Q32 flash's `~WP`/`~HOLD~RESET`
     pull-ups, not FPGA config pins, so UG380's config-pin table doesn't apply to them; they
     were correct already and are only being split out of the old bucket row for clarity.
   Both new jellybean values are Basic tier, matching the sourcing skill's tier-priority
   rule — no cost or assembly-fee impact. `fpga_core.py` already implements all six values
   exactly as above; only the BOM was stale.
   **Also confirmed, not a BOM change:** R31–R33 and the FPGA mode pins (M0/M1/HSWAPEN/
   SUSPEND) deliberately have no resistors per UG380 — those pins are hard-tied, not
   pulled. R31 and R32/R33 in this BOM are unrelated pre-existing rows (FPGA_RESET_N
   pull-up and LED series resistors respectively) and were not touched.
3. **C100/C200 — re-sourced to 0603, 100 V C0G, same 22 pF value. HIGH SEVERITY.** Was
   0402/50 V (`0402CG220J500NT`) with zero derating margin on the BNC input node; SPEC I3
   requires that node to survive ±50 V DC continuous, and `architecture/skeleton_bom.md`
   always specified 0603/100 V — sourcing had silently drifted off the architect's own spec
   at some point before this revision. Searched JLC live for 22 pF C0G ≥100 V in 0603:
   **15 results, all Extended tier — no Basic or Preferred part exists at this spec.**
   Selected `GCM1885C2A220JA16D` (Murata, LCSC C408549, 46,816 in stock, ¥0.0243) — highest
   stock among the 100 V-rated options (several others are 200–250 V but far thinner stock,
   e.g. 200 V/10,853 pcs, 250 V/2,062–7,876 pcs; 100 V is the architecture's own spec and
   this option comfortably clears the 500-unit WARN threshold). C101/C103 (220 pF, same
   node) were already sourced at 100 V and untouched.
4. **C30/C31 — 1 µF 0603 X7R → 100 nF 0402, dielectric could not follow to C0G.** These
   decouple X1 (10 MHz oscillator, ≤1 ps jitter budget) and U8; supply noise converts
   directly to jitter on X1, so local HF impedance (package size / ESL, i.e. self-resonant
   frequency) matters more here than bulk capacitance or dielectric class. Package shrink to
   0402 applied using the project's existing 100 nF X7R MPN (`CL05B104KB54PNC`, C307331,
   12,975,697 in stock, **Basic**) — same part used everywhere else in this design for
   100 nF decoupling, so no new line item. **The C0G half of the request could not be met:
   100 nF C0G does not exist in 0402 as a purchasable part.** Checked live against the full
   JLC 0402 C0G catalog (1,592 parts) — the largest 0402 C0G value stocked is 470 pF
   (`0402CG470J500NT`); 100 nF C0G starts at 1206 minimum (e.g. `GRM31C5C1H104JA01L`,
   1206, 100 V, C516516... stock 110,612). This is a real physical/manufacturing limit
   (C0G's low permittivity needs case volume that 0402 doesn't have at 100 nF), not a
   stock gap — no amount of re-searching finds an in-between part. Kept X7R, took the
   package win (which is the load-bearing half of the ask per the jitter rationale above).
   **`clocking.py` does not yet reflect this** — it still instantiates C30/C31 as 0603/1 µF
   via a `_c0603` template (`footprint='Capacitor_SMD:C_0603_1608Metric'`). Not fixed this
   pass (circuits/ was explicitly off-limits) — flagged in Carried forward for the reviewer/
   coder to pick up once their current pass on that file is done.
5. **Y1 symbol — `Device:Crystal` (2-pin) → `Device:Crystal_GND24` (4-pin), matching the
   4-pad footprint.** `usb_bridge.py` already instantiates `Device:Crystal_GND24` correctly
   (confirmed by reading the file); only the BOM row was stale, carrying the old 2-pin
   symbol name forward from an earlier revision. Verified `Crystal_GND24` exists as a
   standard symbol in the installed `Device.kicad_sym` (pins: 1=XTAL1, 2=GND, 3=XTAL2,
   4=GND — matches the code's ground tie on pins 2/4 for the EMI shield case).
6. **C92/C93 — confirmed correct, no change.** These are Y1's 12 pF load caps
   (`0402CG120J500NT`, C1547, 1,310,066 in stock, Basic), already correctly valued at
   12 pF per Cypress's own datasheet spec (p.4) and already in use in `usb_bridge.py`
   (`Y1[1] += C92[1]`, `Y1[3] += C93[1]`, both grounded). They do belong to `usb_bridge` —
   the architecture block list stopping at C91 was simply an omission in the original ref
   range, not a sign these were spurious. Fixed the `Parts by block` table below to include
   them in `usb_bridge`'s ref list (it previously only said "C80–C91").
7. **L2 footprint — confirmed via a manufacturer-exact re-source, not just checked.**
   `SMNR4020-2.2UH` (SXN) has no manufacturer-specific KiCad footprint; the coder assumed
   `Inductor_SMD:L_Changjiang_FNR4020S` on a same-geometry (4.0×4.0×2.0 mm) argument. Rather
   than merely confirming that assumption against a vendor drawing, **switched the MPN to
   the Changjiang-manufactured `FNR4020S2R2MT`** (LCSC C167825, 10,567 in stock, ¥0.0513,
   Extended) — same electrical spec class (2.2 µH, Isat 3.7 A / rated 2.8 A / DCR 52 mΩ vs.
   the actual ~0.36 A peak load, 7.8x margin), same 4×4 mm package, but now the footprint
   `Inductor_SMD:L_Changjiang_FNR4020S` is an **exact manufacturer match** instead of an
   assumed one — this mirrors how L1 was already sourced in rev.4 (Changjiang
   `FNR4030S3R3MT` against `L_Changjiang_FNR4030S`). Confirmed the footprint file exists in
   the installed KiCad `Inductor_SMD.pretty` library. `power.py` already targets this exact
   footprint string and value (`value='2.2uH'`) — **no code change needed**, this was a pure
   BOM/MPN correction. (Incidentally also fixed L1's BOM row: its Footprint column had been
   left blank/overwritten by the Isat note in rev.4 — filled in
   `Inductor_SMD:L_Changjiang_FNR4030S` there too, no MPN or value change.)
8. **U3/U4 bulk input capacitance — sourced two dedicated 10 µF caps rather than relying on
   the existing shared bulk.** AP62200T's datasheet Table 1 calls for ≥10 µF at VIN per
   regulator instance. Rev.4 argued the existing C2/C3 (2×22 µF on VBUS_SW, downstream of
   the load switch) already exceed that "per regulator" — true in raw µF terms, but on
   reflection that argument conflates *shared, somewhat-remote bulk capacitance* with
   *dedicated local input capacitance*, which is what the datasheet's own placement
   language ("at VIN") calls for: C2/C3 are one shared pair serving both bucks plus
   whatever else sits on VBUS_SW, and a layout note asking the PCB designer to place them
   "close enough" to both U3 and U4 simultaneously is a weaker guarantee than a component
   at each regulator's own VIN pin. `power.py` already has C10/C13 at 100 nF local HF
   bypass on U3/U4's VIN pins respectively, but 100 nF is two orders of magnitude short of
   the datasheet's 10 µF figure. **Allocated C35 (U3 VIN bulk) and C36 (U4 VIN bulk)**,
   both 10 µF X5R 25 V using the project's existing bulk-cap MPN (`CL21A106KAYNNNE`,
   C15850, 5,969,884 in stock, **Basic** — same part as C11/C14/C78/C90/C158-161/C258-261,
   so no new line item, just two more placements). Ref designators chosen as the next free
   slots after C34 (rev.4's newest additions) — C35/C36 were unused anywhere in the BOM.
   **This is a BOM-only addition**: `power.py` does not yet instantiate C35/C36. Flagged in
   Carried forward for the coder to add two `Part()` calls at U3.VIN and U4.VIN in parallel
   with the existing C10/C13, once the file is free to edit again.

## Out-of-band verification (report only, no BOM/code change)

- **BAV199LT1G pin function — verified against the primary onsemi datasheet
  (`BAV199LT1/D`, Rev. 13, Sept. 2026), not EasyEDA.** Fetched the datasheet's own pinout
  diagram (p.1): **pin 1 = Anode, pin 2 = Cathode, pin 3 is labeled "CATHODE/ANODE"** — the
  part is a **Dual Series Switching Diode**, i.e. the two internal diodes are connected in
  series (anode-1 → [D1] → node-3 → [D2] → cathode-2), not in a common-cathode or
  common-anode pair. Pin 3 is therefore the series midpoint: simultaneously the cathode of
  the diode facing pin 1 and the anode of the diode facing pin 2 — exactly what the
  datasheet's own "CATHODE/ANODE" label says, and exactly what `analog_frontend.py`'s
  comment already states ("D100 pin1 = A (to GND), pin2 = C (to avdd), pin3 = C/A common
  (signal)"). Working through the actual clamp topology in that file (pin1→GND as the
  chain's anode end, pin2→AVDD as the chain's cathode end, pin3→signal as the tap) gives:
  D_low conducts GND→signal when the signal dips below GND−Vf (clamps low), and D_high
  conducts signal→AVDD when the signal rises above AVDD+Vf (clamps high) — both directions
  correctly protected, consistent with the single forward direction the series-connected
  datasheet part actually has. **Conclusion: the code's orientation is electrically correct
  and matches the manufacturer's own pinout exactly.** The one imprecision worth flagging is
  in how it's described in prose elsewhere: pin 3 is not a "common cathode" or "common
  anode" node in the usual sense (both diodes sharing one polarity) — it is a series-stack
  midpoint that happens to be cathode-to-one-diode and anode-to-the-other simultaneously.
  No code or BOM change needed; this was purely a verification request.

## Artifacts (this revision)

| File | Contains | Read it when |
|---|---|---|
| `sourcing/sourced_bom.md` | Every ref designator: MPN, LCSC#, live stock, price, package, tier, KiCad symbol, KiCad footprint, notes — rev.5 changes: R52, R30/R34-R39/R35/R38-R39 split, C100/C200, C30/C31, C92/C93 (confirmed), L1/L2 footprints, L2 MPN, C35/C36 (new) | Always — before writing or reviewing any code |

## Parts by block (rev.5 — updates `power`, `clocking`, `fpga_core`, `usb_bridge` only)

| block_id | refs | MPNs |
|---|---|---|
| `usb_front` | J1, U1, U2, R1, R2, R3, C1, C2, C3 | TYPE-C 16PIN 2MD(073), USBLC6-2SC6, TPS22919DCKR, 0402WGF5101TCE(x2), 0402WGF1003TCE, CL21A106KAYNNNE, CL21A226MAQNNNE(x2) |
| `power` | U3, U4, U5, U6, U7, L1, L2, R10–R19, C10–C29, C32–C34, **C35, C36 (new, rev.5)**, FB1–FB4 | AP62200TWU-7(x2), TPS73633DBVR(x2), TLV2372IDR, FNR4030S3R3MT (L1), **FNR4020S2R2MT (L2, re-sourced rev.5)**, assorted E96 1% resistors, 100nF/1µF/10µF/22µF caps, 0402B334K160NT (C32 BST), CL05B104KB54PNC (C33 BST), 0402CG220J500NT (C34 feedforward), **CL21A106KAYNNNE (C35/C36, new VIN bulk, rev.5 — not yet in code, see Carried forward)**, BLM21PG601SN1D(x4) |
| `analog_frontend` (CH1) | J2, U100–U103, R100–R112, C100–C115, D100, D101 | KH-BNC50-3511, TPH2501-TR(x3), THS4521IDR, WR08X9093FTL, 0603WAF9092T5E, precision 147/137/1.00k/1.10k/33 network, **GCM1885C2A220JA16D (C100, 0603/100V, re-sourced rev.5)**, other C0G caps per `sourced_bom.md`, BAV199LT1G (pinout verified rev.5, no change), ESD9B5.0ST5G |
| `analog_frontend` (CH2) | J3, U200–U203, R200–R212, C200–C215, D200, D201 | same MPNs as CH1 (C200 also re-sourced rev.5) |
| `adc_channel` (CH1) | U150, R150, C150–C161 | AD9237BCPZ-40, placeholder 10k (R150 unresolved), 100nF/10µF decoupling |
| `adc_channel` (CH2) | U250, R250, C250–C261 | AD9237BCPZ-40, placeholder 10k (R250 unresolved), 100nF/10µF decoupling |
| `clocking` | X1, U8, R21, R22, R23, **C30, C31 (100nF 0402, re-sourced rev.5 — code not yet updated, see Carried forward)** | OXETDLJANF-10.000000, SN74LVC1G17DBVR, 0402WGF330JTCE(x2), jellybean 100Ω, CL05B104KB54PNC(x2) |
| `fpga_core` | U30, U31, J4, D30, D31, R30–R39, C40–C69 | XC6SLX9-2TQG144C, W25Q32JVSSIQ, HX PZ1.27-2x3P TP, LED green/red, **R30/R34/R36/R37=4.7k, R35=330R, R38/R39=10k (resolved rev.5)**, 100nF/4.7µF caps |
| `buffer_memory` | U40, R40, C70–C78 | W9825G6KH-6I, 0402WGF220JTCE, 100nF(x8)/10µF(x1) |
| `usb_bridge` | U50, U51, Y1, R50–R55, C80–C91, **C92, C93 (confirmed rev.5, refs added to this list)** | CY7C68013A-56LTXC, 24LC64-I/SN, DSX321G 24MHz, **`Device:Crystal_GND24` symbol (fixed rev.5)**, 2.2k(x2)/10k(x4 → R53-R55/R150/R250 style placeholders, R52 resolved rev.5 to 100k), 100nF(x10)/10µF(x1)/12pF(x2) |

## Next phase must

Unchanged from revision 4's list — this was a BOM-maintenance pass, not a new datasheet
worklist. The single still-open datasheet-librarian item remains:

1. **Generate a KiCad symbol for AP62200TWU-7** (U3/U4) — 6-pin TSOT26, pin table
   GND(1)/SW(2)/VIN(3)/FB(4)/EN(5)/BST(6), from `datasheets/AP62200TWU-7.pdf` p.3. Still the
   only open symbol-generation item from the AP62200T worklist.
2. Every other item from revision 2's original "Next phase must" list (AD9235 DNC pins,
   XC6SLX9 VCCAUX, FX2/24LC64 boot address, ⚠️ SYMBOL NEEDED / ⚠️ CUSTOM FP NEEDED rows,
   etc.) still stands unchanged.

## Carried forward (current, supersedes revision 4's list where noted)

- **BOM/code mismatch, new this revision: C30/C31.** `sourced_bom.md` now specifies 100 nF
  0402 X7R (`CL05B104KB54PNC`); `clocking.py` still instantiates 1 µF 0603
  (`CL10B105KB8NQNC` equivalent, via its `_c0603` template). Whoever picks up `clocking.py`
  next needs to change the template call to `_c0402`-equivalent, value `'100nF'`, footprint
  `Capacitor_SMD:C_0402_1005Metric`. Left unedited this pass because `circuits/` was
  explicitly off-limits.
- **BOM-only addition, new this revision: C35/C36.** Two new 10 µF VIN bulk caps exist in
  `sourced_bom.md` (power block) but not yet in `power.py`. Needs two `Part()` calls at
  U3.VIN and U4.VIN respectively, parallel with the existing C10/C13 100 nF HF bypass caps
  (`CL21A106KAYNNNE`, 0805 footprint `Capacitor_SMD:C_0805_2012Metric`).
- **AP62200TWU-7 (U3/U4) — ⚠️ SYMBOL NEEDED**, unchanged from rev.4 — still the only open
  AP62200T item.
- **AP62200T's VIN margin against USB VBUS droop is 0.2V** — unchanged from rev.4, recorded
  not fixed, see that revision's text below for the full figure.
- **X1 (OXETDLJANF-10.000000) — 50 pcs, single LCSC listing. Accepted single-source risk,
  not a blocker** — unchanged from rev.4.
- **L2 is now a Changjiang-manufactured part (`FNR4020S2R2MT`, 10,567 in stock)** rather
  than SXN's `SMNR4020-2.2UH` (121,497 in stock) — stock dropped by >10x but remains well
  clear of both the 100-unit FAIL and 500-unit WARN thresholds; traded stock margin for
  footprint certainty. Worth a second glance if a much larger production run is planned.
  L1 (also Changjiang, 36,844 in stock) is unaffected.
- **C100/C200 are now Extended tier (were already Extended before rev.5, only the
  package/voltage changed)** — no net tier-mix impact, just flagging that this is not a new
  Extended-tier line item, the row was Extended in every prior revision too.
- Every item in revision 4/3/2's "Carried forward" sections not explicitly superseded above
  (AD9235 DNC-pin tolerance, CY7C68013A+24LC64 boot address, XC6SLX9 pin table/config-mode
  pins, USB-C footprint diff, TPH2501-TR/HX header symbols, KH-BNC50-3511 `.kicad_mod`,
  R53–R55/R150/R250 unresolved placeholders) is unchanged and still open — not re-litigated
  this pass. R30–R39's placeholder note in those older sections is now stale and superseded
  by this revision's Decision #2.

## Do not redo

- Everything in revision 4/3/2's "Do not redo" lists — unchanged, **except** the AP62200T
  bootstrap/feedforward/FB-divider/L1 values, which were already settled in rev.4 and
  remain settled; this revision did not reopen any of them.
- **R52 = 100 kΩ (`0402WGF1003TCE`)** — datasheet-derived (CY7C68013A Table 5), matches
  code. Do not revert to 10 kΩ.
- **R30/R34/R36/R37 = 4.7 kΩ, R35 = 330 Ω, R38/R39 = 10 kΩ** — UG380-derived, matches code.
  Do not re-flatten these back into a single 10 kΩ bucket.
- **C100/C200 = 0603, 100 V, 22 pF C0G (`GCM1885C2A220JA16D`)** — matches
  `architecture/skeleton_bom.md`'s original spec, and is the only tier option that exists
  at this rating. Do not re-source to 0402/50V; the whole point was fixing that gap.
- **Y1 symbol = `Device:Crystal_GND24`** — matches the 4-pad footprint and the code. Do not
  revert to `Device:Crystal`.
- **L2 = `FNR4020S2R2MT` (C167825)** — manufacturer-exact footprint match. Do not revert to
  `SMNR4020-2.2UH` on a stock-count argument alone; the footprint certainty is the point.
- **BAV199LT1G pin orientation in `analog_frontend.py` is manufacturer-verified correct** —
  do not "fix" it based on the old EasyEDA-sourced doubt; the primary onsemi datasheet
  confirms the existing code.

## Receipt

- **Revision 5 (this pass):** 8 in-scope BOM rows updated/split (R52; R30/R34/R36/R37/R35/
  R38/R39 split from one bucket into three; C100/C200; C30/C31; C92/C93 confirmed
  unchanged; L1 footprint fixed + L2 re-sourced) + 2 new ref designators added (C35, C36).
  1 out-of-band verification completed (BAV199LT1G pin function, report-only, no change).
- 0 new sourcing failures; `sourcing/sourcing_failures.md` not written.
- Tier impact: all newly-resolved jellybeans (R30/R34/R35/R36/R37, C30/C31, C35/C36) landed
  Basic tier — no new assembly-fee exposure. C100/C200 remains Extended (was already
  Extended; the fix was voltage/package, not tier) — genuinely no Basic/Preferred option
  exists at 22pF/C0G/100V/0603, confirmed live.
- 1 request could not be met as literally stated and is documented rather than silently
  substituted: **100 nF C0G in 0402 does not exist as a purchasable part** (C30/C31) —
  kept X7R, took the 0402 package win, explained why in Decision #4.
- 2 known BOM/code gaps opened by this revision, both flagged in Carried forward for
  whoever next has write access to `circuits/`: C30/C31 (BOM says 0402/100nF, code still
  says 0603/1µF) and C35/C36 (in BOM, not yet instantiated in `power.py`).
- Status: **partial** — same open items as rev.4 (AP62200TWU-7 symbol generation, several
  unresolved placeholder resistors, USB-C footprint verification, custom BNC footprint)
  plus the two new BOM/code gaps this revision documents. Next: `datasheet-librarian` ->
  `handoffs/04_datasheets.md` (unchanged target — this was a maintenance pass, not a new
  phase transition).

---

# Revision 4 (preserved below, unchanged)

# Phase 3 handoff — Sourcing (revision 4 — completes the AP62200T support-passive dependency chain)

**Scope of this revision: finish what revision 3 deliberately left stale.** Revision 3's
"two BOM rows only" scoping correctly flagged rather than edited R10–R13, L1, the missing
bootstrap caps, and the possible feedforward cap — but those are true dependencies of the
U3/U4 regulator swap, not independent BOM items, so leaving them stale left the power
block internally inconsistent (FB resistors still computed for a VFB the board no longer
uses). This revision completes that dependency chain. Read revision 3 and revision 2
(below, preserved) for the full record of what led here.

## Decisions (this revision)

1. **R10/R11/R12/R13 (+3V3D and +1V2 feedback dividers) — updated from the stale
   SY8089A/VFB=0.6V values to the AP62200T/VFB=0.763V values computed and stock-verified
   in revision 3 but not yet placed in the BOM. Ref-to-function mapping, explicit per the
   coordinator's request:**
   - **R10 = +3V3D fb TOP** (VOUT→FB): 45.3 kΩ → **33.2 kΩ**, `0402WGF3322TCE`
     (LCSC C122548, 461,940 in stock, Extended, 0402 1%) → 0.763·(1+3.32) = **3.296V**.
   - **R11 = +3V3D fb BOTTOM** (FB→GND): unchanged at 10.0 kΩ — the bottom leg of a
     VOUT/VFB-scaled divider doesn't depend on VFB itself, only the ratio does, and R11
     stays in the shared 10.0 kΩ Basic-tier bucket (`0402WGF1002TCE`) with R13/R16/R17.
   - **R12 = +1V2 fb TOP** (VOUT→FB): 10.0 kΩ → **5.76 kΩ**, `FRC0402F5761TS`
     (LCSC C5153969, 126,259 in stock, Extended, 0402 1%) → 0.763·(1+0.576) = **1.202V**.
     Pulled out of the old shared 10.0 kΩ bucket row since its value changed.
   - **R13 = +1V2 fb BOTTOM** (FB→GND): unchanged at 10.0 kΩ, same reasoning as R11 —
     stays in the shared Basic-tier bucket.
   - R14, R16, R17 (VCM_REF divider) are unrelated to the bucks and untouched.
2. **L1 (+3V3D buck inductor) — 2.2µH → 3.3µH**, per the AP62200T datasheet's Table 1
   "Recommended Component Selections" for a 3.3V output. New part: **FNR4030S3R3MT**
   (LCSC C167870, cjiang, 4x4mm shielded, Isat 3.6A / rated current 2.6A, DCR 52mΩ,
   stock 36,844, Extended). Verified suitable for the actual current: with L=3.3µH,
   VIN=5V, VOUT=3.3V, fSW=750kHz (all datasheet-stated), ripple
   `ΔIL = VOUT·(VIN−VOUT)/(VIN·L·fSW) = 3.3·1.7/(5·3.3µH·750kHz) ≈ 0.45A`; peak current
   `= Iload(225mA) + ΔIL/2 ≈ 0.45A` — the chosen inductor's 2.6A rated current is a 5.7x
   margin over that peak.
3. **L2 (+1V2 buck inductor) — verified, not changed.** AP62200T Table 1 already
   recommends 2.2µH for a 1.2V output, which is what `SMNR4020-2.2UH` (LCSC C135262,
   already in the BOM) provides. Checked suitability against the actual +1V2 current:
   `ΔIL = 1.2·3.8/(5·2.2µH·750kHz) ≈ 0.55A`; peak `≈ 80mA + 0.28A ≈ 0.36A` — the existing
   part's 3.4A saturation rating is a 9.5x margin. No re-sourcing needed for this rail.
4. **Bootstrap capacitors added — a genuinely new requirement the retired SY8089A design
   never had a line item for**, because SY8089A's datasheet was never obtained (that's
   the entire reason it was replaced) so no one could confirm whether it needed one.
   AP62200T's datasheet is explicit: BST (pin 6) to SW (pin 2) needs a ceramic cap, with a
   value cue by output voltage:
   - **C32 (NEW ref) — U3 (+3V3D) BST cap: 330 nF X7R 16V**, `0402B334K160NT`
     (LCSC C301942, 49,233 in stock, Extended). Datasheet recommends 100–330nF when
     VOUT>3V; picked the top of that range for margin.
   - **C33 (NEW ref) — U4 (+1V2) BST cap: 100 nF X7R 50V**, `CL05B104KB54PNC`
     (LCSC C307331, same MPN as the project's ubiquitous 100nF decoupling bucket,
     12.97M in stock, Basic). Datasheet's default value applies since VOUT<3V.
5. **Feedforward capacitor — added for +3V3D only, per Table 1's explicit call-out.**
   Table 1 lists an optional "C5" position (10–100pF) in parallel with the top FB
   resistor for VOUT=3.3V, but marks it "Open" (do-not-populate) for VOUT=1.2V. Added:
   - **C34 (NEW ref) — U3 (+3V3D) feedforward cap, parallel with R10: 22 pF C0G**,
     `0402CG220J500NT` (LCSC C1555, 1,843,639 in stock, Basic) — reused the exact MPN
     already used elsewhere in this design for the same value (C100/C106/etc.), sits
     mid-range in the datasheet's 10–100pF window. **U4 gets no equivalent part** —
     Table 1 explicitly says not to populate it for the 1.2V rail.
6. **Input capacitance and voltage rating — checked, not changed.** AP62200T Table 1
   wants ≥10µF at VIN per regulator; the existing shared bulk caps downstream of the load
   switch (C2/C3, `CL21A226MAQNNNE`, 2×22µF=44µF, 25V rating) already exceed that per
   regulator and are rated far above the ≤18V absolute max — no new input cap needed.
7. **Net effect: 3 new ref designators added to the BOM this revision (C32, C33, C34),
   beyond the architect's original ~230-placement/~45-line-item count.** This is a
   deliberate, datasheet-justified deviation, not scope creep — flagged explicitly so it
   isn't mistaken for an unreviewed addition later.

## Decisions carried over verbatim from revision 3 (recorded here per the coordinator's
instruction, not re-verified)

- **AP62200T's VIN margin against USB VBUS droop is 0.2V** (4.2V datasheet minimum vs.
  4.4V worst-case droop per architecture's own figure in `ic_selection.md`) — tighter
  than the SY8089A it replaces (2.7–5.5V). The part is kept; this is recorded in Carried
  forward below (not fixed — there is no sourcing fix for a device's own spec floor) so
  ERC/review sees it explicitly rather than having to rediscover it.
- **X1 (OXETDLJANF-10.000000) at 50 pcs, single LCSC listing** — accepted as a
  deliberate single-source risk for this 10-board run (5x margin over the 10 needed),
  because its ≤1ps RMS phase-jitter spec is what makes the 12-bit ADC target achievable
  and no better-stocked part on JLCPCB publishes a jitter figure at all (phase 4 also
  evaluated and rejected ECS-2033-100-BN on exactly this gap). Recorded as an accepted
  risk, not a blocker — see Carried forward.

## Revision 3's Decisions (preserved verbatim for context — superseded in part by this revision's #1–#7 above)

1. **U3/U4 buck regulator replaced: SY8089AAC → AP62200TWU-7 (Diodes Incorporated).**
   Forced by SPEC.md R4 [HARD] (no part single-sourced through an obsolete/NRND MPN) —
   SY8089AAC is NRND at Silergy with no obtainable datasheet (phase 4 confirmed 7+ URL
   attempts failed; manufacturer's own site marks it 不推薦用於新設計). Replacement
   selected and **its datasheet downloaded and read in full** (Diodes DS41957 Rev.6-2,
   23 pages, saved to `datasheets/AP62200TWU-7.pdf`):
   - **LCSC C2895288, live stock 34,540** (vs. 10,740 for the old part) — comfortably
     clears the >100 threshold with a wide margin, not <500 WARN either.
   - **Actively produced** — July 2023 datasheet, no NRND/EOL marking anywhere in the
     document or on the ordering-information page; this is Diodes' current catalog part.
   - **2A continuous output, synchronous, adjustable 0.8V–7V (0.763V–7V for the "T"
     variant)** — 8.9x margin over the +3V3D rail's 225 mA budget and 25x over +1V2's
     80 mA budget (architecture's power budget, `ic_selection.md` §"Rail-by-rail power
     budget"). Same physical part serves both rails via different FB dividers, matching
     the architect's original one-MPN-two-rails intent.
   - **VFB = 0.763V typical (0.747–0.778V over -40 to +125°C), confirmed from the
     Electrical Characteristics table** — this is the AP62200T sub-variant specifically
     (the base AP62200/AP62201 use VFB=0.800V; the "T" in the MPN and the Ordering
     Information table on datasheet p.20 both confirm AP62200TWU-7 = 0.763V typ, TSOT26
     package, PFM/PWM operation).
   - **EN pin polarity confirmed active-high**, from the "Enable" section (datasheet p.13)
     and the EN electrical spec: logic-high threshold 1.20V typ (1.10–1.25V), logic-low
     threshold 1.10V typ (1.04V min). "Drive EN high to turn on the regulator and low to
     turn it off." An internal 1.5µA pull-up current source from the internally-regulated
     VCC to EN means **floating EN auto-enables** the part once VIN's rise brings the
     pulled-up EN node past the logic-high threshold (2.5ms soft-start after that).
   - **Feedback dividers, computed from Eq. 8 (`R1 = R2·(VOUT/VFB − 1)`) and cross-checked
     against the datasheet's own Table 1 "Recommended Component Selections" for the
     AP62200T column:**
     - **+3V3D: R_top (VOUT→FB) = 33.2 kΩ, R_bot (FB→GND) = 10.0 kΩ** →
       `0.763·(1+3.32) = 3.296V` (+0.12% vs 3.3V nominal, inside every load's ±5% window).
     - **+1V2: R_top = 5.76 kΩ, R_bot = 10.0 kΩ** →
       `0.763·(1+0.576) = 1.202V` (inside Spartan-6 VCCINT's 1.14–1.26V window).
     - Matching 0402 1% E96 candidates found and stock-verified this pass (not yet placed
       in the BOM — see Next phase must): 33.2 kΩ → `0402WGF3322TCE` (LCSC C122548,
       461,940 in stock, Extended); 5.76 kΩ → `FRC0402F5761TS` (LCSC C5153969, 126,259 in
       stock, Extended).
   - **Table 1 also gives L/C values** — at the time of writing this bullet (revision 3)
     these were deliberately flagged, not applied, per that revision's narrow two-row
     scope. **They are now applied — see this revision's (rev.4) Decisions #2–#6 above:**
     L1 → 3.3µH, L2 confirmed unchanged at 2.2µH, BST caps C32/C33 added, feedforward
     cap C34 added, input cap rating checked and found already sufficient.
   - **Vin margin — kept despite a tighter number than the old part, flagged explicitly.**
     Recommended Operating Conditions: VIN 4.2–18V (this is a guaranteed-accuracy spec
     range, not the hard cutoff — UVLO falling threshold is 3.6V typ, POR rising is
     3.90–4.15V, so the part won't shut off until well below 4.2V). Architecture's own
     worst-case USB VBUS droop figure is 4.4V (`ic_selection.md` — this exact number was
     used to *reject* TPS562201's 4.5V minimum). AP62200T's 4.2V min clears that with
     **0.2V of margin**, versus SY8089A's much wider 2.7–5.5V range. This is real headroom
     loss, not a failure — 4.2V < 4.4V holds — but it's tighter than what architecture
     designed around, so it's called out rather than silently accepted.
   - **Why not another Silergy part (e.g. SY8088AAC, same 2.5–5.5V range as the rejected
     SY8089A, found in this pass with 138k+ stock):** explicitly rejected. Reusing the
     same manufacturer whose SY8089AAC just failed R4 for an undocumented-NRND pattern
     reintroduces the identical risk class this substitution exists to eliminate, even
     though SY8088AAC itself may currently have a datasheet — diversifying away from
     Silergy for this design's bucks is the safer call given the demonstrated pattern.
   - Package changed SOT-23-5 → TSOT-26 (6-pin, same footprint family as SOT-23-6).
     Footprint `Package_TO_SOT_SMD:TSOT-23-6` verified to exist in the KiCad system
     library and validated with `validate-footprints.py` (dimensions cross-checked
     against the datasheet's Package Outline Dimensions table for TSOT26: D=2.7–3.1mm,
     E1=1.5–1.7mm, e=0.95mm pitch — matches standard JEDEC TSOT-23-6).
   - **No local KiCad symbol** (`find-symbol.py` reports `MISSING`) — flagged
     `⚠️ SYMBOL NEEDED` in the BOM, per rule (a missing symbol is not grounds to
     substitute a different part). Datasheet pin table is on p.3 ("Pin Descriptions") and
     the pin diagram on p.1 ("Pin Assignments", TSOT26 column): VIN(3), SW(2), GND(1),
     FB(4), EN(5), BST(6).

2. **X1 MPN updated in the BOM to match phase-4's already-decided supersession.**
   Phase 4 (`handoffs/04_datasheets.md` Decision #1) had already determined
   `SX3M10.000B10F20TNN` publishes no jitter spec at all and substituted
   **TAITIEN OXETDLJANF-10.000000 (LCSC C17609541)** — same SMD3225-4P footprint,
   datasheet-published RMS phase jitter ≤1ps (7x inside the ~7ps budget) — but
   `sourced_bom.md` still listed the old MPN; that row is now corrected.
   **Live stock re-verified this pass: 50 pcs, single LCSC listing, no alternate found** —
   below the sourcing skill's >100-unit threshold in absolute terms. **Reclassified in
   revision 4, per the coordinator: an accepted single-source risk, not a blocker** — see
   "Decisions carried over" above and Carried forward below.

## Artifacts

| File | Contains | Read it when |
|---|---|---|
| `sourcing/sourced_bom.md` | Every ref designator: MPN, LCSC#, live stock, price, package, tier, KiCad symbol, KiCad footprint, notes | Always — before writing any code |
| `datasheets/AP62200TWU-7.pdf` | Diodes DS41957 Rev.6-2, full 23pp — downloaded and read this pass | Datasheet-librarian's `AP62200TWU-7_SUMMARY.md` and symbol generation |

## Parts by block (unchanged from revision 2 except `power` and `clocking`)

| block_id | refs | MPNs |
|---|---|---|
| `usb_front` | J1, U1, U2, R1, R2, R3, C1, C2, C3 | TYPE-C 16PIN 2MD(073), USBLC6-2SC6, TPS22919DCKR, 0402WGF5101TCE(x2), 0402WGF1003TCE, CL21A106KAYNNNE, CL21A226MAQNNNE(x2) |
| `power` | U3, U4, U5, U6, U7, L1, L2, R10–R19, C10–C29, **C32–C34 (new, rev.4)**, FB1–FB4 | **AP62200TWU-7(x2)**, TPS73633DBVR(x2), TLV2372IDR, **FNR4030S3R3MT (L1, new)**, SMNR4020-2.2UH (L2, unchanged), assorted E96 1% resistors (**R10=33.2k, R12=5.76k, updated rev.4**), 100nF/1µF/10µF/22µF caps, **0402B334K160NT (C32 BST), CL05B104KB54PNC (C33 BST), 0402CG220J500NT (C34 feedforward)**, BLM21PG601SN1D(x4) — power block is now internally consistent with the AP62200T datasheet as of rev.4 |
| `analog_frontend` (CH1) | J2, U100–U103, R100–R112, C100–C115, D100, D101 | KH-BNC50-3511, TPH2501-TR(x3), THS4521IDR, WR08X9093FTL, 0603WAF9092T5E, precision 147/137/1.00k/1.10k/33 network, C0G caps per `sourced_bom.md`, BAV199LT1G, ESD9B5.0ST5G |
| `analog_frontend` (CH2) | J3, U200–U203, R200–R212, C200–C215, D200, D201 | same MPNs as CH1 |
| `adc_channel` (CH1) | U150, R150, C150–C161 | AD9237BCPZ-40, placeholder 10k (R150 unresolved), 100nF/10µF decoupling |
| `adc_channel` (CH2) | U250, R250, C250–C261 | AD9237BCPZ-40, placeholder 10k (R250 unresolved), 100nF/10µF decoupling |
| `clocking` | X1, U8, R21, R22, R23, C30, C31 | **OXETDLJANF-10.000000**, SN74LVC1G17DBVR, 0402WGF330JTCE(x2), jellybean 100Ω, 1µF(x2) |
| `fpga_core` | U30, U31, J4, D30, D31, R30–R39, C40–C69 | XC6SLX9-2TQG144C, W25Q32JVSSIQ, HX PZ1.27-2x3P TP, LED green/red, 10k/1k resistors, 100nF/4.7µF caps |
| `buffer_memory` | U40, R40, C70–C78 | W9825G6KH-6I, 0402WGF220JTCE, 100nF(x8)/10µF(x1) |
| `usb_bridge` | U50, U51, Y1, R50–R55, C80–C91 | CY7C68013A-56LTXC, 24LC64-I/SN, DSX321G 24MHz, 2.2k(x2)/10k(x4) resistors, 100nF(x10)/10µF(x1)/12pF(x2) |

## Next phase must

Addressed to **datasheet-librarian** (this circuit's `next_phase` target):

(Revision 3's original items #1–#4 here — generate AP62200TWU-7 symbol, update
R10/R12, update L1, add a BST cap for U3 — are **done as of revision 4** except symbol
generation, which is correctly datasheet-librarian's job, not sourcing's. Revision 3's
item #5 (revision 2's outstanding list) still stands; folded into the current list below.)

**Current "Next phase must" (addressed to datasheet-librarian, supersedes revision 3's list):**

1. **Generate a KiCad symbol for AP62200TWU-7** — 6-pin TSOT26. Pin table:
   GND(1)/SW(2)/VIN(3)/FB(4)/EN(5)/BST(6), from `datasheets/AP62200TWU-7.pdf` p.3
   ("Pin Descriptions") — already downloaded, no need to re-fetch. Still the only open
   item from the original AP62200T worklist — everything else (FB dividers, L1, BST
   caps, feedforward cap) is done as of revision 4.
2. Generic `Device:C`/`Device:L` symbols cover C32/C33/C34/L1 — no new symbol generation
   needed for those, only correct footprint/value assignment at coding time.
3. Everything from revision 2's "Next phase must" list (AD9235 DNC pins, XC6SLX9 VCCAUX,
   FX2/24LC64 boot address, etc.) still stands unchanged — see below.

## Carried forward (current, supersedes revision 3's list)

- **AP62200TWU-7 (U3/U4) — ⚠️ SYMBOL NEEDED**, pin table available, datasheet PDF already
  in `datasheets/`. This is now the *only* open AP62200T item — its support passives
  (R10–R13, L1, C32/C33/C34) are settled as of revision 4.
- **AP62200T's VIN margin against USB VBUS droop is 0.2V** (4.2V datasheet minimum vs.
  4.4V worst-case droop per architecture's own figure in `ic_selection.md`, §"Rail-by-rail
  power budget" context) — tighter than the SY8089A it replaces (2.7–5.5V range). **The
  part is kept as-is; this is a recorded margin-watch item, not a defect.** UVLO itself
  doesn't trip until 3.6V typ, so the board won't brown out at 4.4V — but datasheet-
  guaranteed regulation accuracy is only assured from 4.2V up, leaving 0.2V of headroom
  against the worst case. Flagged here explicitly so ERC/design-review sees it without
  having to rediscover it from the BOM notes.
- **X1 (OXETDLJANF-10.000000) — 50 pcs, single LCSC listing. Accepted single-source
  risk, not a blocker**, for this 10-board run: 5x margin over the 10 pcs needed, and its
  ≤1ps RMS phase-jitter spec (7x inside the ~7ps budget) is what makes the 12-bit ADC
  target achievable — no better-stocked JLCPCB part publishes a jitter figure at all
  (SX3M and ECS-2033-100-BN, both evaluated in phase 4, publish none). Re-verify or
  qualify a second source only if a production run beyond this prototype batch is planned.
- Every item in revision 2's "Carried forward" section (AD9235 DNC-pin tolerance,
  CY7C68013A+24LC64 boot address, XC6SLX9 pin table/config-mode pins, USB-C footprint
  diff, TPH2501-TR/HX header symbols, KH-BNC50-3511 `.kicad_mod`) is unchanged and still
  open — not re-litigated this pass.

## Do not redo

- Everything in revision 2's "Do not redo" list — unchanged.
- **AP62200TWU-7 as the U3/U4 replacement** — datasheet read in full; VFB, EN polarity,
  and FB dividers are primary-source-verified facts, not assumptions. Do not reopen this
  selection without a new stock/lifecycle failure.
- **OXETDLJANF-10.000000 as X1** — already settled by phase 4; revision 3 synced the BOM
  row and re-verified live stock; revision 4 reclassified its stock level as an accepted
  risk rather than a threshold failure. Do not re-source X1.
- **R10=33.2kΩ, R11=10.0kΩ, R12=5.76kΩ, R13=10.0kΩ, L1=3.3µH (`FNR4030S3R3MT`),
  L2=2.2µH (unchanged), C32=330nF (U3 BST), C33=100nF (U4 BST), C34=22pF (U3
  feedforward, optional/populate)** — all computed, stock-verified, and now placed in
  `sourced_bom.md` as of revision 4. Do not recompute or re-derive these; the block coder
  uses them verbatim.

## Receipt

- **Revision 4 (this pass):** completed the AP62200T support-passive dependency chain
  that revision 3 deliberately left stale. 4 BOM rows edited (R10, generic-bucket row
  split to carve out R12, L1, and the U3/U4 notes column) + 3 new BOM rows added (C32,
  C33, C34). Net new ref designators: 3 (C32/C33/C34), bringing the design from ~230 to
  ~233 placements — documented, not silent.
- Feedback dividers: R10/R12 now hold datasheet-derived values (33.2kΩ, 5.76kΩ) instead
  of the stale SY8089A-era ones; R11/R13 confirmed unaffected at 10.0kΩ.
- Inductors: L1 changed 2.2µH→3.3µH (new MPN `FNR4030S3R3MT`, C167870, 36,844 in stock);
  L2 checked and confirmed still correct at 2.2µH, no change.
- Bootstrap caps: 2 new parts added (C32 330nF for U3, C33 100nF for U4) — a requirement
  the old undocumented SY8089A design never had a line item for.
- Feedforward cap: 1 new optional part added (C34, 22pF, U3/+3V3D only, per the
  datasheet's own Table 1 — explicitly not populated on U4/+1V2).
- Two items recorded rather than fixed, per the coordinator's explicit instruction: the
  AP62200T's 0.2V VIN margin (Carried forward) and X1's 50-pcs single-source stock
  (reclassified from FAIL-flagged to accepted-risk in Carried forward).
- 0 new sourcing failures; `sourcing/sourcing_failures.md` not written.
- Status: **partial** — the only remaining open AP62200T item is symbol generation
  (datasheet-librarian's job, correctly out of sourcing's scope). All other revision-2
  open items (AD9235 DNC pins, XC6SLX9 config pins, FX2/24LC64 boot address, USB-C
  footprint diff, etc.) are unchanged and still open. Next: `datasheet-librarian` ->
  `handoffs/04_datasheets.md`.

---

# Revision 2 (preserved below, unchanged)

## Decisions (revision 2 — historical, superseded by revisions 3–4 above)

1. **AD9237BCPZ-40 stock verified live, unchanged at 211 pcs** (`jlc_get_part` and
   `jlc_stock_check` both confirm). 10-board build needs 20 (2/board) — 10.5x margin. Kept
   as primary; stock is thin in absolute terms (<500 WARN threshold) but not FAIL, and no
   JLC-stocked alternative beats it on power/package (`jlc_find_alternatives` on C514275
   returned zero same-category compatible parts; broader search found nothing else in
   LFCSP-32 12-bit pipeline parallel-CMOS ADC territory).
2. **AD9235BCPZ-40 formally qualified as second source**, beyond the architect's package
   check: pulled both parts' pinouts via `jlc_get_pinout` and confirmed **33/33 pins match**
   position-for-position. The only difference: AD9237 pins 1/3/5 (MODE2/OE/GC — expanded
   control mode) map to DNC on AD9235. Since this design doesn't use AD9237's mux/gain
   features (confirmed against `ic_selection.md` — parallel CMOS output only), those three
   pads simply go unused on a drop-in. **Phase 4 must still confirm from the AD9235
   datasheet whether its DNC pins tolerate a populated pad/trace** (some ADI DNC pins are
   bonded to internal test nodes) before treating this as a true zero-change swap.
3. **The JLCPCB tier snapshot was correct, not broken** — the architect's "basic:0
   preferred:0" result was a snapshot-time gap, not a systemic DB issue. Live `jlc_get_part`
   / `jlc_search` calls this phase found real Basic-tier parts: all standard jellybean
   passives (100 nF 0402, 10 µF/22 µF 0805, most common E24 resistor values) are **Basic**
   tier; every named IC and every precision E96 passive (909 kΩ, 90.9 kΩ, 147 Ω, 137 Ω,
   45.3 kΩ, 12.1 kΩ, 1.10 kΩ) is genuinely **Extended** — that part of the architect's
   assumption holds. Net effect: the BOM has far fewer Extended-tier line items than the
   architecture phase assumed; assembly-fee exposure is lower than budgeted.
4. **909 kΩ 0805 1% is in stock exactly** (WR08X9093FTL, C170980, 4,531 pcs) — most search
   paths surface only the far-more-common 910 kΩ (E24) first. Confirmed the exact E96 value
   the attenuator arithmetic requires; do not let a future re-source silently drift to 910 k.
5. **Reference buffer: substituted TLV2372IDR (C27204) for the architect's SGM8521**.
   SGM8521XN5/TR has no KiCad symbol locally (`MISSING`) and is otherwise unverified;
   TLV2372 is RRIO, 1 pA Ib (same class), Basic-adjacent stock (43,717 pcs), and has an
   **EXACT** local symbol match (`Amplifier_Operational:TLV2372`). Trade: SOIC-8 dual
   package instead of SOT-23-5 single — the skeleton BOM marked this part "sourcer's
   choice," so this is in scope. Second channel's input/output must be tied as a follower
   by the coder to avoid a floating unused op-amp half.
6. **USB-C connector footprint is a generic stand-in, not manufacturer-exact.**
   `cse_get_kicad` found no CSE match for "TYPE-C 16PIN 2MD(073)" (SHOU HAN); no
   manufacturer-specific `.kicad_mod` exists locally either. Used
   `Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A` (generic 16P) as a placeholder —
   flagged for phase 4 to confirm against JLC's mechanical PDF (mounting-hole pattern is
   the risk, not pinout).
7. **Ferrite bead package moved 0603 → 0805** (FB1–4). No 600 Ω @ 100 MHz part exists in
   0603 at JLC (only 60 Ω was found under that footprint); BLM21PG601SN1D (0805, 1.4 A,
   C41556732) is the closest in-spec match. Minor deviation from the skeleton BOM's package
   preference, not from any [calc] value.
8. **CY7C68013A-56LTXC package confirmed QFN-56 8x8mm** via live `jlc_get_part`
   (`"package":"QFN-56-EP(8x8)"`), matching the architect's flagged symbol name
   `MCU_Cypress:CY7C68013A-56LTX`. Second source CY7C68013A-56PVXC confirmed SSOP-56,
   footprint `Package_SO:SSOP-56_7.5x18.5mm_P0.635mm` (validated).
9. **BAV199LT1G has no usable local symbol stand-in.** Nearest name matches
   (`Diode:BAV19` — single diode, THT DO-35; `Diode:BAV199DW` — quad, SOT-363) are the
   wrong diode topology and wrong pin count; do not use either as a placeholder. Left
   MISSING for phase 4 to generate from the datasheet pin table, per the architect's note
   that a symbol gap is not grounds to substitute a different part.
10. **Passive ref-designator rows are grouped by identical MPN**, not listed one physical
    placement at a time, for pure repeated decoupling (100 nF/10 µF/22 µF/4.7 µF). Every
    [calc] and signal-relevant ref (per `net_plan.md`) got its own row. Ref ranges the
    architect allocated but `net_plan.md` never itemized a function for (R19, R30, R34–R39,
    R52–R55, R150/R250) are called out explicitly rather than assigned a fabricated
    function — see Carried forward.

## Artifacts (revision 2)

| File | Contains | Read it when |
|---|---|---|
| `sourcing/sourced_bom.md` | Every ref designator: MPN, LCSC#, live stock, price, package, tier, KiCad symbol, KiCad footprint, notes | Always — before writing any code |

## Next phase must (revision 2)

Addressed to **datasheet-librarian**:

1. **Generate KiCad symbols** for: `AD9237BCPZ-40`, `AD9235BCPZ-40` (second source, same
   pin table), `XC6SLX9-2TQG144C`, `W9825G6KH-6I`, `TPH2501-TR`, `TPS22919DCKR`,
   `BAV199LT1G`, `HX PZ1.27-2x3P TP` (2x3 JTAG header — generic 6-pin part,
   low priority). `SY8089AAC` from this list is now obsolete — replaced per revision 3's
   Decision #1 above; add `AP62200TWU-7` to this worklist instead (see revision 3's
   Next phase must #1). Datasheet URLs are in `mcp__pcbparts__jlc_get_part` results this
   phase pulled for each (re-query by LCSC# in `sourced_bom.md` if needed).
2. **Generate custom footprint** for `KH-BNC50-3511` (architect-flagged) — mechanical
   drawing is in its LCSC datasheet PDF (linked in `sourced_bom.md`).
3. **Confirm the USB-C connector footprint** (`Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A`
   used as placeholder) against the JLC part's own mechanical PDF for `TYPE-C 16PIN
   2MD(073)` (C2765186) — pin function is standard, the risk is mounting-hole placement.
4. **Confirm AD9235BCPZ-40's DNC pins (1/3/5) are safe to leave unpopulated/floating**
   on the shared AD9237 footprint before the second source is treated as a true drop-in
   (decision 2 above).
5. ~~Confirm the 10 MHz XO's RMS phase jitter~~ — **closed**, see revision 3 above.
6. **Confirm AD9237 power at 10 MSa/s** (architecture assumption: ≤90 mW datasheet figure).
7. Every ⚠️ SYMBOL NEEDED / ⚠️ CUSTOM FP NEEDED row in `sourced_bom.md` is this phase's
   worklist — do not re-source a different part just because a symbol is missing.

## Carried forward (revision 2)

- **R3 (thin ADC stock) — addressed, not fully closed.** AD9237 stock re-verified live at
  211 pcs (unchanged from architecture snapshot), sufficient for this run with 10.5x margin,
  but still <500 WARN threshold against future re-orders. AD9235BCPZ-40 (139 pcs, also
  thin) is the qualified second source with 33/33 pin match; if AD9237 drops further before
  fab, switch is low-risk pending phase-4's DNC-pin confirmation (decision 2/4 above).
- ~~R2 (oscillator jitter) — still unresolved.~~ **Closed in revision 3** (X1 row synced to
  phase 4's OXETDLJANF-10.000000 decision).
- **Unallocated ref designators** — `R19` (power block), `R30`, `R34–R39` (fpga_core),
  `R52–R55` (usb_bridge), `R150`/`R250` (adc_channel): `architecture/skeleton_bom.md`
  reserved these ref ranges but `architecture/net_plan.md` never named a function for them.
  Given placeholder 10 kΩ 1% values in `sourced_bom.md` (Basic tier, negligible cost either
  way) so the ref designators aren't orphaned, but the **coder must confirm actual function**
  (pull-up, series termination, or genuinely spare) against the FPGA pinout before finalizing
  — do not assume 10 kΩ is correct without checking what each pin does.
- **TLV2372IDR substitution for the DC reference buffer** (decision 5) — package changed
  from single SOT-23-5 to dual SOIC-8; coder ties the unused second channel as a follower.
- **USB-C connector footprint is unverified against manufacturer mechanics** (decision 6).
- **Ferrite bead package moved 0603→0805** (decision 7) — footprint area increases slightly;
  flag if board space near the rail-isolation points is tight.
- **Trimmer capacitor question — still closed per architecture.** No SMD trimmer was
  reintroduced; this phase didn't search for one again since I2 was already overturned with
  reason in the architecture handoff.

## Do not redo (revision 2)

- Every `[calc]` value in `architecture/ic_selection.md` and `skeleton_bom.md` — confirmed
  sourceable at the exact value for every precision resistor/cap checked (909 k, 90.9 k,
  147, 137, 45.3 k, 12.1 k, 22 p, 220 p, 270 p, 680 p, 100 p, 1.00 k, 1.10 k, 33 Ω). None
  needed rounding to a nearby E24 value. **Exception: the +3V3D/+1V2 buck feedback pair
  (45.3k/10.0k and 10.0k/10.0k) is superseded by revision 3 above — those two dividers were
  computed for SY8089A's VFB=0.6V and no longer apply.**
- The architect's block manifest and 8-block/10-instance modular structure.
- AD9237BCPZ-40 as primary ADC — re-verified live, not just carried forward.
- The five `[U]` requirements and every HARD architecture decision — untouched by sourcing.

## Receipt (revision 2)

- ~45 unique line items sourced, ~230 placements covered; all live-stock-verified
  2026-09-21.
- Tier split: correcting the architect's "everything Extended" assumption — roughly half
  the jellybean passive line items are **Basic** tier; all named ICs and all precision E96
  passives are genuinely **Extended** (13 IC/connector line items + ~15 precision passive
  line items).
- 0 sourcing failures — no part was unobtainable; `sourcing/sourcing_failures.md` not
  written.
- Custom footprints: 1 (`KH-BNC50-3511`, architect-flagged) + 1 unverified generic
  (USB-C connector, decision 6).
- Symbols missing: 9 parts flagged ⚠️ SYMBOL NEEDED (see Next phase must #1).
- R3 (ADC stock) addressed with live re-verification + a pin-confirmed second source;
  R2 (oscillator jitter) — resolved in revision 3.
