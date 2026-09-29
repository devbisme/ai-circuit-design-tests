---
phase: 03_sourcing
agent: part-sourcer
circuit: dual_adc_usb
written: 2026-09-23T12:00:00Z
status: complete
revision: 4
next_phase: 05_coding
---

# Phase 3 handoff — Sourcing (rev.4, tiny addition pass)

This is a **tiny addition pass** against phase 4 rev.6 (Decision 16) plus a fpga_core-coder-reported
decoupling gap — **not a re-source**: the 163 previously-verified refs keep their prior
stock/price/tier/symbol/footprint data unchanged. Only 6 new refs were added and freshly verified
live via the `pcbparts` MCP on 2026-09-23, plus one stale note cell was corrected in place.

## Decisions

1. **U15 + C87 added: the sourced fix for U14's soft-start finding (phase 4 rev.6, Decision 16).**
   Phase 4 verified, with citations, that (a) the 10 mV/µs VCCIO ramp limit (DS117 Table 3-3) is a
   real max applying to VCCIO3, so 180 µs is a genuine floor; (b) U14's (AP2127K-1.8TRG1) 50 µs
   soft-start is a fixed internal timer, unaffected by COUT; (c) sourcing rev.3's own proposed
   mitigation — an RC on U14's Shutdown pin — is confirmed a non-fix, since that pin is a binary
   logic enable (VIH≥1.5V/VIL≤0.5V) with no analog ramp behavior. The verified fix: a second
   **TPS22918DBVR (U15)**, same MPN/LCSC as the existing U9 (`C131941`, already qualified, symbol
   already generated as `dual_adc_usb:TPS22918DBVR`), inserted between U14's VOUT (`P1V8`) and U5
   pin 12 (`VCCIO3`), with a **220 pF C0G/NP0 0402 cap (C87)** on its CT pin. Per TI SLVSD76C
   §8.3.3/Table 2, 220 pF gives a 260 µs 10-90% rise time at VIN=1.8V — clears the 180 µs floor
   with ~44% margin. Live-reverified: U15 stock 8022 pcs (U9 was 8480 at its own sourcing time,
   still deep). C87 (YAGEO CC0402JRNPO9BN221, `C107001`) 412,572 pcs, Extended tier, C0G/NP0
   specifically (not X7R — the slew timing depends on dielectric stability). U14 and its
   C84/C85/C86 are unchanged — this is an addition downstream, not a substitution.
2. **No U15 input/output bypass caps added — checked against TI's datasheet, not assumed.**
   TI's typical-application section (§9.2.2/§10, p.16-20) recommends ≥1 µF ceramic VIN bypass and
   an optional C_L with a 10:1 CIN:CL ratio preferred. U15's VIN net (`P1V8`, shared with U14's
   VOUT) already carries C85 (100 nF) + C86 (4.7 µF); U15's VOUT net (`VCCIO3`) already carries
   C511 (100 nF) + C512 (4.7 µF) + C513 (22 µF) downstream. Both exceed TI's recommendation with
   margin — no new caps needed.
3. **U15's ON-pin drive net is left to the power_tree coder, not speculatively sourced.** Neither
   `net_plan.md` nor phase 4's recommendation specifies how U15 should be enabled. The obvious
   patterns (mirror U9's R71 100 kΩ pull-up to `FT_3V3`, or tie directly to U14's own enable) reuse
   parts already on the BOM either way, so no new resistor was added here — adding one now would be
   guessing at a net-plan decision that belongs to the coder/architect, not sourcing.
4. **C514-C517 added: closes a 7-of-11 100 nF decoupling shortfall on U5, reported by the
   fpga_core coder.** `net_plan.md`'s decoupling policy (lines 172, 178-179) requires 100 nF at
   every U5 VCCIO/VCCX pin (6 on `P3V3D`: 23,44,58,64,67,78) **plus** 1 on `P1V8` (pin 12, already
   C511) **plus** 100 nF ×4 on VCC core (1,22,45,66) — 11 caps total. Rev.3's C501-C506 covered
   only 4 of the 6 P3V3D VCCIO/VCCX pins and 2 of the 4 VCC-core pins (6 caps; 7 with C511) —
   4 short. Added C514, C515 (remaining P3V3D VCCIO/VCCX pins) and C516, C517 (remaining VCC-core
   pins), same part as everywhere else on this board: CL05B104KO5NNNC / `C1525`, 100 nF X7R 0402,
   Basic tier, 27.4M pcs — no new verification needed, folded into the existing combined 100 nF
   row in `sourced_bom.csv`.
5. **U5's stale I/O-margin note corrected, no other cell in that row touched.** The note read
   "free-I/O count (need ≥51) still unverified" — superseded since phase 4 rev.5 (UG803): 48
   3.3V-capable I/O available (BANK1+BANK2) vs. **46** required by architecture rev.3 (not 51 —
   that was an earlier, since-revised figure), **+2 margin**. Corrected in both `sourced_bom.csv`
   and `sourced_bom.md`; MPN/LCSC/stock/price/package/tier/symbol/footprint in that row are
   untouched.
6. **Cost re-checked: new total ≈ $88.9-90.9/board, up ≈$0.42 from rev.3's $88.5-90.5.** U15
   ($0.3988) is the only non-trivial addition; C87 and the four C514-C517 caps are sub-cent. **This
   pushes the top of the range ≈$0.9 over the `[ASSUMED]` $90 target** — flagged plainly per the
   driver's instruction, not absorbed quietly. Rev.3 already had ~$0 headroom and this pass had no
   offsetting cut to give — it was scoped as two correctness fixes, not a cost pass. Escalate to
   the architect if the target is hard. ADS5231 remains the only part over the $25 flag.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `sourcing/sourced_bom.md` | Full per-block sourcing table incl. all rev.4 additions | Always — before writing any code |
| `sourcing/sourced_bom.csv` | Machine-checked BOM, 169/169 refdes (163 + 6 new), zero duplicates/gaps (verified) | Every gate from coding onward — `validate-bom.py` reads this |

`validate-bom.py` was not run against `circuits/dual_adc_usb` this pass — block coding is already
underway (`handoffs/05_blocks/*.md` exist) but `power_tree.py`/`fpga_core.py` were not re-checked as
part of this sourcing addition; the coding/ERC gate should run it once those blocks incorporate
U15/C87/C514-C517.

## Parts by block

| block_id | refs | MPNs (new/changed only, rev.4) |
|---|---|---|
| `afe_input` | J1,J2,R101,R102,R201,R202,C101-C103,C201-C203,D101,D201 | — unchanged |
| `afe_buffer` | U1,C11-C14,C15,C16 | — unchanged |
| `afe_driver` | U2,U3,R111-R118,R211-R218,L111-L114,L211-L214,C111-C119,C211-C219,D111,D112,D211,D212 | — unchanged |
| `adc_dual` | U4,R401,C401-C410 | — unchanged |
| `clock_gen` | X1,R31,R32,C31 | — unchanged |
| `fpga_core` | U5,J3,D51,D52,R51-R55,**C501-C517** | **CL05B104KO5NNNC** (C514,C515,C516,C517 — new, decoupling shortfall fix) |
| `usb_bridge` | U6,U7,U8,J4,Y1,R61-R67,C601-C612 | — unchanged |
| `power_tree` | U9-U15,Q1,FB1,L71,L72,R71-R76,C71-C87 | **TPS22918DBVR** (U15 — new, same MPN as U9), **CC0402JRNPO9BN221** (C87 — new, CT cap) |

169/169 refdes covered exactly once, diffed programmatically (no dupes/gaps). Full mapping in
`sourced_bom.csv`.

## Next phase must

Addressed to `power_tree`'s and `fpga_core`'s coders (via the driver's per-block work orders):

1. **power_tree: wire U15 between U14's VOUT (`P1V8`) and U5 pin 12 (`VCCIO3`)**, CT pin to GND
   through C87. Decide and wire U15's ON-pin drive (R71-style pull-up to `FT_3V3`, or tied to
   U14's enable) — this was intentionally left open by sourcing (Decision 3), not by oversight.
   Sequence U15's enable at or after U14's — no strict interlock needed, U14's 50 µs ramp
   completes long before U15's 260 µs CT-controlled ramp begins driving VCCIO3 (phase 4 rev.6).
2. **fpga_core: wire C514, C515 at the 2 U5 VCCIO/VCCX pins (of pins 23,44,58,64,67,78) not
   already covered by C501-C506, and C516, C517 at the 2 VCC-core pins (of pins 1,22,45,66) not
   already covered** — closes the 11-cap decoupling requirement in full.
3. No datasheet work is needed for U15 (reuses U9's already-generated symbol and datasheets) or
   C87/C514-C517 (standard passives, MPNs already established elsewhere on the BOM).

## Carried forward

| Item | Status / why still open |
|---|---|
| **Systematic decoupling under-allocation pattern — 4th instance found.** | `design_risks.md`/`net_plan.md`'s per-block decoupling allocation has now been short **four separate times**, each found by a block coder reading the datasheet/net-plan against the BOM rather than by sourcing or the architect: U1 (no HF bypass at all, rev.3), U6 VPHY/VPLL + U7 VCC (3 bare pins, rev.3), and now U5 (7-of-11, rev.4). **The reviewer should assume any block not yet coded may have the same gap** — this is a pattern in how the skeleton BOM was built, not a one-off miscount. Worth flagging to the architect if a 5th instance turns up. |
| Board cost at $88.9-90.9, **now ~$0.9 over the $90 `[ASSUMED]` target on the high end** | New this pass (Decision 6) — needs an offsetting cut or a target waiver from the architect; sourcing has no cut to offer from within this pass's scope |
| U14 t_ss vs. 180 µs floor | **Closed this pass** — U15+C87 is the sourced fix. Do not reopen; see Decision 1 |
| U5 free-I/O margin | **Closed** (phase 4 rev.5 + this pass's note fix) — 48 available vs. 46 required, +2 margin |
| ADS5231/GW1NR-9 stock (154/173 pcs) | Single-source, whole-float — buy qty-5 allocation now. Unchanged |
| 910 kΩ divider substitution, 130 pF cap at ±1%, FB1 0805→0603 | Unchanged accepted deviations |
| L112/L114/L212/L214 stock at 602 pcs | Marginal, unchanged |
| USBLC6-2SC6 junction capacitance | Not datasheet-verified (phase 4), doesn't block coding — unchanged |

## Do not redo

- The 163 previously-verified refs and their MPN/stock/tier/footprint/symbol data — unchanged,
  not re-checked, per this being a tiny addition pass.
- U15's ON-pin net — intentionally left undecided by sourcing (Decision 3); do not read this as a
  gap to fill with a new sourced part, it is a net-plan/coding decision.
- U14, C84, C85, C86 — unchanged, U15 is an addition downstream, not a substitution.
- R402's deletion, R66/R67 assignment, C606/C608 net labeling, U7/Y1/D101/D201 symbol-cell fixes
  — all still stand from rev.3, untouched this pass.

## Receipt

- 6 new refs sourced (U15, C87, C514-C517), 169/169 refdes total, 0 gaps/duplicates. 1 stale note
  cell corrected (U5 I/O margin — now closed: 48 vs. 46 required, +2).
- U15 = 2nd TPS22918DBVR (same MPN as U9, C131941, 8022 pcs live) fixes U14's soft-start finding
  per phase 4 rev.6 Decision 16; C87 = 220 pF C0G CT cap (C107001, 412,572 pcs) gives 260 µs rise
  time, clears the 180 µs floor. No U15 bypass caps needed — checked against TI's datasheet.
- C514-C517 (CL05B104KO5NNNC, reused MPN) close a 7-of-11 U5 decoupling shortfall reported by the
  fpga_core coder — the 4th such gap found on this board; flagged as a pattern in Carried forward.
- Cost now ≈$88.9-90.9/board — **pushes ~$0.9 over the $90 target on the high end**, flagged
  plainly, no offsetting cut made. Status: complete (both items sourced, no failures).
