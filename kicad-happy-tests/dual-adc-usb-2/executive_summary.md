# Executive Summary: dual-adc-usb-2

## Task
Design a dual-channel ADC board from a blank slate, per `dual-adc-prompt.txt`:
- inputs of ±10 V;
- 10 MSPS at 12 bits;
- at least 0.1 s of capture at full rate;
- inputs that accept oscilloscope leads;
- USB 2.0 for power and data, with USB-C only if power is short.

Design decisions were to be made without stopping for input. The tools used were KiCad 10.0.4, SKiDL 3.0, Freerouting 2.4.1 and the kicad-happy 2.3.1 analysis plugin.

## Outcome
A complete KiCad 10 project: hierarchical schematic, routed 4-layer PCB, fab outputs and design review.

| Check | Result |
|---|---|
| KiCad ERC | **0 violations** |
| KiCad DRC | **0 errors, 0 unconnected**; 19 warnings, all cosmetic (18 silkscreen, 1 library-copy note) |
| Schematic ↔ PCB parity | **0 mismatches** |
| Schematic netlist vs SKiDL source | **identical** (172/172 multi-pin nets) |
| BOM | 187 parts, 61 lines, **100 % with MPNs** |
| SPICE (kicad-happy, ngspice) | 33 pass, 2 warn (both triaged as false positives), 0 fail |

**Status: buildable prototype, not yet cleared to order.** The open items are listed under *Risks and open items*.

## The design
| Requirement | How it's met |
|---|---|
| ±10 V, 2 channels, scope leads | BNC inputs at 1 MΩ ∥ ≈20 pF. A compensated /10 divider feeds an OPA810 buffer, then a THS4521 differential driver. Full scale is ±10.6 V, and up to ±100 V with a 10× probe. |
| 10 MSPS, 12 bits | LTC2291 dual 12-bit ADC (rated to 25 MSPS), clocked by a dedicated low-jitter 10 MHz oscillator. |
| ≥ 0.1 s at full rate | iCE40HX4K FPGA with an 8 MB SDRAM buffer, which holds **0.2 s** of both channels. |
| USB 2.0 data and power | FT2232H High-Speed bridge. Channel B is a data FIFO; channel A reprograms the FPGA's flash over USB with `iceprog`. |
| USB-C only if needed | Estimated draw is about 1.4 W, against the 2.5 W USB 2.0 budget. **USB-C wasn't needed**; the board uses a USB-B connector. |

Power comes from USB 5 V through:
- a 3.3 V buck for the digital logic;
- a 1.2 V LDO for the FPGA core;
- a low-noise 3.3 V LDO for the ADC;
- a ±3.3 V charge pump for the analog buffers. The FPGA switches it on after USB enumeration.

The board is 130 × 90 mm on 4 layers: signal / GND plane / 3.3 V plane / signal.

## How it was done
1. **Architecture.** For each major choice I listed the options and picked one:
   - capture architecture
   - memory
   - controller
   - USB bridge
   - ADC
   - front end
   - power tree
   - clocks
   - connector
   - stackup

   Each decision is recorded in `design_decisions.md`. Parts were limited to those with symbols in the KiCad 10 library.
2. **Datasheet checks.** TI, Lattice, ISSI and Diodes datasheets were downloaded and used to set component values and pin connections.
3. **Circuit capture in SKiDL** (`dual_adc_usb.py`), the single source of truth.
4. **Schematic generation.**
   - SKiDL's built-in generator (schematizer) **produced an electrically wrong schematic**. It merged GND with +3V3, dropped pins and raised 910 ERC violations.
   - I wrote a replacement, `scripts/sch_writer.py`. It ties every pin to a net label, power symbol or no-connect flag.
   - The replacement's output was checked by exporting KiCad's netlist and comparing it pin-for-pin with SKiDL's.
5. **PCB.** The layout pipeline is all in `scripts/`:
   - a placement script;
   - one plane via for every ground/3.3 V pad;
   - a pre-routed USB pair;
   - Freerouting, kept on the outer layers so the planes stay solid;
   - a custom A* router with rip-up to finish the last connections.

   Several layout problems were fixed at the source:
   - FPGA pins were reassigned to untangle the buses.
   - The FT2232H was rotated, which cut the USB lines from about 35 mm to about 10 mm.
   - The ADC bus got a finer net class.
6. **Review.** The full kicad-happy suite ran: schematic, PCB, cross-domain, EMC, thermal, Gerber, SPICE and lifecycle. Findings were triaged into real issues and false positives in `design_review.md`.
7. **Outputs.**
   - `fab/`: Gerbers, drill, BOM, placement file.
   - `docs/`: 3D renders and assembly drawings.
   - `gateware/dual_adc_usb.pcf`: the FPGA pin constraint file.

## Risks and open items (before ordering)
1. **Two critical datasheets weren't available:** the LTC2291 (analog.com timed out) and the FT2232H (ftdichip.com returned 403). Their pin-level wiring is unverified and must be checked.
2. **The ADC bus uses 0.1 mm track and space,** which needs an advanced fab process tier. JLCPCB's 4-layer service supports it.
3. **Anti-aliasing is only 2nd order.** Signals above 5 MHz will alias. The cheapest fix is to sample at 20 MSPS and decimate in the FPGA.
4. **EMC risk is high** per the analyzer. Most of it comes from having only two signal layers; a 6-layer board is the real fix.
5. **USB lines aren't impedance-controlled.** They're short, but the fab should be asked for a 90 Ω differential stackup.
6. **Not done:** FPGA gateware, host software, test points, lifecycle check (no distributor API keys) and signal-integrity simulation.

## Where to look
- `README.md`: project map and regeneration commands.
- `design_decisions.md`: options considered and choices made.
- `design_review.md`: full review with verdict, findings and false-positive triage.
- `kicad/`: the KiCad 10 project.
- `fab/`, `docs/`, `gateware/`: fabrication, documentation and FPGA outputs.

Nothing was committed to git.
