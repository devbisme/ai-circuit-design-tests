---
phase: 01_requirements
agent: main-thread
circuit: dual_adc_usb
written: 2026-09-21T00:00:00Z
status: complete
revision: 1
next_phase: 02_architecture
---

# Phase 1 handoff — Requirements

Autonomous run. The user supplied `dual-adc-prompt.txt` and instructed: *"When decisions
about the design are needed, list all the options and then select the one you recommend.
Do not pause the design process and wait for my input."* There was no interview. Every
number below is tagged **[U]** (user-stated) or **[C]** (chosen in phase 1). A **[C]**
decision may be overturned by the architect **with a written reason in the handoff**; a
**[U]** decision may not.

Blank-slate run: `use_cache = false`. Do not read, import, or copy anything from sibling
design directories under this tree — the user asked for this explicitly.

## Decisions

1. [U][HARD] Two analog channels, **simultaneously sampled**, not multiplexed.
2. [U][HARD] Input range **±10 V** full scale (20 Vpp) per channel.
3. [U][HARD] **10.000 MSa/s** per channel, **12-bit** resolution.
4. [U][HARD] Capture depth **≥ 0.1 s at full rate = 1 MSa/channel, 2 MSa total**.
5. [C][HARD] **Burst-capture-to-RAM, then drain over USB.** 2 ch x 10 MSa/s x 16 bit is
   **40 MB/s**, which is at or above the practical ceiling of USB 2.0 HS bulk (~35–43 MB/s).
   Continuous full-rate streaming is therefore **not** a design goal and must not be
   promised. Architect: size the buffer, do not try to remove it.
6. [C][HARD] Sample buffer **≥ 4 MB** (2 MSa x 16 bit). Recommended: a single 16-bit
   SDR SDRAM of 32 MB, which gives ~8x depth margin for one part and ~20 pins.
7. [C][HARD] **The ADC sampling clock must come directly from a low-jitter oscillator
   (≤ 5 ps RMS), not from an FPGA PLL output.** 12-bit SNR at a 5 MHz input allows only
   **6.4 ps RMS** of clock jitter; a typical FPGA PLL output at 50–150 ps RMS would cap the
   converter near 8 ENOB. This is the highest-value constraint in this handoff.
8. [C][HARD] Channel-to-channel skew ≤ 100 ns — both ADCs share one sample clock, or use
   one dual ADC with a single clock.
9. [U][HARD] All power from the host USB port. No barrel jack, no battery.
10. [C][HARD] **≤ 450 mA @ 5 V (2.25 W) steady state**, so the board is legal on any
    500 mA USB 2.0 port. Phase-1 estimate is ~1.7–1.9 W at the connector.
11. [C][HARD, conditional] If the architect's real budget exceeds 2.25 W, the user's
    "if insufficient power is available, use a USB-C port" clause fires: add **CC pull-up
    sensing** to claim 1.5 A / 3.0 A, and hold the analog rails off on a default-power
    source. Record which branch was taken.
12. [C][HARD] Inrush limited at plug-in (soft-start or current-limited load switch) so the
    host's budget is never exceeded while the bulk caps charge.
13. [C][HARD] Analog rails come from LDOs or a low-noise charge pump, never straight off a
    switcher node.
14. [U][HARD] Analog inputs on **BNC** connectors — that is what "mates with standard
    oscilloscope leads" means.
15. [C][HARD] Input impedance **1 MΩ ∥ ~20 pF** with a trimmable compensation capacitor, so
    a standard 10x passive probe can be compensated. See open question 1 — this is the one
    [C] decision most worth challenging.
16. [C][HARD] Input protection: survive **±50 V DC** continuous and ESD on the BNC centre
    pin. Series limiting plus clamps; clamp current must not be dumped into a rail that
    cannot sink it.
17. [U][HARD] Host link is **USB 2.0 High Speed**, bulk transfer.
18. [C][HARD] Connector is a **USB-C receptacle**, USB 2.0 signalling only, D+/D− on both
    A6/A7 and B6/B7, 5.1 kΩ CC1/CC2 pull-downs. Chosen even though a USB-B or micro-B would
    satisfy the letter of the spec: same cost, mechanically better, and it is the connector
    that makes decision 11 possible without a redesign.
19. [C][HARD] −3 dB analog bandwidth ≥ 4 MHz; anti-alias filter ≥ 3rd order, ≥ 25 dB at
    10 MHz.
20. [C][HARD] Every part must have live JLCPCB stock ≥ 100 and must not be NRND/obsolete.
21. [C][SOFT] 4-layer PCB ≤ 100 x 80 mm, SMD except BNC/USB, 0–50 °C, no certification,
    5–10 prototypes, BOM ≤ $100/board at qty 10.
22. [C][SOFT] Single ground plane with partitioned analog/digital placement. Do not specify
    a split plane with a stitch.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `SPEC.md` | Full requirement table, five headings, [U]/[C] and HARD/SOFT on every line | Always — before any architecture work |
| `dual-adc-prompt.txt` | The user's original words, 12 lines | When a [C] decision feels wrong and you want the source |

No datasheets, sketches, or reference designs were supplied by the user.

## Next phase must

Addressed to **circuit-architect**:

1. Read `SPEC.md` in full, then produce `architecture/` per your own agent spec:
   block diagram, net plan, IC selection with rationale, skeleton BOM, design risks.
2. **Resolve the three open questions below explicitly**, each as a list of options with a
   recommendation, because the user asked for exactly that format and will read it.
3. Build a **real power budget** — a line per rail with current at each load, conversion
   efficiency, and the total at the USB connector. This decides whether decision 11 fires.
   It is the design's biggest single risk; do not hand it forward as an estimate.
4. Choose the converter topology. At least these belong on the options list:
   (a) one dual 12-bit ADC with a parallel or serial LVDS output;
   (b) two single 12-bit ADCs sharing one clock;
   (c) a higher-rate ADC time-multiplexed across channels — **rule this out** against
   requirement F1 (simultaneous sampling) and say so.
5. Choose the capture engine and host link. Options to weigh: FPGA + external buffer RAM +
   a USB 2.0 HS bridge IC in slave-FIFO mode (lowest risk, the sigrok/fx2 pattern);
   FPGA + ULPI PHY + soft USB device core (fewer parts, much higher firmware risk);
   MCU-only (**check it honestly against 2 ch x 10 MSa/s parallel capture and 4 MB of
   buffer — phase 1 believes no ordinary MCU makes it, but say why, don't just assert it**).
6. Honour decision 7 in the clock tree: draw the ADC sample clock from its own oscillator.
   The FPGA may take the same oscillator as a reference and PLL it up for the memory domain.
7. Emit a `## Block manifest` table. Expect roughly: `analog_frontend` (parameterised, one
   file, two instances), `adc`, `fpga_core`, `buffer_memory`, `usb_bridge`, `power`,
   `clocking`, `io_misc`. That is > 3 blocks, so phase 5 will run in **modular** mode —
   give every block an exact `function_signature` and `interface_nets` list.
8. Flag anything that will need a custom KiCad symbol or footprint (BNC, USB-C, the FPGA)
   so sourcing can plan for it.

## Carried forward

- **Open question 1 — front-end input impedance.** 1 MΩ ∥ 20 pF (10x-probe compatible,
  needs a low-Cin buffer and compensation trimmers) vs ~100 kΩ resistive divider (simpler,
  cheaper, works with plain BNC leads and 1x probes, cannot compensate a 10x probe).
  Phase 1 chose 1 MΩ because "standard oscilloscope leads" most often means 10x passive
  probes. Closes when the architect commits and states why.
- **Open question 2 — power.** Does the real budget stay under 2.25 W? Closes with the
  architect's rail-by-rail budget. If it fails, decision 11 fires and CC sensing is added.
- **Open question 3 — USB path.** Bridge IC vs soft core vs MCU. Phase 1 leans to the
  bridge IC on risk grounds alone. Closes with the architect's choice, subject to phase-3
  JLCPCB stock; if the preferred bridge is unobtainable this comes straight back.
- **AAF order** (F9) is SOFT and may drop to 3rd order if power or part count demands it.
- **Analog trigger** (F11) is a nice-to-have and may be dropped without escalation.
- Exact rail set (P5) is the architect's call, subject to decisions 10, 12 and 13.

## Do not redo

- The five [U] requirements: 2 channels, ±10 V, 10 MSa/s, 12 bits, ≥ 0.1 s depth, USB power
  and USB data, oscilloscope-lead-compatible connectors. These are not open.
- BNC for the analog inputs. Not SMA, not banana, not a header.
- The burst-to-RAM architecture (decision 5). Do not re-propose continuous streaming at
  full rate; the arithmetic is in decision 5 and it does not close.
- The ADC-clock-from-its-own-oscillator rule (decision 7).
- `use_cache = false`. Do not pull anything from sibling design directories.

## Receipt

- Circuit: `dual_adc_usb`. Requirements captured from a written prompt; 0 interview
  questions asked (user forbade pausing).
- Constraints: 22 decisions — 17 HARD, 5 SOFT; 8 user-stated, 14 chosen in phase 1.
- Artifacts: `SPEC.md` (87 lines).
- Open questions: 3 substantive (front-end impedance, power budget, USB path), all routed
  to phase 2 with options listed.
- Status: complete. Next: `circuit-architect` → `handoffs/02_architecture.md`.
