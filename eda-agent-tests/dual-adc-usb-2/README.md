# eda-agent run 2: dual-channel USB ADC from the design prompt

This run used the [eda-agent](https://github.com/salitronic/eda-agent) KiCad backend
(commit 8e659a2, v0.6.1) with KiCad 10.0.4. The prompt is `dual-adc-prompt.txt`, and the
design started from a blank slate. Part choices and the trade-offs behind them are in
[`design_decisions.md`](design_decisions.md).

## What came out

| Item | Result |
|---|---|
| Architecture | 2 × BNC (1 MΩ, ÷11 compensated) → OPA1656 buffer → THS4521 FDA → LTC2290 dual 12-bit 10 MS/s ADC; iCE40HX4K FPGA; 32 MB SDRAM (0.8 s capture); FT232H USB 2.0 HS sync FIFO; USB-B, bus powered (~330 mA est.) |
| Parts / nets | 179 parts, 185 nets (plus 39 no-connect pins) |
| Schematic | 7 sheets (root + power, usb, frontend, adc, fpga, memory), **ERC 0 violations**. kicad-cli netlist matches the plan net-for-net. |
| PCB | 125 × 95 mm, 4 layers (F.Cu signal / In1 GND / In2 +3V3 with +3V3A island / B.Cu signal), 0.45/0.2 mm vias, 0.2 mm tracks (0.4 mm power class) |
| DRC (`kicad/drc.rpt`) | **0 errors, 0 unconnected, 0 schematic-parity issues**; 19 silkscreen warnings |
| eda-agent `kicad_full_review` | 0 errors. The 40 warnings are the intentional no-connect single-pin nets plus netless mechanical/paste pads. |
| Outputs | `kicad/fab/` (Gerbers, drill, positions), `kicad/dual_adc_bom.csv`, `kicad/dual_adc_schematic.pdf`, `kicad/dual_adc_pcb_top.pdf`, `kicad/dual_adc.png` (3D) |

Not done: FPGA gateware and host software. The design captures to SDRAM and then uploads,
and the gateware that does this has not been written.

## How the work split between eda-agent and scripts

| Step | Done by |
|---|---|
| Part/topology decisions, datasheet reading | Claude (`design_decisions.md`) |
| Netlist as an eda-agent **DesignPlan** (`plan/dual_adc_plan.json`) | `scripts/build_plan.py`; it is the single source of truth |
| Plan validation / review | eda-agent `design_validate_plan`, `design_review_plan` (`plan/review_plan.json`) |
| Project generation | eda-agent `kicad_generate_project` → `eda_agent_raw/` |
| Connected schematic | `scripts/sch_writer.py` (eda-agent's schematic is not usable, see below) |
| PCB: 4 layers, FPIDs, symbol links, placement | `scripts/build_pcb.py` + `board_sync.py`, starting from eda-agent's board (its pad nets were correct) |
| Plane fanout, DSN | `scripts/route_prep.py` |
| Routing | Freerouting 2.4.1 CLI (4 runs; the final run left 15 unrouted, most of them plane-connected) |
| Leftovers + local repair | `fix_unrouted.py` (grid A*), `surgery_lm27762*.py`, `cleanup_board.py` |
| Final review, Gerbers, drill, 3D render | eda-agent `kicad_full_review`, `kicad_export_gerbers`, `kicad_export_drill`, `kicad_render_3d` |

The large eda-agent calls (DesignPlan ≈ 50 kB) went through `scripts/mcp_call.py`. It
invokes the same registered tool functions in-process instead of pasting the JSON into
MCP calls. The review/export calls at the end were ordinary MCP calls.

## eda-agent findings (KiCad backend)

What worked:
- The DesignPlan schema, validator and ERC-lite caught real problems: unparseable values
  like `909k 0.1%` and missing VBUS decoupling.
- `kicad_generate_project` produced a board whose **pad nets matched the plan exactly**
  (725/725 pins), with real library footprints.
- The IPC tools all worked once KiCad was running: `kicad_full_review` (ERC + DRC +
  schematic review + sch/PCB compare in one call), Gerber/drill export and 3D render.

What did not:
1. **The generated schematic has no connectivity.** `build_schematic` drops one global
   label per net on a grid below the parts, and none of them touch a pin. Results: ERC
   780 violations (184 dangling labels, 516 unconnected pins) and an empty netlist.
   Only unit 1 of multi-unit parts is placed: the FPGA has 5 units and the OPA1656 has 3.
2. **The symbol and footprint resolvers need a *running* KiCad** to find `kicad-cli`. With
   KiCad closed they silently fall back to generated box symbols and footprints. The
   symbol resolver also only reads single-file `<lib>.kicad_sym` libraries. Here it
   picked up the system KiCad 9 libraries, not KiCad 10's `.kicad_symdir` libraries.
3. The generated board is 2-layer, its parts sit on a grid, its FPIDs lack the library
   nickname, and its footprints have no symbol paths. DRC schematic parity fails on every
   part.
4. There is no placement, routing, zone, or Specctra DSN/SES support on KiCad. The
   autonomous spec-to-board harness is Altium/EasyEDA only (`setup.md`).
5. `design_review_plan` misreads circuits. It calls the compensated input divider an
   "RC high-pass 648 kHz" and "RC low-pass 14.6 kHz", and the FDA feedback Rf‖Cf an
   "RC high-pass 4.8 MHz".
6. The IPC tools connect only through `/tmp/kicad/api.sock`. When a stale socket was left
   behind, a new pcbnew listened on `api-<pid>.sock` and the tools reported "connection
   refused" until the socket was relinked.

## Open items / risks (please check before fabrication)

- **FT232H and LTC2290 support circuits are not verified against their datasheets.** Both
  downloads failed. See `design_decisions.md` → Sources.
- Input compensation caps (2.7 pF / 22 pF / 12 pF) are estimates and need trimming on the
  built board.
- Anti-aliasing is first-order (~4.8 MHz), which is weak for 12 bits. The OPA1656 slew
  rate limits full-scale sine waves to ~4.2 MHz.
- USB inrush and the 100 mA pre-enumeration limit are not enforced; there is no load
  switch on PWREN#.
- The BNC and USB-B edge positions come from footprint courtyards, not from vendor
  drawings, so check them against the enclosure/panel.
- Layout quality: placement is scripted (spiral search). FPGA/SDRAM decoupling sits
  ~2.5 mm out from the pins to leave escape channels, and Freerouting traces are
  serviceable rather than pretty. No length matching on SDRAM or FIFO buses (60 MHz
  max). 19 silkscreen warnings remain. Passive reference designators were moved to F.Fab
  to clear most silk clashes.

## Regenerating

All scripts are in `scripts/`. Run the `python3.11` ones with
`~/bin/kicad10-root/bin/python3.11`.

```
python3 build_plan.py && python3 check_pins.py          # plan + pin coverage
python3 sch_writer.py                                   # schematic (new UUIDs each run)
<eda-agent venv>/python mcp_call.py kicad_generate_project plan_json=@../plan/plan_compact.json output_dir=../eda_agent_raw name=dual_adc
python3.11 build_pcb.py && python3.11 route_prep.py     # placed board, fanout, DSN
freerouting -de route/dual_adc.dsn -do route/dual_adc.ses -mp 40 -mt 1
python3.11 post_route.py && python3.11 fix_unrouted.py <drc report> && python3.11 cleanup_board.py
python3 patch_project.py                                # net classes (pcbnew Save rewrites .kicad_pro)
```

If the schematic is regenerated after routing, run `python3.11 board_sync.py` to
relink the routed board to the new symbol UUIDs. The `surgery_lm27762*.py` scripts are
one-off fixes for this particular routing result.

KiCad 10 python pitfall found here: after `FootprintLoad()` or `BOARD.Remove()`, later
SWIG wrappers in the same process can come back as bare `SwigPyObject`s. The scripts do
each such mutation in its own process.
