# Design risks — dual_adc_10msps

Each item: risk → mitigation (owner phase). Arithmetic is `inputs → result`.

## Analog performance

1. **Anti-alias tolerance.** HARD ≥ 72 dB at ≥ 5 MHz. Monte-Carlo, 3000 runs (R ±1 %, filter C
   ±5 %, +0–4 pF on SK ground caps, op-amp/FDA GBW ±30 %, attenuator trim residual ±1 %) →
   worst 78.7 dB (≥ 6.7 dB margin); with C ±2 % worst 80.0 dB. Mitigation: none needed for HARD.
2. **Passband flatness (SOFT ±0.5 dB, DC–1 MHz).** Nominal ±0.013 dB, but MC: C ±2 % → median
   0.16 dB, p99 0.61 dB; C ±5 % → median 0.28, p99 1.05 dB. Mitigation: C0G ≤ ±2 % on filter
   caps (sourcing); residual gain/flatness error is per-board calibratable in software.
3. **GBW pre-distortion.** SK values assume 70 MHz GBW (OPA2810/OPA810 typ). Swapping to an
   op-amp with different GBW shifts the Q 2.28 stage. Flatness (1 kHz–1 MHz, nominal parts) vs
   GBW: 35 MHz 0.87 dB, 49 MHz 0.38, **70 MHz 0.01**, 91 MHz 0.20, 180 MHz 0.53, ideal 0.86 dB;
   A(5 MHz) stays 79–82 dB throughout. Mitigation: SK op-amps are **not freely substitutable**
   (sourcing); the librarian must extract gbw_hz = 70 MHz (the GBWP at G = 11) — not the
   105 MHz small-signal BW nor the 35 MHz aux-stage figure — or the review gate simulates the
   wrong filter.
4. **OPA810 input range.** JFET stage valid to V+ − 2.5 V = +1.5 V (+1.42 V at +4V0A min
   3.924 V). SK_b input peaks 2.24 × 0.4976 V = 1.11 V (1.25 V at 11.2 V overrange) → 0.17 V
   margin worst case. Mitigation: do not raise attenuator ratio above 0.0498; do not lower +4V0A.
5. **Probe compensation.** HF/DC ratio match needs the trimmer: fixed-cap mismatch of 5 % would
   be 0.42 dB above ~15 kHz (attenuator corner 1/(2π·47.4k·231.5p) = 14.5 kHz). Mitigation:
   C102/C202 trimmer 2–6 pF, adjust with a 1 kHz square wave; document in bring-up.
6. **Input capacitance.** 10.9 pF + BNC/trace (~3–5 pF) ≈ 14–16 pF ≤ 30 pF ✓; inside standard
   10× probe range (10–25 pF). Keep the ATT node trace short; its parasitics add to C103.
7. **Noise / ENOB (SOFT ≥ 10 bit @1 MHz).** Front end at ADC input: kT/C 4.2 µV ×1.82, 3 op-amps
   6 nV/√Hz × √1.37 MHz × √3 × 1.82 = 22 µV, FDA ~11 µV → 26 µV rms → SNR_fe = 20log(0.714/26e-6)
   = 88.8 dB ≫ ADC 70.7 dB → SINAD ≈ 70 dB → ENOB ≈ 11.3 bit FS (≈ 11.2 at ±10 V). ✓
8. **Clock jitter.** Needed for 74 dB at 1 MHz: tj ≤ 10^(−74/20)/(2π·1e6) = 32 ps. XO (≤ 5 ps) +
   LVC buffer (~1 ps) → SNR_j = −20log(2π·1e6·5e-12) = 90 dB ✓. Never re-clock the ADC through
   FPGA fabric/PLL.
9. **ADS5231 below its PLL range.** PLL-enabled range 20–40 MSPS; at 10 MSPS the FPGA must write
   serial reg 0x3 D1 = 1 after a SEL reset pulse. Unconfigured FPGA → ADC runs out of spec (no
   damage). Duty cycle must be 45–55 % without PLL (XO spec ≤ 45/55 %).
10. **Leakage offset.** BAV199 leakage (≤ 5 nA max @75 V, pA typ at < 5 V) × 47.4 kΩ Thevenin
    = ≤ 0.24 mV at ATT → ≤ 0.44 mV at ADC (< 1 LSB = 0.49 mV). Calibrate offset in software.

## Power integrity

11. **USB budget.** Worst-case budget VBUS ≈ 0.43 A (buck 3.3 V × 0.36 A / 0.88 / 4.75 V = 0.284 A,
    LP5907 0.088 A, LM27762 0.057 A) vs 0.5 A USB 2.0 default → 14 % margin; typical ≈ 0.30 A.
    Decision: default USB power, Rd-only USB-C sink, no PD. If bring-up measures > 0.45 A, the
    fallback is CC-voltage sensing of a 1.5 A Type-C source (board rework).
12. **VBUS headroom.** Host 4.75 V − cable 0.25 V − PTC 0.12 V = 4.38 V at +5V. LM27762 +LDO
    needs 4.044 + 0.045 = 4.09 V ✓ (0.29 V margin); −LDO needs |CP| ≥ 4.07 V, CP ≈ 4.37 −
    0.03 A × 2.5 Ω = 4.30 V ✓; LP5907 needs ≥ 3.4 V ✓.
13. **Inrush / VBUS capacitance ≤ 10 µF.** Budget 8.9 µF (see net plan). Adding caps on
    VBUS/+5V/+5VA breaks USB attach compliance.
14. **Ripple on +3V3A (SOFT ≤ 1 mVpp).** Buck at 1.5 MHz → +5V ripple ~50 mVpp; FB701 + 1–2 µF
    ≈ −20 dB; LP5907 PSRR ≈ −40 dB at 1.5 MHz → 50 mV × 0.1 × 0.01 = 0.05 mVpp ✓.
15. **THS4551 supply slew ≤ 1 V/µs (abs max).** LP5907 soft start (~0.1 ms for 3.3 V →
    0.03 V/µs) ✓. Do not power THS4551 from a hard-switched rail.
16. **LP5907 output capacitance ≤ 10 µF (v).** +3V3A total ≈ 8.5 µF as specified.
17. **Thermal.** TLV75712: (3.3 − 1.2) × 0.1 A = 0.21 W (SOT-23-5, ~+42 °C); LP5907:
    (5.25 − 3.3) × 0.088 = 0.17 W (~+35 °C); ADS5231 0.38 W × 42.8 °C/W = +16 °C. All < 125 °C at 50 °C ambient.

## Layout / EMI

18. **4 layers: SIG / GND / PWR / SIG.** Needed for TQFP-144 escape, SDRAM 80 MHz bus, USB
    90 Ω differential pair and a continuous ground under the AFE.
19. **AFE isolation.** Place each channel's AFE as a straight line BNC → ADC on the analog side;
    FPGA/SDRAM/FT232H/buck on the other half; no digital traces over the AFE. The ATT, SKx2 and
    FDA input nodes are high-impedance — guard with ground pour, keep < 10 mm.
20. **Stopband floor.** 80 dB at 5–40 MHz in simulation assumes ideal op-amp Zout; on the board
    the floor is set by capacitive feedthrough around the filter (BNC to ADC). Keep each
    channel's chain compact and away from CLK/SDRAM traces.
21. **ADC digital outputs.** 24 lines switching at 10 MHz next to the ADC: RN301–RN306 (33 Ω)
    at the ADC pins; VDRV on its own ferrite-fed rail.
22. **USB.** 90 Ω diff, ESD U501 at the connector, length-matched DP/DM, no stubs.
23. **Buck.** Hot loop C601–U601–L601 tight; buck at the far edge from the AFE.

## Timing / logic

24. **Spartan-6 clocking.** PLL_BASE needs CLKIN ≥ 19 MHz: from the 10 MHz clock use DCM_SP CLKFX
    (M = 8, D = 1 → 80 MHz). CLK10_FPGA, FT_CLKOUT (60 MHz) and ADC_DVA must land on GCLK pins.
25. **ADC capture timing.** ADS5231 6-cycle latency; capture data with DVA or with CLK10 phase
    shifted in the DCM (gateware). 100 ns period gives ample margin.
26. **SDRAM.** 40 MB/s vs ~144 MB/s usable at 80 MHz; refresh every 15.6 µs (< 1 % overhead).
27. **FT232H sync FIFO.** 60 MHz CLKOUT, FPGA must meet tSU/tH of the FT245 sync interface;
    keep FT_* traces < 50 mm, same bank as FT_CLKOUT. EEPROM must be programmed to 245 FIFO
    once (host tool), else only async/UART modes work.
28. **Power-up states.** HSWAPEN high disables pre-config pull-ups; pull-ups on FT_RD_N/WR_N/OE_N,
    SD_CS_N; pull-down on SD_CKE; pull-downs on ADC SEL/SEN/SCLK/SDATA keep every device idle until
    the FPGA is configured.
29. **I/O budget.** 92 of 102 FPGA I/O used → 6 spare (plus 4 strap/config pins). Adding
    features (e.g. SD_A12 for the 32 MB SDRAM) consumes spares.

## Sourcing / supply

30. ADS5231 stock 152 (< 500 → WARN; single source) — buy early; alternate is 2× AD9235BCPZ-40
    with an `adc` block rework. LCMXO2/ICE40 are not drop-in for the FPGA.
31. All ICs are JLC Extended → per-part assembly fee; BNCs, headers are through-hole.
