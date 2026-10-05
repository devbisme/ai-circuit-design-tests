# Dual-channel ±10 V, 10 MSPS, 12-bit USB ADC — design notes

Source requirement: `dual-adc-prompt.txt`.

## Derived requirements

| Item | Value | Derivation |
|---|---|---|
| Channels | 2 | spec |
| Input range | ±10 V (designed for ±10.5 V full scale) | spec + 5 % headroom |
| Sample rate | 10 MSPS per channel, simultaneous | spec |
| Resolution | 12 bit | spec |
| Capture depth | ≥ 2 ch × 10 M × 0.1 s = 2 M samples = 4 MB at 16 bit/sample | spec |
| Raw data rate | 2 × 10 M × 2 B = 40 MB/s | 16-bit containers |
| Input connector | BNC, 1 MΩ ‖ ~20 pF (scope-probe compatible) | "mates with standard scope leads" |
| Host link | USB 2.0 High-Speed, bus powered | spec |

40 MB/s is at/above the practical USB 2.0 bulk ceiling (~35–42 MB/s), so continuous
streaming is **not** guaranteed. The design captures into on-board memory, then
uploads. This satisfies the 0.1 s requirement with margin.

## Decisions (options → recommendation)

### D1. ADC
- **LTC2290 (dual 12b 10 Msps, 3 V, 120 mW, parallel CMOS)** — ← selected. Exactly meets spec, simultaneous sampling, lowest power, KiCad symbol available. Pin-compatible family (LTC2291 25 Msps, LTC2292 40 Msps) gives a drop-in upgrade path if margin on rate is wanted.
- LTC2292 (40 Msps): same footprint, ~2× power, no requirement benefit.
- Two single-channel ADCs (e.g. AD9226-class): more parts, more pins, channel skew.
- MCU-internal ADC (STM32H7 12-bit): ENOB well below 12 at 10 Msps, inputs not simultaneous across both ADCs at this rate without care.

### D2. Capture/control logic
- **iCE40HX4K-TQ144 FPGA + SDRAM + FT232H** ← selected. Deterministic capture, ~100 user I/O, TQFP (no BGA), open toolchain (yosys/nextpnr/icestorm), low power.
- FX2LP + FPGA: two programmable devices, legacy part.
- STM32H7 + ULPI PHY (USB3300) + SDRAM, ADC via DCMI: no FPGA, but DCMI 14-bit limit forces ADC output muxing at 20 MHz; tighter timing analysis; more firmware risk.
- iCE40HX8K-BG121: more logic than needed, BGA.

### D3. Sample memory
- **MT48LC16M16A2TG (256 Mbit SDR SDRAM, x16)** ← selected. 32 MB → 0.8 s at full rate (8× margin). 16-bit @ 80–100 MHz = 160–200 MB/s ≫ 40 MB/s write.
- IS42S16400J (64 Mbit): 8 MB, 2× margin; same package, little cost difference.
- FPGA internal RAM: iCE40HX4K has 80 kbit. Insufficient.

### D4. USB interface
- **FT232H in FT245 synchronous FIFO mode** ← selected. USB 2.0 HS, ~35–40 MB/s, 8-bit FIFO, 60 MHz CLKOUT. Needs 93LC56B EEPROM to set FIFO mode.
- FT2232H: second channel unused in sync-FIFO mode.
- FT601 (USB 3): not USB 2.0 as specified; larger package.

### D5. Analog front end (per channel)
BNC → compensated 1 MΩ divider (953 kΩ ‖ 12 pF over 47.5 kΩ ‖ (180 pF + 5–30 pF trim)), ratio 0.0475 →
diode clamp (BAV99) to ±2.5 V → 1 kΩ (R5) → OPA356 unity-gain **Sallen-Key** (R2 = 1 kΩ, C1 = 150 pF to
output, C2 = 39 pF to GND; f0 ≈ 2.1 MHz, Q ≈ 1) → THS4521 FDA, gain 2, Cf = 82 pF across each 1 kΩ Rf
(pole 1.9 MHz), VOCM = ADC VCM (1.5 V, 220 nF local bypass) → 2×49.9 Ω + 100 pF diff (16 MHz kickback filter) → ADC.
±10 V in → ±0.95 V diff at ADC (95 % FS); FS = ±10.5 V.

Options considered:
- **Hi-Z divider + buffer + FDA** ← selected. True 1 MΩ scope-like input, 10× probes compensate.
- FDA alone with large input resistors: input Z set by R (≤ ~10 kΩ practical) — not scope-compatible.
- Programmable gain / relays: not required by spec.

Known limitations (TODO):
- Anti-alias response (nodal model incl. divider source impedance; scratch `filter sim`): −3 dB 1.65 MHz,
  −0.03 dB flatness to 200 kHz, −23 dB at 5 MHz (Nyquist), −36 dB at 8 MHz, −42 dB at 10 MHz.
  Not enough for full 72 dB alias rejection at 12 bits; a sharper (5th–7th order) filter or 2–4× oversampling
  + digital decimation would be needed for that.
- Compensation: the SK's C2 (39 pF) appears in parallel with the divider bottom; the trimmer lands at ≈18 pF
  (mid-range) when trimmed with a 1 kHz square wave. (The previous 22 pF/390 pF values could not be balanced
  by the 5–30 pF trimmer — fixed 2026-10-02.)
- Input capacitance ≈ 11–14 pF (typical scope 13–20 pF), within ×10 probe compensation range.
- DC-coupled only (no AC coupling switch).
- 953 kΩ top resistor must be a ≥ 200 V-rated 1206 part (overvoltage tolerance limited by it and the clamp current, ~0.1 mA at 100 V).

### D6. Power source (USB 2.0 vs USB-C)
Estimated budget (from 5 V; unverified vendor-typical numbers except LTC2290):

| Load | Est. power |
|---|---|
| LTC2290 (120 mW) via LP5907 from 5 V | ~0.20 W |
| OPA356 ×2 + THS4521 ×2 via LM27762 (±2.5 V) | ~0.17 W |
| SDRAM active | ~0.40 W |
| FT232H HS active | ~0.23 W |
| iCE40HX4K core + I/O | ~0.12 W |
| Osc, flash, EEPROM, LEDs | ~0.05 W |
| Buck losses (~88 %) | ~0.10 W |
| **Total** | **≈ 1.3 W ≈ 260 mA @ 5 V** |

USB 2.0 high-power port supplies 500 mA (2.5 W) → **USB 2.0 power is sufficient** (~45 % margin).
Before enumeration only 100 mA is allowed; the FPGA keeps the ±2.5 V op-amp rails off (ANA_EN low)
and the ADC in nap mode (ADC_SHDN high, ≈30 mW per datasheet) until the host configures the device.

Connector options:
- **USB-C receptacle wired for USB 2.0 only (Rd = 5.1 kΩ on CC1/CC2)** ← selected. It is still a USB 2.0 port; robust, current-standard cable, and gives 1.5/3 A headroom from Type-C sources at zero cost.
- USB-B: robust, bulky, legacy.
- Micro-B: fragile.

### D7. Power tree
- VBUS → polyfuse (750 mA hold) → ferrite → +5V
- +5V → TPS62162 buck (fixed 3.3 V, 1 A) → +3V3 (digital: FPGA I/O, SDRAM, FT232H, flash, osc)
- +3V3 → TLV75512 LDO → +1V2 (FPGA core); +1V2 → 100 Ω + 4.7 µF + 100 nF → VCCPLL (GNDPLL isolated from GND)
- +5V → LP5907-3.3 LDO (EN tied to IN, always on) → +3.3VA (ADC VDD, THS4521). Always on because LTC2290 digital inputs (CLK, SHDN) must stay ≤ VDD + 0.3 V.
- +5V → LM27762 (EN± = ANA_EN) → ±2.5 V (OPA356 buffers / clamps)

### D8. Clocking
- 10 MHz 3.3 V CMOS oscillator (Abracon ASE) → series-terminated branches to ADC CLKA/CLKB and FPGA GBIN6. ADC is clocked directly by the oscillator (not via FPGA) to keep jitter low.
- FPGA PLL: 10 MHz → SDRAM clock (80–100 MHz). FT232H CLKOUT (60 MHz) → FPGA GBIN4.

## FPGA pin plan (iCE40HX4K-TQ144)

| Bank | Use |
|---|---|
| 3 (IOL) | ADC DA0–11, OFA, DB0–11, OFB; CLK_10M on pin 21 (GBIN6) |
| 1 (IOR) | SDRAM DQ0–15, CLK, CKE, CS#, RAS#, CAS#, WE#, DQML, DQMH |
| 0 (IOT) | SDRAM A0–12, BA0–1, ANA_EN, ADC_SHDN, LED0, LED1 |
| 2 (IOB) | FT232H D0–7, RXF#, TXE#, RD#, WR#, OE#, SIWU#, CLKOUT (pin 52 GBIN4), ACBUS7–9 |
| SPI | W25Q32JV config flash, 2×4 programming header |

## Verification status (2026-10-01)

| Check | Result |
|---|---|
| KiCad 9.0.9 ERC (scratch copy, see below) | 3 items, all intentional: U6 PGOOD→GND (LM27762 datasheet says tie to GND if unused); U9 WP#/HOLD#→+3V3 (2 warnings) |
| Netlist connectivity vs. intent (44 scripted checks: AFE chain, ADC refs/VCM, rails, clocks, USB, config) | 44/44 pass |
| Single-pin nets | Only deliberate no-connects (unused FPGA I/O, NC pins, SBU1/2, TPS62162 PG) |
| Konnect `validate_component_connections` | 0 unconnected pins |
| Components / footprints | 161 parts, all have footprints, no duplicate references |

Outputs in `outputs/`: schematic PDF, KiCad netlist, grouped BOM CSV, ERC JSON.

**Tool-version caveat:** Konnect 0.12.1 writes `(generator_version "10.0")`; the system
KiCad (/usr/bin) is 9.0.9, which refuses to open the file. Open it with KiCad 10
(`~/bin/kicad10`).

**Re-verified 2026-10-02 with KiCad 10.0.4 kicad-cli on the unmodified project file:**
ERC = the same 3 intentional items (plus 290 "library not in configuration" warnings caused
by the extracted KiCad 10 lacking the stock symbol-library table; symbols are embedded, so
not a design fault). Netlist: 194 nets, 44/44 connectivity checks pass, 35 single-pin nets,
all deliberate no-connects.

## Datasheet verification (2026-10-02)

Sources (local copies in session scratch `ds/`):
LTC2290 (analog.com 2290fa via web.archive.org), FT232H (DS_FT232H v1.0, reichelt mirror),
iCE40 Hardware Checklist FPGA-TN-02006-2.3 and iCE40 LP/HX data sheet FPGA-DS-02029-3.9,
TI TPS6216x, THS4521, OPA356, LP5907, TLV755P, LM27762 (ti.com).

| Part | Item | Result |
|---|---|---|
| LTC2290 | REF bypass 0.1 µF + 2.2 µF REFH–REFL, 1 µF each to GND; VCM 2.2 µF; SENSE=VDD → ±1 V; MUX high; MODE 2/3 VDD = 2's comp + DCS; OE/SHDN low = run; NC pins; VDD 2.7–3.4 V, OVDD 0.5–3.6 V; 120 mW | ✓ matches |
| LTC2290 | Digital inputs abs. max VDD + 0.3 V | **Fixed**: +3.3VA no longer gated (clock & SHDN pull-up would have back-driven an unpowered ADC) |
| FT232H | VREGIN = 3V3 → VCCD is input; REF 12 kΩ 1 %; TEST→GND; RESET#→VCCIO; sync-FIFO pins ACBUS0–6; 27 pF crystal loads; 93LC56B (16-bit) | ✓ matches |
| FT232H | VPHY/VPLL LC-filtered (Fig. 6.3) | **Fixed**: FB2/FB3 + 10 nF/100 nF each |
| FT232H | VCORE/VCCA 100 nF | **Fixed**: C29/C31 1 µF → 100 nF |
| FT232H | EEPROM DO pulled to VCCD 10 kΩ; DO→EEDATA via 2.2 kΩ | **Fixed**: R28 moved from EEDATA to EEDO |
| iCE40 | GNDPLL not on board GND; VPP_FAST floating; VPP_2V5 2.5–3.3 V for SPI master; CRESET/CDONE/SS pull-ups | ✓ matches |
| iCE40 | VCCPLL filter 100 Ω + 4.7 µF + 100 nF | **Fixed**: 10 µF → 4.7 µF |
| iCE40 | SPI_SCK 10 kΩ pull-up recommended | **Added** R47 |
| iCE40 | Power-up order VCC→SPI_VCC→VPP | Not followed (+1V2 derives from +3V3), but DS Table 4.3 allows "no sequencing" when ramp ≥ 0.40 V/ms. TPS62162 soft-start ≈ 0.8 ms → OK. **Verify ramps at bring-up.** |
| TPS62162 | FB→AGND on fixed versions; 2.2 µH / 22 µF; PG open-drain may float | ✓ |
| THS4521 | Pinout 1 VIN−, 2 VOCM, 3 VS+, 4 VOUT+, 5 VOUT−, 6 VS−, 7 PD (high/open = on), 8 VIN+; 2.5–5.5 V | ✓ |
| THS4521 | 0.22 µF on VOCM recommended | **Added** C101/C102 (220 nF) |
| OPA356 | VCM (V−)−0.1 … (V+)−1.5 V → −2.6 … +1.0 V on ±2.5 V; signal ±0.48 V | ✓ |
| LP5907 / TLV755P | EN internal pull-down; ≥0.47 µF effective caps | ✓ |
| LM27762 | VOUT+ = 1.2 V(1+R1/R2), R2 ≥ 50 kΩ; PGOOD to GND if unused | ✓ |
| USBLC6-2SC6, BAV99 | ST/Nexperia PDFs not retrieved | KiCad library pinout only — **unverified** |

Power-budget numbers other than LTC2290 remain estimates.

## Verification after cleanup + datasheet fixes (KiCad 10.0.4 CLI)
- ERC: 3 intentional items only (U6 PGOOD→GND; U9 WP#/HOLD#→+3V3).
- Netlist: 198 nets; 54 scripted connectivity checks pass; single-pin nets are only deliberate no-connects.
- Values carry hidden BOM fields: Tolerance, Voltage, Dielectric.
