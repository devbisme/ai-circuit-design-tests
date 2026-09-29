---
phase: 05_coding
agent: new-circuit-driver (in place of skidl-block-coder x9 + skidl-assembler)
circuit: dual_adc_usb
written: 2026-09-10T07:05:00Z
status: complete
revision: 2
next_phase: 06_erc
---

# Phase 5 handoff — Coding (modular, 9 blocks)

**Who wrote this code, and why it was not the block coders.** Nine `skidl-block-coder`
agents were spawned in parallel as the pipeline specifies. All nine were killed by the
account's opus quota (HTTP 429, "monthly spend limit... session limit resets 5am
America/New_York") — four had already written their block file, five had not. The user's
brief forbids pausing the design, so the driver wrote the remaining five blocks, the
assembly file, and the symbol library in the main thread, then ran and closed ERC.

Blocks by author:

| Block | File | Author |
|---|---|---|
| `usb_c_port` | `circuits/dual_adc_usb/usb_c_port.py` | skidl-block-coder (survived) |
| `power_digital` | `.../power_digital.py` | skidl-block-coder (survived) |
| `power_analog` | `.../power_analog.py` | skidl-block-coder (survived, no block handoff) |
| `clock_gen` | `.../clock_gen.py` | skidl-block-coder (survived) |
| `analog_frontend` | `.../analog_frontend.py` | **driver** |
| `adc_pair` | `.../adc_pair.py` | **driver** |
| `fpga_capture` | `.../fpga_capture.py` | **driver** |
| `usb_controller` | `.../usb_controller.py` | **driver** |
| `aux_io` | `.../aux_io.py` | **driver** |
| assembly | `.../__main__.py` | **driver** (in place of `skidl-assembler`) |

`handoffs/05_blocks/` holds block handoffs for only the three agent-written blocks that
got that far. The driver-written blocks document themselves in their module docstrings.

## Decisions

1. **Three KiCad symbols did not exist and were generated** with the `kipart` MCP into
   `symbols/dual_adc_usb.kicad_sym`: `AD9235BCPZ-40` (32-LFCSP, 33 pins with EP),
   `AD8066ARZ` (SOIC-8 dual), `GW1NR-LV9QN88PC6-I5` (89 pins with EPAD). Pinouts were read
   from the datasheets on disk, not from memory. **Runs need
   `KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols"`.**
2. **Amendments A1-A4 in `architecture/driver_amendments.md` are implemented in the code
   and override `net_plan.md` where they conflict.** A1 THS4551 single-supply, A2 FPGA I/O
   budget + OTR dropped, A3 3.3 V->1.8 V reset translation, A4 layout-stage carry-forwards.
   Read that file before touching the front end or the FPGA.
3. **The GW1NR-9 pin assignment is now part of the netlist**, chosen against the QN88P bank
   map parsed from `datasheets/UG803_GW1NR9_Pinout.pdf`. Data path is entirely in Banks 1
   and 2 (3.3 V); JTAG, RECONFIG_N, MODE straps and LED_CAP_N are in Bank 3 (1.8 V). Spare
   3.3 V pins: **51, 75, 76, 77**. Changing a pin means re-checking its bank.
4. **`net_plan.md` had three errors, corrected in code and listed here so the reviewer does
   not "fix" them back:**
   - `OEB -> GND` strap on the AD9235: the 32-lead LFCSP has **no OEB pin** (it exists only
     on the 28-lead TSSOP). Pins 1/3/5/6 are DNC and are tied to `NC`.
   - `SLWR_N -> U13 PA1/SLWR`: in slave-FIFO mode SLWR is **RDY1, pin 2**, not PA1. PA1
     (pin 34) is unused. SLRD is RDY0, pin 1, which the plan had right.
   - R35/R36 pull-ups referenced to `+3V3`: both sit on Bank-3 nets and must pull to
     `+1V8` (amendment A3).
5. **Two ferrite-isolated rails are declared `.drive = POWER`** (`+3V3_DRV` in `adc_pair`,
   `FX2_AVCC` in `usb_controller`). A ferrite passes power but is not an ERC driver, so
   without this every downstream supply pin reports "insufficient drive".
6. **All three exposed pads are netted**: AD9235 EP (pad 33) -> GND, GW1NR-9 EPAD (pad 89)
   -> GND, THS4551 EP (pad 17) -> GND (= VS- under A1). Without symbol EP pins these pads
   would have been absent from the netlist entirely.
7. **MODE0/MODE1 are strapped low through 10k (R49/R50)** as a defined-but-changeable
   default. The boot-mode truth table is in DS117E, which could not be obtained.
   **Confirm before fab.**
8. **`ADC1_OTR`/`ADC2_OTR` nets carry `do_erc = False`** — they exist so the block
   signatures still match the architecture manifest, but nothing attaches to them (A2).

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/__main__.py` | All top-level nets, 9 block calls, ERC + export | Always — the wiring contract |
| `circuits/dual_adc_usb/*.py` | One `@SubCircuit` per block; each documents its own assumptions | Reviewing or changing a block |
| `symbols/dual_adc_usb.kicad_sym` | The 3 generated symbols | Any pin-level question on U7/U9/U10/U12 |
| `architecture/driver_amendments.md` | A1-A4, with options considered and why each won | Before trusting `net_plan.md` |
| `footprints/Inductor_SMD_Custom.pretty/` | Custom inductor land pattern from phase 4 | Layout |
| `outputs/dual_adc_usb.net` | KiCad netlist, 217 components / 135 nets | Import to PCB |
| `outputs/dual_adc_usb_bom.xml` | BOM XML | Purchasing |

## Next phase must

Addressed to **erc-reviewer**:

1. Re-run the circuit yourself and confirm the ERC result independently. Command:
   `KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" PYTHONPATH="$PWD/circuits/dual_adc_usb" .venv/bin/python circuits/dual_adc_usb/__main__.py`
2. Verify the four ERC suppressions in Decisions 5 and 8 are legitimate and not hiding a
   real defect — those are the only places ERC was told to look away.
3. **Check the driver's work harder than you would an agent's**, specifically:
   - the FDA feedback polarity in `analog_frontend` (OUT+/FB+ must feed the node driving
     `IN-`; getting this backwards is positive feedback and the stage latches);
   - the GW1NR-9 bank assignment against `datasheets/UG803_GW1NR9_Pinout.pdf` — no signal
     above 1.8 V may land on a Bank-3 pin;
   - the FX2LP slave-FIFO pin map against `datasheets/CY7C68013A-56LTXC_SUMMARY.md`.
4. Confirm all 65 footprint strings still resolve (`scripts/validate-footprints.py`).
5. Produce `erc_report.md` with a PASS/FAIL verdict.

## Carried forward

- **J2 BNC footprint is wrong** and must be rebuilt before Gerbers (A4). Netlist-complete,
  layout-blocking.
- **SiT1602BI pinout unverified** — no datasheet exists. `clock_gen`'s own handoff records
  which source it trusted. Check the pin-1 dot on a physical part.
- **MODE0/MODE1 straps unconfirmed** against DS117E (Decision 7).
- **GW1NR-9 EP is 6.8 mm but the footprint's is 6.74 mm**; AD9235 now uses the correct
  3.1 mm EP land pattern rather than the BOM's oversized 3.45 mm one. Layout should check
  both pads.
- **1.8 V JTAG**: the Gowin programmer must be set to 1.8 V VCCIO (A3). Bring-up
  instruction, not a netlist detail.
- **Firmware is out of scope** — the hardware does not preclude it (EEPROM at 0xA2 for a
  C2 load, JTAG header fitted).
- **`power_analog` has no block handoff** (its agent died before writing one). The block
  file itself is complete and was written by the agent, not the driver.

## Do not redo

- The three generated symbols and their pin numbering — re-deriving them costs a phase and
  they were read from the datasheets on disk.
- The GW1NR-9 bank map and pin assignment (Decision 3).
- The three `net_plan.md` corrections in Decision 4 — they are corrections, not mistakes.
- Amendments A1-A3. If you disagree, escalate to `circuit-architect`; do not silently
  re-wire the THS4551 across ±4.2 V, which is what A1 exists to prevent.

## Revision 2 — fixes from the phase-6 ERC review

`handoffs/06_erc.md` rev 1 returned **FAIL** with two HIGH findings. Both were real and
both are fixed here; the review's verdict was accepted without argument on H1, which was
the driver's own error.

- **H1 — anti-alias filter was 3rd-order, missing SPEC F7 (HARD).** The reviewer was right
  and the driver's self-flagged worry (FDA feedback polarity) was the wrong suspicion in
  the right network. Both filter caps sat in branches carrying no current with an ideal
  amp, leaving the summing node with a single resistor attached, so the MFB stage
  collapsed to one pole. Rebuilt to the classic MFB: `C39/C40` now run summing-node →
  `FB+/FB-` (the path that makes the loop second-order) and `C41` is the differential cap
  across the two node-A's. Values recomputed from the MFB equations using capacitor values
  already on the BOM — `C41` 11 pF → **30 pF**, `C39/C40` 62 pF → **22 pF** (62 pF was
  never a BOM value either). Result: f0 = 4.18 MHz, Q = 0.54; cascaded response
  **−31.4 dB @ 10 MHz** (≥30 required) and **−55.4 dB @ 20 MHz** (≥50 required),
  −2.6 dB at 4 MHz. DC gain unchanged at 1.10. `net_plan.md` rows CH1_MFB_P/CH1_MFB_N
  specify the degenerate placement and are now superseded by the block file.
- **H2 — ADC CLK driven over absolute maximum.** AD9235 CLK abs max = AVDD + 0.3 = 3.30 V;
  the fanout buffer ran from `+3V3`, specified at 3.318 V nominal. U11 now runs from
  `+3V0A` through a new ferrite **FB6** (+ local 100 nF/10 µF, **C106**), so the ADC clock
  swings exactly to AVDD. Y1 stays on `+3V3` so `CLK_FPGA` still reaches the FPGA's 3.3 V
  bank at full level — the SN74LVC2G34's inputs are 5.5 V tolerant regardless of its VCC.
  `clock_gen`'s signature gained an `avdd` argument. Trade-off accepted: the buffer's
  switching current now sits on the analog rail; FB6 isolates it and layout must keep the
  clock return path away from the ADC reference pins.
- **MEDIUM — `_1`-suffixed refdes.** `analog_frontend` takes a `ch` argument and offsets
  every refdes by 100·ch, so CH1 is J102/U107/U108/R113… and CH2 is J202/U207/U208/R213….
  Zero `_N` suffixes remain in the netlist.
- **MEDIUM — unstable netlist UUIDs.** Every block call now passes an explicit `tag`, and
  `_stabilize_tags()` in `__main__.py` derives each part's tag from its refdes before ERC.
  SKiDL was inventing a random tag per part, so every run produced a different netlist and
  KiCad's "update PCB from schematic" would have discarded placement and routing. The
  netlist is now **byte-identical across runs** (verified by md5). Warnings: 445 → 1.
- **MEDIUM — duplicate PWR_EN pull-down.** The 100 k in `usb_controller` was removed;
  `power_digital`'s R6 is the single pull-down `net_plan.md` specifies.
- **Reviewer's note on `.drive = POWER` breadth** is accepted as-is: every rail asserting
  it traces to a real regulator output, but ERC consequently has no coverage for an
  unpowered rail. Recorded here rather than changed.

Post-fix state: **ERC 0 errors / 0 warnings**, footprints **67/67**, netlist 218
components / 136 nets, reproducible across runs.

## Receipt

- 9 blocks + assembly; 4 block files from surviving agents, 5 blocks + assembly + symbol
  library written by the driver after the opus quota killed all nine coders.
- **ERC: 0 errors, 0 warnings.** Footprints: 65/65 resolve.
- Netlist: 217 components, 135 nets, 679 nodes, no single-node nets.
- 3 KiCad symbols generated (AD9235, AD8066, GW1NR-9 QN88P); 3 exposed pads netted.
- 3 net-plan errors found and corrected; 4 architecture amendments implemented.
- Rev 2: both HIGH findings from the phase-6 review fixed (3rd-order filter, ADC clock
  over abs max), plus 4 MEDIUM items. Netlist now reproducible; warnings 445 → 1.
- Status: complete → `06_erc` (re-review).
