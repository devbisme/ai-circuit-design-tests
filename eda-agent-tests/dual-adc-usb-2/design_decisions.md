# Dual-channel ±10 V, 10 MS/s, 12-bit USB ADC: design decisions

Requirements (from `dual-adc-prompt.txt`): 2 channels, ±10 V input, 10 MS/s, 12 bits,
≥0.1 s capture at full rate, scope-lead-compatible input connectors, USB 2.0 for power
and data (USB-C only if USB 2.0 power is insufficient).

## Derived numbers

| Quantity | Value |
|---|---|
| Raw sample rate, both channels | 2 × 10 MS/s = 20 MS/s |
| Raw data rate (16-bit words) | 40 MB/s (320 Mb/s) |
| Capture for 0.1 s | 2 M samples = 4 MB (16-bit words), 3 MB if packed |
| USB 2.0 HS bulk, practical | ~35–42 MB/s through an FT232H in sync-FIFO mode (FTDI's quoted maximum is 40 MB/s) |

Streaming 40 MB/s over USB 2.0 is at or past the practical limit, with no margin for host
latency. **So the board captures into on-board memory and then uploads.** At lower rates
the same hardware can still stream.

## Decisions (options → choice)

### 1. Input connector
- **BNC (chosen).** Standard oscilloscope probes and BNC leads mate directly.
- SMA: needs adapters for scope probes.
- Banana/test-lead jacks: not compatible with scope probes.

### 2. Input impedance / attenuator
- **1 MΩ compensated ÷11 divider (909 kΩ / 90.9 kΩ) with a JFET/CMOS buffer (chosen).**
  It matches the scope standard of 1 MΩ, so 1× and 10× probes both work. ±10 V maps to
  ±0.909 V, leaving 10 % headroom below the ADC's ±1 V full scale.
- 50 Ω termination: wrong for scope probes.
- Low-impedance resistive attenuator straight into the FDA (e.g. 10 kΩ): simpler, but it
  loads 10× probes and breaks their compensation.

Compensation: 909 kΩ ∥ 2.7 pF over 90.9 kΩ ∥ (22 pF + ~5 pF of parasitics). An extra
12 pF at the connector brings the input to roughly 1 MΩ ∥ 15 pF. **Uncertain:** the
parasitics are estimates, so the compensation should be checked with a square wave on the
built board and C2 adjusted. A trimmer is an option.

Protection: BAV99 clamps to the ±4 V buffer rails, after the 909 kΩ resistor, which
limits fault current to ~0.1 mA at 100 V.

### 3. ADC
- **LTC2290 (ADI/Linear), chosen.** Dual 12-bit, 10 MS/s, 3 V supply, parallel CMOS
  outputs, ±1 V (2 Vpp) differential input, built-in reference and VCM output. It has a
  KiCad library symbol and footprint (QFN-64 9×9).
- AD9238-20: dual 12-bit at 20 MS/s. LQFP-64 is easier to hand-solder, but the part is
  older and has no KiCad symbol.
- 2 × single-channel ADCs (e.g. AD9235): more parts, and the two channels' clocks need
  matching.
- MCU with a built-in ADC: none meets 12 bits at 10 MS/s × 2 with real ENOB.

**Uncertain:** the LTC2290's lifecycle status was not verified (the analog.com page
timed out). The pin-compatible LTC2291 (25 MS/s) and LTC2292 (40 MS/s) are drop-in
fallbacks.

### 4. ADC driver
- **Unity-gain buffer (OPA1656, ±4 V) followed by a fully differential amplifier
  (THS4521, single 3.3 V, gain 1, VOCM from the ADC's VCM pin), chosen.** The FDA runs on
  the ADC's analog rail, so its outputs cannot exceed the ADC's absolute-maximum input
  range.
- Transformer coupling: no DC response, so it is wrong for a DC-coupled scope-style input.
- Single-ended drive of the ADC: costs SNR and even-order distortion.

Limitation: the OPA1656 slew rate is 24 V/µs (datasheet SBOS901), so full-scale
(±0.91 V) sine waves are slew-limited above ~4.2 MHz. Smaller signals reach Nyquist.

Anti-aliasing: a first-order 4.8 MHz pole (1 kΩ ∥ 33 pF in the FDA feedback), plus an
RC (2 × 49.9 Ω, 100 pF differential) at the ADC input. **This is weak anti-aliasing for
12 bits.** A higher-order filter needs a stated signal bandwidth, which the prompt does
not give.

### 5. Capture memory (≥4 MB)
- **32 MB SDR SDRAM, MT48LC16M16A2 (16M × 16), chosen.** It holds 0.8 s at the full
  rate (8× the requirement), is cheap, and uses a TSOP-II-54 package with a KiCad symbol
  and footprint.
- 4 MB async SRAM (IS61WV204816): meets 0.1 s exactly, with zero margin.
- FPGA block RAM: far below 4 MB on small FPGAs.
- HyperRAM: fewer pins, but more complex timing and BGA packages.

### 6. Controller / glue
- **Lattice iCE40HX4K-TQ144, chosen.** 3.3 V I/O, enough I/O for the ADC (26 + clock),
  SDRAM (39) and FT232H (15), an open-source toolchain (yosys/nextpnr/icestorm), and a
  TQFP package.
- Microcontroller (e.g. STM32H7 with a ULPI PHY): it can't easily take 24 parallel bits at
  10 MHz and an SDRAM at the same time.
- Larger FPGA (ECP5): more capability than needed; BGA.

### 7. USB interface
- **FTDI FT232H in 245 synchronous FIFO mode, chosen.** USB 2.0 High Speed, up to
  40 MB/s, needs no firmware, and has vendor drivers plus libftdi.
- Cypress FX2LP (CY7C68013A): about the same throughput, but needs firmware.
- FX3 (USB 3.0): overkill, and BGA.

### 8. USB connector / power source
Power budget (typical, all from VBUS):

| Load | Rail | mA |
|---|---|---|
| LTC2290 (both channels, 10 MS/s) | 3.3 VA | ~40 |
| 2 × THS4521 | 3.3 VA | ~3 |
| OPA1656 (dual) | ±4 V | ~10 (≈20 mA from 5 V via charge pump) |
| iCE40HX4K core + PLL | 1.2 V (from 3.3 V) | ~30 |
| iCE40 I/O, SDRAM (active), FT232H, flash, osc, LEDs | 3.3 VD | ~260 |
| **Total from VBUS (linear regulators)** | 5 V | **~330 mA** |

- **USB 2.0 with a Type-B receptacle, chosen.** 330 mA is under the 500 mA allowed after
  enumeration (about 35 % margin), so USB-C is not needed. Full-size B is mechanically
  robust for a bench instrument.
- Micro-B: smaller, but more fragile.
- USB-C: not required by the power budget.

**Caveat:** before enumeration USB 2.0 allows only 100 mA. The board draws more at
power-up, as most FT232H gadgets do. The FT232H EEPROM must declare 500 mA. A strictly
compliant design would hold the FPGA/SDRAM off until enumeration (FT232H PWREN# could
drive a load switch). That is not implemented here and is flagged as a TODO.

### 9. Clocking
- **One 10 MHz low-jitter XO (Abracon ASE) drives both ADC clock pins directly through
  series resistors; a third copy goes to an FPGA global clock input, chosen.** The FPGA
  runs SDRAM/USB logic from the FT232H's 60 MHz CLKOUT (or its PLL).
- FPGA-generated ADC clock: FPGA output jitter (hundreds of ps) would cost SNR at MHz
  input frequencies. 12-bit SNR at 5 MHz needs ≲6 ps jitter.

### 10. FPGA configuration
- **SPI flash (W25Q32JV) plus a 2×4 programming header (iceprog-compatible signals plus
  CRESET/CDONE), chosen.** It's simple and has no bus sharing with the FIFO data lines.
- Program the flash through the FT232H's MPSSE: this shares ADBUS with the FIFO data bus,
  which risks contention at power-up.
- Later, gateware could also reflash over USB, since the flash SPI pins are user I/O after
  configuration.

### 11. Power rails
| Rail | Source | Part |
|---|---|---|
| +5V (VBUS) | USB, through a 750 mA polyfuse and ferrite | — |
| +3V3 (digital) | LDO from +5V | AP2112K-3.3 (600 mA) |
| +1V2 (FPGA core) | LDO from +3V3 | AP2112K-1.2 |
| +3V3A (ADC, FDAs) | low-noise LDO from +5V | LP5907-3.3 (250 mA) |
| ±4V (buffers) | charge pump + LDOs from +5V | LM27762 (R1=232k/R2=100k → +3.98 V; R3=226k/R4=100k → −3.98 V); PGOOD (open drain) pulled up and read by the FPGA |

A switcher for +3V3 would save ~0.5 W of heat but add noise next to a 12-bit ADC. The
linear regulators fit the budget.

### 12. PCB
4 layers: signal / GND / power / signal. The analog front end and ADC sit on one side of
the board, over solid ground.

## Sources
- LM27762 datasheet SNVSAF7C (TI): pin table §4, equations (1) and (3) in §7.2.2,
  capacitors in §5.5 test conditions.
- THS4521 datasheet SBOS458H (TI): pin functions (pg. 4), 3.3 V common-mode input range.
- OPA1656 datasheet SBOS901 (TI): supply 4.5–36 V, SR 24 V/µs, IB ±10 pA, VCM to (V+)−2.25 V.
- KiCad 10 library symbols (pin numbers) for LTC2290xUP, FT232H, ICE40HX4K-TQ144,
  MT48LC16M16A2TG, W25Q32JVSS, 93LCxxB, LM27762, AP2112K, LP5907, USBLC6-2SC6.
- Nexperia BAV99 datasheet (pinning table): pin 1 = anode D1, pin 2 = cathode D2,
  pin 3 = common. The KiCad symbol's pin *names* are reversed (K/A), but its graphic
  matches; the design wires it by pin number.
- **Not verified against a datasheet:** the download failed for both
  (ftdichip.com returned 403; analog.com timed out). These values come from memory and
  must be checked before fabrication:
  - FT232H support circuit: VREGIN/VCCD strapping, VCCA/VCORE decoupling, 12 kΩ REF,
    27 pF crystal loads, 93LC56B wiring, 245 sync-FIFO pin map.
  - LTC2290 configuration: SENSE=VDD → 2 Vpp, MODE=2/3·VDD → two's complement + DCS,
    MUX=VDD, REFH/REFL capacitors, VCM 2.2 µF.
