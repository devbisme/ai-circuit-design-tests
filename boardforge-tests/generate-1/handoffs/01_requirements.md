---
phase: 01_requirements
agent: driver
circuit: dual_adc_10msps
written: 2026-10-17T02:25:00Z
status: complete
revision: 1
next_phase: 02_architecture
---

# Phase 1 handoff — Requirements

The user asked for an autonomous run ("list options, pick the recommended one, do not
pause"). No interview took place; every item not in `design_prompt.txt` is a driver choice
and is tagged `(driver)` in `SPEC.md`. You may trade driver choices if you write down why.

## Decisions
1. [HARD] 2 analog input channels, each −10 V … +10 V, DC coupled. (user)
2. [HARD] 12-bit resolution, 10 MSPS per channel, both channels sampled simultaneously.
3. [HARD] Capture depth ≥ 0.1 s at full rate, both channels: ≥ 1 M samples/channel, ≥ 4 MB
   as 16-bit words (≥ 3 MB packed).
4. [HARD] Inputs on BNC female connectors (standard scope-probe mating). Input impedance
   1 MΩ ∥ ≤ 30 pF so 10× probes can be compensated. (impedance = driver, but needed for
   probe compatibility)
5. [HARD] Anti-alias attenuation ≥ 72 dB at f ≥ 5 MHz (fs/2), derived as 6.02 × 12 bits.
   [SOFT] passband DC–1 MHz within ±0.5 dB. If ≥ 72 dB at 5 MHz is not reasonably
   achievable, say so and propose the closest option — do not quietly relax it.
6. [HARD] Host link: USB 2.0 High-Speed, power and data on one cable. (user)
7. [HARD] Power only from USB. [SOFT] budget ≤ 500 mA @ 5 V; if more is needed the user
   mandates USB-C with CC-negotiated 1.5 A/3 A.
8. [SOFT] Driver recommends a USB-C receptacle (USB 2.0 data only) in all cases.
9. [HARD] Input protection: ±30 V continuous on either BNC without damage. (driver)
10. [SOFT] ADC analog supply / reference ripple ≤ 1 mV pp; ENOB ≥ 10 bits @ 1 MHz.
11. [SOFT] Software trigger mandatory; level trigger on either channel desirable.
12. [SOFT] 4-layer, SMD, JLCPCB assembly, ≤ 100 × 80 mm, 0–50 °C, qty 5, ≤ $150 parts.
13. use_cache = false: the user demands a blank slate ("do not use results from any other
    designs"). The librarian must run `boardforge datasheets sync --fresh` and not publish.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `SPEC.md` | Full requirements, user vs driver provenance | Always |
| `design_prompt.txt` | User's original prompt, verbatim | To check provenance of a requirement |

## Next phase must
1. circuit-architect: produce block diagram, net plan, IC selection, constraints.json.
2. Reason explicitly about the data path: 40 MB/s full-rate is at the USB 2.0 HS limit, so
   plan capture-to-memory (≥ 4 MB SDRAM/PSRAM/SRAM) then upload. Compare at least:
   FPGA + SDRAM + USB bridge (FT232H/FT2232H sync FIFO, or FX2/FX3), vs. MCU with HS USB
   and parallel ADC capture (e.g. STM32H7 with ULPI PHY / external RAM). State the risks.
3. Choose ADC: dual simultaneous 12-bit ≥ 10 MSPS (parallel or serial LVDS) vs two singles.
4. Front end: 1 MΩ input, attenuation ±10 V → ADC range, protection, buffer, anti-alias
   filter meeting Decision 5, driver for the ADC input. Do the filter order arithmetic.
5. Power tree from USB 5 V, including a negative rail if the front end needs one; produce a
   current budget and decide on 500 mA vs USB-C high-current per Decision 7.
6. Keep block count reasonable; write the `## Block manifest` table.

## Carried forward
- Passband width (1 MHz) and ENOB target are driver choices with no user input; revisit
  only if they force an unreasonable filter.
- Trigger features beyond software trigger are optional.
- Host software is out of scope for the board design; note the firmware/gateware the
  chosen architecture implies.

## Do not redo
- Channel count, range, resolution, sample rate, capture depth, BNC inputs, USB 2.0 power +
  data, USB-C fallback rule (user stated these).

## Receipt
Circuit dual_adc_10msps. 0 questions asked (autonomous run). 9 HARD, 6 SOFT constraints.
Open: passband width, trigger features, host software scope. use_cache=false.
