# Dual-channel 12-bit 10 MS/s USB ADC — design notes

Built from [`dual-adc-prompt.txt`](dual-adc-prompt.txt) with kicad-mcp-pro 4.1.0 and KiCad 10.0.4.
KiCad project: [`dual_adc_usb/`](dual_adc_usb/).

## Requirements and derived numbers

| Requirement | Derived value |
|---|---|
| 2 channels, ±10 V input | Full scale 20 Vpp per channel |
| 10 MS/s, 12 bit | 2 × 10 MS/s × 12 b = 240 Mb/s raw (30 MB/s, or 40 MB/s as 16-bit words) |
| ≥ 0.1 s at max rate | 2 × 1 M samples = 2 M samples → 4 MB as 16-bit words |
| Scope-lead connectors | BNC, 1 MΩ ‖ ~16 pF input, so standard 10× probes can be compensated |
| USB 2.0 for power and data | 5 V / 500 mA = 2.5 W budget |

## Decisions (options → choice)

1. **Converter**
   - LTC2290 dual 12-bit 10 MS/s, QFN-64. Matches the spec exactly, has a shared VCM output, and is in the KiCad library.
   - Two single-channel 12-bit pipelined ADCs (AD9235, AD9226). These need two references and two clock loads, and neither is in the KiCad library.
   - An MCU's built-in ADC (STM32H7 ADCs reach about 3.6 MS/s at 12 bits). Too slow.
   - **Choice: LTC2290** (Analog_ADC:LTC2290xUP).

2. **Capture logic and buffer**
   - FPGA + SDRAM. Deterministic, with plenty of bandwidth headroom.
   - MCU + PSRAM (e.g. RP2350 PIO + QSPI PSRAM). Cheap, but 40 MB/s of sustained PSRAM writes is marginal, and RP2350 USB is full-speed only.
   - FPGA + QSPI PSRAM. Fewer pins, but more complex HDL (CE# max-low time, page-boundary rules).
   - **Choice: iCE40HX4K-TQ144** (open toolchain, 0.5 mm TQFP, no BGA) **+ AS4C4M16SA 64 Mb SDRAM**.
     8 MB holds 0.2 s at full rate on both channels, 2× the requirement. A 16-bit SDRAM at 100 MHz
     gives 200 MB/s peak against 40 MB/s needed.

3. **USB interface**
   - FT2232HL. High-speed USB 2.0. Channel A is a 245 FIFO (async 8 MB/s, sync 40 MB/s). Channel B in MPSSE mode can program the FPGA's SPI flash (iceprog `-I B`).
   - FT232H. Single channel, so FPGA flash programming needs a separate header.
   - Cypress FX2LP. Needs firmware and is not in the KiCad library.
   - **Choice: FT2232HL.** Capture-then-upload: 4 MB at the async 8 MB/s rate takes about 0.5 s. Sync FIFO mode (40 MB/s) can be enabled with the same wiring (ACBUS5 = CLKOUT, ACBUS6 = OE# go to FPGA pins), but it disables channel B while in use.

4. **USB connector / power source**
   - Power estimate (below) is ≈ 1.7 W, under the 2.5 W USB 2.0 limit → the prompt's USB-C fallback is not needed.
   - Connector options: USB-B (THT, rugged, typical for instruments), Micro-B (fragile), USB-C at USB 2.0 rates (would need CC resistors; not required).
   - **Choice: USB-B receptacle** (Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal), protected by a USBLC6-2SC6 ESD array and a 500 mA polyfuse.

5. **Analog front end** (per channel)
   - Compensated 1.01 MΩ divider (909 k ‖ 18 pF over 101 k ‖ 160 pF) → ÷10, giving ±1 V at the tap; input C ≈ 16 pF.
   - BAV99 clamp at the tap to the ±4.5 V AFE rails, then a 1 k series resistor.
   - OPA810 (FET input, 70 MHz, rail-to-rail) unity-gain buffer.
   - THS4521 fully differential amplifier, single-ended to differential, gain Rf/Rg = 1.0 k/1.1 k = 0.91. VOCM comes from the LTC2290 VCM (1.5 V). ±10 V in → 1.82 Vpp differential, about 9 % headroom below the 2 Vpp ADC span, so the ADC's OF flag shows over-range.
   - Cf = 33 pF across each Rf → 4.8 MHz pole (anti-alias); 49.9 Ω + 33 pF to GND at each ADC input (kickback isolation).
   - Options considered: an instrumentation amp or a PGA. Rejected because no gain switching is required and a fixed 1 MΩ BNC input is the scope convention.

6. **AFE bipolar rails**
   - LM27762: charge pump plus positive and negative low-noise LDOs in one 3×2 mm WSON, from 5 V.
   - TPS60403 inverter with VBUS used directly. The positive rail would be noisy.
   - A dual boost/inverting switcher (TPS65131). More parts, higher ripple.
   - **Choice: LM27762, ±4.5 V.**

7. **Clocking**
   - The ADC sample clock must be low-jitter: a 5 MHz input at 12 bits needs well under 10 ps. An FPGA PLL clock (≈ 100–300 ps jitter) would cap SNR near 40 dB.
   - **Choice:** dedicated 10 MHz CMOS oscillator (ASE, +3.3VA) → 33 Ω → CLKA/CLKB. A 74LVC1G34 buffer copies it to an FPGA GBIN, so FPGA I/O noise is kept off the ADC clock node. A separate 50 MHz oscillator drives an FPGA GBIN as the system clock; the PLL multiplies it to 100 MHz for the SDRAM. The FT2232H has its own 12 MHz crystal.

8. **Regulators**

   | Rail | Device | Loads |
   |---|---|---|
   | +3V3 (digital, 1 A) | TLV75733 | FPGA I/O, SDRAM, FT2232H, flash, LEDs |
   | +1V2 (1 A) | TLV75712, from +3V3 | FPGA core; PLLs through RC filters |
   | +3.3VA (250 mA) | LP5907-3.3, from +5V | LTC2290 VDD, THS4521, 10 MHz oscillator |
   | +4V5A / −4V5A | LM27762 | OPA810 buffers, input clamps |

## Power estimate (typical, from datasheet-typical currents; not measured)

| Rail | Load | mA |
|---|---|---|
| +3V3 | FT2232H ~70, SDRAM active ~100, FPGA I/O ~20, flash ~5, LEDs ~6, osc ~10 | ~210 |
| +1V2 (from +3V3) | iCE40HX4K core at ~100 MHz | ~30 |
| +3.3VA | LTC2290 (~40), 2 × THS4521 (~2.5), osc (~5) | ~50 |
| ±4V5A | 2 × OPA810 (~3.7 each) + clamps | ~10 each → ~30 from +5 V via charge pump |
| **Total from VBUS** | linear regulators pass current through | **≈ 320 mA ≈ 1.6 W** |

About 35 % margin to the 500 mA limit. **Risk:** the board draws more than 100 mA before USB
enumeration. This is common for FTDI-based boards, but strictly non-compliant. PWREN# could gate
the analog section in a later revision.

## FPGA pin plan (all banks at 3.3 V)

| Bank (symbol unit) | Use |
|---|---|
| 3 (left, U1D) | ADC: DA0–DA11, DB0–DB11, OFA, OFB, ADC_CLK_FPGA on GBIN7 (pin 20) |
| 2 (bottom, U1C) | SDRAM address, BA, control |
| 1 (right, U1B) | SDRAM DQ0–15, WE, DQM |
| 0 (top, U1A) | FT2232H channel A FIFO, SYS_CLK on GBIN0 (pin 129), LEDs, 8 spare I/O on header J4 |
| Config | SPI flash W25Q32JV; CRESET/CDONE/SPI shared with FT2232H channel B (iceprog convention) |

## Items to verify before fabrication (uncertain)

- LM27762 feedback equations and resistor values (274 k / 100 k for +4.5 V; 374 k / 100 k for −4.5 V) — check against the datasheet.
- LTC2290 REFH/REFL decoupling arrangement and MODE pin level (1/3 VDD = offset binary, clock duty-cycle stabilizer on).
- Input-divider compensation: the 160 pF / 18 pF ratio assumes ~2 pF of tap parasitics; may need a trimmer.
- iCE40 VPP_2V5 tied to 3.3 V (allowed range per the iCE40 HX datasheet is believed to be 2.3–3.46 V).

## How the design was built

| Step | Tool | Notes |
|---|---|---|
| Project, 7 hierarchical sheets | kicad-mcp-pro `kicad_create_new_project`, `sch_create_sheet` | |
| Schematic capture | kicad-mcp-pro `sch_build_circuit` (one call per sheet) | Nets connect by name: global labels for cross-sheet nets, local labels for sheet-internal nets |
| Schematic post-fixes | [`scripts/fixup_sch.py`](scripts/fixup_sch.py), [`add_no_connects.py`](scripts/add_no_connects.py), [`prune_pwr_flags.py`](scripts/prune_pwr_flags.py) | Work around generator bugs (see the executive summary) |
| Footprint + net transfer | kicad-mcp-pro `pcb_sync_from_schematic` (in-process via [`scripts/mcp_call.py`](scripts/mcp_call.py), `force=True`) | 175 footprints, 790 pads, 100 % net-mapped |
| Placement | [`scripts/place_board.py`](scripts/place_board.py) (pcbnew) | The tool's force-directed placement scored 1/100 |
| GND fanout + In1 plane | [`scripts/gnd_fanout.py`](scripts/gnd_fanout.py) | 158 locked vias |
| Routing | Freerouting 2.4.1 ([`scripts/prep_dsn.py`](scripts/prep_dsn.py)); SES import with [`import_ses.py`](scripts/import_ses.py) | 4 connections left unrouted |
| Last connections | [`scripts/finish_routes.py`](scripts/finish_routes.py) (grid A*) | C107 was rotated 180° to untangle the charge-pump flying-cap nets |
| Net classes | [`scripts/set_netclasses.py`](scripts/set_netclasses.py) | Re-applied after every pcbnew save |
| ERC / DRC / exports | kicad-mcp-pro `run_erc`, `export_gerber`, `export_drill`, `export_bom`, `export_pick_and_place`, `export_sch_pdf`; kicad-cli | |

## Verification status (2026-10-10)

- **ERC:** 0 errors. 2 warnings: flash WP#/HOLD# tied directly to +3V3 (bidirectional pin on a power net). Intentional.
- **DRC** (`kicad-cli pcb drc --schematic-parity`): 0 errors, 0 unconnected, 0 parity issues.
  - 18 warnings remain. 16 are silkscreen at the board edge from the overhanging BNC/USB connectors, plus a few silk-over-pad lines at C201, C301 and U701.
  - The other 2 warnings: J701 `lib_footprint_mismatch`, which persists even after reloading J701 from the KiCad 10 library; and 1 silk overlap.
- **Board:** 115 × 85 mm, 4 layers (F.Cu signal, In1 GND plane, In2 signal/power, B.Cu signal + GND pour). 175 parts, 2686 track segments, 530 vias.
- **Track widths:** default 0.15 mm, power 0.4 mm. Freerouting necked 23 segments to 0.112 mm at fine-pitch pins. That is fine for typical 4-layer fab rules (≥ 0.09 mm), but tighter than 5 mil.
- **Outputs:** in `dual_adc_usb/output/` (gerber/ with drill, bom.csv, pos/, schematic.pdf, render_top.png).
- **Not done:** no SPICE simulation of the AFE, no FPGA HDL, no SI analysis of the SDRAM bus, no thermal check. The BOM has no MPN/LCSC fields.
- **Silkscreen:** passive reference designators were hidden (they remain on F.Fab).
