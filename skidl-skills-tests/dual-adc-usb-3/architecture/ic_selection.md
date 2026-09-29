# IC selection — dual_adc_usb

Stock, price and tier below are live JLCPCB/LCSC figures pulled during architecture
(2026-09-09). The `pcbparts` MCP was **not connected**; figures come from the open JLCPCB
parts mirror (`jlcsearch.tscircuit.com`) plus LCSC/JLCPCB product pages. **The part-sourcer
must re-verify every one of them** — they are the reason a part won, not a substitute for
sourcing.

Every part below is JLCPCB **Extended** tier unless marked otherwise. Nothing in this design
exists at Basic tier; a 12-bit 10 MSPS front end has no jellybean parts.

---

## 1. Digitizer — `adc_pair`

Requirement drivers: F1 (2 ch simultaneous), F3 (10 MSPS), F4 (12 bit), P2 (450 mA total),
X4 (no BGA below 0.8 mm).

| candidate | topology | stock | unit $ | power | verdict |
|---|---|---|---|---|---|
| **AD9235BCPZ-40** (LFCSP-32, 5×5) | 2× single, shared clock, parallel CMOS | 170 | 18.41 | ~60 mW ea @ 10 MSPS | **selected** |
| AD9629BCPZRL7-40 (LFCSP-32) | 2× single, parallel CMOS or LVDS | 173 | 13.53 | 66 mW ea @ 40 MSPS | rejected |
| AD9238BCPZ-20 (LFCSP-64) | true dual in one package | **7** | 35.70 | 300 mW | rejected |
| AD9226ARSZ (SSOP-28) | 2× single, parallel CMOS | 88 | 61.15 | 475 mW ea | rejected |
| AD9235BRUZ-20 (TSSOP-28) | 2× single | **12** | 35.55 | 90 mW ea | rejected |

**Why AD9235BCPZ-40 won.** It is pin-strapped — no SPI, no configuration state for firmware
to get wrong, so the netlist alone fully determines the part's behaviour. One 3.0 V analog
supply (no extra rail), and its common mode of AVDD/2 = 1.50 V sits comfortably mid-range
for a THS4551 running on ±4.2 V. Running a 40 MSPS grade at 10 MSPS costs nothing: pipeline
ADC supply current scales with clock, so the -40 draws roughly what a -20 draws at half rate.

**Why AD9629 lost:** $5/ch cheaper and genuinely lower power, but its output format and
default state are set over SPI, and it needs a separate **1.8 V analog rail** with a 0.9 V
common mode. Two new unknowns and one new rail to save $10/board on a $180 budget that is
already 45 % unused. Not worth it.

**Why AD9238 lost:** topologically the *right* answer — one package, one clock, guaranteed
zero inter-channel skew. 7 units in stock. Cannot build five boards. If it ever restocks it
is the preferred re-architecture.

**Why AD9226 lost:** 5 V supply (forces a boost rail and a 2.5 V input common mode) and
475 mW *each* — 950 mW of the 2.25 W total budget for the converters alone, plus $122 for
the pair. Fails P2 and N3 simultaneously.

Same-footprint second sources (LFCSP-32, drop-in): **AD9235BCPZ-20** (28 in stock) and
**AD9235BCPZ-65** (4). Combined same-footprint stock 202. The TSSOP-28 AD9235BRUZ-xx is
**not** a footprint swap — different pin count.

Simultaneity is achieved by driving both CLK pins from the two halves of a single
SN74LVC2G34, giving < 1 ns inter-channel skew against a 100 ns budget (F10).

---

## 2. Capture engine and buffer — `fpga_capture`

Requirement drivers: I6 (bit-packing before the endpoint), F12a (lossless full-rate burst),
X4 (no BGA below 0.8 mm pitch).

| candidate | packing | burst buffer | pins | stock | unit $ | verdict |
|---|---|---|---|---|---|---|
| **GW1NR-LV9QN88PC6/I5** (QFN-88, 0.4 mm) | in fabric | **64 Mbit PSRAM in package** = 2.8 Mpt/ch | 71 I/O | 102 | 20.91 | **selected** |
| GW1N-LV4QN88C6/I5 + W9825G6KH-6 | in fabric | 32 MB external SDRAM | 71 I/O − 39 for SDRAM | 151 / 1470 | 13.48 + 6.65 | rejected |
| GW2AR-LV18QN88C8/I7 (QFN-88) | in fabric | 64 Mbit PSRAM in package | 71 I/O | 168 | 51.19 | **escalation second source** |
| FX2LP alone, no logic | not possible | 4 kB FIFO | — | — | — | rejected |
| STM32H7/F723 + ULPI PHY | in software | ≤ 1 MB internal SRAM | LQFP-176 | — | ~12 | rejected |
| CYUSB3014 (FX3) | in GPIF II | external | BGA-121, 0.65 mm | — | — | rejected |
| Lattice iCE40UP5K | in fabric | 128 kB SPRAM = 42 kpt/ch | SG48 | — | ~5 | rejected |

**Why GW1NR-9 won.** The 64 Mbit PSRAM is *inside the package*, so it costs zero user I/O —
which is exactly what makes a 71-pin QFN work for a design needing 24 ADC lines plus a slave
FIFO. It gives 8 MiB of burst buffer = **2.80 Mpt per channel = 280 ms at 10 MSPS**, a
record length competitive with a benchtop scope, and it satisfies F12a without a single
external memory part. Embedded configuration Flash means instant-on and no config PROM.

**Why the GW1N-4 + external SDRAM combination lost:** identical cost ($20.13 vs $20.91), but
an external SDRAM consumes 39 pins (A0–12, BA0–1, DQ0–15, CLK/CKE/CS/RAS/CAS/WE, DQM0–1).
24 ADC + 18 FIFO + 39 SDRAM + 8 misc = 89 pins against 71 available, forcing an LQFP-144
Gowin part that is not stocked at JLCPCB at all.

**Why an FX2LP-only design lost:** it is the obvious cheap answer and it fails both binding
requirements. Its 4 kB endpoint FIFO gives 1.4 ms of buffer (F12a wants a scope-like record),
and its 8051 cannot repack 20 Msample/s — leaving only the padded-16-bit 40 MB/s path that
requirement 10 explicitly forbids.

**Why an STM32H7 lost:** the largest internal SRAM in the family is ~1 MB, i.e. ~330 kpt/ch,
and sustaining a 20 MB/s parallel capture *plus* software bit-packing *plus* a USB HS bulk
drain on one Cortex-M7 is a firmware gamble, not a design. It also still needs an external
ULPI PHY, so it is not even a part-count win.

**Why FX3 lost:** BGA-121 at 0.65 mm pitch violates the hard X4 constraint. Not negotiable.

**Why iCE40UP5K lost:** 128 kB SPRAM is 42 kpt/ch ≈ 4.2 ms of burst. That is one screen, not
a record, and F12a is what makes the 10 MSPS claim honest.

**Flags.** Single-source (Gowin only), Extended tier, **102 in stock — below the 500-unit
warn threshold** and the lowest-stock keystone in the design. QFN-88 at 0.4 mm pitch is
finer than the 0.5 mm X4 prefers, but X4 is SOFT and the hard rule (no BGA below 0.8 mm) is
satisfied — QFN is not BGA. The stocked variant is the **"P" suffix = PSRAM at 1.8 V**, not
the SDRAM variant; that is where the +1V8 rail in the power tree comes from.

---

## 3. USB device — `usb_controller`

| candidate | stock | unit $ | package | verdict |
|---|---|---|---|---|
| **CY7C68013A-56LTXC** | 2624 | 10.68 | QFN-56-EP 8×8 | **selected** |
| CY7C68013A-56PVXC | 483 | 17.53 | SSOP-56 | second source, different footprint |
| CY7C68013A-100AXC | 2266 | 13.22 | TQFP-100 | rejected — 44 extra pins we never use |

FX2LP is the right USB device here precisely *because* the FPGA does the hard work: in slave
FIFO mode the 8051 is not in the data path at all, so the 480 Mb/s path has no firmware
timing risk. The `-56LTXC` commercial grade is 0–70 °C, which is exactly X5. ROMless part —
boots from the CAT24C128 at I²C address 0xA2 (satisfies I9) or by host download.

**8-bit slave FIFO, not 16-bit.** 8 bits × 48 MHz IFCLK = 48 MB/s against a 30 MB/s payload —
60 % headroom, and it saves 8 FPGA pins that the 1.8 V PSRAM bank may otherwise cost us
(see `design_risks.md` R1).

---

## 4. Front-end buffer and anti-alias amp — `analog_frontend`

Requirement drivers: F6 (flat to 4 MHz), F11 (≥60 dB SNR), I4 (high-Z), F9 (±50 V survival).

The binding number is slew rate: ±0.909 V at 4 MHz needs 2π·4 MHz·0.909 V = **22.8 V/µs**
just to reproduce full scale, before any margin.

| candidate | GBW | slew | Iq/amp | stock | unit $ | verdict |
|---|---|---|---|---|---|---|
| **AD8066ARZ-R7** (dual FET, SOIC-8) | 145 MHz | 180 V/µs | 6.4 mA | 5868 | 4.26 | **selected** |
| OPA2810IDR (dual CMOS, SOIC-8) | 105 MHz | 192 V/µs | 3.6 mA | **35** | 3.48 | rejected |
| OPA1656IDR (dual FET, SOIC-8) | 53 MHz | **24 V/µs** | 3.9 mA | 4877 | 1.51 | rejected |
| AD8065ARZ (single FET) | 145 MHz | 180 V/µs | 6.4 mA | 4896 | 5.37 | fallback (2× the parts) |

**Why AD8066 won.** One dual per channel covers both active stages — unity-gain buffer at the
divider tap, then the Sallen-Key AAF section — so the whole active front end is 2 packages
for 2 channels. FET inputs (2 pA bias) mean the 82.6 kΩ tap impedance costs nothing in DC
accuracy, and 180 V/µs gives 8× margin on the 22.8 V/µs slew requirement.

**Why OPA1656 lost:** one third the price and 4877 in stock, but 24 V/µs against a 22.8 V/µs
full-scale requirement at the top of the band. It would slew-limit on exactly the signal the
spec is written around. This is the clearest reject in the design.

**Why OPA2810 lost:** better on every axis that matters (105 MHz, 192 V/µs, 3.6 mA), and it
would have been the pick — 35 units in stock. Cannot build five boards with margin.

Noise sanity check: the 90.9 kΩ tap contributes 37 nV/√Hz, which over the 4.9 MHz noise
bandwidth is 82 µVrms against a 643 mVrms full-scale sine — a 77.9 dB contribution, well
clear of the ADC's 70 dB. A 90 kΩ source impedance looks alarming and is not.

---

## 5. ADC driver / single-ended-to-differential — `analog_frontend`

| candidate | BW | Iq | output | stock | unit $ | verdict |
|---|---|---|---|---|---|---|
| **THS4551IRGTR** (QFN-16-EP 3×3) | 135 MHz | 1.37 mA | rail-to-rail | 765 | 3.57 | **selected** |
| ADA4940-1ARZ-R7 (SOIC-8) | 260 MHz | 1.25 mA | not RRO | 1092 | 7.38 | second source, **not** footprint-compatible |
| ADA4940-1ACPZ-R7 (LFCSP-16 3×3) | 260 MHz | 1.25 mA | not RRO | 637 | 8.95 | rejected on price |

**Why THS4551 won.** Rail-to-rail output is what lets it sit on ±4.2 V and still put out
1.50 V ± 0.5 V per side with real overdrive headroom; a non-RRO part on those rails is
tighter than it looks. Adjustable VOCM pin takes the 1.50 V divider directly. Half the price
of the ADA4940 with adequate stock. It also carries the high-order half of the AAF as a
differential multiple-feedback section, so the filter costs no extra amplifier.

---

## 6. Bipolar analog rails — `power_analog`

Requirement drivers: P4 (bipolar rails), P5 (**LDO post-regulation on every analog rail**,
≤100 µVrms 10 Hz–1 MHz), P1 (VBUS only).

| candidate | topology | LDO included? | stock | unit $ | verdict |
|---|---|---|---|---|---|
| **LM27762DSSR** (WSON-12-EP 2×3) | 2 MHz inverting charge pump + **integrated ± LDOs**, ±1.5–5 V, 250 mA | **yes, both rails** | 11277 | 0.96 | **selected** |
| TPS65131RGE (VQFN-24) + 2 discrete LDOs | inverting boost, adjustable ±15 V | no — needs TPS7A49xx + TPS7A30xx | — | ~3 + ~6 | rejected |
| MT3608 boost + TPS60403 + 2 LDOs | boost + unregulated inverter | no | — | ~1 + ~1 + ~4 | rejected |
| LM2776 inverter + LDOs | 500 kHz inverter | no | — | ~1 | rejected |

**Why LM27762 won.** It satisfies P5 *by construction* — the LDO post-regulator is on the die
for both polarities, so there is no way to build this block and accidentally leave a
switching rail exposed to the ADC. Its 2 MHz switching frequency puts the fundamental ripple
**above** the 10 Hz–1 MHz band P5 measures in, which is the only reason a charge pump is
acceptable in a 12-bit front end at all. One WSON-12 and four capacitors replaces a converter
plus two scarce LDOs (negative low-noise LDOs are the hardest part class to source), at
$0.96 against roughly $9.

**The tradeoff, stated plainly:** LM27762's VIN maximum is 5.5 V and its positive output is a
plain LDO from VIN, so the positive rail must sit below VBUS minus dropout. At VBUS = 4.75 V
worst case the rails are set to **±4.2 V**, not the ±5 V/±6 V requirement 9 suggests. This is
fine — the front end never needs more: the largest signal anywhere in the chain is ±0.909 V,
and the BAV199 clamp holds the buffer input inside AD8066's ±(VS+0.7) absolute maximum on a
±50 V overload. Requirement 9 says "e.g. ±5 V/±6 V"; the binding part is *bipolar and LDO
post-regulated*, which is met. Recorded as a deliberate SOFT deviation in `design_risks.md`.

Analog 3.0 V for the ADCs: **LP5907MFX-3.0** (43427 in stock, $0.096) off +4V2A — 6.5 µVrms
output noise, 15× inside the 100 µVrms P5 limit.

---

## 7. Digital rails — `power_digital`

| function | selected | stock | unit $ | why |
|---|---|---|---|---|
| +3V3_AON, always on | AP2112K-3.3TRG1 (SOT-23-5, 600 mA) | 79480 | 0.158 | Only the FX2LP island is powered before enumeration; an LDO here costs 110 mW and removes a load switch and its sequencing |
| +3V3 main, EN | TLV62569DBVR (SOT-23-5, 2 A, 1.5 MHz) | 108275 | 0.073 | Buck, not LDO: 190 mA at 3.3 V from an LDO would burn 320 mW and 37 mA of the VBUS budget |
| +1V2 FPGA core, EN | TLV62568DBVR (SOT-23-5, 1 A) | 20475 | 0.080 | Buck off +3V3. An LDO here dissipates 250 mW in a SOT-23 and costs 45 mA of VBUS |
| +1V8 PSRAM bank | LP5907MFX-1.8 (SOT-23-5, 250 mA) | 17548 | 0.206 | 60 mA at a 1.5 V drop = 90 mW; a second inductor is not worth it |

**Why the AON/switched split.** Requirement P3 caps pre-enumeration draw at 100 mA and the
board draws ~327 mA running. The alternative — one always-on buck plus load switches on each
branch — needs three load switches and a sequencing network. Splitting at the source needs
one extra LDO. `PWR_EN` (FX2LP PA0) gates U2, U3, U4 and U5 together. **PWR_EN must have a
100 kΩ pulldown**: FX2LP PORTA pins are high-Z after reset, and a floating enable would put
the board over 100 mA before the host has granted it.

---

## 8. Sample clock — `clock_gen`

Jitter bar: 12-bit at a 4 MHz input needs t_j ≤ 20 ps rms to keep the jitter-limited SNR at
66 dB, above the ADC's own 70 dB and clear of the 60 dB in F11. Arithmetic in
`design_risks.md`.

| candidate | jitter | stock | unit $ | verdict |
|---|---|---|---|---|
| **SiT1602BI-22-33E-10.000000** (MEMS XO, 3225) | ~1.3 ps rms | 1000 | 1.07 | **selected** |
| SG-8002CA quartz XO | < 1 ps rms | 960 (20 MHz) | 1.55 | alternative — no 10.000 MHz line item stocked |
| GW1NR-9 internal PLL from a system clock | tens of ps p-p | — | 0 | rejected |

**Why a dedicated XO won.** It costs $1.07 plus $0.18 for the fanout buffer and it removes an
entire class of question. An FPGA PLL output would put the sample clock on the same die as 24
I/O switching at 10 MHz and a PSRAM controller at 166 MHz, and Gowin specifies PLL jitter in
tens of picoseconds peak-to-peak — inside the margin we care about, for zero saving.

Fanout: **SN74LVC2G34DBVR** (33347 in stock, $0.181), one package feeding both ADC CLK pins.
Both halves in one die is what guarantees the F10 skew spec. Total clock-path jitter
(XO 1.3 ps ⊕ buffer ~2 ps ⊕ AD9235 aperture 0.5 ps) ≈ **2.5 ps rms — 8× inside the bar.**

Variable sample rate is done by decimation in the FPGA, not by retuning the clock.

---

## 9. Considered and deliberately not fitted

**Switchable input range (÷1 / ÷10 second range).** I8 lists "range" in the control endpoint.
A second range needs a bipolar-capable low-Ron analog switch in the gain network — ADG1219BRJZ
is $5.20 each, $10.40/board, and the cheap alternatives (TS5A23159, 74HC4053) either cannot
pass a ±1 V bipolar signal at all or modulate Ron with signal level and cost ENOB. Since a
second range is nowhere in the HARD requirements, it is not fitted; "range" is exposed as a
host-side scaling field. **Carried forward** — the natural place to add it later is a switched
Rg in the THS4551 network.

**Shared external voltage reference.** One ADR510 (1.0 V, $3.78) driving both ADCs' SENSE/VREF
would match channel gains to each other in hardware. Not fitted: F8 already specifies a
one-time host-side calibration, which corrects per-channel gain anyway, and each ADC's
internal reference is the lower-part-count path (SENSE→GND). Saves $3.78 and two nets.

**AC coupling, probe-ratio sensing, on-board calibration DAC.** All carried forward from
requirements; none fitted. See handoff `## Carried forward`.

---

## Summary — final selections

| block | function | MPN | package | stock | unit $ | tier |
|---|---|---|---|---|---|---|
| adc_pair | 12-bit 10 MSPS ADC ×2 | AD9235BCPZ-40 | LFCSP-32 5×5 | 170 | 18.41 | Ext |
| fpga_capture | FPGA + 64 Mbit PSRAM | GW1NR-LV9QN88PC6/I5 | QFN-88 0.4 mm | 102 | 20.91 | Ext |
| usb_controller | USB 2.0 HS device | CY7C68013A-56LTXC | QFN-56-EP 8×8 | 2624 | 10.68 | Ext |
| usb_controller | boot EEPROM 16 kB | CAT24C128WI-GT3 | SOIC-8 | 10534 | 0.41 | Ext |
| analog_frontend | buffer + AAF, dual FET | AD8066ARZ-R7 | SOIC-8 | 5868 | 4.26 | Ext |
| analog_frontend | FDA / ADC driver | THS4551IRGTR | QFN-16-EP 3×3 | 765 | 3.57 | Ext |
| power_analog | ±4.2 V, integrated LDOs | LM27762DSSR | WSON-12-EP 2×3 | 11277 | 0.96 | Ext |
| power_analog | AVDD 3.0 V LDO | LP5907MFX-3.0 | SOT-23-5 | 43427 | 0.10 | Ext |
| power_digital | +3V3_AON LDO | AP2112K-3.3TRG1 | SOT-23-5 | 79480 | 0.16 | Ext |
| power_digital | +3V3 buck | TLV62569DBVR | SOT-23-5 | 108275 | 0.07 | Ext |
| power_digital | +1V2 buck | TLV62568DBVR | SOT-23-5 | 20475 | 0.08 | Ext |
| power_digital | +1V8 LDO | LP5907MFX-1.8 | SOT-23-5 | 17548 | 0.21 | Ext |
| clock_gen | 10.000 MHz XO | SiT1602BI-22-33E-10.000000 | SMD3225-4P | 1000 | 1.07 | Ext |
| clock_gen | dual clock buffer | SN74LVC2G34DBVR | SOT-23-6 | 33347 | 0.18 | Ext |
| usb_c_port | USB-C 2.0 receptacle 16P | TYPE-C 16PIN 2MD(073) | SMD | 1171811 | 0.07 | Ext |
| usb_c_port | USB ESD array | USBLC6-2SC6 | SOT-23-6 | 150192 | 0.05 | Ext |
| usb_c_port | VBUS TVS | SMAJ5.0A | DO-214AC | 64985 | 0.04 | **Pref** |
| analog_frontend | BNC jack ×2 | KH-BNC50-3511 | THT | 4742 | 0.93 | Ext |
| analog_frontend | low-leakage clamp ×2 | BAV199 | SOT-23 | 85473 | 0.01 | Ext |
| usb_controller | 24.000 MHz crystal | X322524MOB4SI | SMD3225-4P | 94151 | 0.09 | Ext |
