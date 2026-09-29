# Net plan — dual_adc_usb

**This file is the coders' contract.** Net names here are exact and case-sensitive. Block
function signatures in `handoffs/02_architecture.md` § Block manifest use these names.

## Ground policy — read this first

There is **one** ground net: `GND`. Do **not** create `AGND`, `DGND`, or a 0 Ω stitch
between them. The analog/digital partition is a *layout* instruction (see
`design_risks.md` R-7), not a schematic one — a split net would only produce ERC noise and
a netlist that lies about the copper.

## Power nets

| Net | Type | Nominal | Connected refs |
|---|---|---|---|
| `VBUS_RAW` | power | 5.0 V, USB | J1.VBUS(A4,B4,A9,B9), D2(TVS), FB1.1 |
| `+5V_IN` | power | 5.0 V filtered | FB1.2, C1(4.7 µF), C2(4.7 µF), U9.IN (pin 5), U7.VREGIN |
| `+5V_SW` | power | 5.0 V, gated | U9.OUT (pin 1), C3, U1.IN, U1.EN, FB3.1 |
| `+3V3_D` | power | 3.30 V, buck | L1.2, C4, U1.FB divider, U2.IN, FB2.1, U6.VCCX/VCCIO, D4+R7 (power LED), U6 I/O supply |
| `+3V3_ADCD` | power | 3.30 V, ferrite-isolated | FB2.2, C7, U5.DRVDD |
| `+3V3_A` | power | 3.30 V, LDO | U3.OUT, C9..C11, U4.V+, U5.AVDD, X1.VCC (via FB4), U_buf1/2.V+, U_fda1/2.VS+, R8 |
| `+1V2_D` | power | 1.20 V, LDO | U2.OUT, C6, U6.VCC (core) |
| `GND` | ground | 0 V | all |

<!-- revised: rev2 — Q1 (bare P-FET) replaced by U9 = AP2161WG-7 active-low-EN current-limited
load switch; R3 (gate pull-up) deleted; C1/C2 dropped to 4.7 µF each so VBUS bulk = 9.4 µF
(SPEC P4 ≤ 10 µF). See handoffs/02_architecture.md rev 2 decisions 13-14. -->

## Analog reference nets

| Net | Type | Nominal | Connected refs | Note |
|---|---|---|---|---|
| `VBIAS` | analog ref | **1.100 V** | R22.2, R19.1, ch1 R_bot.2, ch2 R_bot.2 | divider return; low-Z AC ground. U4A drives it **through R22 = 10 Ω** — see note below. **rev 3: 1.200 V → 1.100 V** (R8 = 22.0 k, R9 = 11.0 k) to buy OPA355 common-mode headroom — see the headroom note below |
| `VREF_FE` | analog ref | **1.0453 V** | U4B.OUT, ch1 R_g2.1, ch2 R_g2.1 | = 0.95025·`VBIAS`, derived from it so the two track and their noise cancels. Divider ordering below; **R19/R11 values unchanged** — only `VBIAS` moved |
| `VOCM` | analog ref | ≈1.65 V | U5.CM, C_vocm, U_fda1.VOCM, U_fda2.VOCM | taken from the ADC's own CM output — do **not** generate it separately |

<!-- revised: rev2 — R11/R19 end assignment corrected (was arithmetically wrong), R22 added. -->
<!-- revised: rev3 — VBIAS 1.200 V -> 1.100 V (ERC M-1), VREF_FE follows to 1.0453 V. -->

**`VREF_FE` divider ordering — R19 is the TOP resistor.** The chain is
`VBIAS` → **R19 (1.00 kΩ)** → tap → **R11 (19.1 kΩ)** → `GND`, and the tap drives U4B(+).
That gives 19.1/(19.1 + 1.00) = **0.95025 → 1.1403 V**. Revision 1 of this file listed the
ends the other way round (`R11.1` on `VBIAS`, `R19.2` on `VREF_FE`), which with the sourced
values yields 0.0498·`VBIAS` = 59.7 mV — not the 0.95 the same row demands. **Values are
unchanged**; only the ends swap. `analog_power_ref.py` already builds it this way, so nothing
downstream of this correction changes.

**`VBIAS` isolation resistor R22 = 10 Ω 0603.** U4A (TLV9062, 10 MHz GBW) drives 200–250 pF
on `VBIAS` — two 82 pF `C_bot` legs plus AFE routing stray — which is enough capacitive load
to cost phase margin and ring on the node the whole front end uses as its AC ground. U4A's
output therefore goes to a local net **`VBIAS_DRV`**, and `R22` sits between `VBIAS_DRV` and
`VBIAS`. U4A's feedback is taken at `VBIAS_DRV` (inside R22), so this is an isolation
resistor, not a 10 Ω error: the isolation zero lands at ≈64 MHz, four decades above the
crossover; 10 Ω is four decades below the 50 kΩ `R_bot` it must look like a short to; and the
DC drop at the ~2.4 µA of divider-return current is 24 nV. `VBIAS_DRV` is **local to
`analog_power_ref`** — it is not an inter-block net.

<!-- revised: rev3 — new section, ERC finding M-1. -->
**`VBIAS` = 1.100 V, not 1.200 V — OPA355 input common-mode headroom (ERC M-1).** The buffer's
VCM ceiling is **(V+) − 1.5 V**, i.e. 1.800 V nominal and **1.734 V** with `+3V3_A` 2 % low.
The buffer input sits at `0.950095·VBIAS + 0.049905·AIN`, so at `AIN` = +10 V it reached
**1.639 V** with `VBIAS` = 1.200 V — only **85 mV** of worst-case margin, and spent exactly
where SPEC F11's full-scale ENOB is measured. `VBIAS` = 1.100 V moves that to **1.544 V**,
**≈180 mV** of worst-case margin (2.1×), while the negative overrange stays inside the
OPA355's abs-max input: at `AIN` = −30 V (SPEC I5) the buffer input reaches **−0.452 V**
against an abs max of (V−) − 0.5 V, so the BAV99 still does not have to conduct.

**Nothing else in the front end moves**, because gain and the zero-input match depend only on
*ratios*: gain = 0.049905 × (1.00 k/499) = 1/10.02 (±10 V → 2.0 V p-p differential), and at
`AIN` = 0 the tap sits at 0.950095·`VBIAS` against `VREF_FE` = 0.95025·`VBIAS` — a residual
0.155 mV·(VBIAS/1 V) → **0.34 mV** differential offset (≈0.7 LSB at 12 bit, covered by F12's
host-side offset correction, and 10 % smaller than at 1.200 V). The FDA summing node moves
from 1.093–1.426 V to **1.030–1.363 V** over the full ±10 V sweep. *(The ERC reviewer's
proposed R8 = 23.0 kΩ would have given 1.000 V and 285 mV of margin, but **23.0 kΩ is not an
E96/E24/E192 value**, and 1.000 V pushes the −30 V case to −0.547 V — past the OPA355's
abs-max input, relying on the clamp — and drops the FDA summing node to 0.967 V, toward a
THS4551 input-CM floor this project has never had a datasheet for. 1.100 V takes most of the
margin for none of that risk, on two E24 jellybeans.)*

## Analog signal nets

| Net | Type | Connected refs |
|---|---|---|
| `AIN1` | analog in, ±10 V | J2.center, ch1 R_top_a.1, ch1 C_top(trimmer).1 |
| `AIN2` | analog in, ±10 V | J3.center, ch2 R_top_a.1, ch2 C_top(trimmer).1 |
| `CH1_P` / `CH1_N` | analog diff, 2 V p-p | U_fda1.OUT+/OUT− → R_o/C_o network → U5.INP_A / U5.INM_A |
| `CH2_P` / `CH2_N` | analog diff, 2 V p-p | U_fda2.OUT+/OUT− → R_o/C_o network → U5.INP_B / U5.INM_B |

Per-channel internal nets (`<ch>` = `CH1` or `CH2`; local to `afe_channel`, listed so the
block coder names them consistently): `<ch>_DIVNODE` (divider tap, 47.5 kΩ source),
`<ch>_BUFOUT` (buffer output), `<ch>_FBP` / `<ch>_FBN` (FDA feedback nodes, **now carrying
only `C_f` and the FB pin — `R_f` no longer lands here**), and **new in rev 3**
`<ch>_MFBP` / `<ch>_MFBN` (the MFB filter nodes: the `R_g`/`R_f`/`R_mfb`
junction on each leg, with the differential capacitor `C_mfb` bridging them).

<!-- revised: rev3 — MFB nodes added; see the anti-alias filter plan below. -->

## Anti-alias filter — the pole plan `afe_channel` must build (rev 3, ERC H-1)

The as-built network was **2nd-order, not 3rd**: `C_cm` and `C_diff` hang off the same node
behind the same `R_o`, so differentially they merge into one pole. Measured from netlist
values: −3 dB at 3.1 MHz, **−4.55 dB at 4.0 MHz**, −9.8 dB at 7 MHz. The inline comments in
`afe_channel.py` (5.1 MHz output pole, 24 dB at 15 MHz) are **wrong — do not trust them**.

**Adding more RC sections cannot fix it.** A cascade of *real* poles obeys a hard bound: with
a droop budget D dB at 4 MHz, the attenuation at 16 MHz can never exceed (16/4)² · D = 16·D,
so 0.5 dB of passband droop buys at most **8 dB** at 16 MHz at *any* order. Complex poles are
mandatory, which means the filter has to run through the FDA's feedback, not just after it.

**The plan: 2nd-order MFB around U_fda (complex pair) + one output RC = 3rd-order
Butterworth, f₋₃dB ≈ 6.1 MHz.** Per leg the gain/feedback network becomes
`bufout → R_g (499) → the MFB node → R_f (1.00 k) → the opposite OUT`, and
`MFB node → R_mfb (499) → the IN pin`, `C_f (10 pF) from the FB pin to that same OUT`, plus **one** differential
`C_mfb (68 pF)` between `CH<n>_MFBP` and `CH<n>_MFBN`. Then the existing output RC:
`R_o 33 Ω` per leg into `C_diff 330 pF` differential + `C_cm 100 pF` per leg to GND.

Realized poles: MFB section f₀ = 5.93 MHz, Q = 1.012; output RC f₁ = 6.35 MHz differential
(CM pole 48 MHz). Response, nominal:

| f | 4.0 MHz | 5.0 MHz | −3 dB | 7 MHz | 10 MHz | 16 MHz | 20 MHz |
|---|---|---|---|---|---|---|---|
| as-built | −4.55 | −6.6 | 3.1 MHz | −9.8 | −15.3 | −21.4 | −25.5 |
| **rev 3** | **−0.15** | −1.01 | **6.1 MHz** | −5.25 | −13.3 | **−25.3** | −31.1 |

Worst case over ±5 % C0G and ±1 % R: droop at 4.0 MHz ≤ 0.40 dB, attenuation at 16 MHz
≥ 22.7 dB. **DC is untouched**: no DC current flows in `R_mfb`, so the MFB node sits at the
summing node's potential and the DC gain is still `R_f/R_g` = 2.004 — every DC number the ERC review
verified carries over unchanged.

## Clock nets

| Net | Type | Freq | Connected refs | Note |
|---|---|---|---|---|
| `ADC_CLK` | clock | 20.000 MHz | X1.OUT → R_s1(33 Ω) → U5.CLK | **direct from the XO** — never from an FPGA output (F14) |
| `FPGA_CLK` | clock | 20.000 MHz | X1.OUT → R_s2(33 Ω) → U6 clock-capable pin | second load on the same XO output; keep both stubs < 15 mm |
| `FIFO_CLK` | clock | 60.000 MHz | U7.ACBUS5 → U6 clock-capable pin | FT232H CLKOUT, asynchronous to the sample domain |
| `FT_XI` / `FT_XO` | clock, xtal | 12.000 MHz | X2, C13, C14, U7.OSCI/OSCO | keep the loop tight, guard with GND |

## ADC ↔ FPGA bus

| Net | Type | Connected refs |
|---|---|---|
| `ADC_D1[11:0]` | digital bus, out of U5 | U5.D1_0..D1_11 → RA1,RA2,RA3 (33 Ω arrays) → U6 |
| `ADC_D2[11:0]` | digital bus, out of U5 | U5.D2_0..D2_11 → RA4,RA5,RA6 (33 Ω arrays) → U6 |
| `ADC_OE_N` | control, U6 → U5 | U6, U5.OE# |
| `ADC_PDWN` | control, U6 → U5 | U6, U5.PDWN |

Every ADC data line carries a **33 Ω series damping resistor** placed at the ADC end
(4-element 0402 arrays, 6 of them). This is the single most effective measure against the
ADC's own output switching coupling back into its analog inputs.

## FPGA ↔ FT232H synchronous FIFO (245 sync mode)

| Net | Dir | FT232H pin | Note |
|---|---|---|---|
| `FIFO_D[7:0]` | bidir | ADBUS0..7 | data bus |
| `FIFO_RXF_N` | U7 → U6 | ACBUS0 | RXF# — host data available |
| `FIFO_TXE_N` | U7 → U6 | ACBUS1 | TXE# — room to write |
| `FIFO_RD_N` | U6 → U7 | ACBUS2 | RD# |
| `FIFO_WR_N` | U6 → U7 | ACBUS3 | WR# |
| `FIFO_SIWU` | U6 → U7 | ACBUS4 | send-immediate / wake-up, tie high if unused |
| `FIFO_OE_N` | U6 → U7 | ACBUS6 | OE# |
| `PWREN_N` | U7 → U9.EN# (pin 4) | **ACBUS8 (U7 pin 32)**, *not* ACBUS7 | low after USB configuration → enables U9. **U9's EN is active-low and GND-referenced**: 3.3 V = off (VIH 2.0 V min), 0 V = on (VIL 0.8 V max) — no level shift, no inverter. `usb_bridge`'s 10 kΩ pull-up to 3V3 (R_pwren) is what holds the rail tree OFF at plug-in and through FT232H reset; R6 (DNP 0 Ω to `GND`) forces it ON for bring-up. **rev 2 pin correction:** in 245 sync FIFO mode ACBUS7 is PWRSAV# only and FTDI Table 3.5 offers PWREN# on ACBUS0–6/8/9; ACBUS0–6 are all consumed by the FIFO, so PWREN# must be on **ACBUS8**. `usb_bridge.py` already wires it there and leaves ACBUS7 (pin 31) NC |

## Control, config, debug

| Net | Type | Connected refs |
|---|---|---|
| `USB_DP` / `USB_DM` | USB 2.0 HS diff pair, 90 Ω | J1.A6+B6 / J1.A7+B7, D1(USBLC6), U7.DP/DM |
| `CC1` / `CC2` | USB-C config | J1.A5 / J1.B5, R1 / R2 (5.1 kΩ to `GND`) |
| `SHIELD` | chassis | J1 shell, C15(1 nF) ‖ R12(1 MΩ) to `GND` |
| `EECS` / `EECLK` / `EEDATA` | EEPROM (Microwire) | U7 ↔ U8, R13(2.2 kΩ) pull-up on `EEDATA` |
| `FT_RESET_N` | reset | U7.RESET#, R14 pull-up, C16 |
| `JTAG_TCK` / `JTAG_TMS` / `JTAG_TDI` / `JTAG_TDO` | JTAG | J4 ↔ U6 dedicated JTAG pins |
| `RECONFIG_N` | config | U6.RECONFIG_N, R15 pull-up, J4 |
| `TRIG_IN` | digital in | J5.1 → R16(1 kΩ) → U6; R17 pull-down |
| `LED_CAP` | digital out | U6 → R18 → D5 → `GND` |

## Inter-block net summary

The nets that cross block boundaries — the only ones a block coder may assume exist
outside its own file:

`VBUS_RAW`, `+5V_IN`, `+5V_SW`, `+3V3_D`, `+3V3_ADCD`, `+3V3_A`, `+1V2_D`, `GND`,
`VBIAS`, `VREF_FE`, `VOCM`, `AIN1`, `AIN2`, `CH1_P`, `CH1_N`, `CH2_P`, `CH2_N`,
`ADC_CLK`, `FPGA_CLK`, `FIFO_CLK`, `ADC_D1[11:0]`, `ADC_D2[11:0]`, `ADC_OE_N`,
`ADC_PDWN`, `FIFO_D[7:0]`, `FIFO_RXF_N`, `FIFO_TXE_N`, `FIFO_RD_N`, `FIFO_WR_N`,
`FIFO_SIWU`, `FIFO_OE_N`, `PWREN_N`, `USB_DP`, `USB_DM`.

Everything else is internal to one block.
