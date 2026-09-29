# Skeleton BOM — `dual_adc_usb`

- **Stage:** architecture (pre-sourcing). Quantities are **per board**; build qty = 5.
- **Tier column:** JLCPCB Basic/Preferred/Extended — **UNKNOWN for every line** because the
  `pcbparts` MCP is not connected in this environment. The part-sourcer must fill it in.
  The **Sourcing rule** column states the policy that applies to each line.
- Rationale for every IC choice is in `ic_selection.md`.

Legend for **Sourcing rule**:
- `JLC-B/P` — must be JLCPCB Basic or Preferred, stock > 100 (passives/jellybeans, SPEC §6.1)
- `CRIT` — one of the four critical ICs: Extended-tier or off-JLC (Digi-Key/Mouser, hand-placed) is **permitted**
- `TH` — through-hole, hand-soldered at prototype qty (SPEC §5), not sent to JLC assembly
- `ADJ` — hand-adjusted at calibration

---

## 1. Critical ICs (SPEC §6.1 — off-JLC permitted)

| Ref | Function | Suggested MPN | Package | Qty | Sourcing rule | Notes |
|---|---|---|---|---|---|---|
| U7 | Dual 12-bit 40 MSPS ADC, parallel CMOS | **LTC2292IUP#PBF** (or CUP) | QFN-64 9×9 (UP) | 1 | CRIT | 235 mW, SNR **71.4 dB typ @5 MHz / 69.6 dB min** [VERIFIED-PDF], separate OVDD. **NO CLKOUT PIN — that claim was false (D3, 2026-09-07); clock pins are CLKA 8 / CLKB 9, inputs only.** KiCad `Analog_ADC:LTC2292xUP` ✔. **Exposed pad must be soldered.** |
| U10 | FPGA | **ICE40HX4K-TQ144** | TQFP-144 | 1 | CRIT | Build bitstream as `--hx8k --package tq144:4k` (7680 LC). KiCad `FPGA_Lattice:ICE40HX4K-TQ144` ✔ |
| U11 | Buffer SRAM 2 M × 16 async | **IS61WV204816BLL-10TLI** | TSOP-I-48 | 1 | CRIT | **≤25 ns cycle is a hard functional requirement.** LCSC out of stock; buy Digi-Key/Mouser. **No KiCad symbol — must be generated** |
| U13 | USB 2.0 HS dual bridge | **FT2232HL** | LQFP-64 | 1 | CRIT | LQFP not QFN (hand-rework). KiCad `FT2232HL` ✔ |

---

## 2. Analog front end — **×2 channels** (qty below is per board, i.e. both channels)

| Ref | Function | Suggested MPN | Package | Qty | Sourcing rule | Notes |
|---|---|---|---|---|---|---|
| J2, J3 | BNC input, vertical PCB mount | Amphenol 031-6575 / Molex 73100-0105 class | TH vertical BNC | 2 | TH | SMD BNC rejected (SPEC §5, mechanical) |
| R101-103, R201-203 | Attenuator top leg, 3 × 300 k series | 300 kΩ **0.1 % thin film**, 25 ppm/°C, 0805 | 0805 | 6 | JLC-B/P | Split into 3 for voltage/pulse withstand. **Thin film, not thick film** — excess-noise and V-coefficient |
| R104, R204 | Attenuator shunt leg | 100 kΩ **0.1 % thin film**, 25 ppm/°C, 0805 | 0805 | 2 | JLC-B/P | Thévenin with top leg = 90 kΩ |
| C101, C201 | Attenuator top cap (sets input C) | 22 pF **C0G**, ≥250 V | 0805 | 2 | JLC-B/P | **Fixed C0G sets the 1 MΩ ∥ ~20 pF input spec** (0.9 × C1) — deliberately *not* a trimmer |
| C102, C202 | Attenuator shunt cap, fixed part | 180 pF **C0G**, 50 V | 0603 | 2 | JLC-B/P | |
| CV1, CV2 | Attenuator compensation trimmer | 5–30 pF SMD trimmer (Murata TZC3 / Sprague-Goodman SGC3S) | SMD trimmer | 2 | ADJ | ⚠ likely Extended/off-JLC. In the **shunt** position so input capacitance stays fixed |
| D101, D201 | Node-X clamp to ±4 V rails | **BAV199LT1G** (dual, low leakage) | SOT-23 | 2 | JLC-B/P | 3 nA leakage × 90 kΩ = 270 µV offset, calibrated out |
| D102, D202 | Node-X ESD/overvoltage | **PESD12VS1UB** (12 V bidirectional) | SOD-323 | 2 | JLC-B/P | **At node X, not at the BNC** — capacitance is free there |
| U101, U201 | High-Z buffer + Sallen-Key (2 amps) | **OPA1656ID** | SOIC-8 | 2 | JLC-B/P | 2.9 nV/√Hz, **6 fA/√Hz** (the decisive spec). KiCad `OPA1656ID` ✔ |
| U102, U202 | FDA / SE→diff ADC driver | **THS4521ID** | SOIC-8 | 2 | JLC-B/P | Negative-rail input, 0.95 mA, runs from +4.00 V. KiCad `THS4521ID` ✔ |
| R105-110, R205-210 | Sallen-Key + FDA gain/filter resistors | 249 Ω **0.1 %** thin film | 0402 | 12 | JLC-B/P | 0.1 % on the FDA Rg/Rf pairs sets CMRR and gain match; low R keeps filter Johnson noise down |
| R111-112, R211-212 | ADC input series damping | 33 Ω 1 % | 0402 | 4 | JLC-B/P | |
| C103-108, C203-208 | Sallen-Key + differential filter caps | C0G, values per 4th-order Butterworth fc = 4.3 MHz | 0402 | 12 | JLC-B/P | **C0G mandatory** — X7R V-coefficient is a distortion source |
| R113-114, R213-214 | Per-amp rail RC series element | **10 Ω 1 %** | 0603 | 4 | JLC-B/P | **Mandatory, and an RC not a ferrite** — a 600 Ω@100 MHz bead is only ~10–30 Ω at 2 MHz. 10 Ω + 10 µF = 1.6 kHz pole ⇒ 62 dB at 2 MHz. Rejects the LM27762 residue (`design_risks.md` §2.2) |
| C109-112, C209-212 | Per-amp rail decoupling | 10 µF X7R 16 V + 100 nF X7R | 0805 / 0402 | 8 | JLC-B/P | The 10 µF is the RC's capacitor — not optional |

---

## 3. Reference and clock

| Ref | Function | Suggested MPN | Package | Qty | Sourcing rule | Notes |
|---|---|---|---|---|---|---|
| U5 | Precision 2.5 V reference | **ADR4525BRZ** | SOIC-8 | 1 | JLC-B/P | ±0.04 %, **2 ppm/°C max**. KiCad `ADR4525` ✔. Alt: ADR3425ARJZ (0.1 %/8 ppm, in-spec cost-down) |
| U6 | Reference divider buffer | **OPA192IDBVR** | SOT-23-5 | 1 | JLC-B/P | 5 µV V_OS, 0.5 µV/°C |
| R30, R31 | 2.500 V → 1.000 V divider | 1.500 kΩ / 1.000 kΩ **0.1 % thin film**, matched TC | 0603 | 2 | JLC-B/P | Ratio error calibrated out; **TC tracking** (~5 ppm/°C) is what matters |
| U8 | Oscillator LDO | **LP5907MFX-3.3/NOPB** | SOT-23-5 | 1 | JLC-B/P | Own filtered supply for the XO (SPEC §2.2) |
| U9 | 40 MHz sample clock | **ASFLMB-40.000MHZ-LC-T** | 5.0 × 3.2 mm XO | 1 | JLC-B/P | ≤1 ps RMS class. Alt: SiT8208AI-8F-33E-40.000000. **≤3 ps is acceptable** — budget is 10.6 ps |
| R40 | ENC series termination | 33 Ω 1 % | 0402 | 1 | JLC-B/P | Shortest path, single load |
| R41 | FPGA clock tap | 100 Ω 1 % | 0402 | 1 | JLC-B/P | High-Z tap, keeps the ENC net clean |
| L7 | XO supply ferrite | 600 Ω @ 100 MHz | 0603 | 1 | JLC-B/P | |

---

## 4. Power tree

| Ref | Function | Suggested MPN | Package | Qty | Sourcing rule | Notes |
|---|---|---|---|---|---|---|
| J1 | USB-C receptacle, USB 2.0 | TYPE-C-31-M-12 (or GT-USB-7010ASV) | SMD 16-pin | 1 | JLC-B/P | D+/D− only. KiCad `USB_C_Receptacle_USB2.0_16P` ✔ |
| R1, R2 | CC pulldowns (sink presentation) | 5.1 kΩ 1 % | 0402 | 2 | JLC-B/P | **Dual pulldowns, constraint 6** |
| D2 | USB data ESD | **USBLC6-2SC6** |  SOT-23-5 | 1 | JLC-B/P | |
| D1 | VBUS TVS | **SMAJ5.0A** | SMA | 1 | JLC-B/P | |
| Q1 | Inrush soft-start P-FET | **DMP2160U** | SOT-23 | 1 | JLC-B/P | Always-on after ~5 ms RC ramp. **Not** a post-enumeration load switch (constraint 7) |
| R3, R4, C5 | Soft-start gate RC | 100 kΩ ×2, 100 nF | 0402 | 3 | JLC-B/P | |
| L1, L2 | 5 V bus / analog-branch split ferrites | 600 Ω @ 100 MHz, ≥1 A | 0805 | 2 | JLC-B/P | **The analog/digital split at source** (SPEC §3.1) |
| U1 | Buck 5 V → 3.3 V digital |  **TLV62569DBVR** |  SOT-23-5 | 1 | JLC-B/P | 1.5 MHz. Alt: RT8059GJ5 |
| L3 | Buck inductor | 2.2 µH, ≥2 A, shielded | 4×4 mm | 1 | JLC-B/P | **Shielded is mandatory** on a 12-bit board |
| R10, R11 | Buck FB divider | 1 % | 0402 | 2 | JLC-B/P | |
| U2 | LDO 3.3 V → 1.2 V FPGA core | **TLV75512PDBVR** | SOT-23-5 | 1 | JLC-B/P | Alt: AP2112K-1.2TRG1 (verify the 1.2 V variant is stocked) |
| U3 | LDO 5 V → 3.0 V ADC AVDD | **LP5907MFX-3.0/NOPB** | SOT-23-5 | 1 | JLC-B/P | 6.5 µV RMS noise. **Separate from digital 3.3 V** (SPEC §3.1) |
| U4 | ±4.00 V charge pump + dual LDO | **LM27762DSSR** | WSON-12 (DSS) 2.5×3 | 1 | JLC-B/P | KiCad `LM27762` ✔. **±4.0 V, not ±5 V** — see `ic_selection.md` §4.4 |
| C24 | LM27762 flying cap | 1 µF X7R 16 V | 0603 | 1 | JLC-B/P | |
| C25 | LM27762 CPOUT | 4.7 µF X7R 16 V | 0805 | 1 | JLC-B/P | |
| R20-23 | LM27762 FB dividers (±4.00 V) | 1 % | 0402 | 4 | JLC-B/P | V_FB+ = 1.200 V, V_FB− = −1.220 V |
| L4, L5, L6 | AVDD / ±4 V rail ferrites | 600 Ω @ 100 MHz | 0603 | 3 | JLC-B/P | |
| C1-C45 (power) | Bulk + decoupling | 10 µF/22 µF X7R 16 V; 100 nF X7R 25 V | 0805 / 0402 | ~30 | JLC-B/P | VBUS bulk held to **10 µF** for USB inrush compliance |

---

## 5. Digital

| Ref | Function | Suggested MPN | Package | Qty | Sourcing rule | Notes |
|---|---|---|---|---|---|---|
| RN1-RN6 | ADC data-bus damping, 33 Ω | 4-element resistor array, 33 Ω 5 % | 0603 4-array (e.g. YC164) | 6 | JLC-B/P | **24 data lines exactly** (6 × 4). OFA/OFB take discrete R44/R45; there is no CLKOUT to damp (D3). Arrays save ~18 placements |
| U12 | FPGA SPI config flash | **W25Q32JVSSIQ** | SOIC-8 208-mil | 1 | JLC-B/P | HX8K bitstream ≈ 1.1 Mbit; room for a golden image. KiCad `W25Q32JVSS` ✔ |
| R60-R65 | Config-bus series + pull-ups | 100 Ω ×4, 10 kΩ ×2, 1 % | 0402 | 6 | JLC-B/P | **100 Ω series on all 4 shared SPI lines is required** (MPSSE/FPGA/flash bus sharing) |
| JP1 | Config mode strap | 1×3 2.54 mm header + shunt | TH | 1 | TH | Self-boot vs MPSSE override (constraint 10) |
| U14 | FT2232H EEPROM = **calibration store** | **93LC66BT-I/OT** (4 kbit, 256×16) |  SOT-23-5 | 1 | JLC-B/P | Constraint 9. DO→EEDATA via 2.2 k; DO 10 k pull-up |
| Y1 | FT2232H crystal | 12.000 MHz, ±30 ppm, 18 pF | 3225 SMD | 1 | JLC-B/P | **Its own crystal**, not shared (SPEC §4.3) |
| C132, C133 | Crystal load caps | 27 pF C0G | 0402 | 2 | JLC-B/P | Trim to the crystal's C_L |
| R70 | FT2232H REF resistor | 12.0 kΩ 1 % | 0402 | 1 | JLC-B/P | Per FTDI datasheet |
| L9, L10 | FT2232H VPLL / VPHY ferrites | 600 Ω @ 100 MHz | 0603 | 2 | JLC-B/P | Per FTDI reference design |
| L8 | ADC OVDD ferrite (from V3V3_D) | 600 Ω @ 100 MHz | 0603 | 1 | JLC-B/P | Keeps output-driver di/dt out of AVDD |
| R71-R80, C130-C150 | FT2232H reset/decoupling | 10 kΩ, 2.2 kΩ, 100 nF, 4.7 µF | 0402/0603 | ~20 | JLC-B/P | 100 nF at **every** VCCIO/VCORE pin |
| C90-C123 | FPGA + SRAM decoupling | 100 nF X7R ×~26, 10 µF ×4 | 0402 / 0805 | ~30 | JLC-B/P | 100 nF per VCC/VCCIO pin; iCE40 VCCPLL via 10 Ω RC |

---

## 6. Auxiliary I/O and mechanical

| Ref | Function | Suggested MPN | Package | Qty | Sourcing rule | Notes |
|---|---|---|---|---|---|---|
| J4 | Probe-comp output terminal | 1×2 2.54 mm header / test loop | TH | 1 | TH | ~1 kHz, ~1.00 Vpp (constraint 12) |
| R90, R91 | Probe-comp divider | 2.32 kΩ / 1.00 kΩ 1 % | 0402 | 2 | JLC-B/P | 3.3 V × 0.301 = 1.00 V; Z_out = 699 Ω |
| J5 | External trigger header | 1×3 2.54 mm | TH | 1 | TH | trig / GND / GND, bidirectional (constraint 11) |
| R92, R93 | Ext-trig series + pulldown | 100 Ω, 10 kΩ | 0402 | 2 | JLC-B/P | |
| D10 | Ext-trig clamp | **BAT54S** | SOT-23 | 1 | JLC-B/P | To V3V3_D / GND |
| D11 | Ext-trig ESD | PESD3V3L1BA | SOD-523 | 1 | JLC-B/P | |
| D12, D13 | Status / activity LEDs | green, amber | 0603 | 2 | JLC-B/P | |
| R94, R95 | LED resistors | 1 kΩ | 0402 | 2 | JLC-B/P | |
| — | Mounting holes ×4 | M3 | — | 4 | mech | ~100 × 80 mm bare board |
| — | PCB | 4-layer, sig/GND/pwr/sig, 1.6 mm | — | 1 | — | JLCPCB, top-side SMD assembly only |

---

## 7. Rough cost sanity check (single-qty, informational)

| Group | Est. $/board |
|---|---|
| LTC2292 | 22–30 |
| IS61WV204816BLL-10TLI | **20–34** (Digi-Key $33.54 listed) |
| ICE40HX4K-TQ144 | 12–18 |
| FT2232HL | 6–9 |
| OPA1656 ×2, THS4521 ×2, OPA192, ADR4525 | 14–18 |
| LM27762, 3 × LDO, buck, XO | 10–14 |
| W25Q32, 93LC66, USB-C, BNC ×2, connectors | 8–12 |
| ~120 passives, 0.1 % thin films, trimmers, ferrites | 12–18 |
| **Total** | **≈ $104–153** |

**Above the SPEC §6 "$70–100 acceptable" band**, driven mainly by the SRAM ($20–34) and the ADC.
SPEC §6 says "no ceiling; no spec compromises on cost grounds", so this is reported, not acted on.
The one honest cost lever that costs nothing technically: **ADR4525BRZ → ADR3425ARJZ** saves ~$4 and
still meets the stated 0.1 %/10 ppm class.

---

## 8. Handoff notes for `part-sourcer`

1. **Fill in the JLCPCB tier column** — it is UNKNOWN throughout because `pcbparts` MCP was not
   connected. Install it: `claude mcp add --transport http pcbparts https://pcbparts.dev/mcp`
2. **SRAM first.** It is SPEC R1 and it is already showing stress (LCSC out of stock). Get a real
   Digi-Key/Mouser quantity before sourcing anything else. **Any substitute needs cycle time ≤ 25 ns**
   — put that in writing. **Do not accept AS6C3216-55** (in stock, cheap, same package, *fails*).
3. **No KiCad symbol exists for the SRAM.** Generate one (`datasheet-to-symbol-lib` skill on the ISSI
   TSOP-I-48 datasheet) or the coder will stall. Every other significant IC has a stock symbol —
   verified against `/usr/share/kicad/symbols`.
4. **0.1 % thin-film resistors** (attenuator, FDA gain pairs, reference divider) are a *specification*,
   not a preference (SPEC §2.1). Thick-film 0.1 % is not an acceptable substitute — V-coefficient and
   excess noise.
5. **C0G/NP0 is mandatory** on every capacitor in the signal path and the attenuator. X7R there is a
   distortion mechanism, not a tolerance question.
6. **XO jitter:** record the actual datasheet number. **≤3 ps RMS is acceptable** (budget is 10.6 ps).
   Do not escalate over a 2–3 ps substitute; see `ic_selection.md` §6.
7. The trimmer caps (CV1/CV2) are the most likely JLC gap after the SRAM — they may need to come
   from Digi-Key and be hand-placed alongside the TH parts.
