---
phase: 03_sourcing
agent: part-sourcer
circuit: dual_adc_usb
written: 2026-09-26T00:00:00Z
status: complete
revision: 4
next_phase: 04_datasheets
---

# Phase 3 handoff — Sourcing (revision 4)

Revision 4 reconciles `sourced_bom.md`/`.csv` against the block coders' actual code in
`circuits/dual_adc_usb/*.py`, per a block-coder escalation that the BOM's symbol/footprint/
note cells for J1, U2, U6, U7, J2/J3, D101/D201, U8, X1, U9, and Y1 disagreed with the code.
Every cell named was checked against the coder's `Part(...)` call and found to be a **BOM
error** (a stale `⚠️ SYMBOL NEEDED`/`⚠️ CUSTOM FP NEEDED` flag left over from before the
datasheet-librarian generated the part, or a wrong symbol/footprint) — the code's
symbol/footprint strings are correct and are treated as authoritative here. No MPN, stock,
price, or tier changed; no part was re-sourced. Rev 3's FT232H VPHY/VPLL content is
unchanged. All rev-1/rev-2/rev-3 content below is otherwise unchanged.

## Decisions — REV 4 (BOM-vs-code reconciliation)

- **J1 symbol corrected to `Connector:USB_C_Receptacle_USB2.0_16P`** (was
  `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`, a footprint string, not a valid
  symbol library:name — that was always a BOM error). `usb_power_in.py` uses
  `Part('Connector', 'USB_C_Receptacle_USB2.0_16P', ...)` with an explicit pin-by-number map
  (A4/A9/B4/B9 VBUS, A1/A12/B1/B12/S1 GND, A5 CC1, B5 CC2, A6/B6 DP, A7/B7 DN, A8/B8 NC).
  Footprint (`Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`) is unchanged and correct.
- **U2 symbol resolved to `dual_adc_usb:TPS22919DCKR`** (was `⚠️ SYMBOL NEEDED`). The
  datasheet-librarian generated this symbol and `usb_power_in.py` already uses it — the BOM
  flag was simply never cleared after generation.
- **U6 symbol resolved to `dual_adc_usb:TPS7A2033PDBVR`** (was `⚠️ SYMBOL NEEDED`), same
  situation — `power_analog.py` already uses the generated symbol.
- **U7 footprint resolved to `Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65`** (was
  `⚠️ CUSTOM FP NEEDED`). This footprint exists in the standard KiCad footprint library
  (`Package_SON.pretty`, confirmed present under `/usr/share/kicad/footprints`) — it does
  not need custom generation after all. **Retires the U7 custom-footprint carry-forward.**
- **J2/J3 symbol corrected to `Connector:Conn_Coaxial`, footprint resolved to
  `ProjectLocal:BNC_Kinghelm_KH-BNC50-3511_Horizontal`** (was a nonstandard
  `Connector_Coaxial:BNC_Generic` symbol name and `⚠️ CUSTOM FP NEEDED`). A project-local
  footprint was generated for the Kinghelm KH-BNC50-3511 and lives at
  `footprints/ProjectLocal.pretty/BNC_Kinghelm_KH-BNC50-3511_Horizontal.kicad_mod` (confirmed
  on disk); `afe_ch_a.py`/`afe_ch_b.py` already reference both strings. **Retires the J2/J3
  custom-footprint carry-forward.**
- **D101/D201 symbol resolved to `dual_adc_usb:BAV199`** (was `⚠️ SYMBOL NEEDED`). The
  datasheet-librarian generated the correct 3-pin series-pair symbol; `afe_ch_a.py`/
  `afe_ch_b.py` already use it. The rejection of `Diode:BAV19` (wrong topology) still stands
  as the reason a generated symbol was needed.
- **U8 symbol resolved to `dual_adc_usb:ADS5231IPAGT`** (was `⚠️ SYMBOL NEEDED`) — generated
  symbol confirmed in use in `adc.py`.
- **X1 symbol resolved to `dual_adc_usb:SX3M40.000B10F20TNN`** (was `⚠️ SYMBOL NEEDED`) —
  generated symbol confirmed in use in `clock.py`.
- **U9 symbol resolved to `dual_adc_usb:GW1NR-LV9QN88PC6`** (was `⚠️ SYMBOL NEEDED`) —
  generated symbol confirmed in use in `fpga.py`. Note the symbol name drops the `/I5`
  ordering suffix that the MPN column carries (`GW1NR-LV9QN88PC6/I5`) — that's the
  datasheet-librarian's naming, not a mismatch.
- **Y1 symbol corrected to `Device:Crystal_GND24`** (was `Device:Crystal`, the 2-pin stock
  symbol). Y1 is a 4-pin crystal with case-ground pins 2/4; `usb_bridge.py` uses
  `Part('Device', 'Crystal_GND24', ref='Y1', ...)` and ties pins 2,4 to GND alongside 1
  (XCSI) and 3 (XCSO). The 2-pin symbol would have left the case-ground pins unmodeled.
- **FT232H decoupling notes corrected to match the 5 V-in power config** (driver decision,
  documented in `usb_bridge.py`'s module docstring): VREGIN ← V5, and VCCD is FT232H's
  *internal* 3.3 V regulator output, feeding local net FT_3V3 (which supplies VCCIO×3,
  VPHY/VPLL via FB3/FB4, the EEPROM, and the RESET# pull-up). Corrected mapping: **C49**
  (0.1 µF) is on VREGIN/V5, not VCCD as the old note said; **C50/C51/C52** (0.1 µF) are the
  three VCCIO pins on FT_3V3; **C53** (0.1 µF) is VCCA, its own cap, not shared with
  VCCCORE; **C54** (0.1 µF) + **C55** (4.7 µF) are VCCCORE; **C56** (4.7 µF) is the VCCD/
  FT_3V3 regulator-output bulk cap, not a second VCCCORE cap as the old note implied. No
  MPN, footprint, or symbol changed — value/package/tier for C49–C56 are unchanged.
- **FB2 note clarified**: FB2 feeds X1's XO_VDD supply from V3V3A (`clock.py`), i.e. it is
  the clock block's own local ferrite, not part of the ADC/FPGA/FT232H rail set it was
  previously grouped with without comment.

Revision 2 resolved the three items the datasheet-librarian escalated in
`handoffs/04_datasheets.md` (rev 1): the C104/C204 trimmer-part mismatch, the wrong U11
symbol, and the R18/R19 MODE pull-down value. All other rev-1 content (C101/C201, exact
909k/909Ω/56.2k/22.1k resistors, D101/D201 BAV199, U9 footprint, U1 substitution, inductor
picks) is unchanged — see the rev-1 decisions below, still in force.

## Decisions

- **REV 3 — U10 FT232H VPHY/VPLL added: ferrite + 10 µF + 0.1 µF per pin.** Phase-4 rev 2
  flagged that VPHY(3) and VPLL(8) had no local caps budgeted, per the Adafruit reference
  design (ferrite + 10 µF each, both rails already carry a separate 0.1 µF as part of the
  chip's general decoupling pattern — added here too for margin since the driver's ask
  specified one per pin explicitly).
  - New refs: **FB3** (VPHY ferrite), **FB4** (VPLL ferrite), **C57** (VPHY 10 µF), **C58**
    (VPHY 0.1 µF), **C59** (VPLL 10 µF), **C60** (VPLL 0.1 µF).
  - **All six reuse existing BOM MPNs — no new part numbers, no new stock/tier risk:**
    - Ferrite: same as FB1/FB2, Chilisin PBY160808T-601Y-N (C108301, 709763 stock, 0603,
      600 Ω @ 100 MHz, 1 A / 200 mΩ DCR) — meets the ≥200 mA ask with wide margin.
    - 10 µF: same as the V5/buck/ADC/FPGA bulk cap, C19702 (10 µF X5R 10 V, 0603, 11.3M
      stock, Basic tier) — meets ≥6.3 V.
    - 0.1 µF: same as the project-wide decoupling cap, CL05B104KB54PNC (C307331, 0.1 µF
      X7R, 0402, 11.7M stock, Basic tier).
  - No new footprint/symbol risk: `Inductor_SMD:L_0603_1608Metric` / `Device:FerriteBead`
    and `Capacitor_SMD:C_0603_1608Metric` / `Capacitor_SMD:C_0402_1005Metric` with
    `Device:C` are all already confirmed elsewhere in this BOM — not re-run through
    `validate-footprints.py`/`find-symbol.py` since they are verbatim repeats of already-
    passing rows, not new strings.
- **REV 3 — VCCA cap confirmed, not added.** The existing C49–C53 pool (5× 0.1 µF, 0402)
  already covers exactly 5 nets — VCCD, VCCIO×3, VCCA — one each, with VCCCORE separately
  on C54 (+ C55, 4.7 µF). So VCCA already has its own 0.1 µF distinct from VCCCORE; no new
  component was needed to satisfy this check. Documented explicitly in `sourced_bom.md` /
  `.csv` notes so this isn't re-litigated.
- **C104/C204 — LXRW19V330-050 (Murata varactor) replaced with Knowles JZ300 (true ceramic
  hand trimmer).** The architecture called for a hand-trimmed 23.8 pF for attenuator
  compensation; LXRW19V330-050 is a *voltage-tuned* capacitor (33 pF at Vt=0V, 16.5 pF at
  Vt=3V, with a 5th "Vt" bias pin) and cannot be hand-trimmed at all — confirmed by the
  datasheet-librarian's escalation.
  - **Options considered:**
    (a) True SMD ceramic hand trimmer covering ~23.8 pF, possibly + fixed C0G.
    (b) Keep the varactor + add a bias trimpot/DAC to set Vt.
    (c) Fixed C0G only, no trim (accept the compensation error).
  - **Chosen: (a).** Searched JLCPCB's dedicated "Trimmers, Variable Capacitors"
    subcategory (16 parts total — this is a thin category on JLCPCB, not a keyword-search
    miss). Found **Knowles JZ300** (LCSC C3273397): ceramic piston trimmer, 5.5–30 pF range,
    125 V, SMD 4.5×3.2 mm, $4.44/ea, **123 in stock**. The 5.5–30 pF range covers the 23.8 pF
    target with comfortable margin either side, so no parallel fixed C0G is needed. Rejected
    the next-closest candidates: STC3MA06-T1/STC3MB10-T1 (ranges top out at 6/10 pF, don't
    reach 23.8 pF), JR200 (4.5–20 pF, doesn't reach 23.8 pF), 2320-4SLR1 (6.5–25 pF covers
    it, but only 10 units in stock — FAIL). Rejected (b): adds a DAC/trimpot + firmware
    calibration loop the architecture never budgeted, for no benefit over a real trimmer
    that's actually in stock. Rejected (c): throws away the calibration the architecture
    explicitly wanted, unnecessarily, given (a) sourced cleanly.
  - **Footprint resolves with no custom work needed.** KiCad ships
    `Capacitor_SMD:C_Trimmer_Voltronics_JZ` (2 SMD pads, 3.9 mm pitch) — Knowles acquired
    Voltronics, and JZ300 is that same package family (JLCPCB's own listing calls it
    "Knowles JZ300 ... SMD,4.5x3.2mm", matching the footprint's descr text and dimensions).
    `validate-footprints.py` confirms it resolves. This also **retires the `⚠️ CUSTOM FP
    NEEDED` item** carried from rev 1 for C104/C204.
  - **Kept despite a concern:** stock is 123 — WARN territory, just above the 100-unit FAIL
    line, and Knowles is the only JLCPCB listing at this LCSC number (no second source in
    the trimmer subcategory that also meets the range+stock bar). Flagged below, not
    resolved silently.
- **U11 symbol changed from `Memory_EEPROM:93LCxxB` to `dual_adc_usb:93LC56BT-I_OT`.** The
  KiCad stock symbol is the 8-pin DIP/SOIC pinout (1 CS…4 DO, 5 GND, 8 VCC); the actual part
  is SOT-23-6 (1 DO, 2 VSS, 3 DI, 4 CLK, 5 CS, 6 VCC) — the stock symbol would miswire every
  pin. The datasheet-librarian's generated symbol `dual_adc_usb:93LC56BT-I_OT` (in
  `symbols/dual_adc_usb.kicad_sym`) has the correct 6-pin map and is confirmed present
  (`find-symbol.py` reports OK). No MPN change — same 93LC56BT-I/OT, C190271, 11173 stock.
- **R18/R19 changed from 10 kΩ to 1 kΩ.** Gowin UG284 (§MODE) recommends 1 kΩ pull-downs on
  the MODE0/MODE1 pins against the FPGA's internal weak pull-ups; 10 kΩ risks not
  overriding them reliably. Reused the existing 1 kΩ 0603 MPN already in the BOM
  (0603WAF1001T5E, C21190, 23.9M stock, Basic tier — same part as R7/R21/R22), so this adds
  no new line item and no tier/stock risk.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `sourcing/sourced_bom.md` (rev 4) | Full BOM with LCSC#, stock, price, tier, symbol, footprint, per-row notes | Always |
| `sourcing/sourced_bom.csv` (rev 4) | Machine-checked BOM, one row per distinct part/value, refdes lists/ranges | Coding phase onward — `validate-bom.py` diffs against this |

## Parts by block

| block_id | refs | MPNs |
|---|---|---|
| `usb_power_in` | J1, U1, U2, R1, R2, C1, C2, C3 | TYPE-C-31-M-12, USBLC6-2SC6, TPS22919DCKR, 5.1kΩ×2, 4.7µF, 10µF, 0.1µF |
| `power_digital` | U3, U4, U5, L1, L2, D1, R3–R7, C4–C9 | TLV62569DBVR×2, TLV75518PDBVR, FNR3015S2R2MT×2, LED, 100k/22.1k/100k/100k/1k, passives |
| `power_analog` | U6, U7, R8–R11, C10–C17 | TPS7A2033PDBVR, LM27762DSSR, 174k/100k/64.9k/100k, passives |
| `afe_ch_a` | J2, U101, U102, D101, R101–R111, C101–C114 | KH-BNC50-3511, OPA356AIDBVR, THS4551IRGTR, BAV199, **JZ300 (C104)**, precision R/C per `sourced_bom.md` |
| `afe_ch_b` | J3, U201, U202, D201, R201–R211, C201–C214 | identical to ch A, incl. **JZ300 (C204)** |
| `adc` | U8, FB1, R12–R15, C18–C30 | ADS5231IPAGT, PBY160808T-601Y-N, 56.2k/2.0/2.0/10k, decoupling |
| `clock` | X1, FB2, R16, R17, C31, C32 | SX3M40.000B10F20TNN, PBY160808T-601Y-N, 33Ω×2, decoupling |
| `fpga` | U9, J4, J5, D2, D3, R18–R24, C33–C46 | GW1NR-LV9QN88PC6/I5, THT headers (C492422, C37208), LEDs, **R18/R19 now 1kΩ (0603WAF1001T5E)**, R20 pull-up, decoupling |
| `usb_bridge` | U10, U11, Y1, R25–R27, C47–C60, FB3, FB4 | FT232HL-REEL, 93LC56BT-I/OT (**symbol dual_adc_usb:93LC56BT-I_OT**), X322512MSB4SI, 12.0k/10k/2.2k, load caps, decoupling, **VPHY/VPLL ferrite+10µF+0.1µF (rev 3, reused MPNs)** |

## Next phase must

1. **C104/C204 no longer need a generated footprint or a design decision** — `Device:C_Variable`
   + `Capacitor_SMD:C_Trimmer_Voltronics_JZ` are both confirmed resolvable. Nothing further
   for the datasheet-librarian to do on this part beyond noting the JZ300 datasheet
   (https://wmsc.lcsc.com/wmsc/upload/file/pdf/v2/lcsc/2404031010_Knowles-JZ300_C3273397.pdf)
   if the coder wants the mechanical adjustment-screw orientation.
2. **U11 is fully resolved** (MPN, symbol, footprint) — no further datasheet work.
3. **R18/R19 needs no datasheet work** — value-only change, same MPN/footprint/symbol as
   R7/R21/R22.
4. Everything else the rev-1 handoff asked of phase 4 remains outstanding and is **unchanged
   by this revision**: the unverified keystone facts in `handoffs/04_datasheets.md`
   (FT232HL-REEL full pinout/power wiring — no PDF obtained, GW1NR-9 exact pin-function
   names beyond the verified bank map, X322512MSB4SI CL cross-check, SX3M40 jitter spec).
   Those are datasheet-phase/coding-phase items, not sourcing failures.
5. **REV 3 — FB3/FB4/C57–C60 need no datasheet work.** All six reuse MPNs, footprints and
   symbols already verified elsewhere in this BOM. Nothing new for the datasheet-librarian.
6. **REV 4 — no new datasheet work.** Every rev-4 change was a BOM correction to match
   already-generated symbols/footprints already in use in the block code; no part is newly
   flagged as needing a symbol or footprint. If anything, rev 4 **reduces** outstanding
   datasheet-phase work by retiring the U7 and J2/J3 custom-footprint flags below.

## Carried forward

- **C104/C204 stock is WARN (123 units), single-source at this LCSC listing** (Knowles
  JZ300, C3273397) — re-check before order placement; no second JLCPCB-stocked trimmer
  covers the 23.8 pF target with usable stock (next-best, 2320-4SLR1, has only 10 units).
- **WARN stock, re-check before order placement (unchanged from rev 1):** U8 ADS5231IPAGT
  (154), U9 GW1NR-LV9QN88PC6/I5 (173), U102/U202 THS4551IRGTR (469).
- **Single-sourced, no pin-compatible second source (unchanged):** U8 ADS5231IPAGT; also
  **C104/C204 JZ300** (rev 2).
- **⚠️ CUSTOM FP NEEDED — both remaining items retired in REV 4:** LM27762DSSR (U7) now
  resolves to `Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65` (standard library); KH-BNC50-
  3511 (J2/J3) now resolves to the project-local `ProjectLocal:BNC_Kinghelm_KH-BNC50-3511_
  Horizontal` footprint, already generated and on disk. **No `⚠️ CUSTOM FP NEEDED` items
  remain open in this BOM.**
- **Project-local footprint library dependency (new in rev 4):** J2/J3 use
  `footprints/ProjectLocal.pretty/BNC_Kinghelm_KH-BNC50-3511_Horizontal.kicad_mod` — confirm
  this local `.pretty` directory is on the KiCad footprint search path at layout/export time,
  since it is not part of the standard KiCad library.
- **Extended tier (assembly setup fee) on nearly the entire BOM** — unchanged from rev 1.
- **Unverified keystone facts carried from architecture/datasheet phase** (GW1NR-9 pin map
  beyond banks, FT232H power-pin wiring, Y1 CL, X1 pin-1 function, op-amp FB pinouts,
  TPS7A2033 thermal) — unchanged by this revision, still open for coding to confirm.

## Do not redo

- All rev-1 MPN choices not touched by this revision — see rev-1 `## Decisions` above
  (unchanged): C101/C201 Murata 0603/250V substitution, exact 909k/909Ω/56.2k/22.1k
  resistor picks, D101/D201 BAV199 topology rejection of `Diode:BAV19`, U9 footprint
  choice, U1 TECH PUBLIC substitution, L1/L2/FB1/FB2 spec-match picks.
- **C104/C204 = Knowles JZ300 (C3273397)** — do not re-substitute back to a voltage-tuned
  part or a different trimmer family; this is the one JLCPCB-stocked true trimmer that both
  covers the 23.8 pF target and has a resolvable KiCad footprint.
- **U11 symbol = `dual_adc_usb:93LC56BT-I_OT`** — do not use `Memory_EEPROM:93LCxxB`.
- **R18/R19 = 1 kΩ (0603WAF1001T5E, C21190)** — do not revert to 10 kΩ.
- **FB3/FB4/C57–C60 (rev 3)** — VPHY/VPLL ferrite+10µF+0.1µF, all reused MPNs (PBY160808T-601Y-N,
  C19702, C307331). Do not source new/different parts for these.
- **REV 4 symbol/footprint corrections** — do not revert J1, U2, U6, U7, J2/J3, D101/D201,
  U8, X1, U9, or Y1 to their pre-rev-4 BOM cells; the code in `circuits/dual_adc_usb/*.py`
  is authoritative and was verified against each row (see `## Decisions — REV 4` above).
  Do not re-flag U2/U6/U7/U8/U9/X1/D101/D201/J1/J2/J3/Y1 as needing symbols/footprints —
  they are resolved.
- **REV 4 FT232H decoupling mapping** — C49 is VREGIN/V5, C56 is VCCD/FT_3V3 bulk; do not
  swap these back into a "C49–C53 = one net each" grouping, which was never what the code
  wires.

## Receipt

Rev 4: fixed 10 BOM rows (J1, U2, U6, U7, J2, J3, D101, D201, U8, X1, U9, Y1 — 12 refs) to
match `circuits/dual_adc_usb/*.py`, per block-coder escalation. All were stale
`⚠️ SYMBOL NEEDED`/`⚠️ CUSTOM FP NEEDED` flags or wrong symbol/footprint strings; code was
authoritative in every case (no code errors found). Retired both remaining
`⚠️ CUSTOM FP NEEDED` flags (U7, J2/J3) — zero open now. Corrected FT232H decoupling notes
(C49 VREGIN not VCCD; C56 is VCCD/FT_3V3 bulk) and FB2 note (feeds X1 XO_VDD). No MPN,
stock, price, or tier changed — zero new sourcing risk. `validate-bom.py` cannot run yet
(no `__main__.py` — assembler hasn't run: `ModuleNotFoundError:
circuits.dual_adc_usb.__main__`), confirmed by running it. `sourced_bom.md`/`.csv` updated
and agree. Cache disabled; no lookups needed. `status: complete`.
