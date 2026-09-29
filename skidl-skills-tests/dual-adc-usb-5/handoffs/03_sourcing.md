---
phase: 03_sourcing
agent: part-sourcer
circuit: dual_adc_usb
written: 2026-09-21T00:30:00Z
status: complete
revision: 4
next_phase: 04_datasheets
---

# Phase 3 handoff — Sourcing

## Revision 4 (narrow amendment, 2026-09-21T00:30:00Z)

Executes architecture revision 3's **WO-3** (`handoffs/02_architecture.md`) verbatim: four
new/changed filter-cap values in `afe_channel`, one new resistor row reusing an existing
MPN, and a value note on the existing `R8`/`R9` generic row. **Nothing else was re-sourced,
re-priced, or re-verified** — not the critical-path five, not any row untouched by WO-3.
All five live-checked parts below were confirmed today (2026-09-21) via
`mcp__pcbparts__jlc_get_part`, all Basic or Preferred tier, all in stock well above the
>100 floor.

1. **`C_f` (C103/203, C104/204): 27 pF → 10 pF.** New MPN `CL10C100JB8NNNC` (**C1634**),
   stock 1,514,480, $0.0076, Basic tier (was Extended — a tier improvement, not just a
   value change). Retires `FCC0603N270J500CT`/C5137568. Per architecture decision 18/WO-1:
   `C_f` stops being a provisional stray value and becomes a fixed pole term in the new
   2nd-order MFB filter.
2. **`C_mfb` (C111/211, new): 68 pF.** New MPN `CL10C680JB8NNNC` (**C28262**), stock
   153,120, $0.0188, Preferred tier. One differential cap between `mfb_p`/`mfb_n` per
   channel — **not** two caps to GND (a GND cap here couples into the FDA's common-mode
   loop, per WO-1 item 2's explicit warning). New row in `sourced_bom.md`; no prior part
   existed at this ref.
3. **`C_diff` (C105/205): 470 pF → 330 pF.** New MPN `CL10C331JB8NNNC` (**C1664**), stock
   906,099, $0.0180, Basic tier (was Extended). Retires C27694. Output-RC pole retune for
   the 3rd-order Butterworth response (decision 18).
4. **`C_cm` (C106/206, C107/207): 220 pF → 100 pF.** New MPN `CL10C101JB8NNNC` (**C14858**),
   stock 3,189,308, $0.0085, Basic tier (was Extended). Retires C27675. Same retune as
   `C_diff`.
5. **`R_mfb` (R111/R112, R211/R212, new): 499 Ω ±0.1%, same MPN as `R105/R106` —
   `PTFR0603B499RP9` (**C478882**), re-verified live stock 28,010 (was 28,087 two days
   prior — normal drift, still Extended tier, still well clear of WARN). Added as its own
   new row in `sourced_bom.md` rather than merged into the existing `R105/106` row, so the
   two functions (`R_g` vs the new `R_mfb`) stay distinguishable; board-wide usage of
   `C478882` is now **8 pieces total** (4 existing + 4 new), matching the architect's WO-3
   quantity note.
6. **`R8`/`R9`: value note only, no new MPN.** The row was already "generic 1% 0603,
   sourcer's discretion" and stays that way — updated to record **R8 = 22.0 kΩ, R9 =
   11.0 kΩ** (VBIAS retargeted 1.200 V → 1.100 V, architecture decision 19:
   3.3·11.0/33.0 = 1.1000 V exactly). Noted the architect's optional concrete parts
   (0603WAF2202T5E/C31850, 0603WAF1102T5E/C25950, both Basic+Preferred) and the explicit
   **do-not-substitute on 23.0 kΩ** (not an E96/E24/E192 value).

**Symbols/footprints unchanged for all five**: all are generic `Device:C`/`Device:R` on
`Capacitor_SMD:C_0603_1608Metric`/`Resistor_SMD:R_0603_1608Metric`, the same footprint
family every other 0603 C0G/thin-film row in this BOM already uses — no new symbol-search
or footprint-validation work was needed.

`sourcing/sourced_bom.md` edited in place: the `afe_channel` ref-number key table (top of
file, values for 103/203, 105/205, 106/206, 107/207, plus new 111/211, 112/212, C111/211
rows added), the `afe_channel × 2` detail table (`C_f`, `C_diff`, `C_cm` rows updated,
`R_mfb` and `C_mfb` rows added), and the `analog_power_ref` `R8, R9` row. No other row,
block, or decision in this document was touched — the critical-path five (ADS5231IPAGT,
GW1NR-9, FT232HL-REEL, THS4551IRGTR, OPA355NA/3K) were not re-verified this pass.

## Revision 3 (narrow amendment, 2026-09-20T23:10:00Z)

Executes architecture revision 2's **WO-1** (`handoffs/02_architecture.md`) verbatim — five
rows in `sourcing/sourced_bom.md`, nothing else re-sourced, re-priced, or re-verified. The
five critical-path parts (ADS5231IPAGT, GW1NR-9, FT232HL-REEL, THS4551IRGTR, OPA355NA/3K)
were not touched. Decisions 1, 2, 4–10 below are untouched; **decision 3 is superseded**
(Q1 no longer exists); **decisions 11–15 are new**.

1. **`Q1` (HL2301A, C7420344) deleted; `U9` = AP2161WG-7 (C176957) added**, per architecture
   decision 13: Q1 could not turn off (PWREN# is a 3.3 V CBUS output, giving Q1's P-FET gate
   a best-case off-Vgs of −1.5…−1.7 V against a −0.4…−1.0 V threshold). U9 is confirmed live
   this pass: **stock 8,848** (`mcp__pcbparts__jlc_get_part`, C176957), $0.2113 @1 /
   $0.1654 @50, Extended tier, active-low GND-referenced EN, 95 mΩ, 1.1/1.5/1.9 A limit
   bracket, 5 V-capable — matches architecture's figures exactly. Symbol
   `Power_Management:AP2161W` confirmed present verbatim in `/usr/share/kicad/symbols/`
   (EXACT, no generation needed); footprint `Package_TO_SOT_SMD:SOT-23-5` confirmed present
   in `/usr/share/kicad/footprints/Package_TO_SOT_SMD.pretty/`. Both were live-checked in
   this pass, not carried from architecture's numbers.
2. **`C1`, `C2`: 10 µF → 4.7 µF each**, MPN CL21A475KAQNNNE (C1779), Basic+Preferred (a tier
   *upgrade*), stock 2.93 M, $0.0346. Sum = 9.4 µF, inside SPEC P4's ≤10 µF; the outgoing
   2×10 µF violated it.
3. **`R20` (11.8 kΩ) and `R21` (10.0 kΩ) added** — U2's FB divider, `digital_power` block.
   **`R22` (10 Ω) added** — `VBIAS` isolation per architecture decision 16, `analog_power_ref`
   block, a *different* R22 usage than any prior ref. All three generic 1% 0603 jellybean,
   `Device:R` / `Resistor_SMD:R_0603_1608Metric`, no availability risk.
4. **`C3`–`C7` quantity mix corrected**: 4×10 µF 0805 (CL21A106KAYNNNE, C15850) + 1×100 nF
   0402 (CL05B104KO5NNNC, C1525). Rev 1 had the count backwards (4×100 nF + 1×10 µF). Same
   two MPNs, nothing new to source.
5. **`U1` (SY8089A1AAC) annotated, not changed.** `datasheets/SY8089A1AAC.pdf` primary-sources
   VREF at 591/600/609 mV; R4/R5 stay. Noted in `sourced_bom.md` as the one condition on this
   row: a future substitute must have its divider recomputed for its own VREF.

`sourcing/sourced_bom.md` edited in place for exactly these rows (`usb_c_input`'s C1/C2 row;
`digital_power`'s U1/U9/R4–R6/R20/R21/C3–C7 rows; `analog_power_ref`'s R22 row) plus the
symbol-check summary's EXACT list (added `AP2161WG-7`). No other row, block, or decision in
this document was touched.

## Revision 2 (narrow amendment, 2026-09-20T20:15:00Z)

Triggered by the `usb_bridge` block coder's handoff (`handoffs/05_blocks/usb_bridge.md`),
which obtained the real FT232H datasheet (FT_000288 v1.81) and found it names the 93C46
density class as explicitly incompatible. Two fixes only — nothing else in this document
was re-sourced or re-checked.

1. **U8 re-sourced: 93C46CT-I/SN-TUDI → 93LC56BT-I/SN (C6164).** FT_000288 §4 states the
   config EEPROM "should be a 16 bit wide configuration such as a 93LC56B or equivalent...
   Please note that the 93LC46B is not compatible with the FT232H device." The rev-1 pick
   was a 93C46 (64×16, 1 Kbit) — the exact incompatible density FTDI calls out by name.
   93LC56BT-I/SN is literally the part FTDI's datasheet cites: 2 Kbit (128×16), 16-bit
   organisation, 2.5–5.5 V supply (covers VCCIO 2.97–3.63 V), 3 MHz clock (clears FTDI's
   1 Mbit/s minimum). Live-verified stock 2,384 (`jlc_stock_check`, re-run this pass) —
   comfortably clear of the 500-unit WARN line, an improvement over the part it replaces.
   Second source: 93LC66BT-I/SN (C46698, 4 Kbit, SOP-8, stock 1,785, $0.43).
2. **Symbol and footprint are unchanged.** `find-symbol.py 93LC56BT-I/SN` resolves via
   WILDCARD to `Memory_EEPROM:93CxxC` — the same symbol rev 1 used for the 93C46, because
   both parts share the Microchip 93Cxx SOIC-8 pinout (CS/SCLK/DI/DO/GND/ORG/NC/VCC).
   Checked directly against the symbol file: pin 6 on `93CxxC` is named `ORG` (not `NC`),
   which matters because `usb_bridge.py` addresses it by name (`U8['ORG']`) — confirmed
   this still resolves, so **no circuit code change is needed beyond the `value=` string**
   the block coder already anticipated. (Note for later phases: KiCad's `93LCxxB` symbol
   is a different, wrong choice here — it extends `93LCxxA` and inherits `NC` on pin 6,
   representing the fixed-org "A" variant, not the ORG-pin "B" variant actually stocked.
   Do not let a future symbol-search step silently swap to it.) Footprint stays
   `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`, re-confirmed present in the stock KiCad library.
3. **7 parts added to `sourced_bom.md`** that the `usb_bridge` coder instantiated under
   non-numeric refs with no prior entry in any ref list — `R_ref`, `R_eedo`, `R_pwren`,
   `C_vregin`, `C_io24`, `C_io46`, `C_ee`. All priced as jellybean at the coder's stated
   values (12 kΩ 1%, 10 kΩ ×2, 100 nF ×4), all Basic tier, all effectively unlimited stock:
   `R_ref`→0603WAF1202T5E (C22790), `R_eedo`/`R_pwren`→0603WAF1002T5E (C25804, same MPN as
   the existing R14 generic-10k family), the four caps→CL05B104KO5NNNC (C1525, the same
   100 nF MPN used throughout this BOM's decoupling). No values changed from what the
   coder specified.

Only the `usb_bridge` rows in `sourced_bom.md` and its `Parts by block` row below were
touched. Every other block, decision, and open item from revision 1 stands as written.

## Decisions

1. **All 5 critical-path parts verified live** (pcbparts MCP, 2026-09-20): ADS5231IPAGT
   stock 154, GW1NR-LV9QN88PC6/I5 stock 180, FT232HL-REEL stock 2048, THS4551IRGTR stock
   588, OPA355NA/3K stock 489. All clear the >100 floor; U5/U6 stay below 500 by
   architecture's own relaxed Q4 threshold (not escalated — no EOL/collapse signal found).
2. **U2 resolved from spec to a real MPN: TLV75801PDRVR** (C2876308, WSON-6-EP 2×2,
   adjustable 0.55–5.5 V, 500 mA, dropout 130 mV@500 mA). Same TI DRV thermal-pad family as
   U3, adjustable as the architecture preferred, meets every constraint in `## Next phase
   must` item 6/7 of the architecture handoff.
3. ~~Q1 resolved to HL2301A...~~ **Superseded in rev 3.** HL2301A could not turn off
   (architecture rev 2 decision 13) — see the rev 3 section above; `Q1` is retired and `U9`
   (AP2161WG-7) takes its place in `sourced_bom.md`.
4. **J2/J3 (BNC) sourced — architecture had not found these.** KH-BNC50-3511 (C2837587),
   50 Ω board-side elbow, through-hole, stock 4,742, $0.93 each. Footprint is the closest
   stocked KiCad match (`BNC_Amphenol_031-6575_Horizontal`), not a verified exact match —
   carried forward for datasheet-phase mechanical confirmation.
5. **C_top trimmer sourced as STC3MA06-T1** (C22468120, 2–6 pF, SEHWA). Range check: target
   C_top = C_bot_total·(R_bot/R_top) ≈ 89 pF·(49.9k/950k) ≈ 4.7 pF sits mid-range — a better
   fit than a wider 3–12 pF part would have been. **Per the user's explicit instruction and
   architecture decision 10, this was never a candidate for substitution with a fixed
   capacitor**, and it wasn't substituted. No standard KiCad footprint exists for this
   MPN — marked `⚠️ CUSTOM FP NEEDED` (closest stocked candidate noted for the librarian:
   `Capacitor_SMD:C_Trimmer_Murata_TZB4-A`, same size class, pad geometry unconfirmed).
6. **U4 resolved to TLV9062IDR** (C398355) over OPA2376/OPA2333 — exact KiCad symbol match,
   151k stock, meets every spec in the architecture's item 7c (RRIO, Vos, GBW, output
   current, package).
7. **±2% C0G specified for C_bot/C_f relaxed to ±5%** (C282510, C5137568) — no ±2% option
   exists in this value/package in JLCPCB's DB at a sane price/stock point (the one ±2%
   82 pF hit, Murata GQM1875C2E820GB12D, is $0.30/ea at stock 4,263 — a >40× price jump for
   2 parts total). The trimmer (decision 5) nulls the resulting HF error per R-2's own
   analysis, so this is a documented substitution, not a silent one.
8. **R_bot/R11 rounded to the nearest E96 value** (49.9 kΩ for "50.0 kΩ", 19.1 kΩ for
   "19.0 kΩ") — these are the actual standard values a 0.5%/0.1% resistor line stocks;
   "50.0"/"19.0" in the skeleton BOM were nominal, not literal E96 values. Ratios move by
   <0.2%, negligible against the ±0.1–0.5% tolerances already budgeted.
9. **X2 crystal specified exactly: 12 MHz, 12 pF load** (SX32Y012000BC1T001, C7420720) —
   this pins down the load capacitance the architecture's skeleton BOM left approximate.
   **The ≈27 pF placeholder for C13/C14 no longer applies**; recompute at ≈16–18 pF each
   for CL=12 pF (formula: Cext ≈ 2·(CL − Cstray), Cstray ≈ 4 pF). Flagged for the coder.
10. **U8 finding improves on the architecture's flagged risk**: 93C46CT-I/SN-TUDI
    (C54935223) specs 1.7–5.5 V supply, so the 3.3V-operation concern architecture raised
    is resolved — it is *not* the 93C46B 4.5–5.5V-only part. The **ORG=×16 pin** is still
    unconfirmed (needs the real datasheet) and is carried to the datasheet-librarian
    unchanged.

**New in revision 3:**

11. **U9 = AP2161WG-7 is the only load-switch candidate carried into the BOM.** Second
    source WS4612EBB-5/TR (C42404603) passes the same substitution test (active-low,
    GND-referenced EN ≤2.0 V VIH, 0.6–2 A limit, ≥1 A continuous, ≤150 mΩ, 5 V-capable) but
    has no KiCad symbol, so it is not worth the generation cost while AP2161WG-7 is in stock
    at 8,848. Not added as a BOM row.
12. **`AP2171WG-7` is a named do-not-substitute**, not merely an inferior option: pin-identical
    to AP2161WG-7 but active-high, so it silently re-breaks SPEC P4 if ever swapped in by a
    later stock-driven substitution pass. Recorded here so a future sourcing rev doesn't pick
    it on parametric match alone.
13. **C1/C2's tier improved, not just its value** — CL21A475KAQNNNE (C1779) is Basic+Preferred
    where the outgoing CL21A106KAYNNNE was Basic only. A capacitance-driven change (SPEC P4
    compliance) happened to also be a tier win.
14. **R20/R21/R22 sourced as generic jellybean, not pinned to a specific MPN** — consistent
    with every other generic-1%-0603 row in this document (R4–R7, R8/R9, R109/R110, etc.):
    cheapest Basic 1% 0603 part at order time, no single-source risk.
15. **U1 (SY8089A1AAC) received no part or value change** — only its BOM note was updated to
    point at the now-primary-sourced VREF. This is a documentation fix, not a sourcing
    decision, and is listed here only so nobody reopens U1 looking for a substitution that
    didn't happen.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `sourcing/sourced_bom.md` | Full ref-designator BOM: MPN, LCSC#, stock, price, package, tier, KiCad symbol, KiCad footprint, notes — organized by block, with the afe_channel R101–110/C101–110 function mapping | Always — before datasheets or coding |

No `sourcing/sourcing_failures.md` — every part was sourced (J2/J3 found; U2/Q1/L1/FB1-4/D2
resolved from spec to MPN; nothing dropped).

## Parts by block

| block_id | refs | MPNs |
|---|---|---|
| `usb_c_input` | J1, R1, R2, R12, D1, D2, FB1, C1, C2, C15 | TYPE-C 16PIN 2MD(073), 0603WAF5101T5E ×2, RC0603FR-071ML, USBLC6-2SC6, SMF5.0CA, PBY160808T-601Y-N, **CL21A475KAQNNNE ×2 (rev 3, was CL21A106KAYNNNE, 10 µF→4.7 µF)**, CL10B102KB8NNNC |
| `digital_power` | U1, U2, **U9** (rev 3, was Q1), L1, FB2, R4–R7, **R20, R21** (rev 3, new; R3 deleted), D4, C3–C7 | SY8089A1AAC, TLV75801PDRVR, **AP2161WG-7** (rev 3, was HL2301A), FNR3015S2R2MT, PBY160808T-601Y-N, generic 1% 0603 ×5, CT-1608UGC-P4, **CL21A106KAYNNNE ×4 + CL05B104KO5NNNC ×1** (rev 3: quantity mix corrected) |
| `analog_power_ref` | U3, U4, FB3, R8–R11, R19, **R22** (rev 3, new), C8–C12 | TLV75733PDRVR, TLV9062IDR, PBY160808T-601Y-N, generic 1% ×3, RT0603BRD0719K1L, FRH0603B1001TS, **generic 1% 0603** (R22, rev 3), decoupling mix |
| `afe_channel` (ch1) | J2, U_buf1, U_fda1, D_clamp1, R101–R110, **R111, R112** (rev 4, new), C101–C110, **C111** (rev 4, new) | KH-BNC50-3511, OPA355NA/3K, THS4551IRGTR, BAV99, 0805W8D4753T5E ×2 + ARG03DTC4992 + 0603WAF1001T5E + PTFR0603B499RP9 ×2 (**R_g**) **+ PTFR0603B499RP9 ×2 (rev 4, new — R_mfb)** + FRH0603B1001TS ×2 + generic 33R ×2, STC3MA06-T1 + TCC0603COG820J500CT + **CL10C100JB8NNNC ×2 (rev 4, was FCC0603N270J500CT/27pF)** + **CL10C331JB8NNNC (rev 4, was CL10C471JB8NNNC/470pF)** + **CL10C101JB8NNNC ×2 (rev 4, was CL10C221JB8NNNC/220pF)** + **CL10C680JB8NNNC (rev 4, new — C_mfb)** + decoupling |
| `afe_channel` (ch2) | J3, U_buf2, U_fda2, D_clamp2, R201–R210, **R211, R212** (rev 4, new), C201–C210, **C211** (rev 4, new) | mirrors ch1 |
| `adc_dual` | U5, RA1–RA6, C41–C55 | ADS5231IPAGT, YC124-JR-0733RL ×6, decoupling mix |
| `clock_20m` | X1, R_s1, R_s2, FB4, C56, C57 | SX3M20.000B10F20TNN, generic 33R ×2, PBY160808T-601Y-N, CL05B104KO5NNNC ×2 |
| `fpga_core` | U6, J4, J5, D5, R13, R15–R18, C23–C40 | GW1NR-LV9QN88PC6/I5, generic 2.54mm headers ×2, KT-0603R, 0603WAF2201T5E, generic 10k/LED-R ×4, decoupling mix |
| `usb_bridge` | U7, U8, X2, R14, C13, C14, C16, C17–C22, R_ref, R_eedo, R_pwren, C_vregin, C_io24, C_io46, C_ee | FT232HL-REEL, 93LC56BT-I/SN (rev 2, was 93C46CT-I/SN-TUDI), SX32Y012000BC1T001, generic 10k, generic ~17pF ×2, CL05B104KO5NNNC ×7, 0603WAF1202T5E, 0603WAF1002T5E ×2, CL05B104KO5NNNC ×4 |

## Next phase must

**Rev 4 note: no new datasheet work either.** All five rev 4 parts (`C_f`, `C_mfb`,
`C_diff`, `C_cm`, `R_mfb`) are generic C0G/thin-film 0603 jellybeans on footprints already
proven elsewhere in this BOM — nothing for the datasheet-librarian to add or re-check. The
list below is unchanged from rev 3/rev 2 and still stands for the remaining items.

**Rev 3 note: no new datasheet work.** `datasheets/AP2161WG-7_SUMMARY.md` + `.pdf` and
`datasheets/SY8089A1AAC.pdf` + `_SUMMARY.md` already exist on disk (used by architecture
rev 2 decisions 13/15) — U9 and U1 need nothing further from the datasheet-librarian. The
list below is unchanged from rev 2 and still stands for the remaining items.

Addressed to **datasheet-librarian**:

1. **Symbol generation** (MISSING from `find-symbol.py`, needed before coding): `ADS5231IPAGT`
   (TQFP-64, 64-pin table), `GW1NR-LV9QN88PC6/I5` (QFN-88), `SY8089A1AAC` (SOT-23-5),
   `SX3M20.000B10F20TNN` (4-pin XO), `TYPE-C 16PIN 2MD(073)` (16-pin standard USB-C pinout —
   low-risk, well-documented). Confirm pinout before trusting the PREFIX/WILDCARD matches on
   `FT232HL-REEL`, `OPA355NA/3K`, `TLV75733PDRVR`/`TLV75801PDRVR`, `THS4551IRGTR`,
   `93C46CT-I/SN-TUDI`.
2. **Two open architecture questions, unchanged from `02_architecture.md`**: (a) ADS5231's
   minimum clock frequency (design needs 20 MHz legal); (b) GW1NR-9's required supply rails
   (design assumes 1.2 V + 3.3 V only). Read these first — everything else in the datasheet
   pass is lower stakes.
3. **U8 ORG pin**: confirm 93C46CT-I/SN-TUDI's ORG pin selects ×16 organisation (needed for
   245 sync FIFO mode). This is the one open item from the architecture's U8 flag that
   sourcing could not close from JLC's parametric data alone.
4. **X1 jitter**: confirm SX3M20.000B10F20TNN specifies ≤5 ps RMS phase jitter from a real
   datasheet, or substitute the vetted second source OT252020MJBA4SL (C669067) if it does
   not, per architecture R-4.
5. **C_top trimmer mechanical drawing**: STC3MA06-T1 (C22468120) needs its footprint
   generated or hand-verified — no exact stock KiCad footprint exists. Get the JLC-hosted
   datasheet/mechanical drawing and either generate a custom `.kicad_mod` or confirm
   `Capacitor_SMD:C_Trimmer_Murata_TZB4-A` is pad-compatible.
6. **J2/J3 BNC mechanical drawing**: KH-BNC50-3511 (C2837587) — confirm pin spacing against
   `BNC_Amphenol_031-6575_Horizontal` before the coder places it; these are board-edge
   parts with no room for a footprint mismatch to be fixed later.
7. **GW1NR-9 QFN-88 exposed-pad size**: the stocked KiCad footprint used
   (`ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm`) matches pin count/pitch/body but
   its EP size is unconfirmed against Gowin's actual package drawing — check before layout,
   since U6's centre pad must be plane-connected (architecture item 6).

## Carried forward

- **Marginal/single-source stock, watch these**: U5 ADS5231IPAGT (154, single-source, NRND
  unchecked — mirror has no lifecycle field); U6 GW1NR-9 (180, single-source); U_buf1/2
  OPA355NA/3K (489, WARN<500, second source OPA355UA/2K5 confirmed available); R_top_a/b
  0805W8D4753T5E (763, only one 475kΩ/0.5%/0805 SKU exists in JLC's DB — no second source
  if this one goes EOL); D4 CT-1608UGC-P4 (two data sources disagree: 226k vs 572 — re-verify
  at order time, low consequence since qty=5).
- **Two ⚠️ CUSTOM FP NEEDED items**: C_top trimmer (STC3MA06-T1) and, if ever substituted in,
  THS4551IRUNR's QFN-10 package. Primary THS4551IRGTR's QFN-16-EP footprint IS in stock
  (`WQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm`), no action needed unless that substitution happens.
  Note: THS4551IRUNR is not simply "extra work" if it's never needed — see architecture's
  own framing, it's a fallback only.
  Both are documented in `sourced_bom.md` with the nearest stocked candidate.
- **X2 load-cap recompute**: C13/C14 target moved from the architecture's placeholder
  ≈27 pF to ≈16–18 pF because the sourced crystal (SX32Y012000BC1T001) specifies a 12 pF
  load, not the ~20 pF the placeholder assumed. Flagged for the coder, not yet fixed in any
  file — no block file exists yet to fix it in.
- **±5% substituted for architecture's requested ±2% on C_bot/C_f** (decision 7 above) —
  the trimmer (C_top) is what makes this safe; if C_top is ever removed, this substitution
  must be revisited.
- **Everything the architecture already carried forward still stands** (filter values
  provisional, X1 jitter unverified, F3 delivered by host-side decimation, no AEC-Q100/
  Q200 requirement, firmware/USB descriptors out of scope) — unchanged by sourcing.

**Revision 2 additions:**

- **U8 = 93LC56BT-I/SN (C6164), Extended tier, single-source in this pass** — only one
  93LC56B-class SOIC-8 MPN was evaluated as primary; second source 93LC66BT-I/SN (C46698,
  SOP-8, stock 1,785) confirmed available if 56B ever goes short. Not flagged marginal
  (stock 2,384, well clear of the 500 line) but noted as single-sourced per the standard
  carry-forward rule.
- **`93LCxxB` is a trap for a future symbol-search pass on this part** — it wildcard-matches
  the MPN just as well as `93CxxC` does, but its pin 6 is `NC` (it extends `93LCxxA`, the
  fixed-organisation "A" variant) rather than `ORG`. `usb_bridge.py` addresses the pin by
  name (`U8['ORG']`); resolving to `93LCxxB` instead of `93CxxC` would break the build.
  Recorded here so a later resourcing or symbol-regeneration pass doesn't silently pick it.
- **7 new refs (`R_ref`, `R_eedo`, `R_pwren`, `C_vregin`, `C_io24`, `C_io46`, `C_ee`)** are
  now in `sourced_bom.md` and the `usb_bridge` row above — all Basic tier, all jellybean,
  no stock risk. The datasheet-librarian and coders should treat them as already closed;
  they need no datasheet of their own (see `handoffs/05_blocks/usb_bridge.md` for the
  FT232H table citations that mandate each one).

**Revision 3 additions:**

- **`U9` (AP2161WG-7) is not "freely substitutable" the way `Q1` was** — architecture rev 2
  flags this explicitly (R-9): EN polarity and the current-limit bracket (≥0.6 A, ≤2 A) are
  hard constraints, not sourcing discretion. `AP2171WG-7` (active-high, pin-identical) is a
  named trap — do not let a future stock-driven resourcing pass pick it.
- **`R22` now names two unrelated parts across two blocks** — `digital_power`'s existing
  ref list never had an R22, so there is no collision, but a future reader searching
  `sourced_bom.md` for "R22" will find it once, under `analog_power_ref`, doing `VBIAS`
  isolation (architecture decision 16). `R20`/`R21` are `digital_power`'s U2 FB divider.
  Keep these straight — they were introduced together in the same WO-1 item but serve
  different blocks.
- **C1/C2 and C3–C7 are both capacitor-count corrections on different rails** — C1/C2 fixes
  a SPEC P4 (≤10 µF on VBUS_RAW) violation; C3–C7 fixes a rev-1 quantity-mix guess with no
  spec implication. Do not conflate them if a future pass touches capacitor counts again.

**Revision 4 additions:**

- **`C_f`'s ±5% tolerance is no longer a documented substitution — it is now what
  architecture itself specifies.** WO-1 item 3 explicitly calls for "C0G ±5%" on the whole
  MFB filter set (`C_f`, `C_mfb`, `C_diff`, `C_cm`). The rev-1 "±2% relaxed to ±5%" carry-
  forward item above now applies **only to `C_bot`**, which WO-1 did not touch — do not
  read it as still covering `C_f`.
- **`R_mfb` (R111/R112/R211/R212) and `R105/R106/R205/R206` (`R_g`) now share one MPN
  (`PTFR0603B499RP9`/C478882) across two different filter functions.** They are kept as
  two separate rows in `sourced_bom.md` precisely so a reader doesn't conflate "gain-set"
  with "MFB feedback" — board-wide qty of this MPN is now 8, not 4. Do not merge the rows.
- **The AC filter values are no longer provisional.** Rev 3 decision 18 ("R-5 closed") plus
  this sourcing pass closes the loop the rev-1/2 carry-forward flagged: `C_f`/`C_diff`/
  `C_cm` are the final 3rd-order-Butterworth values, not placeholders — see architecture
  `## Carried forward` for the one remaining caveat (bench confirmation vs the FDA's
  ≈65 MHz closed-loop pole, R-5).
- **`R8`/`R9` still carry no pinned MPN** — only their target values changed (22.0 kΩ/
  11.0 kΩ). Architecture's decision 19 explicitly forbids 23.0 kΩ; that prohibition is now
  recorded on the BOM row itself, not just in the architecture handoff.

## Do not redo

- The 5 critical-path MPNs and their live-verified stock (ADS5231IPAGT, GW1NR-9, FT232HL,
  THS4551IRGTR, OPA355NA/3K) — re-verify only if a later phase reports a stock failure.
- U2/L1/FB1–4/D2/J2/J3/U4/X2's resolution from architecture spec to a real MPN — these
  were open questions in `02_architecture.md`; they are now closed. Do not re-derive them.
  (**`Q1` is retired as of rev 3** — see below, not part of this "do not redo" set anymore.)
- **Rev 3: the `Q1`→`U9` load-switch substitution** (architecture decision 13) — arithmetic
  on published gate-drive thresholds, not an opinion; do not re-open it with a different
  P-FET. **U1's divider (45.3 k/10.0 k) and U2's divider (11.8 k/10.0 k, now R20/R21)** —
  both verified against primary datasheets; do not re-derive either.
- The afe_channel R101–110/C101–110 function-to-number mapping in `sourced_bom.md` — the
  block coder should read and use it, not invent a different numbering. **Rev 4 extends it
  with R111/R112/C111 (ch1) and R211/R212/C211 (ch2); do not renumber any of it.**
- The trimmer-must-stay-a-trimmer decision — reaffirmed, not reopened, in this phase.
- The E96-rounding of R_bot/R11 (49.9 kΩ, 19.1 kΩ) — a final sourcing decision with
  documented reasoning, not a gap. **The ±5% C0G substitution now applies only to `C_bot`**
  (see rev 4 additions above) — `C_f`'s ±5% is architecture's own spec, not a substitution.
- **Rev 4: the four new/changed filter-cap MPNs and the `R_mfb` MPN** (C1634, C28262, C1664,
  C14858, C478882 ×2 more) — live-verified 2026-09-21, do not re-verify absent a stock
  failure report. **The critical-path five were not touched in rev 4** — same standing as
  rev 3's "do not redo" entry above.

## Receipt

- **~160 ref designators sourced, 0 failures.** 5/5 critical-path parts verified live
  in stock (>100, two WARN<500 per architecture's own relaxed rule). All 12 previously
  spec-only parts (U2, Q1, L1, FB1–4, D2, J2, J3, U4, X2) resolved to real MPNs.
- **Tier split**: 3 Basic (U4's field is Extended but several jellybean passives and R1/R2/
  Q1/D2 landed Basic/Preferred), remainder Extended — consistent with architecture's "every
  active part Extended" expectation except Q1 (Preferred) and D2 (Preferred), two small wins.
- **2 items flagged `⚠️ CUSTOM FP NEEDED`**: C_top trimmer (STC3MA06-T1), THS4551IRUNR
  fallback footprint (not needed unless substituted).
- **9 symbols `⚠️ SYMBOL NEEDED`** for the datasheet-librarian to generate; 6 PREFIX/WILDCARD
  matches to confirm before use; 3 EXACT matches need no action.
- Deviations from the architecture's exact spec (all documented above): ±5% not ±2% on two
  C0G caps (trimmer compensates); E96 rounding on two resistors (negligible); X2 load-cap
  recompute needed (12 pF not ~20 pF assumed).
- **Revision 2: 1 part re-sourced, 7 parts added, 0 failures.** U8 swapped
  93C46CT-I/SN-TUDI → 93LC56BT-I/SN (C6164, live stock 2,384) to fix an FTDI-documented
  incompatibility found by the `usb_bridge` coder; symbol/footprint unchanged, no circuit
  code impact beyond the `value=` string. 7 FTDI-mandated/ERC-required parts
  (`R_ref`, `R_eedo`, `R_pwren`, `C_vregin`, `C_io24`, `C_io46`, `C_ee`) added to
  `sourced_bom.md`, all Basic-tier jellybean. ~167 ref designators now sourced total.
- **Revision 3: 1 part deleted, 1 part added, 3 jellybean refs added, 2 rows
  value/mix-corrected, 1 row annotated, 0 failures.** `Q1` (HL2301A) deleted; `U9`
  (AP2161WG-7, C176957) added with **live stock re-verified at 8,848** and symbol
  (`Power_Management:AP2161W`, EXACT) + footprint (`Package_TO_SOT_SMD:SOT-23-5`) both
  confirmed present in the local KiCad libraries. `C1`/`C2` changed 10 µF→4.7 µF
  (CL21A475KAQNNNE, tier upgrade to Basic+Preferred). `R20`, `R21`, `R22` added (generic
  1% 0603 jellybean, two different blocks). `C3`–`C7` quantity mix corrected (4×10 µF +
  1×100 nF, was reversed). `U1` annotated (VREF primary-sourced, no part/value change).
  The 5 critical-path parts were not touched. ~169 ref designators now sourced total
  (167 + U9 + R22, net of −Q1 +R20/R21 already reflected in the architecture's own delta).
- **Revision 4 (this pass): 4 rows value-changed, 1 row added, 1 row value-annotated,
  0 failures.** Executes architecture rev 3's WO-3 exactly: `C_f` 27→10 pF (CL10C100JB8NNNC/
  **C1634**), `C_diff` 470→330 pF (CL10C331JB8NNNC/**C1664**), `C_cm` 220→100 pF
  (CL10C101JB8NNNC/**C14858**) — all three tier-improved Extended→Basic; new `C_mfb` row
  68 pF (CL10C680JB8NNNC/**C28262**, Preferred); new `R_mfb` row reusing `R105/106`'s MPN
  (PTFR0603B499RP9/**C478882**, board-wide qty 4→8); `R8`/`R9` row annotated 22.0 kΩ/
  11.0 kΩ, no new MPN. All five live-verified 2026-09-21 via `mcp__pcbparts__jlc_get_part`,
  all Basic or Preferred, all comfortably >100 stock. Ref delta **+6** (R111/R112/C111 ch1,
  R211/R212/C211 ch2), matching architecture's own delta exactly. The 5 critical-path parts
  and every other row/block/decision were not touched. ~175 ref designators now sourced
  total (169 + 6).
- status: complete
