# Net plan — dual_adc_usb

The coders' contract. Net names here are used **verbatim** in the block function signatures in
`handoffs/02_architecture.md § Block manifest`. Refs are assigned per block and are unique
board-wide.

**One `GND` net.** Analog/digital ground separation is a *layout* instruction (see
`design_risks.md` R-3), not a netlist split — do not create AGND/DGND nets or a net-tie part.

## Power nets

| Net | Type | Nominal | Connected refs |
|---|---|---|---|
| `VBUS` | POWER | 4.75–5.25 V, always on | J4 (VBUS pins), U8 (USBLC6 VBUS), U6 (FT232HL VREGIN), U9 (TPS22918 VIN), C83 (≤10 µF total, USB inrush limit) |
| `VBUS_SW` | POWER | 5 V, gated by U9 | U9 (VOUT), U10 (VIN), U11 (VIN), U12 (VIN), FB1 (1), C81 |
<!-- revised: rev.3 — VCORE/VCCA are 1.8 V LDO OUTPUTS of U6, never loads on FT_3V3; RESET# tie added; source named. -->
| `FT_3V3` | POWER | 3.3 V, **driven by U6 pin 39 (VCCD)** — no other block may source it | U6 (39 VCCD out; VCCIO 13/24/33, VPHY 16, VPLL 20, **RESET# 34 — direct tie, no resistor**), U7 (EEPROM VCC), **R71** (load-switch EN pull-up), **R65** (PWREN# pull-up), **R66** (EEPROM `EE_DO` pull-up), **R67** (FIFO_SIWU_N tie-off), C603–C607, C610–C612 |
| `FT_VCCA_1V8`, `FT_VCORE_1V8` | POWER, **block-internal to `usb_bridge`** | 1.8 V | U6 pin 37 (VCCA) and pin 38 (VCORE) are **outputs of the FT232H's own internal LDO**. Each takes one 100 nF to GND (C606, C608) and **nothing else**. They must NOT be tied to `FT_3V3` (back-drives the LDO) and must NOT feed `P1V8` or any FPGA rail |
<!-- revised: rev.2 — U5 power tree split; the 1.8 V PSRAM bank is VCCIO3 (pin 12), NOT VCCX/VCCIO0. -->
| `P3V3D` | POWER | 3.287 V (buck) | U10 (FB node via R72/R73), L71 (2), C73, **U5 VCCX/VCCIO0 (pins 64, 67, 78) + VCCIO1 (58) + VCCIO2 (23, 44)**, U4 (VDRV), X1 (VDD), R51/R52 (LEDs), U14 (VIN + EN), C84, C501–C510 |
| `P1V8` | POWER | 1.800 V LDO from `P3V3D` | U14 (VOUT), C85, C86, **U5 VCCIO3 — pin 12 ONLY**, R53 (RECONFIG_N pull-up), C511–C513 |
| `P1V2` | POWER | 1.200 V (buck) | U11 (FB via R74/R75), L72 (2), C75, U5 (VCC core) |
| `P3V3A` | POWER | 3.3 V LDO, low noise | U12 (VOUT), C76, C77, U4 (AVDD), U2 (VS+), U3 (VS+), C117/C118, C217/C218 |
<!-- revised: rev.3 — the ±50 V clamp must reach BOTH rails (SPEC I3); rev.2 listed only the negative side. -->
| `VA_POS` | POWER | +5 V, ferrite-filtered | FB1 (2), C81, C11, C12, **C15**, U1 (V+), U13 (TPS60403 IN), **D101/D201 upper diode cathode — clamps CH*_ATT to +5 V** |
| `VA_NEG_RAW` | POWER | ≈−4.80 V | U13 (OUT), C79, R76 (1) |
| `VA_NEG` | POWER | ≈−4.74 V, RC-filtered | R76 (2), C80, C13, C14, **C16**, U1 (V−), **D101/D201 lower diode anode — clamps CH*_ATT to −5 V** |

| `GND` | GND | 0 V | all blocks |

**Clamp topology (both channels):** D101/D201 are BAV199-class **series pairs in SOT-23** (symbol `Diode:BAV99`). Upper diode: anode → `CH*_ATT`, cathode → `VA_POS`. Lower diode: anode → `VA_NEG`, cathode → `CH*_ATT`. Both diodes reverse-biased over the ±0.909 V signal range; on a ±50 V fault the 910 kΩ top resistor limits clamp current to (50 − 5.7)/910 k = **48.7 µA**, far under BAV199's 250 mA rating — SPEC I3 met. A cathode-to-`VA_NEG` orientation (rev.2's wording) would be permanently forward-biased.

### Why the 1.8 V rail lands on pin 12 and **not** on pins 64/67/78

`GW1NR-LV9QN88PC6-I5.pdf` p.10 requires the I/O bank that hosts the embedded PSRAM to run at
1.8 V. Phase 4 inferred that bank was BANK0 → VCCX/VCCIO0 (64, 67, 78). **That inference is
wrong and would brick the board:**

- DS117 Table 3-2 (Recommended Operating Conditions): VCCX for **GW1NR-4/9 = 2.375 V min**,
  3.6 V max. Its own note: *"For some packages, VCCIO and VCCX may share the same pin. In this
  case, VCCX requirements must be met first."* QN88P is exactly that case (UG119E Table 2-6
  footnote [3], pin multiplexing) — so 64/67/78 may not go below 2.375 V.
- DS117 Table 3-5 (POR): the VCCX power-on-reset trip point is 1.8–2.0 V. A 1.8 V VCCX sits on
  the trip point; the device may never release reset.
- Sipeed Tang Nano 9K reference schematic, **same device, same QN88P package**: pins 64/67/78
  (`VCCX/VCCO0`), 58 (`VCCO1`) and 23 (`VCCO2`) all tie to net `VCCO0_1_2_3V3` = 3.3 V, while
  **pin 12 (`VCCO3`) ties to `VCCO3_1V8` = 1.8 V**, and every BANK3 user-I/O net on that board
  is named `..._1V8`. One bank at 1.8 V, and it is BANK3.
- Corroboration inside UG119E Table 2-6: QN88 (SDRAM) vs QN88P (PSRAM) differ **only in BANK3's
  differential/LVDS counts** (8/4 → 6/3). BANK0 is 0/0/0 in both. The memory die is on BANK3.

**Consequence the coder must honour: BANK3's 23 user I/O are 1.8 V-only.** 3.3 V-capable user
I/O = BANK1 (25) + BANK2 (23) = **48**, not 71. See `design_risks.md` R-12.

### Pin budget, rev.3 — final <!-- revised: rev.3 -->

| Signal group | Pins |
|---|---|
| `ADC_DA[0..11]` + `ADC_DB[0..11]` | 24 |
| `ADC_DVA` | 1 |
| `ADC_SEN`, `ADC_SCLK`, `ADC_SDATA`, **`ADC_SEL`** | 4 |
| `CLK10_FPGA` | 1 |
| `FIFO_D[0..7]` | 8 |
| `FIFO_RXF_N`, `FIFO_TXE_N`, `FIFO_RD_N`, `FIFO_WR_N`, `FIFO_OE_N` | 5 |
| `FIFO_CLK60` | 1 |
| `LED0`, `LED1` | 2 |
| **Demand** | **46** |
| **Available (BANK1 25 + BANK2 23)** | **48** |
| **Margin** | **+2** |

Arithmetic: baseline 49 (24+1+4+1+8+6+1+2+2 with OVRA/OVRB and SIWU_N) − 2 (OVRA/OVRB retired)
− 1 (SIWU_N strapped to R67) = **46**; 48 − 46 = **2 spare pins**. Not zero, but there is no
third pin to find: every other signal on this board is 3.3 V and BANK3 cannot carry it.

**Not charged to this budget** (dedicated configuration pins or BANK3): `JTAG_TCK/TMS/TDI/TDO`,
`MODE0` (88), `MODE1` (87), and `RECONFIG_N` — UG803's per-pin table names it `IOL13B/RECONFIG_N`,
an **IOL\*** i.e. BANK3 pin, which is why R53 pulls it to `P1V8` and not `P3V3D`.

Switch-node / flying-cap nets, local to `power_tree`: `SW_3V3` (U10–L71), `SW_1V2` (U11–L72),
`CP_CAP_P`/`CP_CAP_N` (U13 flying cap C78), `FB_3V3` (R72/R73/U10.FB), `FB_1V2` (R74/R75/U11.FB),
`LS_CT` (U9.CT–C71).

## Analog signal nets — channel A (`afe_input` tag A, `afe_buffer`, `afe_driver` tag A)

| Net | Type | Connected refs | Note |
|---|---|---|---|
| `CHA_IN` | ANALOG HV | J1 (centre), R101 (1), C101 (1) | ±10 V signal, ±55 V survivable. Keep short; this node sets input capacitance |
| `CHA_ATT` | ANALOG hi-Z | R101 (2), R102 (1), C101 (2), C102 (1), C103 (1), D101 (both anodes/cathodes), U1 (+IN A) | 82.6 kΩ source. **Guard this node**; stray C here is budgeted at 5 pF |
| `CHA_BUF` | ANALOG | U1 (OUT A), U1 (−IN A), R111 (1) | Unity-gain feedback is a direct short — no resistor |
| `CHA_FDAP` | ANALOG | U2 (OUT+), R112 (2), C111 (2), R115 (1) | |
| `CHA_FDAN` | ANALOG | U2 (OUT−), R114 (2), C112 (2), R116 (1) | |
| `CHA_FDA_INN` | ANALOG | R111 (2), R112 (1), C111 (1), U2 (IN−) | Driven leg |
| `CHA_FDA_INP` | ANALOG | R113 (2), R114 (1), C112 (1), U2 (IN+) | R113 (1) → `GND` — reference leg |
| `CHA_F1P` / `CHA_F1N` | ANALOG | R115 (2)/L111 (1) · R116 (2)/L113 (1) | |
| `CHA_F2P` / `CHA_F2N` | ANALOG | L111 (2), C113, L112 (1) · L113 (2), C115, L114 (1) | Filter node 1 per leg |
| `CHA_F3P` / `CHA_F3N` | ANALOG | L112 (2), C114, R117 (1), D111 · L114 (2), C116, R118 (1), D112 | Filter node 2 per leg |
| `ADC_INAP` | ANALOG | R118 (2), U4 (IN_A+) | **Fed from the FDA OUT− leg — see polarity note** |
| `ADC_INAN` | ANALOG | R117 (2), U4 (IN_A−) | **Fed from the FDA OUT+ leg** |

**Polarity (do not "fix" this):** the single-ended→differential stage inverts. The inversion is
undone by crossing the pair at the ADC: `CHA_FDAP`-leg → `ADC_INAN`, `CHA_FDAN`-leg →
`ADC_INAP`. Same for channel B. Overall BNC→code transfer is then non-inverting.

Channel B is identical with refs J2, R201/R202, C201–C203, D201, U3, R211–R218, L211–L214,
C211–C219, D211/D212, and nets `CHB_*`, `ADC_INBP`, `ADC_INBN`.

| Net | Type | Connected refs |
|---|---|---|
| `ADC_CM` | ANALOG ref | U4 (CM), U2 (VOCM), U3 (VOCM), C119, C219 — **load ≤ ±2 mA; no resistive load permitted** |
| `ADC_REFT` / `ADC_REFB` | ANALOG ref | U4, 0.1 µF each to GND (C407/C408), 0603 or smaller, at the pins |
| `ADC_ISET` | ANALOG ref | U4 (ISET), R401 = 56.2 kΩ 1 % to GND |

## Clock nets

| Net | Type | Connected refs |
|---|---|---|
| `CLK10_OSC` | CLOCK | X1 (OUT), R31 (1), R32 (1) |
| `CLK10_ADC` | CLOCK | R31 (2), U4 (CLK) — 33 Ω series at the source |
| `CLK10_FPGA` | CLOCK | R32 (2), U5 (dedicated clock-capable input) |

## ADC ↔ FPGA

| Net | Type | Connected refs |
|---|---|---|
| `ADC_DA[0..11]` | DIGITAL 3.3 V | U4 (D0A…D11A) → U5 (bank pins). 12 nets |
| `ADC_DB[0..11]` | DIGITAL 3.3 V | U4 (D0B…D11B) → U5. 12 nets |
| `ADC_DVA` | DIGITAL | U4 (DVA) → U5. DVB is left unconnected (mark NC in SKiDL) |
| ~~`ADC_OVRA`, `ADC_OVRB`~~ | **RETIRED rev.3** | U4 OVRA/OVRB → **NC**. Overrange appears nowhere in SPEC; retiring them buys the 2 pins the budget needs. Clipping is still detectable in firmware (code = 0x000/0xFFF) |
<!-- revised: rev.3 — SEL is dynamic again (TI SBAS295A p.19 requires a low-going reset pulse); OVRA/OVRB retired; pin numbers pinned. -->
| `ADC_SEN`, `ADC_SCLK`, `ADC_SDATA` | DIGITAL | U5 → U4 pins **41 (SEN), 42 (SCLK), 45 (SDATA)**. **Mandatory:** disables the ADC's internal PLL so it can run at 10 MSPS (SPEC F3) |
| `ADC_SEL` | DIGITAL | **U5 → U4 pin 1 (SEL) — FPGA-driven, NOT a strap.** TI SBAS295A p.19: the serial registers need a **low-going pulse on SEL** to reset, "without a reset… registers may be in their non-default state on power-up. This condition may cause the device to malfunction." The PLL's power-up default is **enabled**, and a PLL-enabled ADS5231 cannot run at 10 MSPS. A static strap cannot deliver that pulse, so **R402 stays deleted** and SEL costs one 3.3 V pin |
| tied static in `adc_dual` | — | **`OEB#` (pin 6) → `GND` only.** Pins 41/42 are SEN/SCLK when SEL=1 and must NOT be grounded — the rev.1/rev.2 `OEA`/`MSBI` GND ties are **gone for good**. `INT/EXT#` (56) → `P3V3A` (internal reference) |

## FPGA ↔ FT232HL (245 synchronous FIFO; the FT232HL is clock master)

| Net | Type | Connected refs |
|---|---|---|
| `FIFO_D[0..7]` | DIGITAL bidir | U6 (ADBUS0-7) ↔ U5. 8 nets |
| `FIFO_RXF_N` | DIGITAL | U6 (ACBUS0) → U5 |
| `FIFO_TXE_N` | DIGITAL | U6 (ACBUS1) → U5 |
| `FIFO_RD_N` | DIGITAL | U5 → U6 (ACBUS2) |
| `FIFO_WR_N` | DIGITAL | U5 → U6 (ACBUS3) |
| `FIFO_SIWU_N` | STATIC | **U6 (ACBUS4) → R67 = 10 kΩ → `FT_3V3`.** <!-- revised: rev.3 — refdes R66→R67; R66 belongs to the EEPROM `EE_DO` pull-up. --> Send-immediate/wake-up is unused in a bulk burst read-out. Drive check: SIWU# is active-**low** and held **high** = inactive; 3.3 V through 10 kΩ against ±1 µA input leakage drops 10 mV ⇒ **3.29 V vs VIH 2.0 V** ✓. Never driven low, so no off-state to check |
| `FIFO_CLK60` | CLOCK 60 MHz | U6 (ACBUS5) → U5 clock-capable input |
| `FIFO_OE_N` | DIGITAL | U5 → U6 (ACBUS6) |
| `PWREN_N` | DIGITAL | U6 (ACBUS9, EEPROM-configured PWREN#) → Q1 (gate) |
| tied static | — | U6 ACBUS7 (PWRSAV#) → `FT_3V3` |

## USB and power control

| Net | Type | Connected refs |
|---|---|---|
| `USB_DP`, `USB_DM` | DIFF PAIR 90 Ω | J4 (A6/B6, A7/B7 — both sides strapped), U8 (USBLC6 I/O), U6 (DP/DM) |
| `CC1`, `CC2` | ANALOG static | J4 (A5, B5), R61/R62 = 5.1 kΩ 1 % to `GND` each. **No PD controller** |
| `LS_EN` | DIGITAL | Q1 (drain), R71 (2) → `FT_3V3`, U9 (EN) |
| `FT_REF` | ANALOG | U6 (REF) → R63 = 12 kΩ 1 % → `GND` (FTDI-mandated) |
| `EE_CS`, `EE_SK`, `EE_DI`, `EE_DO` | DIGITAL | U6 ↔ U7 (93LC56). **R64 = 2.2 kΩ in series** on `EE_DO` **and R66 = 10 kΩ pull-up to `FT_3V3`** — FTDI Table 3.3 mandates both; rev.2 named only R64 |
| `XI`, `XO` | CLOCK 12 MHz | U6 ↔ Y1, load caps C601/C602 |

## FPGA support

| Net | Type | Connected refs |
|---|---|---|
<!-- revised: rev.2 — RECONFIG_N rail corrected, MODE straps added -->
| `JTAG_TCK`, `JTAG_TMS`, `JTAG_TDI`, `JTAG_TDO` | DIGITAL 3.3 V | U5 (dedicated JTAG pins) ↔ J3 (1×6 header, plus `P3V3D` and `GND`). Dedicated config I/O are referenced to **VCCX = 3.3 V**, so a 3.3 V pod is correct — see R-13 |
| `LED0`, `LED1` | DIGITAL 3.3 V | U5 (BANK1/BANK2 pin) → R51/R52 → D51/D52 → `GND`. **Must stay on a 3.3 V bank:** a green LED's V_f ≈ 2.0 V exceeds the whole 1.8 V rail, so a BANK3 pin cannot light it |
| `RECONFIG_N` | DIGITAL 1.8 V | U5 → **R53 = 10 kΩ pull-up to `P1V8`** (was `P3V3D`). RECONFIG_N is a BANK3 pin; 3.3 V on it exceeds VCCIO3 + 0.3 V = 2.1 V abs max. Pull-up current 1.8 V / 10 kΩ = 180 µA |
| `MODE0`, `MODE1` | STATIC | U5 pin 88 → R54 = 4.7 kΩ → `GND`; U5 pin 87 → R55 = 4.7 kΩ → `GND`. **MODE[1:0] = 00**, MODE2 is not bonded on QN88P (UG119E Table 2-6). Pull-**downs**, not pull-ups: MODE0/MODE1 are BANK3 pins sampled at power-up and `P1V8` is the last rail to come up, so a strap to GND is valid before VCCIO3 is |

## Decoupling policy (applies to every block; the coder does not need to ask)

- Every IC supply pin: 100 nF 0402 X7R at the pin.
<!-- revised: rev.3 — U1 had no 100 nF anywhere; three U6/U7 supply pins had none. -->
- **U1 (AD8066): C15 = 100 nF on `VA_POS`, C16 = 100 nF on `VA_NEG`, at the pins**, in addition to the C11–C14 bulk. Rev.2 assigned U1 no HF decoupling at all — a defect on a 10 MSPS front end, not a formality.
- **U6/U7: C610 (VPHY 16), C611 (VPLL 20), C612 (U7 VCC)** — 100 nF each; rev.2 left 3 of 10 supply pins bare. C606/C608 stay on `FT_VCCA_1V8`/`FT_VCORE_1V8` (LDO outputs, not rails).
- Per rail per IC: one 1 µF + one 10 µF (X5R/X7R, 10 V or better; 25 V on VBUS).
- ADS5231: 100 nF per AVDD pin **plus** 100 nF on REFT, REFB, CM, and one 10 µF bulk on AVDD.
- GW1NR-9: 100 nF at **every** VCCIO/VCCX pin — 6 on `P3V3D` (23, 44, 58, 64, 67, 78) and
  **1 on `P1V8` (pin 12)** — plus 100 nF × 4 on VCC core (1, 22, 45, 66) and one bulk cap per
  rail. `P1V8` bulk sizing: a 128-byte PSRAM burst at x16 DDR 100 MHz lasts
  128 / (2 B × 2 × 100 MHz) = 320 ns; droop into 22 µF is 0.060 A × 320 ns / 22 µF = **0.87 mV**,
  against the 5 % (90 mV) VCCIO ripple allowance of DS117 Table 3-2 ✓.
- Buck outputs: 22 µF; buck inputs: 10 µF; charge pump: 1 µF flying, 10 µF out.
