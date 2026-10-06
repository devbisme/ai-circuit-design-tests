# SUBSYSTEMS — Architecture (stage 2)

Status: stage 2 (architecture). Derived from docs/SPEC.md; every number here is checked against the SPEC §3 budgets.
Parts named "candidate" are architecture-level examples only. Each one must be confirmed in the part-selection stage against the limits stated here, and must have an installed KiCad symbol.
Net names in `CODE` are the names later stages must use.

## 0. Block diagram (prose)

Power and data both enter through one **USB-C receptacle** (USB 2.0 HS data, 5.1 kΩ Rd sink, no PD).

**Always-on domain.** VBUS feeds one **always-on LDO** (`3V3_AON`). This rail powers only:
- the **FT232H USB bridge**
- its **93LC56 EEPROM**, which also holds the calibration constants
- the VCC pin of a **FIFO bus switch**

This is all that runs before USB configuration and during suspend.

**Gated domain.** VBUS also feeds a **soft-start load switch**. The FT232H `PWREN_N` pin turns it on after the host sets configuration, and it turns off again in suspend. The switched rail `VBUS_SW` feeds:
- a **3.3 V buck** (`3V3_D`), followed by LDOs for the FPGA core (`1V2_FPGA`) and the ADC (`1V8_A`, `1V8_D`)
- a **low-noise clock LDO** (`3V3_CLK`)
- a **±6 V boost/inverter**, followed by **±5 V analog LDOs** (`+5V_A`, `-5V_A`). The FPGA enables this pair (`AFE_EN`) only after the digital rails are good.

**Signal path.** Per channel:
1. BNC
2. Compensated 1 MΩ ÷5 divider
3. Low-leakage clamps
4. FET-input buffer
5. Fully-differential amplifier (FDA)
6. 5th-order LC anti-alias filter
7. One input of a **dual simultaneous-sampling 12-bit ADC**

**Clock.** A **10.000 MHz low-jitter XO** drives a **fanout buffer**. One output goes directly to the ADC clock pin. The other goes to the FPGA, whose PLL makes the 100 MHz SDRAM/logic clock. The ADC clock never passes through the FPGA.

**Capture and readout.** The **FPGA** (no MCU) takes both ADC words and handles triggering and decimation. It writes a circular capture buffer in a **256 Mbit ×16 SDR SDRAM**, and reads captures out to the host through the **FT232H synchronous 245 FIFO**. The FIFO is clocked by the FT232H's 60 MHz CLKOUT and passes through the bus switch.

**Indicators.** Three FPGA-driven LEDs.

**Configuration.** The FPGA configures itself from a SPI flash, which is programmed through a header.

```
USB-C ─┬─ 3V3_AON LDO ── FT232H ═FIFO═[bus switch]═ FPGA ═ SDRAM
       │                  └ 93LC56 (config + cal)     │  └ SPI config flash
       └─ load switch (PWREN_N) ── VBUS_SW            │
            ├─ buck 3V3_D ─┬─ LDO 1V2_FPGA            ├─ LEDs
            │              ├─ LDO 1V8_A / 1V8_D ──── ADC ◄── AA filter ◄ FDA ◄ buffer ◄ clamp ◄ ÷5 ◄ BNC (×2)
            ├─ LDO 3V3_CLK ── XO 10 MHz ── fanout ─┬─► ADC CLK
            │                                     └─► FPGA CLK
            └─ ±6 V boost/inverter (AFE_EN) ── LDO ±5V_A ── buffers, FDAs
```

## 1. Connectivity — USB-C (J1)

**Reasoning:** see SPEC §4.5.

**Key values:**
- **Receptacle:** USB-C, USB 2.0 only (16-pin class).
- **D+/D−:** A6/B6 tied and A7/B7 tied. Routed as a 90 Ω differential pair.
- **CC1 and CC2:** each has its own 5.1 kΩ Rd to GND. They must not be shared, so the board is recognised as a sink in either orientation. The Rd current comes from the source's Rp, not from VBUS, so it does not count against VBUS budgets.
- **D+/D− ESD:** low-capacitance array (≤1 pF/line, needed for HS eye margin).
- **VBUS TVS:** standoff ≥5.5 V, leakage ≤1 µA (counted in the suspend budget).
- **No USB-PD controller** (intentional absence, SPEC §4.5). Type-C Current advertisements are not read; the board is budgeted to ≤450 mA anyway.
- **Shield:** to GND through 1 MΩ ∥ 4.7 nF.

## 2. Power tree, gating and sequencing

### 2.1 Rails

| Net | Source | Feeds | Load allocation | Reasoning |
|-----|--------|-------|-----------------|-----------|
| `VBUS` | USB-C | 3V3_AON LDO, load switch | — | Only these two parts plus ESD/TVS sit on raw VBUS (capacitance budget) |
| `3V3_AON` | LDO from VBUS, Iq ≤50 µA, always on | FT232H (VCCIN/VCCIO), 93LC56, bus-switch VCC, `PWREN_N`/`BUS_OE_N` pull-ups | 61 mA | LDO, not buck: low Iq dominates the suspend budget, and 61 mA × (5.25−3.3) V = 0.12 W is acceptable |
| `VBUS_SW` | Load switch, enabled by `PWREN_N` (active low, default OFF via pull-up to 3V3_AON), rise time ≥3 ms, off-state leakage ≤1 µA | All gated converters | — | Puts all bulk capacitance and all non-USB load behind the switch (preconfig, suspend and capacitance budgets) |
| `3V3_D` | Buck from VBUS_SW, η ≥88 %, f_sw ≥1 MHz (SYNC-capable preferred) | FPGA 3.3 V banks, SDRAM, config flash, LEDs, and the 1V2/1V8 LDO inputs | 205 mA | The largest load, so it must be switched-mode |
| `1V2_FPGA` | LDO from 3V3_D | FPGA VCC and VCCPLL | 30 mA | Small current; an LDO keeps the PLL supply clean |
| `1V8_A` | Low-noise LDO from 3V3_D, PSRR ≥40 dB at f_sw | ADC AVDD | 60 mA | Kept separate from digital 1.8 V for ENOB |
| `1V8_D` | LDO from 3V3_D | ADC DRVDD, FPGA ADC-bank VCCIO | 15 mA | The ADC output level matches the FPGA bank directly, with no level shifters |
| `3V3_CLK` | Low-noise LDO from VBUS_SW, noise ≤10 µV rms | XO, fanout buffer | 15 mA | Supply noise on the XO turns into jitter (§6) |
| `+6V_RAW` / `-6V_RAW` | Boost + inverting converter from VBUS_SW, enabled by `AFE_EN`, η ≥75 %, f_sw ≥1 MHz, SYNC-capable preferred | ±5V_A LDOs | 20.5 / 15.5 mA | The bipolar front end needs ±5 V; 1 V of LDO headroom rejects switching ripple |
| `+5V_A` | LDO from +6V_RAW | 2× buffer, 2× FDA, misc | 20 mA | §7 |
| `-5V_A` | Negative LDO from -6V_RAW | 2× buffer, misc | 15 mA | §7 |

### 2.2 Steady-state VBUS current (worst case at VBUS = 4.4 V) — budget `power.vbus_current_mA` ≤ 450 mA

| Block | Calculation | VBUS mA |
|-------|-------------|---------|
| 3V3_AON (linear) | 60 FT232H + 1 EEPROM + 0.1 LDO Iq + bus switch | 61 |
| Load switch on-state Iq | | 0.05 |
| 3V3_D buck | 205 mA × 3.3 V / 0.88 / 4.4 V | 175 |
| 3V3_CLK (linear from VBUS_SW) | | 15 |
| ±6 V converter | (6 × 20.5 + 6 × 15.5) mW / 0.75 / 4.4 V | 66 |
| Contingency (pull-ups, reference, estimate error) | | 25 |
| **Total** | | **≈342 mA** (margin 108 mA, 24 %) ✓ |

3V3_D load breakdown:

| Load | mA |
|------|----|
| FPGA 3.3 V I/O | 25 |
| SDRAM, average at ~20 % bus utilisation with refresh | 70 |
| Flash | 2 |
| LEDs (3 × 1 mA) | 3 |
| 1V2_FPGA LDO input | 30 |
| 1V8_A LDO input | 60 |
| 1V8_D LDO input | 15 |
| **Total** | **205** |

The linear rails on 4.4 V are the worst case for switchers. LDO current does not depend on VBUS.

### 2.3 Pre-configuration VBUS current — budget `power.preconfig_current_mA` ≤ 100 mA

Only 3V3_AON is live (FT232H enumerating, EEPROM read), plus load-switch off-leakage: **≈61 mA**, margin 39 mA ✓.

This holds only if the FT232H operating current is ≤60 mA. The candidate datasheet typical is about 54 mA. **VERIFY** the maximum in part selection.

### 2.4 Suspend VBUS current — budget `power.suspend_current_mA` ≤ 2.5 mA

In suspend the FT232H drives `PWREN_N` high, so every gated rail is off.

| Item | Allocation |
|------|-----------|
| FT232H suspend current | ≤1.2 mA (**VERIFY** in part selection — SPEC §6 open item) |
| D+ 1.5 kΩ pull-up into host 15 kΩ (3.3 V / 16.5 kΩ) | 0.20 mA |
| 3V3_AON LDO Iq | ≤0.10 mA |
| Bus switch ICC (disabled) | ≤0.02 mA |
| 93LC56 standby | ≤0.01 mA |
| Load switch off-state + gated converter leakage | ≤0.01 mA |
| ESD/TVS/capacitor leakage | ≤0.05 mA |
| **Total allocated** | **≤1.6 mA** (architecture allocation cap 1.75 mA; margin ≥0.75 mA to 2.5 mA) ✓ |

Rules that keep this budget:
- **No LED on 3V3_AON** (intentional).
- No resistive divider or pull-down on 3V3_AON that conducts in suspend.
- `PWREN_N` and `BUS_OE_N` pull-ups sit at the same potential as their nodes in suspend, so they draw 0 µA.

### 2.5 VBUS capacitance — budget `power.vbus_capacitance_uF` ≤ 10 µF

All capacitance that is not behind the soft-start switch counts, including capacitance charged through the AON LDO:
- ≤2.2 µF directly on VBUS (AON LDO input + load-switch input).
- ≤6.8 µF total on 3V3_AON, including all FT232H decoupling and its internal-regulator output capacitors.
- **≤9 µF in total** ✓.

Behind the switch, total bulk capacitance is ≤100 µF. At a rise time of ≥3 ms the inrush is ≤100 µF × 5.25 V / 3 ms ≈ 175 mA. That inrush only occurs after configuration, while the downstream regulators are still in their own soft-start.

### 2.6 Sequencing

1. **Attach.** 3V3_AON comes up. The FT232H loads its EEPROM and enumerates (≈61 mA).
2. **SET_CONFIGURATION.** The FT232H drives `PWREN_N` low and the load switch ramps `VBUS_SW` over ≥3 ms.
3. **Digital rails.** The 3V3_D buck and 3V3_CLK start, then the 1V2_FPGA, 1V8_A and 1V8_D LDOs (enabled from 3V3_D).
4. **Power good.** `PG_3V3D` goes valid. This enables the FIFO bus switch (`BUS_OE_N` low) and releases FPGA CRESET_B. The FPGA then configures from SPI flash.
5. **Analog rails.** The FPGA asserts `AFE_EN`, bringing up ±6 V and then ±5V_A. `PG_AFE` returns to the FPGA.
6. **ADC start.** The FPGA configures the ADC over SPI and the board is ready. The host polls for a status reply before arming.
7. **Suspend.** `PWREN_N` goes high and everything gated collapses. `PG_3V3D` falls, which disables the bus switch. **Capture-buffer contents are lost in suspend** (documented behaviour).

### 2.7 Back-powering protection

The FT232H stays powered while the FPGA is off. Its FIFO outputs would otherwise back-feed the unpowered FPGA through I/O clamp diodes, which breaks both the preconfig and suspend budgets and is a latch-up risk.

**Solution:** a CBT-class bus switch (≥15 bits) between the two parts.
- **Signals:** 8 data lines plus RXF#, TXE#, RD#, WR#, OE#, SIWU# and CLKOUT.
- **Power:** VCC from 3V3_AON.
- **Enable:** `BUS_OE_N` is pulled up to 3V3_AON, so the switch defaults to disabled. A small N-FET pulls it low, with its gate driven from `PG_3V3D` (pulled up to 3V3_D).
- **Timing:** CBT propagation delay (~0.25 ns) is negligible against the 60 MHz FIFO timing.

On the analog side, the ADC and the FDAs share the same gated domain. Two measures keep the FDA from back-feeding the ADC inputs while the rails collapse:
- Keep ±5V_A bulk ≤10 µF per rail, so the analog rails decay no slower than 1V8_A.
- The filter-termination resistance at the ADC input limits any injected current.

Verify both in the schematic stage.

## 3. USB bridge — FT232H (U-bridge) + 93LC56

**Reasoning:** SPEC §4.6.

**Key values:**
- **FIFO mode:** synchronous 245 FIFO, 60 MHz CLKOUT, 8-bit bus. The bus can carry 60 MB/s; USB HS bulk in practice is 35–42 MB/s, which is ≥30 MB/s (`usb.throughput_MBps`) ✓.
- **Readout time:** a 4 MB capture reads out in ≈0.1–0.12 s; the full 32 MB in ≈0.8–1 s.
- **Supplies:** 3V3_AON.
- **Crystal and reference:** 12 MHz crystal and a 12 kΩ RREF, per the datasheet.
- **EEPROM configuration:**
  - 245 FIFO mode, bus-powered, MaxPower = 450 mA (matches `power.vbus_current_mA`).
  - `PWREN_N` on one of the configurable ACBUS pins (ACBUS8/9); exact pin assigned in the schematic stage.
  - Remote wake-up disabled.
- **Calibration storage:** the EEPROM user area holds the calibration constants (§10).

## 4. Capture/control logic — FPGA (no MCU)

There is **no microcontroller** on this board. This is intentional: SPEC §4.7 chose an FPGA because it handles deterministic capture, SDRAM control, triggering and the FIFO in one device, and the FT232H needs no firmware. An empty MCU section is not an omission.

**Functions:**
- **ADC capture:** both channels on the same clock edge (F1).
- **Decimation (F10):** 10 MSPS / N by boxcar/CIC averaging. The averaging acts as the anti-alias filter at decimated rates; the analog filter only protects the 10 MSPS case.
- **Trigger (F9):**
  - software arm/force
  - per-channel level + edge with hysteresis
  - pre-trigger depth set by writing a circular buffer in SDRAM
- **SDRAM controller:** 100 MHz.
- **FT232H FIFO interface:** 60 MHz domain, with async FIFOs in block RAM between the clock domains.
- **Host command set:** arm, force, set trigger, set decimation, read status, read buffer.
- **Board control:** ADC SPI configuration, `AFE_EN`, LEDs.

**I/O count (user I/O, excluding dedicated config pins):**

| Group | Signals | Pins |
|-------|---------|------|
| SDRAM | DQ 16 + A 13 + BA 2 + DQM 2 + CS#, RAS#, CAS#, WE#, CKE, CLK | 39 |
| FT232H FIFO | D 8 + RXF#, TXE#, RD#, WR#, OE#, SIWU#, CLKOUT | 15 |
| ADC data | 2 × 12-bit parallel CMOS + DCO + 2 × OR | 27 |
| ADC control | SPI ×3 + PDN/RESET | 4 |
| FPGA_CLK | | 1 |
| Power control | `AFE_EN`, `PG_AFE` | 2 |
| LEDs | | 3 |
| Spare/test | | 4 |
| **Total** | | **95** |

If the ADC has a multiplexed or serial-LVDS output, the ADC group drops to about 12–14 pins.

- **Requirement:** ≥95 user I/O. At least one bank must be at 1.8 V (`1V8_D`, for the ADC); the others are at 3.3 V (SDRAM, FIFO).
- **Package:** TQFP or other hand-solderable / standard reflow.
- **Candidate:** iCE40HX4K-TQ144. It has 107 user I/O, a 1.2 V core, PLL and 80 Kbit BRAM, and open toolchain support. Its power fits the 1V2_FPGA allocation of 30 mA plus about 25 mA of 3.3 V I/O.
- **Configuration:** SPI flash on 3V3_D. CRESET_B is held low until `PG_3V3D` is good.

## 5. Buffer memory — SDR SDRAM

**Reasoning:** SPEC §4.4.

**Key values:**
- **Part:** 256 Mbit ×16 SDR SDRAM, 3.3 V (TSOP-II-54 class).
- **Clock:** 100 MHz from the FPGA PLL, giving 200 MB/s raw. That is more than 40 MB/s capture write plus ≤40 MB/s readout.
- **Organisation:** 16 M words, channel-interleaved, about 0.84 s per channel at 10 MSPS. This exceeds 0.1 s (`capture.depth_s`) and 4 MB (`capture.buffer_MB`) ✓.
- **Refresh:** 8192 rows / 64 ms.
- **Current:** 70 mA average allocated (on 3V3_D). It is unpowered before configuration and in suspend.

## 6. Clocking

**Topology:** XO (10.000 MHz, 3.3 V LVCMOS, on `3V3_CLK`) → 1:2 fanout buffer.
- **Output A → ADC clock pin.** Point-to-point, series terminated, ≤25 mm, over unbroken GND, away from switchers. AC-couple and bias to the ADC clock-input level if it differs from 3.3 V.
- **Output B → FPGA global clock pin.** The FPGA PLL derives 100 MHz for SDRAM and logic.

The ADC clock never passes through FPGA fabric or the PLL, because FPGA PLL jitter is tens of ps.

The ADC must accept a 10 MSPS clock, so its minimum f_s must be ≤10 MSPS. Verify this in part selection.

**Jitter allocation** — budget `clock.jitter_ps_rms` ≤ 5 ps:

| Contributor | Allocation (ps rms) |
|-------------|---------------------|
| XO phase jitter (12 kHz–5 MHz) | ≤1.0 |
| Fanout buffer additive | ≤0.3 |
| ADC aperture jitter | ≤0.5 |
| Routing, supply-induced, crosstalk | ≤1.0 |
| **RSS total** | **≈1.5** ✓ (SNR_jitter at 5 MHz ≈ 86 dB; at 1 MHz ≈ 100 dB) |

**Converter spurs:** buck and boost switching spurs can alias into the band. The recommended mitigation is to sync those converters to a clock divided from FPGA_CLK, e.g. 10 MHz / 8 = 1.25 MHz, so the spurs land in known bins. This is an option if the selected converters have SYNC pins.

## 7. Analog front end (×2, identical: CH1, CH2)

**Gain chain** (at full scale):

| Point in chain | Swing |
|----------------|-------|
| BNC (full scale) | ±10.53 V |
| BNC (nominal input) | ±10 V |
| Divider tap | ÷5 → ±2.105 V |
| Buffer output | G = +1 → ±2.105 V |
| FDA output | G = 0.475 → ±1.0 V diff |
| ADC | 2 Vpp diff full scale |

The nominal ±10 V input uses 95 % of full scale, leaving ≈5 % over-range headroom so that over-range (OR) flags are meaningful.
- 1 LSB = 21.06 V / 4096 ≈ 5.1 mV referred to input (RTI).
- `input.voltage_range_V` ✓.

### 7.1 Input divider and impedance

**Divider:**
- R_top = 800 kΩ ∥ C_top ≈ 25 pF
- R_bot = 200 kΩ ∥ C_bot ≈ 100 pF (includes buffer input, clamps, parasitics, and a trimmer for compensation)

**Results:**
- R_in = 1.000 MΩ
- C_in = series combination of C_top and C_bot = 0.8 × 25 pF = 20 pF
- `input.impedance` ✓

**Compensation:** the divider is compensated (R_top·C_top = R_bot·C_bot), so its ratio is flat across the band.

**Resistors:** 0.1 %. R_top must have a ≥75 V working-voltage rating.

### 7.2 Overvoltage protection

**Clamps:** low-leakage diode pair (≤5 nA at 5 V, e.g. BAV199-class) from the divider tap to `+5V_A` and `-5V_A`.

**At +30 V on the BNC:**
- The tap clamps at ≈5.6 V.
- Clamp current = (30 − 5.6) V / 800 kΩ ≈ 31 µA.
- R_top dissipates about 1.1 mW.

**With the rails off:** the tap clamps at ≈0.6 V instead, so (30 − 0.6) V / 800 kΩ ≈ 37 µA flows into the unpowered ±5V_A rails. This current comes from the source, not VBUS, so it does not count against the suspend budget; it is harmless. Verify in the schematic stage that it cannot lift the dead ±5V_A rails enough to partially power the buffers (≤10 µF bulk, regulator output pull-down discharges it).

**Buffer input:** a 1 kΩ series resistor between tap and buffer limits current into the op amp's input ESD diodes.

Result: `input.overvoltage_V` ±30 V ✓.

**Effect on accuracy and bandwidth:** clamp leakage of 5 nA × 160 kΩ = 0.8 mV at the tap (4 mV RTI), and clamp capacitance is absorbed into C_bot. Neither degrades 1 MΩ or 3 MHz.

**No TVS at the BNC (intentional).** It would leak, and it would eat into the 20 pF budget. ESD current is coupled through C_top into the tap clamps instead. A DNP footprint for a ≥33 V standoff, low-capacitance TVS is optional.

### 7.3 Buffer

FET-input voltage-feedback op amp, G = +1, on ±5V_A.

| Parameter | Requirement | Reason |
|-----------|-------------|--------|
| GBW | ≥50 MHz | |
| Slew rate | ≥80 V/µs | Full-scale sine at 3.2 MHz needs 42 V/µs; ≈2× margin for distortion |
| I_b | ≤20 pA | Into 160 kΩ gives ≤3.2 µV |
| V_os | ≤0.5 mV | |
| I_q | ≤4 mA | |

Candidate: OPA810-class.

### 7.4 FDA (single-ended → differential)

Single supply on +5V_A.
- **Gain:** G = Rf/Rg = 0.475.
- **V_OCM:** the ADC VCM output (≈0.9 V).
- **Output legs:** 0.9 ± 0.5 V.
- **Input common mode:** 0.29–0.93 V over the full input range. Both are inside a rail-to-rail-output FDA's range.

| Parameter | Requirement |
|-----------|-------------|
| I_q | ≤3 mA |
| HD2/HD3 | ≤ −80 dBc at 1 MHz |
| Output offset | ≤0.3 mV |

Candidate: THS4551-class. Gain resistors are 0.1 %.

### 7.5 Anti-alias filter

Passive LC, 5th order, differential, located between the FDA and the ADC.
- **Termination:** driven from a low impedance (the FDA) and terminated at the ADC input, i.e. singly terminated, so there is no 6 dB loss.
- **Passband:** ripple ≤0.1 dB to 3.2 MHz; −3 dB ≥3.3 MHz.
- **Stopband:** design target ≥50 dB at ≥7.5 MHz, so that ≥40 dB still holds with L ±5 % and C ±2 % tolerances. Result: `analog.bandwidth_MHz` ✓.
- **Response:** elliptic (Cauer) is preferred. A 0.1 dB Chebyshev computes to only 42.5 dB at 7.5 MHz nominal, which is too thin a margin for tolerance; a 5th-order Butterworth (≈33 dB) fails.
- **ADC kickback:** the last element absorbs the ADC's kickback RC.

### 7.6 Accuracy and noise allocations (worst-case linear sum)

**Gain** — `analog.dc_accuracy` ≤1 %:

| Contributor | Allocation |
|-------------|-----------|
| Divider ratio | 0.2 % |
| FDA network | 0.2 % |
| Filter / termination DC | 0.1 % |
| ADC gain error including reference | ≤0.5 % |
| **Total** | **1.0 %** ✓ (no margin) |

If the ADC's internal reference cannot meet 0.5 %, use an external 0.1 % reference.

**Offset** — ≤±20 mV RTI:

| Contributor | Allocation (RTI) |
|-------------|------------------|
| Clamp leakage | 4.0 mV |
| Buffer V_os | 2.5 mV |
| FDA output offset (0.3 mV × 10.53) | 3.2 mV |
| ADC offset ≤0.9 mV at the ADC input (× 10.53) | 9.5 mV |
| **Total** | **19.2 mV** ✓ (no margin) |

**AT RISK:** many 12-bit ADCs specify uncalibrated offset of several mV. If no ADC that meets the other limits achieves ≤0.9 mV, the ASSUMED `analog.dc_accuracy` offset limit must be revised. That revision needs a recorded decision; it must not be silently exceeded.

**ENOB** — `analog.enob_bits` ≥10.5:
- ADC SINAD ≥68 dB at 1 MHz, plus front-end SINAD ≥72 dB, combines to ≈66.5 dB → ENOB ≈10.75 ✓.
- Front-end noise is negligible:
  - kT/C at the tap ≈ 6 µV rms
  - buffer ≈ 14 µV rms
  - both against 1 LSB at the tap ≈ 1 mV
- Jitter is negligible (§6).

## 8. ADC

The ADC is a dual, simultaneous-sampling 12-bit converter (SPEC §4.8) on `1V8_A` / `1V8_D`. Selection limits for the part-selection stage:

| Parameter | Limit |
|-----------|-------|
| Sample rate | f_s = 10 MSPS supported (min f_s ≤10 MSPS) |
| Input | 2 Vpp differential full scale, VCM output |
| AVDD current | ≤60 mA at 10 MSPS, both channels |
| DRVDD current | ≤15 mA |
| SINAD | ≥68 dB at 1 MHz |
| Aperture jitter | ≤0.5 ps |
| Offset | ≤0.9 mV |
| Gain error | ≤0.5 % |
| Outputs | 1.8 V CMOS or LVDS; parallel needs ≤27 FPGA pins |
| Configuration | SPI or pin-strapped |
| Package | QFN/TQFP |

The candidate must also have an installed KiCad symbol.

If the chosen ADC runs on 3 V instead, re-derive the 1V8_A/1V8_D rails and the 3V3_D load against §2.2.

## 9. UI / indicators

The board has three LEDs, driven by the FPGA from 3V3_D at ≈1 mA each:

| LED | Meaning |
|-----|---------|
| `LED_PWR` | Gated rails up and FPGA configured |
| `LED_ARM` | Armed / triggered |
| `LED_OVR` | ADC over-range or error |

**Intentional absences:**
- **No LED on the always-on rail**, because of the suspend budget (§2.4).
- **No buttons, display or external trigger input.** All control is from the host (F9 is a software trigger plus a logic trigger), and no requirement asks for them.

## 10. Configuration, programming and calibration storage

**FPGA bitstream:**
- Stored in a SPI NOR flash on 3V3_D.
- Programmed through a 2×5 1.27 mm SPI header. Programming happens with the board powered and the FPGA held in reset through CRESET_B on the header.
- Optional: field update through gateware over the FIFO.
- The FT232H MPSSE is **not** used for flash programming. Its ADBUS pins are the FIFO data bus, so sharing them would load the FIFO lines.

**Calibration constants** (`analog.dc_accuracy`):
- **Contents:** per-channel gain and offset, stored as 4 × 32-bit values plus a CRC.
- **Location:** the FT232H 93LC56 EEPROM user area.
- **Access:** the host reads them through D2XX even before the FPGA powers up. No extra part is needed and nothing is added to the suspend load.
- If the user area is too small, use a 93LC66 (4 Kbit) instead.

## 11. Budget check summary

| Budget | Architecture value | Status |
|--------|-------------------|--------|
| `power.vbus_current_mA` ≤450 | ≈342 mA at 4.4 V | ✓ |
| `power.preconfig_current_mA` ≤100 | ≈61 mA | ✓ (FT232H max current to VERIFY) |
| `power.suspend_current_mA` ≤2.5 | ≤1.6 mA allocated (cap 1.75) | ✓ (FT232H suspend current to VERIFY) |
| `power.vbus_capacitance_uF` ≤10 | ≤9 µF ungated | ✓ |
| `power.vbus_voltage_V` 4.4–5.25 | All converters and LDOs specified for VBUS_SW down to 4.3 V | ✓ |
| `clock.jitter_ps_rms` ≤5 | ≈1.5 ps RSS | ✓ (routing deferred) |
| `input.impedance` | 1 MΩ ∥ 20 pF | ✓ |
| `input.overvoltage_V` ±30 | 31 µA clamp current | ✓ |
| `analog.bandwidth_MHz` | −3 dB ≥3.3 MHz, ≥40 dB at 7.5 MHz | ✓ |
| `analog.enob_bits` ≥10.5 | ≈10.75 | ✓ |
| `analog.dc_accuracy` | 1.0 % gain / 19.2 mV offset | ✓ at limit (ADC offset AT RISK) |
| `capture.buffer_MB` ≥4, `capture.depth_s` ≥0.1 | 32 MB, ≈0.84 s | ✓ |
| `usb.throughput_MBps` ≥30 | 35–42 MB/s practical | ✓ |
