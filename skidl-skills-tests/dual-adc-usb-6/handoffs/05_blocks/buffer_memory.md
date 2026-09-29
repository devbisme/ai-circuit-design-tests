---
phase: 05_blocks/buffer_memory
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-21T00:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 handoff — block `buffer_memory`

## Decisions

1. **Signature is exactly as issued — unchanged.**
   `buffer_memory(sdr_dq, sdr_a, sdr_ba, sdr_clk, sdr_cke, sdr_cs_n, sdr_ras_n, sdr_cas_n, sdr_we_n, sdr_ldqm, sdr_udqm, v3v3d, gnd)`
2. **Direction of every interface net.** `sdr_dq` is the only **bidirectional** net
   (shared with U30). `sdr_a`, `sdr_ba`, `sdr_clk`, `sdr_cke`, `sdr_cs_n`, `sdr_ras_n`,
   `sdr_cas_n`, `sdr_we_n`, `sdr_ldqm`, `sdr_udqm` are all **sensed only** — driven by
   `fpga_core` (U30), never by this block. `v3v3d` and `gnd` are **consumed only**.
   **This block drives nothing.**
3. **Bus bit order: bit 0 = LSB**, matching `fpga_core`'s existing convention
   (`sdr_dq[0]`→DQ0, `sdr_a[0]`→A0, `sdr_ba[0]`→BA0). Buses are indexed element-wise
   (`bus[i] += pin`), so a `Bus` or a plain list of `Net`s both work.
4. **`sdr_clk` lands on R40, not on U40.CLK.** `net_plan.md` puts the 22 Ω series
   termination inside this block (`U30 -> R40 (22 Ω) -> U40.CLK`). The damped node is a
   local implicit net; the assembler's `SDR_CLK` net stops at R40 pin 1.
5. **Two symbol pin-name traps, handled — do not "correct" them.** The generated symbol
   `dual_adc_usb:W9825G6KH-6I` names the bank selects **`BS0`/`BS1`** (not BA0/BA1) and
   address bit 10 **`A10/AP`** (not `A10`). Active-low pins use `#`: `CS#`, `RAS#`,
   `CAS#`, `WE#`. Exact-name lookup verified non-ambiguous under SKiDL 3.0.0 — `'A1'`
   resolves to pin 24 only and does not also catch `A10/AP`.
6. **VDD and VDDQ both tie to `+3V3D`; VSS and VSSQ both tie to `gnd`.** `net_plan.md`
   lists U40 as a plain `+3V3D` load with no separate VDDQ rail. The VDD/VDDQ split is a
   board-level noise-isolation feature, not a second supply.
7. **Pin 40 (`NC`) is explicitly `+= NC`** — a real die no-connect per
   `datasheets/W9825G6KH-6I_SUMMARY.md`, not an oversight.
8. **Decoupling allocation.** 7 supply pins (3× VDD, 4× VDDQ) get one 100 nF each
   (C70–C76); C77 is an eighth 100 nF placed as an extra HF bypass on the VDDQ/DQ side
   where the ×16 bus switching current concentrates; C78 is the 10 µF local bulk. All
   nine refs from the work order are used — none left dangling.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/buffer_memory.py` | The block — U40, R40, C70–C78 | Assembling the circuit |

## Next phase must

1. Emit exactly this call in `__main__.py`:
   ```python
   buffer_memory(sdr_dq=SDR_DQ, sdr_a=SDR_A, sdr_ba=SDR_BA, sdr_clk=SDR_CLK,
                 sdr_cke=SDR_CKE, sdr_cs_n=SDR_CS_N, sdr_ras_n=SDR_RAS_N,
                 sdr_cas_n=SDR_CAS_N, sdr_we_n=SDR_WE_N, sdr_ldqm=SDR_LDQM,
                 sdr_udqm=SDR_UDQM, v3v3d=V3V3D, gnd=GND, tag='buffer_memory')
   ```
2. Create `SDR_DQ` as `Bus('SDR_DQ', 16)`, `SDR_A` as `Bus('SDR_A', 13)`, `SDR_BA` as
   `Bus('SDR_BA', 2)` — widths are load-bearing, the block indexes 0..15 / 0..12 / 0..1.
3. **Set `V3V3D.drive = POWER` and `GND.drive = POWER` at the top level.** This block
   only consumes both rails; without it ERC reports "insufficient drive" on every U40
   supply pin.
4. Run `KICAD9_SYMBOL_DIR="$KICAD_SYMBOL_DIR:$PWD/symbols"` — U40 uses the *generated*
   symbol `dual_adc_usb:W9825G6KH-6I`, which is not in the stock KiCad libraries.

## Carried forward

- **R40's 22 Ω sits at the receiver end, not the driver end.** Series termination works
  best at the source; `net_plan.md` assigned R40 to this block, so it damps the
  reflection at the SDRAM rather than at the FPGA. 22 Ω against a ~50 Ω trace is a
  compromise that is fine at 100 MHz over a short trace, but if layout puts U40 far from
  U30 this resistor belongs in `fpga_core` instead. Flagged, not changed — moving it
  would break the agreed block interface.
- **U40's pinout is EasyEDA-sourced, not verified against a Winbond PDF** (stated in
  `datasheets/W9825G6KH-6I_SUMMARY.md`; no Winbond datasheet was obtainable in phase 4).
  The table is internally consistent and standard JEDEC, but it is the one part in this
  block resting on a secondary source.
- **CKE is driven, not strapped high**, so the FPGA controller can use self-refresh. If
  `fpga_core`'s controller never asserts CKE the SDRAM stays dead — a firmware
  assumption, noted here so it is not silently lost.

## Do not redo

- U40's MPN, footprint, and the 22 Ω value for R40 — taken verbatim from
  `sourcing/sourced_bom.md`.
- The VDD/VDDQ-to-`+3V3D` tie and the `net_plan.md` bus widths — architecture decisions.

## Receipt

- block_id: `buffer_memory`; file `circuits/dual_adc_usb/buffer_memory.py`
- parts: 11 (U40, R40, C70–C78); nets: 42 in an isolated smoke build
- compile OK (`py_compile`); block instantiates and connects cleanly under SKiDL 3.0.0
- footprints: valid (TSOP-II-54 = 54 pads vs 54 symbol pins; 0402/0805 passives)
- signature changed: **no**
