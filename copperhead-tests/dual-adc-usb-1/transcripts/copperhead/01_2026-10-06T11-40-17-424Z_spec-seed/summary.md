# Run summary

- **Request:** create pipeline stage: spec-seed
- **Outcome:** success
- **OpenSpec change:** spec-seed-dual-adc-usb
- **Tokens:** 66 in / 33930 out

## Environment

- **Run:** 2026-10-06T11-40-17-424Z · create · started 2026-10-06T11:40:17.442Z · autonomous
- **Stage:** spec-seed (1/8)
- **Brief:** dual-adc-prompt.txt (sha256 6fda2f5a66e9…)
- **Model:** claude-code (claude-code, via env)
- **copperhead:** v0.11.0 at /home/devb/.nvm/versions/node/v22.23.3/lib/node_modules/copperhead
- **Tooling:** kicad-cli 9.0.9 · node v22.23.3 · linux-x64
- **Config:** schematic null · board null · docs docs/ · maxTurns 40 · maxRepairCycles 5 · budgets {}
- **Repo:** master@4cadab6b6ec0c077354693ca029ac78ba3b2ee9a · dirty (1 uncommitted) · pre-commit hook absent
- **Memory:** 0 open constraint(s) · 0 prior run(s)

## Run stats

- **Exit path:** done
- **Turns:** 33 / 40
- **Repair cycles:** 0 / 5
- **Tokens:** 66 in / 33.9k out
- **Duration:** 6m53s
- **Per turn:** 1: 2/417 · 2: 2/2022 · 3: 2/4254 · 4: 2/23 · 5: 2/9229 · 6: 2/341 · 7: 2/224 · 8: 2/341 · 9: 2/281 · 10: 2/373 · 11: 2/337 · 12: 2/403 · 13: 2/369 · 14: 2/442 · 15: 2/366 · 16: 2/384 · 17: 2/341 · 18: 2/396 · 19: 2/403 · 20: 2/368 · 21: 2/431 · 22: 2/379 · 23: 2/320 · 24: 2/657 · 25: 2/433 · 26: 2/467 · 27: 2/505 · 28: 2/368 · 29: 2/453 · 30: 2/137 · 31: 2/1063 · 32: 2/6166 · 33: 2/1237

## Plan

First I'll check what docs and `openspec/` workspace already exist, so I know what to seed.

## Files touched

- docs/SPEC.md
- docs/DECISIONS.md

## Verification

- ERC: not run
- DRC: not run
- legibility: not run
- score: not run

## Decisions

- USB connector/power source: USB-C receptacle carrying USB 2.0 HS data, power sink with 5.1 kOhm Rd on CC1/CC2, no USB-PD. Options considered: (a) USB 2.0 Type-B/Micro-B, (b) USB-C with Rd sink, (c) USB-C with PD negotiation. | why: Estimated 170-410 mA is close to the 500 mA USB 2.0 limit, which is the brief's trigger for USB-C; the board stays budgeted to <=450 mA so it still works on any USB 2.0 host via a C-to-A cable, and PD adds cost and complexity with no benefit at 5 V.
- Capture architecture: capture to an on-board buffer then read out over USB as the guaranteed mode, plus best-effort streaming at reduced rate or with packed 12-bit data. Options considered: (a) continuous USB streaming only, (b) capture-to-buffer then readout, (c) hybrid buffered + best-effort streaming. | why: 30-40 MB/s raw data is at or above practical USB 2.0 HS bulk throughput (~35-42 MB/s, host-dependent), so the 0.1 s requirement must be met by on-board memory and not depend on the host.
- Buffer memory: 16-bit SDR SDRAM, 256 Mbit (32 MB). Options considered: (a) FPGA block RAM, (b) x16 SDR SDRAM >=256 Mbit, (c) 64 Mbit HyperRAM, (d) 64 Mbit QSPI PSRAM, (e) DDR3. HyperRAM is the fallback if FPGA pin count gets tight. | why: 4 MB exceeds small-FPGA BRAM; SDR SDRAM is cheap, widely available, gives ~200 MB/s raw at 100 MHz (5x the 40 MB/s write rate) and ~0.8 s depth (8x requirement) with a simple controller, while DDR3 adds layout/termination complexity for no benefit.
- USB bridge: FTDI FT232H in synchronous 245 FIFO mode. Options considered: (a) FT232H sync FIFO, (b) Infineon/Cypress FX2LP (CY7C68013A), (c) Infineon FX3 (CYUSB3014) at HS, (d) MCU with HS PHY (e.g. STM32 + ULPI PHY), (e) FPGA soft USB + ULPI PHY. FX2LP is the fallback if custom descriptors/endpoints are needed. | why: Sync FIFO (~40 MB/s) maps directly to FPGA logic with no bridge firmware and mature host drivers (D2XX/libftdi); FT232H suspend current must still be verified against power.suspend_current_mA (<=2.5 mA) in part selection before committing.
- Input connector: right-angle PCB-mount BNC jack per channel, shell to GND. Options considered: (a) BNC PCB jack, (b) SMA, (c) 4 mm banana, (d) 2.54 mm header with test clips. | why: 'Standard oscilloscope leads' means BNC: passive scope probes and BNC-to-clip leads mate directly; SMA/banana/header would need adapters.
- Front-end input impedance: 1 MOhm || ~20 pF per channel (ASSUMED). Options considered: (a) 1 MOhm || ~20 pF, (b) 50 Ohm, (c) selectable 1 MOhm / 50 Ohm. | why: Passive 1x/10x scope probes only compensate correctly into 1 MOhm; 50 Ohm would load the +/-10 V sources and dissipate 2 W at full scale, and a selectable termination adds a relay and power for no requirement in the brief.
- [affects] adc.sample_rate_MSPS affects ADC selection: no change needed: no ADC chosen yet at spec stage; >=10 MSPS/ch simultaneous is carried in SPEC.md §2 F3/§4.8 as a selection criterion for the part-selection stage
- [affects] adc.sample_rate_MSPS affects clock oscillator: no change needed: no oscillator chosen yet; 10 MHz (or multiple) sample clock requirement carried in SPEC.md §3/§6 for part selection
- [affects] adc.sample_rate_MSPS affects FPGA capture logic: no change needed: logic not yet designed; 2x12-bit @10 MSPS capture rate carried in SPEC.md §4.7
- [affects] adc.sample_rate_MSPS affects capture.buffer_MB: no change needed: checked consistent — 2 ch x 10 MSPS x 0.1 s x 2 B = 4 MB, matches capture.buffer_MB min 4
- [affects] adc.resolution_bits affects ADC selection: no change needed: no ADC chosen yet; >=12-bit carried in SPEC.md §2 F4/§4.8 as selection criterion
- [affects] adc.resolution_bits affects analog.enob_bits: no change needed: checked consistent — 10.5 ENOB target is achievable below the 12-bit ideal (~11.7 ENOB ideal ceiling incl. jitter budget)
- [affects] adc.resolution_bits affects capture.buffer_MB: no change needed: checked consistent — 12-bit stored in 16-bit words gives the 2 B/sample used in the 4 MB derivation
- [affects] input.voltage_range_V affects front-end attenuator/buffer: no change needed: front end not yet designed; ±10 V full scale carried in SPEC.md §2 F2/§3 for front-end design stage
- [affects] input.voltage_range_V affects ADC input driver: no change needed: driver not yet designed; requirement carried in SPEC.md §3
- [affects] input.voltage_range_V affects bipolar rail generation: no change needed: rails not yet designed; SPEC.md §3.1 already anticipates ±5 V-class rails sized after attenuator ratio is chosen
- [affects] input.voltage_range_V affects input.overvoltage_V: no change needed: checked consistent — ±30 V survival exceeds the ±10 V operating range by 3x
- [affects] capture.depth_s affects capture.buffer_MB: no change needed: checked consistent — 0.1 s depth yields the 4 MB minimum; recommended 32 MB SDRAM gives ~0.8 s
- [affects] capture.depth_s affects buffer memory selection: no change needed: recommendation (256 Mbit x16 SDR SDRAM, SPEC.md §4.4) already satisfies 8x margin; part chosen in part-selection stage
- [affects] capture.depth_s affects FPGA capture logic: no change needed: logic not yet designed; depth requirement carried in SPEC.md §2 F5
- [affects] capture.buffer_MB affects buffer memory selection: no change needed: recommended 32 MB SDRAM >= 4 MB (SPEC.md §4.4); final part chosen later
- [affects] capture.buffer_MB affects FPGA capture logic: no change needed: SDRAM controller requirement noted in SPEC.md §4.4/§4.7; logic not yet designed
- [affects] capture.buffer_MB affects FPGA pin count: no change needed: x16 SDRAM needs ~38 FPGA I/O; HyperRAM fallback recorded in SPEC.md §4.4 if pins get tight; checked at FPGA selection
- [affects] capture.buffer_MB affects power.vbus_current_mA: no change needed: SDRAM 100-250 mW already included in SPEC.md §3.1 estimate, total within 450 mA budget
- [affects] data.raw_rate_MBps affects usb.throughput_MBps: changed: SPEC.md §3/§4.3 set capture-to-buffer as guaranteed mode because 40 MB/s raw >= practical HS bulk throughput
- [affects] data.raw_rate_MBps affects FPGA capture logic: no change needed: 40 MB/s write path carried in SPEC.md §3; logic not yet designed
- [affects] data.raw_rate_MBps affects buffer memory selection: no change needed: checked — SDR SDRAM ~200 MB/s at 100 MHz is 5x the 40 MB/s write rate (SPEC.md §4.4)
- [affects] data.raw_rate_MBps affects USB bridge selection: no change needed: FT232H sync FIFO (~40 MB/s) recommended in SPEC.md §4.6; readout need not match raw rate due to buffering
- [affects] usb.throughput_MBps affects USB bridge selection: no change needed: FT232H sync FIFO meets >=30 MB/s readout target (SPEC.md §4.6); verified at part selection
- [affects] usb.throughput_MBps affects FPGA capture logic: no change needed: FIFO readout interface noted in SPEC.md §4.7; logic not yet designed
- [affects] usb.throughput_MBps affects capture architecture: changed: hybrid architecture with buffered capture guaranteed recorded in SPEC.md §4.3 and DECISIONS.md
- [affects] usb.throughput_MBps affects host readout protocol: no change needed: host software out of scope for hardware (SPEC.md §5); arm/capture/readout command set noted
- [affects] power.vbus_voltage_V affects input power path / load switch: no change needed: not yet designed; 4.4-5.25 V operating range carried in SPEC.md §3
- [affects] power.vbus_voltage_V affects bipolar rail generation: no change needed: not yet designed; converter must start from 4.4 V min (SPEC.md §3)
- [affects] power.vbus_voltage_V affects digital rail regulators: no change needed: not yet designed; LDO dropout from 4.4 V checked at part selection
- [affects] power.vbus_voltage_V affects USB connector / power source: no change needed: USB-C 5 V sink (SPEC.md §4.5) supplies within this range
- [affects] power.vbus_current_mA affects ADC selection: no change needed: ADC 100-250 mW budgeted in SPEC.md §3.1; verified at part selection
- [affects] power.vbus_current_mA affects front-end op amp selection: no change needed: 200-350 mW budgeted in SPEC.md §3.1; verified at part selection
- [affects] power.vbus_current_mA affects FPGA selection: no change needed: 150-400 mW budgeted in SPEC.md §3.1; verified at part selection
- [affects] power.vbus_current_mA affects buffer memory selection: no change needed: 100-250 mW budgeted in SPEC.md §3.1
- [affects] power.vbus_current_mA affects USB bridge selection: no change needed: 150-300 mW budgeted in SPEC.md §3.1
- [affects] power.vbus_current_mA affects bipolar rail generation: no change needed: ~85% efficiency loss included in SPEC.md §3.1 total
- [affects] power.vbus_current_mA affects digital rail regulators: no change needed: losses included in SPEC.md §3.1; LDO vs buck chosen at part selection to hold 450 mA
- [affects] power.vbus_current_mA affects USB connector / power source: changed: USB-C recommended (SPEC.md §4.5) as headroom while design stays within 450 mA
- [affects] power.preconfig_current_mA affects USB bridge selection: no change needed: FT232H alone must be < 100 mA; verified at part selection (SPEC.md §6)
- [affects] power.preconfig_current_mA affects input power path / load switch: no change needed: gating requirement stated in SPEC.md §3/§6; not yet designed
- [affects] power.preconfig_current_mA affects power sequencing / enable logic: no change needed: sequence (bridge only, then enable rails after configuration) listed as open item in SPEC.md §6
- [affects] power.preconfig_current_mA affects bipolar rail generation: no change needed: must have enable pin, held off pre-configuration (SPEC.md §6)
- [affects] power.preconfig_current_mA affects digital rail regulators: no change needed: gated regulators need enable pins; checked at part selection
- [affects] power.suspend_current_mA affects USB bridge selection: no change needed: FT232H suspend current flagged for verification in SPEC.md §4.6/§6
- [affects] power.suspend_current_mA affects input power path / load switch: no change needed: load-switch off-leakage checked at part selection
- [affects] power.suspend_current_mA affects power sequencing / enable logic: no change needed: rails must be disabled in suspend (SPEC.md §3); not yet designed
- [affects] power.suspend_current_mA affects digital rail regulators: no change needed: always-on regulator Iq checked at part selection
- [affects] power.suspend_current_mA affects USB connector / power source: no change needed: 5.1 kOhm Rd on CC draws no VBUS current; no PD controller (SPEC.md §4.5)
- [affects] power.vbus_capacitance_uF affects input power path / load switch: no change needed: soft-start switch for bulk caps required by SPEC.md §3; not yet designed
- [affects] power.vbus_capacitance_uF affects bipolar rail generation: no change needed: input caps go behind load switch; checked in power-design stage
- [affects] power.vbus_capacitance_uF affects digital rail regulators: no change needed: input caps go behind load switch; checked in power-design stage
- [affects] power.vbus_capacitance_uF affects USB connector / power source: no change needed: <=10 uF directly at connector carried in SPEC.md §3
- [affects] clock.jitter_ps_rms affects clock oscillator: no change needed: <=5 ps rms carried in SPEC.md §3/§6 as oscillator selection criterion
- [affects] clock.jitter_ps_rms affects ADC selection: no change needed: ADC aperture jitter must fit within the budget; checked at part selection
- [affects] clock.jitter_ps_rms affects FPGA capture logic: no change needed: ADC clock must come from the oscillator directly, not FPGA PLL/fabric; noted for design stage
- [affects] input.impedance affects front-end attenuator/buffer: no change needed: 1 MOhm || ~20 pF carried in SPEC.md §3/§4.2; not yet designed
- [affects] input.impedance affects front-end op amp selection: no change needed: requires FET/CMOS-input buffer with low Ib; checked at part selection
- [affects] input.impedance affects input.overvoltage_V: no change needed: checked consistent — high-impedance divider limits fault current at ±30 V to ~30 uA
- [affects] input.overvoltage_V affects front-end attenuator/buffer: no change needed: attenuator resistor voltage rating checked in front-end design
- [affects] input.overvoltage_V affects front-end op amp selection: no change needed: clamps plus op-amp input current limit checked at part selection
- [affects] input.overvoltage_V affects input protection clamps: no change needed: low-leakage, low-capacitance clamps required (SPEC.md §3); not yet designed
- [affects] analog.bandwidth_MHz affects front-end attenuator/buffer: no change needed: >=3 MHz -3 dB carried in SPEC.md §3
- [affects] analog.bandwidth_MHz affects front-end op amp selection: no change needed: GBW/slew for ±full scale at 3 MHz checked at part selection
- [affects] analog.bandwidth_MHz affects anti-alias filter: no change needed: >=40 dB at 7.5 MHz requirement in SPEC.md §3; filter designed later
- [affects] analog.bandwidth_MHz affects ADC input driver: no change needed: driver bandwidth/settling checked in front-end design
- [affects] analog.enob_bits affects ADC selection: no change needed: ADC datasheet ENOB must exceed 10.5 with margin; checked at part selection
- [affects] analog.enob_bits affects front-end op amp selection: no change needed: noise/distortion budget checked at part selection
- [affects] analog.enob_bits affects ADC input driver: no change needed: driver THD/noise checked at part selection
- [affects] analog.enob_bits affects clock oscillator: no change needed: 5 ps jitter budget already sized for SNR >= 74 dB at 5 MHz
- [affects] analog.enob_bits affects ADC reference: no change needed: reference noise checked at part selection
- [affects] analog.dc_accuracy affects front-end attenuator/buffer: no change needed: resistor tolerance (<=0.1%) and op-amp offset checked in front-end design
- [affects] analog.dc_accuracy affects ADC reference: no change needed: reference initial accuracy checked at part selection
- [affects] analog.dc_accuracy affects ADC input driver: no change needed: driver offset checked at part selection
- [affects] analog.dc_accuracy affects calibration storage: no change needed: EEPROM/config-flash storage noted in SPEC.md §5; chosen later
