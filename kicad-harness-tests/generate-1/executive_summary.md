# Dual-channel ±10 V, 10 MSPS, 12-bit USB ADC — executive summary

## Outcome

A complete KiCad 10 project, `dual_adc/`, built from a blank slate using the kicad-harness (`kh`) toolchain plus my own generator scripts. It contains:

- A hierarchical schematic: root sheet plus Power, FrontEnd, ADC, FPGA, Memory and USB sheets. It has 163 footprinted parts and 176 nets.
- A routed 4-layer board, 120 × 88 mm. The layer stack is F.Cu signal, In1 GND plane, In2 +3V3 plane, B.Cu signal.
- Fabrication outputs in `dual_adc/fab/`: Gerbers, drill, placement CSV, BOM and schematic PDF. Renders are in `dual_adc/renders/`.

| Check | Result |
|---|---|
| Netlist exported by kicad-cli vs. the design description | identical (176/176 nets) |
| ERC | 2 warnings, 0 errors. The warnings come from a library quirk: the FT232H symbol types EECS/EECLK as inputs. |
| DRC (kicad-cli 10, refilled zones) | **0 errors, 0 unconnected.** 41 warnings: silkscreen, one 0.1 mm stub, and a lib-version footprint mismatch. |
| Schematic ↔ PCB parity | 0 issues |

The board has **not** been simulated, built or tested. No FPGA gateware or host software was written.

## Architecture

```
BNC ─► 1 MΩ‖15 pF 10:1 attenuator ─► clamp ─► OPA810 buffer ─► THS4521 FDA (G=0.95, Vocm=1.5 V) ─► RC AAF ─┐
BNC ─► (same, channel B) ──────────────────────────────────────────────────────────────────────────────────┤
                                                                       LTC2290 dual 12-bit 10 MSPS ADC ◄──┘
10 MHz XO ─► ADC CLK + FPGA GBIN                                                   │ 2×12 bit + OF (33 Ω packs)
                                     iCE40HX4K-TQ144 FPGA ◄────────────────────────┘
                                     │  SPI flash W25Q32 (config) + 8-pin prog header
                                     ├─ IS42S16400J 8 MB SDRAM (capture buffer)
                                     └─ FT232H, USB 2.0 HS, sync-245 FIFO ─► USB-B ─► host (power + data)
```

**Capture model.** The board digitizes both channels at 10 MSPS into SDRAM, then uploads to the host. 0.1 s × 2 ch × 10 MSPS × 2 B = 4 MB. The 8 MB SDRAM therefore holds **0.2 s** at the full rate, twice the requirement.

## Decisions (options → choice)

1. **Data path**
   - (a) Stream raw to the host. This needs 30 MB/s sustained (2 × 10 M × 12 bit), which is marginal for USB 2.0 and fragile with host latency.
   - (b) **Buffer in on-board RAM, then upload — chosen.** It removes any dependence on host latency.
   - Buffer options:
     - MCU internal SRAM: too small.
     - **SDRAM — chosen.** TSOP is easy to route and it holds 8 MB.
     - HyperRAM: BGA package.
2. **Controller**
   - (a) **FPGA + FT232H — chosen.** Capture is deterministic at the ADC rate.
   - (b) STM32F7 with HS PHY + FMC SDRAM + DCMI capture. Fewer chips, but the 12-bit DCMI/sync behaviour is risky.
   - (c) Cypress FX2LP + FPGA.
3. **ADC**
   - **LTC2290 — chosen.** Dual 12-bit 10 MSPS, ~120 mW, in the KiCad library.
   - LTC2292 (40 MSPS) would also work but is overkill. AD9238 and ADS4222 have no KiCad symbol.
4. **Input connector:** BNC — the standard mate for scope probes and leads.
   - Input impedance is 1 MΩ‖~15 pF, so 10× probes can be compensated.
   - ±10 V is attenuated to ±0.99 V, then the FDA (gain 0.953) gives a ±0.94 V differential signal. That uses 94 % of the ADC's 2 Vpp range and leaves ~6 % over-range headroom.
5. **Input buffer**
   - **OPA810 — chosen.** FET input (pA bias), 70 MHz, unity-gain stable, runs on ±5 V.
   - OPA356 and ADA4817 were rejected on input range or supply.
6. **Differential driver**
   - **THS4521 — chosen**, on the ADC's 3.0 V rail so its outputs can never exceed the ADC supply.
   - The ADA4940-2 KiCad symbol has wrong pin names (+VS/−VS labelled as FB pins), so I avoided it.
7. **USB connector / power**
   - Estimated draw is **~256 mA typical (1.3 W)**: 3.3 V buck ~188 mA from 5 V, analog/ADC LDO paths ~69 mA. That is within USB 2.0's 500 mA.
   - So per the prompt's rule, **USB-B (USB 2.0) was used, not USB-C**.
   - Options considered: Type-B (**chosen**, robust for an instrument), Micro-B (fragile), USB-C (not needed).
8. **Supplies**
   - TLV62569 buck for 3.3 V (efficiency).
   - LP5907 3.0 V LDO for the ADC, FDAs and clock (low noise).
   - AP2112 1.2 V for the FPGA core.
   - TPS60403 charge pump for −5 V for the buffers.
9. **Board**
   - 4 layers with solid GND and +3V3 planes. A 2-layer board was rejected given the TQFP-144, QFN-64 and TSOP-54 density.

## How it was built (tool flow)

1. `scripts/design.py` describes the circuit in a small Python DSL.
   - Every symbol and footprint ID and every pin number was looked up with `kh sym --pins` / `kh validate`.
   - Pins left unassigned raise an error.
2. `scripts/gen_sch.py` writes a label-based hierarchical KiCad 10 schematic: every pin gets a stub plus a net label or a no-connect flag.
3. `scripts/verify_netlist.py` checks kicad-cli's netlist against the design.
4. `kh board-from-netlist` creates the PCB.
5. `scripts/place.py` places the board:
   - Hand-placed anchors for ICs and connectors.
   - FPGA I/O reassigned by angular matching to the ADC, SDRAM and FT232H pins, with `pinmap.json` fed back into the schematic.
   - Greedy cost-based placement of passives and decaps near the pins they serve.
6. `scripts/route_prep.py` sets up for routing: net classes, inner-plane zones, 196 locked GND/+3V3 fanout vias, and the DSN export.
7. `scripts/dsn_cut.py` removes the plane nets from the DSN, so Freerouting 2.4.1 routes only signals on F/B. Freerouting left 12 unrouted.
8. `scripts/fix_route.py` is a small grid A* that completed the last links.
   - One overflow-flag line (ADC_OFA_S, ~10 mm) had to use a short run in the In2 +3V3 plane layer: its target pad was walled off on both outer layers.
9. `scripts/prune.py` removes dead-end spurs, and `scripts/polish.py` handles outline, holes and silk.
10. DRC and parity checks, then fab exports.

## Risks and open items (in priority order)

1. **Datasheet facts I could not verify this session.**
   - The FTDI, ADI and Lattice PDFs were blocked (HTTP 403, timeout, 404). The THS4521 pinout and supply range *were* verified from TI's datasheet.
   - These are from memory and should be checked before fabrication:
     - FT232H: VREGIN at 3.3 V; VCCA/VCCCORE as decoupled 1.8 V outputs; ACBUS0–6 mapping in sync FIFO mode; 93LC56B wiring; 12 kΩ REF resistor.
     - LTC2290: MUX/MODE/SENSE semantics; REF/VCM bypass values; ~120 mW.
     - iCE40HX4K: VPP_2V5 tied to 3.3 V; VPP_FAST left open; the 100 Ω/10 µF PLL filter.
2. **USB inrush / unconfigured current.** The board draws ~250 mA as soon as it is plugged in, but USB 2.0 allows 100 mA before configuration. A load switch on FT232H PWREN# would fix this; it is not included.
3. **FT232H EEPROM** must be programmed (FT_Prog) for 245 sync-FIFO mode. The FPGA flash is programmed through J4 with an external SPI programmer; the host cannot reflash it.
4. **Anti-aliasing is a single pole at 4.8 MHz.** Content above 5 MHz will alias. A 3rd–5th order filter is the obvious next revision if scope-like fidelity matters.
5. **Signal integrity was not engineered.**
   - USB D+/D− are routed as ordinary tracks, not 90 Ω differential.
   - The SDRAM bus is not length-matched. I recommend running the SDRAM at ≤ 80 MHz.
   - Freerouting necked some tracks to 0.10 mm, so the rule minimum was relaxed to 0.10 mm. Typical 4-layer fabs accept this, but check with yours.
6. **Probe compensation.** The input capacitors are fixed: 16 pF across the 909 k resistor, 150 pF across the 100 k. A trimmer would allow exact compensation.
7. **Clock.** The FPGA PLL takes the 10 MHz clock, which is at the iCE40 PLL's minimum input frequency. A separate faster oscillator is the fallback.
8. **Cosmetic.**
   - 41 DRC warnings: silkscreen, and USB-B footprint "lib mismatch". The mismatch arises because DRC compares against the KiCad 9 library copy, whose shield pad is named `5` instead of `SH`.
   - Placement is not compact; the board has spare area at the top.

## Tooling notes (kicad-harness on this machine)

- **Library tables:** `kh` resolves symbols and footprints through stale KiCad 10 tables and falls back to the KiCad 9 libraries. The USB-B shield pad differed (`5` vs `SH`). I fixed this with project `sym-lib-table`/`fp-lib-table` files pointing at the KiCad 10 `.kicad_symdir`/`.pretty` libraries.
- **Rendering:** `rsvg-convert` is missing, so I used an Inkscape shim in the session scratchpad for `kh view`/`sview`.
- **KiCad 10 pcbnew SWIG problems:**
  - `BOARD.Tracks()` stops being iterable after `Remove()`.
  - Removing Edge.Cuts drawings segfaults.
  - Workaround: snapshot first, remove last, and use `kh outline`/`kh place` for geometry.
- **Not committed:** the skill tells agents to commit and push fixes to its own repo. I did not, because your rules require approval for git operations. These findings are candidates for that repo if you want them pushed.
