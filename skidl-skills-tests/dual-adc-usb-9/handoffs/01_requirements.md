---
phase: 01_requirements
agent: driver
circuit: dual_adc_usb
written: 2026-09-30T22:05:00Z
status: complete
revision: 1
next_phase: 02_architecture
---

# Phase 1 handoff — Requirements

## Decisions
- [HARD] Two channels, each accepting -10 V..+10 V.
- [HARD] 10 MSPS per channel, 12-bit resolution, both channels simultaneously.
- [HARD] Capture >= 0.1 s at full rate on both channels => >= 2 M samples total (>= 24 Mbit buffer; 32 Mbit at 16 bit/sample).
- [HARD] Inputs via connectors that mate with standard oscilloscope leads -> BNC female.
- [HARD] Single USB 2.0 port supplies all power and carries sample data to host.
- [HARD] If the power budget exceeds USB 2.0 (5 V / 500 mA), use a USB-C receptacle instead (sink, Rd on CC).
- [SOFT] 1 MOhm input impedance with ~15-25 pF so 10x probes compensate.
- [SOFT] DC coupling; >= 5 MHz analog bandwidth; anti-alias filter.
- [SOFT] Input protection to survive +/-50 V.
- [SOFT] JLCPCB assembly; SMD; 4-layer; 0-70 C; prototype qty.
- use_cache = false: user demanded a blank slate; do not consult the cross-project part cache or any sibling design directories.
- User directive: at every design decision, list the options and pick the recommended one; do not pause for user input.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `SPEC.md` | Full requirements, user vs driver-default marked | Always |
| `dual-adc-prompt.txt` | Original user prompt | To check provenance of a requirement |

## Next phase must
1. circuit-architect: derive blocks — 2x analog front end (BNC, protection, attenuation/level shift to ADC range, driver/AAF), dual 12-bit 10 MSPS ADC, buffer memory (>= 32 Mbit), capture/control logic (FPGA or capable MCU), USB 2.0 HS bridge, power (VBUS -> digital + analog rails, possibly bipolar analog), clock, USB connector.
2. Explicitly trade: FPGA+SDRAM+USB bridge (FT232H/FT2232H/FT601-class or CY7C68013A) vs MCU with HS USB + parallel ADC interface + external SDRAM/PSRAM; single dual-channel ADC vs two single ADCs.
3. Do a power budget; if > ~2.25 W (90% of 2.5 W), switch to USB-C per the HARD rule and state so.
4. Document every choice as options list + recommendation (user directive).
5. Prefer parts with JLCPCB stock.

## Carried forward
- Input impedance, coupling, protection level, bandwidth, physical and production items are driver defaults (SOFT) — architect may trade them with a stated reason.
- Host software is out of scope for the hardware pipeline.

## Do not redo
- Channel count, range, rate, resolution, capture depth, scope-lead connectors, USB power+data.

## Receipt
dual_adc_usb; 0 user questions (autonomous run per prompt); 6 HARD, 5 SOFT constraints; driver defaults marked in SPEC.md; use_cache=false.
