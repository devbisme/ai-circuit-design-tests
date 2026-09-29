---
phase: architecture
status: complete
next_phase: 03_sourcing
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Produced a complete architecture for the dual-channel ±10 V / 12-bit / 10 MSPS USB 2.0
  acquisition board: **9 blocks, 15 ICs, ~70 BOM line items, ≈$85–115/board at qty 5–10.**
- **Resolved the capture-buffer feasibility gap honestly.** 32,768 samples/ch does not fit
  any iCE40-class BRAM (16 kB max vs 98 kB needed), and the one FPGA that *does* fit it
  exactly (iCE40UP5K, 1 Mbit SPRAM) has only 39 I/O against a 46-pin minimum — it is not
  buildable. Chose **iCE40HX4K-TQ144 + a 512 kB external 10 ns SRAM**, which delivers
  **131,072 samples/channel (13.107 ms gap-free, both channels, full 10 MSPS, full
  12 bit)** — 4× the requested depth rather than a compromise.
- **Defined the missing control protocol.** Discovered the binding constraint: FTDI
  AN_130 states channel B is unusable when an FT2232H is in sync-FIFO mode, so the
  obvious "channel B = control" split does not exist. Defined a 4-byte in-band command
  frame on the same FIFO (7 commands: mode, decimation, depth, arm, readout, status,
  reset) needing **zero extra pins** — and consequently **downgraded FT2232H → FT232H**,
  since the second channel is provably dead weight.
- **Recomputed the AFE from the real ADC.** The requirements' provisional "~11:1, 0–2 V,
  CM ~1 V" become **20:1 passive attenuator + ×2 gain = 10:1 net**, ADC span
  **0.500–2.500 V**, **CM 1.500 V**, 1 LSB = 4.883 mV at the BNC, full scale ±10.000 V
  exactly. Noise budget closes at **ENOB ≈ 11.1 bits** against the ≥10.5 target.
- Also corrected two requirements numbers: the anti-alias filter must be **4th order**
  (2nd/3rd order miss the [HARD] ≥40 dB-by-15-MHz stopband), and dual-channel continuous
  streaming uses **integer decimation N ≥ 2 → 5 MSPS/ch**, not the fractional 8 MSPS/ch
  sketched in the spec.
- Power budget closes at **≈345 mA of the 500 mA USB ceiling (31% margin)**, with a
  PWREN#-gated analog section so pre-enumeration draw stays under 100 mA.
- 15 design risks logged; **7 remain open** and are named with owners.
- **Counts:** 9 blocks (11 instantiations) · 15 ICs · 7 of 15 risks unresolved · revision 1.

## Artifacts

| Path | What it contains | Read it when |
|------|------------------|--------------|
| architecture/block_diagram.md | Mermaid top-level flow, per-channel AFE detail, data-path modes, block list, ground strategy, 4-layer stackup | You need to see how the nine blocks connect, or which zone a part belongs in |
| architecture/net_plan.md | Every net: name, type, level, and the exact parts/pins on it, in 10 sections (power, USB, analog, clock, ADC buses, SRAM, FIFO, config, FT232H housekeeping, decoupling census) | You are wiring anything, or you need a net name verbatim |
| architecture/ic_selection.md | The two feasibility resolutions (buffer sizing, control protocol) + the AFE recomputation, then 2–4 candidates per block with pros/cons and a marked RECOMMENDED, then a fixed-vs-free summary table | **Sourcer: read this first.** It says what each part must do, not just what it is |
| architecture/skeleton_bom.md | Function / suggested MPN / package / qty / notes for all nine blocks, plus board totals and the itemised power budget | You are building the sourced BOM or checking the current budget |
| architecture/design_risks.md | 15 risks (R-01…R-15) with severity, mitigation, and what each one constrains in sourcing/layout/coding | Before substituting any part, and before starting layout |

## Block manifest

Nine blocks. `afe_channel` and `adc_channel` are **each instantiated twice** (channel A
and channel B) — one block file, two calls. Interface nets below use `<X>` for the
instance suffix `A`/`B`; every name matches `net_plan.md` exactly.

| block_id | block_name | function_signature | interface_nets |
|----------|------------|--------------------|----------------|
| `usb_c_input` | USB-C Input & Protection | `def usb_c_input(vbus, gnd, usb_dp, usb_dm):` | `VBUS, GND, USB_DP, USB_DM` |
| `power_digital` | Digital Power (3V3_D, 1V2) | `def power_digital(vbus, gnd, v3v3_d, v1v2):` | `VBUS, GND, V3V3_D, V1V2` |
| `power_analog` | Analog Power (gated) | `def power_analog(vbus, gnd, pwren_n, v3v3_a, v3v3_clk, v5_a, vn5_a, vref_0v5_a, vref_0v5_b):` | `VBUS, GND, PWREN_N, V3V3_A, V3V3_CLK, V5_A, VN5_A, VREF_0V5_A, VREF_0V5_B` |
| `clock_gen` | 10 MHz Low-Jitter Clock | `def clock_gen(v3v3_clk, gnd, clk_adc_a, clk_adc_b, clk_10m):` | `V3V3_CLK, GND, CLK_ADC_A, CLK_ADC_B, CLK_10M` |
| `afe_channel` | Analog Front End (×2) | `def afe_channel(bnc_sig, gnd, v5_a, vn5_a, v3v3_a, vref_0v5, adc_in, adc_vinn):` | `BNC_<X>_SIG, GND, V5_A, VN5_A, V3V3_A, VREF_0V5_<X>, ADC_<X>_IN, ADC_<X>_VINN` |
| `adc_channel` | 12-bit 10 MSPS ADC (×2) | `def adc_channel(adc_in, adc_vinn, adc_clk, pdwn, v3v3_a, v3v3_d, gnd, data, otr):` | `ADC_<X>_IN, ADC_<X>_VINN, CLK_ADC_<X>, ADC<X>_PDWN, V3V3_A, V3V3_D, GND, ADC<X>_D[11:0], ADC<X>_OTR` |
| `sram_buffer` | 512 kB Capture SRAM | `def sram_buffer(v3v3_d, gnd, addr, data, ce_n, oe_n, we_n, ub_n, lb_n):` | `V3V3_D, GND, SRAM_A[17:0], SRAM_D[15:0], SRAM_CE_N, SRAM_OE_N, SRAM_WE_N, SRAM_UB_N, SRAM_LB_N` |
| `usb_bridge` | FT232H USB2-HS Sync FIFO | `def usb_bridge(vbus, v3v3_d, gnd, usb_dp, usb_dm, fifo_data, rxf_n, txe_n, rd_n, wr_n, oe_n, clk60, pwren_n):` | `VBUS, V3V3_D, GND, USB_DP, USB_DM, FIFO_D[7:0], FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N, FIFO_WR_N, FIFO_OE_N, CLK60, PWREN_N` |
| `fpga_core` | iCE40HX4K Controller | `def fpga_core(v3v3_d, v1v2, gnd, adca_data, adca_otr, adca_pdwn, adcb_data, adcb_otr, adcb_pdwn, clk_10m, clk60, sram_addr, sram_data, sram_ce_n, sram_oe_n, sram_we_n, sram_ub_n, sram_lb_n, fifo_data, rxf_n, txe_n, rd_n, wr_n, oe_n, ext_trig, led_usb_n, led_cap_n):` | `V3V3_D, V1V2, GND, ADCA_D[11:0], ADCA_OTR, ADCA_PDWN, ADCB_D[11:0], ADCB_OTR, ADCB_PDWN, CLK_10M, CLK60, SRAM_A[17:0], SRAM_D[15:0], SRAM_CE_N, SRAM_OE_N, SRAM_WE_N, SRAM_UB_N, SRAM_LB_N, FIFO_D[7:0], FIFO_RXF_N, FIFO_TXE_N, FIFO_RD_N, FIFO_WR_N, FIFO_OE_N, EXT_TRIG, LED_USB_N, LED_CAP_N` |

Bus arguments (`*_data`, `sram_addr`, `fifo_data`, `sram_data`) are SKiDL `Bus` objects.
`fpga_core` additionally owns purely internal nets not in its signature: `SPI_SCK`,
`SPI_SI`, `SPI_SO`, `SPI_SS_N`, `CDONE`, `CRESET_N`, `LED_PWR`.

## Parts by block

Ref designators are the architect's scoping allocation. SKiDL assigns final designators;
this table exists so the sourcer knows *how many of what* each block needs and so the
orchestrator can scope work orders. `(×2)` blocks list refs **per instance** — instance A
uses the `1xx` series, instance B the `2xx` series.

| block_id | refs |
|----------|------|
| `usb_c_input` | J1, F1, D1, D2, FB1, R1, R2, R3, C1, C2 |
| `power_digital` | U1, U2, D3, R4, C3–C7 |
| `power_analog` | U3, U4, U5, Q1, FB2, FB3, FB6, L1, L2, R5–R9, C8–C21 |
| `clock_gen` | X1, U16, U17, R10–R12, C22–C24 |
| `afe_channel` (×2) | A: J2, U100, U101, D100, D101, R100–R115, C100–C112 · B: J3, U200, U201, D200, D201, R200–R215, C200–C212 |
| `adc_channel` (×2) | A: U110, FB10, R120–R133, C120–C132 · B: U210, FB20, R220–R233, C220–C232 |
| `sram_buffer` | U8, C41–C46 |
| `usb_bridge` | U6, U7, Y1, R13–R19, FB4, FB5, C25–C40 |
| `fpga_core` | U9, U18, J4, J5, D4, D5, D6, D7, R20–R26, C47–C64 |

## Key facts for the next phase

**Hard numbers the sourcer must not renegotiate:**

- Burst depth **131,072 samples/channel**, 13.1072 ms, both channels, gap-free, 10.000 MSPS,
  12 bit. Set by the 512 kB SRAM: 262,144 × 16-bit words ÷ 2 channels.
- Full scale **±10.000 V**; net BNC→ADC attenuation **10:1 (20.0 dB)** = 20:1 passive
  divider × 2 gain; ADC span **0.500–2.500 V**; CM **1.500 V**; **1 LSB = 4.8828 mV** at
  the BNC.
- Input impedance **1.000 MΩ** exactly (950 kΩ + 50 kΩ). ±40 V over-range is survivable by
  design — the attenuator node only reaches ±2.0 V.
- Anti-alias: **4th-order Butterworth, fc = 5.0 MHz** (−38 dB @ 15 MHz, −48 dB @ 20 MHz).
- Continuous streaming: single channel 10 MSPS = 15.0 MB/s; dual channel decimated
  **N ≥ 2 → 5.000 MSPS/ch = 15.0 MB/s**. Sync-FIFO sustained budget ≈30 MB/s.
- Power: **≈345 mA of 500 mA VBUS**. Rails 3V3_D 187 mA · 1V2 45 mA · 3V3_A 100 mA ·
  5V_A 58 mA · −5V_A 26 mA. Pre-enumeration ≈65–80 mA (PWREN#-gated).
- Ground: **one GND net, one solid plane.** No AGND/DGND split, no 0 Ω link.
- FPGA I/O used: **86 of 107**.

**Symbols already verified present** in `/usr/share/kicad/symbols`:
`FPGA_Lattice:ICE40HX4K-TQ144`, `Interface_USB:FT232H`, `Memory_Flash:W25Q32JVSS`,
`Memory_EEPROM:93CxxC`, `Regulator_Linear:AP7361C-33E`, `Regulator_Linear:AP2112K-1.2`,
`Regulator_Linear:LP5907MFX-3.3`, `Regulator_SwitchedCapacitor:LM2776`,
`Reference_Voltage:REF3025`, `Power_Protection:USBLC6-2SC6`, `Diode:BAV99`,
`74xGxx:74LVC1G34`, `Oscillator:ASE-xxxMHz`, `Connector:BNC`,
`Connector:USB_C_Receptacle_USB2.0_16P`.

**Symbols that do NOT exist and must be generated with `kipart`:** AD9235BRUZ-20 (28 pin),
IS61WV25616BLL-10TLI (44 pin), the AD8066 dual op-amp (8 pin), the OPA836 single op-amp
(6 pin). See `design_risks.md` R-14.

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|----------|--------------------|--------|-----|
| A1 | Capture buffer | reduce depth to fit BRAM (5,461/ch) / iCE40UP5K 1 Mbit SPRAM / larger FPGA + async SRAM / FPGA + SDRAM / ECP5 with 1 Mbit EBR | **iCE40HX4K-TQ144 + IS61WV25616 (512 kB, 10 ns)** | Only option that is buildable on pins *and* low-risk in gateware. UP5K fits the 32k exactly but has 39 I/O against a 46-pin minimum — not buildable. SRAM gives **131,072 samples/ch**, 4× the request, with 5× write-timing margin and no refresh/PHY/calibration |
| A2 | Control protocol | in-band frames on the sync FIFO / FT2232H channel B / GPIO straps / second bridge IC | **4-byte in-band command frames, `0xA5 CMD ARG_L ARG_H`** | FTDI AN_130: channel B is **unusable** when channel A is in sync-FIFO mode, which eliminates the split-channel option outright. In-band costs zero pins; the sync FIFO is already full-duplex |
| A3 | USB bridge | FT2232HL / **FT232HL** / FT600 (USB3) / Cypress FX3 | **FT232HL, LQFP-48** | Direct consequence of A2 — the FT2232H's second channel is provably dead in this mode, so it is pure cost, 16 extra pins and package area |
| A4 | ADC | AD9235BRUZ-20 / AD9226ARSZ / LTC2290 (dual) / ADS807E / ADC12010 | **AD9235BRUZ-20, TSSOP-28** | Only candidate meeting 12 b + ≥10 MSPS + parallel CMOS **and** the power budget: 2 × 40 mA vs the AD9226's 2 × 95 mA (38% of the entire USB budget). LTC2290 is electrically the nicest part in the field but ~$40–60 each breaks the cost target |
| A5 | ADC input drive | true single-ended ADC (AD9226) / single-ended-configured AD9235 / fully-differential driver | **Single-ended AD9235, VIN− at 1.500 V, 2 V p-p span** | Simplest AFE and lowest power; noise budget closes at ENOB ≈ 11.1 b vs the 10.5 target. The partitioning deliberately leaves a one-package upgrade to a differential driver if bench SFDR disappoints (R-07) |
| A6 | Attenuator ratio and level shift | 10:1 + ×1 (needs negative reference) / 10:1 with offset-return divider (single supply, but 1 MΩ no longer referenced to ground) / **20:1 + ×2 with positive reference** | **20:1 passive + ×2 gain, positive 0.5 V reference** | ×1 cannot add offset without a negative reference; ×2 lets a single positive reference do the whole shift, which is what allows A3 to run from +3V3_A. The offset-return alternative was rejected because it makes the 1 MΩ input read non-zero with the probe open — a real behavioural regression for a scope input |
| A7 | AFE output stage supply | ±5 V op-amp + Schottky clamps at the ADC / **+3V3_A single-supply op-amp** | **A3 (OPA836) on +3V3_A** | The amp's own rails become the ADC's over-voltage protection. Clamp diodes would add ~10 µA of leakage across 33 Ω ≈ 0.7 LSB of offset. Costs nothing, removes two parts per channel |
| A8 | Filter order | 2nd / 3rd / **4th** order | **4th-order Butterworth, fc = 5.0 MHz** | The [HARD] "≥40 dB by 15–20 MHz" is unreachable below 4th order: 2nd gives 19/24 dB, 3rd gives 29/36 dB, 4th gives 38/48 dB. Three op-amp stages per channel is the cost of that spec, not gold-plating |
| A9 | ADC sample clock source | FPGA fabric divide of the 60 MHz CLKOUT / FPGA PLL / **dedicated 10 MHz XO** | **Dedicated ≤5 ps RMS XO + 2× 74LVC1G34** | The 12-bit jitter budget at 5 MHz input is 12.7 ps RMS; fabric-generated clocks are 15–30 ps and would cost ≈1 bit of ENOB. **The sample clock must never pass through FPGA fabric** |
| A10 | FPGA | iCE40HX4K-TQ144 / MachXO2-4000HC-TG144 / iCE40HX1K-TQ144 / iCE40UP5K / Gowin GW1NR-9 | **iCE40HX4K-TQ144** | Only candidate with enough I/O (107 vs 86 needed) *and* a verified KiCad symbol *and* an open toolchain *and* a non-BGA package. MachXO2 is the better silicon (single rail, internal config flash) but has no KiCad symbol for any device — a hand-built 144-pin symbol is avoidable defect risk |
| A11 | Grounding | split AGND/DGND joined by a 0 Ω link / **single continuous GND** | **One GND net, one solid plane, isolation by placement** | With a 39-line SRAM bus and a 60 MHz FIFO bus, a split plane detours return current and radiates more than it isolates. Modern ADI/Kester practice for converter boards |
| A12 | Regulation topology | LDOs throughout / buck for 3V3_D / buck for everything | **LDOs throughout** | At 345 mA the 0.67 W of linear loss is affordable and buys a 12-bit-clean supply. Buck for 3V3_D is documented as the **contingency** if measured draw exceeds 450 mA (R-09), not the default |
| A13 | Dual-channel continuous rate | fractional decimation to 8 MSPS/ch (as sketched in requirements) / **integer N ≥ 2 → 5 MSPS/ch** | **Integer decimation, N ≥ 2** | A fractional 1.25 decimator is needless FPGA complexity. N = 2 gives 15.0 MB/s = 120 Mbps with >2× margin under the ~30 MB/s FIFO budget, satisfying the [HARD] ceiling constraint |
| A14 | USB enumeration compliance | ignore (draw 345 mA at plug-in) / **gate the analog section with PWREN#** | **FT232H ACBUS9 = PWREN# gates V5_A, V3V3_A and the LM2776** | 345 mA before configuration violates the USB 100 mA pre-config limit. Gating 165 mA of analog load plus the oscillator brings pre-enumeration draw to ≈65–80 mA |

## Next phase must

**Critical path — verify these four first; everything else is downstream of them:**

1. **AD9235BRUZ-20** (TSSOP-28, ×2). Highest sourcing risk in the design. Speed grades
   **−20 / −40 / −65 and AD9236BRUZ-80 share the same TSSOP-28 pinout and are drop-in.**
   Take a higher grade if −20 is short — **but if you take −65 for both channels, escalate:**
   2 × 300 mW ≈ 180 mA vs 80 mA breaks the power budget (R-09).
   Package is **fixed to TSSOP-28 (RU)** — the LFCSP (CP) variant is a different footprint.
2. **iCE40HX4K-TQ144.** Package **fixed by pin count** (86 I/O needed; TQFP-100 parts have
   79 and will not fit). Fallback iCE40HX1K-TQ144 has enough pins but only 1,280 LUT and
   **is not pin-compatible** — that is an escalation, not a substitution.
3. **IS61WV25616BLL-10TLI.** Substitute freely on: **≥256K × 16, ≤15 ns, 3.3 V,
   TSOP-II-44.** Vetted equivalents: CY7C1041GN30-10ZSXI, AS7C34098A-10TCN. **Speed is the
   binding spec, not capacity** — AS6C1616 has more capacity, a KiCad symbol, and 55 ns
   access that cannot complete a write inside the 50 ns budget. **IS61WV51216BLL-10TLI
   (1 MB) is a free upgrade** on the same outline and doubles burst depth to 262,144
   samples/ch — take it if it is better stocked.
4. **FT232HL** (LQFP-48). Do not "upgrade" to FT2232HL; see decision A3.

**Packages fixed by thermal or layout, not by preference — do not shrink these:**

- **U1 (3V3_D LDO): SOT-223 or better.** 0.37 W. A SOT-23-5 part would run 87 °C above
  ambient (R-11).
- **AFE attenuator top-leg resistors: 0805.** The package size is a working-voltage rating
  and a voltage-coefficient measure, not a footprint preference (R-12).
- **AD9235: TSSOP-28.** **iCE40HX4K: TQ144.**

**Freely substitutable, on stated criteria:**

- **A1/A2 dual op-amp:** any **dual, standard SOIC-8 pinout, ≥50 MHz GBW, FET/CMOS input
  (Ib ≤ 100 pA), ±5 V capable, ≤7 mA/amp.** Vetted drop-ins: OPA2810IDR (half the
  current), OPA1656IDR.
- **Jellybean passives:** cheapest JLCPCB Basic part meeting spec, 0402 preferred —
  **except** the attenuator resistors (0.1 %, 25 ppm, 0805) and every filter/attenuator
  capacitor, which must be **C0G/NP0**. X7R's voltage coefficient would distort the
  passband.
- **−5 V charge pump:** any inverting switched-cap converter ≥60 mA with **low output
  impedance**. TPS60403 works but its ~15 Ω Zout drops 0.45 V at 30 mA and eats op-amp
  headroom.
- SPI config flash: any ≥1 Mbit 3.3 V SPI NOR in SOIC-8.

**Specs that are binding and must appear in the sourced BOM row:**

- **X1: ≤5 ps RMS phase jitter (12 kHz–20 MHz), ±25 ppm.** An oscillator without a
  published jitter figure is not acceptable — this part sets ENOB (R-01).
- **U4 (3V3_A LDO): must have an enable pin**, and must be a low-noise type
  (≤20 µV RMS). Without the enable pin the board violates USB pre-enumeration current
  limits (R-10).
- **U_b (A3): must be a 3.3 V single-supply, rail-to-rail-output part.** This is ADC
  over-voltage protection, not a preference (A7).
- **R13: 12.0 kΩ ±1% on the FT232H REF pin.** Mandatory; omitting it means the board
  never enumerates.
- **C1: VBUS bulk ≤10 µF total** — USB inrush limit.
- **R1, R2: 5.1 kΩ ±1%** CC pull-downs — fixed by the USB-C sink specification.

**Second sources already vetted (no further analysis needed):** AD9235 speed grades ·
OPA2810IDR and OPA1656IDR for AD8066 · ADA4891-1ARJZ for OPA836 · CY7C1041GN30-10ZSXI and
AS7C34098A-10TCN for the SRAM · TPS60403DBVR and LT1054CS8 for the LM2776 (with the Zout
caveat) · TLV75533P and ADP151AUJZ-3.3 for the LP5907 · RT9080-33GJ5 and TLV75733PDRVR
for the AP7361C (SOT-223-equivalent thermal only).

**Mechanically critical:** the BNC jacks (J2, J3) and the USB-C receptacle (J1) sit on the
panel edge. Verify the KiCad footprint against the **exact** MPN, not a family footprint.

## Carried forward

**Requirement questions I had to resolve myself, and how:**

1. *Burst depth (requirements: "32,768 assumed baseline, SOFT").* Resolved to **131,072
   samples/channel** by adding external SRAM. The requirements' figure was not achievable
   in any small-FPGA BRAM and the one part that fit it exactly was pin-starved.
   `ic_selection.md` F1 has the full options table.
2. *Control protocol (requirements: "architect should define at least a minimal scheme").*
   Resolved to a 7-command in-band frame protocol on the sync FIFO, driven by the FTDI
   AN_130 constraint that channel B is unusable in sync-FIFO mode. `ic_selection.md` F2 is
   normative for the gateware and the host driver.
3. *AFE ratio and common mode (requirements: "provisional, recompute once the ADC is
   fixed").* Recomputed: **20:1 passive + ×2 = 10:1 net, CM 1.500 V, span 0.5–2.5 V**.
   `ic_selection.md` F3.
4. *Anti-alias filter order (not specified).* The [HARD] stopband forces **4th order**.
   Two 2nd-order sections plus a mandatory input buffer = three amps per channel.
5. *Dual-continuous rate.* Changed from the spec's fractional 8 MSPS/ch to **integer
   N ≥ 2 → 5 MSPS/ch**. Still satisfies the [HARD] bandwidth ceiling.
6. *Signal polarity.* The MFB output stage inverts. Corrected in the FPGA packer as
   `code_out = 4095 − code_raw`. **Do not "fix" this in hardware** — an extra inverting
   stage would cost an op-amp, bandwidth and noise for nothing.
7. *Grounding strategy (not specified).* Chose a single continuous ground net.
8. *Requirements D3 named "FT2232H (or FT232H)".* Chose FT232H, for the reason in A3.
9. *Requirements D5 said "two independent ADC ICs".* Honoured — two AD9235 packages on one
   clock. I evaluated a single dual-core ADC (LTC2290, which also satisfies the
   simultaneity intent) and rejected it on cost, not on D5.

**Risks from `design_risks.md` that constrain sourcing:**

- **R-01:** the 10 MHz XO's ≤5 ps RMS jitter spec is binding — it is the ENOB-limiting part.
- **R-09:** the power budget has 31% margin, not 50%. An AD9235**-65** substitution on both
  channels breaks it and requires escalation.
- **R-10:** the 3V3_A LDO must have an enable pin, or the board fails USB pre-enumeration
  current limits.
- **R-11:** the 3V3_D LDO package is a thermal requirement (SOT-223 or better).
- **R-12:** the attenuator top-leg resistors must stay 0805; the optional BNC TVS must be
  **<2 pF and ≥45 V standoff** or it must stay DNP.
- **R-14:** four parts need `kipart`-generated symbols — budget that work in the datasheet
  and coding phases.
- **R-15:** **no live JLCPCB stock, tier or price was verifiable during architecture** (the
  `pcbparts` MCP was not connected). Every tier expectation in `skeleton_bom.md` is an
  estimate. This is precisely the sourcer's job.

**Deferred to the sourcer's judgement:**

- JLCPCB tier optimisation across all ~150 passives (Basic wherever it meets spec).
- Exact BNC and USB-C MPNs, subject to the panel-edge mechanical constraint.
- Whether to take the IS61WV51216 (1 MB) upgrade — purely a stock/price call, and the
  architecture supports either.
- Exact filter R/C values: 4th-order Butterworth at fc = 5.0 MHz, sections
  Q = 0.5412 and Q = 1.3065, A3 carrying gain −2. Synthesis belongs to the coder; the
  sourcer only needs the **C0G/NP0, 0402, ±2%** constraint.

**Still open, owned by later phases:** AD9235 `SENSE`/`REFT`/`REFB` strapping topology
(datasheet phase) · 60 MHz sync-FIFO timing closure (gateware, R-08) · attenuator
compensation trim procedure (bring-up, R-05) · bench ENOB verification and the
differential-driver escape hatch (R-07) · FT232H EEPROM image with ACBUS9 = PWREN#
(bring-up, R-10).

## Do not redo

These are settled. Reopening any of them invalidates work downstream.

- **Topology, all of it:** external-SRAM capture buffer (not BRAM, not SDRAM); one ADC per
  channel on a shared XO clock; three-amp-per-channel AFE; LDO-only regulation;
  single-ended ADC drive; in-band control protocol; single ground net.
- **131,072 samples/channel** and the 13.1072 ms record length — these are now the
  design's published numbers, not the requirements' 32,768.
- **20:1 attenuator / ×2 gain / CM 1.500 V / span 0.5–2.5 V.** The ratio is derived from
  the selected ADC; changing the ADC changes it, which is an escalation, not an edit.
- **4th-order AAF at 5.0 MHz.** Do not reduce the stage count "to save an op-amp".
- **A3 on +3V3_A single supply.** This is protection, not a preference.
- **Dedicated XO for the ADC clock.** Never generate it in FPGA fabric.
- **FT232H over FT2232H**, and the FPGA/USB-bridge two-chip split from requirements D3.
- **PWREN#-gated analog rails.** Removing the gate breaks USB compliance.
- **Polarity inversion corrected digitally**, not with another op-amp.
- Everything in the requirements' own "Do not redo": BNC inputs, ±10 V / 10 MSPS / 12 bit,
  USB-C USB2-only, on-board charge-pump negative rail, 4-layer PCB.

## Escalation

none
