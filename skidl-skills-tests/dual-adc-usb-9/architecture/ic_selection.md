# dual_adc_usb — IC selection (rev 2)

Rev 2: §2 FPGA I/O facts corrected, §2a I/O-budget options, §5 +1V8 regulator, §6 Y1 swapped. <!-- revised: escalation from 04_datasheets -->

Stock/tier data: JLCPCB mirror via `stock-check.py` / pcbparts `jlc_search`, 2026-09-30. Every
JLCPCB IC below is Extended tier (no Basic/Preferred part exists for any of these functions).
Lifecycle checked on DigiKey only where noted.

## 0. System-level trades (user directive: list options, pick one)

| Decision | Options | Pick | Why it won / why others lost |
|---|---|---|---|
| Capture engine | (a) FPGA + memory + USB bridge; (b) MCU w/ HS USB + DCMI/parallel + SDRAM (STM32H7+USB3300, STM32F723, i.MX RT1062) | **(a)** | Deterministic 2×12-bit capture every clock and a logic-level trigger; (b) lost: 24-bit simultaneous input exceeds DCMI's 14-bit width, DMA/bus contention risks dropped samples, RT106x is BGA-only |
| ADC count | (a) one dual simultaneous ADC; (b) two singles on a shared clock | **(a) ADS5231** | Same-die aperture match, one footprint, $30 vs $50 for 2×AD9235-40 |
| Sample strategy | (a) ADC at 10 MSPS, AAF at 5 MHz; (b) ADC at 40 MSPS, analog AAF ~9 MHz + 4:1 digital decimation to 10 MSPS | **(b)** | (a) cannot meet both "≥5 MHz BW" and "anti-alias" (zero transition band; a 5 MHz pole gives ≈0 dB rejection at Nyquist). (b) gives −35.8 dB at the 35 MHz alias edge with −0.16 dB droop at 5 MHz. Also forced: ADS5231 minimum rate is 20 MSPS with PLL on |
| Capture memory | (a) FPGA with in-package PSRAM; (b) FPGA + W9825G6KH SDRAM; (c) QSPI PSRAM (APS6404) | **(a)** | Removes a 54-pin TSOP and ~40 routed nets; 64 Mbit = 0.2097 s ≥ 0.1 s; (c) not stocked at JLC |
| USB link | (a) FT232H 245-sync FIFO; (b) CY7C68013A FX2LP; (c) FT2232H | **(a)** | No firmware, 40 MB/s class, LQFP-48; (b) needs 8051 firmware + I²C EEPROM; (c) channel B is unusable in sync-FIFO mode, larger package |
| Connector | USB-B, mini-B, micro-B, USB-C (2.0 wiring, Rd) | **USB-C** | Budget 1.47 W < 2.25 W so the [HARD] USB-C trigger is *not* fired; connector is a free choice. USB-C is reversible, rugged, a 2167–89k-stock part, and gives headroom (1.5 A hosts) if the estimate grows. Micro-B is a freely substitutable fallback |
| Analog rails | (a) ±3.4 V from LM27762 (LDO + inverting CP); (b) TPS60403 inverter + separate LDOs; (c) single-supply AFE with offset-biased attenuator | **(a)** | One 2×3 mm part, both rails regulated & low-noise; (c) lost: BNC would sit at a DC bias, not a ground-referenced 1 MΩ |

## 1. ADC — `adc_dual`

| Candidate | Key specs (required: 2 ch, 12 b, ≥10 MSPS, simultaneous) | Stock / price | Verdict |
|---|---|---|---|
| **ADS5231IPAGT** (TI) | dual, 12 b, 20–40 MSPS (PLL on), 70.7 dB SNR, 2.02 Vpp diff, VCM 1.5 V, CMOS out, 321 mW typ/380 max, TQFP-64 | C2670079, 235, $30.0, DigiKey **Active** | **Selected** |
| AD9235BCPZ-40 ×2 (ADI) | single, 12 b, 40 MSPS, 70.6 dB, LFCSP-32 | C653327, 134–170, $18.4–25.3 each | Lost: two parts + two QFNs, $37–50, stock < 500; vetted *non-drop-in* fallback |
| AD9238BSTZ-65 | dual 12 b 65 MSPS | C514277, 21, $71 | Lost: stock 21 < 100 |
| LTC2225IUH | single 12 b 10 MSPS | 84 | Lost: stock < 100, two needed |

## 2. FPGA — `fpga`

| Candidate | Key specs | Stock / price | Verdict |
|---|---|---|---|
| **GW1NR-LV9QN88PC6/I5** (Gowin) | 8640 LUT, **64 Mbit PSRAM in package (2×x8 DDR, 1.8 V)**, 20 18×18 mults, 2 PLL, on-chip config flash, 71 user I/O of which **48 are 3.3 V-capable** (bank 1 25, bank 2 23) and 23 are on bank 3 = **VCCO3 1.71–1.89 V** (PSRAM bank, also JTAG/MODE/RECONFIG_N); no READY/DONE bonded; VCC 1.2 V, VCCX 3.3 V, QN88 0.4 mm | C5799578, 182, $20.9 | **Selected** (kept in rev 2: the 1.8 V bank costs one buck, and the I/O shortfall is closed in §2a without dropping a function) <!-- revised --> |
| XC6SLX9-2TQG144C (AMD) | 9152 LC, no large RAM, LQFP-144 | C27408, 1502, $7.3 | Lost: needs external SDRAM + SPI flash + 3 rails; ISE toolchain is legacy |
| iCE40HX4K-TQ144 (Lattice) | 3520 LUT, no DSP | C1521989, **3** | Lost: out of stock, no multipliers for decimation FIR |
| AG10KL144 (AGM) | Cyclone-clone | 476–661 | Lost: toolchain/documentation risk |

## 2a. FPGA I/O budget — 53 planned vs 48 available at 3.3 V <!-- revised: new -->

ADS5231 VDRV ≥ 3.0 V, so the ADC bus cannot move to the 1.8 V bank. Need to shed 5 of 53 (ADC 33, FT245 15, CLK 1, LED 2, TRIG 2).

| Option | Pins freed | Pick? | Why |
|---|---|---|---|
| A. Drop ADC_DVA/DVB, capture on phase-shifted FPGA_CLK40 | 2 | **Yes** | 10.2 ns data window at 40 MSPS gives ≈5 ns margin after U8 skew (net_plan adc_dual); DV is redundant with a synchronous clock |
| B. Drop ADC_OVRA/OVRB, flag saturated codes 0x000/0xFFF in gateware | 2 | **Yes** | Over-range clips the code, so OVR adds no information beyond a 1-code ambiguity |
| C. Tie FT SIWU# to VCCIO | 1 | **Yes** | DS_FT232H allows it; short packets flush on the host-set latency timer — irrelevant for MB-sized block readout |
| D. Tie ADC_OEB low | 1 | Reserve | Point-to-point bus never needs tri-state; kept on the FPGA to leave the settled ADC control set intact. First pin to take if a new 3.3 V signal is ever needed |
| E. Move FPGA_CLK40 to bank 3 (U8 on +1V8) | 1 | No | LVC1G34 tpd spread at 1.8 V is roughly twice its 3.3 V spread, eating most of the 10.2 ns capture window once DV is gone |
| F. LEDs on bank 3, sinking from 3V3D | 2 | No | 1.5 V across an "off" LED ghost-glows and back-feeds the 1.8 V pin clamp when tri-stated |
| G. Trigger on bank 3 (LVCMOS18) | 2 | No | 3.3 V external trigger sources would over-drive the pin; needs two level-shifter ICs |
| H. Level-translate the ADC bus into bank 3 | ≥ 5 | No | 2–4 translator ICs, added skew at 40 MHz |
| I. Larger package (GW1NR-9 LQ144P) | — | No | Re-opens the settled FPGA/critical-path choice and footprint |

Result: A+B+C → **48 of 48** 3.3 V I/O; pin map fixed in `net_plan.md` §2 fpga.

## 3. USB bridge — `usb_bridge`

| Candidate | Key specs | Stock / price | Verdict |
|---|---|---|---|
| **FT232HL-REEL** (FTDI) | USB 2.0 HS, 245 sync FIFO 60 MHz, 8-bit, LQFP-48 | C51997, 2353, $11.3 | **Selected** |
| CY7C68013A-56LTXC | FX2LP, 16-bit slave FIFO | C14912, 2624, $10.7 | Lost: firmware + QFN; keep as redesign fallback |
| FT2232HL-REEL | dual channel | C27882, 3313, $12.4 | Lost: no benefit in sync-FIFO mode |
| FT232HQ-REEL | QFN-48 variant | C82158, 86 | Lost: stock < 100 |
EEPROM: **93LC56BT-I/OT** (C190271, 25 777) — FTDI's documented part.

## 4. Analog front end — `afe_ch_a/b`

| Function | Candidate | Key specs | Stock | Verdict |
|---|---|---|---|---|
| Buffer | **OPA810IDBVR** | FET in, 2 pA Ib, 70 MHz GBW / 140 MHz UGBW, unity-gain stable, 4.75–27 V, RRIO, 4.6 mA max | 3280 | **Selected** |
| | AD8065ARTZ-REEL7 | FET, 145 MHz, 5–24 V, not RR input | 3859 | Lost: input range not rail-to-rail; second source (pin-compatible SOT-23-5 — verify pinout) |
| | OPA356AIDBVR | CMOS, 5.5 V max | 2053 | Lost: 5.5 V max supply, input CM ≤ V+−1.5 V |
| FDA | **THS4521IDGKR** | 145 MHz, 1.25 mA max, RRO, 2.5–5.5 V, VOCM 0.8–2.3 V, MSOP-8 | 17 791, $1.08 | **Selected** |
| | THS4551IRGTR | 150 MHz, lower offset, QFN-16 | 765, $3.57 | Lost: QFN, 3× price, offset is calibrated out anyway |
| Clamp | **BAV199** (or BAV199LT1G) | low-leakage series pair, SOT-23 | 106 k | Selected |
| Trimmer | **STC3MA06-T1** (SEHWA) | 2–6 pF, 100 V, 4.5×3.2 mm | 1377–4521 | Selected (Knowles JZ060 2–6 pF second source, stock 75) |
| BNC | **KH-BNC50-3511** | 50 Ω right-angle THT | 5725 | Selected; DOSIN-801-0038 (3306) second source |

## 5. Power

| Function | Candidate | Key specs | Stock | Verdict |
|---|---|---|---|---|
| Load switch | **TPS22918DBVR** | 1–5.5 V, 2 A, 52 mΩ, CT rise-time, ON VIH 1.0 V | 44 958 | Selected (inrush 55 mA) |
| 3V3D & 1V2 bucks | **TLV62569DBVR** ×2 | 2.5–5.5 V in, 2 A, VFB 0.600 V (0.588–0.612), 1.5 MHz, tSS 900 µs, EN VIH ≤1.2 V | 108 275 | Selected — one part number for both rails; AMS1117-1.2 lost (2.1 V drop ×150 mA = 0.32 W wasted from the USB budget) |
| **+1V8 (VCCO3)** <!-- revised: new --> | **TLV62569DBVR** (3rd, U12) | VBUS_SW → 1.8 V, 200k/100k on VFB 0.600 V → 1.800 V (1.741–1.861 V), tSS 800 µs | 108 275 | **Selected**: same MPN as U3/U4 (no new part to source); 0.220 W from VBUS at 100 mA keeps the budget at 496 mA ×1.25 @4.4 V |
| | TLV75718PDBVR LDO from +3V3D | 1 A fixed 1.8 V, 3 parts | — | Lost: draws 100 mA through the 3V3D buck → 0.378 W; budget 541 mA ×1.25 @4.4 V > 500 mA |
| | LDO from VBUS_SW | (5.25−1.8)×0.1 = 0.345 W dissipated | — | Lost: 0.53 W from VBUS and θJA heat in SOT-23 |
| 3V3A LDO | **TLV75733PDBVR** | fixed 3.3 V, 1 A, dropout ≤ 300–425 mV, EN VHI 1.0 V | 194 991 | Selected; TLV75733PDRVR (WSON, better θJA) is a drop-in-electrical alternative |
| ±AFE | **LM27762DSSR** | 2.7–5.5 V in, ±1.5…±5 V, 250 mA, VFB+ 1.2 V, VFB− −1.22 V, 2 MHz CP | 11 277 | Selected; LM27761 (neg only) + TLV757P lost on part count |
| VBUS ESD | **USBLC6-2SC6** | 2-line + VBUS | 150 192 | Selected |
| PTC | 0.75 A hold 1206 (e.g. SMD1206P075TF) | | sourcer | 0.5 A (SMD1206P050TF) rejected: derates to ≈0.35 A at 70 °C vs 0.32 A load |

## 6. Clock

| Function | Candidate | Notes | Verdict |
|---|---|---|---|
| 40 MHz XO <!-- revised: K8 --> | **OT322540MJBA4SL** (YXC YSO110TR, 3225, CMOS, 1.8–3.3 V, ±10/±20 ppm) | C2831396, stock 10 567, $0.55; **0.7 ps rms max (12 k–20 MHz) published**, 5 mA, OE pin 1 | **Selected**: published jitter 7× under the 5.04 ps budget; same 4-pin 3225 pinout as the old part; highest stock |
| | TAITIEN OXETGLJANF-40.000000MHZ (3225) | C7470494, 928; 1 ps rms max published, 15 mA | Second source (lost on stock and current) |
| | Seiko Epson X1G0041710150 (SG-210STF, 2520) | C256001, 910; phase noise only (−161 dBc/Hz floor), no jitter figure | Lost: jitter must be derived, 2520 footprint |
| | SX3M40.000B10F20TNN (SCTF, rev 1 pick) | C5452689, 2262; **no jitter published** (K8) | Lost: unverifiable against the SNR requirement |
| FPGA clock buffer | SN74LVC1G34 (SOT-23-5/SC-70) | single non-inverting LVC buffer | Selected; 74LVC1G125GW (OE tied low) substitute |
| FT232H crystal | **X322512MSB4SI** (YXC 12 MHz 3225) | Basic tier, 240 k | Selected |
