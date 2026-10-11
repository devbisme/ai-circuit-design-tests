# dual-adc-usb-2 — executive summary

## What was done

Claude designed the board from a blank slate using the KiCad backend of eda-agent
(commit 8e659a2, v0.6.1) and KiCad 10.0.4. The design brief was `dual-adc-prompt.txt`:
2 channels, ±10 V input, 10 MS/s, 12 bits, at least 0.1 s of capture, scope-lead inputs,
and USB 2.0 for both power and data. The work went:

1. Choose the architecture and parts (`design_decisions.md`).
2. Write the netlist as an eda-agent DesignPlan (`plan/dual_adc_plan.json`) with a script.
3. Check it with eda-agent's `design_validate_plan` and `design_review_plan`.
4. Generate a project with eda-agent's `kicad_generate_project` (`eda_agent_raw/`).
5. Replace the generated schematic with a script-written one, because eda-agent's had no
   connections.
6. Turn eda-agent's board into a 4-layer board, then place and route it with scripts and
   Freerouting.
7. Run the final review and Gerber/drill/3D export with eda-agent's IPC tools.

## The design

| Block | Choice |
|---|---|
| Inputs | 2 × BNC, 1 MΩ compensated ÷11 divider (±10 V → ±0.91 V), BAV99 clamps |
| Driver | OPA1656 unity buffer (±4 V), then a THS4521 FDA (3.3 V, gain 1, VOCM from the ADC) |
| ADC | LTC2290: dual 12-bit 10 MS/s, 2 Vpp differential, clocked by a 10 MHz Abracon ASE XO |
| Capture | iCE40HX4K-TQ144 FPGA plus a 32 MB MT48LC16M16A2 SDRAM (0.8 s at full rate; 8× the requirement) |
| USB | FT232H in 245 sync-FIFO mode (USB 2.0 HS), 93LC56B EEPROM, USBLC6 ESD, USB-B receptacle |
| Power | Bus powered, ~330 mA estimated. AP2112K 3.3 V and 1.2 V; LP5907 3.3 V analog; LM27762 ±4 V. |
| Config | W25Q32 SPI flash and a 2×4 iceprog-style header |

Capture-then-upload was chosen because streaming 40 MB/s is at or past the practical
limit of USB 2.0. USB-C was not needed: the estimated draw is well under 500 mA.

## Results

| Item | Result |
|---|---|
| Size | 179 parts, 185 nets |
| Schematic | 7 sheets, **ERC 0**. kicad-cli netlist matches the plan exactly. |
| PCB | 125 × 95 mm, 4 layers (signal / GND / +3V3 with a +3V3A island / signal) |
| DRC | **0 errors, 0 unconnected, 0 schematic-parity issues**; 19 silkscreen warnings |
| eda-agent `kicad_full_review` | 0 errors; 40 warnings, all intended no-connect pins and netless mechanical/paste pads |
| Deliverables | Gerbers, drill, positions (`kicad/fab/`); BOM; schematic and PCB PDFs; 3D render |
| Not done | FPGA gateware and host software |

## How eda-agent held up

eda-agent made a modest contribution; scripts did most of the work.

**What it did well**
- The DesignPlan validator and ERC-lite caught real problems: unparseable values and
  missing VBUS decoupling.
- The board from `kicad_generate_project` had **every pad on the right net** (725/725
  plan pins) with real library footprints. It served as the starting board.
- Once KiCad was reachable, the IPC tools worked: `kicad_full_review` (ERC + DRC +
  schematic review + schematic/PCB compare in one call), Gerber and drill export, and the
  3D render.

**What failed or was missing**
- **The generated schematic is electrically empty.** Its global labels sit on a grid and
  touch no pins: 780 ERC violations and an empty netlist. Multi-unit parts get only unit 1,
  so the FPGA lost 4 of its 5 units.
- **Library lookup needs a running KiCad, and it can't read KiCad 10's libraries.** With
  KiCad closed, it silently falls back to box symbols. It also reads only single-file
  libraries, so it used the system KiCad 9 copies.
- **The generated board was unusable as-is.** It was 2-layer with grid placement, its
  footprint IDs had no library nickname, and its footprints had no links to the
  schematic.
- **There are no KiCad tools for placement, routing, zones, or DSN/SES.** The autonomous
  spec-to-board harness exists only for Altium and EasyEDA.
- **`design_review_plan` misidentifies circuits.** For example, it calls the compensated
  input divider an RC high-pass and an RC low-pass.
- **The IPC tools only connect through `/tmp/kicad/api.sock`.** A stale socket left by a
  closed KiCad blocked the connection until the socket was relinked.

**What filled the gaps.** The scripts are in `scripts/`:
- The schematic was written by a label-based writer.
- Placement used a hand table for ICs and spiral search for passives, with escape bands
  around fine-pitch parts.
- GND/+3V3 pads got locked fanout vias to the inner planes.
- Freerouting needed 4 runs. The first wrote an empty SES because of NPEs from the plane
  polygons; the last left 15 unrouted, most of them already connected through the planes.
- A small A* router closed the final links, after a local re-layout around the LM27762.

KiCad 10's Python API added friction: in-process object mutations broke later SWIG
wrappers, so the scripts run each such mutation in its own process.

## Risks and caveats

- **The FT232H and LTC2290 support circuits were not checked against datasheets.** Both
  downloads failed (FTDI returned 403; analog.com timed out), so these come from memory:
  FT232H power strapping, crystal, REF and EEPROM wiring; LTC2290 SENSE, MODE, MUX and
  REF capacitors.
- **The input compensation capacitors are estimates.** They need trimming on a built board
  with a square wave.
- **Anti-aliasing is weak for 12 bits.** It is first-order, at about 4.8 MHz. The OPA1656
  slew rate (24 V/µs) also limits full-scale sine waves to about 4.2 MHz.
- **The USB 100 mA pre-enumeration limit is not enforced**; there is no load switch on
  PWREN#.
- **The BNC and USB-B edge positions come from footprint courtyards**, not vendor
  mechanical drawings.
- **The layout works but isn't refined.** Placement was scripted and FPGA/SDRAM decoupling
  sits about 2.5 mm from the pins. The SDRAM and FIFO buses have no length matching, which
  is acceptable at their ≤60 MHz rates. The design has not been validated by a human.

## Sources

- TI LM27762 datasheet SNVSAF7C: output equations (1) and (3), pin table, capacitors.
- TI THS4521 datasheet SBOS458H: pinout and 3.3 V common-mode range.
- TI OPA1656 datasheet SBOS901: supply range, slew rate, input bias, common-mode range.
- Nexperia BAV99 datasheet: pinning table. The KiCad symbol's pin names are swapped, so
  it was wired by pin number.
- KiCad 10 library symbols and footprints: pin numbers and land patterns.
- eda-agent source: `tools/kicad.py`, `core/kicad_schematic.py`, `core/kicad_pcb.py`,
  `core/kicad_symbol.py`, `design/plan.py`.
- Run artifacts: `README.md`, `design_decisions.md`, `kicad/drc.rpt`, `kicad/erc.rpt`,
  `plan/review_plan.json`.
