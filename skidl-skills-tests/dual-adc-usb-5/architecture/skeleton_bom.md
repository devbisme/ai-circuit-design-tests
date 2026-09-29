# Skeleton BOM — dual_adc_usb

Per board. The part-sourcer extends this with LCSC numbers, verified stock, tier, and
KiCad symbol/footprint. Refs match `handoffs/02_architecture.md` § Parts by block.

## Active / keystone

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| U5 | Dual 12-bit ADC, 20 MSPS/ch, simultaneous | ADS5231IPAGT | TQFP-64 (10×10) | 1 | **Critical path.** C2670079, stock 154, $31.77. Single source, verify NRND, **verify min clock ≤20 MHz** |
| U6 | FPGA + 8 MB in-package PSRAM | GW1NR-LV9QN88PC6/I5 | QFN-88, 0.4 mm | 1 | **Critical path.** C5799578, stock 180, $23.31. Single source. Package fixed by the part |
| U7 | USB 2.0 HS FIFO bridge | FT232HL-REEL | LQFP-48 | 1 | C51997, stock 2048. LQFP fixed by choice (reworkable); FT232HQ is the QFN version, stock 12 |
| U_fda1, U_fda2 | Fully differential ADC driver, G=2 | THS4551IRGTR | QFN-16-EP (3×3) | 2 | C2869590, stock 602. **Second source vetted:** THS4551IRUNR (C2060364, QFN-10, stock 4229) |
| U_buf1, U_buf2 | High-Z divider buffer, unity gain | OPA355NA/3K | SOT-23-6 | 2 | C2058090, stock 489. **CMOS input mandatory** (3 pA) — no bipolar substitution. Second source OPA355UA (SOIC-8, C2059993) |
| U4 | Dual reference buffer | OPA2376 / TLV9062 / OPA2333 | MSOP-8 or SOIC-8 | 1 | Freely substitutable. RRO, Vos ≤500 µV, ≥1 MHz, ≥10 mA |
| U8 | FT232H config EEPROM | 93LC46B or 93C46C, **×16 org** | SOIC-8 | 1 | C54935223 candidate — **verify ORG pin = ×16 and 3.3 V operation**. Mandatory: sync-FIFO mode lives here |
| X1 | ADC sample-clock oscillator | SX3M20.000B10F20TNN, 20.000 MHz | SMD3225-4P | 1 | C5452685, stock 3072. **≤5 ps RMS jitter required and unverified.** Second source OT252020MJBA4SL (C669067) |
| X2 | FT232H crystal | 12.000 MHz, ±30 ppm, 12 pF | SMD3225 | 1 | Jellybean |

## Power

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| U1 | 5 V → 3.3 V sync buck, 2 A | SY8089A1AAC | SOT-23-5 | 1 | C479074, stock 122 k, $0.086. **VREF = 591/600/609 mV confirmed** (`datasheets/SY8089A1AAC.pdf`) → R4 = 45.3 k / R5 = 10.0 k = 3.318 V, **unchanged**. Substitutable only for a sync buck with EN whose own VREF is datasheet-confirmed *and whose divider is recomputed for it* |
| U2 | 3.3 V → 1.2 V LDO, FPGA core | *spec:* 1.20 V ±3 %, ≥250 mA, dropout ≤200 mV@200 mA | **DFN/WSON with thermal pad** | 1 | **Package fixed by thermal:** dissipates 315 mW, the largest on the board. Adjustable preferred over fixed |
| U3 | 5 V → 3.3 V analog LDO | TLV75733PDRVR | WSON-6 (2×2), thermal pad | 1 | C2868428, stock 16 468. **Package fixed by thermal** (200 mW). Upgrade if TPS7A2033-class is in stock |
| U9 | Load switch, PWREN#-gated (**was Q1**) | AP2161WG-7 | SOT-23-5 | 1 | C176957, stock 8 848, $0.211. **Must have an ACTIVE-LOW, GND-referenced EN** (VIH ≤ 2.0 V so a 3.3 V level reads as "off") and a current limit **between 0.6 A and 2 A**. Symbol `Power_Management:AP2161W` exists. 2nd source WS4612EBB-5/TR (C42404603). **Never AP2171W — pin-identical, active-HIGH** |
| L1 | Buck inductor | 2.2 µH, ≥1.5 A sat, shielded | 0806 / 1210 | 1 | Shielded strongly preferred — it sits on a 12-bit analog board |
| FB1–FB4 | Ferrite beads | 600 Ω @ 100 MHz, ≥500 mA | 0603 | 4 | FB1 VBUS, FB2 → +3V3_ADCD, FB3 analog LDO input, FB4 oscillator supply |
| D2 | VBUS TVS | 5 V working, ≥200 W | SOD-123 | 1 | Jellybean |

## Connectors, protection, indicators

| Ref | Function | Suggested MPN | Package | Qty | Notes |
|---|---|---|---|---|---|
| J1 | USB-C receptacle | TYPE-C 16PIN 2MD(073) | SMD, right-angle | 1 | C2765186, stock 1.13 M. **16-pin only** — USB 2.0 pins, no SS pairs, no PD |
| J2, J3 | BNC analog input jacks | PCB board-edge BNC, 50 Ω body | through-hole | 2 | Not yet found by search — sourcer to locate. Board-edge, one edge of the PCB (H5) |
| J4 | FPGA JTAG header | 2×3 or 1×6, 2.54 mm | through-hole | 1 | TCK/TMS/TDI/TDO + 3V3 + GND |
| J5 | External trigger input | 1×2, 2.54 mm | through-hole | 1 | Nice-to-have (F13); costs one FPGA I/O |
| D1 | USB D+/D− ESD array | USBLC6-2SC6 | SOT-23-6 | 1 | C2687116, stock 107 k, $0.048 |
| D_clamp1, D_clamp2 | Front-end input clamp | BAV99 (dual series) | SOT-23 | 2 | Low capacitance matters — it lands on the divider node |
| D4 | Power LED | green, 0603 | 0603 | 1 | |
| D5 | Capture LED | red/amber, 0603 | 0603 | 1 | Driven by U6 |

## Precision passives — the ones that set performance

| Ref | Function | Value | Package | Qty | Notes |
|---|---|---|---|---|---|
| R_top_a, R_top_b (×2 ch) | Divider top leg, split for voltage rating | 475 kΩ ±0.5 % | 0805 | 4 | Two in series per channel = 950 kΩ. 0805 for the voltage rating, not the power |
| R_bot (×2 ch) | Divider bottom leg | 50.0 kΩ ±0.5 % | 0603 | 2 | Sets the ÷20 ratio with R_top; **tolerance sets channel-to-channel gain match** |
| C_top (×2 ch) | Divider HF compensation | 2–10 pF **trimmer** | SMD trimmer | 2 | **Not substitutable with a fixed capacitor** — see `design_risks.md` R-2 |
| C_bot (×2 ch) | Divider HF compensation | 82 pF ±2 %, C0G | 0603 | 2 | With node stray → ≈89 pF; trimmer nulls the remainder |
| R_prot (×2 ch) | Clamp current limit | 1.00 kΩ ±1 % | 0603 | 2 | |
<!-- revised: rev3 — ERC H-1 (MFB filter: R_mfb/C_mfb added, C_f/C_diff/C_cm retuned) and M-1 (R8/R9). -->
| R_g1, R_g2 (×2 ch) | MFB input resistors, set gain with R_f | 499 Ω ±0.1 % | 0603 | 4 | **±0.1 % matched pairs** — mismatch here becomes common-mode-to-differential error |
| R_f (×2 ch) | MFB feedback resistors — **rev 3: now land on the MFB node, not the FB pin** | 1.00 kΩ ±0.1 % | 0603 | 4 | Matched to R_g; sets G = R_f/R_g = 2.004 |
| **R_mfb (×2 ch)** | MFB series resistor, MFB node → FDA IN pin | 499 Ω ±0.1 % | 0603 | **4 (new)** | **New in rev 3** (refs R111/R112, R211/R212). Same MPN as R_g — carries no DC current, so it adds no offset |
| C_f (×2 ch) | MFB feedback capacitor, FB pin → OUT | **10 pF** ±5 %, C0G | 0603 | 4 | **rev 3: was ≈27 pF.** +0.6 pF internal to the THS4551 ⇒ 10.6 pF effective |
| **C_mfb (×1 ch)** | MFB differential capacitor (ref C111 / C211), `CH<n>_MFBP` ↔ `CH<n>_MFBN` | **68 pF** ±5 %, C0G | 0603 | **2 (new)** | **New in rev 3.** Differential, *not* two caps to GND — a cap to real GND here would couple into the FDA's CM loop |
| R_o, C_diff, C_cm (×2 ch) | Output RC (3rd pole) + ADC kickback filter | 33 Ω / **330 pF** / **100 pF**, C0G | 0603 | 10 | **rev 3: C_diff 470→330 pF, C_cm 220→100 pF.** R_o unchanged. Differential pole 6.35 MHz, CM pole 48 MHz |
| R8, R9 | VBIAS reference divider from +3V3_A | **R8 = 22.0 kΩ, R9 = 11.0 kΩ**, 1 % | 0603 | 2 | **rev 3: sets 1.100 V, was 1.200 V (21.0 k/12.0 k)** — OPA355 common-mode headroom, ERC M-1. 3.3·11/33 = 1.1000 V exactly; both are E24 jellybeans |
| R19 (top), R11 (bottom) | VREF_FE divider from VBIAS (0.95) — **values unchanged in rev 3**, output follows VBIAS to 1.0453 V | R19 = 1.00 kΩ, R11 = 19.1 kΩ, ±0.1 % | 0603 | 2 | **R19 is the VBIAS-side resistor, R11 the GND-side** — 19.1/20.1 = 0.95025. **Ratio must match the attenuator's 0.95** or a fixed offset appears; noise cancels because VREF_FE is derived from VBIAS |
| R22 | `VBIAS` isolation resistor at U4A's output | 10 Ω ±1 % | 0603 | 1 | **New in rev 2.** U4A drives 200–250 pF of `VBIAS`; feedback is taken inside R22. Jellybean value, but the part must exist — see `net_plan.md` |
| R20, R21 | U2 (1.2 V core LDO) FB divider | 11.8 kΩ / 10.0 kΩ, 1 % | 0603 | 2 | **Recorded in rev 2** — added by the `digital_power` coder because the block was allocated 5 resistor refs for 7 resistor functions. Values fixed by `handoffs/04_datasheets.md` decision 8 (VFB = 0.55 V), do not re-derive |
| R1, R2 | USB-C CC pulldowns | 5.1 kΩ ±5 % | 0603 | 2 | Exactly 5.1 kΩ — this is what advertises a 5 V sink |
| RA1–RA6 | ADC data-bus damping | 33 Ω, 4-element array | 0402 ×4 | 6 | 24 lines total, placed at the ADC end |

## Jellybean passives (sourcer's discretion, 0402 preferred)

| Function | Approx qty | Notes |
|---|---|---|
| IC decoupling 100 nF X7R | ~30 | One per supply pin, U5/U6 need the most |
| **C1, C2 = 4.7 µF 25 V X5R 0805** | 2 | CL21A475KAQNNNE (C1779, **Basic/Preferred**). 4.7 + 4.7 = **9.4 µF VBUS bulk**, inside SPEC P4's ≤10 µF. Was 2 × 10 µF, which violated it |
| Bulk 10 µF / 22 µF X5R | ~7 | **VBUS bulk ≤10 µF total** (SPEC P4 — inrush) — C1/C2 are now their own 4.7 µF line above. `digital_power` needs **4 × 10 µF 0805** (C3, C4, C6, C7) + 1 × 100 nF 0402 (C5), not the 4 × 100 nF + 1 × 10 µF the rev-1 sourcing guessed |
| 1 µF / 4.7 µF X7R | ~10 | Rail-local, LDO in/out, reference RC |
| C15 shield cap 1 nF + R12 1 MΩ | 2 | USB-C shield to GND |
| Pull-ups / pull-downs / LED resistors | ~10 | RESET#, RECONFIG#, EEDATA 2.2 k, trigger, LEDs |
| X2 load caps | 2 | Per crystal datasheet, ≈27 pF |

## Board

4-layer, ≤100 × 80 mm, all SMD except BNC jacks and headers, single-side placement.
Stack-up: signal / GND / power / signal. BNCs on one edge, USB-C on the opposite edge (H5).
