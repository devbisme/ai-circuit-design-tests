# Skeleton BOM — dual_adc_usb (per board, qty 5)

MPNs are architecture-level *suggestions*: verified in stock at JLCPCB on 2026-09-22 but not
yet footprint-checked. The part-sourcer owns final selection, LCSC codes and footprints.
Everything on this board is **Extended tier** for the actives — JLCPCB carries no Basic/Preferred
FPGA, HS-USB bridge or 12-bit 10 MSPS ADC.

`[CRIT]` = critical path, do not substitute without re-architecting.
`[FREE]` = substitute freely on equivalent specs.
`[PKG]`  = package is fixed by thermal/layout/pin-count.

## Active devices

| Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|
| FPGA + 8 MB in-package PSRAM | GW1NR-LV9QN88PC6/I5 | QFN-88 | 1 | `[CRIT]` `[PKG]` C5799578, 173 pcs, $23.32. **The whole memory architecture is this part.** No drop-in second source exists. Needs 51 free user I/O — verify |
| Dual 12-bit 40 MSPS ADC | ADS5231IPAGT | TQFP-64 | 1 | `[CRIT]` C2670079, 154 pcs, **$31.78 — flagged >$25**. Second source: 2× AD9220ARSZ-REEL (C653287, $14.19 ea) at +190 mW and board-level skew |
| USB 2.0 HS ↔ sync FIFO bridge | FT232HL | LQFP-48 | 1 | `[CRIT]` C51997, 2016 pcs, $9.72. Requires the EEPROM below to enter 245-sync-FIFO mode and to map ACBUS9 = PWREN# |
| Dual JFET op amp (input buffers, both channels) | AD8066ARZ-R7 | SOIC-8 | 1 | `[CRIT]` C9647, 1478 pcs, $9.07. Needs I_B ≤ 55 nA — bipolar-input parts do not qualify |
| Fully differential ADC driver | THS4521IDR | SOIC-8 | 2 | `[CRIT]` C16092, 12 361 pcs, $1.75. Runs on +3.3 VA; V_OCM from the ADC CM pin |
| 10.000 MHz CMOS XO, ±30 ppm | SX3M10.000M20F30TNN | SMD3225-4P | 1 | `[FREE]` C2901558, $0.32. Any ±50 ppm CMOS XO, ≤3.3 V, ≤20 mA. Low jitter matters, frequency accuracy does not |
| Load switch, 2 A, soft-start | TPS22918DBVR | SOT-23-6 | 1 | `[CRIT]` C131941, 8480 pcs, $0.40. EN must be 5 V-tolerant and active-high |
| Buck 5 V→3.3 V / 5 V→1.2 V | TLV62569DBVR | SOT-23-5 | 2 | `[FREE]` C141836, 135 k pcs, $0.08. Any ≥600 mA synchronous buck with a **0.6 V** reference; a different V_REF means different feedback resistors |
| LDO 3.3 V analog, low noise | RT9013-33GB | SOT-23-5 | 1 | `[FREE]` C47773, 240 k pcs, $0.14. ≥150 mA, ≤50 µV_RMS |
<!-- revised: rev.2 — 1.8 V rail for U5 VCCIO3 (embedded-PSRAM bank) -->
| **LDO 1.8 V, U5 VCCIO3 / PSRAM bank** | **AP2127K-1.8TRG1** | SOT-23-5 | 1 | `[CRIT]` **U14.** C151375, 35 912 pcs, $0.154. Requirements, in priority order: fixed **1.800 V ±2 %**; V_IN 3.0–3.6 V; **I_OUT ≥ 150 mA**; **built-in soft-start with t_on ≥ 180 µs** (DS117 Table 3-3 caps the VCCIO ramp at 10 mV/µs — a fast LDO violates it and no output cap fixes it); stable with ≥1 µF ceramic; SOT-23-5. Second source: RT9013-18GB (C59969, 20 557 pcs, $0.171 — same footprint and vendor as U12) or TLV73318PDBVR (C882824, 11 871 pcs, $0.129). **Both alternates need their t_on confirmed against the 180 µs floor before substitution.** |
| Inverting charge pump | TPS60403DBVR | SOT-23-5 | 1 | `[FREE]` C11338, $0.70. ≥40 mA. **Prefer a switching frequency ≥1 MHz if a pin-compatible option exists** — 250 kHz lands in-band |
| USB ESD array | USBLC6-2SC6 | SOT-23-6 | 1 | `[FREE]` |
| FT232H configuration EEPROM | 93LC56BT-I/OT | SOT-23-6 | 1 | `[CRIT]` C190271, $0.44. 93LC46/66 variants are **not** interchangeable — the FT232H expects 93LC56 organisation |
| Logic-level NMOS (EN inverter) | BSS138 | SOT-23 | 1 | `[CRIT]` V_GS(th) ≤ 1.5 V max. 2N7002 does **not** qualify at 3.3 V drive |
| Input clamp diode, low leakage | BAV199 | SOT-23 | 2 | `[FREE]` I_R ≤ 5 nA at 25 °C — leakage appears directly as input offset |
| ADC input clamp | BAT54S | SOT-23 | 4 | `[FREE]` Schottky pair per leg to P3V3A/GND |
| Status LEDs | 0603 green/red | 0603 | 2 | `[FREE]` |

## Connectors and mechanical

| Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|
| Analog input | KH-BNC50-3511 | TH right-angle | 2 | `[CRIT]` `[PKG]` C2837587, $0.93. BNC female is a `[HARD]` requirement |
| USB host port | TYPE-C 16PIN 2MD(073) | SMD | 1 | `[CRIT]` `[PKG]` C2765186, $0.07. 16-pin USB-2.0-only body; 6-pin bodies lack the second CC |
| FPGA JTAG | 1×6 2.54 mm pin header | TH | 1 | `[FREE]` |
| 12 MHz crystal (FT232H) | 12.000 MHz, 12 pF, ±30 ppm | SMD3225 | 1 | `[FREE]` |

## Passives — filter and gain critical (tolerance is a requirement, not a preference)

| Function | Value | Package | Qty | Notes |
|---|---|---|---|---|
| Divider top | 909 kΩ **0.1 %** (1 % fallback) | 0805 | 2 | `[CRIT]` sets input Z and DC gain. 0805 for the 75 V working rating at ±55 V input |
| Divider bottom | 90.9 kΩ **0.1 %** (1 % fallback) | 0603 | 2 | `[CRIT]` pair-matched with the top resistor |
| Divider compensation, top | 15 pF **C0G ±2 %** | 0603 | 2 | `[CRIT]` sets input capacitance (13.6 pF of the ~17.6 pF total) |
| Divider compensation, bottom | 130 pF + 15 pF **C0G ±2 %** | 0603 | 4 | `[CRIT]` 145 pF fixed + ~5 pF node stray = 150 pF target |
| FDA gain set | 1.00 kΩ and 1.10 kΩ **0.1 %** | 0402 | 4 + 4 | `[CRIT]` R_f/R_g = 1.100 sets full-scale match |
| FDA feedback cap | 4.7 pF C0G | 0402 | 4 | `[CRIT]` stability + the 5th pole |
| AAF series resistor | 100 Ω 1 % | 0402 | 4 | `[CRIT]` filter source termination |
| AAF inductor L1 | **3.3 µH ±5 %** | 0805 | 4 | `[CRIT]` SRF ≥ 40 MHz required. ±10 % misses both `[SOFT]` filter targets |
| AAF inductor L2 | **5.6 µH ±5 %** | 0805 | 4 | `[CRIT]` SRF ≥ 30 MHz required |
| AAF capacitor | **680 pF C0G ±2 %** | 0603 | 8 | `[CRIT]` ±5 % X7R is not acceptable here |
| ADC series isolation | 22 Ω | 0402 | 4 | `[FREE]` |
| ADC ISET | 56.2 kΩ 1 % | 0402 | 1 | `[CRIT]` datasheet-mandated value; it scales the ADC bias current |
| Clock series termination | 33 Ω | 0402 | 2 | `[FREE]` |
| CC pulldowns | 5.1 kΩ 1 % | 0402 | 2 | `[CRIT]` Type-C sink advertisement |
| FT232H REF | 12 kΩ 1 % | 0402 | 1 | `[CRIT]` FTDI-mandated |
| Buck feedback | 180 kΩ, 40.2 kΩ, 100 kΩ ×2, all 1 % | 0402 | 4 | `[CRIT]` computed against a 0.6 V V_REF — recompute if the regulator changes |
| Load-switch pull-up / CT | 100 kΩ, 1 nF | 0402 | 2 | `[CRIT]` pull-up **must** return to `FT_3V3`, never to `P3V3D` |
| Buck inductors | 2.2 µH, ≥1.5 A, shielded | 0806/1210 | 2 | `[CRIT]` `[PKG]` shielded — unshielded parts couple into the front end |
| Negative-rail filter | 4.7 Ω 1 % | 0402 | 1 | `[CRIT]` with 10 µF gives 37 dB at the 250 kHz pump frequency |
| Ferrite bead, +5 VA | 600 Ω @100 MHz, ≥1 A | 0805 | 1 | `[FREE]` |
| LED resistors | 1 kΩ | 0402 | 2 | `[FREE]` |
| EEPROM pull-up | 2.2 kΩ | 0402 | 1 | `[FREE]` |
| Reconfig pull-up (R53) | 10 kΩ | 0402 | 1 | `[FREE]` <!-- revised: rev.2 --> **returns to `P1V8`, not `P3V3D`** — RECONFIG_N is a BANK3 (1.8 V) pin |
| **MODE0 / MODE1 straps (R54, R55)** | 4.7 kΩ | 0402 | 2 | `[CRIT]` <!-- revised: rev.2 --> **both to `GND`** ⇒ MODE[1:0] = 00; MODE2 is not bonded on QN88P. Value and polarity taken from the Sipeed Tang Nano 9K reference schematic for this exact device (R17/R19). Leaving them NC leaves the configuration mode undefined |
| ~~ADC_SEL strap (R402)~~ | — | — | 0 | <!-- revised: rev.3 --> **DELETED, final.** TI SBAS295A p.19 requires a low-going reset pulse on SEL; a static strap cannot deliver it and risks an undisableable PLL (fails SPEC F3). SEL is FPGA-driven. **Do not re-add R402.** |
| **FIFO_SIWU_N tie-off (R67)** | 10 kΩ | 0402 | 1 | `[FREE]` <!-- revised: rev.3 — refdes R66→R67 (collision). --> to `FT_3V3`, inactive-high. SIWU# is a plain input with no reset requirement, so unlike SEL it strapped safely. Frees one 3.3 V FPGA pin |
| **EEPROM `EE_DO` pull-up (R66)** | 10 kΩ | 0402 | 1 | `[CRIT]` <!-- revised: rev.3 — new; FTDI Table 3.3 mandates it alongside R64's 2.2 kΩ series. --> `EE_DO` → `FT_3V3`. Absent from rev.2 entirely. **This is the R66 that keeps the refdes**; the SIWU strap moved to R67 |
| **U1 (AD8066) HF decoupling (C15, C16)** | 100 nF X7R | 0402 | 2 | `[CRIT]` <!-- revised: rev.3 — new; rev.2 gave U1 no 100 nF at all. --> C15 on `VA_POS`, C16 on `VA_NEG`, at the pins. A 10 MSPS front-end op amp with only bulk caps is a real defect |
| **U6/U7 decoupling gap (C610–C612)** | 100 nF X7R | 0402 | 3 | `[CRIT]` <!-- revised: rev.3 — new. --> VPHY (U6.16), VPLL (U6.20), U7 VCC — three supply pins had none in rev.2 |
| **U6 internal-LDO caps (C606, C608)** | 100 nF X7R | 0402 | 2 | `[CRIT]` <!-- revised: rev.3 --> On `FT_VCORE_1V8` (U6.38) and `FT_VCCA_1V8` (U6.37). These pins are **LDO outputs**; each takes one cap to GND and nothing else — **never tie them to `FT_3V3` or to `P1V8`** |

## Passives — decoupling and bulk (`[FREE]`, per the policy in `net_plan.md`)

| Function | Value | Package | Qty (approx) |
|---|---|---|---|
| IC pin decoupling | 100 nF X7R 16 V | 0402 | 36 |
| **`P1V8` decoupling / bulk (C85, C86, C511–C513)** | 100 nF + 4.7 µF + 22 µF | 0402 / 0603 / 0805 | 5 |
| Local bulk | 1 µF X5R 16 V | 0402 | 8 |
| Rail bulk | 10 µF X5R 16 V | 0805 | 9 |
| Buck output bulk | 22 µF X5R 10 V | 0805 | 2 |
| VBUS bulk (≤10 µF total, USB inrush) | 10 µF X5R 25 V | 0805 | 1 |
| Charge-pump flying cap | 1 µF X7R 16 V | 0603 | 1 |
| Crystal load caps | 12 pF C0G | 0402 | 2 |

<!-- revised: rev.2 — +U14 and its passives, +4 strap resistors, +P1V8 decoupling -->
**Board totals:** **17** active devices, 4 connectors/mechanical, ≈61 critical passives,
≈62 decoupling/bulk passives.
<!-- revised: rev.3 -->
**161 refs.** Rev.3 delta against rev.2's 158: **+R67** (SIWU tie-off, resolving the R66
collision — R66 is now the EEPROM `EE_DO` pull-up), **+C15, +C16** (U1 decoupling),
**+C610, C611, C612** (U6/U7 decoupling gap), **−R402** (deleted, final).
C606/C608 were already allocated and are re-scoped, not added. **R66 keeps its number for the
EEPROM pull-up; nothing may collide with the existing set.** Estimated build cost ≈ **$89–91/board at qty 5** (see
`ic_selection.md § Cost roll-up`). One part is over the $25 flag: ADS5231IPAGT at $31.78.
