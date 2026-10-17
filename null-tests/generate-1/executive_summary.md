# Executive summary — dual-channel ±10 V, 12-bit, 10 MS/s USB ADC board

## What was asked

Two channels, ±10 V input, 10 MS/s, 12 bits, at least 0.1 s of samples at full rate,
scope-lead-compatible input connectors, USB 2.0 for power and data (USB-C only if USB 2.0
power is insufficient). Start from a blank slate; pick options without waiting for input.

## What was produced

A complete KiCad 10 project, generated from code:

| File | What it is |
|---|---|
| `dual_adc.py` | SKiDL description of the whole circuit (source of truth) |
| `dual_adc.kicad_sch` + 10 sub-sheets | Hierarchical schematic drawn by schematizer from the SKiDL netlist |
| `dual_adc_schematic.pdf` | Schematic PDF |
| `dual_adc.kicad_pcb`, `dual_adc.kicad_pro` | 4-layer, 140 × 95 mm board, placed and routed |
| `dual_adc_bom.csv` | Grouped BOM (with a Spec column for tolerance/dielectric) |
| `dual_adc.net` / `dual_adc_sch.net` | SKiDL netlist / netlist exported from the drawn schematic |
| `dual_adc_top.png` | Top-copper + silkscreen render of the routed board |
| `make_pcb.py` | Loads footprints, assigns nets, rule-based placement, outline, In1 GND plane |
| `route.py` | DSN export / SES import + GND pours, and `relink` (footprint ↔ symbol UUIDs and fields) |
| `finish_board.py` | Fixes DRC "starved thermal" pads, marks mounting holes board-only, refills zones |
| `write_project.py` | Writes `dual_adc.kicad_pro` (design rules, Default/Power net classes) |
| `fix_sch.py`, `compare_nets.py` | Schematic post-fix (PWR_FLAG footprints); netlist-vs-netlist check |
| `dual_adc.dsn`, `dual_adc.ses`, `freerouting.log` | Freerouting input/output for the delivered board |
| `erc.rpt`, `drc.rpt` | Final KiCad 10 ERC / DRC reports |

Flow: SKiDL → netlist + schematic (schematizer) → KiCad ERC → schematic netlist exported by
`kicad-cli` and compared pin-for-pin with the SKiDL netlist → PCB built with KiCad 10's
`pcbnew` Python (footprints, rule-based placement) → Freerouting 2.4.1 → zones → KiCad DRC.

To rebuild from scratch:

```bash
python3 dual_adc.py && python3 fix_sch.py                     # netlist + schematic
K=~/bin/kicad10-root/bin; $K/kicad-cli sch export netlist -o dual_adc_sch.net dual_adc.kicad_sch
python3 compare_nets.py dual_adc.net dual_adc_sch.net        # expect 0 differing nets
$K/python3.11 make_pcb.py dual_adc_sch.net dual_adc.kicad_pcb
$K/python3.11 route.py export dual_adc.kicad_pcb dual_adc.dsn
java -jar freerouting-2.4.1.jar -de dual_adc.dsn -do dual_adc.ses -mp 60   # Java 25
$K/python3.11 route.py import dual_adc.kicad_pcb dual_adc.ses
$K/python3.11 route.py relink dual_adc.kicad_pcb dual_adc_sch.net
python3 write_project.py                                      # pcbnew saves clobber the rules
$K/kicad-cli pcb drc --schematic-parity -o drc.rpt dual_adc.kicad_pcb
$K/python3.11 finish_board.py dual_adc.kicad_pcb drc.rpt && python3 write_project.py
```

Freerouting is not deterministic; another run may leave a connection or two unrouted.

## Architecture

```
BNC A ─ 1MΩ‖20pF attenuator ─ OPA356 buffer ─┐
                               (REF3020 bias) ├ THS4521 FDA ─ RC ─┐
          matched rest-voltage ─ OPA356 ──────┘                   │
BNC B ─ (same) ───────────────────────────────────────────────────┤
                                                       LTC2290 dual 12-bit 10 MS/s
10 MHz XO ─ 74LVC2G34 ─┬─ ADC CLKA/CLKB                    │ 2×13 bits (33 Ω packs)
                       └─ FPGA GBIN                        ▼
                        iCE40HX4K-TQ144 ── IS42S16400J 8 MB SDRAM (capture buffer)
                              │  FT245 sync FIFO (8 bit, 60 MHz)
                         FT232H ── USB-B (USB 2.0 HS)
USB VBUS ─ polyfuse ─ ferrite ─ TPS62160 3.3 V │ AP2112 1.2 V │ LP5907 4.5 V (analog) │ LP5907 3.0 V (ADC, clock)
```

### Key numbers

| Item | Value | How |
|---|---|---|
| Input range | ±10.09 V full scale | attenuator 100k/(909k+100k) = 0.0991, ADC 2 Vpp differential |
| Input impedance | 1.009 MΩ ‖ ≈20 pF | 909k + 100k, 15 pF shunt + attenuator caps; matches normal scope inputs so 1×/10× probes compensate |
| LSB (input-referred) | ≈4.9 mV | 20.18 V / 4096 |
| Analog bandwidth (−3 dB, estimate) | ≈4.4 MHz | FDA Rf·Cf pole 4.8 MHz + output RC pole 10.6 MHz; only 2nd-order anti-aliasing |
| Capture memory | 8 MB → 0.2 s at 2 ch × 10 MS/s × 16 bit | requirement is 0.1 s = 4 MB |
| USB transfer | FT232H sync FIFO, ≈35–40 MB/s practical (FTDI spec max 40 MB/s) | 4 MB capture uploads in ≈0.1–0.15 s |
| Power (estimate) | ≈1.3 W ≈ 260 mA at 5 V | see below |

Power estimate (typical datasheet currents, not measured): analog front end 4 × OPA356 +
2 × THS4521 + REF ≈ 40 mA at 5 V (LDO); ADC + clock ≈ 50 mA at 5 V (LDO); 3.3 V digital
(SDRAM ≈ 80 mA, FT232H ≈ 70 mA, FPGA I/O + core ≈ 50 mA, misc ≈ 20 mA) ≈ 220 mA at 3.3 V
through an ≈88 % buck ≈ 165 mA at 5 V. Total ≈ 255–260 mA, about half of the 500 mA a
USB 2.0 port supplies, **so USB-C was not needed** and the board uses a USB 2.0 type-B
receptacle.

## Decisions (options → choice)

1. **ADC** — LTC2290 (dual 12-bit 10 MS/s, ≈120 mW), LTC2291/2292 (25/40 MS/s, more
   power), AD9238 (not in KiCad's library), two single ADCs, MCU-internal ADC (STM32
   12-bit tops out at ≈4–5 MS/s). **Chose LTC2290**: exact fit, both channels sampled on the
   same clock, lowest power; the symbol is KiCad's `LTC2292xUP` (same pinout across the
   LTC2290/91/92 family). Risk: running at its maximum rated rate; LTC2291 is a drop-in if
   margin is wanted.
2. **Input connector / impedance** — BNC at 1 MΩ‖≈20 pF, BNC at 50 Ω, SMA, banana.
   **Chose BNC, 1 MΩ‖20 pF**: mates with standard scope probes and BNC leads, and a 10×
   probe can be compensated.
3. **Front end** — (a) resistive divider straight into an FDA (input impedance only kΩ —
   breaks probe compatibility); (b) split ±5 V supplies with a classic JFET buffer (needs a
   negative rail from USB); (c) **chosen:** single-supply 1 MΩ attenuator whose bottom leg
   sits on a 2.048 V reference, a CMOS buffer (OPA356, pA bias), and a THS4521 FDA whose
   other input gets a matched, buffered copy of the attenuator's rest voltage. Reference
   noise is common-mode to the FDA and cancels; the FDA's VOCM comes from the ADC's VCM pin.
   BAV199 low-leakage diodes clamp the attenuator node to 0 V/4.5 V.
4. **Capture buffer** — FPGA BRAM (too small: iCE40HX4K has 10 kB), MCU with internal
   SRAM (largest common parts ≈1 MB, and 40 MB/s of parallel capture is a stretch),
   **FPGA + SDR SDRAM** (chosen: 8 MB, simple, 200 MB/s available vs 40 MB/s needed).
5. **FPGA** — iCE40HX8K-BG121 (BGA, harder to route on 4 layers), **iCE40HX4K-TQ144**
   (chosen: TQFP, 107 I/O, open-source toolchain, enough logic), ECP5 (overkill, BGA).
6. **USB bridge** — FX2LP (firmware download, GPIF), FT601 (USB 3), **FT232H in FT245
   synchronous-FIFO mode** (chosen: no USB firmware, 40 MB/s, one chip + EEPROM).
7. **USB connector** — USB-C (not required: power is sufficient), micro-B (fragile),
   **USB-B** (chosen: robust bench-instrument connector, unambiguously USB 2.0).
8. **Sample clock** — FPGA PLL (hundreds of ps jitter → ≈40 dB SNR at 5 MHz input, far
   below 12-bit), **dedicated 10 MHz XO on the clean 3.0 V analog rail, buffered to the
   ADC and to an FPGA global clock pin** (chosen). FPGA PLL derives the SDRAM clock.
9. **Power** — all-LDO (≈2 W dissipated, tighter USB margin), **buck for 3.3 V digital +
   low-noise LDOs for analog** (chosen).
10. **Board** — 4 layers: signals / solid GND plane / signals+power / signals, with GND
    pours on the routing layers. One unbroken ground; analog and digital separated by
    placement (front ends left, ADC centre-left, digital right).

## Verification results

- **SKiDL ERC:** 0 errors, 2 warnings (SPI flash WP/HOLD tied to +3V3: intentional).
- **Schematic netlist vs SKiDL netlist:** identical connectivity (`compare_nets.py`,
  0 differing nets).
- **KiCad 10 ERC:** 0 errors, 435 warnings: 239 off-grid wire ends and 194 "symbol
  differs from library copy" (both artifacts of the generated schematic, cosmetic), plus
  the 2 intentional flash WP/HOLD ties.
- **KiCad 10 DRC (with schematic parity):** 0 errors, 0 unconnected pads, 0 parity
  errors; 30 warnings (27 silkscreen overlap/clipping, 3 footprints differing from the
  library copy).
- **Board:** 4 layers, 140 × 95 mm, 182 footprints, 2370 track segments, 339 vias.
  Rules: 0.15 mm clearance, 0.2 mm default track (0.5 mm power), 0.6/0.3 mm vias; five
  tracks were necked to 0.12 mm by the router and the buck's WSON thermal vias are
  0.25 mm, so the rule minimums are 0.1 mm track / 0.25 mm hole. These are within
  common 4-layer fab limits, but check them against your fab.

## Problems hit along the way (and fixes)

- schematizer crashed on footprint-only parts (mounting holes) → holes are added in the PCB
  script instead and marked board-only.
- schematizer's first full routing attempt failed → `auto_stub=True` (labels for
  high-fanout/cross-group nets).
- **schematizer drew two parallel 2-pin parts on top of each other** (PLL filter R over
  its C), which joined +1V2 to GND in the drawn schematic. Found by ERC and by the netlist
  comparison; fixed by moving the PLL filters to their own sub-sheet. Lesson: always diff
  the drawn schematic's netlist against the source.
- OPA356 SOIC symbol has hidden NC pins that the drawing placed on other nets (ERC
  warnings) → switched to the SOT-23-5 variant with no NC pins.
- **Routing took four Freerouting runs** (10–30 min each):
  1. 0.25 mm placement margin: 4 unrouted. One was impossible to hand-patch, because a +3V0A
     trace boxed in the ADC clock pins with no room for a via. A follow-up pass on the
     routed board ripped up existing work and ended at 60 unrouted, so it was discarded.
  2. 0.5 mm placement margin: 1 unrouted (ADC pin 36). The hand patch created a short
     with inner-layer traces and was dropped.
  3. Kept the 33 Ω packs ≥3 mm from the ADC: **0 unrouted. This is the delivered board.**
  4. Same, with In1 marked as a power layer to keep signals off the GND plane: 4
     signals + ~19 GND pads unconnected. Rejected.
- `pcbnew`'s `board.Save()` rewrites `dual_adc.kicad_pro` with default rules; the rules
  are re-applied with `write_project.py` after every board save.
- DRC parity flagged 182 Datasheet/Description field mismatches; `route.py relink`
  now copies the symbol fields onto the footprints.

## Known limitations, risks and open items

- **No gateware or host software.** The FPGA design (ADC capture, SDRAM controller,
  FT245 FIFO interface, trigger) and the host driver are not written. Pin assignments are
  in `dual_adc.py` (`ADC_PINS`, `SDRAM_PINS`, `FIFO_PINS`).
- **FT232H EEPROM** must be programmed once (FT_Prog) to select 245 FIFO mode; the
  host then enables synchronous mode with `FT_SetBitMode(0x40)`.
- **FPGA configuration** is through the 2×4 header J4 (SPI flash + CRESET/CDONE,
  iceprog-style programmer). Updating over USB is not supported in this revision.
- **USB unconfigured-current limit:** the board draws ≈260 mA as soon as it is plugged
  in, above the 100 mA allowed before enumeration. Most hosts don't enforce this; a
  load switch gated by the FT232H would fix it.
- **Attenuator compensation** (2.4 pF across 909k, 18 pF across 100k) assumes ≈4 pF of
  stray + buffer + clamp capacitance; expect to tune C on the first board (a trimmer would
  be better).
- **Anti-aliasing is only 2nd-order** (≈4.4 MHz). Out-of-band content above 5 MHz aliases;
  a steeper filter would cost passband flatness or need a higher sample rate.
- **The In1 GND plane is cut by signal traces.** Freerouting routed 81 nets
  (≈1.7 m of track) on In1.Cu, including traces under the ADC. GND pours on the
  other three layers fill around them, but the return paths are not what a 12-bit
  mixed-signal board should have. **This is the biggest layout weakness.** Fixes: route
  the ADC area by hand, or move to 6 layers with two clean planes. Reserving In1 on this
  placement left 4 signals unrouted (run 4).
- **USB D+/D− are not impedance-controlled** — Freerouting doesn't do differential pairs.
  They are short, but should be re-routed as a 90 Ω pair before fabrication.
- **Connector geometry:** the BNC footprint's mating face is assumed to overhang the left
  edge by ≈20 mm; check against the Amphenol B6252HB drawing before ordering.
- **Datasheet details taken from memory, not re-read** (moderate confidence): LTC2290
  REFH/REFL decoupling values, FT232H VCCA/VCCCORE/VREGIN hookup and EEPROM resistors,
  THS4521 pin 4/5 polarity (confirmed against the KiCad symbol's graphics), iCE40 GNDPLL
  tied to GND, TPS62160 0.8 V feedback reference, REF3020 output capacitor. These should
  be checked against the datasheets before fabrication.
- The design was **not simulated**; signal-chain numbers above are hand calculations.
- Silkscreen: reference designators overlap pads/each other in places (DRC warnings only).
- No Gerbers or drill files were generated; the design has not been reviewed by a human.

## Tools used

SKiDL 3.0.0, schematizer 0.2.0, KiCad 10.0.4 (`kicad-cli`, bundled Python `pcbnew`),
Freerouting 2.4.1 (Java 25), Inkscape (board renders). No MCP servers, skills or
plugins.
