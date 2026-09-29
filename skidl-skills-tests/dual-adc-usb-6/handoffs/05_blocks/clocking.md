---
phase: 05_blocks/clocking
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-21T00:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — clocking

## Decisions

1. **Signature unchanged from the work order, verbatim:**
   `clocking(vdd, clk_adc, clk_fpga, gnd)`. No parameter renamed. Single instance.
2. **Net directions.** `clk_adc` and `clk_fpga` are **driven by this block**, but each
   through a series resistor (R21 / R23), so the driving pin is one element back — see
   `Next phase must` #3 for the ERC consequence. `vdd` and `gnd` are **consumed only**.
3. **X1's MPN updated to `OXETDLJANF-10.000000`** per `handoffs/04_datasheets.md`
   Decision #1 / `Next phase must` #1 — the superseded `SX3M10.000B10F20TNN` published no
   jitter spec at all. Symbol `dual_adc_usb:OXETDLJANF-10.000000`, footprint unchanged
   (`Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm`).
4. **Topology exactly as `net_plan.md` § "clocking nets":** `CLK_XO` = X1.OUT, splitting
   into R21 (33 Ω) → `CLK_ADC` and R22 (100 Ω) → U8.A; U8.Y → R23 (33 Ω) → `CLK_FPGA`.
   Two internal nets added that net_plan does not name: `CLK_BUF_IN` (R22→U8 pin 2) and
   `CLK_BUF_OUT` (U8 pin 4→R23).
5. **The ADC leg is the direct leg.** `CLK_ADC` is X1 → R21 → ADCs, full stop. It does
   **not** pass through U8 and does not come from an FPGA PLL. Phase-1 hard constraint:
   12-bit SNR at a 5 MHz input allows only ~6.4 ps RMS clock jitter; X1 is ≤1 ps. U8
   exists only so the FPGA pin's capacitance and any reflections stay behind R22.
6. **X1's OE (pin 1) is tied HIGH to `vdd`, not left floating.** The datasheet enables
   the output on "high or floating", but a floating enable on the board's only clock
   source is not worth the one net it saves.
7. **U8 is wired entirely by pin number.** The KiCad symbol `74xGxx:74LVC1G17` names
   both signal pins `~`. Mapping used — which matches TI's DBV (SOT-23-5) pinout for the
   1G17 and is confirmed by the symbol's own pin types:
   **1 = NC, 2 = A (input), 3 = GND, 4 = Y (output), 5 = VCC.**
   Note this is *not* the 1G04-style pinout; pin 1 really is the NC on this part.
8. **Pin 1 of U8 is left unconnected.** It is typed `NOCONNECT` in the symbol, so it is
   genuinely a no-connect, not an oversight.
9. **C30/C31 kept at the BOM's 1 µF X7R 0603 (`CL10B105KB8NQNC`)**, one at X1's VDD and
   one at U8's VCC — taken verbatim rather than substituted for the more conventional
   100 nF. See Carried forward.
10. **R22 = 100 Ω is the sourcer's choice, not `[calc]`** (`sourced_bom.md` says so
    explicitly): edge control / isolation only. R21 and R23 are the `[calc]` 33 Ω values.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/clocking.py` | The `@SubCircuit` block — 7 parts / 8 nets | Assembling the circuit |

## Next phase must

1. Emit exactly this call (keyword args, `tag`):

```python
clocking(vdd=V3V3D, clk_adc=CLK_ADC, clk_fpga=CLK_FPGA, gnd=GND, tag='clk')
```

2. **`.drive = POWER` at top level on `GND` and `+3V3D`** — this block only consumes them.
3. **Expect an ERC "no driving pin" note on `CLK_ADC` and `CLK_FPGA`.** Both nets are
   reached through a series resistor (R21, R23), so the only pins physically on them are
   the resistor's passive pin and the consumers' input pins. This is correct for a
   series-terminated clock, not a defect. If it must be silenced, set
   `CLK_ADC.drive = POWER` / `CLK_FPGA.drive = POWER` at top level — do **not** "fix" it
   by deleting the series resistors.
4. **Pass the same `CLK_ADC` net object to both `adc_channel` instances.** SPEC F13
   (≤100 ns channel-to-channel skew) is met by the shared clock.
5. Run with `KICAD9_SYMBOL_DIR` including `$PWD/symbols` — X1 comes from the project
   library `dual_adc_usb`; U8 comes from the stock KiCad `74xGxx` library.
6. `CLK_FPGA` must land on a **GCLK-capable** FPGA input in `fpga_core`. Phase 4 carried
   forward that the XC6SLX9 per-pin names are EasyEDA-sourced and not verified against
   Xilinx UG385 — this is exactly the net where that matters.

## Carried forward

- **C30/C31 = 1 µF is the BOM's value, not a considered decoupling choice.** A 10 MHz
  XO and a single-gate buffer would normally each get 100 nF close in, optionally with
  bulk behind it. 1 µF X7R 0603 has enough ESL that its HF impedance is worse than a
  0402 100 nF would be. Taken verbatim per instruction; worth one look from review —
  changing it is a value swap, not a topology change.
- **SN74LVC1G17DBVR has no primary-source datasheet on disk.**
  `datasheets/SN74LVC1G17DBVR_SUMMARY.md` is MCP-data-only. The pin mapping in Decisions
  #7 is taken from the KiCad symbol's own pin numbers and types, which are consistent
  with TI's DBV pinout for this gate — but it has not been checked against TI's PDF.
  If U8 ever misbehaves, verify pin 1 vs pin 2 first.
- **U8 adds ~4.6 ns of propagation delay** (and its own jitter) to `CLK_FPGA` relative to
  `CLK_ADC`. That is deliberate — the FPGA is expected to capture ADC data on this
  delayed copy, and `fpga_core` must account for the skew in its capture timing. It does
  **not** affect the ADC sampling instant, which is R21's leg only.
- No pins are left `NC` other than U8 pin 1, which is a true package NC.

## Do not redo

- X1's MPN — the `OXETDLJANF-10.000000` substitution is settled (phase-4 Decision #1),
  and its ≤1 ps jitter figure is what makes the 12-bit target reachable. Do not revert to
  `SX3M10.000B10F20TNN`.
- The CLK_ADC / CLK_FPGA split — X1 feeds the ADCs directly and the FPGA through U8.
  This is a phase-1 hard constraint, not a layout preference.
- U8's by-number wiring — the `~` pin names are a KiCad symbol property, not a mistake.

## Receipt

- Block `clocking` — 1 file, single instance.
- 7 parts / 8 nets (X1, U8, R21, R22, R23, C30, C31 — exactly the allocated refdes set).
- `py_compile` OK. Smoke-instantiated once: zero SKiDL `_1` uniquification, zero
  collisions; every pin lands on the intended net.
- `validate-footprints.py`: ✓ all 4 distinct footprints valid.
- Signature changed: **no**.
- ERC not run (assembler's job).
