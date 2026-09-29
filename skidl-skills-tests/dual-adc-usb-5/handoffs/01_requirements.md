---
phase: 01_requirements
agent: main-thread (new-circuit interview, non-interactive)
circuit: dual_adc_usb
written: 2026-09-20T15:14:02Z
status: complete
revision: 1
next_phase: 02_architecture
---

# Phase 1 handoff — Requirements

No interactive interview was possible: the user's prompt (`dual-adc-prompt.txt`) explicitly
says *"When decisions about the design are needed, list all the options and then select the
one you recommend. Do not pause the design process and wait for my input."* So every
requirement below is tagged in `SPEC.md` as **[USER]** (from the prompt), **[DERIVED]**
(arithmetic from a USER item) or **[CLAUDE]** (my choice, open to revision by the user
later). The architect must honour USER/DERIVED items and may challenge CLAUDE items with a
stated reason.

## Decisions

1. **[HARD]** 2 analog channels, **simultaneously sampled** (no input mux), 12-bit, **10.0 MSPS
   per channel**, continuous for the whole capture. (USER)
2. **[HARD]** Input full-scale range **±10 V at the BNC with a 1:1 lead** (20 V p-p). (USER)
3. **[HARD]** Capture depth **≥ 0.1 s at full rate** = ≥ 1 Msample/ch = 2 Msample total
   = **3.0 MB packed 12-bit / 4.0 MB as 16-bit words**. (USER/DERIVED)
4. **[HARD]** **Burst-to-onboard-RAM then read out over USB** — do *not* architect a live
   30 MB/s USB stream. 2 ch × 10 MSPS × 12 b = 240 Mbit/s = 30 MB/s, which is 60–75 % of the
   theoretical USB 2.0 HS bulk ceiling and not reliably sustainable; the requirement is a
   finite 0.1 s record, so a buffered digitizer is the correct reading. (SPEC D1)
5. **[HARD]** Onboard capture buffer **≥ 4 MB (32 Mbit)**; ≥ 8 MB preferred for headroom.
6. **[HARD]** Host interface is **USB 2.0 High-Speed bulk** on a **USB-C receptacle** with
   5.1 kΩ CC1/CC2 pulldowns, USB 2.0 pins only — **no PD controller, no SuperSpeed pairs**.
   Rationale: estimated load ≈ 300 mA typ / 450 mA worst case at 5 V leaves no margin inside
   a 500 mA USB-A budget, and the prompt authorises USB-C when power is tight. (SPEC D2)
7. **[HARD]** **Bus-powered only.** No battery, no external supply, no sleep modes.
   Design target ≤ 700 mA @ 5 V; hard ceiling 1.5 A. Keep VBUS bulk ≤ 10 µF for
   enumeration inrush.
8. **[HARD]** **No negative rail and no boost converter.** The front end must attenuate
   **passively first** (1 MΩ compensated 10:1 divider) so every active stage runs from the
   board's single-polarity rails. (SPEC D3)
9. **[HARD]** Analog inputs are **BNC board-edge connectors**, input impedance **1 MΩ ±1 %**
   with a compensated attenuator so standard 1:1 and 10:1 scope probes both work.
10. **[HARD]** ADC sample clock comes from a **dedicated ≤ 5 ps RMS oscillator feeding both
    ADCs**, *not* from an FPGA PLL output. Jitter budget: ≤ 14 ps RMS to keep 11 ENOB at
    4.5 MHz. One shared clock edge is what makes the two channels simultaneous. (SPEC D5)
11. **[HARD]** Every part must be **in stock at JLCPCB (≥ 200 pcs)**, no NRND/EOL;
    Basic/Preferred tier preferred; 4-layer SMD board ≤ 100 × 80 mm.
12. **[HARD]** **Blank slate** — `use_cache: false`. Do not read, reuse, or cross-reference
    artifacts, BOMs, datasheet caches or symbol caches from the sibling `dual-adc-usb-*`
    directories. (USER)
13. **[SOFT]** Analog BW −0.5 dB to 4 MHz, −3 dB ≤ 5 MHz; anti-alias ≥ 25 dB above 7 MHz;
    ≥ 10.5 ENOB at 1 MHz FS; survives ±30 V DC at the BNC; 0…+50 °C; 5 prototypes;
    ≤ $70 parts cost at qty 5; JTAG header + power/capture LEDs.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `SPEC.md` | All five requirement areas as numbered tagged rows (F/P/I/H/Q) plus decisions D1–D5 with the options considered | Always — before architecting |
| `dual-adc-prompt.txt` | The user's verbatim prompt | To check my reading of a USER requirement |

## Next phase must
Addressed to **circuit-architect**:

1. Architect a **buffered dual-channel digitizer**, not a streaming one (Decision 4).
2. Blocks the spec implies — expect roughly: (a) ×2 analog front end (BNC → protection →
   1 MΩ compensated 10:1 divider → anti-alias filter → single-ended-to-differential driver
   with the ADC's common-mode level), (b) ×2 or ×1-dual ADC block, (c) capture
   controller + buffer RAM (FPGA, preferably with in-package SDRAM/PSRAM ≥ 64 Mbit), (d) USB
   2.0 HS bridge (FTDI synchronous-FIFO class device — no firmware development), (e) power
   tree from VBUS (3.3 V / 1.2 V / clean analog LDO), (f) clocking (dedicated ADC XO +
   logic clock), (g) USB-C receptacle + CC pulldowns + VBUS protection, (h) JTAG/config +
   LEDs. Merge or split as engineering dictates; record the final list in
   `## Block manifest`.
3. Trade-offs to reason about **explicitly, with options listed and one recommended**
   (the user asked for this style, and it is how the design is reviewed):
   - two single ADCs vs one dual-channel ADC (pin count, cost, channel matching);
   - parallel-CMOS vs serial-LVDS ADC output vs the FPGA's available I/O count;
   - FPGA with in-package SDRAM/PSRAM vs external 16-bit SDR SDRAM (pin count, layout risk,
     stock);
   - ADC input structure: differential input driven by an FDA vs single-ended input
     (simpler, needs a level-shifted unipolar drive);
   - divider compensation: fixed C vs trimmer;
   - overvoltage clamp: series-R + BAV99 to rails vs TVS vs both.
4. **Ruled out already — do not design these:** live USB streaming of the full sample rate;
   USB 3.0 / FX3; ±12 V analog rails or any boost/inverting converter; 50 Ω input
   termination; an MCU whose internal ADCs must reach 10 MSPS; battery or external supply;
   USB-PD negotiation; onboard calibration DAC; onboard MCU firmware development.
5. Give each ADC a **shared sample clock net** from one oscillator, and show the
   clock-domain crossing in the net plan.
6. Size the power tree against a **500 mA worst case** so a USB-A adapter still works even
   though the connector is USB-C.
7. Keep the block count in mind: >3 blocks puts phase 5 in modular mode, which is expected
   and fine here.

## Carried forward
- Every **[CLAUDE]**-tagged row in `SPEC.md` is my engineering choice, not a user statement:
  analog BW, ENOB, protection level, temperature range, board size, quantity, cost target,
  JTAG/LED provisions, connector detail. If any turns out to constrain the design badly,
  flag it in the architecture handoff rather than silently violating it.
- **Trigger capability** is only "host-commanded start" as a firm requirement; a hardware
  level trigger is a nice-to-have and must not cost a keystone part or extra I/O bank.
- **Gain/offset calibration** is deferred to host software; no hardware provision required.
- FPGA bitstream, USB descriptors, and host-side capture software are **out of scope** for
  this pipeline (hardware only), but the architecture must not make them impossible —
  e.g. leave the FPGA config flash/JTAG accessible.
- Whether the buffer ends up in-package or external is open; Decision 5 (≥ 4 MB) is what
  binds.

## Do not redo
- The buffered-capture architecture (Decision 4) — settled by the USB 2.0 throughput
  arithmetic in SPEC D1.
- The passive-attenuate-first front end and the absence of negative rails (Decision 8).
- USB-C connector with plain 5.1 kΩ CC pulldowns and USB 2.0 signalling only (Decision 6).
- 1 MΩ BNC inputs (Decision 9).
- Dedicated ADC clock oscillator (Decision 10).
- The blank-slate rule (Decision 12).

## Receipt
- Circuit name: **dual_adc_usb**
- Interview: **0 interactive questions** — prompt forbade pausing; requirements derived from
  `dual-adc-prompt.txt` + engineering defaults, each tagged USER/DERIVED/CLAUDE in `SPEC.md`.
- Constraints: **12 HARD**, **1 SOFT group** (13 soft rows in SPEC), 5 design decisions
  (D1–D5) resolved with options listed.
- Open questions carried forward: 5 (all CLAUDE-chosen defaults + out-of-scope firmware).
- `use_cache: false` (blank-slate run).
