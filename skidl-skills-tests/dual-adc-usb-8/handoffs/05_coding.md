---
phase: 05_coding
agent: skidl-assembler
circuit: dual_adc_usb
written: 2026-09-26T15:10:00Z
status: complete
revision: 1
next_phase: 06_erc
---

# Coding handoff (assembly) — dual_adc_usb

## Decisions
- All 9 blocks are called with the exact signatures in their `handoffs/05_blocks/*.md`. None of the blocks declared a signature change. No net renames were needed: every interface net name matches `architecture/net_plan.md` § 1.
- **usb_bridge takes `v5=V5`** (driver decision: the FT232H runs 5 V-in with its internal VCCD 3.3 V on the block-local FT_3V3). This supersedes net_plan's "U10 … on V3V3D". V3V3D now feeds only fpga and power_digital loads.
- `.drive = POWER` is set at top on **GND, V5, V3V3D, V1V2, V1V8, V3V3A, VP_AFE, VN_AFE**:
  - V3V3D and V1V2 are required: they are inductor-fed (L1/L2 passive), per power_digital.
  - GND is required by every block.
  - V5, V1V8, V3V3A, VP_AFE and VN_AFE are already driven by PWROUT pins (U2.VOUT, U5.OUT, U6.OUT, U7.OUT±). Setting drive on them is harmless and keeps the rail valid if a block is run alone.
- **VCM has no drive override.** It is driven by U8.CM (OUTPUT, adc block). ERC confirmed it is clean with that alone.
- Buses: `DA = Bus('DA',12)` and `DB = Bus('DB',12)` are shared by adc and fpga. `FT_D = Bus('FT_D',8)` is shared by fpga and usb_bridge. Index 0 is the LSB in each.
- Each block is called once with `tag='<block_id>'`. afe_ch_a and afe_ch_b are separate functions with fixed refdes (1xx/2xx), so no `ch=` argument is used.
- `_stabilize_tags()` is called before `ERC()`.
- **Netlist-stability fix (in `__main__.py` only):** SKiDL 2.3 stores hierarchy nodes in a `set`, so the `(sheet …)` list order changed from run to run even though tags and tstamps were stable. `_stabilize_tags()` now overrides `default_circuit.get_node_names` to return the nodes sorted by path. After this fix, 3 runs produce identical netlists apart from the `(date …)` line.
- ProjectLocal footprint dir `footprints/` is appended to `footprint_search_paths[KICAD9]` in `__main__.py`.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/__init__.py` | empty package marker | — |
| `circuits/dual_adc_usb/__main__.py` | nets, 9 block calls, ERC, netlist/XML generation | ERC run / rework |
| `outputs/dual_adc_usb.net` | KiCad netlist | Export / layout |
| `outputs/dual_adc_usb_bom.xml` | XML BOM | BOM review |
| `outputs/run3.txt` | full ERC + generation log | ERC review |
| `outputs/validate_bom.txt` | validate-bom.py output (exit 1) | BOM gate routing |

## Next phase must
1. Run from the project root. There is no `.venv` in this project, so use the pyenv `python3` (SKiDL 2.3.0):
   `KICAD_SYMBOL_DIR=/usr/share/kicad/symbols KICAD9_FOOTPRINT_DIR=/usr/share/kicad/footprints KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python3 -m circuits.dual_adc_usb`
2. Known false positives (all are warnings; ERC reports 0 errors):
   - **FT_EECS / FT_EECLK: 6 warnings**, "No drivers" plus "Insufficient drive" on U10 pins 44/45 and U11 CS/CLK. The KiCad `Interface_USB:FT232H` symbol types EECS/EECLK as INPUT, but on the chip they are FT232H outputs (usb_bridge).
   - "Missing tag on  instantiated at <frozen importlib…>" during netlist generation. This is SKiDL's root hierarchy node, which has an empty name and tag. No random tag is generated, and the root sheet tstamp is "/". Benign.
   - Possible "no driver" on the passive/INPUT-only local nets listed by the block coders. None appeared in this run:
     - FB33, FB12 (power_digital)
     - LM_FBP, LM_FBN (power_analog)
     - ADC_REFT_C, ADC_REFB_C, ADC_ISET (adc)
3. Intentional NC pins, collected from the block handoffs:
   - J1 A8/B8 SBU and U2.4 (usb_power_in)
   - U5.4 (power_digital)
   - U6.4 (power_analog)
   - U8 DVB(22), OVRA(39), OVRB(9) (adc)
   - U9 3, 4, 10, 11, 13–16, 79–86, and J4 pins 7/8 (fpga)
   - U10 ACBUS7/8/9 (usb_bridge)
4. **BOM gate: `validate-bom.py` exit 1** with 9 value-cell mismatches. Symbols, footprints and refdes all agree: 170 in the BOM and 170 in the circuit. The driver must decide which side is correct. They are cosmetic value strings, not wiring:

   | Ref | Block | BOM value | Code value |
   |---|---|---|---|
   | FB1 | adc | `600R` | `600R@100MHz` |
   | X1 | clock | `SX3M40.000B10F20TNN` | `40MHz` |
   | FB2 | clock | `600R` | `600R@100MHz` |
   | J4 | fpga | `Conn_02x05` | `JTAG` |
   | J5 | fpga | `Conn_01x06` | `AUX` |
   | Y1 | usb_bridge | `X322512MSB4SI` | `12MHz X322512MSB4SI` |
   | R25 | usb_bridge | `12k` | `12.0k 1%` |
   | FB3 | usb_bridge | `600R` | `600R PBY160808T-601Y-N` |
   | FB4 | usb_bridge | `600R` | `600R PBY160808T-601Y-N` |

   The simplest fix is for part-sourcer to adopt the BOM values or the block coders to adopt them; either one closes the gate. The assembler did not edit either side.
5. validate-bom also printed 15 "package not evident" notes. These are not failures. Confirm them by hand at footprint review.

## Carried forward
- **ERC errors: none.** No block rework is attributed.
- Upstream open items remain open and were not re-decided:
  - X1 jitter is unverified (clock).
  - The sync-245 ACBUS map, Y1 CL and the 93LC56B x16 choice are unverified (usb_bridge).
  - The PSRAM bank-3 / MODE2 assumptions and the J4 JTAG pinout vs the Gowin cable are unverified (fpga).
  - The BNC footprint must be verified against KH-801-0038 before fab (afe_ch_a/b).
  - VBUS transients above 6 V exceed U2's abs max (usb_power_in).
- The BOM value mismatches in the table above gate the pipeline until they are resolved.

## Do not redo
- Block-internal design, sourcing and footprints.
- The drive=POWER set. VCM correctly has none.
- The netlist-stability fix. It is verified over 3 runs.

## Receipt
- Blocks: 9. Parts: 170. Nets: 129 (incl. bus bits and block-local nets).
- ERC: 0 errors, 6 warnings (all FT_EECS/FT_EECLK symbol-typing false positives). **PASS**.
- Netlist is stable across 3 runs (only the `(date …)` line differs).
- validate-bom.py exit 1: 9 value-cell mismatches (adc 1, clock 2, fpga 2, usb_bridge 4).
