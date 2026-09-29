---
phase: 03_sourcing
agent: part-sourcer
circuit: dual_adc_usb
written: 2026-09-10T20:10:00Z
status: complete
revision: 1
next_phase: 04_datasheets
---

# Phase 3 handoff — Sourcing

## Decisions
- **U4 (VD_1V2 LDO): switched to TLV75512PDBVR** (LCSC C2877864, 3,636 in stock). The
  architect's recommended AP2112K-1.2TRG1 (C460310) has dropped to 77–80 units — FAIL (<100).
  Used the architect's own vetted second source (`02_architecture.md` §4) rather than picking
  a new part, so no re-escalation is needed.
- **U3 (VD_3V3 LDO): chose the genuine TI TLV1117LV33DCYR (C15578, 842 stock, $0.335)** over a
  cheaper JSMSEMI clone of the same MPN (C48937499, 166,989 stock, $0.11). The clone's own
  listed dropout is 1.2V@1A, which fails the architect's stated reason for rejecting AMS1117
  (dropout ≤0.6V to clear the 4.4V VBUS corner). The genuine part's dropout is 455mV@1A —
  matches the architecture's numbers. Do not let a later pass "optimize" this back to the
  cheap clone; it would silently reopen a closed HARD-adjacent risk.
- **FB1 (VBUS ferrite): substituted BLM21PG221SN1D** (220Ω@100MHz, 2A, 45mΩ DCR) for the
  skeleton's illustrative "600Ω@100MHz 0805" example. The 600Ω-class bead in stock
  (BLM21PG601SN1D) has 140mΩ DCR, which fails FB1's own ≤0.1Ω spec. FB2–FB8 (which only need
  600Ω@100MHz, no DCR spec) keep BLM21PG601SN1D.
- **BAV199 (D2/D3): left as `⚠️ SYMBOL NEEDED`, did not accept either candidate symbol.**
  `Diode:BAV19` (single diode) is wrong per the architecture's own flag. `Diode:BAV99`
  (common-cathode dual) is also wrong — BAV199 is a series-connected pair, a different internal
  topology from BAV99 despite the similar part number and identical SOT-23 pinout count.
  Datasheet-librarian must generate a real BAV199 symbol from the datasheet pin table, not
  reuse either lookalike.
- **U15 (GW1NR-9) footprint flagged, not accepted outright.** The only QFN-88/10×10mm/0.4mm-pitch
  footprint in the KiCad library is third-party (ArtInChip), with a 6.74×6.74mm exposed pad.
  Gowin's own QN88P mechanical drawing (UG803) was not cross-checked against that EP size —
  do this in the datasheet phase before it reaches layout. Marked `⚠️ CUSTOM FP NEEDED (verify
  first)` rather than a clean pass, even though a same-name-pattern footprint technically
  exists, because a wrong EP size on a 468kbit-BSRAM, single-source, critical-path FPGA is the
  single costliest place for this to go unnoticed.
- **Y1 crystal selected: X322512MSB4SI** (12MHz, SMD3225-4P, CL=20pF, Basic tier, C9002). This
  resolves the skeleton BOM's open item — C65/C66 load caps are now fixed at 22pF C0G (nearest
  standard value to CL=20pF; the 2pF offset is within normal crystal-loading tolerance).
- **VC1/VC2 trimmer**: kept STC3MA06-T1 (architect's pick, 2–6pF/100V, only in-spec option
  found) but the footprint match (`C_Trimmer_Sprague-Goodman_SGC3`) is a generic trimmer body
  substitution, not a verified match to SEHWA's 4.5×3.2mm mechanical drawing — flagged below.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `sourcing/sourced_bom.md` | Every ref designator: MPN, LCSC#, stock, price, package, tier, KiCad symbol, KiCad footprint, notes | Always — this is the BOM the coder and datasheet-librarian use |

No `sourcing/sourcing_failures.md` was written — nothing failed sourcing outright (the one
stock failure, AP2112K-1.2, had a pre-vetted substitute and did not need escalation).

## Next phase must
1. **Generate KiCad symbols** for the parts marked `⚠️ SYMBOL NEEDED` in `sourced_bom.md`:
   SY6280AAC (SOT-23-5, Silergy datasheet p.1 for pinout, p.6 for ISET formula),
   TPS7A2033PDBVR (SOT-23-5, TI SBVS221 — do not reuse the X2SON-5 `TPS7A20xxxDQN` symbol
   without confirming pin order matches the DBV package), BAV199 (SOT-23, series-pair pinout —
   **not** BAV19 or BAV99's topology), OPA354AIDBVR (SOT-23-5 — verify against TI's standard
   5-pin SOT-23 op-amp pinout before treating `OPA356xxDBV` as a stand-in), ADS5231IPAGT
   (TQFP-64, TI SBAS295A), GW1NR-LV9QN88PC6/I5 (QFN-88, Gowin UG803/DS117).
2. **Resolve `⚠️ CUSTOM FP NEEDED` for U15 (GW1NR-9) first**, before any other datasheet work —
   pull UG803's QN88P mechanical drawing and confirm the 6.74×6.74mm exposed pad on
   `ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` matches, or generate a custom footprint.
3. **Resolve LM27762 FB-divider values (R6–R9)** from TI SNVSAF7C's ±2.50V application formula
   — this was already flagged `[VERIFY]` by the architect and is still open; part-sourcer left
   it unpriced (generic 0402 1% Basic-tier family, exact resistance TBD).
4. **Resolve SY6280AAC ISET (R3)** from the datasheet's current-limit formula for ≈0.8A, per
   the architect's original note.
5. **Confirm X1 jitter** (≤5ps rms) on the SX3M20.000B10F20TNN datasheet — still unverified,
   carried from architecture. Note this part has no EasyEDA footprint on file at JLC; the
   generic 3225 4-pin oscillator footprint used here should be spot-checked against its
   datasheet's land pattern.
6. **Confirm VC1/VC2 (STC3MA06-T1) footprint** against SEHWA's mechanical drawing (4.5×3.2mm
   body) — the KiCad footprint used is a different manufacturer's trimmer body, not verified
   pad-for-pad.
7. Coders (`04` is datasheets, but downstream): every MPN, LCSC#, and footprint string in
   `sourced_bom.md` is final for parts **not** flagged above — use them verbatim.

## Carried forward
- **U15 GW1NR-9 footprint (EP size), unresolved.** See Decisions and Next-phase-must #2 — this
  is the highest-risk open item in this handoff.
- **⚠️ SYMBOL NEEDED (6 parts):** SY6280AAC, TPS7A2033PDBVR, BAV199, OPA354AIDBVR, ADS5231IPAGT,
  GW1NR-LV9QN88PC6/I5. All go to the datasheet-librarian as generation work, not back to the
  architect.
- **R6–R9 (LM27762 FB dividers) and R3 (SY6280 ISET): values not yet computed**, both were
  already `[VERIFY]` items from architecture. Not priced/LCSC'd until the datasheet phase
  supplies the resistance.
- **Marginal stock (WARN band, <500 units but >100):** none below 500 except the two
  already-flagged single-source critical-path parts: ADS5231IPAGT (160 units) and
  GW1NR-LV9QN88PC6/I5 (182 units) — both `## Do not redo` below, buy full 10-board qty now
  per the architecture's instruction. J2/J3 BNC-KWE-6 (615 units) and U8/U10 OPA354AIDBVR (847
  units) are both just above the 500 line and worth a stock recheck before placing the order,
  since they were higher at architecture time (BNC was not measured before; OPA354 was 3,147).
- **Single-source parts:** ADS5231IPAGT and GW1NR-LV9QN88PC6/I5 (unchanged from architecture).
- **Extended-tier count grew slightly:** ~27 unique Extended MPNs (architecture estimated ~25),
  ≈$8/board loading fee at qty 10 — driven by the genuine-TI TLV1117LV33DCYR swap and several
  precision passives (453kΩ/200V, 0.1% resistors, C0G≥100V caps) that only exist Extended-tier
  at JLCPCB.
- **C34/C35/C44/C45 (Cf 22pF C0G 100V) has only one JLC listing** (GRM1555C2A220JA01D, C710855,
  1,877 units) — low diversity but a standard Murata MLCC, easily re-sourced if it ever runs out.

## Do not redo
- Every MPN/LCSC#/footprint in `sourced_bom.md` not marked `⚠️` is confirmed — use verbatim.
- ADC (ADS5231IPAGT), FPGA (GW1NR-LV9QN88PC6/I5), FT232HL-REEL, THS4521IDGKR×2: all **CP**,
  confirmed in stock, unchanged from the architect's picks.
- Y1 crystal is now fixed: X322512MSB4SI, CL=20pF, C65/C66 = 22pF C0G.
- U4 is now TLV75512PDBVR (not AP2112K-1.2TRG1) — this is a final decision, not open for
  re-litigation absent a new stock check showing AP2112K-1.2 recovered.
- All architecture-level topology, net names, and ref designators — unchanged, per `02`'s
  own `## Do not redo`.

## Parts by block

| block_id | refs | MPNs |
|---|---|---|
| `usb_power_in` | J1, U1, U2, D1, FB1, R1, R2, R3, R4, C1, C2, C3, C4 | TYPE-C-31-M-12, USBLC6-2SC6, SY6280AAC, SMF5.0A, BLM21PG221SN1D, 0603WAF5101T5E, (R3 TBD), 0603WAF1004T5E, CL10A475KO8NNNC, CL05B104KB54PNC, CL21A106KAYNNNE, CC0603KRX7R0BB472 |
| `power_rails` | U3, U4, U5, U6, LED1, R5, C5–C13, TP1–TP6 | TLV1117LV33DCYR(TI), TLV75512PDBVR, TLV75518PDBVR, TPS7A2033PDBVR, CT-1608UGC-P4, 0603WAF1001T5E, CL21A106KAYNNNE, CL05B104KB54PNC, CL05A105KA5NQNC, (TP: no MPN) |
| `bipolar_supply` | U7, R6–R9, C14–C21, FB2–FB4, TP7, TP8 | LM27762DSSR, (R6–R9 TBD), CL10A106MA8NRNC, CL05B104KB54PNC, CL05A105KA5NQNC, 0603B225K160NT, BLM21PG601SN1D |
| `analog_front_end` | J2, J3, U8, U9, U10, U11, D2, D3, VC1, VC2, R10–R29, C30–C38, C40–C48 | BNC-KWE-6, OPA354AIDBVR, THS4521IDGKR, BAV199, STC3MA06-T1, FRC1206F4533TS, RT0603BRD07100KL, 0603WAF1001T5E, PTFR0603B1K10P9, FRH0603B1001TS, 0402WGF499JTCE, GCM1885C2A150JA16D, GRM1885C1H161JA01D, CL05B104KB54PNC, GRM1555C2A220JA01D |
| `adc` | U12, R50–R56, RN1–RN7, C50–C62, FB5, FB6 | ADS5231IPAGT, FRC0603F5622TS, FRC0402F2R00TS, 0402WGF1002TCE, 4D03WGJ0330T5E, CL05B104KB54PNC, CL05A105KA5NQNC, CL10A106MA8NRNC, BLM21PG601SN1D |
| `sample_clock` | X1, R57, R58, C63, C64, FB7, TP9 | X322512MSB4SI, 0402WGF330JTCE, CL05B104KB54PNC, CL05A105KA5NQNC, BLM21PG601SN1D |
| `usb_bridge` | U13, U14, Y1, R60–R67, C65–C79, FB8 | FT232HL-REEL, 93LC56BT-I/OT, X322512MSB4SI, 0402WGF2201TCE, 0402WGF1002TCE, 0402WGF1202TCE, 0402WGF330JTCE, GRM1555C2A220JA01D, CL05B104KB54PNC, CL10A475KO8NNNC, BLM21PG601SN1D |
| `fpga_core` | U15, J4, R70–R74, C80–C95, TP10 | GW1NR-LV9QN88PC6/I5, (J4 generic 1×7 header, C492406), 0402WGF4701TCE, 0402WGF1002TCE, CL05B104KB54PNC, CL10A106MA8NRNC, CL10A475KO8NNNC |
| `io_expansion` | U16, U17, LED2, LED3, R80–R85, C96, C97, J5 | SN74LV4T125PWR, SN74LV1T34DCKR, CT-1608UGC-P4, 0402WGF1001TCE, 0402WGF1000TCE, 0402WGF1003TCE, CL05B104KB54PNC, (J5 generic 1×6 header, C37208) |

## Receipt
Sourcing complete, revision 1. 159 ref designators across 9 blocks, all sourced (0 failures,
no `sourcing_failures.md`). Tier split: ~1 Preferred, ~27 Extended, remainder Basic. 6 parts
carry `⚠️ SYMBOL NEEDED`; 1 part (U15 GW1NR-9) carries `⚠️ CUSTOM FP NEEDED (verify first)`.
One stock failure caught and resolved (U4, AP2112K-1.2 → TLV75512PDBVR via architect's own
second source). One quiet spec violation caught and avoided (U3 counterfeit-dropout clone).
status: complete.
