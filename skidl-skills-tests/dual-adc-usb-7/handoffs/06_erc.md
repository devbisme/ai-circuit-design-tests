---
phase: 06_erc
agent: erc-reviewer
circuit: dual_adc_usb
written: 2026-09-23T14:55:00Z
status: complete
revision: 2
next_phase: export
---

# Phase 6 handoff — ERC and design review

**0 ERC errors, 0 ERC warnings. Verdict: PASS. Export is unblocked.**

Revision 2 re-gates the circuit after the HIGH-1 and MED-2 fixes. Both are closed and
independently re-verified. Full detail in `erc_report.md`; this file carries only what the
next agent must act on.

## Decisions

1. **HIGH-1 CLOSED — and I verified the coder's *audit*, not just its one line.** The line
   is right (`fpga_core.py:140` → `p1v8 += j3[1]`; netlist shows `J3.1` on `P1V8`). More
   importantly, I enumerated **all 13 IOL (BANK3) pins** from the symbol and resolved each
   mechanically against the netlist rather than reading the coder's list back: pins 5–8
   (JTAG, via `J3`) and 9 (RECONFIG_N, via `R53`) are the only ones used and **all five are
   now referenced to `P1V8` = VCCIO3**; pins 3, 4, 10, 11, 13, 14, 15, 16 are NC. **Zero
   BANK3 pins touch `P3V3D`.** A sweep of every U5 signal pin for a rail mismatch found
   none. The audit claim is true.
2. **MED-2 CLOSED as recommended.** `VBUS_SW` now carries `C88.1` (100 nF 0402) with
   `C88.2` on `GND`, at the VIN pin U12 shares with two 1.5 MHz switchers. U9/U10/U11
   correctly left bare per the revision 1 split.
3. **Nothing the fixes could have disturbed was disturbed.** Checked explicitly: `P1V8`
   gained J3.1 (a pod's high-impedance reference — no effect on U15's CT-limited ramp);
   `P3V3D` lost J3.1 (trivial); `VBUS_SW` gained 100 nF against ~60 µF, so U9's 150 mA
   inrush arithmetic is unchanged; `N$33`–`N$43` map to the same pins as revision 1, so the
   netlist stayed reproducible; ERC stayed 0/0.
4. **No open item is export-blocking.** See `erc_report.md` § "Is anything still open
   export-blocking?". I agree MED-1 is layout-blocking — but **not** for the reason given.
   The footprint string *is* in the exported netlist and travels into KiCad on import. What
   makes it safe is that nothing downstream of export commits to copper: a human opens the
   board and a swap costs minutes. Recorded below so layout cannot miss it.
5. **`datasheets/BAT54S_SUMMARY.md` corrected in this pass.** The impossible claim (the
   part "holds ADS5231 input pins inside AVDD+0.3V") is removed and replaced with the
   correct physics: the clamp shares its net with AVDD so the two track; its ~0.4 V Vf
   keeps the ADC's ~0.7 V internal ESD junction off, which is what the +0.3 V limit exists
   for; and the only driver on those nodes (the THS4521) is powered from that same net, so
   nothing in-circuit can forward-bias the clamp at all. R-10 should be reworded to match.
6. **Revision 1 decisions 1, 2 and 4 stand unchanged** — the EEPROM pin-override acceptance,
   the benign `Missing tag` finding, and the 6-benign/2-real split of the package notes.
   Not re-derived; see revision 1 text retained in `erc_report.md`.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `erc_report.md` | Rev 2 gate results, the BANK3 audit table, both closed findings, the export-blocking analysis, all retained rev 1 verification | Always |
| `outputs/dual_adc_usb.net` | **170 components, 127 nets**, reproducibility- and refdes-verified | Export |
| `datasheets/BAT54S_SUMMARY.md` | Corrected clamp analysis (was wrong on its face) | R-10 review |

## Next phase must

**Export is unblocked.** Nothing is owed to a coder. Run:

```bash
KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python3 -m circuits.dual_adc_usb
```

which regenerates `outputs/dual_adc_usb.net` and the BOM XML. Expect ERC `0 errors,
0 warnings` and the one benign `Missing tag` line at netlist generation (Decision 2,
revision 1 — SKiDL's root hierarchy node, not fixable from `__main__.py`, creates no random
tag, does not affect output). Gate commands, both currently exit 0:

```bash
python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/validate-footprints.py circuits/dual_adc_usb
python3 ${CLAUDE_PLUGIN_ROOT:-.}/scripts/validate-bom.py sourcing/sourced_bom.csv --circuit circuits/dual_adc_usb
```

## Carried forward

Accepted for export; a human must still close these before the board is fabricated or trusted.

- **MED-1 — J1/J2 and J4 land patterns. Resolve before layout.** Sourced `KH-BNC50-3511`
  sits on `BNC_Amphenol_031-6575_Horizontal`; sourced `TYPE-C-16PIN-2MD073` sits on
  `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal`. Neither is the sourced
  manufacturer's own pattern, and USB-C receptacles are not interchangeable between makers.
  Drawings already on disk: `datasheets/KH-BNC50-3511.pdf`,
  `datasheets/TYPE-C-16PIN-2MD073.pdf`. **`validate-footprints.py` is structurally unable
  to catch this** — it confirms a `.kicad_mod` exists, nothing about the package variant.
- **MED-3 — THS4521 summing node ≈ −0.79 V vs (V−) − 0.7 V under ±55 V overload.** Held by
  the FDA's internal clamp at ~4 mA through Rg = 1.00 kΩ, inside the ±10 mA rating.
  Survives by clamp, not by design. Bench-verify overload recovery.
- **U15.ON bench item stands** (VCCIO3 rise ≥ 180 µs, monotonic; fallback 10 k + 100 nF RC
  from P3V3D). **Refinement from this pass:** now that `J3.1` references `P1V8`, run that
  measurement **with the JTAG pod attached** as well as without — that is the loaded case,
  and it is the configuration a developer will actually power up in.
- **LOW-1 — VBUS is 11 µF nominal** (C83 10 µF + C609 1 µF) against the 10 µF USB
  convention, and `power_tree`'s comment says nothing may be added while `usb_bridge` added
  C609. MLCC derating at 5 V almost certainly saves it; the contradictory comments should go.
- **LOW-2 — 11 auto-named nets `N$33`–`N$43`** in `fpga_core` (JTAG ×4, RECONFIG_N,
  MODE0/1, two LED chains). Cosmetic; verified stable across runs.
- **LOW-3 — U5's EP is a single 6.8 × 6.8 mm paste aperture.** Dimensionally correct per
  UG119E and on `GND`, but needs stencil segmentation (3×3 windows, ~50–60 % coverage) or
  the part floats and voids on reflow. **This footprint is custom-generated, not
  library-sourced** — no library vetting behind it. Tell the fabricator.
- **Doc:** correct the U5 pin-12 label in `symbols/dual_adc_usb.kicad_sym`
  (`VCCX_VCCO0` → `VCCIO3`). That mislabel shares a root cause with HIGH-1 and has now
  bitten once. `design_risks.md` R-10 should be reworded per Decision 5.

## Do not redo

- **ERC** — 0/0, re-run independently at revision 2.
- **The BANK3 / IOL audit** — all 13 IOL pins enumerated and resolved against the netlist;
  zero on a 3.3 V net. Closed.
- **Both false-positive claims** (EEPROM pin override; `Missing tag`) — verified from
  primary sources at revision 1, unaffected by these fixes.
- **Reproducibility and refdes integrity** — two fresh runs byte-identical ignoring
  `(date …)`; 170 components, 170 unique, no duplicates, no `_1` suffixes.
- **`validate-bom.py`** — exit 0 at 170 parts / 67 rows, including C88.
- **Exposed pads** — U5 is the only EP part; pad 89 present (6.8 × 6.8, matching UG119E
  D2=E2) and on `GND`.
- **Anti-alias filter topology and response** — recomputed from netlist values:
  **−3 dB at 4.235 MHz, −41.3 dB at 10 MHz**, ripple ≤ 1.6 dB, no peaking. Meets SPEC
  (−3 dB ≥ 4 MHz, ≥ 40 dB at 10 MHz). Both shunt caps carry real current — a genuine 4-pole
  ladder, not the silently-degraded topology this check exists to catch.
- **Supply spans** — every IC against its abs max. FDAs single-supply 3.3 V/GND, AD8066 on
  ±5 V against ±13.2 V. No violations.
- **All other bank voltages** — ADC data (IOB/BANK2), status and serial (IOR/BANK1), FIFO
  (IOT/BANK0) all correctly on 3.3 V rails.

## Receipt

- **ERC: 0 errors, 0 warnings** — re-run independently; 1 benign netlist-generation note.
- **HIGH-1 CLOSED**, audit verified independently: all 13 IOL pins enumerated, 5 used and
  all on `P1V8`, 8 NC, **zero BANK3 pins on a 3.3 V net**.
- **MED-2 CLOSED**: C88 100 nF at U12 VIN on `VBUS_SW`/`GND`.
- **Gates:** footprints exit 0 (61 strings); BOM exit 0 (**170 parts** / 67 rows, 8 package
  notes, 6 benign); netlist byte-identical across two runs; 170/170 unique refdes.
- **`BAT54S_SUMMARY.md` corrected** — the impossible AVDD+0.3 V claim replaced.
- **5 open findings: 2 MED, 3 LOW. None export-blocking** — 1 layout, 1 bench, 3 doc/fab.
- **Verdict: PASS.** Export unblocked.
