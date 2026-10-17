# Executive summary — dual_adc_10msps

Dual-channel, ±10 V, 12-bit, 10 MSPS ADC board with a USB 2.0 host interface. It was
produced by the boardforge pipeline (phases 1–7), run autonomously from a blank slate:
no files from other designs and no datasheet cache (`use_cache = false`).

## Result

| Item | Result |
|---|---|
| Board | 100 × 80 mm, 4 layers (SIG / GND / +3V3 / SIG), 239 parts, all top side |
| Routing | 0 unrouted, 6190 mm of track, 714 vias |
| DRC | 0 errors; 50 warnings (silkscreen 36, dangling track stubs 9, hole-to-hole 5) |
| ERC | SKiDL 0 errors; KiCad 0 errors; netlist parity 217/217 |
| Review gate (phase 6) | PASS; no HARD failures; BOM ↔ code PASS |
| Release gate | PASS (12/12) |
| Fab outputs | `build/fab/`: Gerber zip, JLCPCB BOM (72 lines, 0 without LCSC numbers), CPL (239 placements) |

## Architecture

```
BNC ─► 1 MΩ attenuator/clamp ─► OPA2810 buffer + 2× Sallen-Key ─► THS4551 FDA (MFB) ─► ADS5231 ─┐
BNC ─► (identical channel B)  ──────────────────────────────────────────────────────────────────┘
                                                                     │ 2×12-bit parallel, 10 MSPS
 10 MHz XO ─► LVC2G34 fan-out ─► ADC clock / FPGA clock      XC6SLX9 FPGA ◄─► W9812G6KH 16 MB SDRAM
                                                                     │ 8-bit sync FIFO
                                       USB-C (USB 2.0 HS) ◄─► FT232H
 USB 5 V ─► TLV62569 buck 3.3 V ─► TLV757 1.2 V;  LP5907 3.3 V analog;  LM27762 ±4 V (analog)
```

Main decisions. For each one I listed the options and chose one; the reasoning is in
`architecture/*.md`.

- **Capture, then upload.** Streaming both channels at full rate needs 40 MB/s, which is at
  or above the practical USB 2.0 HS bulk limit. The FPGA therefore captures into a 16 MB
  SDRAM, which holds **0.42 s** against the 0.1 s required, and uploads through an FT232H
  sync FIFO. Rejected:
  - STM32H7 + ULPI: its DCMI port and bus contention are limiting.
  - FX2LP streaming: no margin.
- **ADC.** ADS5231, a dual simultaneous-sampling 12-bit converter with 40 MSPS capability.
  It is single-sourced with only **152 in stock** at JLCPCB; this is the largest sourcing
  risk.
- **Input.** BNC jacks with a 1 MΩ ∥ trimmed input capacitance, so 1×/10× scope probes can
  be compensated, plus ±30 V clamp protection.
- **Anti-alias.** 7-pole filter for ≥ 72 dB (6.02 × 12 bits) at fs/2 = 5 MHz. Simulated:
  - −80.9 dB nominal (Monte-Carlo worst case −78.7 dB).
  - Passband ripple ±0.013 dB to 1 MHz.
- **Power.** Worst case 0.43 A from USB 5 V, inside the 500 mA USB 2.0 budget, so no
  high-current USB-C negotiation is needed. A USB-C receptacle (USB 2.0 data, 5.1 kΩ Rd)
  is still used, as recommended.

## Things to know before ordering

1. **Fab-file bug in boardforge (fixed for this board).** KiCad's grouped BOM export
   compresses designators into ranges (`C1001-C1022`). boardforge's CPL filter
   (`vendor/.../translate_bom_pnp.py:_expand_designators`) does not expand them, so it
   silently dropped 80 parts from the CPL. I regenerated both files in `build/fab/` with
   the ranges expanded, using boardforge's own CPL adapter: 239/239 parts, the same 12
   rotation offsets, and the original 159 rows unchanged. The upstream fix is to pass
   `--ref-range-delimiter ""` to `sch export bom` in `physical.py`, or to expand ranges in
   `_expand_designators`. **Re-running `boardforge fab` will bring the bug back.**
2. **ADC power-up sequencing (review W2, MEDIUM, deferred).** For a brief moment at
   power-up, the ADS5231 AVDD/VDRV ±0.3 V abs-max limit may be exceeded. The fix is to tie
   U701 EN to +3V3. This changes the `power_analog` block's signature, so it needs an
   architect + coder pass; I deferred it rather than spend a rework cycle. I recommend
   doing it before fab.
3. **FT232H VREGIN sits at its 3.3 V minimum (W3, MEDIUM).** This is a documented
   configuration, but it has no margin.
4. **Unverified facts:**
   - Y901 12 MHz crystal: no datasheet; its pinout follows the 2520 convention.
   - SX3M oscillator: jitter is unspecified. 50 ps would still give about 70 dB SNR at 1 MHz.
   - W9812G6KH: the KH datasheet was not found; the JH datasheet was used.
5. **Custom footprints to eyeball against their drawings:** BNC `KH-BNC50-3511` and trimmer
   `STC3MA06`.
6. **Official SPICE path checks show NOT CHECKED.** boardforge can't map the custom
   OPA2810 dual-op-amp pin names to op-amp roles. The reviewer re-ran the same checker with
   the names mapped: 12/12 pass (`build/reports/spice_patched/`). The models are 1-pole
   behavioral, so the real stopband floor depends on layout feedthrough
   (`design_risks.md` §20).
7. **Cost.** About 50 of the 75 BOM lines are JLCPCB Extended parts, so assembly setup fees
   will likely put the board above the $150-per-board soft target at qty 5.
8. **Not included:** FPGA gateware, FT232H EEPROM configuration and host software. The
   requirements are listed in `architecture/block_diagram.md` and
   `handoffs/05_blocks/fpga.md`. They include the ADS5231 DISABLE_PLL register write,
   which is required at 10 MSPS.

## Process notes

- **Run cost:** about $23 API-equivalent (63 M tokens, mostly cache reads), measured with
  `session_cost.py`.
- **Interruption:** one session limit stopped the datasheet phase; it was resumed with no
  work lost.
- **Fix cycles:** one cycle after assembly, covering the LCSC fields on all parts, 3
  power-flag/pin ERC errors, and one added part (R705, the PGOOD pull-up).
- **Requirements:** where the prompt was silent, I made the choices myself; each is tagged
  `(driver)` in `SPEC.md`:
  - 1 MΩ input
  - ±30 V protection
  - 1 MHz passband
  - 4 layers
  - JLCPCB assembly at qty 5

## Where things are

- `SPEC.md`: requirements, with each item tagged as stated by you or chosen by me.
- `architecture/`: block diagram, net plan, IC selection, design risks.
- `sourcing/`: the sourced BOM.
- `datasheets/`: the datasheets used.
- `circuits/dual_adc_10msps/`: SKiDL source, 9 blocks.
- `review_report.md`: the phase 6 review.
- `build/kicad/`: the KiCad schematic and board.
- `build/fab/`: Gerbers, BOM, CPL.
- `build/reports/`: all check reports.
- `handoffs/`: per-phase decisions and what was carried forward.
