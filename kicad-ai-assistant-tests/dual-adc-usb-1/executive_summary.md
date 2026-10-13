# dual_adc_usb — Design Review & Fab Output Summary (KiCad-AI-Assistant / kcaa)

**Date:** 2026-10-11  **Tool:** KiCad-AI-Assistant `kcaa` 0.2.7 MCP server (full profile), with KiCad 10.0.4 (`~/bin/kicad10-root`)
**Design files were not modified.** The md5 of all 11 `.kicad_*` files was the same before and after the run (`.kicad_pcb` = `1319dddf…`).

## What the design is

A two-channel, 12-bit, 10 MS/s USB acquisition board. It is 140 × 90 mm, has 4 layers, and holds 170 schematic parts plus 4 mounting holes, all on the top side. It has 493 vias (0.6/0.3 mm), and both inner layers are planes: In1 = GND, In2 = +3V3.

| Block | Function (from the netlist) |
|---|---|
| AFE_A / AFE_B | BNC → 953k/49.9k ÷20.1 compensated divider (2.2 pF ‖ 27 pF + 4.5–20 pF trimmer) → BAV199DW clamp to +4V/VEE → ADA4817 follower → THS4521 FDA (G = 953/499 = 1.91, VOCM = ADC VCM) → 49.9 Ω + 220 pF to the ADC. Full scale ≈ ±10.5 V at the BNC (calculated, assuming a 2 Vpp ADC range). |
| ADC | LTC2290 on +3V0. SENSE, MUX = VDD; MODE = 2/3 VDD (10k/20k). One SiT8008 10 MHz oscillator drives the ADC and FPGA GBIN6 through separate 33 Ω resistors. |
| FPGA_SDRAM | iCE40HX4K-TQ144 (SPI-master boot from W25Q32), W9812G6KH SDRAM (16 MB), 2×5 GPIO header, 2 LEDs. |
| USB | FT2232HL. Channel A is a 245 sync FIFO (FT_CLK → GBIN0). Channel B is SPI to the flash, CRESET and CDONE. 93LC56 EEPROM, 12 MHz crystal, USBLC6 ESD, USB-B. |
| Power | VBUS → ferrite → +5V. TPS62160 → +3V3, TLV75512 → +1V2, LP5907 → +3V0, LM27762 → +4V/VEE. +3V0 and ±4V are enabled by FT2232H PWREN# through Q401. |

## What was done

1. **kcaa review tools.** In order: `get_project_structure`, `validate_project`, `run_erc` (all severities), `check_reference_conflicts`, `get_board_info`, `get_effective_design_rules`, `list_zones`, `get_board_outline`, `score_placement`, `get_ratsnest`, `find_footprints_not_in_libraries`, `identify_circuit_patterns` (root and each sub-sheet), `extract_schematic_netlist`, `find_component_connections`, `analyze_bom`, `export_bom_csv`, `export_pcb_layer_image`, `generate_pcb_thumbnail`, `list_skills` and `check_kicad_ipc_connection`. Several of them failed or gave wrong answers on this design (see **kcaa observations**).
2. **Fallbacks for kcaa's gaps, all read-only:**
   - **DRC.** kcaa has no headless DRC, so I ran DRC with schematic parity using KiCad 10 `kicad-cli`.
   - **Netlist.** kcaa's netlist tools returned no pins, so I exported a KiCad 10 netlist and dumped every IC's pin-to-net map by script (`reports/pinmap.txt`).
   - **Board geometry.** A KiCad 10 pcbnew Python script measured decoupling distances, critical-net lengths and layers, widths, attributes and silk (`reports/pcb_geometry.txt`).
3. **Datasheets.** The TI LM27762 (SNVSAF7C) and Diodes BAV199DW (ds30417) datasheets were downloaded and read. analog.com timed out on the LTC2290 and FTDI returned 403 for the FT2232H, so **claims about those two parts are from memory** and are marked that way.
4. **Fab outputs**, all with KiCad 10 `kicad-cli` (listed at the end).

## Results

### ERC / DRC / parity
- **kcaa `run_erc`: 0 errors and 203 warnings.**
  - 201 are `lib_symbol_issues` ("configuration does not include the symbol library 'Device'…"). This is an environment artifact of the global library table, not a design fault. Because of it, the symbol-vs-library comparison didn't really run.
  - 2 are flash WP#/HOLD# tied to the +3V3 PWR_FLAG. These are benign.
- **DRC (KiCad 10 CLI): 0 errors and 0 unconnected items. 343 warnings:**
  - 170 `lib_footprint_mismatch` (environment)
  - 94 silk over copper
  - 71 silk overlap
  - 8 silk-to-edge
- **Parity:** 170 Datasheet-field mismatches (noise), plus 4 extra footprints: mounting holes H1–H4, which aren't in the schematic, as expected.
- **No duplicate references** (kcaa `check_reference_conflicts`).

### Checked and found correct
- **BAV199DW clamp is correct, though KiCad's symbol suggests otherwise.** KiCad's pin names put DIV on the unused pair's junction (pin 6 = "K3A4"). The Diodes top-view internal schematic shows pin 1 (A1) → pin 6 (AC1) → pin 2 (C1) as one series pair. So VEE → DIV → +4V clamps correctly. The symbol is still misleading to anyone reading the schematic. *Verified against the datasheet.*
- **Rail voltages:**
  - +4V = 1.2·(1+115/49.9) = 3.97 V and VEE = −1.22·(1+115/49.9) = −4.03 V. The 1.2 V and −1.22 V references are verified in the LM27762 datasheet.
  - +3V3 = 0.8·(1+316/100) = 3.33 V. The TPS62160 0.8 V reference is from memory.
- **Divider compensation.** 953k·2.2p = 2.10 µs needs ≈42 pF at DIV. That is 27 pF + about 3 pF of strays and buffer input, plus about 12 pF of trimmer, which sits mid-range in the 4.5–20 pF trimmer.
- **Power-gating polarity.** PWREN# goes low after enumeration → Q401 off → AN_EN pulled high → LP5907 and LM27762 enabled.
- **iCE40:**
  - SS pull-up → SPI-master boot, with SDO→flash DI and SDI←flash DO.
  - CRESET and CDONE pull-ups. FT2232H channel B can hold CRESET low and reprogram the flash.
  - VCCPLL0/1 have 100 Ω + 10 µF + 100 nF filters, and VPP_2V5 is on 3.3 V.
- **FT2232H:**
  - 12 kΩ on REF, VREGOUT→VCORE, TEST→GND.
  - EEPROM in x16 mode (ORG high), with DO joined to DI through 2.2 k.
  - The sync-FIFO strobes are on ACBUS, and CLKOUT goes to global buffer GBIN0.
- **SDRAM, ADC and FPGA bus mapping.** The pin maps are complete and one-to-one (A0–A11, BA0/1, DQ0–15, DQM, both ADC buses + OF). The iCE40 banks are partitioned by function: ADC on bank 3, SDRAM on bank 1, FTDI on bank 0.

### Issues found (ranked; confidence noted)

**Architectural**
1. **The FPGA has no guaranteed clock before USB enumeration, and the ADC can be back-powered.**
   - X301 (Vdd and OE) runs on the gated +3V0 rail, and FT_CLK runs only once the host puts channel A into sync-FIFO mode. Until both happen, the FPGA has no clock source.
   - The LTC2290 (VDD and OVDD on +3V0) is unpowered while iCE40 bank 3 is at 3.3 V. Any FPGA pull-up or driven pin facing ADC_A*/ADC_B* can back-power it through its output ESD diodes.

   *Netlist facts: high confidence. Impact depends on the gateware.* **Fix:** power X301 from +3V3, or ungate +3V0. In the gateware, keep the bank 3 inputs pull-up-free.
2. **The ADC inputs can be overdriven.**
   - The THS4521 runs from 0/+4 V and drives the 3.0 V LTC2290 through only 49.9 Ω.
   - Above about ±38 V at the BNC (calculated), the positive FDA output heads toward +4 V. The DIV clamp doesn't engage until about ±94 V (±4.7 V at DIV).
   - This exceeds the ADC's analog-input abs max, which I recall as ≈VDD+0.3 V.

   *Medium confidence: the abs-max value is from memory.* **Fix:** add Schottky clamps at AIN±, or run the FDA from +3.3 V.
3. **USB throughput is marginal for continuous streaming.** 2 × 10 MS/s × 12 bit is 30 MB/s packed, or 40 MB/s as 16-bit words, against a practical FT2232H sync-FIFO rate of about 35–40 MB/s. The 16 MB SDRAM buffers only about 0.4–0.5 s. *Low–medium confidence: FTDI figures from memory.*
4. **FT2232H channel B is likely unavailable while channel A is in sync-FIFO mode.** If so, the flash and CRESET can be reached only outside streaming sessions. *About 75% confidence, from memory; the datasheet download was refused.*

**Datasheet deviations (verified, minor)**
5. **LM27762 feedback resistors.** R406 and R408 are 49.9 kΩ, but the datasheet says "R2 must be no less than 50 kΩ" (and the same for R4). The margin is 0.2%, so this is a technicality, but 51 kΩ with ≈118 kΩ top resistors would satisfy it.
6. **LM27762 PGOOD** (U404 pin 1) is left NC. The datasheet says "Connect pin to ground if PGOOD is not used."

**Physical design** (`reports/pcb_geometry.txt`: straight-line distance from a supply pin to the nearest same-net capacitor pad)

7. **Decoupling is far from the IC pins; this is the main PCB weakness.**

   | IC | Supply pins > 5 mm from a cap | Worst |
   |---|---|---|
   | iCE40 U601 | 14 of 16 | 22.2 mm |
   | LTC2290 U301 | 9 of 9 | 10.8 mm |
   | FT2232H U502 | 7 of 11 | VCORE, 16.2 mm |
   | SDRAM U602 | 5 of 7 | 14.1 mm |
   | THS4521 U102/U202 | 2 of 2 | 8.3 mm |

   Regulator output caps are also far: C402 (buck output) is 9.4 mm away and C409 (VEE) 9.8 mm. kcaa's `score_placement` agrees in aggregate (mean decap proximity 6.0 mm), though its "worst contributors" list ranks by net-centroid displacement and names regulator caps instead. *High confidence on the geometry.*
8. **The anti-alias caps C106 and C206 are 15–18 mm from the ADC pins.**
   - AIN± run 19–23 mm, about 15 mm of it on B.Cu.
   - B.Cu's adjacent plane is In2 = +3V3, not GND.
   - The RC can't absorb sampling kickback at the pins, and the inputs reference a digital supply plane.

   *High confidence on the geometry; medium on the impact.*
9. **The differential paths are asymmetric.** FDA_OUTP is 15–16 mm with 2 vias, while FDA_OUTN is 8.6 mm with none. VCMA and VCMB are 40–43 mm, mostly on B.Cu.
10. **The high-impedance DIV nodes are long.** /AFE_A/DIV is 39 mm. /AFE_B/DIV is 36 mm with 3 vias, so the two channels differ in parasitics and the trimmer settings will differ.
11. **USB D+/D− aren't routed as a pair.** D+ takes a via and runs 4.5 mm on B.Cu; D− stays on F.Cu. Widths vary from 0.20 to 0.28 mm, and there is no diff-pair net class (only Default exists). The run is short (≈20 mm), so the impact at HS is modest. *Medium confidence.*
12. **The FT2232H crystal traces are long.** OSCI and OSCO run 15–16 mm from Y501 to U502.
13. **No stackup is defined** in the board file (no `(stackup …)` section). Impedance-controlled nets (USB) will follow whatever the fab assumes. Specify JLC's 4-layer stackup (e.g. JLC04161H-7628) if USB HS margin matters.

**Manufacturing (JLCPCB)**
14. **Silkscreen.**
    - All 463 footprint silk strokes are 0.12 mm, below JLC's recommended ≈0.15 mm (from memory).
    - DRC reports 165 silk-overlap and silk-over-copper warnings, plus 8 silk-to-edge. Reference designators collide around the ADC and FPGA (see the PNG).
15. **The BOM is not orderable as-is.** The schematic has no MPN, Manufacturer or LCSC fields, so the `LCSC Part #` column is empty. Check sourcing first for LTC2290, ADA4817, THS4521, iCE40HX4K-TQ144, FT2232HL, W9812G6KH, SiT8008, the Murata TZB4 trimmers and the Amphenol BNCs.
16. **The footprints have no SMD/THT attribute** (all 174 are "unspecified"). I excluded the four through-hole connectors (J101, J201, J501, J601) from the BOM and CPL by hand and listed them in `THT_parts_not_in_assembly.csv`. Hand-solder them, or order JLC THT assembly.
17. **CPL rotations are KiCad's.** Some JLC package zero-orientations differ (QFN, QFP, SOT, TSOP), so check JLC's placement preview. No aux origin is set, so the coordinates are absolute (Y negative); JLC aligns the file to the board.
18. **The BNCs overhang the left edge by about 20 mm** (by design; visible in the PNG). Confirm panelization and enclosure clearance.

**Fab parameters are within JLC's standard 4-layer capability** (from memory):
- Minimum track 0.15 mm (14 segments, allowed by the `.kicad_dru` rules) and clearance 0.15 mm
- One via size, 0.6/0.3 mm
- Minimum drill 0.3 mm
- Mask expansion 0.05 mm

### kcaa observations (tool behaviour)
- **Worked well:**
  - `run_erc` is headless (KiCad 10 CLI) and structured.
  - `check_reference_conflicts`, `get_effective_design_rules` (it reports the `.kicad_dru` custom rules), `list_zones` and `get_board_outline` gave correct results.
  - `export_pcb_layer_image` is a fast pure-Python render and handy for visual checks. Its output is in `reports/kcaa_export_pcb_layer_image.png`.
- **Wrong or empty on this design:**
  - **`extract_schematic_netlist`** returned every component with `pins: []` and every net with 0 pins, then labelled all 14 power-sheet nets "floating". This design connects almost entirely through labels placed on pin ends (power sheet: 81 labels, 10 wires), and kcaa resolved none of them.
  - **`find_component_connections`** looks only at the root sheet; it found 6 "components", which are the sheet symbols.
  - **`identify_circuit_patterns`** also reads one sheet at a time and found 0 patterns at the root. Per sheet, its pattern guesses are by name and often wrong:
    - It calls the TPS62160 an LDO, a boost and a buck-boost.
    - It calls the LM27762 an op-amp and a buck.
    - It says Y501 has no load caps, but C502 and C503 are 18 pF.
  - **`get_ratsnest`** reported 6 unconnected +4V pairs at U101/U201 pins 7/8. **This is a false positive.** The tracks end inside the pads, not at their centres, and KiCad DRC reports 0 unconnected.
  - **`get_board_info`** reports `copper_layer_count: 0` on a 4-layer board.
  - **`find_footprints_not_in_libraries`** reports all 30 footprints, including stock `Resistor_SMD` parts, as missing. That is probably because the footprint index wasn't synced (not run).
- **Environment and IPC limits:**
  - **`export_bom_csv` failed** ("Failed to load schematic"). `bom_tools.py` hard-codes `kicad-cli`, so it ignores `KICAD_CLI_PATH` and runs the system KiCad 9, which can't read this KiCad 10 schematic.
  - **`analyze_bom`** works only once a BOM CSV sits next to the project. When I supplied one, it counted 170 parts / 56 lines correctly, but its "categories" are BOM-line counts per footprint, and it gives no cost or sourcing data.
  - **`generate_pcb_thumbnail`** returned nothing and left an empty `temp/` directory, which I removed.
  - **IPC tools:** no KiCad GUI was running (`api.sock` was a dangling link). In any case, `run_drc_check` only opens the DRC dialog and returns no violations, so DRC was done with the CLI.
- **Net:** kcaa is oriented toward building designs (placement, wiring and routing tools, plus skills). Its review and analysis tools are shallow and, on a hierarchical, label-connected KiCad 10 design, often wrong. Most of the review above came from the KiCad 10 CLI, a netlist script, a pcbnew script and the datasheets.

## Output files

| File | Contents |
|---|---|
| `jlcpcb/dual_adc_usb_gerbers_JLCPCB.zip` | Upload to JLC. 4 Cu (In1/In2 as `.g1`/`.g2`; the job file carries the layer order), 2 mask, 2 silk (soldermask subtracted), 2 paste, Edge.Cuts (Protel extensions), a metric Excellon drill file (PTH + NPTH merged) and the job file. Zones were checked and refilled in memory; nothing was saved. |
| `jlcpcb/gerbers/` | Unzipped plot plus the drill map |
| `jlcpcb/assembly/dual_adc_usb_BOM_JLCPCB.csv` | 53 lines / 166 SMD parts, grouped by value + footprint (Comment, Designator, Footprint, LCSC Part # (blank), Quantity) |
| `jlcpcb/assembly/dual_adc_usb_CPL_JLCPCB.csv` | 166 placements (Designator, Mid X, Mid Y, Layer, Rotation), in mm, all Top |
| `jlcpcb/assembly/THT_parts_not_in_assembly.csv` | J101, J201 (BNC), J501 (USB-B), J601 (2×5 header) |
| `dual_adc_usb_pcb.png` | 500 dpi on #303030. Shows F.Cu (red), B.Cu (blue), F/B Fab footprint outlines, F/B silkscreen and Edge.Cuts. The edge is drawn yellow and thickened to 0.35 mm for visibility, and the BNC overhang is not clipped. Rendered from a KiCad 10 SVG with Inkscape. |
| `reports/` | `kcaa_erc.json`, `drc.json` (DRC + parity), `dual_adc_usb.xml` (netlist), `pinmap.txt`, `pcb_geometry.txt`, `bom_kicad_raw.csv`, `pos_raw.csv`, `kcaa_export_pcb_layer_image.png`, `scripts/` (`pinmap.py`, `pcb_geometry.py`, `jlc_assembly.py`) |

## Sources
- kcaa 0.2.7 tool outputs from this session; KiCad 10.0.4 `kicad-cli` (DRC, netlist, gerbers, drill, BOM, position) and pcbnew Python
- kcaa source: `kcaa/tools/bom_tools.py:705` (hard-coded `kicad-cli`)
- TI LM27762 datasheet SNVSAF7C:
  - VFB+ = 1.2 V and VFB− = −1.22 V (Electrical Characteristics)
  - "The value for R2 [and R4] must be no less than 50 kΩ" (Eq. 1/3 discussion)
  - "Connect pin to ground if PGOOD is not used"
- Diodes Inc BAV199DW datasheet ds30417, p.1 "Top View / Internal Schematic"
- **From memory, not verified this session:**
  - LTC2290 abs max, MODE/SENSE meanings and VCM
  - FT2232H sync-FIFO rate and channel-B restriction
  - TPS62160 VFB
  - JLC silk minimum and stackup

  Treat items 2–4, 13 and 14 accordingly.
