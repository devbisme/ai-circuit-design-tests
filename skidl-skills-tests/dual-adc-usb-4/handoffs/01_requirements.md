---
phase: 01_requirements
agent: driver
circuit: dual_adc_usb
written: 2026-09-10T17:25:51Z
status: complete
revision: 1
next_phase: 02_architecture
---

# Phase 1 handoff — Requirements

## Decisions
Source is a one-paragraph user prompt (`dual-adc-prompt.txt`). The user told the pipeline to
list options and pick the recommended one without pausing — so most numbers below were chosen
by the driver ([DRIVER] in `SPEC.md`), not the user. Only the [USER] items are firm.

- [HARD][USER] 2 analog channels, each −10 V…+10 V full scale at the connector.
- [HARD][USER] 10 MSPS per channel, 12-bit resolution.
- [HARD][USER] Inputs on connectors that mate with standard scope leads → BNC female, PCB mount.
- [HARD][USER] USB 2.0 port supplies all power and carries the samples.
- [HARD] USB 2.0 **High-Speed** device required — 2×10 MSPS×12 b = 240 Mb/s (30 MB/s packed); Full-Speed cannot carry it.
- [HARD] Both channels sampled simultaneously from one sample clock.
- [HARD] Input impedance 1 MΩ ∥ 15–25 pF (scope-standard; lets 10× probes compensate).
- [HARD] Total VBUS draw ≤ 450 mA.
- [HARD] ESD protection on USB D+/D−/VBUS; programming/debug headers for every programmable device.
- [HARD] Block/triggered capture with ≥ 16 k samples/channel buffered on board is the guaranteed transfer mode.
- [SOFT] Gap-free continuous streaming of both channels is a goal — ~30–40 MB/s is at the practical USB-2 HS bulk ceiling.
- [SOFT] DC coupling; −3 dB ≥ 3 MHz with anti-alias roll-off near Nyquist (target 4–5 MHz, ≥ 2nd order).
- [SOFT] Survive ±50 V continuous at the BNC; clamp before any active device.
- [SOFT] Front-end noise ≤ 1 LSB rms (≈ 4.9 mV input-referred); ENOB ≥ 10 at 1 MHz; clock jitter ≲ 20 ps rms.
- [SOFT] Gain error ≤ 2 %, offset ≤ 1 % FS uncalibrated (software calibration assumed).
- [SOFT] USB Type-C receptacle, USB 2.0 wiring only, 5.1 kΩ CC pull-downs; no galvanic isolation.
- [SOFT] JLCPCB assembly, in-stock parts, Basic preferred; BOM ≤ US$120 at qty 10; SMD; ≤100×80 mm, 4-layer; 0–50 °C.
- `use_cache = false` — user demanded a blank slate. Do **not** read or reuse any file from sibling design directories (`../dual-adc-usb-*` or anywhere else in the tree); only this project directory.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `SPEC.md` | All requirements in 5 areas, each tagged USER/DRIVER and HARD/SOFT, plus the decisions log (options → selection) | Always — before any architecture work |
| `dual-adc-prompt.txt` | The user's original prompt | To check what the user actually said vs. driver choices |

## Next phase must
1. **circuit-architect**: produce the architecture for a bus-powered, 2-channel, 12-bit 10 MSPS USB 2.0 HS digitizer. Implied blocks: USB-C connector + ESD; power tree (VBUS → digital/analog rails, any bipolar rail); 2× analog front end (BNC, 1 MΩ attenuator/protection, driver/level-shift, anti-alias filter); dual ADC + reference; sample clock; capture logic + sample buffer (FPGA/CPLD or MCU); USB HS bridge/PHY; programming/config (flash, JTAG/SWD); LEDs.
2. Reason explicitly, with numbers, about these trade-offs and record the choice in `architecture/`:
   - ADC: one dual-channel ADC vs two single-channel ADCs; parallel CMOS vs serial LVDS output; sampling rate headroom (a 20+ MSPS part run at 10 MSPS is acceptable).
   - Front end: ±10 V → ADC input span. Single-supply level-shift vs bipolar op-amp supply; attenuator ratio and its 1 MΩ/compensation network; op-amp GBW/slew for 5 MHz, 20 Vpp-at-input (after attenuation); clamp placement.
   - Capture + USB: FPGA + HS bridge (e.g. FT232H/FT2232H sync-FIFO, CY7C68013A slave-FIFO) vs HS-capable MCU with ULPI PHY or on-chip HS PHY vs other. State the achievable sustained throughput and whether streaming (SOFT) is feasible; the ≥16 k samples/ch buffer (HARD) must fit in the chosen device's RAM or an external memory.
   - Clock: oscillator feeding ADC directly vs FPGA-derived; jitter budget.
   - Power: rail list with a current budget summed against 450 mA.
3. Keep every chosen IC realistically sourceable at JLCPCB (the part-sourcer will verify stock); prefer parts with KiCad library symbols.
4. Produce a `## Block manifest` table in `handoffs/02_architecture.md` (the driver uses its row count to pick the coding mode).

## Carried forward
- All [DRIVER] numbers (F5–F14, P2–P6, I3–I8, M*, Q*) are the driver's recommendations, not user-confirmed. Architect may trade [SOFT] items with a stated reason; [HARD] items need escalation.
- Continuous streaming (SOFT) — feasibility depends on the bridge chosen; document the result, do not silently drop it.
- Pre-enumeration 100 mA limit is not enforced in hardware (accepted risk).
- Firmware, gateware, host software and PCB layout are out of scope; the schematic must still expose what they need (config flash, JTAG, clock, test points).

## Do not redo
- BNC connectors, 1 MΩ input impedance, USB 2.0 HS, USB bus power only, 2 ch/10 MSPS/12 b — settled.
- Blank-slate constraint: no reuse of other designs' outputs or intermediate files.

## Receipt
Circuit `dual_adc_usb`. 0 user questions asked (user pre-authorized driver decisions); 10 decisions logged in SPEC.md.
Constraints: 10 HARD, 9 SOFT (in `## Decisions`). Open: streaming feasibility, front-end supply topology, ADC/bridge selection — all for architect.
