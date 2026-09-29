---
phase: 05_coding
agent: skidl-assembler
circuit: dual_adc_usb
written: 2026-09-20T23:40:00Z
status: complete
revision: 1
next_phase: 06_erc
---

# Phase 5 handoff — Assembly (`circuits/dual_adc_usb/__main__.py`)

**0 ERC errors, 19 ERC warnings, all 19 on block-INTERNAL nets.** No warning lands on any
inter-block net, so the top-level wiring is clean; nothing here is attributable to
`__main__.py`.

## Decisions

1. **No signature disagreement had to be resolved.** All 8 block handoffs are
   `status: complete`; the only deviation from `handoffs/02_architecture.md` rev 2 is
   `afe_channel(..., ch=1|2)`, called twice as its handoff dictates (ch=1 → AIN1/CH1_P/CH1_N,
   ch=2 → AIN2/CH2_P/CH2_N). Every other call is the keyword form its own handoff printed,
   verbatim. Python variable names differ cosmetically from the handoff snippets
   (`V5V_IN` vs `V5_IN`); the **net names** are `net_plan.md` exact (`+5V_IN`, …).
2. **Net names taken from `architecture/net_plan.md` verbatim**, including the `+` prefixes.
   `ADC_D1`/`ADC_D2` are `Bus(...,12)`, `FIFO_D` is `Bus(...,8)`. SKiDL 3.0 names bus nets
   `ADC_D1_0…ADC_D1_11` / `FIFO_D0…FIFO_D7` — verified U5 → RA1–RA6 → U6 is continuous on
   all 24 ADC lines and U6 ↔ U7 on all 8 FIFO lines.
3. **`.drive = POWER` set on:** `GND`, `+5V_IN`, `+5V_SW`, `+3V3_D`, `+3V3_ADCD`, `+3V3_A`,
   `+1V2_D`, `VBIAS`, `VREF_FE`. Rationale: each is fed either from a connector/passive pin
   (`+5V_IN` via FB1, `+3V3_D` via L1, `+3V3_ADCD` via FB2, **`VBIAS` via R22** — the
   architecture-rev-2 isolation resistor) or from a regulator/op-amp output the KiCad symbol
   types as passive (`+3V3_A`, `+1V2_D`, `VREF_FE`). `+5V_SW` now comes from U9 pin 1, a real
   `power_out` pin, so its flag is redundant — kept as a one-line no-op so the rail tree is
   uniform; removing it changes nothing.
4. **`VOCM` deliberately has NO drive flag and no second source** (`adc_dual` decision 3):
   U5.CM is its only driver. Confirmed 5 pins — U5, C54, C55, U_fda1, U_fda2.
5. **`VBUS_RAW` is not a top-level net** (`usb_c_input` decision 2) — it stays internal, as
   do `VBIAS_DRV`, `FT232H_3V3`, `XO_VDD`, `V5_LDO_IN`, `EE_CS/EE_CLK/EEDATA`, `SHIELD`,
   `CC1/CC2`, `BUCK_LX`, `TRIG_*`. None were created or passed.
6. **`R13` needed no action.** `fpga_core` item 3 asked the assembler to place it; `usb_bridge`
   decision 8 already instantiates it (2.2 kΩ series EEDATA→DO, plus `R_eedo` pull-up). No
   duplicate ref exists — 169 distinct refs, zero SKiDL `_1` uniquified names.
7. **Root-node tag left untagged on purpose.** `_stabilize_tags()` tags every part from its
   refdes; the lone remaining "Missing tag" line is the *unnamed root hierarchy node*. Tagging
   it makes `generate_netlist()` raise (`kicad10/gen_netlist.py` asserts the top hierarchy
   level is an empty string). `check_tag(create_if_missing=False)` for nodes means no random
   tag is invented, and the netlist is provably stable (below).
8. **Netlist stability verified**: two consecutive runs are byte-identical except the
   `(date …)` line (`diff` = 0 lines).

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/__main__.py` | 30 top-level nets + 3 buses, 9 block calls, tags, ERC | Always |
| `circuits/dual_adc_usb/__init__.py` | Empty (package marker) | Never |
| `outputs/dual_adc_usb.net` | KiCad netlist, 169 parts / 146 nets | Reviewing connectivity |
| `outputs/dual_adc_usb_bom.xml` | BOM XML | BOM reconciliation |
| `__main__.erc` (project root) | The 19 ERC warnings verbatim | Classifying ERC output |

## Next phase must

1. **Run exactly this** (project root, as a module). **There is no `.venv/` in this project** —
   the interpreter with SKiDL 3.0.0 is the pyenv `python3` (3.14.6), the same one that
   produced the blocks' `__pycache__`:
   ```bash
   KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python3 -m circuits.dual_adc_usb
   ```
   `symbols/` is mandatory — U5, U6, X1 and J1 are generated symbols in
   `symbols/dual_adc_usb.kicad_sym`. `KICAD_SYMBOL_DIR` in this shell points at
   `/usr/share/kicad/library`, which does **not** exist; use the literal path above.
2. **Known false positives — all 19 warnings, each collected from a block handoff's
   `## Carried forward` / `## Next phase must`, none fixable in `__main__.py`:**
   - `EE_CS`, `EE_CLK` — 3 each (1 "no drivers" + 2 "insufficient drive"), **6 total**.
     KiCad's `Interface_USB:FT232H` types EECS(45)/EECLK(44) as INPUT although U7 drives U8's
     CS/SCLK. Symbol pin-type artifact (`usb_bridge` decision 8 wires by number on purpose).
   - `FT232H_3V3` (7) — U7.VCCD(39) is a 3.3 V *output* of U7 typed as a supply input;
     it feeds VCCIO/VPLL/VPHY and U8.VCC. `usb_bridge` decision 3: intended, no `+3V3_D` here.
   - `VBUS_RAW` (4) — J1's four VBUS pads are POWER-IN with only passive neighbours; the
     supply is the USB host cable. `usb_c_input` decisions 2/3.
   - `XO_VDD` (1) — X1.VDD behind FB4, a ferrite. `clock_20m` decision 4.
   - `V5_LDO_IN` (1) — U3.IN behind FB3, the SPEC-P8 pi-filter. `analog_power_ref` decision 6.
   - 1 netlist-generation warning: `Missing tag on  … <frozen importlib._bootstrap>:491`
     = the root hierarchy node. See Decision 7 — do **not** "fix" it.
3. **`ADC_CLK` / `FPGA_CLK` produced NO warnings** under SKiDL 3.0.0 (a passive resistor pin
   satisfies its driver check), contrary to `clock_20m`'s prediction. Either way: do not
   connect X1 pin 3 to those nets directly — R_s1/R_s2 isolation is the design.
4. **Footprints**: `validate-footprints.py circuits/dual_adc_usb` → **33/33 valid across 9
   files**, exit 0, including the project-local `Capacitor_Trimmer_SEHWA.pretty` trimmer.
5. ERC/netlist outputs land as `__main__.erc` / `__main__.log` in the project root (script
   name is `__main__`), not `dual_adc_usb.erc`.

## Carried forward

- **Zero ERC errors to attribute.** The 19 warnings above map to blocks as:
  `usb_bridge` 13 (U7, U8), `usb_c_input` 4 (J1), `clock_20m` 1 (X1),
  `analog_power_ref` 1 (U3) — via `handoffs/03_sourcing.md` § Parts by block. All are
  symbol-pin-type or passive-feed artifacts; **no rework is implied for any block**.
- Unsourced/BOM-owed items are unchanged and belong to sourcing, not to me: `adc_dual`
  R41–R45 + C51/C53 (2.2 µF); `usb_bridge`'s 7 FTDI-mandated parts (`R_ref`, `R_eedo`,
  `R_pwren`, `C_vregin`, `C_io24`, `C_io46`, `C_ee`); `R22` 10 Ω; C1/C2 at 4.7 µF; C57
  recommended 1 µF. All 169 refs do carry a footprint.
- Design-level open items stay open and are **not** ERC-visible: VOCM 1.5 V vs the plan's
  1.65 V (`adc_dual`), MSBI=0 offset binary vs FPGA capture logic, X2 pad-map continuity
  test (`usb_bridge` decision 6), J2/J3 BNC footprint pad count, DONE pull-up on U6 pin 10.
- `pipeline_state.json` still shows `handoffs.coding: null` and `erc_status.last_run: null` —
  the driver owns that file; I did not edit it.

## Do not redo

- Block-internal design, values, straps, pin-number wiring, sourcing and footprints — all
  settled in `handoffs/05_blocks/*.md` and their `## Do not redo` sections.
- The `ch=1/ch=2` two-call pattern for `afe_channel`, and the tag names
  (`afe_channel_ch1`/`afe_channel_ch2`) — changing a tag re-UUIDs the parts in KiCad.
- The `.drive = POWER` set in Decision 3, and the absence of one on `VOCM`.
- The root-node tag question (Decision 7).

## Receipt

- Blocks assembled: **8** (9 calls — `afe_channel` twice), all tagged.
- Parts: **169**; nets: **146** in the netlist (30 top-level scalars + 3 buses = 62 inter-block nets, rest block-internal).
- ERC: **0 errors / 19 warnings** — every warning on a block-internal net, all justified above.
- Netlist reproducibility: two runs byte-identical apart from `(date …)`.
- Footprints: 33/33 valid. Duplicate refs: none.
- Verdict: **PASS** — ready for `06_erc`.
