---
phase: 01_requirements
agent: main-thread
circuit: dual_adc_usb
written: 2026-09-22T00:00:00Z
status: complete
revision: 1
next_phase: 02_architecture
---

# Phase 1 handoff — Requirements

## Decisions

Constraints the architect designs against. `[HARD]` cannot be traded; `[SOFT]` may be.

1. `[HARD]` Two analog channels, **simultaneously sampled**, 12-bit, **10 MSPS/channel**.
2. `[HARD]` Full-scale input **−10 V … +10 V** (20 Vpp) per channel, DC-coupled.
3. `[HARD]` Capture depth **≥ 0.1 s at full rate on both channels** = 2,000,000 samples
   total ⇒ **≥ 4,000,000 bytes of on-board sample memory** (16-bit word per sample).
4. `[HARD]` **Burst-capture architecture**: acquire to on-board memory at full rate, then
   read out over USB. Continuous 40 MB/s streaming is explicitly *not* a requirement and
   must not be designed for — USB 2.0 HS cannot carry it reliably.
5. `[HARD]` Analog inputs on **BNC female PCB jacks**, one per channel (scope-probe mating).
6. `[HARD]` Input impedance **1 MΩ ∥ ~20 pF** (passive 1×/10× scope probe compatible).
7. `[HARD]` Host interface **USB 2.0 High-Speed**, bulk, sustained read-out ≥ 20 MB/s.
8. `[HARD]` **Bus-powered only** via **USB Type-C receptacle**, USB 2.0 signalling, CC1/CC2
   5.1 kΩ pulldowns, **no PD controller**. Type-C was chosen over Type-B specifically
   because the 2.5 W of a legacy port does not cover the load — this is the prompt's own
   stated fallback and the condition is met.
9. `[HARD]` Total bus draw **≤ 1.5 A @ 5 V**; design target **≤ 1.0 A**. Pre-enumeration
   draw **≤ 150 mA**.
10. `[HARD]` Bipolar analog rails for the front end are generated **on board** from +5 V.
11. `[HARD]` Input overvoltage survival **≥ ±50 V** continuous (clamped).
12. `[SOFT]` Analog BW **−3 dB ≥ 4 MHz**, anti-alias **≥ 40 dB at 10 MHz**.
13. `[SOFT]` **SNR ≥ 60 dB** (≈10 ENOB). 12-bit *resolution* is required; 12 *noise-free*
    bits is not. This is the design's main cost lever — do not over-engineer past it, and
    say so if the chosen ADC forces a much better or much worse number.
14. `[SOFT]` DC gain accuracy ≤ ±1 % FS, offset ≤ ±0.5 % FS, uncalibrated.
15. `[SOFT]` Channel skew ≤ 5 ns.
16. `[SOFT]` **Software (host-commanded) trigger only.** No analog trigger, no external
    trigger connector.
17. `[SOFT]` PCB ≤ 100 × 80 mm, **4-layer**, SMD (BNC jacks and headers may be TH),
    0 °C … +70 °C.
18. `[SOFT]` **JLCPCB** assembly, Basic/Preferred tier preferred, qty 5, ≤ $90/board;
    flag any part > $25.
19. `[HARD]` **`use_cache = false`** — the user demanded a blank slate: "Do not use the
    results or any intermediate files from any other designs in this directory tree."
    No cross-project datasheet/symbol cache reads or writes.
20. `[HARD]` **Do not stop to ask the user anything.** The user's instruction is: list the
    options, pick one, state the recommendation, keep going. An unresolved question becomes
    a documented assumption, never a halt.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `SPEC.md` | Full requirement table (5 areas), decision log D1–D9 with the options considered, open questions | Always — before architecting. The decision log says *why* each number is what it is |
| `dual-adc-prompt.txt` | The user's original, verbatim request | Only to check an interpretation |

No datasheets, sketches, or reference designs were supplied by the user.

## Next phase must

Addressed to **circuit-architect**:

1. Produce the block diagram, net plan, IC selection, and skeleton BOM per your normal
   protocol, honouring every `[HARD]` item above.
2. **Solve the memory problem first — it is the keystone.** ≥ 4 MB must be writable at
   40 MB/s sustained. Enumerate the options explicitly and pick one:
   FPGA embedded PSRAM (e.g. Gowin GW1NR-9 class, 64 Mbit in-package) ·
   external HyperRAM / xSPI PSRAM · external SDR SDRAM · external async SRAM ·
   MCU with large on-chip SRAM. State pin count, bandwidth headroom, and JLCPCB
   availability for the one you choose. Everything else in the digital domain follows from
   this choice.
3. **Decide the digital controller** in the same breath: FPGA vs. high-pin-count MCU vs.
   a bridge IC with FIFO mode. It must concurrently service 2× 12-bit ADC at 10 MSPS
   (24 bits @ 10 MHz), the sample memory, and the USB FIFO.
4. **Decide the USB HS path**: discrete bridge with an 8/16-bit synchronous FIFO
   (FT232H/FT2232H/FT600-class, or a CH-series equivalent) vs. a soft/hard USB HS device
   inside the controller vs. an MCU with an on-chip HS PHY. Note that USB HS needs a real
   PHY — a full-speed-only path fails Decision 7.
5. **Design the analog front end explicitly for ±10 V into a low-voltage ADC.**
   The chain must deliver: 1 MΩ ∥ ~20 pF input, ±50 V survival, attenuation to the ADC's
   input span, level shift to the ADC common mode, and anti-alias filtering. Reason about
   attenuator-then-buffer vs. buffer-then-attenuator, and about single-ended vs. fully
   differential drive into the ADC. Say what bipolar rail voltages the chosen op amps need
   and how they are produced from +5 V (inverting charge pump vs. inverting switcher vs.
   isolated module) — Decision 10 makes this your problem, not the coder's.
6. **Budget the power** rail by rail, in mA, and check it against Decision 9. If the total
   exceeds 1.5 A, come back and change the architecture, not the requirement.
   **State explicitly what happens on a legacy A-to-C cable (500 mA source)** — either the
   design fits in 500 mA, or it must detect the condition. Pick one and say which.
7. Provide the ADC clock source and state how channel skew ≤ 5 ns is met.
8. Where a choice exists, **list the options in the architecture document and mark the one
   you selected** — the user asked for this explicitly and it is a deliverable, not a
   courtesy.

## Carried forward

| Open item | Why still open | What would close it |
|---|---|---|
| SNR ≥ 60 dB vs. true 12-bit accuracy (SPEC D5) | User specified resolution, not accuracy | A user statement on required ENOB |
| Burst vs. continuous streaming (SPEC D6) | Inferred from the 0.1 s wording + USB 2.0 bandwidth ceiling | A user statement that capture must be unbounded — which would invalidate USB 2.0 |
| Behaviour on a 500 mA (legacy A-to-C) source | Depends on the final power budget | The architect's rail-by-rail budget — **assigned to phase 2, item 6** |
| $90/board cost target | Assumed, not user-stated | A user budget |
| Enclosure / mounting | Never mentioned | User input; assume bare board |

## Do not redo

- **BNC** for the analog inputs. The prompt's "standard oscilloscope leads" settles it.
- **USB Type-C, USB 2.0 signalling, no PD.** The prompt authorised the Type-C fallback and
  the power budget triggers it. Do not revert to Type-B to save a connector, and do not
  escalate to PD.
- **12 bits and 10 MSPS and ±10 V and 0.1 s.** These are the user's four numbers. They are
  not negotiable and must not be "optimised".
- **Bus-powered.** No external supply jack may be added.
- **Burst-capture topology** (Decision 4) — re-deriving this as a streaming design wastes a
  full cycle.
- **The interview itself.** The user forbade pausing; do not generate questions back to the
  user in place of decisions.

## Receipt

- Circuit: `dual_adc_usb`; spec written autonomously from `dual-adc-prompt.txt` (user
  forbade interactive Q&A).
- Constraints: **11 `[HARD]`, 9 `[SOFT]`**; 9 logged design decisions (D1–D9) each with
  alternatives and a selected option.
- Open questions: **5**, all documented as assumptions; none blocking.
- Keystone risk flagged to phase 2: ≥ 4 MB sample buffer at 40 MB/s write, bus-powered.
- `use_cache = false` (blank-slate run).
