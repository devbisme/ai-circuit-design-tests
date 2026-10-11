# dual_adc_usb — Design Review & Fab Output Summary (eda-agent)

**Date:** 2026-10-11  **Tool:** eda-agent 0.6.1 KiCad backend (`mcp__eda-kicad__*`) driving KiCad 10.0.4 (`~/bin/kicad10-root`)
**Design files were not modified.** The `.kicad_pcb` md5 (`1319dddf…`) was the same before and after.

## What the design is

A two-channel, 12-bit, 10 MS/s USB acquisition board. It is 140 × 90 mm, has 4 layers, and holds 170 schematic parts plus 4 mounting holes, all on the top side.

| Block | Parts | Function |
|---|---|---|
| AFE_A / AFE_B | BNC → 953k/49.9k compensated ÷20 divider (+trim cap) → BAV199DW clamp to ±4 V → ADA4817 follower → THS4521 FDA (G = 953/499 = 1.91) → 49.9 Ω / 220 pF RC | ±10.5 V full scale at the BNC (calculated) |
| ADC | LTC2290 (dual 12-bit), SiT8008 10 MHz oscillator (feeds ADC and FPGA), SENSE = VDD, MODE = 2/3·VDD, MUX = VDD | Digitizer |
| FPGA_SDRAM | iCE40HX4K-TQ144, W9812G6KH 16 MB SDRAM, W25Q32 config flash, 2×5 expansion header | Capture/buffer |
| USB | FT2232HL: ch A = 245 sync FIFO (CLKOUT → GBIN0), ch B = SPI to flash/CRESET/CDONE; 93LC56 EEPROM; USBLC6 ESD; USB-B | Host link |
| Power | VBUS → TPS62160 3.3 V → TLV755 1.2 V; LP5907 3.0 V (ADC + oscillator); LM27762 ±4 V (AFE). +3V0 and ±4 V are gated by FT2232H PWREN# via Q401 | Supplies |

## What was done

1. **Connected eda-agent to KiCad.** I started a second standalone pcbnew on this board (another session's pcbnew held the IPC socket). The new instance took over `/tmp/kicad/api.sock`. After the run I closed it and pointed `api.sock` back at the other instance. `kicad_ping` confirmed KiCad 10.0.4 / API 10.0.6 on the right project.
2. **eda-agent review tools:**
   - `kicad_full_review`: ERC, DRC, schematic review, PCB review, and schematic-vs-PCB compare.
   - Board queries: `kicad_get_board_summary`, `get_stackup`, `get_fab_stats`, `get_via_summary`, `list_zones`, `get_layer_usage`, `get_trace_lengths`, `get_diff_pairs`, `get_net_classes`, `list_tracks`, `list_pads`.
   - Impedance: `pcb_calc_impedance` and `pcb_calc_trace_width_for_impedance`.
3. **Full ERC/DRC reports.** `kicad_full_review` caps each list at 200 rows, so I reran ERC and DRC (all severities, schematic parity on) through eda-agent's `kicad_cli` passthrough. Output is in `reports/`.
4. **Netlist review.** I exported the netlist with `kicad_export_netlist` and checked every IC's pin-to-net map by script. All 34 embedded symbols match the stock KiCad library pin-for-pin.
5. **PCB geometry** (fallback, not eda-agent). `kicad_list_pads` returns no component references, so it can't give per-IC decoupling distances. I used KiCad's bundled pcbnew Python, read-only, for those, for per-layer routing of the critical nets, and for silk widths. Script and output are in `reports/scripts/` and `reports/pcb_geometry.txt`.
6. **Datasheets.** The TI LM27762 and Diodes BAV199DW datasheets were downloaded and read. FTDI blocked the FT2232H download (HTTP 403), and analog.com timed out on the LTC2290 and ADA4817. Claims about those parts are **from memory** and marked as such.
7. **Fab outputs** (listed at the end).

## Results

### ERC / DRC / parity
- **No errors. No unconnected items.**
- **DRC: 343 warnings, all cosmetic or library-related:**
  - 170 `lib_footprint_mismatch`
  - 94 silk over copper
  - 71 silk overlap
  - 8 silk-to-edge (BNC, H1, H2)
- **Parity: 174 warnings:**
  - 170 are the `Datasheet` field, `''` vs `'~'`/URL. This is noise.
  - 4 are mounting holes H1–H4, which aren't in the schematic, as expected.
- **ERC: 203 warnings:**
  - 201 are "The current configuration does not include the symbol library 'Device'/'power'/…". This is an environment artifact: the kicad-cli that eda-agent finds can't see the global symbol library table. That also means ERC's normal library-mismatch check didn't run. Probable cause; not investigated.
  - 2 are flash WP#/HOLD# tied straight to +3V3. This is benign.

### Things checked and found correct
- **BAV199DW clamp.** KiCad's pin names suggest DIV sits on the unused pair's junction (pin 6 = "K3A4"). The Diodes ds30417 top-view diagram shows otherwise: pin 1 (A1) → pin 6 (AC1) → pin 2 (C1) is one series pair. So VEE → DIV → +4V clamps correctly.
- **LM27762 rails.** V+ = 1.2·(1+115/49.9) = 3.97 V and V− = −1.22·(1+115/49.9) = −4.03 V, using the datasheet references 1.2 V and −1.22 V.
- **TPS62160 output.** 0.8·(1+316/100) = 3.33 V. The 0.8 V reference is from memory.
- **Divider compensation.** 953k·2.2 pF = 2.1 µs falls within 49.9k·(27 + 4.5…20 pF) = 1.6–2.3 µs, plus strays.
- **iCE40 configuration and power:**
  - SS pull-up (SPI-master boot), CRESET/CDONE pull-ups, and SDO→flash DI / SDI←flash DO are correct.
  - VCCPLL filters (100 Ω + 10 µF + 100 nF) are in place.
  - VPP_2V5 = 3.3 V.
- **FT2232H wiring:**
  - Sync-FIFO pins are on ACBUS/ADBUS, with CLKOUT on a global buffer.
  - 12 kΩ REF; VREGOUT feeds VCORE.
  - EEPROM in x16 mode (ORG high) with the 2.2 k DO→DI join.
  - PWREN# gating polarity is correct: analog rails come on after enumeration.
- **AFE amplifiers.** The ADA4817 EP is on −VS and PD is tied high. THS4521 VOCM is driven from the ADC's VCMA/VCMB.

### Issues found (ranked; confidence noted)

**Architectural**
1. **The FPGA's only free-running clock depends on the gated analog rail.**
   - X301 (Vdd and OE) runs from +3V0, which is off until USB enumeration (PWREN#). Before that, the FPGA's only clock is FT_CLK, which exists only once the host puts channel A into sync-FIFO mode.
   - The LTC2290's OVDD is also on +3V0, while iCE40 bank 3 (3.3 V, powered) faces its outputs. Any FPGA pull-ups or driven pins could back-power the ADC.

   *Facts: high confidence (netlist). Impact: depends on gateware.* **Fix:** power X301 from +3V3, or don't gate +3V0.
2. **ADC inputs can be driven past absolute maximum.**
   - The THS4521 runs from 0/+4 V and feeds a 3.0 V ADC through only 49.9 Ω.
   - Above about ±38 V at the BNC (calculated), one FDA output exceeds about 3.3 V. The diode clamp limits DIV only to the ±4 V rails, which still lets the FDA swing to its +4 V rail.

   *Medium confidence: the LTC2290 abs max (≈VDD+0.3 V) is from memory.* **Fix:** add Schottky clamps at the ADC inputs, or lower the FDA's positive supply.
3. **USB bandwidth is tight.** Two channels × 10 MS/s is 30 MB/s if packed at 12 bits, or 40 MB/s at 16 bits. That is near or above the practical FT2232H sync-FIFO rate (≈35–40 MB/s). The 16 MB SDRAM holds only ≈0.4–0.5 s. *Low–medium confidence: FTDI figures from memory.*
4. **FT2232H channel B is likely unusable while channel A is in sync-FIFO mode.** If so, flash and CRESET access are available only outside streaming sessions. *≈80% confidence, from memory; the FTDI datasheet download was blocked.*

**Datasheet deviations (verified, minor)**
5. **LM27762 bottom feedback resistors.** R406 and R408 are 49.9 kΩ, but the datasheet says R2 and R4 "must be no less than 50 kΩ" (§7.2.2.1). Use 51 kΩ and rescale R405/R407 to ≈118 kΩ.
6. **LM27762 PGOOD** (U404.1) is left NC. The datasheet says to "connect pin to ground if PGOOD is not used" (§7.2).

**Physical design** (geometry from `reports/pcb_geometry.txt`: straight-line distance from IC pad to the nearest same-net capacitor pad)
7. **Decoupling is far from the pins:**

   | IC | Supply pins > 5 mm from a cap | Worst |
   |---|---|---|
   | iCE40 U601 | 14 of 16 | 22 mm |
   | LTC2290 U301 | 11 of 19 | 10.8 mm |
   | FT2232H U502 | 6 of 11 | VCORE, 16 mm |
   | SDRAM U602 | 5 of 7 | 14 mm |

   Regulator output caps are also far: C408/C409 (±4 V) at 8–10 mm, C402 (3.3 V buck) at 9.4 mm. eda-agent's review reported no decoupling problem; it checks that caps exist, not where they are. **This is the biggest PCB-level weakness.** *High confidence on the geometry.*
8. **The anti-alias capacitors aren't at the ADC.**
   - C106 and C206 (220 pF across AIN±) sit 16–18 mm from the LTC2290 pins.
   - The AIN traces after them run ≈15 mm on B.Cu, whose nearest plane is In2 = +3V3, not GND.
   - The filter can't absorb sampling kickback at the pins, and the inputs pick up digital-plane noise.

   *High confidence on the geometry; medium on the impact.*
9. **The FDA output pairs are asymmetric.** FDA_OUTP is 15.4–16 mm with 2 vias, while FDA_OUTN is 8.6 mm with none. FDA_INP is 25 mm vs FDA_INN 17 mm. Expect some differential-to-common-mode conversion. VCMA and VCMB run 40–43 mm, mostly on B.Cu.
10. **The high-impedance divider nodes are long.** /AFE_A/DIV is 39 mm and /AFE_B/DIV is 36 mm with 3 vias. The trim caps C103/C203 are 13 mm from the buffer inputs, which hurts compensation repeatability and noise pickup.
11. **USB D+/D− aren't routed as a pair.**
    - D+ goes through a via with 4.5 mm on B.Cu; D− stays on F.Cu. Widths vary from 0.20 to 0.28 mm.
    - No differential-pair rule is defined; only the Default net class exists.
    - eda-agent calculates Z0 ≈ 99 Ω single-ended for 0.2 mm over the declared 0.48 mm dielectric, against a 45 Ω (90 Ω differential) target.

    The run is short (≈20 mm), so the impact on HS is modest. *Medium confidence.*
12. **The FT2232H crystal is far from the chip.** Y501 has its load caps close by, but OSCI/OSCO run 15–16 mm to the FT2232H. Expect some loss of start-up margin and more EMI.
13. **SDRAM clock length.** SD_CLK is 34 + 20 = 54 mm, including the 33 Ω series resistor, for a part 27 mm away. That is workable at iCE40 speeds, but the skew needs budgeting.
14. **Stackup and planes:**
    - The layers are F.Cu / In1 = GND / In2 = +3V3 / B.Cu. All other rails are 0.25–0.4 mm traces, which is adequate for tens of mA.
    - The stackup leaves dielectric materials undefined, and its 0.48 mm dielectrics don't match JLC's standard 4-layer prepreg (≈0.2 mm, from memory). Specify the stackup if impedance matters.

**Manufacturing (JLCPCB)**
15. **Silkscreen.**
    - All 463 footprint silk strokes are 0.12 mm, below JLC's 0.15 mm minimum (from memory), so they may print faintly.
    - DRC also reports 165 silk overlap/over-copper and 8 silk-edge warnings. Reference designators collide around the ADC and FPGA (see the PNG).
16. **The BOM is not orderable.** The schematic has no MPN, manufacturer or LCSC fields, so the `LCSC Part #` column is blank. Check sourcing first for LTC2290, ADA4817, THS4521, iCE40HX4K, FT2232HL, W9812G6KH, SiT8008, the Murata TZB4 trimmers and the Amphenol BNCs.
17. **The footprints have no SMD/THT attribute.** All 174 have type "unspecified" (fab stats show 0 SMD / 0 THT), so KiCad can't filter the CPL by type. J101, J201, J501 and J601 are through-hole and are included in the CPL. Remove them, or order JLC THT assembly.
18. **CPL rotations** are KiCad's own. Some JLC packages use a different zero orientation (QFN, QFP, SOT), so check in JLC's placement preview.
19. **The BNC courtyards extend about 21 mm past the left edge.** This is by design, but confirm panel and enclosure clearance.

**Fab parameters are within JLC's standard 4-layer capability** (from memory):
- Minimum track 0.15 mm (14 segments) and minimum clearance 0.15 mm
- One via size, 0.6/0.3 mm (493 vias)
- Minimum drill 0.3 mm
- Mask expansion 0.05 mm

### eda-agent observations (tool behaviour)
- **IPC dependence.** Every query needed a live KiCad. The server connects only to `/tmp/kicad/api.sock`, so running two KiCad instances means juggling that socket.
- **`kicad_full_review`** is a useful single call, but:
  - It truncates DRC and ERC to 200 rows each (it showed 22 of 71 silk overlaps).
  - Its schematic and PCB "findings" are 53 deliberate single-pin no-connect nets.
  - Its decoupling check checks only that caps exist, not how far they are from the pins.
- **`kicad_list_pads`** omits component references, which blocks per-part geometry analysis.
- **Exports work but are generic:**
  - `kicad_export_gerbers` plots all 20 layers (adhesive, courtyard, fab, user) with no options.
  - `kicad_export_bom` writes one ungrouped row per part with no fab columns.
  - `kicad_export_pos` writes ASCII in inches.

  The `kicad_cli` passthrough filled each gap (mm CSV position file, SVG plot).
- **The impedance calculators** were handy and gave plausible numbers.

## Output files

| File | Contents |
|---|---|
| `jlcpcb/dual_adc_usb_gerbers_JLCPCB.zip` | Upload to JLC. Contains 4 Cu, 2 mask, 2 silk, 2 paste and Edge.Cuts (Protel extensions), a metric Excellon drill file (PTH + NPTH merged), and the job file. Plotted by `kicad_export_gerbers` / `kicad_export_drill`; zones were filled on disk (DRC: 0 unconnected). |
| `jlcpcb/gerbers/` | Everything eda-agent plotted, including non-fab layers that are not in the zip |
| `jlcpcb/assembly/dual_adc_usb_BOM_JLCPCB.csv` | 56 lines grouped by value + footprint (Comment, Designator, Footprint, LCSC Part # (blank), Quantity), 170 parts |
| `jlcpcb/assembly/dual_adc_usb_CPL_JLCPCB.csv` | 170 placements (Designator, Mid X, Mid Y, Layer, Rotation) in mm, all Top; mounting holes excluded |
| `dual_adc_usb_pcb.png` | Top view, 400 dpi, on #303030. Shows F.Cu, B.Cu, F/B Fab outlines, F/B silk and Edge.Cuts, not clipped to the outline, so the BNC overhang shows. |
| `reports/` | `drc.json`, `erc.json`, `eda_agent_full_review.json`, `dual_adc_usb.net`, raw eda-agent `dual_adc_usb.csv` (BOM) and `dual_adc_usb.pos`, `pos_raw.csv` (mm), `pcb_geometry.txt`, `scripts/` |

## Sources
- eda-agent tool outputs from this session, which ran KiCad 10.0.4 kicad-cli for ERC, DRC, netlist and exports
- KiCad stock symbol libraries in `/usr/share/kicad/symbols` (pin-map comparison)
- TI LM27762 datasheet SNVSAF7C: Eq. 1, "R2 must be no less than 50 kΩ" (§7.2.2.1), R4 likewise, VFB± in the Electrical Characteristics, PGOOD-to-GND (§6.3/§7.2)
- Diodes Inc BAV199DW datasheet ds30417, p.1 internal schematic (top view)
- **From memory, not verified this session:**
  - FT2232H sync-FIFO rate and channel-B restriction
  - LTC2290 abs-max and strap meanings
  - ADA4817 and THS4521 pinouts and limits (pin maps match the KiCad library)
  - TPS62160 Vfb
  - JLC silkscreen minimum and stackup

  Treat items 2–4, 14 and 15 accordingly.
