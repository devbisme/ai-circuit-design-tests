# IC Selection — `dual_adc_usb`

- **Stage:** architecture
- **Date:** 2026-09-06
- **Sourcing policy:** SPEC §6.1 as amended by the orchestrator — passives/jellybeans hold
  JLCPCB Basic/Preferred + stock > 100; the **four critical ICs (ADC, FPGA, SRAM, FT2232H)** may be
  Extended-tier or off-JLC (Digi-Key / Mouser, hand-placed). Qty = 5 boards, ~$70–100/board OK.

> ## Tooling note — read this first
> **The `pcbparts` MCP server is not connected in this environment** (`claude mcp list` shows only
> `kipart` and Google Drive). Live JLCPCB tier/stock/LCSC# fields therefore **could not be queried
> directly**. Stock and lifecycle evidence below comes from vendor pages and search (cited per row);
> **JLCPCB assembly tier is UNKNOWN for every part and must be filled in by the part-sourcer.**
> Install with:
> `claude mcp add --transport http pcbparts https://pcbparts.dev/mcp`
>
> Local KiCad symbol availability *was* verified with `skidl-part-search` /
> `/usr/share/kicad/symbols` and is reported per row — that is real, checked data.

---

## 1. ADC — dual 12-bit, ≥40 MSPS, **parallel CMOS** (constraint 4, and iCE40 has no usable LVDS SERDES)

| # | MPN | Ch × bits × rate | Interface | Power | SNR | Pkg | KiCad symbol | Evidence |
|---|---|---|---|---|---|---|---|---|
| **A1 ✅** | **LTC2292CUP / LTC2292IUP** (ADI) | 2 × 12 b × 40 MSPS | **parallel CMOS**, separate or MUX; separate OVDD 0.5–3.6 V; ~~CLKOUT data-ready pin~~ **← FALSE, see D3 note below** | **235 mW total** | **71.3 dB @ Nyquist, 71.4 dB typ**; SFDR 90 dB | QFN-64 (UP) 9×9 mm | **`Analog_ADC:LTC2292xUP` exists** ✔ | [ADI product page](https://www.analog.com/en/products/ltc2292.html) |
| A2 | AD9238BSTZ-40 (ADI) | 2 × 12 b × 40 MSPS | parallel CMOS, 3 V | ~300 mW @65 MSPS grade | ~70 dB | LQFP-64 | **none** ✘ | ADI; older part, symbol must be drawn |
| A3 | ADC12DL040CIVS (TI) | 2 × 12 b × 40 MSPS | parallel CMOS | ~358 mW | 70 dB | TQFP-64 | none ✘ | TI; NRND risk, higher power |

**→ RECOMMEND: LTC2292 (I-grade `LTC2292IUP#PBF` preferred for the 0–50 °C spec margin).**

Why it wins on every axis that matters here:
1. **Parallel CMOS.** ~~with a CLKOUT data-ready pin~~ — **RETRACTED 2026-09-07 (decision D3).**

   > **CORRECTION — the LTC2292 has no CLKOUT pin.** This claim was written from ADI's product
   > page while `analog.com` was stalling PDF downloads. It is false. Verified against
   > `datasheets/LTC2292_LTC2293_LTC2291_229321fa.pdf`: zero occurrences of "CLKOUT" in all
   > 28 pages; and against the KiCad symbol `Analog_ADC:LTC2292xUP`: 65 pins, no such pin.
   > The part has **CLKA (pin 8) and CLKB (pin 9), single-ended clock *inputs* only** — and no
   > ENC+/ENC− differential pair either.
   >
   > **This does not change the part selection.** The capture problem is solved instead by
   > clocking the FPGA's PIO input registers from the same 40 MHz XO that drives CLKA/CLKB,
   > on the **falling** edge. Against t_D = 1.4/2.7/5.4 ns that gives 7.1 ns setup and 13.9 ns
   > hold at 50 % duty, and never less than 5.85 / 12.65 ns across a 45-55 % duty range. The
   > full derivation, including why *rising*-edge capture is impossible (the iCE40's own
   > t_H = 2.38 ns exceeds t_D(min) = 1.4 ns outright), is in `net_plan.md` §1.4.1.
   >
   > Two further errors from the same source, corrected in `net_plan.md` §3.6: the part has
   > **no single `VREF` pin** (it has REFHA/REFLA and REFHB/REFLB pairs), and VCMA/VCMB,
   > SENSEA/SENSEB, SHDNA/SHDNB, OEA/OEB are **independent per-channel pins** — the datasheet
   > explicitly forbids joining VCMA to VCMB.
   >
   > **Process note:** the SNR figure from the same product page was also wrong (71.3 dB
   > Nyquist quoted where 71.4 dB @5 MHz applies). Two errors from one unverified source.
   > Nothing in this file sourced from a product page should be treated as settled.
2. **235 mW measured against SPEC's 350 mW allowance** — 115 mW back into the USB budget.
3. **Separate OVDD (0.5–3.6 V)**, so the 24 switching outputs run off `V3V3_D` through a ferrite and
   never touch `V3V0_AVDD`. This is the single most important structural defence for 12-bit SNR.
4. **A KiCad symbol already exists** (`Analog_ADC:LTC2292xUP`). A2 and A3 would each cost a
   hand-drawn 64-pin symbol — real schedule risk for zero performance gain.
5. Input span is programmable **1 Vpp to 2 Vpp**, so the ±1 V post-attenuator swing maps to full
   scale with **gain = 1 everywhere** — no gain stage, no extra noise, no extra offset term.

**⚠ Open datasheet items handed to `datasheet-librarian` (ADI's PDF host repeatedly timed out here):**
- Exact `SENSE` pin mapping and the external-reference voltage that yields a 2 Vpp span. The plan
  assumes **SENSE = 1.000 V ⇒ span = 2 × V_SENSE = 2 Vpp**. *If the LTC2292 instead wants SENSE tied
  to VDD for a fixed internal-2.5 V-derived span, `vref_2v5` changes from "divider to 1.000 V" to a
  different value — the block interface does not change.*
- S/H acquisition-delay jitter (aperture jitter) in ps RMS.
- Exact VDD range (assumed 3.0 V nominal; `power_analog` is set for 3.0 V).
- Whether `LTC2292CUP` (0–70 °C) or `LTC2292IUP` (−40–85 °C) is better stocked.

**Rejected outright:** every serial/LVDS dual 12-bit ADC (AD9231, AD9204, ADS4222, LTC226x). The
iCE40 HX has no SERDES and no usable input delay primitives; a 12-bit × 2-lane DDR LVDS stream at
480 Mbps/lane cannot be received reliably. Constraint honoured.

---

## 2. FPGA — Lattice iCE40, TQFP-144, open toolchain (**binding constraint 1**)

| # | MPN | Logic | I/O (TQ144) | Toolchain | KiCad symbol | Evidence |
|---|---|---|---|---|---|---|
| **F1 ✅** | **ICE40HX4K-TQ144** | 3520 LC advertised — **physically an HX8K die (7680 LC)** | **107** | Yosys/nextpnr/icestorm ✔ | **`FPGA_Lattice:ICE40HX4K-TQ144` exists** ✔ | [DigiKey — ships today](https://www.digikey.com/en/products/detail/lattice-semiconductor-corporation/ICE40HX4K-TQ144/220-1572-ND/3083582); [TrustedParts — in stock, low lifecycle risk](https://www.trustedparts.com/en/part/lattice/ICE40HX4K-TQ144); RS UK 55 units immediate |
| F2 | ICE40HX1K-TQ144 | 1280 LC | 95 | ✔ | exists ✔ | **too small** — see logic estimate below |
| F3 | ICE40HX8K-CT256 / -CB132 / -BG121 | 7680 LC | 206 / 107 / 107 | ✔ | `ICE40HX8K-BG121` exists | **BGA only — violates constraint 13's TQFP-144/hand-assembly intent** |

**→ RECOMMEND: ICE40HX4K-TQ144, but *build the bitstream as HX8K*.**

**`iCE40HX8K-TQ144` does not exist.** Lattice ships HX8K only in CB132 / CT256 / BG121 (all BGA).
The escape hatch is well documented: the HX4K-TQ144 **is** an HX8K die with the device ID changed, and
Project IceStorm / nextpnr expose the full 7680 LUTs with:

```
nextpnr-ice40 --hx8k --package tq144:4k --pcf pinout.pcf --json top.json --asc top.asc
```

Sources: [Project IceStorm](https://prjicestorm.readthedocs.io/en/latest/overview.html),
[icestorm issue #273](https://github.com/YosysHQ/icestorm/issues/273),
[element14 IceStorm thread](https://community.element14.com/technologies/fpga-group/f/forum/28129/project-icestorm-fully-open-source-fpga-tools-for-lattice-ice40)
("the iCE40HX4K in TQFP-144 is actually a rebadged 8K device … no reports of missing functionality").

### 2.1 Does it fit? — I/O

**99 pins committed of 107 available (8 spare).** Full table in `net_plan.md` §4.
All four banks at VCCIO = 3.3 V; `VCC_SPI` = 3.3 V matches the W25Q32JV; `VPP_2V5` accepts
2.30–3.47 V so it ties to 3.3 V. **No mixed-bank-voltage problem exists in this design.**
The only bank/pin constraint that survives to layout is that `xoClkFpga` and `ftClk60` (only two GBINs now — `adcClkOut` was deleted by D3)
must each land on a **GBIN** (global buffer input) pin — TQ144 has eight.

**Verdict: TQ144's I/O count and bank arrangement do work, with ~7 % headroom.**
If it ever gets tight, the escape hatch is the LTC2292's MUX mode (24 → 12 data pins at an 80 MHz
capture rate); it is *not* needed and costs a clock domain, so it stays unused.

### 2.2 Does it fit? — logic

| Function | Est. LUT4 | Est. FF | BRAM |
|---|---|---|---|
| 2 × CIC (N=4, R=2, 18-bit) | 300 | 300 | 0 |
| 2 × 21-tap symmetric decimating FIR, CSD constant multipliers, 16-bit | **1800–2500** | 600 | 2 |
| SRAM burst controller + circular pre-trigger addressing | 250 | 150 | 0 |
| Digital trigger engine (level/slope/either ch/force/ext) | 200 | 120 | 0 |
| FT2232H sync-245 drain + async FIFO (40 → 60 MHz CDC) | 300 | 200 | 2 |
| Control/status register file + slow-control SPI slave | 250 | 200 | 0 |
| **Total** | **3100–3800** | ~1570 | 4 |

**3100–3800 LUT4 is at or slightly over the HX4K's advertised 3520.** Built as HX8K (7680 LC) the
utilisation is ~45 %. **This is why the HX8K build flag is not a nicety — it is load-bearing.**

Fallback if the FIR still does not fit (record for the gateware stage): the **inverse-sinc droop
compensation does not have to be in gateware at all.** Capture is a buffered burst, not a stream, so
the host can apply the fixed linear correction after the drain. Only the *alias-rejecting* decimation
must be on-chip (it sits ahead of the SRAM). Folding the inverse-sinc into the same 21 taps is free,
so do that first; moving it host-side is the fallback, not the plan.

---

## 3. Buffer SRAM — 2 M × 16 async, **≤ 25 ns** (constraints 3 + the timing derivation below)

### 3.1 The timing requirement, derived

Sustained capture write rate = 2 ch × 10 MSPS × one **unpacked 16-bit word** each
= **20 M writes/s ⇒ 50 ns per word.**
The FPGA runs the SRAM state machine on the 40 MHz domain (25 ns/state) and uses **2 states per
word** (address/data setup, then WE# pulse) = exactly 50 ns/word. Therefore:

- **Device cycle time must be ≤ 25 ns** for a 1-state access, or ≤ 50 ns for the 2-state access.
- Choosing **10 ns** gives 5× margin on the device and leaves headroom for a future
  concurrent-drain mode (20 M writes + 20 M reads = 25 ns/access, still inside a 10 ns part).
- USB drain reads **do not contend** in the specified buffered-burst model (capture completes, then
  drain). This is stated so the gateware author does not have to rediscover it.

| # | MPN | Org | t_AA | Pkg | Stock evidence | Verdict |
|---|---|---|---|---|---|---|
| **S1 ✅** | **IS61WV204816BLL-10TLI** (ISSI) | 2 M × 16, 3.3 V | **10 ns** | TSOP-I-48 | **Digi-Key: "ships today", ~$33.54**; **Mouser: listed/available**; **LCSC C1349134 & C2065018: OUT OF STOCK** ([LCSC](https://www.lcsc.com/product-detail/C1349134.html), [Mouser](https://www.mouser.com/en/ProductDetail/ISSI/IS61WV204816BLL-10TLI?qs=cttFivMKqWz%2BDMMKFLCg1w%3D%3D), [DigiKey](https://www.digikey.com/en/products/detail/issi-integrated-silicon-solution-inc/IS61WV204816BLL-10TLI/6004263)) | **PRIMARY.** Meets spec with 5× margin. Off-JLC, hand-soldered TSOP — permitted by SPEC §6.1. |
| S2 | IS61WV204816BLL-**10BLI** | same | 10 ns | 48-ball TFBGA 6×8 | Cytech ref. $31.08 | Same die, BGA. Only if JLC places it — **cannot be hand-soldered**, so it defeats the off-JLC fallback. Second choice. |
| S3 | **AS6C3216-55TIN** (Alliance) | 2 M × 16 / 4 M × 8, 2.7–3.6 V | **55 ns** | TSOP-I-48 | **Digi-Key: "buy now, ships today"**, ~$8 ([DigiKey](https://www.digikey.com/en/products/detail/alliance-memory-inc/AS6C3216-55TIN/4234585)) | **❌ FAILS TIMING.** 55 ns cycle ⇒ max 18.2 M writes/s vs the 20 M required — short by 9 %. Cheap and in stock, and it *will* look like an attractive substitution to the sourcer. **It is not one.** |
| S4 | IS66WVE2M16 / IS66WVE4M16 (ISSI PSRAM) | 2 M × 16 / 4 M × 16 | ~70 ns random, ~20 ns page | BGA-54 / TSOP | not checked | **In-class per SPEC §1.2 ("async or pseudo-SRAM")** but random-cycle timing fails; only viable if the burst controller is rewritten for page-mode. Escalate before adopting. |
| S5 | 2 × IS61WV102416BLL-10 (1 M × 16 each, shared address) | 1 MS/ch each | 10 ns | TSOP-I-44 | good stock generally | **❌ I/O BUDGET FAILS.** Costs +17 FPGA pins (20 addr + 32 data + 5 ctrl vs 21+16+3) ⇒ 116 of 107. Not viable on TQ144. |

**→ RECOMMEND: IS61WV204816BLL-10TLI, sourced from Digi-Key or Mouser (not LCSC).**

**⚠ This is SPEC R1 materialising exactly as predicted.** Direction for the part-sourcer:
1. Confirm a real Digi-Key/Mouser quantity ≥ 5 (ideally ≥ 10 for spares) before anything else.
2. **Any substitute must have a cycle time ≤ 25 ns.** Speed grade is a hard functional requirement
   here, not a nice-to-have — put that sentence in the RFQ.
3. **Do not substitute AS6C3216-55.** It is in stock, cheap, same organisation, same package, same
   voltage, and it does not work. If it is the only thing available, that is an **escalation** with
   two options for the user: (a) drop to 9 MSPS/ch delivered, or (b) 5:1 decimation ⇒ 8 MSPS/ch.
   Neither is a silent change.
4. Migration inside the low-complexity class (constraint 3) is fine; **SDRAM/DDR is not.**

---

## 4. Power ICs

### 4.1 Buck, 5 V → 3.3 V digital (~200 mA)

| # | MPN | Vin | Iout | f_sw | Pkg | Note |
|---|---|---|---|---|---|---|
| **P1 ✅** | **TLV62569DBVR** (TI) | 2.5–5.5 V | 2 A | 1.5 MHz | SOT-23-6 | Correct Vin *minimum* for a 5 V bus; internal comp; commonly Basic/Preferred at JLC |
| P2 | RT8059GJ5 | 2.5–5.5 V | 1 A | 1.5 MHz | SOT-23-5 | Cheaper JLC Basic alternate |
| P3 | MP2315 / TPS563201 | **4.5 V min** | 3 A | 500 kHz–1.4 MHz | SOT-23-6 | **Reject:** 4.5 V minimum has no margin against a sagging USB bus |

**→ RECOMMEND TLV62569DBVR.** Note for layout: 1.5 MHz fundamental lands **inside** the 4.3 MHz
analog passband — it cannot be filtered out downstream. Mitigation is rail isolation + the corner
keep-out, not filtering. See `design_risks.md` §2.1.

### 4.2 LDO, 3.3 V → 1.2 V FPGA core (~40 mA)

| # | MPN | Note |
|---|---|---|
| **P4 ✅** | **TLV75512PDBVR** (TI, 1.2 V fixed, 500 mA, SOT-23-5) | Fixed 1.2 V is a stocked TI variant |
| P5 | AP2112K-1.2TRG1 | Cheaper, but the **1.2 V** option of AP2112K is a less-common variant — sourcer must verify |
| P6 | XC6206P122MR | 250 mA only; marginal, no thermal pad |

### 4.3 LDO, 5 V → 3.0 V ADC AVDD (~62 mA, low noise, isolated)

| # | MPN | Noise (10 Hz–100 kHz) | PSRR | Pkg |
|---|---|---|---|---|
| **P7 ✅** | **LP5907MFX-3.0/NOPB** | 6.5 µV RMS | 82 dB @ 1 kHz | SOT-23-5 |
| P8 | TPS7A2030PDBVR | ~12 µV RMS | 60 dB @ 100 kHz | SOT-23-5 |
| P9 | ADP151AUJZ-3.0 | 9 µV RMS | 70 dB @ 10 kHz | TSOT-5 |

**→ LP5907-3.0.** Fed from `VBUS_A5V` (post-ferrite) per SPEC §3.1 — **not** shared with digital 3.3 V.
The same part at 3.3 V (`LP5907MFX-3.3`) feeds the oscillator in `clock_40m`.

### 4.4 ±V analog rails — LM27762 (named in constraint 7)

Real datasheet numbers pulled from
[TI SNVSAF7C (Oct 2025 rev)](https://www.ti.com/lit/ds/symlink/lm27762.pdf):

| Parameter | Value |
|---|---|
| Adjustable output range | ±1.5 V to ±5 V |
| V_IN | 2.7–5.5 V |
| **f_SW** | **1.7 / 2.0 / 2.3 MHz (min/typ/max)** |
| R_NEG (charge-pump output resistance) | 2.5 Ω @ V_IN 5.5 V, I_L 100 mA |
| LDO dropout, positive | **45 mV @ 100 mA, V_OUT = 5 V** |
| LDO dropout, negative | **30 mV @ 100 mA** |
| Output noise (both) | 22 µV RMS, 10 Hz–100 kHz |
| Output ripple | ~1–5 mV p-p (Fig. 5-1/5-2) |
| I_Q | 390 µA |
| Package | WSON-12 (DSS), 2.5 × 3 mm |

#### ⚠ DEVIATION FROM SPEC §3.1's LITERAL "±5 V" — decision needed, flagged not buried

**Regulated ±5.0 V is not achievable from a 5 V USB bus with an LM27762-class part.** Arithmetic:

- **Positive rail:** the positive LDO's input is V_IN. USB VBUS is 4.75 V min at the receptacle
  (4.40 V worst case at the far end of a long cable), and this board drops a TVS/ferrite/soft-start
  FET in front of it. With 45 mV dropout, +5.00 V out needs ≥ 5.05 V in. **Unachievable.**
- **Negative rail:** CPOUT ≈ −(V_IN − I_L × R_NEG). At the ~20 mA this board draws that is only a
  50 mV loss, so CPOUT ≈ −4.70 V at V_IN = 4.75 V; minus 30 mV LDO dropout ⇒ −4.67 V max.

**→ Setting the rails to ±4.00 V** (FB dividers to V_FB+ = 1.200 V, V_FB− = −1.220 V) keeps both
regulators in regulation down to V_IN ≈ 4.1 V, i.e. through any realistic bus sag.

**What is actually lost:** nothing that SPEC §3.1 was buying. The rails exist to (a) keep the buffer
common mode off the rails, (b) remove level-shift gain/offset terms, and (c) give graceful overdrive
recovery. The signal at the buffer is ±1 V. ±4 V leaves **3 V of headroom** — the OPA1656 output
stage is the binding constraint long before the rails are. All three benefits are fully retained.

*If the user wants literal ±5 V,* the alternative is **TPS65133** (boost + inverter, regulated ±5 V
from 2.9–5.5 V in). It costs the integrated post-LDOs, so the analog rails go from "LDO-quiet with
1–5 mV of 2 MHz ripple" to "switcher-quiet" — a strictly worse trade on a 12-bit board. Recommend
**not** doing this; recorded so the choice is visible.

---

## 5. Voltage reference — external, ~2.5 V, 0.1 % / 10 ppm class (constraint 8)

| # | MPN | Init. acc. | Tempco | Pkg | I_Q | KiCad symbol |
|---|---|---|---|---|---|---|
| **R1 ✅** | **ADR4525BRZ** (ADI) | ±0.04 % | **2 ppm/°C max** | SOIC-8 | 950 µA | **`ADR4525` exists** ✔ |
| R2 | ADR3425ARJZ | ±0.10 % | 8 ppm/°C | SOT-23-6 | 100 µA | not in lib |
| R3 | REF5025AIDR | ±0.05 % | 3 ppm/°C | SOIC-8 | 800 µA | not in lib |

**→ ADR4525BRZ.** It beats the 0.1 %/10 ppm requirement by 2.5×/5× for about $6, has a KiCad symbol,
and its tempco is the single largest fixed contributor to the SPEC §2.1 **25 ppm/°C** drift target.
ADR3425 (R2) meets the letter of the spec at ~$2.50 and is the cost-down option if the sourcer finds
ADR4525 unavailable — that substitution is *inside* spec and needs no escalation.

**Reference chain consequence (new — not in SPEC):** the LTC2292 sets its span from a **~1 V**
`SENSE` input, not from 2.5 V. So the chain is
`ADR4525 (2.5 V) → 0.1 % thin-film divider (1.500 k / 1.000 k) → OPA192 unity buffer → SENSE`.
The divider adds a ratio error (removed by the per-board calibration in SPEC §2.1) and a **tracking**
drift term (~5 ppm/°C for matched thin-film) that stacks with the reference's 2 ppm/°C. Total
reference-path drift ≈ 7 ppm/°C — still well inside the 25 ppm/°C budget. Buffer:
**OPA192IDBVR** (5 µV V_OS, 0.5 µV/°C, SOT-23-5).

---

## 6. Sample clock — 40 MHz LVCMOS XO (constraint 5)

| # | MPN | Jitter (12 kHz–20 MHz) | Pkg | Note |
|---|---|---|---|---|
| **C1 ✅** | **ASFLMB-40.000MHZ-LC-T** (Abracon) | **≤1 ps RMS** | 5.0 × 3.2 mm | Quartz XO, matches SPEC's "≤1 ps class" literally |
| C2 | SiT8208AI-8F-33E-40.000000 (SiTime MEMS) | ~1.1 ps RMS | 3.2 × 2.5 mm | Excellent availability; MEMS |
| C3 | CCHD-957-25-40.000 (Crystek) | **0.13 ps RMS** | 7 × 5 mm | Bulletproof but ~$20 and ~35 mA — gold-plating |

**→ ASFLMB-40.000MHZ-LC-T primary, SiT8208 alternate.**

**Useful correction to SPEC R3's severity:** the aperture-jitter budget is **10.6 ps RMS** (SPEC §2.2,
arithmetic verified). A ≤1 ps part has **10× margin**; even an ordinary **3 ps** XO has **3.5× margin**
and would contribute only 40 µV RMS of the ~100 µV total noise at a 3 MHz full-scale input. R3 is
graded "Medium" in the SPEC; on the numbers it is **Low** — the 12-bit claim does *not* hinge on
finding a ≤1 ps part. The sourcer should still record the actual datasheet jitter number, but should
**not** escalate over a 2–3 ps substitute.

---

## 7. Analog front end

### 7.1 High-Z buffer + Sallen-Key (2 amps/channel, dual package)

| # | MPN | e_n | i_n | GBW | I_Q/ch | Supply | KiCad symbol |
|---|---|---|---|---|---|---|---|
| **B1 ✅** | **OPA1656ID** (TI) | **2.9 nV/√Hz @10 kHz** | **6 fA/√Hz @1 kHz** | 53 MHz | 3.9 mA | ±2.25 to ±18 V | **`OPA1656ID` exists** ✔ |
| B2 | OPA2810IDR | 6.7 nV/√Hz | ~fA | 70 MHz | 3.6 mA | ±1.35 to ±6 V | not in lib |
| B3 | AD8066ARZ | 7 nV/√Hz | 0.6 fA/√Hz | 145 MHz | 6.4 mA | ±2.5 to ±12 V | not in lib |

**→ OPA1656ID.** The CMOS input's **6 fA/√Hz current noise is the decisive spec**, not the voltage
noise: it sees a 90 kΩ Thévenin source. A bipolar amp at a typical 2 pA/√Hz would inject
2 pA × 90 kΩ = **180 nV/√Hz** — five times the resistor's own Johnson noise and instantly fatal to
the 12-bit claim. OPA1656 injects 6 fA × 90 kΩ = **0.54 nV/√Hz** (see §9, term 3). It also has the
lowest voltage noise available in a JFET/CMOS part at this bandwidth, runs from the ±4 V rails, and
has a KiCad symbol.

### 7.2 ADC driver — fully differential, DC-coupled (constraint: DC only, no transformer)

| # | MPN | e_n | I_Q | Supply | Input CM | KiCad symbol |
|---|---|---|---|---|---|---|
| **B4 ✅** | **THS4521ID** (TI) | 4.6 nV/√Hz @100 kHz | **0.95 mA** | 2.5–5.5 V single | **negative-rail input** | **`THS4521ID` exists** ✔ |
| B5 | ADA4940-1ACPZ | 3.9 nV/√Hz | 1.25 mA | ±2.5 V / +5 V | not negative-rail | `ADA4940-1xCP` exists ✔; [LCSC C468516](https://www.lcsc.com/product-detail/C468516.html) |
| B6 | THS4551 | 3.3 nV/√Hz | 1.37 mA | 2.7–5.5 V | negative-rail | not in lib |

**→ THS4521ID (SOIC-8).** The **negative-rail input range** is what earns it the slot: the signal is
a ground-referenced ±1 V swing, so the FDA's input common mode moves between 0.5 V and 1.5 V in normal
operation and can be pushed toward 0 V under overdrive. ADA4940 is 0.7 nV/√Hz quieter — worth
**3 µV of a ~100 µV total** (see §9), i.e. nothing. Robustness wins.

Supply arrangement: the FDA runs from the **LM27762 +4.00 V LDO output**, not from raw VBUS. That
gives it a genuinely quiet rail for free and removes a whole regulator from the tree.
`VOCM` is driven by the LTC2292's own `VCM` output (~1.5 V), which is the DC-coupling contract.

---

## 8. Remaining ICs (brief)

| Function | Recommended | Alternates | Notes |
|---|---|---|---|
| USB bridge | **FT2232HL** (LQFP-64) | FT2232HQ (QFN-64) | `FT2232HL` symbol exists ✔. **LQFP over QFN deliberately** — hand-inspectable, hand-reworkable, and the SPEC permits off-JLC hand placement for this part. Datasheet: core I_CC = **70 mA typ @1.8 V**, internal LDO from VREGIN 3.3 V ([FTDI DS_FT2232H §5.2](https://ftdichip.com/products/ft2232hl/)) |
| FT2232H EEPROM (**also the calibration store**, constraint 9) | **93LC66BT-I/OT** (4 kbit, 256×16, SOT-23-6) | 93LC56B (2 kbit) | 4 kbit chosen so the FTDI user area comfortably holds per-channel gain/offset/date. Wiring per FT2232H DS §3.3: DO→EEDATA via 2.2 k, DO pulled up 10 k |
| FPGA config flash (constraint 10) | **W25Q32JVSSIQ** (SOIC-8) | W25Q16JVSS | `W25Q32JVSS` symbol exists ✔. HX8K bitstream ≈ 1.1 Mbit; 32 Mbit leaves room for a golden image + user data |
| USB-C receptacle | 16-pin USB 2.0 type (e.g. TYPE-C-31-M-12) | GT-USB-7010ASV | `USB_C_Receptacle_USB2.0_16P` symbol exists ✔. **Dual 5.1 kΩ CC pulldowns**, D+/D− only (constraint 6) |
| USB ESD | **USBLC6-2SC6** | PRTR5V0U2X | JLC Basic |
| VBUS TVS | **SMAJ5.0A** | PESD5V0S1BA | |
| Inrush limiting (constraint 7: no post-enum load switch) | **DMP2160U P-FET + 100 k/100 n gate RC** (~5 ms always-on ramp) | NTC | This is a *soft-start*, permanently on after ramp — **not** a post-enumeration load switch. Bulk held to 10 µF on VBUS per USB inrush rules |
| AFE clamp diodes | **BAV199LT1G** (dual, low leakage ~3 nA) | BAS116 (1 nA) | 3 nA × 90 kΩ = **270 µV** of offset — inside the ±0.2 % FS (±2 mV) post-cal budget, and calibrated out anyway |
| AFE node-X TVS | 12 V bidirectional (e.g. **PESD12VS1UB**) | SMAJ12CA | Placed at node X, **not** at the BNC — see §10 |
| Attenuator trimmer | 5–30 pF SMD trimmer (Murata TZC3 / Sprague-Goodman) | — | ⚠ likely Extended/off-JLC; hand-adjusted at calibration |
| Ext-trigger clamp | **BAT54S** + PESD3V3L1BA | | |

---

## 9. ⭐ MANDATORY WORK ITEM W1 — INPUT-REFERRED NOISE BUDGET

> **This is SPEC §11 W1, the user-required deliverable from the approval gate.**
> The full derivation, including the correction to R5, lives in
> **`design_risks.md` §1 — "W1: Input-referred noise budget and expected ENOB"**.
> It is duplicated in outline here only so this file is not the dead end.

**Headline results:**

| | |
|---|---|
| **Expected ENOB (0–3 MHz input, at the 10 MSPS decimated output)** | **12.50 bits** |
| **Dominant term** | **The LTC2292's own SNR — 92.8 % of total noise power** |
| Attenuator Johnson noise contribution | **0.19 %** of total noise power |
| Total input-referred noise at the ADC input | **99.9 µV RMS** (of a 0.707 V RMS full-scale sine ⇒ SNR 77.0 dB) |
| Verdict vs the 12 ENOB target | **Above 12. No finding requiring a spec change.** |

**The SPEC's R5 premise is arithmetically incorrect** (not the multiplication — the model). R5 and the
gate's independent check both compute 38.6 nV/√Hz × √(4 MHz) ≈ 77 µV, which assumes the attenuator
node is *flat-band* to 4 MHz. It is not: the **same 20 pF input-capacitance requirement that R5 says
"cannot be designed away"** forces ~222 pF across the divider's Thévenin resistance, which band-limits
the attenuator's own thermal noise to a **7.96 kHz** corner. The correct integral is the classic
kT/C result: **√(kT/222 pF) = 4.3 µV RMS**, not 77 µV. Derivation, sanity checks and the "what if R5
were right anyway" case are all in `design_risks.md` §1.

**Dependencies still open (per SPEC §11 W1.3), to revisit after sourcing:**
- LTC2292 SNR is taken as **71.3 dB at Nyquist** from ADI's published figure. The datasheet PDF
  itself must be attached at the `datasheet-librarian` stage and the number re-read (ADI's PDF host
  timed out repeatedly here). SNR at 3 MHz input is *better* than the Nyquist figure, so 12.50 ENOB
  is the conservative end.
- If the ADC is substituted, **the ENOB number changes by essentially the ADC's SNR delta** — the
  front end contributes only 5.4 % of the noise power, so re-running W1 for a new ADC is a one-line
  recalculation, not a redesign.
