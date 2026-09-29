# IC Selection — dual_adc_usb

Autonomous run: no user questions asked. Every choice below is an options table with a
marked **RECOMMENDED** row, adopted as the design decision.

> **Sourcing-tool caveat (important for the part-sourcer):** the `pcbparts` MCP was **not
> connected** in this session, so **no live JLCPCB stock or tier data could be retrieved**.
> Every "JLCPCB expectation" note below is an engineering estimate, not a verified fact.
> The sourcer MUST verify stock/tier/lifecycle for every row. Where I could reduce the
> sourcer's risk I did so by choosing parts with **named, vetted second sources**, and by
> stating the *electrical criteria* a substitute must meet — substitute on the criteria,
> not on the part number.
>
> What I *could* verify locally is **KiCad symbol availability** in
> `/usr/share/kicad/symbols` (224 libs). That is recorded per part, because a missing
> symbol is real downstream work (kipart generation) that the coder must budget for.

---

# PART 1 — Two feasibility issues the requirements phase left open

## F1. CAPTURE BUFFER SIZING — resolved

**The problem, stated honestly.** 32,768 samples/ch × 2 ch × 12 bit = 98,304 bytes.
No iCE40-class FPGA has that much block RAM: iCE40HX8K has 128 kbit = **16 kB** of BRAM,
iCE40HX4K 80 kbit = 10 kB, MachXO2-4000 92 kbit = 11.5 kB. The requirements' baseline is
**6× too large for on-chip BRAM.** Something has to give.

| Option | Achieved burst depth per channel | Pros | Cons |
|---|---|---|---|
| **A. Reduce depth to fit BRAM** — iCE40HX8K, 16 kB BRAM, 12-bit packed | 5,461 /ch (0.55 ms) | Cheapest, fewest parts, no external memory bus | 6× *below* the requested 32k; 0.55 ms is too short to be a useful scope record; wastes the 10 MSPS spec |
| **B. iCE40UP5K — 1 Mbit on-die SPRAM** (4 × 256 kbit, 16-bit wide) | **32,768 /ch exactly** (3.277 ms) | Mathematically perfect fit: 32768 × 2 ch × 16 b = 1,048,576 b = exactly the SPRAM; no external memory chip; lowest power | **FAILS ON PIN COUNT.** UP5K's largest package (SG48) has only 39 user I/O, 4 of which are the SPI-config pins. Minimum need is 24 (ADC data) + 14 (sync FIFO) + 1 (clock in) = **39 with zero left for LEDs, reset, trigger or the config flash.** UWG30 is worse (25 I/O). Not buildable. |
| **C. Larger FPGA + external asynchronous SRAM** (iCE40HX4K-TQ144 + IS61WV25616, 256K×16, 10 ns, 512 kB) | **131,072 /ch (13.107 ms)** — 4× the requested depth | Deterministic, no refresh, no PHY, no calibration; 50 ns write budget vs 10 ns access = 5× timing margin; 107 I/O is ample; verified KiCad symbol for the FPGA; open toolchain | +1 IC, +39 FPGA pins, +1 mm² of BOM cost; SRAM bus is the board's biggest EMI aggressor (mitigated, see design_risks R-04) |
| **D. Larger FPGA + SDRAM** (e.g. W9812G6KH 128 Mbit, or Gowin GW1NR-9 with in-package 64 Mbit SDRAM) | 2,000,000+ /ch | Enormous depth for ~$1.50; Gowin variant needs no external memory chip at all | Needs a refresh-aware SDRAM controller + timing closure — real gateware risk for a gap-free 20 MS/s writer; Gowin locks the design to a vendor toolchain; depth far beyond what a 13 ms scope record needs |
| **E. ECP5 LFE5U-25F — 1,008 kbit on-die EBR** | ~126 kB → 32,768 /ch comfortably | No external memory, plenty of I/O | caBGA-256 0.8 mm on a 4-layer board is a fab/assembly step change; ~3× the FPGA cost; large power draw against a 500 mA USB budget |

**RECOMMENDED → Option C.** It is the only option that is simultaneously buildable on
pins, low-risk in gateware, and *exceeds* rather than compromises the requested depth.

### The hard number (this supersedes the requirements' 32,768 baseline)

- **Burst depth: 131,072 samples per channel**, both channels, simultaneous, gap-free,
  full 10.000 MSPS, full 12-bit.
- **Record length: 13.1072 ms.**
- Storage format in SRAM: one 12-bit sample right-justified in one 16-bit word (no
  packing in RAM — packing happens on readout). 262,144 words ÷ 2 channels = 131,072.
- **Host-configurable** in 1,024-sample steps from 1,024 to 131,072 per channel
  (`SET_DEPTH`, see F2).
- Readout size at maximum depth: 131,072 × 2 × 1.5 B = **393,216 bytes**, ≈13 ms at the
  ~30 MB/s sustained sync-FIFO rate.
- Upgrade path already footprint-compatible: **IS61WV51216** (512K×16, same TSOP-II-44
  outline, 1 MB) doubles this to **262,144 samples/ch (26.2 ms)** for ~$1 more. The
  sourcer may take this substitution freely if the ×16/512K part is short.

## F2. CONTROL PROTOCOL — resolved

**The constraint that decides this.** FTDI documents that when an **FT2232H is placed in
FT245 synchronous FIFO mode, channel B cannot be used** (AN_130). So the tempting
"channel A = data, channel B = MPSSE control" split **is not available**. That removes an
entire option and simultaneously removes the reason to pay for a dual-channel bridge.

| Option | Pros | Cons |
|---|---|---|
| **A. In-band command frames on the same synchronous FIFO** (host→device path: `RXF#`/`RD#`/`FIFO_D[7:0]`) | Zero extra pins — the sync FIFO is already full-duplex and the two directions are independent FIFOs; works identically on FT232H and FT2232H; one host handle, one driver | FPGA needs a ~60-LUT byte-level command parser; host must frame commands |
| B. FT2232H channel B as a separate MPSSE/UART control port | Clean separation of control and bulk data | **Not possible** — channel B is unusable in sync FIFO mode; also +5 FPGA pins and a bigger, costlier LQFP-64 bridge |
| C. Dedicated GPIO strap pins / DIP switch | Trivial | Not host-controllable; fails the requirement that the mode be host-selectable |
| D. Separate USB-serial bridge IC for control | Full separation | +1 IC, +1 USB endpoint, 2 device handles the host must correlate; unnecessary complexity |

**RECOMMENDED → Option A**, and consequently **downgrade the bridge from FT2232H to
FT232H** (see block 8): the second channel is provably unusable, so it is pure cost, pins
and package area.

### The protocol (this is normative for the FPGA gateware and the host driver)

**Pins/nets that implement it — no additional hardware:** `FIFO_D[7:0]`, `FIFO_RXF_N`,
`FIFO_RD_N`, `FIFO_OE_N` (host→device commands) and `FIFO_D[7:0]`, `FIFO_TXE_N`,
`FIFO_WR_N` (device→host data and status), all on the FT232H channel-A sync FIFO already
listed in `net_plan.md` §7. Plus one optional `EXT_TRIG` FPGA input.

**Host→device command frame: 4 bytes, `0xA5, CMD, ARG_L, ARG_H`.** The parser hunts for
the `0xA5` sync byte, so it self-recovers from any host-side desync.

| CMD | Name | ARG | Effect |
|-----|------|-----|--------|
| `0x01` | `SET_MODE` | 0 = idle, 1 = burst, 2 = continuous ch A, 3 = continuous ch B, 4 = continuous dual (decimated) | writes the mode register |
| `0x02` | `SET_DECIM` | N, 1…65535 | effective rate = 10 MSPS ÷ N per channel |
| `0x03` | `SET_DEPTH` | D, 1…128 (units of 1024 samples/ch) | burst depth; D = 128 → 131,072 samples/ch |
| `0x04` | `ARM` | 0 = immediate, 1 = `EXT_TRIG` rising, 2 = `EXT_TRIG` falling | arms burst capture |
| `0x05` | `READOUT` | 0 | drains the capture buffer to the host |
| `0x06` | `STATUS` | 0 | device replies with one 4-byte status frame |
| `0x07` | `RESET` | 0 | abort, flush, return to idle |

**Device→host framing.** Every block is `0x5A, TYPE, LEN_L, LEN_H` followed by the
payload, where `LEN` counts 3-byte groups. `TYPE` 0x00 = status (payload:
`STATE, FILL_L, FILL_H` + OTR flags), 0x01 = sample data.

**Sample packing (12-bit packed, 3 bytes per 2 samples — [HARD] requirement):**
`b0 = S0[11:4]`, `b1 = (S0[3:0] << 4) | S1[11:8]`, `b2 = S1[7:0]`.
In dual-channel modes `S0` is the channel-A sample and `S1` is the *time-coincident*
channel-B sample, so one 3-byte group = one simultaneous sample pair. In single-channel
modes `S0`/`S1` are consecutive samples of that channel.

**Correction to a requirements number.** The requirements sketched dual-channel
continuous at "≈8 MSPS/ch, ≈192 Mbps". That implies a fractional decimation of 1.25,
which is needless FPGA complexity. Integer decimation gives **N ≥ 2 → 5.000 MSPS/channel
dual continuous = 15.0 MB/s = 120 Mbps**, identical to single-channel-full-rate mode and
comfortably inside the ~30 MB/s sustained sync-FIFO budget with >2× margin. The [HARD]
part of that requirement was the ≤240 Mbps ceiling, which this satisfies with room to
spare.

## F3. AFE ATTENUATION AND COMMON MODE — recomputed from the real ADC

The requirements' "~11:1, ADC 0–2 V, CM ~1 V" were explicitly flagged as placeholders.
The selected **AD9235** in single-ended configuration has: `VIN−` biased at AVDD/2 =
**1.500 V**, span selectable **2.0 V p-p**, so `VIN+` must swing **0.500 V to 2.500 V**.

| Quantity | Requirements placeholder | **Actual, from AD9235** |
|---|---|---|
| ADC input span | 0–2 V | **0.500–2.500 V (2.000 V p-p)** |
| ADC common mode | ~1.0 V | **1.500 V** |
| Passive attenuator ratio | ~11:1 | **20:1** (950 kΩ / 50 kΩ, Zin = 1.000 MΩ exactly) |
| Post-attenuator gain | ×1 | **×2** (in the A3 MFB stage) |
| **Net BNC→ADC attenuation** | ~11:1 | **10:1 (20.0 dB)** |
| LSB referred to the BNC | ~5.4 mV | **4.8828 mV** (= 20 V ÷ 4096) |
| Full scale at the BNC | ±10 V | **±10.000 V exactly** |

Level-shift arithmetic (A3, multiple-feedback, inverting, gain −2, non-inverting input at
`VREF_0V5` = 0.500 V):
`Vout = VREF·(1 + Rf/Rin) − Vin·(Rf/Rin) = 0.5 × 3 − 2·Vin = 1.500 − 2·Vin`
→ Vin = +0.5 V ⇒ Vout = 0.500 V; Vin = −0.5 V ⇒ Vout = 2.500 V. Exact.

**Why 20:1-then-×2 instead of 10:1-then-×1:** a ×1 stage cannot add a DC offset without a
negative reference; ×2 lets a single positive 0.5 V reference do the whole level shift,
which is what allows A3 to run from **+3V3_A single supply** — which in turn is what makes
A3's output incapable of exceeding the ADC's absolute maximum. The gain buys the ADC
protection for free.

**Over-range survivability, as a hard number:** at the [SOFT] target of ±40 V continuous
the attenuator node reaches only **±2.0 V** — inside the ±5 V op-amp rails, so *no clamp
conducts and nothing is stressed*. Power in the 950 kΩ top leg at 40 V is 1.7 mW. The
BAV99 clamp at the buffer input only conducts beyond roughly **±100 V**. The 950 kΩ is
built as two series 475 kΩ 0805 parts so neither exceeds its working-voltage rating and
neither dominates the voltage coefficient of resistance.

**Noise budget check (this is why the design closes on ENOB):**

| Contributor | RMS at the ADC input |
|---|---|
| 47.5 kΩ attenuator Thevenin noise, ×2 gain, 5 MHz NBW | 126 µV |
| Op-amp chain (AD8066 7 nV/√Hz, 3 stages) | ~30 µV |
| AD9235 itself (70 dB SNR at 2 V p-p) | 224 µV |
| **Total** | **259 µV** → SNR 68.7 dB → **ENOB ≈ 11.1 bits** |

Meets the ≥10.5-bit target with ~0.6 bit of margin before distortion terms. 1 LSB = 488 µV.

---

# PART 2 — IC selection by block

## Block 5/6 — ADC (`adc_channel`, ×2)

Requirement: 12-bit, ≥10 MSPS, **parallel CMOS output [HARD]**, single 3–5 V supply,
single-ended-capable input, and — the binding constraint nobody wrote down — it must fit
a **500 mA total USB budget shared with an FPGA, an SRAM and a USB PHY**.

| Candidate | Res / rate | Supply | Power (each) | Input | Package | Verdict |
|---|---|---|---|---|---|---|
| **AD9235BRUZ-20** | 12 b / 20 MSPS | 3.0–3.6 V single | **120 mW (≈40 mA)** | diff or single-ended, 1 or 2 V p-p, CM = AVDD/2 | TSSOP-28 | **RECOMMENDED** |
| AD9226ARSZ | 12 b / 65 MSPS | 5 V AVDD + 3 V DRVDD | **475 mW (≈95 mA)** | true single-ended, 2 V p-p, CM 2.0 V | SSOP-28 | Best native single-ended input of the three, but **two of them draw 190 mA — 38% of the entire USB budget** before the FPGA is even powered. Rejected on power. |
| LTC2290CUP | **dual** 12 b / 10 MSPS | 3 V | 120 mW for *both* channels | differential, 2 V p-p, CM 1.5 V | QFN-64 9×9 | Electrically the nicest part in the table (one chip, both channels, exactly 10 MSPS, 71 dB SNR) and it even has a KiCad symbol (`Analog_ADC:LTC2290xUP`). Rejected on **cost** (~$40–60 each vs ~$12) against the assumed ≤$150 BOM target, and on JLCPCB stock likelihood. |
| ADS807E | 12 b / 53 MSPS | 5 V | 380 mW | single-ended | SSOP-28 | Rejected on power, same reason as AD9226. |
| ADC12010CIVY | 12 b / 10 MSPS | 3 V | 160 mW | single-ended, CM 1.5 V | LQFP-32 | Spec-perfect but long-obsolete/NRND; unsourceable. |

**Why AD9235BRUZ-20 wins:** it is the only candidate that meets 12 b / ≥10 MSPS /
parallel CMOS **and** fits the power budget (2 × 40 mA = 80 mA, vs 190 mA for the
AD9226), **and** its single-ended input configuration (VIN− tied to AVDD/2, 2 V p-p span)
lands on 0.5–2.5 V / CM 1.500 V — clean numbers the AFE hits exactly. The −20 speed grade
is the lowest-power member; we clock it at 10 MHz, half its rated rate, which is also
where its distortion is best.

- **Second source, drop-in, zero schematic change:** `AD9235BRUZ-40`, `AD9235BRUZ-65`,
  and `AD9236BRUZ-80` share the **same TSSOP-28 pinout**. The sourcer may take any of
  them if −20 is short; higher grades cost only more power (−40 ≈ 200 mW, −65 ≈ 300 mW
  each — **if the sourcer takes −65 for both channels, flag it: 2 × 300 mW = 180 mA
  breaks the power budget and the design must revert to LDO→buck for 3V3_D**).
- Package is **fixed to TSSOP-28 (RU)**; the LFCSP (CP) variant is a different footprint.
- **KiCad symbol: does NOT exist** — must be generated with `kipart` (28 pins, simple).
- Configuration straps the coder must get from the datasheet phase: `SENSE` strapping for
  the 2 V p-p span, `OEB` → GND, `PDWN` → FPGA, `CLK` from `clock_gen`.

## Block 5 — AFE amplifiers (`afe_channel`, ×2)

Two different roles, two different parts. Each channel is self-contained (no op-amp
package is shared between channel A and channel B) so `afe_channel` can be instantiated
twice without cross-block wiring.

### A1 + A2 — high-Z buffer and first filter section (one dual, ±5 V)

Must have: FET/CMOS input (it buffers a 47.5 kΩ source; bipolar input bias current would
create a large offset), ≥100 MHz GBW, ±5 V rails, no phase inversion on input overdrive.

| Candidate | GBW | Iq/amp | Input | Package | Verdict |
|---|---|---|---|---|---|
| **AD8066ARZ** | 145 MHz | 6.4 mA | FET, 2 pA bias, 7 nV/√Hz | SOIC-8 dual | **RECOMMENDED** — the classic ±5 V FET-input dual for exactly this job; specified as no-phase-reversal |
| OPA2810IDR | 70 MHz | 3.6 mA | JFET, 3 pA | SOIC-8 dual | Strong second source: nearly half the current, standard SOIC-8 dual pinout so it is a **drop-in**. 70 MHz is still ≥14× the 5 MHz corner. Take this if AD8066 is short or if power comes in tight. |
| OPA1656IDR | 53 MHz | 3.9 mA | CMOS, 1 pA, 2.9 nV/√Hz | SOIC-8 dual | Lowest noise of the three, also drop-in, but 53 MHz is the least filter-margin. Third choice. |

Substitution criteria for the sourcer: **dual op-amp, standard SOIC-8 pinout, ≥50 MHz
GBW, FET/CMOS input (Ib ≤ 100 pA), ±5 V supply capable, ≤7 mA/amp.**
**KiCad symbol: none of these exist by name** — use any standard dual-op-amp SOIC-8
symbol from `Amplifier_Operational` (e.g. `LM7332`) or generate with `kipart`.

### A3 — level-shifting MFB output stage (one single, **+3V3_A only**)

Must have: rail-to-rail output, ≥100 MHz GBW, input common-mode range including 0.5 V on
a 3.3 V supply, and — the point of the whole choice — **it must run off the same rail as
the ADC** so its output cannot exceed the ADC's absolute maximum.

| Candidate | GBW | Iq | Supply | Package | Verdict |
|---|---|---|---|---|---|
| **OPA836IDBVR** | 205 MHz | **1.0 mA** | 2.5–5.5 V single | SOT-23-6 | **RECOMMENDED** — 205 MHz for 1 mA, RRO, unity-gain stable, input CM includes the negative rail |
| ADA4891-1ARJZ | 220 MHz | 4.4 mA | 2.7–5.5 V single | SOT-23-5 | Good second source, 4× the current |
| OPA357AIDBVR | 250 MHz | 8 mA | 2.7–5.5 V single | SOT-23-5 | Third choice; 8 mA each is 16 mA of budget for no benefit |

Substitution criteria: **single op-amp, ≥150 MHz GBW, rail-to-rail output, 3.3 V single
supply, input CM range including 0.5 V, ≤5 mA.**
**Design intent the sourcer must not break: A3 is powered from `V3V3_A`, not ±5 V. That
is deliberate — it is the ADC's over-voltage protection and it replaces clamp diodes
whose leakage would cost ~0.7 LSB of offset. Do not substitute a ±5 V-only part.**

## Block 9 — FPGA (`fpga_core`)

Needs: **≥86 usable I/O** (24 ADC data + 2 OTR + 2 PDWN + 1 clock in + 39 SRAM + 14 sync
FIFO + 4 housekeeping), a PLL (for the 60 MHz FIFO output phase), ≥1,500 LUT, and low
enough power to live inside a 500 mA USB budget.

| Candidate | LUT / BRAM | Usable I/O | Rails | Config | Package | Verdict |
|---|---|---|---|---|---|---|
| **iCE40HX4K-TQ144** | 3,520 / 80 kbit | **107** | 1.2 V core + 3.3 V I/O (VPP_2V5 tied to 3.3 V per Lattice TN1256) | external SPI flash | TQFP-144, 0.5 mm | **RECOMMENDED** |
| LCMXO2-4000HC-4TG144C | 4,320 / 92 kbit | 115 | **single 3.3 V** (internal regulator) | **internal flash — no SPI flash IC, instant-on** | TQFP-144 | Genuinely the better *silicon* choice for a bus-powered board: it deletes the 1.2 V LDO *and* the config flash. Rejected because **no KiCad symbol exists** for any MachXO2 device, so it would require hand-building a 144-pin symbol from the datasheet — a real, avoidable defect risk in a pipeline whose next stages are automated. Recorded as the runner-up; revisit if the iCE40 is unsourceable. |
| iCE40HX1K-TQ144 | 1,280 / 64 kbit | **95** | same as HX4K | external SPI flash | TQFP-144 | Fits the 86-pin need with 9 to spare and has a KiCad symbol, but 1,280 LUT is uncomfortably tight for SRAM controller + capture FSM + decimator + packer + command parser. **Not pin-compatible with HX4K-TQ144** despite the shared package — treat as a schematic-changing fallback, not a drop-in. |
| iCE40UP5K-SG48 | 5,280 / 1 Mbit SPRAM | 39 | 1.2 V + 3.3 V | external SPI flash | QFN-48 | **Eliminated on pin count** — see F1 option B. |
| GW1NR-9C QN88 | 8,640 / 468 kbit + in-package 64 Mbit SDRAM | ~66 | 1.2 V + 3.3 V | internal | QFN-88 | Cheapest, best-stocked at JLCPCB, and needs no memory chip. Rejected: vendor-locked toolchain, no KiCad symbol, and an SDRAM controller is more gateware risk than the async SRAM it replaces. |

**Why iCE40HX4K-TQ144 wins:** it is the only candidate that has **all** of enough I/O, a
verified KiCad symbol (`FPGA_Lattice:ICE40HX4K-TQ144`, 5-unit), an open and free
toolchain (yosys/nextpnr/icestorm — no license server for a hobby-scale instrument), and
a non-BGA package a 4-layer JLCPCB build can assemble. The price is one extra LDO and one
config flash, ≈$1.

- Package **fixed to TQ144** by the 86-pin requirement — TQFP-100 parts (79 I/O) will not
  fit. Do not let the sourcer "downsize the package".
- Config flash: **W25Q32JVSSIQ** (SOIC-8, symbol exists as `Memory_Flash:W25Q32JVSS`).
  Any ≥1 Mbit 3.3 V SPI NOR in SOIC-8 works; iCE40HX4K bitstream is ~137 kB.
- Core rail: **AP2112K-1.2TRG1** (symbol `Regulator_Linear:AP2112K-1.2`), ~45 mA.

## Blocks 7, 8 — SRAM and USB bridge

### SRAM (`sram_buffer`)

| Candidate | Organization | Access | Supply | Package | Verdict |
|---|---|---|---|---|---|
| **IS61WV25616BLL-10TLI** | 256K × 16 (512 kB) | 10 ns | 3.3 V | TSOP-II-44 | **RECOMMENDED** — 50 ns write budget vs 10 ns access = 5× margin |
| CY7C1041GN30-10ZSXI | 256K × 16 | 10 ns | 3.3 V | TSOP-II-44 | Second source, same pinout, drop-in |
| AS7C34098A-10TCN | 256K × 16 | 10 ns | 3.3 V | TSOP-II-44 | Third source, same pinout |
| IS61WV51216BLL-10TLI | 512K × 16 (1 MB) | 10 ns | 3.3 V | TSOP-II-44 | **Free upgrade** — same outline, +1 address pin, doubles burst depth to 262,144 samples/ch. Take it if the 256K part is short or similarly priced. |
| AS6C1616 (has a KiCad symbol) | 1M × 16 | **55 ns** | 3.3 V | TSOP-48 | Rejected: 55 ns cannot complete a write inside the 50 ns budget. Do not substitute on capacity alone — **speed is the binding spec.** |

Substitution criteria: **≥256K × 16, ≤15 ns, 3.3 V, TSOP-II-44.**
**KiCad symbol: does not exist — must be generated with `kipart` (44 pins).**

### USB bridge (`usb_bridge`)

| Candidate | Channels | Sync FIFO | Package | Verdict |
|---|---|---|---|---|
| **FT232HL** | 1 | yes, 8 b @ 60 MHz, ~30–35 MB/s sustained | LQFP-48 | **RECOMMENDED** |
| FT2232HL | 2 (but **B unusable in sync FIFO mode**) | same | LQFP-64 | The requirements' default. Rejected: the second channel is provably unusable in the mode we need (AN_130), so it is pure cost, 16 extra pins and area. Symbol exists if a fallback is ever needed. |
| FT600Q / FT601Q | 1 | 16/32 b, USB **3.0** | LQFP-56/76 | Far more bandwidth than USB 2.0 needs; would violate the [HARD] "USB 2.0" requirement's connector/PHY assumptions |
| Cypress FX3 / CYUSB3014 | 1 | GPIF II | BGA-121 | Massive firmware effort, BGA, overkill |

**KiCad symbol: `Interface_USB:FT232H` exists ✓.** Requires 93LC46B EEPROM (symbol
`Memory_EEPROM:93CxxC` is pin-compatible), 12 MHz crystal, and a **12.0 kΩ ±1% resistor
on the REF pin** (mandatory, easy to forget). ACBUS9 must be EEPROM-programmed to
**PWREN#** — that signal is load-bearing for USB enumeration compliance (see power).

## Blocks 2, 3 — Power

Rail-by-rail. Total VBUS draw is estimated at **≈345 mA against a 500 mA ceiling (31%
margin)** — see `skeleton_bom.md` for the itemised budget. This is the tightest global
constraint in the design.

| Rail | Candidates | RECOMMENDED | Why |
|---|---|---|---|
| **3V3_D**, 190 mA | AP7361C-33E (SOT-223, 1 A, 250 mV dropout) / RT9080-33GJ5 (SOT-23-5) / TLV75733PDRVR (WSON) | **AP7361C-33E** | **Package is fixed by thermal, not by preference:** (5.25 − 3.3) × 0.19 A = **0.37 W**. SOT-223 (θJA ≈ 60 °C/W with a pour) gives a 22 °C rise; a SOT-23-5 part (θJA ≈ 235 °C/W) would rise 87 °C over a 50 °C ambient and cook. **Do not substitute a SOT-23-5 LDO here.** Symbol exists ✓ |
| **1V2**, 45 mA | AP2112K-1.2 / TLV75712 / XC6206P122 | **AP2112K-1.2TRG1** | 0.095 W, SOT-25 is fine at this power. Symbol exists ✓ |
| **3V3_A**, 105 mA | LP5907MFX-3.3 (6.5 µV RMS noise, 75 dB PSRR) / TLV75533P / ADP151AUJZ-3.3 | **LP5907MFX-3.3** | Low-noise LDO is required here: it feeds both ADCs' AVDD and the clock oscillator. 0.20 W in SOT-23-5 = 48 °C rise, acceptable. **Must have an enable pin** (used by PWREN#). Symbol exists ✓ |
| **5V_A**, 60 mA | LDO / **P-FET load switch + LC filter** / dedicated switcher | **P-FET load switch + ferrite + LC** | Op-amp rails do not need regulation, only filtering and gating. A regulator here would waste headroom on a rail already near VBUS. |
| **−5V_A**, 30 mA | **LM2776DBVR** (200 mA) / TPS60403DBVR (60 mA) / LT1054CS8 (100 mA) | **LM2776DBVR** | 200 mA capability means ~7× margin and a low output impedance; TPS60403's ~15 Ω output impedance would drop 0.45 V at our 30 mA and eat op-amp headroom. Switching noise is handled by a 10 µH + 22 µF post-filter (>90 dB at the switching frequency). Symbol exists ✓ (`Regulator_SwitchedCapacitor:LM2776`) |
| **VREF_2V5** | REF3025AIDBZR / REF3125 / LM4040-2.5 | **REF3025AIDBZR** | 30 ppm/°C, 50 µA, SOT-23-3. Sets the AFE level-shift offset; drift here is a pure offset error and is calibrated out in host software, so 0.2% initial accuracy is plenty. Symbol exists ✓ |

**LDOs, not switchers, everywhere.** At 345 mA total the linear losses (0.67 W) are
affordable and buy a 12-bit-clean supply. A buck for 3V3_D would save ~50 mA of VBUS but
inject switching noise next to a 12-bit ADC — recorded in `design_risks.md` R-09 as the
contingency if measured draw exceeds 450 mA.

**USB enumeration compliance (the reason PWREN# exists).** A USB device may not draw
>100 mA before it is configured. `PWREN_N` from the FT232H gates the P-FET load switch
feeding `V5_A`, the LP5907 enable (`V3V3_A`), and the LM2776 — i.e. **all 165 mA of
analog load, the ADCs and the oscillator**. Pre-enumeration draw is then FT232H
(unconfigured, ~35 mA) + iCE40 static + SRAM standby + LEDs ≈ **65–80 mA**, inside the
100 mA limit. VBUS bulk capacitance is held to 10 µF to satisfy the USB inrush limit.

## Block 4 — Clocking (`clock_gen`)

| Option | Pros | Cons |
|---|---|---|
| **Dedicated 10.000 MHz CMOS XO driving both ADCs through a buffer** | Jitter is set by the oscillator (~1–3 ps RMS), not by FPGA fabric; ADC clock never crosses the digital zone | +1 XO, +2 buffers, ~18 mA |
| Divide the FT232H's 60 MHz CLKOUT by 6 in the FPGA | Zero extra parts; sample rate locked to the FTDI crystal | **Rejected.** FPGA-fabric-generated clocks carry 15–30 ps RMS jitter. The 12-bit budget at a 5 MHz input is **12.7 ps RMS** (SNR_jitter = −20 log(2π·f·t_j)); fabric jitter alone would cost ~1 bit of ENOB. |
| FPGA PLL output | Slightly better than raw fabric | Still 10–20 ps RMS; same failure mode |

**RECOMMENDED → dedicated XO.** This is the single most important non-obvious choice in
the digital section: **the ADC sample clock must never be generated in FPGA fabric.**

- **X1:** 10.000 MHz, 3.3 V CMOS, ±25 ppm, **≤5 ps RMS phase jitter (12 kHz–20 MHz)**,
  3225 4-pad. Candidates: ASEM1-10.000MHZ-LC-T, SiT8008BI-73-33S-10.000000,
  SG-8018CA-10M. Symbol: `Oscillator:ASE-xxxMHz` ✓
- **U16, U17:** 2 × **74LVC1G34** (single buffer, SOT-23-5, symbol exists ✓) or one
  74AUC2G34 dual. Two separate buffers give symmetric, isolated drive to the two ADCs;
  route `CLK_ADC_A`/`CLK_ADC_B` length-matched to ±2 mm so channel-to-channel sampling
  skew stays under ~15 ps (0.00015 sample).

## Blocks 1 — Connectors and protection

| Function | RECOMMENDED | Alternates | Notes |
|---|---|---|---|
| USB-C receptacle, USB 2.0 only | **U262-161N-4BVC11** (16-pin) | TYPE-C-31-M-12, GT-USB-7010ASV | JLCPCB Basic-tier expectation; CC1/CC2 each 5.1 kΩ to GND. Symbol `Connector:USB_C_Receptacle_USB2.0_16P` ✓ |
| USB D+/D− ESD | **USBLC6-2SC6** | PRTR5V0U2X, ESD122DMLT | Symbol `Power_Protection:USBLC6-2SC6` ✓ |
| USB common-mode choke | DLW21SN900HQ2L | ACM2012-900-2P | Optional but recommended for FCC Class B |
| VBUS overcurrent | 500 mA hold / 1 A trip PPTC, 1206 | MF-MSMF050-2, 0ZCJ0050FF2E | |
| BNC jack, 1 MΩ input | Right-angle THT PCB BNC jack | Amphenol 031-5431-10RFX, Molex 73100-0105 | **Footprint-critical and mechanically critical** — must match the panel edge. Symbol `Connector:BNC` ✓, footprint must be verified against the exact MPN. |
| Input clamp | **BAV99** (3 nA leakage) | BAV99W, 1N4148WS pair | Sits *after* a 1 kΩ series resistor at the buffer input, clamping to ±5 V. Symbol `Diode:BAV99` ✓ |

---

# PART 3 — Summary of what is fixed vs. free

| Decision | Status for the sourcer |
|---|---|
| AD9235BRUZ-20, TSSOP-28 | Package **fixed**. Speed grade **free** among −20/−40/−65 (same pinout) with a power warning at −65 |
| iCE40HX4K-TQ144 | **Fixed** — package fixed by pin count, part fixed by symbol availability |
| IS61WV25616BLL-10TLI | Part **free** among ≥256K×16 / ≤15 ns / 3.3 V / TSOP-II-44; **speed is the binding spec, not capacity** |
| FT232HL | **Fixed** — dropping to a smaller bridge loses sync FIFO; going to FT2232H wastes a provably unusable channel |
| AP7361C-33E | **Package fixed to SOT-223 or better by 0.37 W dissipation** |
| LP5907MFX-3.3 | Must have an **enable pin**; must be a low-noise LDO |
| A3 = OPA836 | Must be a **3.3 V single-supply** part — this is ADC protection, not a preference |
| A1/A2 dual op-amp | **Free** among ≥50 MHz FET-input SOIC-8 duals; OPA2810 vetted as drop-in |
| 10 MHz XO | Jitter spec ≤5 ps RMS is **binding** |
| LM2776 | **Free** among ≥60 mA inverting charge pumps, but low output impedance is required |
