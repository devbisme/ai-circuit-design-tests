---
phase: requirements
status: complete
next_phase: architecture
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Derived a complete SPEC.md for a dual-channel, ±10 V, 12-bit, 10 MSPS/channel ADC
  board from the raw prompt — no user interview performed (autonomous-run override),
  0 questions asked.
- Resolved all four flagged hard issues (throughput, analog front end, input
  connector, power budget) with explicit options tables and a recommendation, adopted.
- Also fixed: channel count/simultaneity, ADC interface type, digital controller
  family, resolution/ENOB target, input protection, form factor, host connector.
- Production quantity/cost/manufacturer were not specified by the user — reasonable
  SOFT defaults assumed and flagged below for confirmation.
- 8 design decisions logged (D1-D8); 15+ hard constraints, 7 soft/open items carried
  forward (see below).

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|-------------------|
| SPEC.md | Full spec: Functional/Power/Interface/Physical/Production + Design Decisions log (D1-D8) | architecture |
| dual-adc-prompt.txt | Original raw user prompt (verbatim, for traceability) | architecture (optional) |

## Key facts for the next phase

- **Channels:** 2, simultaneous (two independent ADC ICs, shared convert clock — not
  a mux'd single ADC). [HARD]
- **Input range:** ±10 V bipolar, DC-coupled, per channel. [HARD]
- **Sample rate:** 10 MSPS per channel, both channels concurrently in burst mode.
  [HARD]
- **Resolution:** 12-bit nominal, target ENOB ≥10.5 bits. [HARD/SOFT: rate is hard,
  ENOB target is soft — a datasheet-typical figure, not user-specified]
- **Burst capture depth:** 32,768 samples/channel (3.2768 ms full-rate dual-channel,
  gap-free). [SOFT — architect's choice of exact buffer depth given available FPGA
  BRAM/external SRAM; 32k is the assumed baseline]
- **Continuous streaming:** either single-channel at full 10 MSPS/12-bit (120 Mbps,
  recommended default) or dual-channel decimated to ~8 MSPS/ch combined ≈192 Mbps.
  [HARD constraint: must stay ≤~240 Mbps practical USB2 HS ceiling with margin]
- **Data packing:** 12-bit packed (3 bytes / 2 samples), not 16-bit padded. [HARD]
- **Analog bandwidth:** front end ≥5 MHz −3dB; anti-alias LPF corner ≈5 MHz, ≥40 dB
  attenuation by 15-20 MHz. [HARD]
- **AFE topology:** ~11:1 resistive attenuator (±10V → ±0.91V) + single-supply op-amp
  level-shift/anti-alias stage into ADC's single-ended unipolar input (assume ADC
  common-mode ~1V, input range ~0-2V — verify against exact ADC MPN chosen at
  sourcing). [HARD requirement: attenuate+shift+filter; exact ratio/topology is SOFT
  and depends on final ADC MPN's actual input range]
- **ADC family:** 12-bit, ≥10 MSPS, parallel CMOS (LVCMOS) output, single 3.3-5V
  supply — candidates AD9226/AD9235/ADS822 family. Exact MPN NOT yet chosen — that is
  sourcing's job. [interface type is HARD (parallel CMOS, not LVDS); exact MPN SOFT]
- **Digital controller:** small CPLD/FPGA (e.g. Lattice iCE40) for ADC clocking,
  dual-channel capture RAM, mode muxing, 12-bit packing — paired with FTDI FT2232H (or
  FT232H) in USB2 Hi-Speed synchronous FIFO mode for the USB link. [HARD: this
  two-chip split; exact FPGA MPN SOFT]
- **Host connector:** USB-C receptacle, USB 2.0 signaling only (D+/D-, VBUS, GND),
  CC1/CC2 5.1kΩ pull-downs to GND for default power negotiation. [HARD]
- **Input connectors:** BNC ×2, 1 MΩ input impedance (standard passive-probe
  compatible). [HARD]
- **Input protection:** series resistor (attenuator) limits fault current + clamp
  diodes/TVS at op-amp input; target survive ±40V continuous overdrive; ESD per IEC
  61000-4-2 at the BNC. [SOFT — target values assumed, not user-specified]
- **Power rails:** +3.3V (~120mA, FPGA/USB logic), +5V clean analog (~90mA, ADC+opamp
  positive supply), −5V analog (~30mA, opamp negative supply), optional 1.8V FPGA core
  (~30mA). Total est. ≈270-300mA against the USB 500mA ceiling. [HARD ceiling: total
  must stay ≤500mA with margin; individual rail current estimates are SOFT]
- **Negative rail generation:** on-board switched-capacitor charge-pump inverter (e.g.
  TPS60403/LM2776 class), −5V from USB +5V. [HARD: must be on-board, no external
  supply; exact part SOFT]
- **Board:** 4-layer PCB, ~100mm x 70mm, SMD-first construction, 0-50°C operating
  range assumed. [layer count HARD given mixed-signal noise risk; exact dimensions
  SOFT]

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|
| D1 | Throughput strategy | capture RAM+burst / decimation / single-ch-full-rate / 12-bit packing / lossless compression | Capture-RAM burst (primary) + packing always-on + continuous mode trades rate/channels | Only combination giving true dual-simultaneous 10MSPS/12-bit capture while still offering continuous data; compression rejected as unreliable on real signals |
| D2 | Analog front end | passive divider only / divider+single-ended op-amp+AAF / divider+differential driver+AAF | Divider (~11:1) + single-ended op-amp level-shift+AAF | Matches single-ended parallel-CMOS ADC choice; simplest that still meets noise/bandwidth needs |
| D3 | Digital controller / ADC interface | FT2232H+CPLD / MCU w/ native USB2 HS / FPGA w/ own USB core | FT2232H sync-FIFO + small CPLD/FPGA; parallel CMOS ADC interface | Lowest USB engineering risk, FIFO throughput matches budget exactly; parallel CMOS simpler than LVDS at only 10MSPS |
| D4 | Negative rail generation | charge-pump inverter / inductor inverting buck-boost / isolated DC-DC / external supply | Switched-capacitor charge-pump inverter | Simple, cheap, sufficient current for op-amp bias, stays within USB power budget, no isolation needed |
| D5 | Simultaneous vs multiplexed sampling | 2x ADC (one/channel) / 1x ADC + analog mux | 2x ADC, shared convert clock | True time-coincident dual-channel capture expected of a "dual-channel" instrument; mux'd approach needs 2x ADC rate anyway and adds phase skew |
| D6 | Host connector | USB Type-B / Micro-B / USB-C | USB-C (USB2 signaling only) | Modern robust standard connector; SuperSpeed lanes simply unused |
| D7 | Input connector impedance | 1MΩ / 50Ω | 1MΩ | Matches "standard oscilloscope leads" (passive probes), general-purpose ±10V signal range, not RF |
| D8 | PCB layer count | 2-layer / 4-layer | 4-layer | Ground/power plane isolation needed to protect 12-bit ENOB from 10MHz digital switching noise |

## Carried forward

- **Production quantity** — user gave none. Assumed 5-10 board prototype run (SOFT).
  Architect/sourcing should proceed with this; revisit if the user states a real
  volume (affects part packaging, panelization, DFM tradeoffs).
- **Cost target** — user gave none. Assumed ≤$150/unit BOM at prototype quantity
  (SOFT). Needed to close: does the user care about cost at all, or is this
  performance-first? No signal either way in the prompt.
- **Manufacturer preference** — user gave none. Assumed JLCPCB (matches this
  pipeline's part-sourcing tooling: pcbparts MCP / find-part skill JLCPCB rules).
  Needed to close: confirm no conflicting preference (e.g. a specific US-based fab)
  before final BOM lock.
- **Exact ADC MPN** — family fixed (12-bit, ≥10MSPS, parallel CMOS, e.g.
  AD9226/AD9235/ADS822), exact part deferred to sourcing/architecture. Needed to
  close: real-time JLCPCB stock/price check, exact input-range/common-mode spec to
  finalize the AFE attenuation ratio in D2.
- **Exact FPGA/CPLD and USB bridge MPNs** — family fixed (small Lattice-class
  CPLD/FPGA + FT2232H/FT232H), exact parts deferred to sourcing.
- **AFE attenuation ratio and common-mode voltage** — currently a placeholder (~11:1,
  assumed ADC input 0-2V/CM~1V) pending the actual chosen ADC's datasheet input-range
  spec. Architect should treat the ratio as provisional and recompute once the ADC MPN
  is fixed.
- **Environmental/regulatory targets** (0-50°C, CE/FCC Class B) — assumed defaults,
  not user-specified. No action needed unless user later states real requirements.
- **Continuous-streaming host protocol details** (mode-select command, endpoint
  framing) — not specified; architect should define at least a minimal control
  scheme (e.g. vendor control transfer to select burst vs. streaming vs. decimation
  factor) since the FT2232H FIFO interface alone doesn't carry control semantics.

## Do not redo

- BNC input connectors — firm (matches "standard oscilloscope leads" explicitly).
- ±10V bipolar input range, 10 MSPS/channel, 12-bit resolution — firm, from the
  prompt verbatim.
- USB 2.0 port providing both power and data — firm, from the prompt verbatim.
- Two channels, simultaneous (not multiplexed) sampling — settled in D5, do not
  reopen without a strong architecture-driven reason (e.g. ADC unavailability at the
  needed spec).
- On-board negative rail generation via charge pump — settled in D4; do not
  reintroduce an external supply.
- USB-C connector, USB2-only signaling — settled in D6.
- 4-layer PCB — settled in D8, do not downgrade to 2-layer without flagging cost vs.
  ENOB-risk tradeoff explicitly to the user.

## Escalation

none
