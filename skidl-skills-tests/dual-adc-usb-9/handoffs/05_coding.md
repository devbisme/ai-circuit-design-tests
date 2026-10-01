---
phase: 05_coding
agent: skidl-assembler
circuit: dual_adc_usb
written: 2026-10-01T03:29:00Z
status: complete
revision: 1
next_phase: 06_erc
---

# Phase 5 handoff — Coding (assembly)

## Decisions
- All 9 block handoffs declare "Signature changed: no"; every call uses the exact kwargs from each block's `## Next phase must`. No signature or net-name disagreements found, no nets renamed.
- Net names match `architecture/net_plan.md` §1 exactly (31 interface nets incl. buses `ADC_DA`[12], `ADC_DB`[12], `FT_D`[8]). Python vars V3V3D/V1V2/V1V8/V3V3A map to nets `+3V3D`/`+1V2`/`+1V8`/`+3V3A`.
- `.drive = POWER` at top level on **GND only** (no pin drives ground). Not set on: VBUS_SW (U2.VOUT PWROUT, per usb_power_in), +3V3A/VAFE_P/VAFE_N (U5.OUT, U6.OUT+/- PWROUT, per pwr_analog), +3V3D/+1V2/+1V8 (set inside pwr_digital because buck SW reaches rail via inductor).
- `__main__.py` appends `<project>/symbols` to `lib_search_paths[KICAD]` (coders reported KICAD9_SYMBOL_DIR alone was overridden) and `<project>/footprints` to `footprint_search_paths[KICAD]` (guarded). ProjectLocal fp-lib registration not needed by SKiDL netlisting; footprint string `ProjectLocal:KH-BNC50-3511` is emitted verbatim for J2/J3.
- Each block call carries `tag='<block_id>'`; `_stabilize_tags()` runs before `ERC()`. No repeated blocks (afe_ch_a/afe_ch_b are distinct functions with fixed refs), so no `ch=` arg.
- Netlist + XML BOM written to absolute `outputs/` paths under the project root.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/__init__.py` | empty | never |
| `circuits/dual_adc_usb/__main__.py` | nets, 9 block calls, ERC, netlist/XML | always |
| `outputs/dual_adc_usb.net` | KiCad netlist (169 comps, 130 nets) | footprint/export checks |
| `outputs/dual_adc_usb_bom.xml` | XML BOM | BOM checks |
| `outputs/run1.log`, `outputs/run2.log` | full stdout of both runs | to confirm ERC output |
| `__main__.erc` (project root) | SKiDL ERC log | to confirm ERC output |

`outputs/run1.net` is a stale copy of run 1 used for the stability diff (protected dir; could not delete). Ignore it.

## Next phase must
1. erc-reviewer: run from project root:
   `KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python -m circuits.dual_adc_usb`
   (no `.venv` exists in this project; system `python` has SKiDL 3.0.0 from `/home/devb/projects/KiCad/tools/skidl/src`).
2. Expected result: `ERC INFO: No errors or warnings found`, plus one netlist/XML "Missing tag on <blank> instantiated at <frozen importlib._bootstrap>" warning. That is the unnamed root hierarchy node created by `python -m`; no random tag is generated and the netlist is stable (two runs diff empty apart from `(date …)`).
3. Intentional NC pins (all explicitly NC in blocks; verify they stay NC):
   - usb_power_in: J1 SBU1/SBU2 (A8/B8), USB 2.0 only.
   - pwr_analog: U5 pin 4 (symbol NC pin).
   - adc_dual: U7 pins 9 OVRB, 22 DVB, 26 DVA, 39 OVRA (outputs, removed from FPGA I/O budget, net_plan rev 2).
   - clock_gen: U8 pin 1 (symbol NC).
   - fpga: U9 pins 3, 10, 11, 13-16, 79-86 (unused bank-3 user I/O).
   - usb_bridge: U10 ACBUS7/8/9 (unused in 245 FIFO mode).
4. Deliberate tie-offs/overrides to accept: LM27762 (U6) PGOOD tied to GND (per datasheet when unused); U10 VCCA retyped PWRIN and EECS/EECLK retyped OUTPUT inside usb_bridge (symbol type fixes); ADC_VCM single driver U7.CM, THS4521 VOCM inputs only; FT_D / USB_DP / USB_DM bidirectional on both ends (FPGA and FT232H pins typed BIDIRECTIONAL). No open-drain or multi-driver nets.
5. Footprint check: J2/J3 use `ProjectLocal:KH-BNC50-3511` at `footprints/ProjectLocal.pretty/KH-BNC50-3511.kicad_mod`; register a `ProjectLocal` fp-lib entry if your validator needs it.

## Carried forward
- ERC: 0 errors, 0 warnings — nothing to attribute.
- **BOM gate (`validate-bom.py`) FAILS on 10 value-field mismatches**, all block-internal (refs and footprints agree, 169 = 169). The driver must route each mismatch to the block owner or the part-sourcer. Do not fix these here.
  - usb_power_in: J1 'USB-C' vs BOM 'USB-C 16P'
  - clock_gen: U8 '74LVC1G34' vs 'SN74LVC1G34DCKR'
  - fpga: U9 'GW1NR-LV9QN88PC6' vs 'GW1NR-LV9QN88PC6/I5'; J4 'JTAG' vs '1x6'; J5 'TRIG' vs '1x3'
  - usb_bridge: U10 'FT232HL' vs 'FT232HL-REEL'; U11 '93LC56B' vs '93LC56BT-I/OT'; C110/C111 '33pF C0G' vs '33pF'; R100 '12k 1%' vs '12k'
  - Also informational `?` lines: U9, J4, J5 package not evident in footprint name. Confirm by hand.
- Block-level open items still apply (see each `handoffs/05_blocks/*.md` § Carried forward): BNC footprint geometry, C21/C41 trimmer and L1-L3/Y1/U9 land patterns to verify at layout, keystone assumptions K3/K5/K10, U9 EP = GND.

## Do not redo
- Block-internal design, part values, sourcing, footprints and pin maps (owned by block handoffs and `handoffs/03_sourcing.md`).
- Net naming and power-drive placement above.

## Receipt
- 9 blocks assembled; 169 parts (matches BOM refdes count), 130 nets, 0 single-node nets.
- ERC: 0 errors, 0 warnings. PASS.
- Netlist stable across two runs (diff empty except date).
- validate-bom.py: FAIL, 10 value mismatches in usb_power_in, clock_gen, fpga, usb_bridge (block/sourcing, not wiring).
