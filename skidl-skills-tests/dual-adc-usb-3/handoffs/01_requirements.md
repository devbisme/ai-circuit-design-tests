---
phase: 01_requirements
agent: new-circuit-driver
circuit: dual_adc_usb
written: 2026-09-09T00:00:00Z
status: complete
revision: 1
next_phase: 02_architecture
---

# Phase 1 handoff — Requirements

Autonomous mode. The user supplied a written brief (`dual-adc-prompt.txt`) and explicitly
forbade interactive questions: *"When decisions about the design are needed, list all the
options and then select the one you recommend. Do not pause the design process and wait for
my input."* That directive binds you too — decide, record the options you rejected and why,
never stop to ask. Also: **start from a blank slate — do not read, copy, or reuse anything
from sibling directories (`../dual-adc-usb-1`, `../dual-adc-usb-2`) or any other design in
this tree.**

## Decisions

Constraints the architecture must design against. `[HARD]` = do not trade away.
`[SOFT]` = trade away only with a stated reason in `architecture/design_risks.md`.
Full text and rejected options: `SPEC.md`.

1. [HARD] 2 analog channels, **simultaneously sampled** (shared sample clock, no input mux).
2. [HARD] Full scale ±10 V (20 Vpp) at the BNC with a 1× lead; DC-coupled.
3. [HARD] 10 MSPS per channel, 12-bit resolution.
4. [HARD] Input network 1 MΩ ∥ ≤25 pF, compensated — passive scope probes require it.
   50 Ω termination is explicitly rejected.
5. [HARD] Anti-alias filter: −3 dB at ~4 MHz, ≥30 dB at 10 MHz, ≥50 dB at 20 MHz
   (4th-order class). Do not spend op-amps chasing a brick wall.
6. [SOFT] Inputs survive ±50 V DC continuous; clamp/protect at the front end.
7. [HARD] USB 2.0 high-speed device, USB-C receptacle (USB 2.0 wiring only, 2× 5.1 kΩ CC
   pulldowns). Bus-powered from VBUS only — no jack, no battery.
8. [HARD] ≤450 mA @ 5 V sustained; ≤100 mA before enumeration.
9. [HARD] Bipolar analog rails (e.g. ±5 V/±6 V) generated on-board from VBUS; every analog
   rail LDO post-regulated, ≤100 µVrms 10 Hz–1 MHz at ADC and reference pins.
10. [HARD] **Sample payload is 30 MB/s only if bit-packed** (2 × 10 MSPS × 12 b = 240 Mb/s).
    Padding to 16 bits gives 40 MB/s, which exceeds practical USB 2.0 bulk throughput
    (~35–43 MB/s). Packing (4 samples → 3 × 16-bit words) happens on-board, before the USB
    endpoint. Do not design a padded-16-bit streaming path.
11. [HARD] Two capture modes: (a) triggered burst into on-board buffer memory, lossless at
    full rate, host-independent; (b) continuous streaming, best-effort, with an overrun flag
    in the stream. Mode (a) is what makes the 10 MSPS claim honest — a design with no
    buffer is not acceptable.
12. [HARD] Vendor control endpoint for arm/trigger/range/status; bulk IN endpoint for data.
13. [SOFT] Hardware level/edge trigger on either channel; 3-pin 3.3 V ext-trigger header.
14. [HARD] 4-layer FR4 ≤100 × 80 mm, all SMD except BNC/USB/headers, 0–70 °C, no BGA finer
    than 0.8 mm pitch, no regulatory certification required.
15. [HARD] JLCPCB-assemblable: in-stock parts, Basic/Preferred preferred, no NRND/EOL.
    [SOFT] ≤$180 BOM per board at qty 5, qty 5 prototypes.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `SPEC.md` | All 5 requirement areas, each requirement tagged HARD/SOFT with the options considered and why the selection won | Always — before choosing any topology |
| `dual-adc-prompt.txt` | The user's original brief, verbatim | To confirm what the user actually asked for vs. what the driver assumed |

No datasheets, sketches, or reference designs were supplied by the user.

## Next phase must

Addressed to **circuit-architect**:

1. Read `SPEC.md` in full. Every requirement is tagged `[USER]` or `[DRIVER]` — a `[DRIVER]`
   tag means the driver chose it in autonomous mode, so you may revisit it if you state the
   reason; a `[USER]` tag is not yours to change.
2. Produce the standard architecture artifact set (`architecture/block_diagram.md`,
   `net_plan.md`, `ic_selection.md`, `skeleton_bom.md`, `design_risks.md`) plus the
   `## Block manifest` table this pipeline's stage-5 router needs.
3. Reason **explicitly, with options listed and one recommended**, about at least these:
   - **Digitizer chain**: dual-channel ADC vs. two single ADCs on a shared clock; serial
     (LVDS/CMOS) vs. parallel output. Parallel CMOS is cheap and easy to capture but costs
     ~24 I/O; serial saves pins but needs deserialization.
   - **Data path to USB**: USB MCU with slave-FIFO (e.g. FX2LP-class) directly off the ADC
     bus, vs. programmable logic (CPLD/small FPGA) doing capture + packing + buffering in
     front of the USB device, vs. a high-pin-count MCU. Requirement 10 (packing) and 11
     (buffer) are the deciding constraints — say how each option meets them.
   - **Capture buffer**: FPGA block RAM vs. external SRAM vs. SDRAM. State the resulting
     burst depth in samples and check it against a scope-like use case.
   - **Front end**: high-Z compensated attenuator + buffer topology; single-ended vs. fully
     differential drive into the ADC; how ±10 V maps to the ADC's input range and
     common-mode; where the AAF sits.
   - **Power tree**: VBUS → digital rails, and how the bipolar analog rails are made
     (inverting charge pump vs. inverting DC-DC vs. transformer-coupled), with the 450 mA
     budget allocated per block. Include a current budget table.
   - **Clocking**: ADC sample clock source and how the two channels stay phase-aligned;
     jitter budget for 12 bits at 4 MHz input (≥ ~10 ps rms is the rough bar).
4. Keep the block count consistent with the pipeline's coding modes: >3 blocks selects
   modular mode, which is expected and fine here. Give every block a stable `block_id`
   usable as a Python module name.
5. Any part you name must be plausibly stockable at JLCPCB — the next phase will verify
   stock and will send the design back to you if a keystone part is unobtainable. Prefer
   parts with a real second source; flag single-source parts in `design_risks.md`.
6. Record the current budget, the USB throughput arithmetic, and the jitter budget in
   `design_risks.md` so the coder and reviewer inherit the numbers rather than re-deriving
   them.

## Carried forward

- **AC coupling** deferred (DC-only chosen). Would close if the user says they need to look
  at small signals riding on a DC offset — costs a relay + film cap per channel.
- **Probe attenuation sensing** (the ring contact on a compensated BNC) is not implemented;
  the host must be told the probe ratio manually. Would close on a user request.
- **On-board calibration source** not specified. F8 (±2 % FS) assumes a one-time host-side
  calibration against an external reference. A DAC-based self-cal path is a cost/complexity
  add the architect may propose but should not assume.
- **Firmware** is out of scope for this pipeline (hardware/netlist only), but the hardware
  must not preclude it: EEPROM fitted, programming/JTAG header present.
- **Enclosure and BNC ground referencing** unaddressed — BNC shells tie to board ground; if
  the user later wants isolated channels, this design cannot do it.
- Nothing in the user's brief pins down cost, size, quantity, or temperature range: items
  N1, N3, X1, X5 are driver assumptions and are the first things to trade away under
  pressure.

## Do not redo

- Channel count, ±10 V range, 10 MSPS, 12 bits, USB 2.0 bus power — these are the user's
  words and are not open for reinterpretation.
- BNC connectors and the 1 MΩ ∥ ≤25 pF input: settled by "mate with standard oscilloscope
  leads". Do not propose SMA or 50 Ω inputs.
- Bus-powered-only: do not add an auxiliary power jack.
- Do not re-run the requirements interview; the user has forbidden interactive questions.
- Do not read or reuse artifacts from any sibling design directory.

## Receipt

- Circuit: `dual_adc_usb`; requirements captured from a written brief, 0 interactive questions
  (user forbade pausing).
- 24 HARD constraints, 14 SOFT constraints across the 5 spec areas.
- 6 open questions carried forward; none blocks architecture.
- Key derived constraint: 30 MB/s bit-packed vs 40 MB/s padded over USB 2.0 HS → packing and
  an on-board capture buffer are mandatory.
- Status: complete → `02_architecture`.
