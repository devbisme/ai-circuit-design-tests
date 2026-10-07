# Executive Summary — dual-adc-usb-1 (copperhead)

**Result:** an **incomplete** design. The spec, architecture and BOM are done for a 2-channel board that samples ±10 V inputs at 12 bits and 10 MSa/s, stores ≥ 0.1 s of samples per channel (≈ 0.84 s), and connects to the host over USB-C (USB 2.0 High-Speed data and power). **No schematic exists.** The run stopped in stage 4 of 8.

- 132 BOM rows (24 ICs, 52 C, 36 R, 7 L, 6 D, 4 J, 2 Q, 1 Y). `board.kicad_sch` is an empty scaffold; ERC/DRC pass only because there is nothing to check.
- Of the 37 active/connector rows, 14 have pins checked against an installed symbol (`SYM✓`); 23 are `SYM?`.
- Every MPN is marked **UNVERIFIED**. No datasheet was read at any stage.
- **Not drawn, laid out or built.** No FPGA logic or host software.
- Equivalent API cost: ≈ $30.5 for copperhead's own Claude Code sessions (208 single-turn sessions), plus ≈ $3 for the driving session. See `transcripts/INDEX.md`. About 69 % (≈ $21) went to the 7 of 10 runs that did not finish a stage.
- Wall time: about 10 h across three 5-hour usage windows; the usage limit stopped the run 3 times.

**Method:** copperhead v0.11.0, `copperhead create --brief dual-adc-prompt.txt`, `claude-code` backend.

- 8 fixed stages: spec-seed, architecture, part-selection, schematic, layout-draft, outputs, firmware, devplan. Each stage is a tool loop with a 40-turn cap. It commits to git only when the stage's completion check passes.
- State passes between stages only through `docs/` (SPEC, SUBSYSTEMS, BOM, DECISIONS, CHANGELOG), `.copperhead/constraints.json` and OpenSpec change folders.
- After a failure, a recovery call decides whether to retry (up to 3 attempts) or stop for a human. The failed work is kept as a git stash.
- The model has only copperhead's tools; the Claude Code web, file and shell tools are disabled. Parts come from model memory and must be in the **stock KiCad symbol libraries**; user `sym-lib-table` libraries are not searched.
- The prompt said not to pause for input. At every decision the options were listed and the recommended one chosen and recorded. Copperhead still stopped once for a user decision (§4).

---

## 1. Requirements (spec-seed, 1 run)
- Wrote `docs/SPEC.md` from the prompt:
  - 8 requirements from the brief (F1–F8) and 2 **ASSUMED** (F9 trigger, F10 decimation). Simultaneous sampling and DC coupling are also **ASSUMED**.
  - 16 numeric budgets in `.copperhead/constraints.json`. **ASSUMED** ones include 1 MΩ ∥ 20 pF input, ±30 V survival, −3 dB ≥ 3 MHz with ≥ 40 dB at 7.5 MHz, ENOB ≥ 10.5, and DC accuracy.
  - USB limits taken from the standard: ≤ 450 mA steady (90 % of 500 mA), ≤ 100 mA before configuration, ≤ 2.5 mA in suspend, ≤ 10 µF on VBUS.
- Applied the user's power rule: the estimate was 170–410 mA at 4.4 V, close to the 500 mA limit, so **USB-C** was chosen. The board is still budgeted at ≤ 450 mA so it works on any USB 2.0 host.
- Defaults for the rest: no isolation, 0–40 °C, ≤ 100 × 80 mm 4-layer board.
- Commit `6fbce13`.

## 2. Architecture (1 run)

### Functional blocks
| # | Block | Function |
|---|---|---|
| 1 | USB-C input | USB-C receptacle (5.1 kΩ Rd, no PD), ESD/TVS on VBUS and D± |
| 2 | Always-on power | 3V3_AON LDO for only the FT232H, its EEPROM and the bus-switch VCC |
| 3 | Gated power | Soft-start load switch (FT232H PWREN_N) → VBUS_SW → 3.3 V buck, 1.2 V / 1.8 V LDOs, low-noise 3.3 V clock LDO |
| 4 | Bipolar analog power | ±6 V boost/inverter → ±5 V analog LDOs, enabled by the FPGA (AFE_EN) |
| 5 | Analog front end ×2 | BNC → 1 MΩ ÷5 divider → clamps → FET buffer → FDA → 5th-order LC elliptic filter |
| 6 | ADC | Dual simultaneous-sampling 12-bit ADC |
| 7 | Clock | 10 MHz XO → 1:2 fanout: ADC clock direct, FPGA clock to its PLL |
| 8 | FPGA | Capture, trigger, decimation, SDRAM control, FIFO interface; no MCU |
| 9 | Buffer memory | 256 Mbit ×16 SDR SDRAM |
| 10 | USB bridge | FT232H in synchronous 245 FIFO mode, through a bus switch |
| 11 | Config/cal | SPI config flash + programming header; cal constants in the FT232H's 93LC56 |

### Criteria and decisions by block

**Power**
- *Criteria:* ≤ 61 mA before configuration, ≤ 2.5 mA in suspend, ≤ 10 µF ungated, ≤ 450 mA steady at 4.4 V.
- *Decisions:*
  - **Two domains.** Only the USB bridge, its EEPROM and the bus switch are always on. Everything else sits behind a load switch that PWREN_N turns on after configuration. This is what makes ≈ 61 mA before configuration and ≤ 1.6 mA in suspend achievable.
  - A bus switch isolates the FIFO lines so the powered FT232H cannot back-power the FPGA.
  - Steady state ≈ 342 mA at 4.4 V (24 % margin).

**Analog front end, ×2**
- *Criteria:* ±10 V full scale; 1 MΩ for scope probes; ±30 V survival; ≥ 40 dB at 7.5 MHz; ENOB ≥ 10.5.
- *Decisions:*
  - **Compensated ÷5 divider** (800 k ∥ 25 p over 200 k ∥ ~100 p, 0.1 %). It brings ±10 V within ±5 V op-amp rails without high-voltage rails. Full scale ±10.53 V (95 % used at ±10 V).
  - **BAV199** clamps at the divider tap; a ±30 V fault gives about 31–37 µA. No TVS at the BNC (footprint only, DNP).
  - **OPA810** FET-input buffer (G = +1), then a **THS4551** FDA (G = 0.475, VOCM from the ADC).
  - **5th-order elliptic LC filter**, sized for ≥ 50 dB nominal so tolerances still give ≥ 40 dB. Butterworth (≈ 33 dB) and 0.1 dB Chebyshev (42.5 dB) lost on margin.
  - Rejected: a high-voltage unity buffer on ±12 V rails; a programmable-gain front end.

**Clock**
- *Criteria:* ≤ 5 ps rms at the ADC clock pin.
- *Decisions:* the XO drives a fanout buffer, so the ADC clock never passes through FPGA fabric or the PLL. Allocation: XO 1.0, fanout 0.3, aperture 0.5, routing 1.0 → ≈ 1.5 ps RSS.

**Capture, memory and USB**
- *Criteria:* ≥ 4 MB buffer; 30–40 MB/s raw data against ≈ 35–42 MB/s practical USB 2.0 bulk.
- *Decisions:*
  - **Capture to buffer, then read out** as the guaranteed mode. Best-effort streaming is extra.
  - **SDR SDRAM, 256 Mbit ×16** (≈ 0.84 s, 8× the requirement). Rejected: BRAM (too small), DDR3 (layout cost); HyperRAM is the fallback if pins run short.
  - **FT232H sync FIFO.** No bridge firmware and mature drivers. FX2LP is the fallback if custom descriptors are needed. MPSSE is not used for flash programming because ADBUS carries the FIFO.

**Calibration**
- Per-channel gain/offset constants live in the FT232H's 93LC56 EEPROM user area. The host can read them before the FPGA is powered, with no added part or suspend load.

- Commit `207d7c6`.

## 3. Part selection (4 runs; 1 completed)
- Runs: ran out of turns (40/40) → stopped by the usage limit → a cached replay of the first failure → completed on the retry. Commit `359b20e`.
- Selected parts, all **UNVERIFIED**:

| Function | Part |
|---|---|
| ADC | **LTC2290** |
| FPGA | **iCE40HX4K-TQ144** |
| SDRAM | **MT48LC16M16A2P** |
| USB bridge + EEPROM | **FT232H** + 93LC56B |
| Bus switch | 2 × 74CBTLV3861 |
| Load switch | TPS22917 |
| Regulators | MCP1700 (AON, 1.2 V, 1.8 V); TLV62084 buck; TPS7A2033 (ADC, clock); TPS65131 (±6 V); TPS7A4901 / TPS7A3001 (±5 V) |
| Front end | OPA810, THS4551, BAV199 |
| USB-C | USB4105 |
| Config flash | W25Q32JV |

- **The symbol-library limit drove the choices.**
  - The architecture's AD9238-class ADC has no stock symbol. Every other installed dual-channel candidate was 8-bit or ≤ 1 MSPS, which left the LTC2290.
  - The LTC2290 runs from 3.3 V, so `1V8_A` became `3V3_ADC`.
  - No 16-bit CBT bus switch symbol exists, so two 10-bit parts are used.
- Power budget recomputed with these parts: ≈ 1.43 mA suspend, ≈ 61 mA before configuration, ≈ 6.6 µF ungated, ≈ 336 mA steady. All pass.

## 4. User decision: DC accuracy (main thread)
- Copperhead had **assumed** a limit of ≤ 1 % gain and ±20 mV offset at the input, uncalibrated. From memory, the LTC2290 is ±12 mV offset (≈ 126 mV at the input) and ≈ 1.5 % gain error. Copperhead flagged its own assumption as a BLOCKER and refused to start the schematic.
- The user chose **option (a)**: the limit applies **after calibration**. Uncalibrated limits were relaxed to ≤ 3 % and ±150 mV at the input, to size the calibration range. This was recorded in DECISIONS, SPEC §3/§6, BOM and `constraints.json`. The rejected option (b) was to install an ADC library with a better part.
- These edits are **uncommitted**.

## 5. Schematic (4 runs; none completed)
- Runs: refused (the §4 blocker) → stopped by the usage limit at turn 34 → stopped by the usage limit at turn 19 after reaching `draft_schematic`.
- Work done before stopping, **held only in git stashes** and not in the working tree:
  - Pins confirmed for the LTC2290, 93LC56B and MCP1700 family.
  - Symbol substitutions:
    - TPS7A20 moved to the X2SON-4 package (the only installed symbol).
    - TPS7A49 + TPS7A30 replaced by one **TPS7A39** dual ±LDO.
    - LMK1C1102 fanout replaced by a **74LVC2G34**, whose additive jitter is not specified.
  - A first `schematic.intent.json` was sent to the drafting engine. Copperhead noted that some of its lib_ids and pins were guesses.
- The pre-schematic symbol check also found wrong symbol name-matches for the BNCs, BSS138, USBLC6, LMK1C1102 (matched to `Motor:Fan`) and OPA810 (SOIC instead of SOT-23-5).

## 6–8. Layout draft, outputs, firmware, devplan
- Not started.

---

## Open risks
- **No schematic.** Everything past the BOM is a plan. To resume: `copperhead create --brief dual-adc-prompt.txt --model claude-code`. Apply or drop the stashed stage-4 BOM edits first.
- **Nothing checked against a datasheet.** Copperhead has no web or datasheet access. LTC2290 offset/gain, FT232H suspend current (largest item in the 1.75 mA AON budget), SDRAM IDD and regulator Iq figures are all from model memory.
- **Clock jitter:** the 74LVC2G34 substitute has no jitter spec, against the 0.3 ps fanout allocation. ≈ 1.5 ps RSS leaves room, but it is not shown.
- **Bus-switch current:** 2 × ≤ 10 µA ICC uses exactly the 0.02 mA allocation, with no margin.
- **Library limits:** parts are restricted to stock KiCad symbols. Better ADC or clock-buffer choices need a custom library in a path set by `KICAD_SYMBOL_DIR`. That variable **replaces** the stock paths, so it must point at a directory holding both.
- **Docs drift:** SUBSYSTEMS §0/§2/§8 still show `1V8_A` and the AD9238-class ADC; BOM notes "SUBSYSTEMS update pending". SUBSYSTEMS §7.6 allocations now mean post-calibration residuals; that is recorded only in SPEC/DECISIONS.
- **Cost and throughput:** each turn is a new session that rewrites ≈ 22k tokens of prompt cache, so cache writes are ≈ 70 % of cost. At ≈ $10 per 5-hour window, the 4½ remaining stages will likely take several more windows on a subscription.
- **Git:** copperhead commits straight to `master` of the parent repo (3 commits). 5 failed-run stashes are in `git stash list`.
