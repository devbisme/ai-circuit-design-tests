---
phase: 06_review
agent: erc-reviewer
circuit: dual_adc_10msps
written: 2026-10-17T07:30:00Z
status: complete
revision: 1
next_phase: physical
---

# Phase 6 handoff — Review

## Decisions
1. **PASS.** 0 SKiDL / 0 KiCad ERC errors, parity 217/217, `boardforge review` WARN (0 FAIL), BOM PASS, components/nets stable, no HIGH checklist finding.
2. **The 12 `ac_gain` constraints were evaluated, not waived.** boardforge's `spice_path.check` was run on `build/netlist.json`, with one change: the OPA2810 custom-symbol pin names `VIN1±/VO1/VIN2±/VO2` were added to its op-amp role tables. Result: 12/12 PASS. GAIN -20.87 dB; ALIAS@5 MHz -80.86 dB (limit -72); @10 MHz -123.3 dB. Both channels give the same values, and `architecture/afe_nominal.cir` matches. Evidence: `build/reports/spice_patched/` (script, results.txt, .cir per constraint).
3. **No `[review.models]` entry was added**, because one cannot fix this: `pins` maps one role set per part, and the OPA2810 is a dual whose units the tool fails to split. The cause is `role_is_out`/`OPAMP_ROLES` not recognising `VO1`/`VIN1+` names. Models and GBW were never missing.
4. Accepted coder claims: the intentional NC list, the SUSPEND→GND tie, the lib_symbol_mismatch warnings, and "symbol pin order only" netlist drift (verified: components/nets/UUIDs identical). Rejected: "SPICE NOT CHECKED = model coverage" (see 3).
5. Dispositioned as acceptable (SOFT): W2 AVDD/VDRV power-up skew (~0.65 ms, within TI's ±10 ms recommended skew) and W3 FT232H VREGIN 3.318 V nominal against its 3.3 V minimum.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `review_report.md` | Gate summary, SPICE table, findings W1–W3 / N1–N9, false-positive dispositions | Always |
| `build/reports/spice_patched/results.txt` | Re-evaluated `ac_gain` results | Checking the anti-alias evidence |
| `build/reports/spice_patched/patched_spice.py` | Reproducer: `~/.local/share/uv/tools/boardforge/bin/python3 -I <it> <project> <outdir> --patch` | Re-running after an AFE change |
| `build/reports/review.json`, `erc.json`, `skidl.log` | Official gate output | Detail |

## Next phase must
1. The physical pipeline is unblocked: `boardforge run --from c2`.
2. Optional, not blocking. Make the official gate show these PASS results, either with a boardforge upstream fix (any `output`-type pin in a unit counts as `out`; accept `VIN\d[+-]`, `VO\d`), or by having datasheet-librarian rename the OPA2810IDR unit pins to `+`/`-`/`~` while the afe_channel skidl-block-coder switches U101/U201 to pin numbers. After either change, re-run `boardforge review`.
3. Optional (circuit-architect, W2): tie U701 EN to `+3V3` instead of `+5VA` to sequence AVDD after VDRV's source.

## Carried forward
- `review.json` still lists 12 `ac_gain` NOT CHECKED until W1 is fixed. The evidence is in `build/reports/spice_patched/`. The models are 1-pole behavioral with ideal Zout, the clamps (D101/D201) and the ADC input (U301) are left open, and the gate runs nominal values only (the architect's MC worst case was -78.7 dB).
- W2: the ADS5231 AVDD/VDRV ±0.3 V abs max is exceeded briefly at power-up, and the ramps are under TI's recommended 10 ms.
- W3: FT232H VREGIN is at its 3.3 V minimum.
- DS:coverage: PSC-1608U52GC-G4 (OK by hand) and TXM12M0004252FBCEO00T (Y901: no datasheet, pinout UNVERIFIED, ±40 ppm vs FTDI's ±30 ppm), so eyeball Y901 before fab.
- Custom footprints: `my_board:BNC_KH-BNC50-3511` (J101/J201) and `my_board:C_Trimmer_SEHWA_STC3MA06` (C102/C202). Check them against their mech drawings before fab.
- Gateware: ADS5231 DISABLE_PLL write (10 MSPS is outside the default PLL range of 20–40 MSPS); FT232H EEPROM 245-sync with ACBUS7 suspend off; FPGA UCF as in `fpga.md`.
- J1002 TRIG_IN has no clamp (N3). SX3M jitter is unspecified.

## Do not redo
- ERC classification, parity, BOM (PASS), all DS:/PKG:/rail_current checks (PASS).
- Hand checks: FPGA bank-by-bank VCCO = +3V3, signal levels, ADC input abs max, THS4551 input CM, enable/reset/config straps, SDRAM JEDEC pinout, supply spans.
- Netlist stability (components/nets identical across two runs).

## Receipt
ERC: SKiDL 0 E / 1 W; KiCad 0 E / 259 W (accepted); parity 217/217 ok.
Review: 43 PASS / 0 FAIL / 13 NOT CHECKED; HARD fails 0; BOM PASS.
ac_gain re-evaluated with a pin-alias patch: 12/12 PASS (ALIAS @5 MHz -80.9 dB ≥72 dB req).
Findings: 0 HIGH, 3 MEDIUM (W1 tool, W2/W3 architect SOFT), 9 notes. Result: PASS.
