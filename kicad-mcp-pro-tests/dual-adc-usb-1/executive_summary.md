# dual-adc-usb-1 — executive summary

## What was done

Four short prompts in one session tried out kicad-mcp-pro (v4.1.0, `kicad-pro` plugin) as an
**analyzer and fab-output generator** on an existing design. Claude did not change the design.
The prompts asked Claude to:

1. Use kicad-pro to analyze the project.
2. Output Gerber files for JLCPCB.
3. Generate the BOM and pick-and-place files for JLCPCB.
4. Render a PNG of the PCB showing front/back traces, footprints, silkscreen and the board edge
   on a dark-gray background.

KiCad 10.0.4 was used via `kicad-cli` only. The live KiCad (IPC) connection was not available,
so every kicad-pro tool fell back to reading the files directly.

## Results

| Item | Result |
|---|---|
| Board | 140 × 90 mm, 4 layers, 174 footprints, 214 nets, 2,501 track segments, 493 vias, 2 filled inner-layer zones. Fully routed. |
| ERC | 0 errors, 203 warnings: 201 "symbol library not in configuration", plus 2 pin conflicts. |
| DRC | 0 errors, 0 unconnected items, 343 warnings: 170 footprint/library mismatches, 173 silkscreen. |
| kicad-pro quality gate | **FAIL**. Most of its blocking items are false positives (below). |
| Gerbers / drill | `mcp_out/gerber/` (all layers) and `mcp_out/dual_adc_usb_jlcpcb.zip` (the 13 files JLCPCB needs). |
| BOM / CPL | `mcp_out/jlcpcb/dual_adc_usb_BOM.csv` (56 lines, 170 parts) and `dual_adc_usb_CPL.csv` (170 placements, mm). |
| Image | `mcp_out/render/dual_adc_usb_pcb.png` (3120 × 2049) and `pcb.svg`. |
| ERC/DRC reports | `mcp_out/erc_report.json`, `mcp_out/drc_report.json`. |
| Cost / time | $2.07 equivalent API cost (`claude_cost.txt`). About 5 min of model working time; 8:49 to 9:05 wall clock. |

## Main findings

### Real issues (all warnings)

- **Stale global symbol-library table.** `~/.config/kicad/10.0/sym-lib-table` points to a
  temporary AppImage folder (`/tmp/.mount_kicad…`) that no longer exists. This causes all 201
  ERC library warnings. It is a problem with this machine's setup, not the design.
- **U603 (W25Q32 flash) WP/IO2 and HOLD/IO3 are tied directly to +3V3.** This is fine for
  single or dual SPI, but it rules out quad mode. Pull-ups would keep that option open.
- **170 footprints differ from the current library copies.** This is library drift and harmless
  unless you want the footprints updated.
- **173 silkscreen warnings:** silk over copper, silk-to-silk clearance, and silk clipped by the
  board edge. All cosmetic; JLCPCB clips silk that lands on pads.
- **BNC connectors J101/J201 overhang the left board edge by about 21 mm.** This is expected for
  horizontal edge-mount BNCs. Confirm it against the enclosure.

### kicad-pro gate failures that were checked and are false positives

| Gate claim | What was actually found |
|---|---|
| 176 "isolated" symbols with no connectivity | The schematics connect parts with labels rather than wires. The KiCad netlist has 748 pin connections, and DRC shows 0 unconnected items. |
| PCB transfer only 92.9 %, 53 pad-net mismatches | Pins with no connection get an automatic `unconnected-(…)` net name, which is normal KiCad behaviour. The tool expects no net at all. |
| H1–H4 missing from schematic | M3 mounting holes that exist only on the board, which is normal. |
| J501 (USB-B) 7.33 mm from the board edge | The tool measured from the connector's anchor point. Its outline reaches y = 50.1 and the edge is at y = 50, so it sits at the edge. |
| Decoupling caps 7.7–15.7 mm from U301/U501/U502/U601/U602 | The tool measured from part centres. Measured pad to pad on the shared supply net, the nearest caps are about 2.7–3.8 mm away (rough script). U501 is a USBLC6 ESD chip and doesn't need a local cap. |
| Part overlaps (C101/J101 and others) | DRC reports 0 courtyard overlaps; the tool is probably comparing rough bounding boxes. |
| J601 outside the board | DRC does not flag it. This was **not conclusively checked**. |
| DFM: layer count, track width and via drill "unavailable" | These checks need the live KiCad connection. Checked by hand instead: the minimum track is 0.15 mm, the clearance rule is 0.15 mm, and all vias are 0.6/0.3 mm. These look within JLCPCB's standard 4-layer limits (quoted from memory). |

### Fab-package caveats

- **No LCSC part numbers.** The symbols have no LCSC, MPN or manufacturer fields, so all 56 BOM
  lines must be matched by hand in JLCPCB's web tool.
- **Likely not stocked at JLCPCB** (a judgement from experience; stock was not checked): LTC2290,
  ADA4817, THS4521, FT2232HL, iCE40HX4K, W9812G6KH, LM27762, the 0.1 % resistors, the TZB4
  trimmers and the BNCs.
- **CPL rotations are KiCad's raw values and were not checked** against JLCPCB's part
  orientations. Check each placement in their preview before ordering.
- The through-hole parts J101, J201, J501 and J601 are included in the BOM/CPL, and JLCPCB charges
  extra to assemble them.
- All outputs are **draft files that nobody has approved for production**. kicad-pro labelled every
  export a "debug export" because its own quality gate failed.

## How kicad-mcp-pro held up

- **Used for:** project setup, board summary, ERC, DRC, footprint-vs-schematic parity, the
  project quality gate, the JLCPCB DFM profile check, and the Gerber, drill, BOM and
  pick-and-place exports.
- **Problems:**
  - It refuses output directories outside the project folder, so the outputs went into
    `mcp_out/` inside the project.
  - The server lost its active project once between prompts and had to be reset.
  - The ERC and DRC results were too large to return in one response and had to be read from
    saved files.
  - The pick-and-place export came out in inches. JLCPCB wants millimetres, so it was redone with
    `kicad-cli`.
- **Gate quality:** the gate has many checks, but on this board **it reported more false alarms
  than real findings**. Many of its checks measure from part centres or bounding boxes, assume
  parts are connected by wires rather than labels, or need a live KiCad connection. Its
  suggested fixes (e.g. "run sch_annotate", "pcb_place_decoupling_caps") did not match the
  actual causes. Every gate claim needed checking against the netlist or the board file.
- **Not done with kicad-pro:**
  - Converting the BOM and CPL into JLCPCB's column layout (a short Python script).
  - The mm pick-and-place export, the PNG render (`kicad-cli` SVG plus cairosvg and ImageMagick)
    and the checks above. The render tools couldn't choose layers or a background colour.
