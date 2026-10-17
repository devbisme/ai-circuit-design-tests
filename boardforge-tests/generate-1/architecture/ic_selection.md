# IC selection — dual_adc_10msps

Stock/price: pcbparts MCP (live JLCPCB), queried 2026-10-16. All candidates below are JLC
**Extended** (no Basic/Preferred part exists in these categories). "Fail" = stock < 100.

## ADC (block `adc`)

| Candidate | Key specs vs requirement | LCSC / stock / price | Verdict |
|---|---|---|---|
| **ADS5231IPAGT** (TI) | Dual 12-bit, one CLK pin → simultaneous; 2–30 MSPS with PLL disabled (serial reg), 70.7 dBFS SNR, 2.02 Vpp diff, CM output 1.5 V, 3.3 V single supply, 321 mW, TQFP-64 | C2670079 / 152 / $29.81 | **Chosen** |
| AD9235BCPZ-40 ×2 (ADI) | Single 12-bit 40 MSPS, 70.6 dB, LFCSP-32 | C653327 / 132 / $24.37 each | Loses: two packages ($48.7), two clock loads, QFN with EP, no shared CM pin |
| LTC2225IUH ×2 | Single 12-bit 10 MSPS, 71.3 dB | C679583 / 84 / $24.14 | Loses: stock < 100 |
| AD9238BSTZ-65 | Dual 12-bit 65 MSPS | C514277 / 18 / $69.85 | Loses: stock 18, price |

Why ADS5231 won: the only in-stock dual-in-one-package part — one clock pin gives truly
simultaneous sampling, and its CM output sets both FDAs' VOCM. **Keystone:** at 10 MSPS the
internal clock PLL must be disabled over the serial interface (PLL-enabled range is 20–40
MSPS); duty cycle must be 45–55 % (XO + LVC buffer gives ~50 %). Second source: 2× AD9235BCPZ-40
(needs an `adc` block rework — not drop-in).

## FPGA (block `fpga`)

| Candidate | Key specs | LCSC / stock / price | Verdict |
|---|---|---|---|
| **XC6SLX9-2TQG144C** (AMD) | 9152 LC, 576 Kb BRAM, 16 DSP48A1, 2 CMT, 102 I/O, TQFP-144; 1.2 V core, 3.3 V aux/IO; KiCad symbol via pin-compatible XC6SLX4-TQG144 | C27408 / 1678 / $7.37 | **Chosen** |
| LCMXO2-4000HC-4TG144C (Lattice) | 4320 LUT, 92 Kb EBR, 114 I/O, single 3.3 V, internal flash | C1521625 / 139 / $18.11 | Runner-up — loses: no KiCad symbol (144-pin generation risk), 2.5× price, ¼ the RAM, stock barely over 100 |
| GW1NR-LV9QN88PC6/I5 (Gowin) | 8640 LUT + 64 Mbit in-package PSRAM (no SDRAM) | C5799578 / 164 / $23.37 | Loses: no symbol, QFN-88 0.4 mm, proprietary PSRAM IP |
| ICE40HX4K-TQ144 (Lattice) | 3520 LUT, open toolchain, symbol exists | C1521989 / 32 / $17.05 | Loses: stock 32 |
| EP4CE6E22C8N (Intel) | 6272 LE, 91 I/O | C36238 / 211 / $28.79 | Loses: 91 I/O < 92 needed, price, 2.5 V PLL rail |

I/O need 92 (see net plan). Second source: XC6SLX4-2TQG144C (same pinout, fewer LCs — enough
for this gateware) if LX9 stock fails.

## Capture memory (block `sdram`)

| Candidate | Specs | LCSC / stock / price | Verdict |
|---|---|---|---|
| **W9812G6KH-6** (Winbond) | 128 Mbit (16 MB) ×16 SDR, 166 MHz, exact KiCad symbol | C62379 / 1241 / $6.10 | **Chosen**: 16 MB = 4 M samples/ch = 0.42 s (need 0.1 s) |
| W9825G6KH-6 | 256 Mbit (32 MB), same TSOP-II-54 pinout + A12 on pin 36 | C62246 / 6659 / $5.90 | Vetted second source (drop-in; route A12 if used) |
| APS6404L QSPI PSRAM ×2 | 8 MB each, 6 pins | — | Loses: 8 µs CE# limit complicates 20 MB/s/ch writes |

Bandwidth: 40 MB/s needed vs 160 MB/s peak at 80 MHz ×16 bit.

## USB bridge (block `usb_fifo`)

| Candidate | Specs | LCSC / stock / price | Verdict |
|---|---|---|---|
| **FT232HL** (FTDI) | HS USB, 245 sync FIFO 60 MHz ×8 (~35–40 MB/s), no firmware, LQFP-48, KiCad symbol | C51997 / 2262 / $9.51 | **Chosen** |
| FT2232HL | Dual channel; ch B unavailable while ch A in sync FIFO | C27882 / 388 / $12.38 | Loses: price, pins, no benefit in sync mode |
| CY7C68013A FX2LP | 16-bit GPIF, 8051 firmware | not stocked | Loses: firmware + not stocked |
| STM32H7 + USB3300 ULPI | see block_diagram options | — | Loses: no 24-bit simultaneous capture path |

Requires 93LC56B EEPROM (U902) programmed to 245-FIFO mode, 12 MHz crystal, 12 kΩ REF.

## Front-end amplifiers (block `afe_channel`)

| Role | Candidate | Specs | LCSC / stock / price | Verdict |
|---|---|---|---|---|
| Buffer + SK_a (dual) | **OPA2810IDR** | FET input 2 pA (on a 47 kΩ Thevenin node), 70 MHz GBW, RRIO, no phase reversal, 4.75–27 V, HD2/HD3 −99/−104 dBc @1 MHz | C1849413 / 4319 / $2.57 | **Chosen** |
| | AD8066ARZ | FET, 120 MHz | C578621 / 49 | Loses: stock |
| | OPA2836IDR | 205 MHz but bipolar 650 nA (×47 kΩ = 31 mV offset), max 5.5 V supply < 8 V rails | C1848153 / 44 | Loses: Ib, supply, stock |
| SK_b (single, Q 2.28) | **OPA810IDBVR** | same die family as OPA2810, 70 MHz, SOT-23-5, symbol `OPA810xDBV` | C2833513 / 3036 / $3.09 | **Chosen** — own package per channel keeps channels out of a shared die (OPA2810 crosstalk −93 dBc @100 kHz, worse at 1 MHz) |
| SE→diff + MFB | **THS4551IRGTR** | FDA 135 MHz, 3.3 nV/√Hz, RRO, 2.7–5.4 V → runs from +3V3A so ADC inputs can never exceed AVDD | C2869590 / 1357 / $4.85 | **Chosen** |
| | ADA4940-1 | 260 MHz FDA | not stocked | Loses: availability |
| | LTC6362 | 34 MHz | — | Loses: GBW too low for 1.1 MHz MFB |

Topology decision (anti-alias): **7-pole Butterworth-type** (SK Q0.78 + SK Q2.28 + MFB Q0.59
+ RC) chosen over 5-pole Chebyshev 0.1 dB (the first design). Both meet the HARD 72 dB at
5 MHz nominally (77 vs 81 dB), but the Chebyshev needed a Q = 3.28 stage at the band edge:
Monte-Carlo (R ±1 %, C ±5 %, GBW ±30 %) gave passband flatness median 0.52 dB / p99 1.73 dB
(SOFT ±0.5 dB fails on half the boards) vs 0.28 / 1.05 dB for the 7-pole (0.16 / 0.61 dB with
±2 % C0G). Cost: one OPA810 + 4 passives per channel. The Q 3.28 stage in an MFB was
rejected outright (needs C1/C2 ≈ 85 → loop gain ≈ 1.4 at f0 on a 135 MHz FDA).

Attenuator ratio decision: ÷20 (953 k / 49.9 k) instead of ÷10, because the SK_b output peaks
at 2.24× its input near 1.23 MHz: with ÷10 a full-scale signal reaches ±2.2 V, beyond the
OPA810 JFET input range (V+ − 2.5 V = +1.5 V on +4 V rails) → crossover distortion. With ÷20
the peak is ±1.11 V (±1.25 V at the 11.2 V overrange). Gain is made up by the FDA (G 1.82).

## Power

| Rail | Candidate | Specs | LCSC / stock / price | Verdict |
|---|---|---|---|---|
| ±4.0 V analog | **LM27762DSSR** | inverting CP + ±LDOs, 250 mA each, 22 µVrms, VFB+ 1.200 V / VFB− −1.220 V, WSON-12 | C473398 / 41441 / $0.96 | **Chosen** |
| | TPS65131 boost/inverter + 2 LDOs | ±15 V capable | — | Loses: inductors, more noise, 3 ICs |
| +3V3A (ADC AVDD, FDA) | **LP5907MFX-3.3/NOPB** | 250 mA, 6.5–10 µVrms, 82 dB PSRR @1 kHz, fixed (no divider) | C80670 / 51190 / $0.16 | **Chosen** |
| | TPS7A2033 | 300 mA, lower noise | no KiCad symbol | Loses: symbol |
| +3V3 digital | **TLV62569DBVR** | 2 A buck 1.5 MHz, VFB 0.600 V, SOT-23-5, exact symbol | C141836 / 460465 / $0.07 | **Chosen** |
| | LDO from 5 V | — | — | Loses: (5 − 3.3) × 0.36 A = 0.61 W heat |
| +1V2 (VCCINT) | **TLV75712PDBVR** | 1 A fixed 1.2 V, SOT-23-5, exact symbol | C1509296 / 5075 / $0.28 | **Chosen** |
| | AP2112K-1.2TRG1 | 600 mA | C460310 / 59 | Loses: stock |

## Clock

| Candidate | Specs | LCSC / stock | Verdict |
|---|---|---|---|
| **SX3M10.000B10F20TNN** 10 MHz 3.3 V CMOS XO 3225 | ±10 ppm | C5452682 / 1999 / $0.34 | **Chosen** (any 3.3 V CMOS 10 MHz XO, jitter ≤ 5 ps rms, is a free substitute) |
| **SN74LVC2G34DBVR** dual buffer (fan-out to ADC + FPGA) | 74LVC, SOT-23-6 | C7394039 (UMW) / 47898 | **Chosen** (free substitute among LVC2G34 makers) |

Ruled out: clocking the ADC from an FPGA pin/PLL (Spartan-6 PLL jitter ~100+ ps vs. the
32 ps needed for a 74 dB jitter SNR at 1 MHz).
