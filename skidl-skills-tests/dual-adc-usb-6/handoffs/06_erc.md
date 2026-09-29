---
phase: 06_erc
agent: skidl-erc-reviewer
circuit: dual_adc_usb
written: 2026-09-22T06:30:00Z
status: complete
revision: 2
next_phase: export
---

# Phase 6 handoff — ERC review (re-gate)

**0 errors, 2 warnings, 3 notes. Circuit is PASS.** Export is unblocked.

All four HIGH and all three MEDIUM findings from revision 1 are closed and verified in the
built netlist, not accepted from the change list. Three new findings, none blocking.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `erc_report.md` | Rev.1 closure evidence, the 3 new findings with fix snippets, the recomputed front-end response, the re-verified census | Always — before export, and before touching the AFE |
| `__main__.erc` | Raw ERC output of the run below | Cross-checking the receipt |
| `sourcing/sourced_bom.md` | Rows 26 (J1) and 46 (TVS) carry stale prose — notes 2 and 3 | Before export writes a BOM from it |
| `datasheets/TYPE-C-16PIN-2MD-073_SUMMARY.md` | The corrected J1 mechanical reading that the BOM row has not caught up with | Adjudicating any J1 footprint question |

## Decisions

1. **PASS.** 0 ERC errors; footprint gate clean — both package mismatches fixed and
   re-verified against the sourced MPN, not against library existence.
2. **Accepted: the 2 ERC drive warnings, unchanged.** Same two, same cause, re-verified
   pin-by-pin. Ferrite pins are PASSIVE so `VBUS_SW.drive = POWER` cannot cross FB1/FB2.
   **Still do not suppress them** with `.drive = POWER` on the LDO input nets.
3. **Accepted: the census is now 58, not 57, and that is correct.** `VREF_OFF` joined it
   (driving pin moved behind R19); `VREF_OFF_AMP` did not (U7.OUT drives it). Nothing else
   moved. `VREF_OFF` was correctly **not** given `.drive = POWER` — classification, not
   suppression — and the stale `__main__.py` comment was fixed.
4. **Accepted: the part change to ESD9L5.0ST5G was necessary, not gold-plating.** I
   recomputed the counterfactual: relocating the 15 pF part alone gives −3 dB at
   **3.996 MHz** against F8's 4.000 MHz floor. The claim was right, by a hair. As built
   (9.4 pF): 4.322 MHz and −30.9 dB at 10 MHz. Both pass.
5. **Accepted: TVS polarity.** Verified from the library, not the comment —
   `Device:D_Zener` pin 1 is named `K` and lands on BUFIN, pin 2 on GND. Correct for a
   unidirectional part. BUFIN never leaves 0.734–2.552 V in service, well under the 5 V
   standoff.
6. **Accepted: R19/RNULL.** Feedback at the op-amp output, all 300 nF on the load side.
   Textbook. My rev.1 MEDIUM-6 was raised as unproven and came back datasheet-backed
   (SLOS270F §8.3.2) — the stronger answer, and I am recording that it was strengthened
   rather than argued away. Crosstalk: I get −78 dB where they state −75 dB (the bottom
   legs swing −11.8/+8.2 µA, not ±8.2), so the real number is marginally worse than their
   arithmetic and still ≈0.5 LSB. No spec requires channel isolation. Accepted.
7. **Dispositioned acceptable, not blocking: the 3.9 % compensation shelf (report finding
   1).** It misses F12's ±2 % gain window, but F12 is **SOFT**, explicitly "before
   host-side calibration", and the error is one first-order shelf at a known corner —
   characterisable and correctable in firmware. That is why F8 was worth a FAIL and this is
   not. **It is also my miss from revision 1** and it is pre-existing, not a regression: I
   modelled from `CHn_BUF` onward and treated the divider as ideal. Recorded so it is not
   mistaken for damage from this round of fixes.

## Next phase must

**Export is unblocked.** Run from the project root (there is no `.venv/`):

```bash
cd /home/devb/projects/AI/ai-circuit-design-tests/skidl-skills-tests/dual-adc-usb-6
KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python3 -m circuits.dual_adc_usb
```

1. **Netlist byte-stability is already audited — do not re-run it as a gate.** Two
   consecutive generations into the scratchpad are identical apart from the `(date …)`
   line. This closes the item I left open in rev.1.
2. **Expect one benign netlist-generation warning**, `Missing tag on <frozen
   importlib._bootstrap>` (the unnamed root node). It does not affect the output — the
   netlists are byte-identical with it present. Do not chase it.
3. **Before writing the BOM, fix two stale rows in `sourced_bom.md`** (notes 2 and 3):
   row 46 says symbol `Device:D_TVS` where the code uses `Device:D_Zener`; row 26 (J1)
   repeats the "round holes Ø1.70/Ø1.80" reading that
   `datasheets/TYPE-C-16PIN-2MD-073_SUMMARY.md` has explicitly retracted, and calls the
   footprint "(to be generated)" when it exists and is in use. Both are prose-only, neither
   changes the netlist — but this design has now lost two phases to exactly this kind of
   stale cell.
4. **Optional, and cheaper now than after fabrication** — `circuit-architect` may take
   report finding 1: `C_att_b` 220 pF → 210 pF (0.3 % residual), or better, 200 pF fixed
   plus a 5–20 pF trimmer, which is what SPEC I2's "trimmable compensation cap" wording
   points at and what handles C_node's own spread. One passive, existing refdes. If it is
   declined, say so explicitly so it stops resurfacing.

## Carried forward

- **R12 — TVS leakage, tracked and unresolved by design.** ESD9L5.0ST5G is Ir ≤1 µA at
  Vrwm/150 °C. On an 82.6 kΩ Thevenin source that would be 4.5 % FS; my independent
  calculation gives 4.6 %, corroborating theirs. The real operating point is 0.73–2.55 V at
  ≤85 °C where leakage is orders of magnitude lower, but **that is an assumption, not a
  datasheet number.** `design_risks.md` R12 names the action: read the ESD9L5.0ST5G
  I_R-vs-V_R curve, or bench-check DC offset on board 1. The BAV199 was chosen at ~1 nA for
  this exact reason, so the TVS is now the dominant leakage term on that node.
- **Two project-generated footprints I cannot independently verify.**
  `ProjectLocal:USB_C_Receptacle_TYPE-C-16P-2MD073` and
  `ProjectLocal:BNC_KH-BNC50-3511_Horizontal`. I confirmed pad/pin consistency and that the
  USB-C geometry matches the corrected datasheet summary, but re-deriving vector geometry
  from the drawings is beyond what I can check. Human eyes before fab.
- **Unchanged from rev.1:** AP62200T VIN minimum 4.2 V against a 4.4 V worst-case USB
  droop (0.2 V margin); X1 single-sourced at 50 pcs — re-qualify before any reorder larger
  than this 10-board run.
- **The 2 U5/U6 warnings are permanent** and will appear on every future run.

## Do not redo

- **ERC run, refdes hygiene, exposed pads, driverless census, NC census.** Re-verified this
  round: 241 parts, 187 nets, no duplicates, no `_1`, no single-pin nets, 3/3 EPs on GND,
  58 driverless nets all correct by construction.
- **Netlist byte-stability.** Audited, identical. See Next phase must #1.
- **Footprint package match.** Every footprint checked by hand against the sourced MPN's
  package, not just against library existence. `validate-footprints.py` being green still
  proves only that paths resolve — that tooling gap is recorded and is not evidence.
- **Anti-alias filter and front-end response.** Recomputed this round *including* the
  divider and the BUFIN node capacitance, which rev.1 omitted: −3 dB at 4.322 MHz (F8 needs
  ≥4 MHz), −30.9 dB at 10 MHz (F9 needs ≥25 dB). Both Sallen-Key sections correctly formed.
  Finding 1 is the only open item in this area; the bandwidth and stopband are settled.
- **Supply spans, signal levels, FPGA bank voltages, rail sequencing.** Settled in rev.1,
  untouched by these changes.
- **TVS polarity, R19 topology, U31 and D101/D201 land patterns.** All verified in the
  netlist this round.

## Receipt

- ERC: **0 errors, 2 warnings** (U5.IN / U6.IN — verified false positives, accepted).
- Rev.1 findings: **4 HIGH + 3 MEDIUM all closed and verified.**
- New: **1 MEDIUM, 2 LOW** — none blocking; the MEDIUM is a SOFT-spec miss I missed in rev.1.
- Circuit: 241 parts, 187 nets, no `_1` refdes, 3/3 EPs netted, netlist byte-stable.
- Status: **PASS.** Export unblocked.
