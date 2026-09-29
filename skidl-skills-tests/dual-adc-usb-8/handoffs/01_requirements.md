---
phase: 01_requirements
agent: main-thread
circuit: dual_adc_usb
written: 2026-09-25T22:50:00Z
status: complete
revision: 1
next_phase: 02_architecture
---

# Phase 1 handoff — Requirements

## Decisions
- [HARD] 2 channels, simultaneous sampling, 10 MSa/s each, 12-bit.
- [HARD] Input range −10 V … +10 V at the connector.
- [HARD] Capture depth ≥ 1 M samples/channel (0.1 s @ 10 MSa/s) → ≥ 3 MB packed / 4 MB as 16-bit.
- [HARD] Inputs via PCB-mount BNC female (mates with standard scope probes/leads).
- [HARD] Host interface USB 2.0; board is bus-powered from it.
- [HARD] Power rule from user: USB 2.0 budget is 5 V/500 mA. If estimated draw exceeds ~2.0 W, use a USB-C receptacle (5 V @ 1.5/3 A via Rd pull-downs). Architect must show the power budget and state which applies.
- [SOFT] 1 MΩ ‖ ~20 pF input impedance so 1×/10× scope probes compensate correctly (driver choice).
- [SOFT] ≥ 5 MHz bandwidth with anti-alias filter; ≥ ±30 V input survival (driver choice).
- [SOFT] Capture-to-buffer then upload over USB HS; continuous streaming not required (driver choice — 40 MB/s is marginal on USB 2.0).
- [SOFT] SMD, JLCPCB PCBA, prototype qty 5–10, 0–50 °C, ≤ 100×80 mm target (driver choices).
- use_cache = false — user demanded a blank slate; do not read or write the cross-project part/datasheet cache.
- User instruction: at every design decision, list all options, then select the recommended one and proceed — never pause for user input.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `SPEC.md` | Full requirements, five areas, HARD/SOFT tags, driver-chosen items marked | Always |

## Next phase must
1. circuit-architect: implied blocks — BNC input + protection, analog front end (attenuate/level-shift ±10 V to ADC range, anti-alias, ADC driver), dual 12-bit ≥10 MSa/s ADC (a single dual-channel ADC preferred), sample capture/buffer (FPGA or MCU + memory ≥ 4 MB), USB 2.0 HS bridge/controller, power (USB 5 V → digital rails + bipolar/clean analog rails), clocking, debug header.
2. Reason explicitly (list options, pick one, give why) about: capture engine (FPGA + SDRAM/HyperRAM vs MCU with parallel camera/DCMI interface + external RAM vs FX2/FX3-style bridge), memory type/size, USB HS PHY/bridge choice (e.g. FT232H/FT601/CY7C68013A/MCU with integrated HS PHY), ADC choice (parallel vs serial LVDS; a JLCPCB-available part), bipolar front-end rail generation.
3. Produce a power budget and apply the USB 2.0 vs USB-C rule.
4. Prefer parts likely stocked at JLCPCB; KiCad-library symbols/footprints where possible.

## Carried forward
- All [SOFT] items above were chosen by the driver without user input; revise freely with justification.
- Trigger features beyond software start: open, architect's call.

## Do not redo
- The [HARD] items and the user's power rule.

## Receipt
Circuit dual_adc_usb. 0 interview questions (user forbade pausing; driver chose defaults). 7 HARD, 6 SOFT constraints. Open: trigger scheme, final connector type for USB (depends on power budget).
