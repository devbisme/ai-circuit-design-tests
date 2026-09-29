# SPEC — `dual_adc_usb`

Dual-channel, 12-bit, 10 MSPS USB oscilloscope-style acquisition board.

- **Status:** requirements captured, awaiting user approval
- **Date:** 2026-09-06
- **Source prompt:** `dual-adc-prompt.txt`
- **Requirements basis:** 9-question interview, Q1–Q9, all answers recorded below
- **Deliverable scope:** SKiDL source + ERC pass + KiCad netlist + BOM + **draft iCE40 gateware**. PCB layout is out of scope (user's own work in KiCad).

---

## 1. Functional

### 1.1 Acquisition

| Parameter | Value | Source |
|---|---|---|
| Channels | 2, simultaneous | prompt |
| Full-scale input range | ±10 V **at the BNC** (1× probe / direct coax) | Q2 |
| Resolution | 12 bit | prompt |
| Delivered sample rate | 10 MSPS/channel | prompt |
| **ADC clock rate** | **40 MSPS/channel (4× oversampling)** | Q3 |
| Decimation | 4:1 in gateware (CIC or short FIR), ahead of the SRAM | Q3 |
| Usable analog bandwidth | 3 MHz flat (−0.5 dB), −3 dB at ~4 MHz | Q3 |
| Alias rejection | −74 dB (full 12-bit) | Q3 |
| Input ranges | Single fixed range; no switchable attenuation in rev A | Q2 |
| Coupling | DC only; no AC coupling path, no series cap, no relay | Q2 |

### 1.2 Capture model — buffered burst (not continuous streaming)

Rejected at Q1: continuous streaming. 2 ch × 10 MSPS × 12 bit = 240 Mbit/s = 30 MB/s packed, against
~35–42 MB/s practical USB 2.0 high-speed bulk throughput. No headroom, and overrun is data loss rather
than slowdown.

| Parameter | Value |
|---|---|
| Buffer type | Async or pseudo-SRAM (no refresh, no DDR training) |
| Depth | ≥1 MS/channel = 100 ms at 10 MSPS |
| Organization | Unpacked 16-bit words; 2 M × 16 (4 MB) device holds exactly 1 MS/ch × 2 ch |
| Bit packing | Not in the capture path. Optional on the USB drain side only. |
| Drain time | 4 MB at ~20–40 MB/s ≈ 100–200 ms |

**Locked direction, not just a number:** async/pseudo-SRAM in the low-complexity class. If sourcing finds a
better-stocked alternative *in that same class*, flag it to the user. Do not silently migrate to SDRAM.

### 1.3 Trigger (Q7)

- Implemented **digitally in the FPGA** against the decimated sample stream. No analog comparator tap on the
  front end — nothing may load the 1 MΩ ∥ 20 pF node.
- Programmable level and slope, selectable on either channel.
- Programmable pre-trigger depth via circular addressing of the SRAM.
- Host force-trigger command.
- External trigger pin, bidirectional (trigger-in / trigger-out) for chaining two boards.
- **Accepted tradeoffs:** trigger granularity = one decimated sample = 100 ns. Trigger latency = decimation
  filter group delay — a fixed, calibratable offset. *The architecture doc must state the computed group-delay
  number once the filter is specified.*

### 1.4 Probe compensation output (Q6)

~1 kHz, ~1 Vpp square wave on a dedicated test terminal, generated from an FPGA pin through a resistor
divider. Required: the 1 MΩ ∥ 20 pF input exists so that standard 10× passive probes can be compensated,
and those probes cannot be adjusted without a compensation signal.

---

## 2. Analog front end

Per channel, in order:

1. BNC input, 1 MΩ ∥ ~15–20 pF, DC-coupled
2. Overvoltage protection clamps (must survive and accurately divide a real ±10 V swing at the connector)
3. Compensated 10:1 attenuator, **0.1% thin-film resistors**, preserving 1 MΩ ∥ 15–20 pF so 10× passive
   probes remain compensatable
4. High-Z JFET/CMOS-input buffer, >10 MHz bandwidth
5. 4th-order anti-alias low-pass at ~4 MHz (gentle filter; the 40 MSPS oversampling is what buys the −74 dB)
6. ADC driver / single-ended-to-differential stage as required by the selected ADC

### 2.1 Reference and accuracy (Q6)

| Item | Requirement |
|---|---|
| Voltage reference | **External precision reference**, ~2.5 V, 0.1% / 10 ppm class. **Not** the ADC internal reference. |
| Attenuator resistors | 0.1% thin-film |
| Calibration | One-time **factory per-board calibration**, constants applied host-side |
| Gain error, post-cal | ±0.5% |
| Offset error, post-cal | ±0.2% FS |
| Drift | ~25 ppm/°C |
| Constant storage | **FT2232H EEPROM user area** — readable over channel B before the FPGA is configured, so the host reads cal data with no gateware and no loaded bitstream |

**Explicitly rejected:** ADC internal reference (2–4% absolute); on-board self-calibration analog switch
(charge injection, R_on nonlinearity, added capacitance in the 1 MΩ / 3 MHz front end); 0.05% resistors as a
substitute for the calibration step. **Nothing extra may be placed in series with the signal path.**

### 2.2 Sample clock (Q7)

| Item | Requirement |
|---|---|
| Source | Fixed 40 MHz LVCMOS XO, ≤1 ps RMS integrated phase jitter class |
| Routing | Drives the ADC encode input directly, shortest possible trace, own filtered supply |
| FPGA role | **Consumes** the clock. Never synthesizes it. |
| Variable rate | None in hardware. Lower effective rates come from larger gateware decimation ratios only. |

**Aperture jitter budget:** for −74 dB SNR at a 3 MHz full-scale input,
t_j ≤ 1/(2π · 3 MHz · 10^(−74/20)) = **10.6 ps RMS**. Target ≤5 ps RMS for margin.
This budget is what the entire 12-bit claim rests on.

**Rejected:** iCE40 PLL-derived sample clock (jitter an order of magnitude too high); Si5351-class programmable
generator (hundreds of ps).

---

## 3. Power

Bus-powered from USB only. Budget: 500 mA at 5 V = **2.5 W**.

### 3.1 Tree (Q5)

```
USB 5V ──TVS──ferrite──bulk──┬── BUCK ──── 3V3 digital ── LDO ── 1V2 FPGA core
                             ├── ferrite ── LDO ─────── 3V3 AVDD (ADC, isolated from digital 3V3)
                             └── LM27762 (or equiv. charge pump w/ integrated ± LDO) ── ±4.00 V analog
```

- 3.3 V digital is a **buck**, not an LDO: an LDO at ~250 mA burns 0.43 W, 17% of the whole budget.
  The user accepts the switcher near the analog section and the layout discipline it requires.
- ADC AVDD is a **separate** LDO off the 5 V rail through a ferrite. Not shared with digital 3.3 V.
- **±4.00 V** for the front-end amplifiers, not a single-supply front end: keeps buffer common-mode away
  from the rails, removes level-shift gain/offset error terms, and gives graceful overdrive recovery.

  > **Revised 2026-09-06 at the architecture gate — supersedes the original ±5 V.** Regulated ±5.0 V is not
  > achievable from a 5 V USB bus with an LM27762-class part: the positive LDO's 45 mV dropout means +5.00 V
  > needs ≥5.05 V in, against a 4.75 V minimum VBUS (worse after the TVS/ferrite/soft-start FET), and the
  > negative rail maxes at ≈ −4.67 V. **Rails are ±4.00 V** (V_FB+ = 1.200 V, V_FB− = −1.220 V), in
  > regulation down to V_IN ≈ 4.1 V. The signal at the buffer is ±1 V, so 3 V of headroom remains and all
  > three benefits above are fully retained — the OPA1656 output stage binds long before the rails do.
  > TPS65133 would give literal ±5 V but loses the integrated post-LDOs; **rejected by the user** as a worse
  > trade on a 12-bit board. See `architecture/ic_selection.md` §4.4.

### 3.2 Estimated budget

| Block | Estimate |
|---|---|
| Dual 40 MSPS ADC | ~350 mW |
| iCE40HX | ~150 mW |
| FT2232H | ~130 mW |
| SRAM | ~100 mW |
| Analog front end (4 amps) | ~200 mW |
| Conversion losses, misc | ~250 mW |
| **Total** | **~1.2–1.6 W of 2.5 W** |

Power is a first-class sourcing criterion, especially for the ADC.

### 3.3 USB enumeration (Q5)

Declare 500 mA in the descriptor and power up immediately, with inrush limiting. **No** post-enumeration load
switch. The user accepts the technical non-compliance during the enumeration window as normal instrument
practice.

### 3.4 Power-related PCB constraints (carry into architecture and layout)

- Charge-pump switching residue (~600 kHz–1 MHz) must be kept off AVDD and the front end — explicit
  ferrite/LDO isolation. The 4 MHz anti-alias filter provides additional attenuation.
- Buck switching frequency and a layout keep-out around it are **explicit PCB constraints**. The buck is the
  principal risk introduced into a 12-bit precision board.

---

## 4. Interface

### 4.1 Host interface (Q4)

| Item | Choice |
|---|---|
| Bridge | **FTDI FT2232H** |
| Channel A | Synchronous 245 FIFO mode — sample drain |
| Channel B | MPSSE — FPGA bitstream load and slow control |
| Connector | **USB-C receptacle wired as a USB 2.0 device**: D+/D− only, dual 5.1 kΩ CC pulldowns to present as a sink |

Because capture is buffered burst, USB throughput is **not** a hard requirement — the bridge was chosen for
low integration cost, not peak bandwidth. **Rejected:** FX2LP (inherits an 8051 firmware image + I²C EEPROM),
MachXO2 + FT232H, ECP5/Artix-7.

### 4.2 Digital device (Q4)

| Item | Choice |
|---|---|
| FPGA | Lattice **iCE40HX4K / HX8K, TQFP-144** (~107 I/O) |
| Toolchain | **Yosys / nextpnr / icestorm — HARD, BINDING CONSTRAINT** |
| Configuration | **Both paths populated**: ~$0.20 SPI config flash for standalone self-boot, **plus** FT2232H MPSSE override for development and field updates. Include the mode strap. |

> **Binding constraint:** any FPGA substitution proposed at sourcing must stay inside the iCE40 family.
> MachXO2, Efinix, and anything requiring vendor-only tools are eliminated and must not be reintroduced as a
> silent substitute.

**I/O budget (drove the TQ144 choice):** 24 ADC data + 21 SRAM address + 16 SRAM data + 3 SRAM control +
~12 USB FIFO + clocks ≈ **80 I/O**.

### 4.3 Clock domains (Q7)

1. 40 MHz sample clock (from the XO)
2. 60 MHz FT2232H sync-FIFO clock output
3. 12 MHz FT2232H crystal — its own, not shared

Capture-to-USB domain crossing is handled through the SRAM burst boundary.

### 4.4 External trigger I/O (Q7)

Protected 3.3 V header pin — series resistor and clamp — configurable as trigger-in or trigger-out so two
boards can be chained. Not a third BNC.

---

## 5. Physical

| Item | Value |
|---|---|
| Form factor | Bare board, ~100 × 80 mm, mounting holes. No enclosure constraint for rev A. |
| Stackup | **4-layer**: signal / solid ground / power / signal |
| Ground | Analog section over an uninterrupted ground pour |
| Buck placement | Corner, with keep-out (§3.4) |
| Connector placement | BNCs vertical PCB-mount on one edge; USB-C on the opposite edge — physically separating the ±10 V analog inputs from the switching and USB sections |
| Assembly | All-SMD on the top side for JLCPCB assembly. Bottom side kept free of components if possible. |
| Through-hole parts | BNCs, trigger header, probe-comp terminal, mode strap — hand-soldered at prototype quantity. Not paying for JLCPCB TH assembly. |
| Operating temperature | 0–50 °C commercial (consistent with the 25 ppm/°C cal target) |

SMD BNCs were rejected as mechanically weak on a connector that gets tugged by probe leads.
2-layer was rejected outright: 12-bit performance is not defensible with a buck converter on 2 layers.
6-layer rejected as unnecessary at 3 MHz given a disciplined 4-layer floorplan.

---

## 6. Production

| Item | Value |
|---|---|
| Rev A quantity | **5 boards**, optimized as a working prototype |
| Volume readiness | Not required. User accepts that the rev A BOM will not scale to volume without re-sourcing. |
| BOM cost | ~$70–100 single-quantity is **acceptable**. No ceiling; no spec compromises on cost grounds. Stay sensible, do not gold-plate. |
| Fab/assembly | JLCPCB PCB + top-side SMD assembly; TH parts hand-soldered |

### 6.1 Sourcing policy (Q9) — modifies the default pipeline rule

- **Passives and jellybeans:** hold JLCPCB Basic/Preferred discipline, stock > 100.
- **The four critical ICs — ADC, FPGA, SRAM, FT2232H:** Extended-tier or off-JLC
  (Digi-Key / Mouser, hand-placed) sourcing is **permitted**.
- **The tier rule must not force a substitution that breaks the specs settled in Q1–Q8.**
- Any FPGA substitute remains bound by the open-toolchain constraint (§4.2).

### 6.2 Calibration in the production flow

Per-board calibration is now part of the build process, and the host-side software contract includes reading
gain/offset constants from the FTDI EEPROM user area.

---

## 7. Deliverables

1. SKiDL source (`circuits/dual_adc_usb/`)
2. ERC pass — 0 errors
3. KiCad netlist (`outputs/*.net`)
4. BOM (`outputs/*.xml` / CSV)
5. **Draft iCE40 gateware** (additional deliverable, Q9), covering:
   - 4:1 decimation, with CIC droop compensation per §8.1
   - SRAM burst controller with circular pre-trigger addressing
   - Digital trigger: level / slope / either channel, host force-trigger, bidirectional external trigger pin
   - FT2232H synchronous-FIFO drain path

Gateware is produced **after** the netlist/BOM export stage completes. It must not disturb pipeline stage
order. PCB layout remains the user's own work in KiCad.

---

## 8. Known engineering tasks (not risks)

### 8.1 CIC passband droop
If 3 MHz flatness is specified tightly, a short compensating FIR may be required after the CIC decimator.
Recorded as a gateware task.

### 8.2 Trigger offset characterization
The decimation filter's group delay must be computed and documented as the calibratable trigger offset.

---

## 9. Risks and open technical concerns

| # | Risk | Severity | Notes |
|---|---|---|---|
| R1 | **2 M×16 async SRAM availability** | High | The async SRAM market is shrinking. This is the most likely sourcing failure. Substitution must stay in the low-complexity class (no refresh, no training); escalate to the user, do not silently move to SDRAM. |
| R2 | **iCE40HX4K-TQ144 and FT2232H stock/tier** | Medium | Both plausibly Extended-tier. FPGA substitutes are constrained to the iCE40 family by the open-toolchain requirement. |
| R3 | **40 MHz XO phase jitter** | Medium | "≤1 ps RMS" is a part *class*, not a confirmed part number. Its actual spec and availability must be verified at sourcing. If nothing in that class is available, bring the substitution **and its jitter number** back to the user — the 12-bit claim rests on this budget. |
| R4 | **Dual 12-bit ≥40 MSPS ADC within the power budget** | Medium | ~350 mW assumed. Power is a first-class selection criterion alongside interface type (parallel CMOS preferred, given the iCE40's lack of usable LVDS SERDES). |
| R5 | **Front-end thermal noise partly cancels the oversampling gain** | Medium | The 1 MΩ requirement fixes the attenuator's Thevenin source at ~90 kΩ → ~38.5 nV/√Hz → ~78 µV RMS over a 4 MHz noise bandwidth, against ~141 µV of ideal 12-bit quantization noise at 2 Vpp. After 4× decimation drops quantization noise ~6 dB, the resistor noise becomes the co-dominant term. Net effect: the oversampling gain is roughly halved, and the design lands near 12 ENOB rather than comfortably above it — *before* the real ADC's own SNR (typically ~70 dB) is included. **This is inherent to the 1 MΩ ∥ 20 pF requirement and cannot be designed away without changing it.** Numbers to be re-derived against the actual selected ADC. |
| R6 | **Buck switcher on a 12-bit board** | Medium | Accepted deliberately (§3.2 power budget). Mitigation is layout discipline, keep-out, and rail isolation — all specified, none yet verified. |

---

## 10. Assumptions requiring user confirmation at the approval gate

- **A1 — Regulatory: none for rev A. USER-CONFIRMED (2026-09-06 approval gate).** The board is treated as a
  bench prototype, not a product. No compliance work in rev A. **Note retained:** if the board is ever sold,
  FCC Part 15B / CE EMC becomes a real design input, and a bus-powered instrument carrying a buck converter
  and a 40 MHz clock is not automatically compliant.

## 11. Required architecture work items (from the SPEC approval gate)

- **W1 — Full input-referred noise budget (from R5).** The user did not accept R5 as a logged risk and did not
  reopen the 1 MΩ requirement; they required it be re-examined at architecture. Deliver:
  1. A complete input-referred noise budget: attenuator Thevenin resistance, front-end buffer op-amp voltage
     **and** current noise, anti-alias filter contribution, the candidate ADC's own SNR/ENOB from its
     datasheet, and the effect of 4:1 decimation on **each** term separately.
  2. An **actual expected ENOB number**, not an estimate, with an explicit statement of which term dominates.
  3. The analysis must be run against the **real candidate ADC and op-amp**. If the number depends on a part
     not yet sourced, flag that dependency explicitly for revisit after part sourcing.
  4. **The 1 MΩ ∥ 20 pF requirement stays fixed.** It is not to be traded away to improve the number — report
     the consequence instead. If the honest number lands materially below 12 ENOB, that is a **finding to
     bring to the user**, not grounds to silently adjust the spec.

  R5 arithmetic independently verified at the gate: 90 kΩ Thevenin, 38.6 nV/√Hz, ~77 µV over 4 MHz, versus
  141 µV quantization at 2 Vpp and ~70 µV after decimation. The effect is real; model it properly.
