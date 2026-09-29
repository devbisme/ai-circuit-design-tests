---
phase: 05_coding
agent: skidl-assembler
circuit: dual_adc_usb
written: 2026-09-21T20:50:00Z
status: complete
revision: 1
next_phase: 06_erc
---

# Phase 5 handoff — Coding (assembly)

8 blocks / 10 instances wired in `circuits/dual_adc_usb/__main__.py`. **ERC: 0 errors,
2 warnings, both predicted.** No netlist exported (phase 07 gate).

## Decisions

1. **No signature or net-name disagreement existed to resolve.** All eight block handoffs
   report `signature changed: no`, and the eight signatures in the block files match their
   handoffs verbatim (checked against the source, not just the handoffs). Every call is
   keyword-form, copied from each block's `## Next phase must` #1.
2. **Net names are `net_plan.md` verbatim**, including the `+` in `+3V3D` / `+1V2` /
   `+3V3A_ADC` / `+3V3A_AMP`. Signal nets are UPPERCASE rather than the camelCase of
   `rules/skidl-syntax.md` because `net_plan.md` declares itself "verbatim" and is the
   cross-block contract; a rename here would silently break the block handoffs' net tables.
   Python variable names drop the `+` (`V3V3D = Net('+3V3D')`).
3. **`.drive = POWER` on 8 nets**: `GND`, `VBUS`, `VBUS_SW`, `+3V3D`, `+1V2`, `+3V3A_ADC`,
   `+3V3A_AMP`, `VCM_REF`. Union of every block's request. Reasons: each of the four rails
   is generated behind a passive (L1/L2/FB3/FB4) so no pin drives it; `VCM_REF` is an
   unbuffered R16/R17 divider; `VBUS` sees only passive J1 pins; `GND` is consumed
   everywhere. `VBUS_SW` is flagged although U2.VOUT (`power_out`) already drives it —
   `power`'s handoff asked for it and it is a no-op alongside a real driver.
4. **`VREF_OFF` is deliberately NOT flagged** — U7 unit A output is a genuine driver
   (`power` Decision #2). Flagging it would mask a future loss of that driver.
5. **`CLK_ADC` and `ADC_PDWN` are single net objects passed to both `adc_channel`
   instances** (SPEC F13, ≤100 ns skew). `CLK_ADC` originates at X1 → R21 in `clocking`;
   nothing connects it to an FPGA PLL. **`CLK_ADC`/`CLK_FPGA` were left without
   `.drive = POWER`** although `clocking` offered it as a silencer — classification over
   suppression, and this SKiDL version emits nothing on them anyway.
6. **Bus widths, bit 0 = LSB**: `ADC1_D`/`ADC2_D` 12, `SDR_DQ` 16, `SDR_A` 13, `SDR_BA` 2,
   `FIFO_D` 8, `FIFOADR` 2. Created with `Bus(...)` at top level and shared by the two
   blocks at each end.
7. **No top-level `SCL`, `SDA`, `EE_A0/1/2`, `FX2_RESET_N`** — internal to `usb_bridge`
   (its `Next phase must` #4). Verified absent from `__main__.py`.
8. **Every block call carries `tag=`** (`usb_front`, `power`, `afe_ch1`, `afe_ch2`,
   `adc_ch1`, `adc_ch2`, `clk`, `fpga_core`, `buffer_memory`, `usb_bridge`) and
   `_stabilize_tags()` runs before `ERC()`. Two netlist generations (into the scratchpad,
   not `outputs/`) are **byte-identical** after filtering the `(date …)` line.
9. **`__init__.py` stays empty** — nothing needs to live there; blocks are imported
   relatively by `__main__.py`.
10. **`__main__.py` exports no netlist.** Net creation and block calls live in `build()`
    so a reviewer can import and re-run the circuit without duplicating the wiring.

## Artifacts

| File | Contains | Read it when |
|---|---|---|
| `circuits/dual_adc_usb/__main__.py` | All 51 inter-block nets/buses + the 10 block calls + `_stabilize_tags()` + `ERC()` | Re-running or reviewing the assembled circuit |
| `circuits/dual_adc_usb/__init__.py` | Empty (package marker) | Never |
| `__main__.erc` (project root) | The ERC output of the run below | Cross-checking the receipt |

## Next phase must

1. Run exactly (there is **no `.venv/`** in this project — the pyenv `python3` on PATH is
   the interpreter that has SKiDL 3.0.0):

   ```bash
   cd /home/devb/projects/AI/ai-circuit-design-tests/skidl-skills-tests/dual-adc-usb-6
   KICAD9_SYMBOL_DIR="${KICAD_SYMBOL_DIR:-/usr/share/kicad/symbols}:$PWD/symbols" \
       python3 -m circuits.dual_adc_usb
   ```
   As a module from the project root; running the file fails on the relative imports.

2. **Known false positives, collected from the block handoffs' `## Carried forward` /
   `Next phase must` — verify, do not suppress:**
   - **The 2 warnings actually emitted** (below) — U5.IN / U6.IN sit behind FB1/FB2, so a
     top-level `.drive = POWER` on `VBUS_SW` cannot propagate past the ferrite.
     `power` predicted exactly these two.
   - **Intentional NC pins** — `usb_front`: J1 SBU1/SBU2, U2 pin 4 and QOD (pin 5);
     `clocking`: U8 pin 1 (typed NOCONNECT in the symbol, a true package NC);
     `adc_channel`: U150/U250 pins 5 and 6 (DNC per datasheet);
     `buffer_memory`: U40 pin 40 (die NC);
     `usb_bridge`: U50 PD0–PD7, CTL0/FLAGA, PA0, PA1, PA3, PA7/~SLCS, CLKOUT;
     `fpga_core`: U30 pins 66, 67, 74, 75, 102, 104, 105.
   - **Open-drain / pull-up-only nets** — `INIT_B` (R34), `DONE` (R35), `PROGRAM_B` (R30),
     `CMPCS_B` (R37), `FPGA_RESET_N` (R31), `SCL`/`SDA` (R50/R51), `FX2_RESET_N` (R52/C89).
   - **"No driving pin" nets that are correct by construction** (this SKiDL version does
     not print them, but they show up in any driver census — I ran one): `CH1_BNC`/
     `CH2_BNC` (passive BNC jacks J2/J3 are the signal source); `CLK_ADC` and `CLK_BUF_IN`
     (series-terminated behind R21/R22); `CHn_VREF`, `CHn_REFT`, `CHn_REFB` (ADC internal
     reference outputs read as passive); the whole `CHn_*` analog chain (op-amp outputs
     through passives); `CHn_MODE_STRAP`, `EE_A0/1/2`, `EN_3V3D`, `FB_3V3D`, `FB_1V2`,
     `VREF_OFF_DIV`, `LDO_ADC_IN`, `LDO_AMP_IN`, `PWR_EN`, `TCK`/`TMS`/`TDI` (J4 pins are
     passive). 57 nets total in that census; none is a wiring defect.
   - **Deliberate multi-driver nets: none.** `SDR_DQ` and `FIFO_D` are bidirectional by
     design (U30↔U40, U30↔U50) and ERC reports no conflict on them.
3. **BOM corrections still open and owed by sourcing, not by me** (raised in block
   handoffs, none applied): `fpga_core` — R30/R34/R36/R37 are 4.7 kΩ and R35 is 330 Ω, not
   the 10 kΩ placeholders; `usb_bridge` — Y1 symbol `Device:Crystal` → `Device:Crystal_GND24`,
   R52 10 kΩ → 100 kΩ (MPN `0402WGF1003TCE`, LCSC C25741), and C92/C93 belong to
   `usb_bridge` although the work-order ref list stopped at C91.
4. `R19` is spare by `power` Decision #4 and **is absent** from the circuit (verified by a
   refdes census). It must stay out of the BOM.

## Carried forward

- **ERC errors: none.** There is nothing to attribute.
- **Residual warnings, both attributed to `power`** (via `handoffs/03_sourcing.md`
  § Parts by block → U5/U6 = `power`):
  1. `ERC WARNING: Insufficient drive current on net LDO_ADC_IN for pin POWER-IN pin 1/IN
     of TPS73633DBV/U5.`
  2. `ERC WARNING: Insufficient drive current on net LDO_AMP_IN for pin POWER-IN pin 1/IN
     of TPS73633DBV/U6.`
  Both are internal `power` nets fed from `VBUS_SW` through FB1/FB2. Not fixable from
  `__main__.py`; fixing them would mean deleting the ferrites, which risk R5 requires.
- **Unverified facts carried up from blocks and still binding** (each already argued in its
  own handoff, repeated so phase 6 does not lose them): AD9235 DNC-pin tolerance
  (R150/R250 DNP mitigation); `adc_channel` DRVDD fed from `+3V3D` while `net_plan.md`'s
  power table says `+3V3A_ADC`; BAV199 pin-3 identity; U40 and XC6SLX9 pinouts are
  EasyEDA-sourced (re-verify U30 pins 124/56 against UG385 before fab); TPS22919 `ON`
  polarity; L2 footprint; C2/C3 must be placed at the U3/U4 VIN pins.
- **The project has no `.venv/`.** `rules/environment.md`'s command must be adapted (see
  `Next phase must` #1) or every downstream run fails with "No such file or directory".

## Do not redo

- Block-internal design, part selection, values, footprints, pin assignments, and every
  `## Do not redo` item in the eight `handoffs/05_blocks/*.md`. This phase touched
  integration only; no block file was modified.
- The net names and bus widths — they are `net_plan.md`'s contract, already matched on both
  sides of every interface.
- Footprints: `validate-footprints.py` on the package prints `✓ All footprints valid
  (62 checked across 9 files)`.

## Receipt

- Blocks: **8 files / 10 instances**; parts **238**; nets **186** (51 created at top level,
  the rest block-internal); no refdes uniquification (`_1`), no single-pin nets, no `R19`.
- ERC: **0 errors, 2 warnings** (both the predicted U5/U6 drive warnings behind FB1/FB2).
- Tag stability: two consecutive netlist generations identical apart from `(date …)`.
- Footprints: 62 checked, all valid. Netlist **not** exported — phase 07 gate.
- Status: **PASS**.
