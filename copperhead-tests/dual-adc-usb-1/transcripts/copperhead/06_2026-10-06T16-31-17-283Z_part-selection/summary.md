# Run summary

- **Request:** create pipeline stage: part-selection
- **Outcome:** success
- **OpenSpec change:** part-selection-bom
- **Tokens:** 74 in / 44333 out

## Environment

- **Run:** 2026-10-06T16-31-17-283Z · create · started 2026-10-06T16:31:17.302Z · autonomous
- **Stage:** part-selection (3/8)
- **Brief:** dual-adc-prompt.txt (sha256 6fda2f5a66e9…)
- **Model:** claude-code (claude-code, via flag)
- **copperhead:** v0.11.0 at /home/devb/.nvm/versions/node/v22.23.3/lib/node_modules/copperhead
- **Tooling:** kicad-cli 9.0.9 · node v22.23.3 · linux-x64
- **Config:** schematic null · board null · docs docs/ · maxTurns 40 · maxRepairCycles 5 · budgets {}
- **Repo:** master@207d7c64c0ae3bb8d37d46a4e52318a15ac8a1a0 · clean · pre-commit hook absent
- **Memory:** 20 open constraint(s) · 7 prior run(s)

## Run stats

- **Exit path:** done
- **Turns:** 37 / 40
- **Repair cycles:** 0 / 5
- **Tokens:** 74 in / 44.3k out
- **Duration:** 9m14s
- **Per turn:** 1: 2/134 · 2: 2/1531 · 3: 2/308 · 4: 2/397 · 5: 2/267 · 6: 2/362 · 7: 2/350 · 8: 2/500 · 9: 2/546 · 10: 2/580 · 11: 2/598 · 12: 2/309 · 13: 2/337 · 14: 2/210 · 15: 2/368 · 16: 2/560 · 17: 2/181 · 18: 2/175 · 19: 2/292 · 20: 2/300 · 21: 2/634 · 22: 2/118 · 23: 2/225 · 24: 2/321 · 25: 2/248 · 26: 2/711 · 27: 2/910 · 28: 2/593 · 29: 2/792 · 30: 2/577 · 31: 2/2220 · 32: 2/6189 · 33: 2/56 · 34: 2/19158 · 35: 2/175 · 36: 2/1345 · 37: 2/1756

## Plan

Following the recovery guidance, I'll start by reading the existing docs/BOM.md and repair it in place rather than start over.

## Files touched

- docs/BOM.md
- docs/DECISIONS.md

## Verification

- ERC: not run
- DRC: not run
- legibility: not run
- score: not run

## Decisions

- ADC: LTC2290 (dual simultaneous 12-bit 10 MSPS, Analog_ADC:LTC2290xUP, UNVERIFIED) replaces the AD9238-class candidate, which has no installed symbol. It runs on 3.3 V VDD, so the 1V8_A rail becomes 3V3_ADC, a low-noise LDO from VBUS_SW. 1V8_D is kept for OVDD and the FPGA ADC bank. Supporting substitutions: 93LC56B on Memory_EEPROM:93LCxxB; 2x 74CBTLV3861 instead of one 16-bit CBT; TPS22917 load switch with a BSS84 P-FET inverter from PWREN_N (no conducting pull on 3V3_AON). analog.dc_accuracy is NOT accepted as met: the LTC2290's expected uncalibrated offset (mV class) and gain error (~1.5 %) exceed the 0.9 mV / 0.5 % ADC allocations in SUBSYSTEMS §7.6. This is flagged as a BLOCKER that needs a user decision: (a) revise the ASSUMED limit to apply after calibration, or (b) install an ADC symbol library with a better part. | why: It is the only installed dual simultaneous 12-bit >=10 MSPS symbol. Every other installed candidate is 8-bit or <=1 MSPS. The budget conflict is surfaced rather than silently exceeded.
