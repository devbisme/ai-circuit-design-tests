# Design Risks — dual_adc_usb

Severity: **H** = will cause a respin or miss a [HARD] spec if unmitigated · **M** =
degrades performance or yield · **L** = watch item.
Status: **mitigated in architecture** = the mitigation is already in `block_diagram.md` /
`net_plan.md` / `skeleton_bom.md` · **open** = needs a later phase or bench work.

---

## R-01 — Sample-clock jitter limits ENOB · **H** · mitigated in architecture

The 12-bit jitter budget at a 5 MHz input is **12.7 ps RMS**
(`SNR_jitter = −20·log₁₀(2π·f_in·t_j)`, solved for 68 dB). A clock generated in FPGA
fabric or by an FPGA PLL carries 15–30 ps RMS — that alone would cost ≈1 bit of ENOB and
miss the ≥10.5-bit target.

**Mitigation (already in the design):** a dedicated 10.000 MHz CMOS XO with a **≤5 ps RMS
phase jitter spec** drives the ADCs through 74LVC1G34 buffers, on a ferrite-isolated
`V3V3_CLK` rail. The clock **never passes through FPGA fabric**; the FPGA only *receives*
a copy for its capture domain.
**Constrains sourcing:** the jitter spec on X1 is binding — an "10 MHz oscillator" without
a phase-jitter number is not an acceptable substitute.
**Constrains layout:** keep `CLK_ADC_A`/`CLK_ADC_B` short, over unbroken ground, and
length-matched to ±2 mm.

## R-02 — Charge-pump switching noise on the −5 V op-amp rail · **M** · mitigated

The LM2776 switches at a frequency inside the ADC's Nyquist band. Raw output ripple can be
tens of mV; the AD8066's PSRR at MHz frequencies is only ~40 dB, so unfiltered ripple
would appear as a spur of roughly 1 LSB.

**Mitigation:** 10 µH + 22 µF LC post-filter on `VN5_A` (>90 dB at the switching
frequency), plus 100 nF + 1 µF at every op-amp supply pin. Place U3 in the power zone,
never under or beside the AFE.
**Open item for layout:** the LM2776 flying-cap loop is the noisiest loop on the board —
keep it under ~5 mm² and away from the attenuator nodes.

## R-03 — Digital coupling into the 12-bit analog front end · **H** · partially open

`1 LSB = 488 µV at the ADC = 4.88 mV at the BNC`. Three aggressors switch hard: 24 ADC
data lines, 39 SRAM lines at up to 60 MHz, and 8 sync-FIFO lines at 60 MHz.

**Mitigations in the architecture:** 100 Ω series damping on all 24 ADC data lines *at the
ADC end*; DRVDD fed through a ferrite so ADC output return current stays in the digital
zone; A3 and the ADCs on a separate low-noise `V3V3_A` LDO; physical zoning with the
analog half of the board on the BNC side.
**Open — belongs to layout:** ADC packages must straddle the zone boundary with analog
pins facing the AFE; no digital trace may cross under the attenuator nodes; the
attenuator's high-impedance node needs a ground guard ring.

## R-04 — Split ground planes would make R-03 worse, not better · **M** · decided

The instinctive fix for R-03 is a split analog/digital plane. With a 39-line SRAM bus and
a 60 MHz FIFO bus, a split plane forces return currents to detour around the gap and
radiates far more than it isolates.

**Decision:** **one continuous ground net and one solid uninterrupted GND plane on layer
2**, isolation by placement only. This follows current ADI/Kester practice for
mixed-signal converter boards. Recorded here so a later reviewer does not "fix" it.
**Constrains coding:** SKiDL must use a **single `GND` net** — no AGND/DGND pair, no 0 Ω
link component.

## R-05 — Attenuator compensation is a production trim step · **M** · open

The 20:1 divider presents 1 MΩ ∥ ~20 pF and a 47.5 kΩ Thevenin source. Its flatness to
5 MHz depends on `R_top·C_top = R_bot·C_bot` holding across stray capacitance that is
board- and assembly-dependent. Untrimmed, expect several dB of error at 5 MHz and visible
square-wave overshoot/rolloff.

**Mitigation:** a 2–10 pF C0G trimmer per channel (in the BOM), C0G/NP0 only in the
divider, minimum copper area at the divider node, guard ring.
**Open:** this makes board bring-up a **per-unit calibration step** (square-wave in,
trim for flat top) exactly as on a real scope probe. At 5–10 boards this is acceptable;
at volume, consider a fixed-C design characterised on the final stackup.

## R-06 — Anti-alias filter order is set by the [HARD] stopband spec · **M** · resolved

"≥40 dB by 15–20 MHz with a 5 MHz corner" cannot be met by 2nd order (19 dB @ 15 MHz,
24 dB @ 20 MHz) or 3rd order (29 / 36 dB). Only **4th order** clears it
(**38 dB @ 15 MHz, 48 dB @ 20 MHz**).

**Consequence, recorded so no one "simplifies" it away:** three op-amp stages per channel
are not gold-plating — A1 is mandatory because the 47.5 kΩ attenuator source cannot drive
a filter network directly, and A2+A3 are the two 2nd-order sections the stopband spec
requires. Deleting a stage breaks a [HARD] requirement.
**Open for the coder:** exact R/C values from a 4th-order Butterworth synthesis at
fc = 5.0 MHz (two sections, Q = 0.5412 and Q = 1.3065), with A3 carrying gain −2.

## R-07 — Single-ended drive of the AD9235 costs SFDR · **M** · open, with a planned escape

The AD9235 is characterised differentially; driven single-ended it loses roughly 2–3 dB of
SNR and considerably more SFDR (even-order distortion no longer cancels). The noise budget
in `ic_selection.md` closes at ENOB ≈ 11.1 bits *before* distortion terms, so there is
~0.6 bit of margin — but it is not enormous.

**Planned escape if bench ENOB < 10.5 bits:** replace A3 (OPA836, single) with a
fully-differential driver (THS4521IDGK / OPA1637) feeding `VIN+`/`VIN−`. The AFE is
deliberately partitioned so this is a **change to one package plus its R/C network** —
A1/A2, the attenuator, the ADC and every other block are untouched.
**Constrains layout:** route `ADC_x_IN` and `ADC_x_VINN` as a matched pair to the ADC
even in single-ended mode, so the differential upgrade needs no re-route.

## R-08 — FT232H sync-FIFO write timing at 60 MHz · **M** · open

The FPGA drives `FIFO_D[7:0]` and `WR#` synchronously to the FT232H's 60 MHz `CLKOUT`
(16.67 ns period). iCE40 clock-to-out through an I/O register plus PCB delay can eat most
of the FT232H's setup window.

**Mitigation:** register all FIFO outputs in **I/O cell flip-flops** (not fabric), and use
the **iCE40 PLL to phase-shift the FIFO output clock domain** relative to `CLK60`. The
iCE40HX4K has a PLL; this is why a PLL was a selection criterion.
**Open:** timing closure is a gateware task, not a schematic one — but if it fails, the
fallback is to drop the FIFO to 30 MHz, which halves sustained throughput to ~15 MB/s and
would force dual-continuous mode down to N ≥ 4 (2.5 MSPS/ch). Flagged so the consequence
is known.

## R-09 — USB power budget has 31% margin, not 50% · **M** · mitigated, with a contingency

Estimated total is **345 mA against 500 mA**. The estimate is built from datasheet typicals;
FPGA I/O power in particular scales with how hard the SRAM bus is driven and is the least
certain line.

**Mitigations:** LDOs sized with headroom; the 3V3_D LDO in SOT-223 (0.37 W); ADC data
lines damped at 100 Ω which also reduces I/O switching current.
**Contingency if measured draw exceeds 450 mA:** replace the 3V3_D LDO with a synchronous
buck (e.g. TPS62825, 2 MHz) — saves ≈50 mA of VBUS. **This is the contingency, not the
default**, because a switcher next to a 12-bit ADC costs noise margin (R-03).
**Constrains sourcing:** if the sourcer substitutes AD9235BRUZ-**65** for both channels
(2 × 300 mW ≈ 180 mA vs 80 mA), the budget breaks. That substitution requires escalation.

## R-10 — USB enumeration current compliance · **M** · mitigated in architecture

A USB device may draw no more than 100 mA before it is configured. Fully powered, this
board draws 345 mA.

**Mitigation:** `PWREN_N` (FT232H ACBUS9, EEPROM-configured) gates the P-FET load switch
on `V5_A`, the LP5907 enable on `V3V3_A`, and the LM2776 — 165 mA of analog load plus the
oscillator. Pre-enumeration draw is ≈65–80 mA.
**Constrains sourcing:** the `V3V3_A` LDO **must have an enable pin**. A fixed-on LDO
breaks USB compliance.
**Open:** the FT232H EEPROM image must be programmed with ACBUS9 = PWREN# at first
bring-up, or the analog section never powers on. Document it in the bring-up procedure.

## R-11 — Thermal: 3V3_D LDO dissipation · **L** · mitigated

0.37 W at 190 mA and VBUS = 5.25 V. In SOT-223 with a copper pour (θJA ≈ 60 °C/W) this is
a 22 °C rise over a 50 °C ambient — fine. In SOT-23-5 (θJA ≈ 235 °C/W) it would be an
87 °C rise and fail.
**Constrains sourcing: the SOT-223 (or better) package on U1 is a thermal requirement, not
a preference.**

## R-12 — Input over-voltage survivability · **L** · quantified, closed

At the [SOFT] target of ±40 V continuous, the 20:1 attenuator node reaches only ±2.0 V —
inside the ±5 V op-amp rails, so nothing conducts and nothing is stressed (1.7 mW in the
top leg). The BAV99 clamp only conducts beyond roughly ±100 V. The 950 kΩ top leg is two
series 475 kΩ **0805** parts so neither exceeds its working-voltage rating and the voltage
coefficient of resistance is halved.
**Constrains sourcing:** **do not shrink the attenuator top-leg resistors to 0402** — the
package size is a voltage rating, not a footprint preference.
**Residual/open:** ESD at the BNC is handled by the 950 kΩ series path plus the buffer
clamp. A discrete TVS footprint is provided but left DNP: any TVS there must be **<2 pF**
(or it loads a 1 MΩ / 5 MHz input) **and ≥45 V standoff** (or it conducts during legal
±40 V over-range). Expect ±4 kV contact per IEC 61000-4-2 to pass; **±8 kV requires bench
validation.**

## R-13 — Channel-to-channel sampling skew · **L** · mitigated

"Simultaneous" is the headline claim of a dual-channel instrument. Two ADCs on one XO
through two separate buffers accumulate buffer skew (≈50 ps part-to-part) plus trace
mismatch.
**Mitigation:** length-match `CLK_ADC_A`/`CLK_ADC_B` to ±2 mm (≈13 ps). Total skew stays
under ~70 ps = **0.0007 sample** at 10 MSPS. Not a practical concern once matched, but it
*is* a concern if the two clocks are routed casually.

## R-14 — Parts with no KiCad symbol · **M** · open, hands to the datasheet phase

Verified against the installed libraries. These have **no symbol** and must be generated
with `kipart` before coding:

| Part | Pins | Difficulty |
|---|---|---|
| AD9235BRUZ-20 (×2 uses) | 28 | easy |
| IS61WV25616BLL-10TLI | 44 | easy, mechanical |
| AD8066ARZ (dual op-amp) | 8 | trivial — or reuse any standard SOIC-8 dual-op-amp symbol |
| OPA836IDBVR (single op-amp) | 6 | trivial — or reuse a standard SOT-23-5/6 op-amp symbol |

These **do** exist and must be used rather than regenerated: `FPGA_Lattice:ICE40HX4K-TQ144`,
`Interface_USB:FT232H`, `Memory_Flash:W25Q32JVSS`, `Memory_EEPROM:93CxxC`,
`Regulator_Linear:AP7361C-33E`, `Regulator_Linear:AP2112K-1.2`,
`Regulator_Linear:LP5907MFX-3.3`, `Regulator_SwitchedCapacitor:LM2776`,
`Reference_Voltage:REF3025`, `Power_Protection:USBLC6-2SC6`, `Diode:BAV99`,
`74xGxx:74LVC1G34`, `Oscillator:ASE-xxxMHz`, `Connector:BNC`,
`Connector:USB_C_Receptacle_USB2.0_16P`.

## R-15 — Live stock data was unavailable during architecture · **M** · open

The `pcbparts` MCP was not connected, so **no JLCPCB stock, tier or pricing was verified**
for any part in this design. Every "JLCPCB expectation" is an engineering estimate.
**Highest sourcing risk, in order:** AD9235BRUZ-20 (high-speed ADI converter, thin
distributor stock is common), iCE40HX4K-TQ144, IS61WV25616BLL-10TLI, FT232HL.
**Mitigation already provided:** each of these carries a named, vetted second source and
an explicit "substitute on these electrical criteria" rule in `ic_selection.md` Part 3.

---

## Summary

| Severity | Count | IDs |
|---|---|---|
| **H** | 2 | R-01, R-03 |
| **M** | 10 | R-02, R-04, R-05, R-06, R-07, R-08, R-09, R-10, R-14, R-15 |
| **L** | 3 | R-11, R-12, R-13 |
| **Unresolved / open at end of architecture** | **7** | R-03 (layout), R-05 (trim), R-07 (bench ENOB), R-08 (gateware timing), R-10 (EEPROM programming), R-14 (symbol generation), R-15 (stock verification) |
