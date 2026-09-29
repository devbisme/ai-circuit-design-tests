---
phase: 05_coding
agent: skidl-assembler
circuit: dual_adc_usb
written: 2026-09-23T09:20:00Z
status: complete
revision: 1
next_phase: 06_erc
---

# Phase 5 handoff — Assembly

8 blocks, 10 instances, wired from the **final** signatures in `handoffs/05_blocks/*.md`.
No block file was modified. **ERC: 0 errors, 6 warnings.** `validate-bom.py` **FAILS** — six
BOM parts are not instantiated by their blocks (see § Carried forward); that is a block
defect, not a wiring defect, and is not mine to fix.

## Decisions

1. **Every block called by its own handoff's signature, not the architecture's.** Honoured:
   `ch=` (not `tag=`) on `afe_input`/`afe_driver` ×2 each; no `ovra`/`ovrb` on `adc_dual`;
   no `siwu_n` on `usb_bridge`; no `ovra`/`ovrb`/`siwu_n` and `p1v8` added on `fpga_core`;
   `ft_3v3` added on `power_tree`. `tag=` is still passed on all 10 calls as SKiDL's
   hierarchy tag, separately from `ch=`.
2. **`fpga_core`'s open [MED] U15 item is closed by construction.** Its handoff asked:
   "if `power_tree` adds U15, pin 12 must move to its output net." `power_tree` rev.1 did add
   U15 and defines its `p1v8` parameter as **U15's output** (U14's output is the block-internal
   `P1V8_PRE`). One top-level `P1V8` therefore already lands U5 pin 12 on the slew-limited
   rail. **No signature change was needed and none was made.**
3. **`FT_3V3` is one shared top-level net with a single source** — U6 pin 39 in `usb_bridge`.
   `power_tree` senses it for R71 (U9's EN pull-up). No second driver, no local `Net('FT_3V3')`.
4. **`.drive = POWER` set on 7 nets: `P3V3D`, `P1V2`, `VA_POS`, `VA_NEG`, `GND`** (their only
   source in `power_tree` is an inductor/ferrite/resistor pin, so ERC sees no driver), **plus
   `VBUS` and `FT_3V3`** (requested by `usb_bridge`'s handoff: U6 pin 39 is declared `power_in`
   in the symbol although it is the LDO output). **Deliberately NOT set on `P1V8`, `P3V3A`,
   `VBUS_SW`** — `power_tree` states each has a real `power_out` pin there, and the run proves
   it: no drive warning on any of the three.
5. **No net renaming was required.** Every block's parameter mapped onto a `net_plan.md` name
   verbatim; no two blocks disagreed on a net name. `FIFO_SIWU_N`, `ADC_OVRA`, `ADC_OVRB`,
   `LED0`, `LED1`, `CHA_IN`/`CHB_IN`, `P1V8_PRE` are block-internal and are **not** declared at
   top level, as their handoffs require.
6. **Buses, not Nets:** `ADC_DA`/`ADC_DB` = `Bus(...,12)`, `FIFO_D` = `Bus(...,8)`.
7. **Run command uses `python3`, not `.venv/bin/python`** — this project has no `.venv`.
   `rules/environment.md`'s path does not exist here; `python3` carries SKiDL 3.0.0.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/__main__.py` | 36 top-level nets + 2 buses, 10 block calls, `_stabilize_tags()`, ERC, netlist/XML | Always |
| `circuits/dual_adc_usb/__init__.py` | Empty, as required | — |
| `outputs/dual_adc_usb.net` | 163 components, 127 nets | Export review |
| `__main__.erc` / `__main__.log` | Full ERC + netlist output | Verifying my counts |

## Next phase must

Addressed to **erc-reviewer**:

1. **Exact run command** (from the project root, as a module):
```bash
KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python3 -m circuits.dual_adc_usb
```
   There is no `.venv/` in this project — `.venv/bin/python` fails with "No such file".
2. **Known false positives, collected from the block handoffs' `## Carried forward`.** All were
   declared in advance; verify rather than re-derive:
   - **18 intentional `NC` pins on U5** (`fpga_core`): 3, 4, 10, 11, 13–16 (BANK3/1.8 V,
     unusable for 3.3 V signals), 57, 59–62 (MSPI, no external config memory), 82–86.
     `fpga_core` predicted ERC would report all 18; **it reported none** — connecting them to
     the `NC` net exempts them. Nothing to waive.
   - **U4 pins 39 (OVRA), 9 (OVRB), 22 (DVB) `NC`** (`adc_dual`): outputs, deliberately open.
     Over-range retired at architecture rev.3 to close a 2-pin I/O shortfall.
   - **U9.QOD, U15.QOD, U12 pin 4, U14 pin 4 `NC`** (`power_tree`): TI specifies both switches'
     rise times with QOD open; those two numbers are what the sequencing depends on.
   - **J4 A8/B8 (SBU1/2), U6 ACBUS8 `NC`** (`usb_bridge`).
   - **`ADC_CM` carries no resistive load** and only C119/C219 bypass it — by design
     (`afe_driver`); `adc_dual` deliberately provides no CM bypass. Not an omission.
   - **`P1V8`/`P3V3A`/`VBUS_SW` have no `.drive = POWER`** — intentional, per Decision 4.
   - **One `WARNING: Missing tag on  instantiated at <frozen importlib._bootstrap>:491`** during
     netlist generation. I traced it: it is SKiDL's **root hierarchy node** (`name=''`,
     **0 parts**), not a component. All 10 block nodes are tagged and all 163 parts are tagged.
     No component UUID depends on it — see the stability result below. Benign; not fixable from
     `__main__.py`.
3. **Tag stability verified.** Two consecutive runs; netlists diffed ignoring the `(date …)`
   line: **byte-identical**. 163 unique refdes, 0 collisions, no `_1` suffixes.
4. **Re-run `validate-bom.py` yourself** — it exits **1**. See § Carried forward.
5. `validate-footprints.py circuits/dual_adc_usb` exits **0** (59 strings across 9 files
   resolve). It warns this is not a package-variant gate; 8 package notes are open in the BOM
   validator output (J1, J2, X1, U5, J3, J4, L71, L72) — hand-confirm items, not failures.

## Carried forward

**ERC: 0 errors.** No cross-block wiring error exists. The 6 warnings are one root cause:

| Warning (×6) | Attributed block | Note |
|---|---|---|
| `No drivers for net EE_SK` + 2× `Insufficient drive current` (U6 pin 44 EECLK, U7 pin 4 CLK); `No drivers for net EE_CS` + 2× (U6 pin 45 EECS, U7 pin 5 CS) | **`usb_bridge`** (U6, U7 — `03_sourcing.md § Parts by block`) | **Symbol pin-type defect, not a wiring error.** Both ends of each net are declared `INPUT` in their KiCad symbols, so ERC sees no driver. In hardware the FT232H **masters** the 93LC56 bus — EECLK/EECS are outputs. Contrast `EE_DI`, where U6 pin 43 EEDATA is `BIDIR` and no warning appears. Fix is on the `FT232H` symbol (or a targeted `do_erc = False`), inside `usb_bridge`. **`usb_bridge`'s handoff did not declare this** — it reports "instantiates clean" but never ran ERC. New finding. |

**`validate-bom.py` exits 1 — 13 mismatches, 169 BOM refdes vs 163 parts in circuit.** Two kinds:

| Mismatch | Attributed to | Note |
|---|---|---|
| **C514, C515, C516, C517 in BOM, absent from circuit** | **`fpga_core`** | Sourcing rev.4 added these four 100 nF *in response to* the `fpga_core` coder's own "4 × 100 nF short of policy" flag, and `03_sourcing.md § Next phase must` item 2 instructed that coder to wire them at the 2 uncovered U5 VCCIO/VCCX pins and the 2 uncovered VCC-core pins. `fpga_core.md` rev.2 still says "only 7 × 100 nF are sourced" — **written against the stale BOM**. Needs a `fpga_core` re-spawn, not an assembly edit. |
| **C15, C16 in BOM, absent from circuit** | **`afe_buffer`** | `net_plan.md § Decoupling policy` names them explicitly ("U1 (AD8066): C15 = 100 nF on `VA_POS`, C16 = 100 nF on `VA_NEG`, at the pins"), the `VA_POS`/`VA_NEG` rows list them, and `03_sourcing.md` assigns both to `afe_buffer`. `afe_buffer.md` Decision 5 asserts "the BOM assigns U1 none" and cites net_plan lines 20/22 — **it read the rev.2 text; rev.3 added them.** U1 currently has no HF bypass on either rail. Needs an `afe_buffer` re-spawn. |
| **7 symbol/footprint placeholder cells** — U1, U4, X1, U5, U9, U12 `SYMBOL NEEDED`; U5 `CUSTOM FP NEEDED` | **sourcing (`part-sourcer`)** | BOM side is stale: the symbols were generated at phase 4 and the code uses the real names (`dual_adc_usb:AD8066ARZ-R7`, `ProjectLocal:QFN-88-1EP_10x10mm_P0.4mm_Gowin_QN88P`, …). **The code is right; the BOM cell is wrong.** Do not "fix" by editing the code. |

- `afe_input`'s declared D101/D201 `Diode:BAV19` → `BAV99` BOM drift **no longer appears** — the
  BOM cell was corrected. Closed.
- `power_tree`'s 5 standalone-test warnings (`P1V8`, `PWREN_N`, `FT_3V3` one-pin nets) are
  **gone**, as predicted, now that the blocks are connected.
- Still open from the blocks, unchanged by assembly: `power_tree` **[HIGH]** U15 ON-pin tie
  outside TI's characterized condition (bench-verify VCCIO3 rise ≥180 µs monotonic);
  `power_tree` **[MED]** 4 × 100 nF missing at U9/U10/U11/U12 VIN (U12 is the one worth
  arguing — analog LDO between two 1.5 MHz switchers); `afe_driver` ADC headroom at the window
  edge; `net_plan.md` FT232H pin-numbering defect (docs only).

## Do not redo

- Block-internal design, sourcing and footprints — all settled in `05_blocks/*.md`.
- The `tag` → `ch` rename on `afe_input`/`afe_driver` (forced by SKiDL semantics).
- The OVRA/OVRB/SIWU_N retirements and the `p1v8`/`ft_3v3` additions.
- `P1V8` = U15's output (Decision 2) — `fpga_core` needs no signature change.
- The FDA→ADC polarity crossing, `ADC_SEL` as a driven pin, the BANK3/pin-12 rail resolution.

## Receipt

- **8 blocks, 10 instances** (`afe_input` ×2, `afe_driver` ×2, 6 singletons); all tagged.
- **163 parts, 127 nets** in the netlist; 36 top-level nets + 2 buses declared; 0 refdes collisions.
- **ERC: 0 errors, 6 warnings** — all 6 the `EE_SK`/`EE_CS` no-driver pair, attributed to `usb_bridge`.
- **Netlist stable:** two runs byte-identical ignoring `(date …)`.
- `validate-footprints.py` **exit 0**; `validate-bom.py` **exit 1** (6 BOM parts not in circuit,
  7 stale BOM symbol/footprint cells).
- **ERC PASS / BOM gate FAIL.** No block file modified.
