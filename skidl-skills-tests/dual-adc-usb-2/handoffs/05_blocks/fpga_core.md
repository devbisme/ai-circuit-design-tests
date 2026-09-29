---
phase: 05_blocks/fpga_core
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-09
---

## Receipt

- Wrote `circuits/dual_adc_usb/fpga_core.py`: U9 (iCE40HX4K-TQ144) + U18 (W25Q32JVSSIQ
  config flash) + J4 (2x5 programming header) + J5 (EXT_TRIG header) + D4-D7 (status
  LEDs / clamp) + R20-R26 + C47-C64, matching the work order's exact function signature
  (unchanged from the work order).
- Parsed the installed `FPGA_Lattice:ICE40HX4K-TQ144` KiCad symbol directly (144 pins)
  to build a complete pin table, then verified the pin budget: **101 GPIO-capable pins
  available** (144 minus 28 power/gnd, 7 NC, 8 dedicated config/SPI pins) against **85
  needed** (83 general GPIO + 2 GBIN clock inputs) — fits with **16 pins spare**. No
  escalation needed.
- Compiles clean (`py_compile`), footprints validate clean (23/23), and instantiates
  standalone (33 parts, 98 nets, ref designators exactly matching the work order's
  allocation with zero collisions). `ERC()` on the standalone instantiation returns
  **0 errors** (100 warnings, all benign single-block-context artifacts: buses with
  only this block's end connected, and the 16 genuinely-spare GPIO pins/7 NC pins
  reading as "unconnected" — both expected until the assembler wires the sibling
  blocks).

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/fpga_core.py | `fpga_core()` SubCircuit: U9, U18, J4, J5, D4-D7, R20-R26, C47-C64 | skidl-assembler |

## Key facts for the next phase

- **Final signature (unchanged from work order):**
  `fpga_core(v3v3_d, v1v2, gnd, adca_data, adca_otr, adca_pdwn, adcb_data, adcb_otr, adcb_pdwn, clk_10m, clk60, sram_addr, sram_data, sram_ce_n, sram_oe_n, sram_we_n, sram_ub_n, sram_lb_n, fifo_data, rxf_n, txe_n, rd_n, wr_n, oe_n, ext_trig, led_usb_n, led_cap_n)`
- Bus params and required sizes: `adca_data`/`adcb_data` = 12-bit, `sram_addr` = 18-bit,
  `sram_data` = 16-bit, `fifo_data` = 8-bit. Caller must pass `Bus(...)` objects of
  exactly these widths.
- Net directions for the assembler's keyword call:
  - **Inputs to this block** (driven elsewhere): `v3v3_d`, `v1v2`, `gnd`,
    `adca_data`/`adcb_data` (from adc_channel's series dampers), `adca_otr`/`adcb_otr`,
    `clk_10m` (from clock_gen), `clk60` (from usb_bridge/FT232H CLKOUT), `rxf_n`/`txe_n`
    (from usb_bridge), `ext_trig` (from J5, this block's own header — external world).
  - **Outputs from this block** (driven here): `adca_pdwn`/`adcb_pdwn`,
    `sram_addr`/`sram_data`(write path)/`sram_ce_n`/`sram_oe_n`/`sram_we_n`/`sram_ub_n`/
    `sram_lb_n`, `rd_n`/`wr_n`/`oe_n` (to usb_bridge), `led_usb_n`/`led_cap_n`.
  - `sram_data` and `fifo_data` are genuinely bidirectional.
  - None of `v3v3_d`/`v1v2`/`gnd` need `.drive = POWER` here — all three are driven by
    power_digital at the top level; this block only consumes them.
- **U9's `VCCIO_0..3`, `VCC`, `GND`, `GNDPLL0/1`, `NC` pin names each alias multiple
  physical pins** — a single `u9['VCCIO_0'] += v3v3_d`-style connection wires every
  physical pin of that name at once (same pattern usb_bridge.py and sram_buffer.py
  already used and verified for their own parts).
- **Internal nets this block owns** (created via `Net(...)`, not parameters — assembler
  does not wire these): `SPI_SCK`, `SPI_SI`, `SPI_SO`, `SPI_SS_N`, `CDONE`, `CRESET_N`,
  plus `ICE40_VCCPLL_FILT` and `EXT_TRIG_CLAMPED` (both purely local, not named in the
  work order but needed for the PLL filter and the EXT_TRIG clamp node respectively).
- **GPIO pin-to-net allocation table** (U9 pin numbers; generic bank names in
  parentheses for traceability — exact assignment is arbitrary/refined later by the
  gateware `.pcf`, only bank/electrical fitness matters at schematic level):
  - `adca_data[0..11]` -> pins 1,2,3,4,7,8,9,10,11,12,15,16
  - `adca_otr` -> 17; `adca_pdwn` -> 18
  - `adcb_data[0..11]` -> pins 19,20,21,22,23,24,25,26,28,29,31,32
  - `adcb_otr` -> 33; `adcb_pdwn` -> 34
  - `sram_addr[0..17]` -> pins 37,38,39,41,42,43,44,45,47,48,49,55,56,60,61,62,73,74
  - `sram_data[0..15]` -> pins 75,76,78,79,80,81,82,83,84,85,87,88,90,91,93,94
  - `sram_ce_n`->95, `sram_oe_n`->96, `sram_we_n`->97, `sram_ub_n`->98, `sram_lb_n`->99
  - `fifo_data[0..7]` -> pins 101,102,104,105,106,107,110,112
  - `rxf_n`->113, `txe_n`->114, `rd_n`->115, `wr_n`->116, `oe_n`->117
  - `ext_trig` (post-clamp node) -> 118; `led_usb_n`->119; `led_cap_n`->120
  - `clk_10m` -> pin 52 (`IOB_82_GBIN4`, PLL0-adjacent); `clk60` -> pin 129
    (`IOT_198_GBIN0`, PLL1-adjacent, per R-08's PLL phase-shift mitigation)
  - Spare GPIO (16 pins, available for a future revision): 121, 122, 124, 125, 128,
    130, 134-139, 141-144.
- **U9 dedicated/fixed pins used**: CBSEL0=63 (tied GND), CBSEL1=64 (tied GND),
  CDONE=65, `~{CRESET}`=66, SDO=67 (SPI_SI net), SDI=68 (SPI_SO net), SCK=70
  (SPI_SCK net), SS=71 (SPI_SS_N net), VCC_SPI=72 (V3V3_D).

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| F1 | VPP_2V5 (pin 108) supply | Escalate for a new dedicated 2.5V rail / tie to V3V3_D / tie to GND | **Tie to V3V3_D** | The datasheets-phase summary flags VPP_2V5 as needing "2.5V even without NVCM use", but no 2.5V general-purpose rail exists anywhere in `net_plan.md`'s 9-block architecture (the only 2.5V-adjacent net, VREF_2V5, is a µA-level analog reference internal to power_analog/afe_channel, not a power rail, and is not passed into this block's signature). This design never uses NVCM programming (single external SPI-flash image, SPI-master boot). Adding a whole new regulated rail for one housekeeping pin is disproportionate; tying to the nearest available rail (V3V3_D, 0.8V off nominal) is the pragmatic, commonly-used fallback on 3.3V-only iCE40 designs. **RECOMMENDED and taken.** Flagged for bring-up verification, not an escalation-worthy blocker. |
| F2 | VPP_FAST (pin 109) supply | Tie GND / tie V3V3_D / leave floating | **Tie GND** | Datasheet summary itself flags this as "common practice for non-NVCM designs... not independently confirmed" — GND is the documented common-practice default and the lower-risk choice (floating a programming-related pin risks undefined behavior; the datasheet explicitly warns an incorrect tie risks "either non-function or accidental NVCM programming" — GND is the standard safe default cited). |
| F3 | W25Q32 `~WP`/`~HOLD` pull-ups (flagged by the datasheets phase as unbudgeted — no spare resistors in R20-R26) | Add 2 unbudgeted resistors (violates "use refs from work order, never invent") / tie both directly to V3V3_D | **Tie directly to V3V3_D** | The datasheet summary itself offers this as the explicit fallback ("tie directly to VCC if no quad-mode future-proofing is wanted"); this design uses standard single-SPI only, so quad-mode future-proofing has no value here, and it respects the fixed R20-R26 ref allocation. |
| F4 | LED_PWR / D3 (work order text lists `LED_PWR` as an internal net "owned" by fpga_core) | Instantiate D3+resistor here (ref collision with power_digital) / omit entirely, since it's hardwired and un-FPGA-connected per net_plan and belongs to a different block's ref allocation | **Omit** | `net_plan.md` Sec.8 describes LED_PWR as fully hardwired (`V3V3_D -> 1k -> D3 -> GND`, no FPGA pin), and `handoffs/02_architecture.md`'s own Parts-by-block table puts D3 + its resistor (R4) in `power_digital`'s ref range (U1, U2, D3, R4, C3-C7), not in fpga_core's (U9, U18, J4, J5, D4-D7, R20-R26, C47-C64 — no D3/R4). The "owned net" line in the manifest appears to be a stale carry-over; instantiating D3 here would collide with power_digital's part. Not built in this block. |
| F5 | CDONE (open-collector) pull-up + D4 LED, with only 1 resistor (R20) budgeted for both functions | Separate pull-up + separate LED resistor (needs 2 unbudgeted resistors) / single R20 doing double duty: `V3V3_D --R20--> CDONE node --> D4(A->K) --> GND` | **Single R20, double duty** | Matches the sourced BOM's own framing verbatim ("needs external pull-up... shared with D4 LED + R20") and the fixed 7-resistor R20-R26 budget. LED lights when CDONE is released HIGH (config done); dims/off while U9 holds it low internally during configuration. |
| F6 | D7 (BAV99, common-anode symbol) EXT_TRIG clamp topology — a common-anode dual diode cannot form a symmetric two-rail clamp (per `datasheets/BAV99_SUMMARY.md`'s own flag) | High-side-only clamp (anode=signal, one cathode=V3V3_D, other cathode NC) / low-side-only clamp (anode=GND, cathode=signal) / tie the unused cathode to GND anyway | **High-side-only clamp, second cathode NC** | Protects against a trigger source driven above V3V3_D (the more likely real-world fault for an external BNC/header trigger input). Tying the second cathode to GND was rejected: with a common anode at the signal node, a GND-tied cathode would forward-bias on every normal HIGH pulse (signal > ~0.6V) and clamp EXT_TRIG to ~0.6V, breaking the input entirely — computed and rejected, not just asserted. |
| F7 | VCCPLL0/VCCPLL1 (2 physical pins) filtering, with only 1 resistor (R26) + 1 cap (C63) budgeted | 2 independent RC filters (needs 2 more unbudgeted parts) / one shared filtered node feeding both pins | **One shared node** (`ICE40_VCCPLL_FILT`) | Matches sourced BOM's exact qty (R26 x1, C63 x1) for "VCCPLL filter"; both PLL supply pins get equally clean, equally filtered power from the single RC network. |
| F8 | GBIN pin choice for CLK_10M / CLK60 | Any of the 8 GBIN pins / pins adjacent to a PLL block, since R-08's mitigation needs the iCE40 PLL to phase-shift the FIFO clock domain | **CLK_10M -> pin 52 (GBIN4, PLL0-adjacent); CLK60 -> pin 129 (GBIN0, PLL1-adjacent)** | CLK60 is the one that needs PLL phase-shifting per R-08 (design_risks.md); placing it on a GBIN pin physically adjacent to a PLL block (VCCPLL1/GNDPLL1 at pins 126/127) keeps that gateware-level PLL instantiation straightforward. CLK_10M placed near the other PLL (pins 53/54) on the same principle, though it has no stated PLL requirement itself. |
| F9 | J4 (2x5 programming header) pin mapping — not specified numerically anywhere upstream | Any consistent assignment of the 8 needed signals (V3V3_D, GND, SPI_SCK, SPI_SI, SPI_SO, SPI_SS_N, CRESET_N, CDONE) across 10 physical pins | **Pins 1-8 = the 8 signals in that order; pin 9 = redundant GND; pin 10 = NC** | Arbitrary but documented — matches the sourced BOM's stated content ("SPI + CRESET_B + CDONE + 3V3 + GND") with 2 spare pins handled explicitly rather than left ambiguous. |

## Carried forward

- **Gateware is explicitly out of scope** for this file (see docstring TODO block):
  the ADC-capture FSM, the SRAM address/byte-lane sequencing, the FT245 sync-FIFO
  packer/parser with I/O-cell-registered outputs and PLL phase shift (R-08), the
  in-band 4-byte command-frame parser (`0xA5 CMD ARG_L ARG_H`, `ic_selection.md` F2),
  and the digital polarity correction (`code_out = 4095 - code_raw`) are all future
  work for whoever writes the actual bitstream. Nothing here should be mistaken for a
  functional description of FPGA behavior.
- **VPP_2V5 tied to V3V3_D (F1) and VPP_FAST tied to GND (F2) are both judgement
  calls under real (if low) uncertainty** — flagged for bring-up/datasheet
  cross-check against the full Lattice DS1040 datasheet (never fetched this session
  per the architecture and datasheets handoffs' own "PDF not retrieved" notes), not
  fully resolved facts.
- **Pin-to-net GPIO assignment is arbitrary at the schematic level** (see Decisions
  F8/F9 and Key facts table) — a gateware `.pcf` constraints file will make the real
  binding assignment; nothing here should be treated as fixed for layout/gateware
  purposes beyond "this pin belongs to this bank, is GPIO-capable, and is 3.3V".
- **Assumes upstream blocks drive what this block only consumes**: `adca_data`/
  `adcb_data`/`adca_otr`/`adcb_otr` from adc_channel, `clk_10m` from clock_gen,
  `clk60`/`rxf_n`/`txe_n` from usb_bridge. This block does not add series damping,
  termination, or additional buffering on any of those — it assumes adc_channel's
  100R data-bus dampers and usb_bridge's own I/O characteristics are sufficient.
- **EXT_TRIG (J5) is this block's own external-world input** — no other block drives
  or consumes it; `ext_trig` the function parameter is the raw (pre-header, pre-R25)
  net from the caller's perspective, matching the work order's signature.

## Do not redo

- **Parts/footprints, settled upstream (sourced_bom.md Block 9):** U9 =
  iCE40HX4K-TQ144, `Package_QFP:TQFP-144_20x20mm_P0.5mm`; U18 = W25Q32JVSSIQ,
  `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm`; J4 = `Connector_PinHeader_1.27mm:PinHeader_2x05_P1.27mm_Vertical`;
  J5 = `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical`; D4-D6 =
  `Device:LED` / `LED_SMD:LED_0603_1608Metric`; D7 = `Diode:BAV99` /
  `Package_TO_SOT_SMD:SOT-23`; R20-R22/R25 = 1k, R23/R24 = 10k, R26 = 470R, all
  `Resistor_SMD:R_0402_1005Metric`; C47-C58/C63/C64 = 100nF 0402; C59/C60 = 1uF
  0603; C61/C62 = 10uF 0805.
- **CBSEL0/CBSEL1 -> GND** (single-image SPI-master boot) — datasheets-phase
  decision DS4, implemented verbatim.
- **iCE40HX4K-TQ144 pin table** — parsed directly from the installed KiCad symbol
  this session (144 pins, all named/numbered); do not re-derive from the datasheet
  summary's partial table alone.

## Escalation

none
