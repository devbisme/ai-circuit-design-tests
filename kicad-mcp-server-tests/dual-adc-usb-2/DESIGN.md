# Dual-channel 12-bit 10 MS/s USB ADC — design record

Requirements (`dual-adc-prompt.txt`): two inputs, ±10 V, 10 MS/s, 12 bits, ≥0.1 s of samples at
full rate, oscilloscope-lead connectors, USB 2.0 for power and data (USB-C if power is short).

Everything here was derived from scratch in this session. Part parameters come from my
memory of the datasheets, plus the KiCad 10 library descriptions. **Items marked VERIFY were not
checked against a datasheet in this session.**

## Block diagram

```
BNC A ─ 1MΩ ÷10 attenuator ─ clamp ─ OPA810 buffer ─ THS4521 FDA ─┐
                                                                   ├─ LTC2290 ═24b═ iCE40HX4K ═16b═ SDRAM 32 MB
BNC B ─ 1MΩ ÷10 attenuator ─ clamp ─ OPA810 buffer ─ THS4521 FDA ─┘      ▲            ║
                          10 MHz XO (+3.0 V) ─────────────────────────┴────┘            ║ 8b sync FIFO
USB-C (USB 2.0) ─ ESD/fuse ─ regulators                               FT2232H ch A ════╝
                         └────────── D+/D− ───────────────────────── FT2232H ch B ── SPI flash (config)
```

## Key numbers

| Item | Value |
|---|---|
| Capture memory needed | 0.1 s × 2 ch × 10 MS/s × 2 B = **4 MB** |
| Capture memory fitted | 32 MB (0.8 s at full rate) |
| Write bandwidth into SDRAM | 40 MB/s (16-bit SDRAM at ≥66 MHz gives ≥133 MB/s peak) |
| Host link | FT2232H 245 sync FIFO, ~35–40 MB/s practical (VERIFY with real host) |
| Input range / impedance | ±10.06 V full scale, 1.006 MΩ ∥ ~19 pF |
| ADC span | 2 Vpp differential (SENSE = VDD) |
| 5 V budget (estimate) | ~300 mA (below) |

### Power budget (estimates, VERIFY on hardware)

| Load | Rail | Current | From 5 V |
|---|---|---|---|
| FT2232H | 3.3 V | ~70 mA | |
| SDRAM (active) | 3.3 V | ~100 mA | |
| iCE40 I/O, flash, LEDs, ADC OVDD | 3.3 V | ~60 mA | |
| iCE40 core (via AP2112 from 3.3 V) | 1.2 V | ~50 mA | |
| **3.3 V buck total** | | ~280 mA → 0.92 W | ~205 mA (90 % eff.) |
| LTC2290 core + oscillator | 3.0 V (LDO) | ~45 mA | 45 mA |
| Op amps, FDAs | +3.3 V A (LDO) | ~12 mA | 12 mA |
| Op amps | −3.3 V A (LM27761) | ~10 mA | ~12 mA |
| **Total** | | | **≈ 275–300 mA** |

USB 2.0 supplies 500 mA after enumeration (100 mA before), so **USB 2.0 power is sufficient**.
FT2232H's EEPROM should declare 400 mA bus power. Risk: before enumeration the board draws more
than 100 mA. Most hosts tolerate that; a strict host would need the FPGA/SDRAM held in reset
until enumeration (PWREN#-gated load switch, not fitted).

## Decisions (options → recommendation)

1. **Input connector**
   - BNC (standard scope probes plug in directly) — *chosen*
   - SMA (needs an adapter for scope leads)
   - Banana jacks / test hooks (unshielded)

2. **Input network**
   - 1 MΩ compensated ÷10 divider + FET buffer (scope-style; 10× probes compensate) — *chosen*
   - 50 Ω termination (kills probe use)
   - Differential/instrumentation front end (more parts; not asked for)

   2 × 453 kΩ + 100 kΩ (0.1 %) top/bottom; 4.7 pF top, 30 pF + 4.5–20 pF trimmer bottom
   (target ≈42.6 pF incl. parasitics). 15 pF shunt makes total input C ≈19 pF so standard
   10× probes (10–25 pF range) can compensate. BAV99 clamps the divider node to ±3.3 V
   through 1 kΩ into the op amp.

3. **Buffer amplifier**
   - OPA810 (FET input, 140 MHz, rail-to-rail in/out, pA bias) — *chosen*
   - ADA4817 (1 GHz FET, 19 mA, not rail-to-rail input)
   - ADA4807 (bipolar, 0.6 µA bias → ~55 mV error through 91 kΩ)
   - OPA356 (CMOS, input range ends 1.5 V below V+)

4. **ADC driver**
   - THS4521 FDA, gain 1, VOCM from ADC VCM — *chosen* (1.1 mA, negative-rail input)
   - ADA4938 (37 mA)
   - Drive ADC single-ended (worse distortion)

5. **ADC**
   - LTC2290 dual 12-bit 10 MS/s, simultaneous, parallel CMOS out — *chosen*
     (in the KiCad library; LTC2291/2292 are drop-in faster grades)
   - AD9238 dual 12-bit 20/40/65 MS/s (TQFP, not in library)
   - 2 × AD9226 single 12-bit (more parts, two references)
   - MCU with integrated ADC (LPC4370: 12-bit 80 MS/s but multiplexed, not simultaneous)

6. **Sample clock**
   - Dedicated 10 MHz XO on the clean analog rail, star-fed to ADC and FPGA — *chosen*
     (ps-class jitter; FPGA PLL jitter would cost SNR at 5 MHz input)
   - FPGA PLL output (simpler, too much jitter)

7. **Capture buffer and controller**
   - iCE40HX4K + 32 MB SDR SDRAM — *chosen* (open toolchain, TQFP, enough I/O: 26 ADC + 39 SDRAM
     + 15 FIFO + clocks; 107 I/O available)
   - FPGA + QSPI PSRAM (APS6404, 8 MB/chip, 6 pins; tight timing margin at 20 MB/s/channel)
   - FPGA BRAM only (iCE40 has 10 kB — far short of 4 MB)
   - MCU with HS USB + SDRAM (i.MX RT1062 CSI capture; workable but parallel-capture limits uncertain)
   - Stream without buffering (40 MB/s sustained over USB 2.0 is marginal; 0.1 s guarantee lost)

8. **USB 2.0 interface**
   - FT2232H: ch A 245 synchronous FIFO for data, ch B MPSSE for flash programming — *chosen*
   - FT232H (one channel: fast FIFO *or* flash programming, not both)
   - Cypress FX2LP (GPIF, firmware needed, ageing part)
   - FT601 / FX3 (USB 3; overkill)

   VERIFY: that ch B MPSSE works while ch A is EEPROM-configured for 245 FIFO (sync mode is
   entered at run time with `SetBitMode(0x40)`; ch B is unusable only while sync mode is active).
   Fallback without board change: program the flash with the EEPROM temporarily set to MPSSE.

9. **USB connector**
   - USB-C receptacle wired as USB 2.0 (5.1 kΩ Rd on CC1/CC2) — *chosen* (robust, reversible;
     the board stays within the USB 2.0 500 mA budget, so no USB-C power negotiation is needed)
   - USB-B (bulky), Micro-B (fragile)

10. **Supplies**
    - 3.3 V digital: TPS62162 buck (linear would drop 0.5 W in a SOT-23) — *chosen*
    - 1.2 V core: AP2112K-1.2 from 3.3 V
    - +3.3 V A and +3.0 V A: LP5907 low-noise LDOs from 5 V
    - −3.3 V A: LM27761 inverting charge pump + negative LDO (one chip) — *chosen*;
      alternatives TPS60403 + LT1964 (two chips), LM27762 (±, more than needed)
    - VBUS capacitance kept to ≈ 7.7 µF (USB limit 10 µF).

11. **PCB**
    - 4 layers: F.Cu signal, In1.Cu solid GND, In2.Cu signal/power, B.Cu signal — *chosen*
    - 2 layers (TQFP-144 + SDRAM fanout and analog ground quality would suffer)
    - Analog on the left (BNCs on the left edge), digital centre, USB on the right edge.

## Open items / VERIFY list

- LM27761 feedback: assumed VOUT = −1.22 V × (1 + R4/R5) → −3.28 V.
- LTC2290 REFH/REFL network (0.1 µF + 2.2 µF across, 1 µF each to GND) and MODE = 2/3 VDD
  (two's complement, duty-cycle stabiliser on).
- iCE40 GNDPLL pins are tied to GND with the RC filter at VCCPLL; check Lattice's hardware
  checklist (some packages want GNDPLL isolated).
- iCE40 VPP_2V5 tied to 3.3 V (HX allows 2.3–3.46 V).
- FT2232H crystal load caps (27 pF assumed) vs. the chosen crystal's CL.
- THS4521 pin 4 = VOUT+, pin 5 = VOUT− (the library symbol leaves them unnamed).
- Anti-aliasing is only 2 poles (FDA feedback pole ≈7.2 MHz, output RC ≈34 MHz); content
  above 5 MHz will alias. A sharper filter would cost passband flatness.
- USB D+/D− are routed as ordinary tracks (no 90 Ω differential-pair control by the autorouter).
- Gateware (SDRAM controller, capture FSM, FIFO bridge) and host software are not part of this.

## Results

- **Schematic**: 6 sheets (root + power, afe, adc, fpga, usb), 186 parts. KiCad ERC: 0 errors;
  197 `lib_symbol_issues` warnings come from the stale global `sym-lib-table` (environment).
  The kicad-cli netlist matches `design.py` net-for-net (191/191 nets).
- **PCB**: 150 × 90 mm, 4 layers (F.Cu / In1 GND plane / In2 signal + GND pour / B.Cu),
  0.15 mm track/clearance, 0.45/0.2 mm vias. FPGA, SDRAM and FT2232H decoupling is on the bottom
  side under the ICs. 3119 track segments, 534 vias, **0 unconnected**; schematic parity clean.
- **DRC**: 4 errors, all pad-to-NPTH hole clearance (0.194 mm) inside KiCad's stock GCT USB4105
  footprint; check against the fab's limit. Remaining warnings: silkscreen overlap/over-copper
  (cosmetic) and 4 mounting-hole BOM-flag mismatches (the MCP tool always writes `in_bom yes`).
- **Gerbers**: `gerbers/` (exported with the MCP `export_gerber` tool).

### Layout caveats

- USB D+/D− are plain 0.15 mm tracks, not a controlled 90 Ω pair.
- ~5 connections were finished by a simple grid router (`finish_routes.py`); they have
  staircase jogs and 0.15 mm width even on power nets (SW_3V3, +3V0A MUX strap).
  The buck switch node (U2 → L1) should be reworked as a short, wide trace.
- U301 pin 22 (SHDNB, GND) is strapped to pin 23 (GND) instead of having its own via, to make
  room for the MUX pin's escape.
- Analog and digital share one GND plane; the AFEs sit on the far left away from the FPGA,
  but there is no split or star point. In2 GND pour is fragmented by routing.
- Silkscreen was not cleaned up.

## How it was built (and what kicad-mcp-server could not do)

kicad-mcp-server's editing tools were used for: project creation, placing every symbol
(`add_component_from_library`), connecting pins with global labels (`add_global_label`),
the board outline (`setup_pcb_layout`), ERC/DRC, SVG/3D renders and Gerbers. They were called
in bulk from `build_schematic.py` (same functions, imported from the server package) rather
than 1,000+ individual MCP calls.

Gaps found and worked around:

1. Derived library symbols (`extends`) are copied without their parent → pinless symbol.
   Workaround: place the root symbol (identical pins) and keep the real part number as value.
2. Pin lookup for labels stops at the first unit of a multi-unit symbol (iCE40 has 5 units).
3. Label direction is guessed from pin position relative to the symbol origin, which turns
   labels sideways on tall ICs; the library pin orientation is the right source.
4. No tools for sheets, no-connect flags, paper size, text notes, or field placement
   (the Value field lands on the symbol centre).
5. No netlist import, footprint placement, routing or zone tools for the PCB; `pcbnew` and
   Freerouting were used directly (`build_pcb.py`, `route_prep.py`, `finish_pcb.py`,
   `finish_routes.py`, `polish_pcb.py`).
6. Not an MCP issue: the stock USB-C footprint numbers its shell pads `SH` while the
   symbol's pin is `S1`, so the shield silently had no net. Fixed in `build_pcb.py`.

Freerouting notes: GND was fanned out to In1 with locked vias and removed from the DSN;
In1 marked as a plane layer. 0.6 mm vias / 0.2 mm tracks stalled at ~45 unrouted;
0.45 mm vias / 0.15 mm tracks reached 2 real unrouted in 20 passes. A +3V3 plane on In2
(leaving only two signal layers) was worse (>100 unrouted).

### Rebuild

```
~/bin/kicad10-root/bin/python3.11 build_schematic.py <empty_project_template>.kicad_sch
~/bin/kicad10-root/bin/kicad-cli sch export netlist --format kicadsexpr -o dual_adc_usb.net dual_adc_usb.kicad_sch
~/bin/kicad10-root/bin/python3.11 build_pcb.py <outline_from_setup_pcb_layout>.kicad_pcb
~/bin/kicad10-root/bin/python3.11 route_prep.py WORK
freerouting -de WORK/route.dsn -do WORK/route.ses -mp 20 -mt 1
~/bin/kicad10-root/bin/python3.11 finish_pcb.py WORK
kicad-cli pcb drc ... ; finish_routes.py <pcb> <drc.rpt> <out>; polish_pcb.py <out>
```
The last steps (rip-up at U301 pins 22/53/54, shield routing) were done interactively and are
not scripted end-to-end.

## Files

- `design.py` — the netlist (parts, pins, nets). Single source of truth.
- `build_schematic.py` — writes the schematic sheets with kicad-mcp-server's editing functions.
- `build_pcb.py`, `route_prep.py`, `finish_pcb.py`, `finish_routes.py`, `polish_pcb.py` —
  board population, placement, GND fanout, Freerouting handoff, zones, clean-up (pcbnew API).
- `design_notes.txt` — summary placed as a text note on the root sheet.
- `dual_adc_usb.net` — netlist exported from the schematic (input to `build_pcb.py`).
- `dual_adc_usb_render_top.png` — 3D render (MCP `render_pcb`); `gerbers/` — fab outputs.
