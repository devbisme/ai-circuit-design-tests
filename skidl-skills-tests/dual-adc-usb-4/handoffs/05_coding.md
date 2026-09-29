---
phase: 05_coding
agent: skidl-assembler
circuit: dual_adc_usb
written: 2026-09-10T23:37:14Z
status: complete
revision: 1
next_phase: 06_erc
---

# Phase 5 handoff — Coding (assembly)

## Decisions
- **Each of the 9 blocks is called by the signature in its own `handoffs/05_blocks/<id>.md`.** All 9 report "signature changed: no", and each matches the `02_architecture.md` manifest. Every call is by keyword with `tag='<block_id>'`. No block is repeated, so no `ch=` instance argument is needed.
- **Net names are verbatim from `architecture/net_plan.md`** (UPPER_SNAKE, including the signal nets). The net plan's exact names outrank the camelCase convention. No net was renamed and no block pair disagreed on a name.
- **Buses are shared single objects:** `ADC_DA = Bus('ADC_DA',12)` and `ADC_DB = Bus('ADC_DB',12)` go to adc and fpga_core, and `FT_D = Bus('FT_D',8)` goes to usb_bridge and fpga_core. Index 0 is the LSB, and the nets come out as `ADC_DA0…11`, `ADC_DB0…11` and `FT_D0…7`.
- **`.drive = POWER` is set at top level on all 8 supply nets:** GND, VBUS_SW, VD_3V3, VD_1V8, VD_1V2, VA_3V3, VA_P2V5 and VA_N2V5. GND needs it: no block drives it, and it carries power_in pins. The other 7 are already driven inside their source blocks (usb_power_in, power_rails, bipolar_supply). The top-level setting repeats that on purpose, per the assembler rule "every supply net", so a rail keeps its drive even if a block edit drops it.
- **Search paths are set in `__main__.py`, not through the environment.** SKiDL 3.0.0 defaults to tool `kicad10` and does not split `KICAD9_SYMBOL_DIR` on colons, so `__main__.py` appends `<root>/symbols` to `lib_search_paths[get_default_tool()]`. It also appends `<root>/footprints/ProjectLocal.pretty` to `footprint_search_paths`: a directory with no fp-lib-table is loaded as one library named after its basename (`ProjectLocal`), see `skidl/part_query.py:694`.
- **MPN/LCSC post-pass (`_export_sourcing_fields()`):** before ERC, each part's `MPN`/`LCSC` attribute is copied into `part.fields` wherever the field is missing. It filled 111 MPN and 113 LCSC fields. Fields the blocks had set explicitly (analog_front_end) are left alone.
- `_stabilize_tags()` runs before `ERC()`, as in the template. Outputs go to `outputs/dual_adc_usb.net` and `outputs/dual_adc_usb_bom.xml`.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/__init__.py` | empty package marker | never |
| `circuits/dual_adc_usb/__main__.py` | path setup, 68 interface nets (3 buses), 9 block calls, field post-pass, ERC, netlist/XML export | running ERC; any inter-block wiring error |
| `outputs/dual_adc_usb.net` | KiCad netlist, 201 components, 168 nets | footprint validation, netlist review |
| `outputs/dual_adc_usb_bom.xml` | BOM XML | BOM checks |

## Next phase must
1. **erc-reviewer:** run from the project root:
   `KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols" python3 -m circuits.dual_adc_usb`
   This project has **no `.venv/`**, so `.venv/bin/python` does not exist. `python3` is pyenv 3.14.6 with SKiDL 3.0.0 from `~/projects/KiCad/tools/skidl/src`. The env var is harmless but not needed, because `__main__.py` appends the paths itself.
2. Expect **0 ERC errors and 0 ERC warnings**, plus one netlist/XML warning: `Missing tag on  instantiated at <frozen importlib._bootstrap>:491`. **This is a false positive.** It comes from the circuit's root node, which `Circuit.__init__` (`skidl/circuit.py:172`) creates with `tag=""`, and `check_tags()` then flags it. It is not a block or a part. Its tag_or_name is `""` on every run, so it does not affect stability, and the two-run netlist diff passed.
3. **Treat these intentional no-connects as false positives** if a stricter check flags them (each comes from a block's `## Carried forward`):
   - **adc:** U12.DVB (pin 22). Channel B data is captured on DVA, since both channels share one clock. RN7 element 4 (pins 4 and 5) is a spare.
   - **fpga_core:** U15 pins 3, 10 (DONE), 11, 13, 14, 15, 16, 84, 85, 86 are unused bank-3 pins, NC per net_plan §8.
   - **io_expansion:** U17 pin 1 has no internal connection.
   - **power_rails:** pin 4 of U4, U5 and U6 is the NC pin on TLV755xx/TPS7A20.
   - **usb_bridge:** U13 ACBUS8/9 (pins 32 and 33), NC per net_plan §7.
   - **usb_power_in:** J1 SBU1/SBU2, unused on a USB2 sink.
4. **Blind spots ERC cannot see (these are not errors):**
   - Seven passive-fed local rails get forced `.drive = POWER` inside their blocks, so ERC will never report them undriven: ADC_AVDD and ADC_VDRV (adc, via FB6/FB5), OSC_VDD (sample_clock, FB7), FT_VPHY (usb_bridge, FB8), CP_VIN (bipolar_supply, FB2), and VBUS and VBUS_F (usb_power_in).
   - Pin types were corrected on individual instances: U12 CLK becomes input and DVA/DVB become outputs (adc); U13 pin 37 VCCA becomes power_in (usb_bridge).
   - Every U15 I/O is typed BIDIR, so ERC cannot check any FPGA-side direction. No open-drain nets and no deliberate multi-driver nets are declared.
5. Validate footprints on the assembled netlist, not on the block sources. analog_front_end keeps its footprint strings in constants, so `validate-footprints.py` reports "0 checked" for it. I checked all 29 unique footprint strings in the netlist: every one resolves to a `.kicad_mod`, 2 of them in `footprints/ProjectLocal.pretty`.

## Carried forward
- **ERC errors: none.** Nothing to attribute to a block.
- **Direction disagreement on ADC_DVA (no ERC effect).** Attributed to `fpga_core` (documentation only).
  - The adc handoff and net_plan §5 say U12 drives ADC_DVA, the ADC's data-valid output. The fpga_core handoff lists `adc_dva` as an FPGA *output*.
  - U15 pin 72 is BIDIR, so ERC is silent. Gateware must configure pin 72 as an **input**. If it were an output it would fight U12 through RN7.
  - The wiring itself is correct (RN7.6 to U15.72), so the schematic needs no change.
- **Missing MPN fields, as sourced:** J4 and J5 are generic headers with LCSC numbers only (C492406 and C37208). TP1–TP10 are bare test pads with neither MPN nor LCSC. This matches `03_sourcing.md` § Parts by block and is not an assembly defect.
- **The BOM XML is not byte-stable, but the netlist is.** Across two runs, `dual_adc_usb_bom.xml` differs only in the order of `<node>` lines within some nets; the sorted content is identical. My unverified guess is hash-randomized set iteration in SKiDL's XML generator. This is a SKiDL issue, not a design issue.
- Block-level open items are unchanged and still bind. They are listed in each block handoff (X1 jitter, the adc REFT/REFB bulk caps, the U12 symbol pin-type defect, MODE/TCK straps `[VERIFY UG290]`, FT232H EEPROM programming, and the J2/J3/VC1/VC2 footprint rows in `sourced_bom.md`).
- Block coders left stray empty files in the project root: `probe_afe.*`, `t_fpga.*`, `skidl_REPL.*`, `skidl_REPL_sklib.py`. I left them in place.

## Do not redo
- Block-internal design, part choices, sourcing and footprints (see each `handoffs/05_blocks/*.md`).
- The net names and bus objects in `__main__.py`, which match net_plan exactly. Every one of the 68 interface nets touches at least 2 blocks, and none is single-node.
- Tag stability. Two runs gave netlists identical except for the `(date …)` line.

## Receipt
- Blocks: 9. Parts: 201 (13+21+18+48+30+7+27+24+13). Nets: 168 (68 interface).
- ERC: 0 errors, 0 warnings. Netlist: 0 errors, 1 warning (the SKiDL root-node tag, a false positive).
- Netlist stable across 2 runs. MPN/LCSC fields exported (J4/J5/TP1–TP10 lack MPN, as sourced). Footprints 29/29 resolve.
- PASS.
