---
phase: 03_sourcing
agent: part-sourcer
circuit: dual_adc_usb
written: 2026-09-09T00:00:00Z
status: partial
revision: 1
next_phase: 04_datasheets
---

# Phase 3 handoff — Sourcing

`pcbparts` MCP checked again this phase (`ToolSearch` for `mcp__pcbparts__*`) — **still not
connected.** All figures below come from `jlcsearch.tscircuit.com` (the same open JLCPCB
mirror the architect used), queried live via `curl`, one part/value at a time, on
2026-09-09. Every stock/price/tier figure in `architecture/ic_selection.md` was re-pulled
independently, not copied — most matched exactly (the mirror hadn't moved), a few did not
(documented below). KiCad footprint strings were validated against
`/usr/share/kicad/footprints` with `scripts/validate-footprints.py`; all 25 distinct
footprints resolve to real `.kicad_mod` files (see `sourcing/fp_check.py`).

## Decisions

1. **GW1NR-LV9QN88PC6/I5 (U12) and AD9235BCPZ-40 (U9/U10) are unchanged** — stock confirmed
   at 102 and 170 respectively, matching the architect exactly. Per the architect's explicit
   instruction these are escalate-not-substitute parts; both still clear the 100-unit floor,
   so no escalation was triggered.
2. **LP5907MFX-1.8 sourced as `LP5907MFX-1.8/NOPB` (LCSC C92498)**, not the bare
   `LP5907MFX-1.8` string (LCSC C23380872, only 3062 in stock). The `/NOPB`-suffixed listing
   is the one whose stock (17548) and price ($0.206) match the figures the architecture
   actually relied on — same TI part, lead-free suffix, functionally identical.
3. **909 kΩ attenuator resistor: PTFR0603B909KP9 (LCSC C2849091), ±0.1%, 100V, 0603, 513 in
   stock.** This is the *only* part in the whole JLCPCB catalog that is simultaneously
   ±0.1% and ≥100V at this value — checked every package/tolerance combination. Its stock
   (513) is just above the 500-unit warn line; flagged, not blocking (qty needed across 5
   boards is 10, vs 513 available).
4. **Compensation trimmer (6–30pF) confirmed unsourceable at scale** — the only two SKUs in
   range carry 2 and 7 units respectively. Per the architecture's own pre-approved fallback,
   substituted with a fixed compensation network: 15pF ±5%/100V top (GRM/06031A150JAT2A —
   ±2% doesn't exist at 100V, only voltage rating is held exactly), 150pF ±1%/50V bottom
   (GRM1555C1H151FA01D — ±1% is stocked at 16181 units where ±2% is stocked at 1–34 units,
   so ±1% was substituted as a *strictly tighter* superset of the ±2% ask). **Not escalated**,
   per the architecture's explicit instruction not to.
5. **Buck inductors (L1, L2) need a custom footprint.** No 3×3mm shielded power inductor
   exists in the standard KiCad library. Sourced the part (FNR3015S2R2MT, 2.2µH/2A, 60663 in
   stock) but the footprint is `⚠️ CUSTOM FP NEEDED` — see `## Carried forward`.
6. **BNC jack and USB-C receptacle footprints are best-effort, not confirmed.** Both parts
   themselves matched the architecture's stock/price exactly (KH-BNC50-3511, TYPE-C 16PIN
   2MD(073)); no session tool could read the vendor's mechanical drawing to confirm the exact
   land pattern, so a same-pin-count/same-mount-style KiCad footprint was assigned and
   flagged `⚠️ VERIFY FP`. This is a mechanical-fit risk (pads won't line up with the part),
   not an electrical one.
7. **1uF general decoupling sourced as X5R, not X7R** (skeleton asked X7R). The Basic-tier
   X5R part (CL10A105KB8NNNC, 5.98M in stock, $0.03) is both cheaper and vastly better
   stocked than any Extended-tier X7R option found; both are Class II ceramics and the
   tempco difference is immaterial for local bulk decoupling. Everywhere tolerance or
   voltage rating was load-bearing (the ±0.1%/±1%/±2% filter network, the 909k/100V leg),
   the exact spec was held or tightened — this substitution is confined to non-critical bulk
   decoupling.
8. **Feedback-divider resistors (8 total, 2 bucks + LM27762 ± outputs) are not sourced to a
   specific value.** TLV62569/TLV62568 are adjustable bucks and LM27762's outputs are also
   resistor-set — the exact ratios depend on each regulator's datasheet equations, which is
   datasheet-phase work, not sourcing-phase work. Real 0402 ±1% E96 resistor families exist
   at every value (confirmed via the searches used for every other resistor in this BOM);
   the datasheet-librarian/block coder computes values and cites concrete MPNs from the same
   families already verified here.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `sourcing/sourced_bom.md` | Every ref designator, real MPN, LCSC#, stock, price, package, tier, KiCad footprint, notes | Always — before writing any code |
| `sourcing/fp_check.py` | The 25 distinct footprint strings used in this BOM, in `validate-footprints.py`-checkable form | To re-run footprint validation, or to see the exact footprint-string-to-part mapping |

## Next phase must

Addressed to **datasheet-librarian**:

1. **Confirm exposed-pad (EP) dimensions for three parts whose KiCad footprint is a
   generic/wrong-vendor guess**, all flagged `⚠️ VERIFY FP` in `sourced_bom.md`:
   - `AD9235BCPZ-40` (U9, U10) — ADI's CP-32-2 mechanical drawing; footprint currently
     assumes a generic QFN-32/0.5mm EP of 3.45×3.45mm.
   - `GW1NR-LV9QN88PC6/I5` (U12) — **highest priority**, this is the critical-path part.
     Gowin's UG803 QN88P mechanical drawing; footprint currently borrows an ArtInChip
     QFN-88/10×10/0.4mm EP of 6.74×6.74mm, which is very likely wrong for Gowin's actual
     package. This is the same UG803 document R1 (in `02_architecture.md`) already requires
     you to pull for pin-budget reasons — get the mechanical drawing from the same document.
   - `THS4551IRGTR` (U8 ×2) — TI's RGT-16 drawing; footprint assumes a 1.7×1.7mm EP, which is
     TI's typical value for this package family but not confirmed for this exact part.
2. **Get the mechanical drawing for `FNR3015S2R2MT`** (buck inductors L1, L2) and hand the
   block coder a 2-pad custom footprint — none exists in the standard KiCad library for this
   package.
3. **Confirm land patterns for `KH-BNC50-3511` and `TYPE-C 16PIN 2MD(073)`** against their
   own datasheets. Both are flagged `⚠️ VERIFY FP` — a same-shape KiCad footprint was
   assigned without seeing the actual drawing.
4. **Pull TLV62569DBVR, TLV62568DBVR, and LM27762DSSR datasheets** and compute the 8
   feedback-divider resistor values (left unsourced, see `## Decisions` #8). Cite concrete
   0402 ±1% MPNs from the same resistor families already used elsewhere in
   `sourced_bom.md` (e.g. the `04XXWGFxxxxTCE` / `RT0402BRDxxxxL` families) rather than
   introducing new ones.
5. Datasheets needed regardless of the above (significant parts per the standard rule — ICs,
   FETs, magnetics, crystals, and anything whose pinout/application circuit a coder needs):
   AD9235BCPZ-40, GW1NR-LV9QN88PC6/I5, CY7C68013A-56LTXC, AD8066ARZ-R7, THS4551IRGTR,
   LM27762DSSR, TLV62569DBVR, TLV62568DBVR, SiT1602BI-22-33E-10.000000, SN74LVC2G34DBVR,
   CAT24C128WI-GT3, FNR3015S2R2MT (for the custom footprint). LP5907MFX-3.0/1.8, AP2112K,
   BAV199, USBLC6-2SC6, SMAJ5.0A, PESD3V3L1BA are simple enough to skip a full datasheet pull
   unless the coder hits a pinout question.

## Carried forward

- **GW1NR-9 single-source at 102 units** — unchanged from architecture, still the design's
  lowest-stock keystone. Not re-escalated this phase (escalation part
  `GW2AR-LV18QN88C8/I7` remains available at 168 units if needed).
- **909kΩ attenuator resistor at 513 units** — new flag from this phase. Above the 500-unit
  warn line but close to it; the only part meeting both ±0.1% and ≥100V. If a future board
  spin needs >500 units total, re-check stock before committing.
- **Buck inductors need a custom KiCad footprint** — `⚠️ CUSTOM FP NEEDED`, see `## Next
  phase must` #2. Block coder cannot place L1/L2 until this exists.
- **BNC and USB-C receptacle footprints need land-pattern confirmation** — `⚠️ VERIFY FP`,
  see `## Next phase must` #3. Risk is mechanical fit, not electrical function.
- **AD9235, GW1NR-9, THS4551 EP pad dimensions unconfirmed** — see `## Next phase must` #1.
  Wrong EP size mainly affects thermal-pad soldering/via placement, not pin alignment, so
  these parts will still place and route; confirm before Gerber generation.
- **Feedback-divider resistor values (8 refs) left unresolved** — see `## Decisions` #8 and
  `## Next phase must` #4. Not a sourcing failure — a datasheet-phase computation.
- **15pF compensation cap tolerance is ±5%, not the architecture's ±2% target** (voltage
  rating held at the required ≥100V). Accepted per the architecture's own framing that this
  network trades HF flatness, not DC accuracy — see `## Decisions` #4. If the datasheet
  phase or ERC review disagrees with that risk acceptance, it should escalate back to the
  architect rather than have the coder silently re-decide it.
- Every "still open" item from `02_architecture.md` `## Carried forward` (R1 pin budget,
  AD8066 phase-reversal confirmation, TLV6256x soft-start ramp confirmation, GW2AR-18
  pin-compatibility confirmation) remains open and is now the datasheet phase's job.

## Do not redo

- Every MPN in `sourced_bom.md` marked "Confirmed exact match" — stock, price, and tier were
  independently re-verified this phase via live query, not assumed from the architecture.
  Re-querying them again next phase wastes a phase; trust these rows.
- The critical-path/no-substitution decision on `GW1NR-LV9QN88PC6/I5` and `AD9235BCPZ-40` —
  both still clear stock thresholds; do not re-litigate without a new stock failure.
- The trimmer-capacitor non-escalation (`## Decisions` #4) — the architecture pre-approved
  this exact fallback path.
- The single `GND` net, the 8-bit slave FIFO, the ±4.2V rails, the exact ÷11/×1.10 signal
  plan, the FPGA-between-ADC-and-USB topology — all carried from `02_architecture.md`
  `## Do not redo` and untouched by sourcing.
- No sibling design directory (`../dual-adc-usb-1`, `../dual-adc-usb-2`) was read this phase.

## Receipt

- ~70 distinct parts/values sourced across ~200 ref designators; every ref in
  `02_architecture.md`'s block manifest appears in exactly one row of `sourced_bom.md`.
- Tier split: 11 Basic, 1 Preferred (SMAJ5.0A, unchanged), remainder Extended (expected —
  architect flagged this design as Extended-only for actives; sourcing found real Basic-tier
  jellybean passives for ~11 line items the skeleton hadn't distinguished by tier).
- 2 sourcing gaps, neither blocking: buck inductor footprint (custom FP needed, part itself
  is sourced and in stock) and 8 feedback-divider resistor values (deferred to datasheet
  phase by design, real MPN families already identified).
- 3 KiCad footprints flagged for EP-dimension confirmation, 2 flagged for land-pattern
  confirmation — none blocking, all handed to the datasheet-librarian with the exact
  document to pull.
- `pcbparts` MCP still unavailable — confirmed via `ToolSearch`, not assumed.
- Status: **partial** → `04_datasheets`. Revision 1.
