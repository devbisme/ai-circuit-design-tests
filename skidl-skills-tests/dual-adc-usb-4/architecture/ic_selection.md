# IC selection — dual_adc_usb

Stock and price figures come from the JLCPCB mirror (`scripts/stock-check.py`, pcbparts `jlc_search`) on
2026-09-10. They are snapshots, and EOL/NRND status was **not** checked. The sourcer must re-verify.
Spec figures come from the vendor datasheets named in each section.

Each block lists its candidates, the recommendation, why it won, and one line on why each loser lost.

---

## 1. ADC — the part that shapes everything else

Constraint: 2 ch, 12 bit, ≥ 10 MSPS, simultaneous sampling (F1, F3–F5 HARD), in stock at JLCPCB.
Most Western 12-bit pipeline ADCs have fewer than 100 units there, so stock decided the shortlist.

| Candidate | Ch | Rate | Out | Power | JLC stock / price | Verdict |
|---|---|---|---|---|---|---|
| **ADS5231IPAGT** (TI) | 2 | 40 MSPS (PLL on: 20–40; PLL off: 2–30) | parallel 3.3 V CMOS, 2×12 b | 321 mW typ @ 40 MSPS | 160–235 / $30.0 | **Selected** |
| AD9235BCPZ-40 ×2 (ADI) | 1 | 40 MSPS | parallel CMOS | ~180 mW each | 151 / $25.3 ea | Two packages cost $50.5 vs $30; the two references are unmatched; LFCSP with an exposed pad |
| AD9237BCPZ-40 ×2 | 1 | 40 MSPS | parallel CMOS | — | 211 / $32.8 ea | $65 for two channels |
| AD9238BSTZ-20/-40 (ADI, dual) | 2 | 20/40 | parallel | 180 mW | 0 | Not stocked |
| ADS4222, ADC3221, ADS5232, AD9226, LTC2225 | — | — | — | — | 1–88 | Stock below 100 (fails the rule) |

**Why ADS5231:** it is the only in-stock *dual*. One die with one shared reference gives inherent simultaneous
sampling and matched channel gain (F5). It is also the cheapest per channel ($15/ch). Its SNR is 70.7 dB
(about 11.4 ENOB), which clears F11 with margin. It has a VCM output (1.5 V, ±2 mA) that sets the driver
common mode directly. Its CMOS outputs run from the 3.3 V VDRV supply and connect straight to the FPGA's
3.3 V banks. The TQFP-64 has no hidden exposed pad, so it is easy to inspect at JLC.
Source: TI SBAS295A (ADS5231 datasheet), pp. 2–5, 12, 18–19.

**Operating mode (decided):** run the ADC at **20 MSPS, PLL enabled (the datasheet default)**, and have
the FPGA decimate 2:1 to 10 MSPS/ch.
- Options considered: (a) a 10 MHz clock with the PLL disabled over the serial interface (the minimum
  with PLL on is 20 MSPS, datasheet p. 3; PLL-off mode needs a 45–55 % clock duty cycle);
  (b) **20 MHz, PLL on, 2× oversample + digital decimation**.
- (b) wins on three counts. It keeps the ADC in its fully characterised default mode. Oversampling moves
  the alias band from 5–15 MHz up to 15–25 MHz, where the 2nd-order analog filter gives ≥ 14 dB instead
  of about 4 dB; the digital half-band filter handles 5–10 MHz. It also removes the dependence on a
  serial-register write at boot.
- The serial pins (SEL/SEN/SCLK/SDATA) are still wired to the FPGA, so (a) is a BOM-only fallback: swap
  X1 for 10 MHz and have the gateware disable the PLL. No schematic change is needed.

**Second source:** none drop-in. Fallback is AD9235BCPZ-40 ×2 (different footprint, needs an
architecture rework). Flag ADS5231 as **single-source, critical path**.

---

## 2. Capture logic + sample buffer — FPGA

Constraints: 16 k samples/ch buffer (HARD F13), i.e. 16 384 × 24 bit = **384 kbit** of on-chip RAM;
about 44 I/O at 3.3 V (ADC 24 bits plus FT232H 14 plus clocks); an in-stock QFP/QFN package.

| Candidate | LUT | RAM | 3.3 V I/O | Extra | JLC stock / price | Verdict |
|---|---|---|---|---|---|---|
| **GW1NR-LV9QN88PC6/I5** (Gowin) | 8640 | 468 kbit BSRAM + **64 Mbit PSRAM** (in-package) | 48 (banks 1+2) + 22 @ 1.8 V (bank 3) | internal config flash; open toolchain (Apicula/nextpnr-himbaechel) and Gowin EDA | 182 / $20.9–23.3 | **Selected** |
| GW1N-LV4QN88C6/I5 | 4608 | 180 kbit | ~70 | — | 114 / $15.8 | 180 kbit < 384 kbit, fails the HARD buffer |
| ICE40UP5K-SG48I (Lattice) | 5280 | 1 Mbit SPRAM | 39 total | needs external SPI flash | 479 / $9.5 | 39 I/O < 44 needed; slow fabric for 60 MHz FIFO |
| ICE40HX4K-TQ144 | 3520 | 80 kbit | 107 | ext flash | 56 / $18.7 | RAM too small, stock < 100 |
| 10M08SAE144C8G (MAX10) | 8k | 378 kbit | 101 | single 3.3 V | 1 / $47 | Stock, cost, and RAM just short |
| GW1N-LV9QN88 (no PSRAM) | — | — | — | — | 0 | Not stocked |

**Why GW1NR-9:** it is the only stocked part that holds the 16 k/ch buffer on chip (384 of 468 kbit
BSRAM). Its 64 Mbit in-package PSRAM (8 MB, about 280 ms of elastic buffer at 30 MB/s) is what makes
gap-free streaming (SOFT) plausible across USB host scheduling stalls. It also gives ≥ 2 M-sample/ch deep
capture as a bonus. With internal flash it needs no config-flash part. Source: Gowin DS117 v3.2.5 Table 1-1;
UG803 v1.6.5 (QN88P pinout).

**Constraints this imposes (fixed; the sourcer must not substitute):**
- QN88P **bank 3 is fixed at 1.8 V** (VCCIO3 powers the internal PSRAM, UG803 p. 5) and holds JTAG,
  MODE0/1, RECONFIG_N, and JTAGSEL_N. JTAG is therefore 1.8 V, and the JTAG header carries VREF = 1.8 V.
- VCCX/VCCIO0 are tied internally and must be at ≥ 2.375 V, so they go to 3.3 V. VCC core is 1.2 V (LV).
- Only 48 I/O are 3.3 V-capable. The ADC and FT232H use 47 of them, plus one spare (see `net_plan.md` pin map).
  Slow signals (LEDs, trigger, GPIO) go out on bank 3 through single-supply translators.
- Rails: 1.2 V (VCC), 1.8 V (VCCIO3), 3.3 V (VCCX/VCCIO0/1/2).

Single-source (Gowin); stock 182 is WARN (< 500). Flag it.

---

## 3. USB 2.0 High-Speed bridge

Constraint: HS 480 Mb/s (HARD I2); 30 MB/s packed payload for streaming (SOFT); ≤ 16 FPGA pins.

| Candidate | Bus to FPGA | FPGA pins | Firmware | Throughput | JLC stock / price | Verdict |
|---|---|---|---|---|---|---|
| **FT232HL-REEL** (FTDI) | 8-bit 245 sync FIFO, 60 MHz | **14** | none (EEPROM config; D2XX/libftdi host) | "up to 40 Mbytes/s" (DS_FT232H p. 1) | 2353 / $11.3 | **Selected** |
| CY7C68013A-56LTXC (FX2LP) | 16-bit slave FIFO, 48 MHz | ~24 | 8051 firmware required | ~35–42 MB/s | 2624 / $10.7 | Needs 24 FPGA pins; the 3.3 V banks have only 1 spare |
| CH32V307VCT6 (HS PHY MCU) | DVP/FSMC | — | full MCU firmware | unproven at 30 MB/s | 40 / $4.9 | Stock < 100; firmware-heavy |
| STM32F723 + HS PHY | DCMI | — | full firmware | ~30 MB/s | 0 | Not stocked |
| FT2232H / FT601 | — | — | — | — | — | FT2232H sync FIFO disables channel B (no gain); FT601 is USB 3, excluded by SPEC decision 4 |

**Why FT232H:** it uses the fewest FPGA pins (decisive given the 48-pin 3.3 V budget), needs no device
firmware, and its 40 MB/s ceiling exceeds the 30 MB/s packed stream (2 × 12 b × 10 MSPS).
**Streaming verdict:** feasible at 75 % of the bridge ceiling on hosts that sustain ≥ 32 MB/s bulk-in with
large transfers. Not guaranteed on every host. The 8 MB PSRAM FIFO absorbs stalls up to about 280 ms.
Block capture (HARD) is always available. The FT232H must run in 3.3 V-only supply mode (VREGIN = VCCD =
3.3 V, DS_FT232H §6), and the sync-FIFO mode is set in its EEPROM (93LC56B).

---

## 4. Analog front end — input buffer (after the 10:1 attenuator)

Needs: pA-level bias current (it sees a 90 kΩ source); ±1.1 V swing about ground; slew ≥ 31 V/µs
(1 V at 5 MHz); unity-gain stable; ±2.5 V supply.

| Candidate | GBW / SR | Input range on ±2.5 V | Ib | Iq | Stock / price | Verdict |
|---|---|---|---|---|---|---|
| **OPA354AIDBVR** | 100 MHz / 150 V/µs | RRI, beyond both rails | 3 pA | 5 mA | 3147 / $1.28 | **Selected** |
| OPA356AIDBVR | 200 MHz / 360 V/µs | V− −0.1 … V+ −1.5 V → ≤ +1.0 V | 3 pA | 8.3 mA | 2053 / $0.74 | Positive CM limit +1.0 V clips the +1.1 V overrange |
| OPA365AIDBVR | 50 MHz / 25 V/µs | RRI | 0.2 pA | 4.6 mA | 5960 / $1.51 | 25 V/µs < 31 V/µs: slew-limits a full-scale 5 MHz sine |
| AD8065ARTZ | 145 MHz / 180 V/µs | needs V− < −3 V | 2 pA | 6.4 mA | 3859 / — | Needs ±5 V rails (more power/parts) |

OPA354 source: TI SBOS233H p. 1 (100 MHz GBW, 150 V/µs, 6.5 nV/√Hz, 3 pA, 2.5–5.5 V, RRIO).
Freely substitutable with a pin-compatible SOT-23-5 CMOS RRIO op-amp that meets GBW ≥ 80 MHz,
SR ≥ 60 V/µs, Ib ≤ 50 pA, and a 5 V supply.

## 5. Analog front end — ADC driver (single-ended → differential, level shift, AAF)

| Candidate | BW / noise | Iq | Supply | Pkg | Stock / price | Verdict |
|---|---|---|---|---|---|---|
| **THS4521IDGKR** | 145 MHz / 4.6 nV/√Hz, 490 V/µs | 1.14 mA | 2.5–5.5 V, NRI + RRO | VSSOP-8 | 17 791 / $1.08 | **Selected** |
| THS4551IRGTR | 150 MHz / 3.3 nV/√Hz | 1.37 mA | 2.7–5.4 V | QFN-16 | 765 / $3.57 | Lower noise not needed (front-end noise ≈ 0.07 LSB); 3× the cost; QFN |
| ADA4932-1YCPZ | 560 MHz | 9.6 mA | ±5 V | LFCSP | 181 / — | Power, stock |
| THS4541IRGTR | 850 MHz | 10 mA | — | QFN | 23 | Stock |

It runs on 3.3 V (VA_3V3), so its outputs cannot exceed the ADS5231 absolute-max input range
(−0.3 V … min(3.3 V, AVDD + 0.3 V)). VOCM is driven from the ADS5231 CM pin, as in the datasheet's
Fig. 20. Source: TI THS4521 datasheet p. 1.

## 6. Front-end bipolar supply (±2.5 V)

Options: (a) single-supply level shift in front of the buffer. This is rejected because it makes the BNC
float at the shift voltage and source current into the DUT, which is not scope-like.
(b) An inverting charge pump plus separate LDOs (TPS60403 + negative LDO + positive LDO: 3 ICs).
(c) **LM27762DSSR**: an integrated regulated inverter plus positive and negative LDOs, adjustable ±1.5…±5 V,
±250 mA, 2.7–5.5 V in, 2 MHz fixed switching (TI SNVSAF7C p. 1). Stock 11 277, $0.96.
**(c) selected**: one IC, both rails post-regulated, fixed 2 MHz (only 2 harmonics below 5 MHz, versus a
dense comb from 250 kHz pumps). Set to ±2.5 V (OPA354 limit: 5.5 V total).

## 7. Power tree

**Decision: all-linear from VBUS**, with no switcher except the LM27762's internal, post-regulated
charge pump.
- Options: (A) all LDO; (B) a buck for 3.3 V digital plus LDOs for analog; (C) a buck to 3.8 V then LDOs.
- (A) wins because it removes every in-band (0–5 MHz) switching spur source near a 12-bit ADC. Its cost is
  about 0.8 W of heat and a thinner current margin: **~364 mA worst-case budget (≈ 261 mA typ) vs 450 mA HARD**
  (budget table in `design_risks.md`). (B) would draw about 305 mA. It stays as the documented fallback
  if measured draw exceeds 400 mA.

| Rail | Part | Why it won | Loser (why) |
|---|---|---|---|
| VD_3V3 (≈ 240 mA) | **TLV1117LV33DCYR**, SOT-223, 98 k stock, $0.11 | ~0.2–0.45 V dropout keeps regulation at VBUS = 4.4 V; SOT-223 dissipates 0.46 W | AMS1117-3.3 (Basic tier, but ~1.1 V dropout fails the 4.4 V USB corner); AP2112K-3.3 (SOT-23-5 cannot shed 0.46 W) |
| VA_3V3 (≈ 85 mA, ADC + drivers + XO) | **TPS7A2033PDBVR**, 7 µVrms, 300 mA, 52 k stock | lowest noise; high PSRR | LP5907 (250 mA, similar; less headroom); AP2112K (50 µV noise) |
| VD_1V2 (FPGA core, ≈ 80 mA) | **AP2112K-1.2TRG1**, fed from VD_3V3, 1299 stock | exact KiCad symbol; 600 mA | TLV75512 (stock 443 WARN) |
| VD_1V8 (bank 3 + PSRAM, ≈ 30 mA) | **TLV75518PDBVR**, fed from VD_3V3, 6329 stock | stock | AP2112K-1.8 (stock 86 FAIL) |
| VBUS switch / soft-start | **SY6280AAC**, 233 k stock, $0.10 | adjustable current limit + soft start keeps inrush within spec, P5 | TPS2553DBVR (alt, 3× cost) |

## 8. Small support ICs

| Function | Selected | Stock | Why | Alt |
|---|---|---|---|---|
| USB D+/D−/VBUS ESD | USBLC6-2SC6 | 150 k | HS-rated, ~3.5 pF | TPD2E2U06 |
| VBUS surge TVS | SMF5.0A | 970 k (Preferred) | 5 V standoff | SD05 |
| FT232H config EEPROM | 93LC56BT-I/OT | 25 k | FTDI-supported 93C56 | 93LC46B |
| 1.8 V → 3.3 V outputs (LEDs, trigger, GPIO) | SN74LV4T125PWR | 3.9 k | single-supply translator: VIH 1.35 V at VCC 3.3 V; 4 channels | SN74LVC2T45 ×2 |
| 3.3/5 V → 1.8 V trigger input | SN74LV1T34DCKR | 101 k | runs at 1.8 V; 5.5 V-tolerant input | SN74LVC1T45 |
| Input clamp | BAV199 | 106 k | low-leakage series pair (pA at room temperature) | BAV99 (higher leakage, OK) |
| Sample clock | 20 MHz 3.3 V CMOS XO, 3225 (e.g. SX3M20.000B10F20TNN, 3210 stock) | — | a direct XO keeps jitter at a few ps, far below the 20 ps budget | any 3.3 V CMOS XO specified ≤ 5 ps rms jitter |
