# Sourced BOM — `dual_adc_usb`

- **Stage:** part sourcing (complete, pending user approval)
- **Date:** 2026-09-06
- **Build qty:** 5 boards; all prices are **single-quantity USD** unless noted
- **Live data sources:** `mcp__pcbparts__jlc_search` / `jlc_stock_check` (LCSC/JLCPCB library),
  `digikey_get_part`, `mouser_get_part`. Every stock and price figure below carries its source.
- **Tier column:** now filled from live JLCPCB library data (was UNKNOWN at architecture).

> **STATUS: APPROVED BY USER 2026-09-06.** Both open decisions answered. See §0.

---

## 0. Decisions — RESOLVED

| # | Item | **User decision (2026-09-06)** |
|---|---|---|
| **D1** | SRAM topology | **OPTION (a): 1× IS61WV204816BLL-10TLI**, ~$33.54, Mouser stock 1303, Active. Single 2M×16 device, 21 address lines, matches the existing net plan with **zero architecture rework**. User accepts it is off-JLC and becomes a fifth hand-soldered part including a 0.5 mm-pitch TSOP-48. **Option (b) is explicitly NOT to be substituted.** |
| **D2** | 40 MHz XO | **Populate YXC OT322540MJBA4SL** (LCSC C2831396, $0.55, stock 14 369) on the universal 3225 footprint. **Jitter is UNVERIFIED and MUST be measured at bring-up.** Rationale accepted: 40 MHz is fundamental-mode with no PLL, so generic parts are typically 1–3 ps; MEMS often worse; the footprint makes it a drop-in swap. |

**Cost ~$175–185/board is acknowledged and accepted by the user.** Report it; do **not** re-optimize
for it. The Basic/Preferred tier finding (§7.4) is likewise accepted as unmeetable.

### 0.1 ⚠ CARRY-FORWARD — must not be lost between sourcing and bring-up

**XO jitter (D2) is an unverified number on the critical path of the 12-bit claim.**

| Item | Value |
|---|---|
| Part populated | YXC OT322540MJBA4SL, LCSC C2831396, $0.55, 3225 4-pad, ±10 ppm |
| Published jitter spec | **NONE — the manufacturer publishes no jitter figure at all** |
| Expected (inference, not fact) | 1–3 ps RMS, because 40 MHz is fundamental-mode with no PLL multiplication |
| **Practical threshold** | **~5 ps RMS** |
| Headline aperture budget | 10.6 ps (SPEC §2.2) — but this is *not* the operative number |
| **Consequence if it measures 10 ps** | **~0.7 ENOB lost**; jitter-limited SNR falls to 74.5 dB, comparable to the whole 76.96 dB budget |
| Action required | **Measure at bring-up.** If > 5 ps, swap to a jitter-specified 3225 part — drop-in, no board change |

Jitter-limited SNR at 3 MHz full scale = `−20·log₁₀(2π·f·t_j)`: 1 ps → 94.5 dB; 3 ps → 84.9 dB;
5 ps → 80.5 dB; **10 ps → 74.5 dB**.

Also recorded in `architecture/design_risks.md` (R3).

---

## 1. Hard-floor compliance summary

| Floor (SOURCING_BRIEF §4) | Status | Evidence |
|---|---|---|
| SRAM cycle ≤ 25 ns (single-device topology) | **PASS** | All recommended options are 8–10 ns. AS6C3216 (55 ns) rejected — §2.1 |
| Buffer op-amp i_n ≤ ~100 fA/√Hz | **PASS** | OPA1656 CMOS input; I_b 20 pA, I_os 20 pA (JLC C1849431 parametrics). Datasheet i_n = 6 fA/√Hz to be confirmed from PDF at the datasheet stage |
| XO ≤ 3 ps RMS acceptable | **UNRESOLVED** | No in-stock 40 MHz part with a *published* jitter number was found. See §5 / D2 |
| 0.1 % thin-film in signal path | **PASS** | §7.1 — all thin-film, all confirmed in stock |
| C0G in signal path | **PASS** | §7.2 |
| **ADC SNR ≥ 68.5 dB (substitution gate)** | **NOT TRIPPED** | No ADC substitution made — LTC2292 retained. The SNR figure itself is still unverified from the PDF; see §3.1 |

---

## 2. SRAM — the R1 risk, resolved

### 2.1 AS6C3216 shared-bus scheme: EVALUATED AND REJECTED

Rejected on **two independent grounds**, either of which is sufficient.

**(a) Timing — fails.** From `datasheets/AS6C3216A.pdf` (Alliance Memory AS6C3216A-55TIN,
Rev 1.0, Mar 2017, p.6, "AC ELECTRICAL CHARACTERISTICS — (2) WRITE CYCLE"):

| Parameter | Sym | Min |
|---|---|---|
| Write cycle time | t_WC | 55 ns |
| Address valid to end of write | t_AW | **50 ns** |
| Chip enable to end of write | t_CW | 50 ns |
| Address set-up time | t_AS | 0 ns |
| Write pulse width | t_WP | **45 ns** |
| Write recovery time | t_WR | 0 ns |
| Data to write time overlap | t_DW | 25 ns |
| Data hold from end of write | t_DH | 0 ns |
| Write to output in High-Z | t_WHZ | 20 ns (max) |

Against a **50 ns shared bus slot** (20 M words/s total across both devices):

- **t_AW = 50 ns min** against an address valid for exactly 50 ns in its slot → **zero margin**.
- **t_WP = 45 ns min** inside a 50 ns slot leaves 5 ns for everything else.
- Neither survives iCE40 pin-to-pin output skew (typ. ±1–2 ns across 21 address + 16 data lines),
  PCB propagation skew, or 40 MHz clock jitter.
- Generation is awkward independently: at 40 MHz the FPGA's granularity is 25 ns (12.5 ns using
  both edges). A 45 ns WE# pulse is not cleanly generatable, so WE# would have to be asserted for
  the entire 50 ns slot — which is exactly the zero-margin case.
- t_WHZ is footnoted "guaranteed by device characterization, **but not production tested**."

Per-device t_WC = 55 ns *is* satisfied (each device writes every 100 ns) — as the brief anticipated,
that was never the binding constraint. The binding constraints are t_AW and t_WP, and both fail.

**No stretch was applied. The scheme is rejected.**

The technically clean two-device variant — simultaneous 32-bit write, shared address and WE#,
separate data buses — is the architect's already-rejected option **S5**, which fails on pin count
(+16/17 pins against 8 spare).

**(b) Availability and cost — the premise has inverted.** The brief assumed ~$16 for two devices
against $33.54 for one. That is wrong by ~4.5×:

| MPN | Source | Stock | Price | Lifecycle |
|---|---|---|---|---|
| AS6C3216-55TIN (the exact part in the brief) | Digi-Key 1450-1026-ND | **0** | — | **Discontinued at Digi-Key** |
| AS6C3216A-55TIN (successor) | Digi-Key 1450-1414-ND | 543 | **$36.46** | Active |
| AS6C3216A-55TIN | Mouser 913-AS6C3216A-55TIN | **0** | — | **Obsolete** |
| AS6C3216A-55TIN | LCSC C1348728 | **0** | $54.26 | Extended |

Two AS6C3216A = **$72.92**, versus $33.54 for one IS61WV204816BLL. The cheap option is neither
cheap nor available.

### 2.2 The real options

**Capacity required:** 1 MS/ch × 2 ch × 16-bit unpacked = 2 M words = **32 Mbit total**.

**Structural finding:** all **155** SRAM parts in the JLCPCB library are Extended tier
(basic = 0, preferred = 0). Tier is not a discriminator here, and SPEC §6.1's relaxation covers it.
The specified 2M×16 IS61WV204816BLL **does not appear in the JLCPCB library at all**; the largest
fast in-stock JLC part is 16 Mbit.

| Opt | Configuration | Cost | Stock / source | Pins | Timing margin | Assembly |
|---|---|---|---|---|---|---|
| **(a)** | 1× **IS61WV204816BLL-10TLI** (2M×16, 10 ns, TSOP-I-48) | **$33.54** | Mouser 870-WV204816BLL10TLI, **stock 1303**, Active. Also Digi-Key 706-1467-ND, stock 327, $35.55 | 21 addr + 16 data + 3 ctrl | 10 ns vs 50 ns slot — 5× | **Off-JLC, hand-soldered** TSOP-48 |
| **(b)** | 2× **IS61WV102416BLL-10TLI** (1M×16, 8 ns, TSOP-I-48), one per channel, shared addr + shared data, separate CE# | **$55.80** ($27.90 ea) | LCSC **C28124**, **stock 2195**, Extended | 20 addr + 16 data + 2 CE# + 2 ctrl (**≈ +2 net**) | 8 ns vs 50 ns slot — 6× | **In JLC stock → machine-placed** |
| (c) | 4× IS61WV51216EDBLL-10TLI (512K×16, 10 ns) | $51.56 | LCSC C57407, stock 630, Extended | +4 CE#, 4 placements | ample | machine-placed |

**Note the key asymmetry:** the shared-bus time-multiplex scheme that *fails* on 55 ns parts
*works comfortably* on 8–10 ns parts. Option (b) is a shared bus and it is not marginal — it has
6× margin. The AS6C3216 failure was a speed-grade failure, not a topology failure.

### 2.3 Recommendation — but this is D1, your call

**Recommended: option (a)**, 1× IS61WV204816BLL-10TLI, $33.54 from Mouser.

Rationale: it matches the architecture, net_plan, and pin budget exactly as written — zero rework.
It is $22 cheaper. Stock is deep (1303) and the part is Active at two distributors.

- **(a) pros/cons** — Pro: cheapest; no architecture change; single placement; 21-bit address already
  in the net plan. Con: **not in JLC stock**, so it is a fifth hand-soldered part, and it is a 0.5 mm-pitch
  48-pin TSOP — the hardest hand-solder on the board. Needs a KiCad symbol generated.
- **(b) pros/cons** — Pro: **machine-placed by JLC**, removing the riskiest hand-solder operation;
  deeper stock (2195); one device per channel is conceptually cleaner for the gateware; 8 ns part.
  Con: +$22.26; two TSOP-48 placements; +2 FPGA pins (8 spare, so it fits); needs a KiCad symbol
  *and* a net_plan revision.
- **(c)** — dismissed: 4 placements and 4 CE# lines for no cost or timing advantage over (b).

**My read:** if you are hand-assembling 5 prototypes anyway, (a) is right. If you want JLC to place
everything it can, the $22 in (b) buys away a genuine assembly-yield risk on a fine-pitch part.
I am not deciding this for you.

---

## 3. Critical ICs (SPEC §6.1 — Extended / off-JLC permitted)

| Ref | Function | MPN | Tier | Stock | Unit $ | Source |
|---|---|---|---|---|---|---|
| U7 | Dual 12-bit 40 MSPS ADC | **LTC2292IUP#PBF** | **off-JLC** (not in JLC library) | 344 | **$51.64** | Digi-Key 505-LTC2292IUP#PBF-ND, Active |
| U10 | FPGA iCE40HX4K | **ICE40HX4K-TQ144** | Extended | 52 | **$18.44** | LCSC **C1521989** |
| U11 | Buffer SRAM 2M×16 async, 10 ns | **IS61WV204816BLL-10TLI** | **off-JLC** (not in JLC library) | 1303 | **$33.54** | Mouser 870-WV204816BLL10TLI, Active. **SELECTED — D1 option (a)** |
| U13 | USB 2.0 HS dual bridge | **FT2232HL** (reel) | Extended | 5202 | **$11.34** | LCSC **C27882**. Tray variant C1521564, stock 49, $12.62 |

### 3.1 ADC — SNR gate PASSES, now VERIFIED FROM THE DATASHEET PDF

No ADC substitution was made, so the substitution gate was never triggered. **And the underlying
number is now verified**, closing the long-standing open item.

Source: `datasheets/LTC2292_LTC2293_LTC2291_229321fa.pdf` (28 pp), Dynamic Accuracy table **p.4**,
LTC2292 column, A_IN = −1 dBFS:

| Input frequency | SNR |
|---|---|
| **5 MHz** (the design's band) | **71.4 dB typ** — no min specified |
| 20 MHz | **69.6 dB MIN over full temp** / 71.3 dB typ |
| 70 MHz | 71.1 dB typ |
| 140 MHz | 70.7 dB typ |

SFDR @5 MHz = 90 dB. From p.1: 235 mW, single 3 V supply (2.7–3.4 V), 575 MHz full-power-bandwidth
S/H, 1–2 V(P-P) input range. **Gate: SNR ≥ 68.5 dB → PASS.**

**Correction to the architecture:** the ≤3 MHz band maps to the **5 MHz** spec = **71.4 dB**, not the
71.3 dB *Nyquist* figure the architecture assumed.

**Recomputed budget** (non-ADC noise power unchanged):

| Case | ADC term | Total | SNR | **ENOB** |
|---|---|---|---|---|
| 71.4 dB typ | 95.2 µV | 99.2 µV | 77.06 dB | **12.51** (was 12.49) |
| 69.6 dB **guaranteed min** | 117.1 µV | 120.4 µV | 75.38 dB | **12.23** |

**Stronger claim than the architecture made:** 69.6 dB @20 MHz is the *only* guaranteed minimum in the
table. Taken as a pessimistic worst case — the part is essentially flat 5–20 MHz — **ENOB = 12.23. The
≥12 ENOB claim therefore holds at guaranteed minimum over full temperature, not merely typical.**

**Cost flag:** $51.64 actual against the architecture's $22–30 assumption — the largest contributor to
the cost overrun (§9).

**Alternative checked and rejected:** AD9238BSTZ-40 (dual 12-bit 40 MSPS, parallel CMOS, LQFP-64) —
Digi-Key **stock 0**, $45.47. Not viable at qty 5, and no cheaper. LTC2292 stands.

---

## 4. Analog front end (×2 channels)

| Ref | Function | MPN | Tier | Stock | Unit $ | Qty | Source |
|---|---|---|---|---|---|---|---|
| U101,U201 | High-Z buffer + Sallen-Key | **OPA1656IDR** | Extended | 6628 | $1.54 | 2 | LCSC **C1849431** |
| U102,U202 | FDA / SE→diff ADC driver | **THS4521IDR** | Extended | 13692 | $1.75 | 2 | LCSC **C16092** |
| D101,D201 | Node-X clamp, low leakage | **BAV199LT1G** (onsemi) | Extended | 505 972 | $0.028 | 2 | LCSC **C145516** |
| D102,D202 | Node-X ESD | PESD12VS1UB | Extended | — | ~$0.05 | 2 | LCSC — standard stock |
| J2,J3 | BNC vertical PCB mount | Amphenol 031-6575 class | **off-JLC, TH** | — | ~$2–3 | 2 | Hand-soldered per SPEC §5 |
| CV1,CV2 | Attenuator comp trimmer 5–30 pF | Murata TZC3 / Sprague-Goodman SGC3S | **off-JLC** | — | ~$1–1.50 | 2 | **Zero SMD trimmer capacitors in the JLC library** — confirmed by search. Digi-Key, hand-placed |

**OPA1656 note:** the JLC parametric row lists 4.3 nV/√Hz @1 kHz; the architecture's 2.9 nV/√Hz is
the broadband (≥10 kHz) figure. These are consistent, not contradictory — the noise budget uses the
broadband number and the AAF corner is at 4 MHz. Confirm both from the TI PDF at the datasheet stage.

**Trimmer confirmed as the architect predicted:** it is the largest JLC gap after the SRAM.

---

## 5. Reference and clock

| Ref | Function | MPN | Tier | Stock | Unit $ | Source |
|---|---|---|---|---|---|---|
| U5 | 2.5 V reference, 2 ppm/°C | **ADR4525BRZ** | Extended | 110 | $8.78 | LCSC **C395112** — ±0.02 %, 2 ppm/°C, 1.25 µVp-p |
| U6 | Reference divider buffer | **OPA192IDBVR** | Extended | 7457 | $1.76 | LCSC **C139648** — 5 µV V_OS, 200 nV/°C |
| U8 | Oscillator LDO | **LP5907MFX-3.3/NOPB** | Extended | 14 798 | $0.21 | LCSC **C80670** — 10 µVrms, 82 dB@1 kHz |
| U9 | **40 MHz sample clock** | **OT322540MJBA4SL** (YXC) | Extended | 14 369 | $0.55 | LCSC **C2831396** — 3225 4-pad, ±10 ppm, CMOS. **SELECTED — D2. ⚠ JITTER UNSPECIFIED — MEASURE AT BRING-UP (§0.1)** |

> **Stock flag:** ADR4525BRZ stock is **110** — the thinnest of any active line on this BOM.
> Sufficient for 5 boards, but order early. Architecture's in-spec cost-down alternate
> (ADR3425ARJZ, 0.1 %/8 ppm) remains available if stock moves.

### 5.1 D2 — the 40 MHz XO is unresolved. This is SPEC R3 materialising.

**Nothing in stock anywhere has a published phase-jitter number at qty 5.**

- **JLC:** 94 × 40 MHz oscillators in stock, **all Extended, none with any jitter specification**.
  All generic (YXC, TROQ, Yajingxin, TOGNJING, HCI, Interquip). Frequency tolerance (±10–50 ppm)
  is specified; jitter is not. Best candidate: **YXC OT322540MJBA4SL**, LCSC C2831396,
  stock 14 369, **$0.55**, 3225 4-pad, ±10 ppm, CMOS, 1.8–3.3 V.
- **Architecture's part, ASFLMB-40.000MHZ-LC-T:** Digi-Key **stock 0, min order qty 1000**. Dead for a
  5-board prototype.
- **ASEM1-40.000MHZ-LC-T:** Digi-Key stock 0 / MOQ 1000; Mouser stock 0 / MOQ 1000. Dead.
- **DSC1001CI2-040.0000:** Mouser stock 0, MOQ 660. Dead.
- SiT8008 and ECS-2520MV lookups **errored out** (Digi-Key daily quota) — *not* confirmed unavailable,
  just unverified. Flagging that explicitly.

**The engineering position, so you can decide with the numbers:**

Jitter-limited SNR at a 3 MHz full-scale input is `SNR = −20·log₁₀(2π·f·t_j)`:

| t_j (RMS) | Jitter-limited SNR | Effect on the 76.96 dB / 12.49 ENOB budget |
|---|---|---|
| 1 ps | 94.5 dB | negligible (<0.2 % of noise power) |
| 3 ps | 84.9 dB | ~1.6 % of noise power — negligible |
| 5 ps | 80.5 dB | ~4 % — still acceptable |
| 10 ps | 74.5 dB | **comparable to total budget; ~0.7 ENOB lost** |

So the practical threshold is **~5 ps**, not the 10.6 ps headline budget, and well above the 1 ps class
the architecture specified. **Relevant physics:** 40 MHz is a *fundamental-mode* crystal XO with no PLL
multiplication, so even generic parts are typically 1–3 ps RMS. MEMS oscillators (SiTime, Abracon
ASEM/ASFLMB) are PLL-based and are often *worse*, not better, on integrated jitter.

**Recommendation:** the 3225 4-pad footprint is universal across every candidate. **Lay out the standard
3225 footprint, populate the $0.55 YXC part for rev A, and measure jitter at bring-up.** If it measures
poorly, it is a drop-in swap with no board change. This costs nothing, defers the decision to a point
where you have data instead of a datasheet claim, and keeps a jitter-specified part as a documented
alternate.

Surfacing rather than deciding, because SPEC R3 explicitly requires you see this. Note also that the XO
is **not** one of the four §6.1-exempt ICs, so an off-JLC XO is a policy exception you would be granting.

---

## 6. Power tree

| Ref | Function | MPN | Tier | Stock | Unit $ | Source |
|---|---|---|---|---|---|---|
| U1 | Buck 5 V → 3.3 V, 1.5 MHz | **TLV62569DBVR** | Extended | 157 181 | $0.081 | LCSC **C141836** |
| U2 | LDO 3.3 V → 1.2 V core | **TLV75512PDBVR** | Extended | 3673 | $0.233 | LCSC **C2877864** |
| U3 | LDO 5 V → 3.0 V ADC AVDD | **LP5907MFX-3.0/NOPB** | Extended | 15 291 | $0.344 | LCSC **C475492** — **6.5 µVrms**, 82 dB@1 kHz |
| U4 | ±4.00 V charge pump + dual LDO | **LM27762DSSR** | Extended | 10 827 | $1.009 | LCSC **C473398** |
| D2 | USB data ESD | **USBLC6-2SC6 (STMicroelectronics)** | Extended | 48 237 | $0.183 | LCSC **C7519** |
| D1 | VBUS TVS | SMAJ5.0A | Basic/Extended | — | ~$0.05 | LCSC — standard stock |
| Q1 | Inrush soft-start P-FET | DMP2160U | Extended | — | ~$0.10 | LCSC |
| J1 | USB-C receptacle, USB 2.0 16P | TYPE-C-31-M-12 | Basic | — | ~$0.30 | LCSC — standard stock |
| L3 | Buck inductor 2.2 µH shielded ≥2 A | — | Basic | — | ~$0.10 | 4×4 mm shielded, mandatory |

### 6.1 Counterfeit/clone flag — acted on

`jlc_get_part("LP5907MFX-3.0")` returns **LCSC C23380873, manufacturer "TECH PUBLIC"** — a clone, not TI.
Its JLC parametric row lists **Noise: "-"** (unspecified) and PSRR 75 dB@1 kHz.

**This part was rejected.** The ADC AVDD rail is exactly where the LP5907's 6.5 µVrms noise spec is the
reason for choosing it; a clone with unspecified noise is not a substitute. The BOM specifies the
genuine TI **LP5907MFX-3.0/NOPB, LCSC C475492** (6.5 µVrms, 82 dB@1 kHz), stock 15 291, $0.344.

The same applies to **USBLC6-2SC6**: six clone manufacturers are listed (UMW, TECH PUBLIC, HXY, GOODWORK,
Slkor, KUU) at $0.03–0.09 with *differing* junction-capacitance claims. The BOM specifies genuine
**ST, LCSC C7519** at $0.183 for a USB 2.0 high-speed data line.

---

## 7. Passives — and a tier-policy collision

### 7.1 Precision resistors — 0.1 % thin film (SPEC §2.1, hard floor)

| Ref | Value | MPN | Tier | Stock | Unit $ | Qty |
|---|---|---|---|---|---|---|
| R101-103, R201-203 | 300 kΩ 0.1 % 0805, ±25 ppm/°C | **RT0805BRD07300KL** (YAGEO) | Extended | 60 258 | $0.052 | 6 |
| R104, R204 | 100 kΩ 0.1 % 0805, ±25 ppm/°C | **RT0805BRD07100KL** (YAGEO) | Extended | 592 975 | $0.049 | 2 |
| R105-110, R205-210 | 249 Ω 0.1 % 0402, ±25 ppm/°C | **RT0402BRD07249RL** (YAGEO) | Extended | 19 780 | $0.029 | 12 |
| R30, R31 | 1.5 kΩ / 1.0 kΩ 0.1 % 0603 | YAGEO RT0603 series | Extended | ample | ~$0.05 | 2 |

**Deliberate choice:** the 300 k and 100 k attenuator legs are **the same YAGEO RT series** so their
temperature coefficients track. Ratio TC tracking (~5 ppm/°C within a series), not absolute TC, is what
sets attenuator drift — and ±25 ppm/°C matches the SPEC §2.1 target of ~25 ppm/°C exactly.

**Upgrade available if wanted:** ±10 ppm/°C parts exist in the same footprint —
RT0805BRB07300KL ($0.41, stock 4460) and PTFR0805B300KN9 ($0.18, stock 5362). ~$0.70/board for
2.5× better TC. Not required by spec; noted, not applied.

### 7.2 C0G capacitors — signal path (SPEC hard floor)

| Ref | Value | MPN | Tier | Stock | Unit $ | Qty |
|---|---|---|---|---|---|---|
| C101, C201 | 22 pF C0G **250 V** 0805 | **GRM21A5C2E220JW01D** (Murata) | Extended | 1375 | $0.041 | 2 |
| C102, C202 | 180 pF C0G 50 V 0603 | Standard C0G | Extended | ample | ~$0.02 | 2 |
| C103-108, C203-208 | Filter caps, C0G 0402, per 4th-order Butterworth f_c = 4.3 MHz | Standard C0G | Extended | ample | ~$0.02 | 12 |

Lower-cost 250 V C0G alternates confirmed in stock: HHV0805G0220J251NTGJ (C5186739, stock 6940,
$0.0098) and 0805CG220J251NT (C20616279, stock 2382, $0.0096). Murata specified for the
input-capacitance-defining part because C101 sets the 1 MΩ ∥ 20 pF input spec; the others are free choice.

### 7.3 Digital and jellybean passives

| Ref | Function | MPN | Tier | Stock | Unit $ | Qty |
|---|---|---|---|---|---|---|
| RN1-RN6 | 33 Ω ×4 array, 1 % | **YC164-FR-0733RL** (YAGEO) | Extended | 45 159 | $0.023 | 6 |
| C (decoupling) | 100 nF X7R 0402 50 V | **CL05B104KB54PNC** (Samsung) | **BASIC / Preferred** | 21 750 952 | $0.0092 | ~60 |
| R (pull-ups etc.) | 10 kΩ 1 % 0402 | **0402WGF1002TCE** (Uniroyal) | **BASIC / Preferred** | 30 872 362 | $0.0031 | ~10 |
| R | 33 Ω / 100 Ω / 5.1 kΩ / 100 kΩ / 12 kΩ / 2.32 kΩ / 1 kΩ 1 % 0402 | Uniroyal 0402WGF series | **Basic** | ample | ~$0.003 | ~25 |
| C | 10 µF / 4.7 µF / 22 µF / 1 µF X7R 0805 | Samsung CL21 series | **Basic** | ample | ~$0.02 | ~25 |
| L1,L2,L4-L10 | Ferrite 600 Ω @100 MHz 0603/0805 | Standard | Basic | ample | ~$0.01 | 9 |
| Y1 | 12.000 MHz crystal ±30 ppm 18 pF 3225 | Standard | Extended | ample | ~$0.15 | 1 |
| D10-D13 | BAT54S, PESD3V3L1BA, LEDs ×2 | Standard | Basic/Extended | ample | ~$0.10 | 4 |
| JP1, J4, J5 | 2.54 mm headers | Standard | **TH** | — | ~$0.10 | 3 |

### 7.4 FINDING — the Basic/Preferred tier rule cannot be held (SPEC §6.1)

SPEC §6.1 says *"Passives and jellybeans: hold JLCPCB Basic/Preferred discipline, stock > 100."*

**Live data shows this is unachievable for the precision passives.** Every search returned
`basic: 0, preferred: 0`:

- **0.1 % thin-film resistors** — 0 Basic, 0 Preferred, across 300 k / 100 k / 249 Ω.
- **250 V C0G capacitors** — 0 Basic, 0 Preferred.
- **SRAM** — 0 Basic, 0 Preferred across all 155 parts.
- **Precision op-amps / references** — OPA1656, THS4521, ADR4525, OPA192 all Extended.
- **Resistor arrays** — 0 Basic across all 14 parts.

The tier check itself is sound — I verified it against known Basic parts, and CL05B104KB54PNC and
0402WGF1002TCE do come back `basic: true, preferred: true`. So this is real, not a data artifact.

**JLCPCB's Basic library simply does not contain 0.1 % thin-film or 250 V C0G parts.** SPEC §2.1 makes
both a specification, and SPEC §6.1 itself states *"The tier rule must not force a substitution that
breaks the specs settled in Q1–Q8."* **The specification wins; the tier rule is reported as unmeetable.**

True Basic/Preferred discipline **is** held where it is achievable: all generic decoupling, pull-ups,
bulk caps and 1 % thick-film resistors (~120 of ~160 placements) are Basic tier.

---

## 8. KiCad symbols

| Part | Symbol status |
|---|---|
| LTC2292, ICE40HX4K-TQ144, FT2232HL, OPA1656, THS4521, ADR4525, OPA192, LM27762, W25Q32, USB-C | Present in `/usr/share/kicad/symbols` (verified at architecture) |
| **SRAM IS61WV204816BLL** | ✅ **GENERATED** → `lib/dual_adc_usb.kicad_sym` |

Built via the **kipart MCP** from the genuine ISSI datasheet (`IS61/64WV204816ALL/BLL`, Rev. A,
10/27/2016, p.2 "PIN CONFIGURATIONS — 48-Pin TSOP, TYPE I"). **2M×16, 21 address lines** as selected
by D1 option (a) — not the 20-line 1M×16 variant.

**Verified programmatically after generation:**

| Check | Result |
|---|---|
| Total pins | 48 |
| Pins 1–48 each present exactly once | ✅ none missing, none duplicated, none out of range |
| Address pins A0–A20 | **21** ✅ |
| Data pins IO0–IO15 | **16** ✅ |
| Control (CE#, OE#, WE#, UB#, LB#), inverted style | 5 ✅ |
| Power (VDD ×2, GND ×2), `power_in` | 4 ✅ |
| No-connect (pins 6, 19) | 2 ✅ |
| Spot-check vs datasheet (17 pins incl. A0=5, A4=1, A5=48, A20=31, CE#=7, WE#=18, IO15=41, VDD=12/36, GND=13/37) | **all match** ✅ |

**Naming note (deliberate):** pin 7 is named **CE#**, matching `net_plan.md` §3.9 and the datasheet's
own BGA table (which labels the same pin CE#); the TSOP table calls it CS#. Likewise VSS is named
**GND** and I/O*n* is named **IO*n***, both matching the net plan so the block coder's references
resolve as written.

**Footprint:** `Package_SO:TSOP-I-48_18.4x12mm_P0.5mm`. The datasheet states "12mm x 20mm", which is
the **lead-tip span**; the JEDEC MO-142 **body** is 18.4 × 12.0 mm at 0.5 mm pitch. Same package —
reconciled, not assumed. Present in the stock KiCad library (verified on disk).

> **Housekeeping:** `datasheets/IS61WV204816BLL.pdf` from an earlier attempt is a **1157-byte Incapsula
> bot-block HTML page, not a datasheet**. Never cite it as a verified source. A project hook blocks
> writes and deletes under `datasheets/`, so it was left in place; the datasheet-librarian should
> overwrite it with the genuine PDF or write the real one under a clearly different filename and note
> the stale file in its report. The genuine 17-page PDF is staged and verified.

> **Housekeeping:** `datasheets/IS61WV204816BLL.pdf` from an earlier attempt is a **1157-byte Incapsula
> bot-block HTML page, not a datasheet**. Do not cite it. I could not remove it — a project hook blocks
> writes and deletes under `datasheets/`. Please delete it manually, or authorise the write.

---

## 9. Cost — materially above both prior figures

| Group | Architecture est. | **Sourced actual** | Δ |
|---|---|---|---|
| LTC2292 | $22–30 | **$51.64** | **+$22 to +$30** |
| SRAM | $20–34 | **$33.54** (opt a) / $55.80 (opt b) | in range / +$22 |
| ICE40HX4K-TQ144 | $12–18 | $18.44 | top of range |
| FT2232HL | $6–9 | $11.34 | +$2 to +$5 |
| OPA1656 ×2, THS4521 ×2, OPA192, ADR4525 | $14–18 | **$17.12** | in range |
| LM27762, 3× LDO, buck, XO | $10–14 | **$2.42** | **−$8 to −$12** |
| W25Q32, 93LC66, USB-C, BNC ×2, connectors, trimmers | $8–12 | ~$10–13 | in range |
| ~120 passives, 0.1 % thin films, ferrites | $12–18 | ~$6–8 | −$6 to −$10 |
| **Component subtotal** | **$104–153** | **≈ $151–157** (opt a) | |
| **JLCPCB Extended-part setup fees** | **not counted** | **≈ +$24/board** | **new** |
| 4-layer PCB, qty 5 | not counted | ~$5–10/board | |
| **Total per board** | $104–153 | **≈ $175–185** | |

### 9.1 What actually drove the overrun

1. **LTC2292 at $51.64** — roughly double the assumption. Single largest factor. No cheaper dual
   12-bit 40 MSPS parallel-CMOS part is in stock (AD9238 checked, stock 0).
2. **Extended-part assembly fees, previously uncounted.** ~40 unique Extended part types × ~$3
   one-time per order ≈ $120/order ≈ **$24/board at qty 5**. This follows directly from §7.4 — the
   precision parts are all Extended, and each one carries a setup fee.
   > **Uncertainty flagged:** JLCPCB's fee schedule has changed over time and some Extended parts are
   > now fee-free (the search tool exposes a `no_fee` library class). Treat $24/board as an
   > upper-bound estimate and confirm against their current schedule at quote time.
3. Power tree came in **well under** budget (−$8 to −$12) and partly offsets the above.

Against the Q9 discussion figure of $70–100, the board is roughly **2×**. Per SPEC §6
("no ceiling; no spec compromises on cost grounds") this is **reported, not acted on**.

### 9.2 Honest cost levers, if you want them

- **ADR4525BRZ → ADR3425ARJZ** — saves ~$4, stays within the stated 0.1 %/10 ppm class. The
  architecture already identified this as the one free lever.
- **Reduce unique Extended part types** by consolidating filter-capacitor values in §7.2 — each value
  eliminated saves ~$3/order. Possibly $15–20/order across the C0G set.
- Nothing else can be cut without breaking a settled spec.

---

## 10. Summary of flags

| # | Flag | Severity |
|---|---|---|
| F1 | **D1 — SRAM topology needs your decision** (§2.3) | **blocking** |
| F2 | **D2 — XO has no published jitter spec at any source** (§5.1); SPEC R3 requires you see this | **blocking-ish** — recommendation given |
| F3 | LTC2292 SNR still unverified from PDF; ADI host timed out 7× total. Datasheet-librarian must close it | high — 12.49 ENOB rests on it |
| F4 | Board cost ≈ $175–185, vs $104–153 architecture / $70–100 Q9 (§9) | high — reported per SPEC §6 |
| F5 | Basic/Preferred tier rule unmeetable for precision passives (§7.4); spec wins per SPEC §6.1 | medium — policy, resolved |
| F6 | Clone parts rejected for LP5907 (AVDD) and USBLC6 (USB data); genuine parts specified (§6.1) | medium — resolved |
| F7 | ADR4525BRZ stock only 110 — thinnest active line | low — order early |
| F8 | SMD trimmer caps: zero in JLC library; off-JLC hand-placed (§4) | low — architect predicted it |
| F9 | AS6C3216 rejected on timing **and** availability (§2.1) | resolved |
| F10 | `datasheets/IS61WV204816BLL.pdf` is a bot-block HTML page, not a datasheet (§8) | low — needs manual deletion |

---

## 11. Off-JLC / hand-soldered parts (assembly note)

| Part | Reason |
|---|---|
| LTC2292IUP#PBF | Not in JLC library. QFN-64, **exposed pad must be soldered** |
| SRAM (if option (a)) | Not in JLC library. TSOP-I-48, 0.5 mm pitch — hardest hand-solder on the board |
| BNC ×2, headers ×3 | TH, per SPEC §5 |
| Trimmer caps ×2 | Zero SMD trimmers in JLC library |
| XO (if a jitter-specified part is chosen) | See D2 |

Option (b) for the SRAM removes one hand-soldered fine-pitch part from this list.
