# IC selection — dual_adc_usb (revision 1)

Stock and price are JLCPCB/LCSC figures from `stock-check.py` and pcbparts `jlc_search` on 2026-09-25.
All of these parts are Extended tier. EOL/NRND status was **not** checked by the tool, so phase 3 must confirm lifecycle for every ★ part.
★ = critical path.

## 1. ADC ★ — **ADS5231IPAGT** (TI, dual 12-bit 40 MSPS, TQFP-64, C2670079)
| Candidate | Stock / price | Key specs vs requirement | Verdict |
|---|---|---|---|
| **ADS5231IPAGT** | 235 / $30.03 | Two channels in one die, so simultaneous sampling is inherent. 20–40 MSPS with PLL (2–30 without). SNR 70.7 dBFS at 5 MHz. 3.3 V single supply. Parallel 3 V CMOS output. 321 mW typ / 380 mW max | **Chosen.** One package gives inherent A/B timing match and 0.01 dB gain matching. It is the cheapest option with ≥ 100 stock |
| 2 × AD9235BCPZ-40 | 134 / $25.25 each | 12-bit 40 MSPS, single channel, LFCSP-32 | Lost: $50 per board, two packages whose channel-to-channel skew depends on layout, and stock of 134 only just covers 10 boards (20 parts) |
| 2 × AD9237BCPZ-40 | 208 / $32.76 each | 12-bit 40 MSPS, single channel | Lost: $65 per board and two packages |
| AD9238BSTZ-65 | 3 / $76.5 | dual 12-bit 65 MSPS | Lost: out of stock (3) |

The ADS5231 minimum conversion rate is 20 MSPS with the PLL on, so the ADC cannot simply run at 10 MSa/s. That constraint fixed the **40 MSa/s oversample + ×4 FPGA decimation** architecture (see §8). Second source: none pin-compatible. The fallback is 2 × AD9235BCPZ-40, which means an adc-block redesign.

## 2. Capture engine + memory ★ — **GW1NR-LV9QN88PC6/I5** (Gowin, QFN-88, 64 Mbit PSRAM in package, C5799578)
| Candidate | Stock / price | Key facts | Verdict |
|---|---|---|---|
| **GW1NR-LV9QN88PC6/I5** | 182 / $20.91 | 8.6k LUT, 20 × 18×18 multipliers, 468 kbit BSRAM, 2 PLLs, internal config flash, **2 × 32 Mbit PSRAM (8-bit DDR, 166 MHz) in package**, 71 user I/O (bank 3 is 1.8 V) | **Chosen.** No external RAM or config flash to route. 8 MB ≥ 4 MB required. QFN, not BGA |
| GW2AR-LV18QN88C8/I7 | 168 / $51.19 | 20k LUT, 48 multipliers, 64 Mbit SDRAM in package, 1.0 V core, external SPI flash | Lost: 2.4× the cost, plus an extra flash and a 1.0 V rail, for resources the design does not need |
| LFE5U-25F-6BG256C + W9825G6KH-6 | 321 / $13.53 + 1470 / $6.65 | ECP5 BGA-256 + 32 MB SDR SDRAM on TSOP-54 | Lost: BGA escape on 4 layers, a 16-bit SDRAM bus to route, external config flash |
| MCU (STM32H7/F7 DCMI + FMC SDRAM + HS PHY) | — | DCMI parallel capture is ≤ 14 bit wide | Lost: 2 × 12 bit at 40 MSa/s (24 bits, 960 Mbit/s) exceeds DCMI width. A multiplexed ADC would be needed, and none is stocked |

Arithmetic checks:
- **Depth:** 8 MiB ÷ (2 ch × 2 B × 10 MSa/s) → 0.21 s, against ≥ 0.10 s required. Storing 1 M samples/ch × 2 ch × 2 B → 4.0 MB, which fills 50 % of the PSRAM.
- **Bandwidth:** each die needs 10e6 × 2 B → 20 MB/s. In raw 40 MSa/s mode it needs 80 MB/s. A 120 MHz DDR ×8 die gives 240 MB/s raw, which is ≥ 3× margin at ~60 % burst efficiency.
- **DSP:** a ×4 decimator (half-band 11-tap then 31-tap, symmetric) needs ≈ (3 × 20 + 8 × 10) M → 140 M mult/s per channel. That is 280 M/s in total, or 3.5 multipliers when time-shared at 80 MHz. 20 are available ✓.
- **I/O:** 44 3.3 V signals against ≈ 48 3.3 V-capable I/O on banks 1 and 2 (unverified; see handoff).

## 3. USB 2.0 HS bridge ★ — **FT232HL-REEL** (FTDI, LQFP-48, C51997)
| Candidate | Stock / price | Key facts | Verdict |
|---|---|---|---|
| **FT232HL-REEL** | 2353 / $11.33 | USB 2.0 HS, sync 245 FIFO: 8 bit × 60 MHz, ≈ 35–40 MB/s in practice. No firmware. D2XX/libftdi drivers | **Chosen.** 4 MB → 0.114 s upload at 35 MB/s. Uses 15 FPGA pins |
| CY7C68013A-56LTXC | 2624 / $10.68 | FX2LP with GPIF, 16-bit slave FIFO at 48 MHz, needs 8051 firmware + boot EEPROM | Lost: similar throughput, but needs custom firmware and 19+ FPGA pins, which are not free |
| FT2232HL-REEL | 3313 / $12.43 | Two channels. Channel B is unavailable while A is in sync FIFO | Lost: costs more and adds pins for nothing |
| FT601Q-B-T | 357 / $14.47 | USB 3 with 32-bit FIFO | Lost: needs 32 data pins. FPGA I/O is exhausted |

## 4. Input buffer — **OPA356AIDBVR** (TI, SOT-23-5, C183100)
Buffer input swing is ±1.111 V (FS ±11.21 V × 0.09911). The rails were chosen for this part: VP_AFE = +3.288 V and VN_AFE = −2.012 V, deliberately asymmetric.
| Candidate | Stock / price | Key facts | Verdict |
|---|---|---|---|
| **OPA356AIDBVR** | 2053 / $0.744 | CMOS, IB 3 pA (±50 max), 200 MHz GBW, SR 360 V/µs, 8.3/11 mA, 2.7–5.5 V, unity-gain stable. Input CM (V−) − 0.1 … (V+) − 1.5 V. There is one input pair and no crossover | **Chosen.** CM top at worst = 3.198 − 1.5 → 1.698 V, ≥ 1.111 V with 0.59 V margin. CM bottom = −2.058 − 0.1 or lower, ≪ −1.111 V ✓. Supply at most 5.438 V ≤ 5.5 V ✓. Full-power BW = 360e6/(π × 2.22 Vpp) → 52 MHz ✓ |
| OPA357AIDBVR | 752 / $2.04 | RRIO, 250 MHz, SR 150 V/µs, 4.9 mA. Input-pair transition at (V+) − 1.5 … (V+) − 0.9 V typ, ±0.5 V with process | Lost: the transition region can start at 3.198 − 2.0 → 1.198 V, only 0.087 V above the 1.111 V peak, so crossover distortion is risked near FS. It also costs 2.7× as much and has lower stock. It saves 3.4 mA per rail, but the budget does not need that |
| OPA365AIDBVR | 5960 / $1.51 | 50 MHz, SR 25 V/µs | Lost: full-power BW = 25e6/(π × 2.22) → 3.6 MHz, below 5 MHz |

On symmetric ±2.52 V rails the OPA356 would **fail**: its CM top is 2.52 − 1.5 → 1.02 V, below 1.111 V. That is why VP_AFE is +3.288 V. **Do not substitute a buffer or change the rails without redoing this check.**

## 5. ADC driver (FDA) — **THS4551IRGTR** (TI, VQFN-16, C2869590)
| Candidate | Stock / price | Key facts | Verdict |
|---|---|---|---|
| **THS4551IRGTR** | 765 / $3.57 | 135 MHz GBW, 3.3 nV/√Hz, 1.37 mA, 2.7–5.4 V, input CM (VS−) − 0.1 … (VS+) − 1.2 V | **Chosen.** Input CM needed is 0.521–1.050 V and the allowed range is −0.1…2.1 V ✓. VOCM 1.5 V lies inside 0.65…2.0 V ✓ |
| ADA4940-1ACPZ-R7 | 637 / $8.95 | 260 MHz, rail-to-rail out | Lost: 2.5× the cost with no spec the design needs |
| THS4541IRGTR | 23 / $5.16 | 850 MHz | Lost: stock 23 (FAIL) |

## 6. Bipolar buffer rails — **LM27762DSSR** (TI, WSON-12, C473398)
| Candidate | Stock / price | Verdict |
|---|---|---|
| **LM27762DSSR** | 11277 / $0.96 | **Chosen.** One chip gives low-noise positive and negative LDO outputs (22 µVrms each), 250 mA, from a 2.7–5.5 V input |
| TPS60403DBVR + TPS7A3001DGNR | 10018 / $0.53 + 8199 / $1.57 | Lost: two parts and a higher total cost |
| LTC3260EMSE#TRPBF | 491 / $8.91 | Lost: 9× the cost and thin stock |

## 7. Power regulators
| Function | Chosen | Runner-up — why it lost |
|---|---|---|
| 5 V → 3.3 V and 5 V → 1.2 V buck (×2, same MPN) | **TLV62569DBVR** (108k / $0.073, VFB 0.600 V ±2 %, VIN 2.5–5.5 V, 2 A) | SY8089AAAC: fine, but VFB was not verified from a datasheet this phase. TPS563201: VIN min 4.5 V, above the 4.40 V USB VBUS minimum |
| 3.3 V analog LDO | **TPS7A2033PDBVR** (52k / $0.233, 300 mA, 6.5 µVrms) | LP5907MFX-3.3: 250 mA, which leaves less headroom over the 139 mA worst-case load |
| 1.8 V LDO (PSRAM bank) | **TLV75518PDBVR** (6.3k / $0.234, 500 mA) | XC6206P182MR: 200 mA and higher dropout from 3.3 V. Acceptable as a fallback |
| VBUS load switch (inrush) | **TPS22919DCKR** (35k / $0.138, 1.5 A, controlled rise, ON VIH ≥ 1 V) | SY6280AAC: its datasheet could not be retrieved, so the ISET formula is unverified. AP22804: 2.4× the cost |
| USB ESD | **USBLC6-2SC6** (150k / $0.048) | — |

## 8. Clock ★ — **SX3M40.000B10F20TNN** (SCTF, 40 MHz 3.3 V CMOS XO, 3225, C5452689, 2390 / $0.46)
The jitter budget is set at 5 MHz input: SNRj = −20·log10(2π × 5 MHz × tj).
- 3 ps → 80.5 dB. Combined with the ADC's 70.7 dB that gives 70.27 dB, a loss of 0.4 dB.
- 5 ps → 76.1 dB, giving 69.6 dB combined.

**Requirement: tj ≤ 3 ps rms (12 kHz–20 MHz).** An FPGA PLL output (~50–100 ps) would give ≤ 50 dB, so the ADC is clocked straight from the XO. Alternative: Interquip 1601-40005-BTBEYA (1405 / $0.48, 5032). Pick whichever datasheet states ≤ 3 ps phase jitter and 45–55 % duty cycle.

## 9. Connectors and passive specials
| Function | Chosen | Note |
|---|---|---|
| BNC ×2 | **KH-BNC50-3511** (Kinghelm, 50 Ω right-angle, THT, 4742 / $0.93) | Mechanical strength needs THT. JLCPCB does THT assembly |
| USB-C receptacle | **TYPE-C-31-M-12** (16-pin USB 2.0, 89.8k / $0.186) | Only Rd resistors, no PD controller |
| Divider trimmer ×2 | **LXRW19V330-050** (Murata, 16.5–33 pF, 50 V, 3163 / $0.735) | Knowles JZ300 (5.5–30 pF) lost: stock fell to 7 |
| 12 MHz crystal | **X322512MSB4SI** (YXC, Basic tier, 240k / $0.10) | Confirm its CL before fixing C47/C48 |
| EEPROM | **93LC56BT-I/OT** (25.8k / $0.50) | Required for FT232H 245-FIFO mode |
| Clamp diode ×2 | **BAV199** (low-leakage series pair, SOT-23) | 5 pA typ leakage × 100 kΩ → negligible offset |
