# Design risks and inherited budgets — dual_adc_usb

Sections 1–3 are the numbers the coder and the ERC reviewer should **inherit, not
re-derive**. Section 4 is the risk register.

---

## 1. Current budget — requirement P2 (≤450 mA @ 5 V) and P3 (≤100 mA pre-enumeration)

### Running (post-enumeration)

| rail | load | current | source | VBUS current drawn |
|---|---|---|---|---|
| `+3V3_AON` | FX2LP 60 mA, EEPROM 1 mA, PWR LED 3 mA, misc 1 mA | 65 mA | AP2112K LDO from VBUS | **65 mA** |
| `+3V3` | FPGA VCCX + 3.3 V bank I/O 45 mA; +1V8 LDO input 60 mA; ADC DRVDD 24 mA; XO 4 mA; clock buffer 3 mA; CAP LED 3 mA; +1V2 buck input 41 mA; misc 10 mA | 190 mA | TLV62569 buck, η ≈ 0.88 | **143 mA** |
| `+1V2` | GW1NR-9 core + PSRAM controller | 100 mA | TLV62568 buck off +3V3, η ≈ 0.88 | (in the 190 mA above) |
| `+1V8` | GW1NR-9 PSRAM bank | 60 mA | LP5907-1.8 off +3V3 | (in the 190 mA above) |
| `+4V2A` | AD8066 ×2 (25.6 mA), THS4551 ×2 (2.8 mA), AVDD LDO input 60 mA | 88 mA | LM27762 positive LDO **from VBUS** | **88 mA** |
| `-4V2A` | AD8066 ×2, THS4551 ×2 | 28 mA | LM27762 charge pump, η ≈ 0.85 | **29 mA** |
| `+3V0A` | AD9235 ×2 AVDD | 60 mA | LP5907-3.0 off +4V2A | (in the 88 mA above) |
| — | LM27762 quiescent | 2 mA | — | **2 mA** |
| **Total** | | | | **327 mA** |

**Margin: 123 mA, 27 % of the 450 mA budget.** The two soft numbers are the FPGA core
(100 mA @ 1.2 V) and the PSRAM (60 mA @ 1.8 V), both estimates rather than datasheet
maxima. Even at double both, the total lands near 400 mA — still inside. Measure at
bring-up; a test point sits on every rail (N5).

### Pre-enumeration (P3, ≤100 mA)

Only `+3V3_AON` is live: **65 mA plus leakage ≈ 70 mA.** Everything else is held off by
`PWR_EN`, which FX2LP PA0 raises after the host has granted 500 mA. See R8 — this only
works if `PWR_EN` has its 100 kΩ pulldown.

### Thermal (X5, 0–70 °C, no heatsinks)

Worst dissipators: AP2112K 65 mA × 1.7 V = 110 mW; LP5907-3.0 60 mA × 1.2 V = 72 mW;
LP5907-1.8 60 mA × 1.5 V = 90 mW. In SOT-23-5 (θJA ≈ 250 °C/W) that is a 28 °C rise on
the worst one, giving 98 °C junction at 70 °C ambient — inside spec but the smallest margin
on the board. Nothing else exceeds 60 mW.

---

## 2. USB throughput arithmetic — requirements I5, I6, F12

| quantity | value |
|---|---|
| Sample payload, 2 ch × 10 MSPS × 12 bit | 240 Mbit/s = **30.0 MB/s** |
| Same payload padded to 16 bit | 40.0 MB/s |
| USB 2.0 HS bulk, theoretical (13 × 512 B per 125 µs microframe) | 53.2 MB/s |
| USB 2.0 HS bulk, practical on a good host with deep async queuing | 35–43 MB/s |
| Margin at 30 MB/s vs the 35 MB/s worst practical case | **17 %** |
| Margin at 40 MB/s vs the same | **−14 %** — this is why requirement 10 forbids padding |
| FX2LP slave FIFO ceiling, 8 bit × 48 MHz IFCLK | 48 MB/s — **not** the bottleneck |

**Packing scheme:** 4 consecutive 12-bit samples (48 bits) → 3 × 16-bit words, done in FPGA
fabric before the FIFO. Channel interleaving is CH1, CH2, CH1, CH2 …, so one packed group
carries two samples from each channel and the stream needs no per-sample channel tag.

**Burst mode (F12a) depth:**

| quantity | value |
|---|---|
| Embedded PSRAM | 64 Mbit = 8.00 MiB = 8.389 MB |
| Packed samples it holds | 8.389e6 × 8 / 12 = 5.59 M samples |
| Per channel | **2.80 Mpt** |
| Record length at 10 MSPS | **280 ms per channel** |
| After reserving 1 MiB for headers and metadata | 2.45 Mpt/ch = 245 ms |
| Drain time at 30 MB/s | ≈ 250 ms, host-independent, lossless |
| Fallback if the PSRAM interface cannot be brought up: BSRAM only (468 kbit) | 19.5 kpt/ch = **1.95 ms** |

The fallback number is the reason the PSRAM part was chosen over a plain GW1N-9: 1.95 ms is
one screen, 245 ms is a record.

**Streaming mode (F12b):** the FPGA drains the BSRAM elastic FIFO straight to the endpoint
and sets an overrun bit in the packet header when the FIFO backs up. Best-effort by
definition; the burst path is what makes the 10 MSPS claim honest.

---

## 3. Jitter budget — requirement F11 (≥60 dB SNR, ≥9.5 ENOB)

Jitter-limited SNR = −20·log₁₀(2π · f_in · t_j,rms).

| t_j,rms | SNR at 1 MHz | SNR at 4 MHz (band edge) |
|---|---|---|
| 2.5 ps (this design) | 96 dB | **84 dB** |
| 10 ps | 84 dB | 72 dB |
| 20 ps | 78 dB | 66 dB ← the bar |
| 50 ps | 70 dB | 58 dB — would fail F11 |

**Budget:** SiT1602 MEMS XO ≈ 1.3 ps + SN74LVC2G34 additive ≈ 2 ps + AD9235 aperture
jitter 0.5 ps, RSS ≈ **2.5 ps rms — roughly 8× inside the 20 ps bar.** Jitter is a non-issue
in this design, which is the whole point of spending $1.25 on a dedicated oscillator instead
of taking the clock from the FPGA PLL.

**Composite SNR at 4 MHz:** ADC 70 dB ⊕ front-end thermal noise 77.9 dB ⊕ jitter 84 dB
≈ **68.9 dB → ENOB 11.2 bits.** Comfortably past F11's 60 dB / 9.5 bit.

**Channel skew (F10, ≤100 ns):** both CLK pins are driven from the two halves of one
SN74LVC2G34 die — part-to-part skew < 1 ns, trace mismatch < 100 ps, analog group-delay
mismatch from component tolerance a few ns at 4 MHz. Total < 5 ns against a 100 ns budget.

---

## 4. Risk register

Severity is about **what it costs to discover late**, not likelihood.

### R1 — [HIGH] FPGA pin budget against the 1.8 V PSRAM bank

GW1NR-9 QN88P offers 71 user I/O, but the PSRAM is bonded internally to one I/O bank whose
VCCIO must be **1.8 V**. Any package pins in that bank cannot carry 3.3 V signals. Our 3.3 V
pin demand is: 24 ADC data + 1 ADC clock + 2 OTR + 18 slave FIFO + 2 trigger/LED + 2 misc =
**~49**, plus 4 dedicated JTAG. If the 1.8 V bank consumes ~19 package pins, 52 remain — a
3-pin margin.
*Mitigations already taken:* 8-bit slave FIFO instead of 16-bit (saves 8 pins; 48 MB/s still
gives 60 % headroom over the 30 MB/s payload).
*Mitigation if still short:* drop `ADC1_OTR`/`ADC2_OTR` (the FPGA can detect full-scale codes
in the data), then the trigger output direction, then the CAP LED.
**Action for the datasheet phase: obtain Gowin UG803 (GW1NR-9 Pinout) and confirm which bank
is the PSRAM bank and exactly how many 3.3 V-capable user I/O the QN88P leaves.** This is the
single most likely source of an architecture escalation.

### R2 — [HIGH] GW1NR-9 is single-source with 102 units in stock

Gowin is the only manufacturer; JLCPCB stock is 102 at $20.91, Extended tier — below the
500-unit warning threshold and the lowest-stock keystone in the design. Five boards need 5.
*Escalation part:* GW2AR-LV18QN88C8/I7 (168 in stock, $51.19) — same QN88 package and same
64 Mbit embedded PSRAM, believed pin-compatible. **Verify pin compatibility against UG803
before relying on it.** If both are gone the architecture must change, not the BOM.

### R3 — [MED] AD9235BCPZ-40 stock and tier

170 in stock, Extended, $18.41. Ten needed. Same-footprint LFCSP-32 alternates
AD9235BCPZ-20 (28) and AD9235BCPZ-65 (4) bring the pool to 202. The TSSOP-28 variants share
the die but **not** the footprint. If the LFCSP pool empties, escalate — do not silently
substitute a different converter family; the ADC's supply voltage and common mode set the
whole front-end signal plan.

### R4 — [MED] Anti-alias stopband margin is thin

Design gives 32.7 dB at 10 MHz against F7's ≥30 dB — **2.7 dB of margin**. A +5 % shift in
filter fc from component tolerance eats most of it (fc → 4.1 MHz gives 31.0 dB).
*Mitigation:* specify ±2 % C0G capacitors and ±1 % resistors in both filter stages (already
in the skeleton BOM), and centre fc at 3.9 MHz rather than 4.0 MHz. The 20 MHz figure
(56.8 dB vs ≥50 dB) has real margin and is not at risk.
*If it fails at bring-up:* drop the SK section's R from 324 Ω to 340 Ω, moving fc to
3.75 MHz and buying 2.5 dB, at the cost of 0.4 dB of droop at 4 MHz.

### R5 — [MED] Compensation trimmer availability

The bottom-leg compensation capacitor wants a 6–30 pF trimmer so each channel's attenuator
can be flattened at bring-up. SMD trimmer capacitors are poorly stocked at JLCPCB.
*Fallback:* a fixed 150 pF C0G, selected at bring-up from a small kit. This costs HF
flatness (a few percent of amplitude error above ~100 kHz) but **not** DC gain accuracy —
F8's ±2 % FS is a DC specification and is unaffected. The sourcer should attempt the trimmer
and fall back without escalating.

### R6 — [MED] Gowin power-supply ramp-rate window

GW1NR-9 requires **monotonic** ramps: VCC 0.6–6 mV/µs, VCCX and VCCIO 0.6–10 mV/µs. For the
1.2 V core that is a **0.2–2 ms** ramp; for 3.3 V, 0.33–5.5 ms. The datasheet imposes no
sequencing *order*, only these rates, and requires all supplies in range before
configuration.
*Action:* the datasheet phase must confirm TLV62568 and TLV62569 soft-start times land in
those windows (both are ~1 ms typical, which does — but confirm, and check that the EN-pin
release from `PWR_EN` does not produce a non-monotonic step).

### R7 — [MED] The ±4.2 V rails are a deliberate deviation from requirement 9

Requirement 9 says "bipolar analog rails (e.g. ±5 V/±6 V)". This design uses **±4.2 V**
because LM27762's positive output is an LDO from VBUS (max 5.5 V in) and VBUS can be as low
as 4.75 V at the port. The binding parts of requirement 9 — *bipolar* and *LDO
post-regulated on every analog rail* — are met, and the largest signal anywhere in the chain
is ±0.909 V, so the headroom is never needed. Recorded here rather than silently taken.

### R8 — [MED] `PWR_EN` must default low, or P3 is violated on every power-up

FX2LP PORTA pins are high-impedance after reset. Without the **100 kΩ pulldown on `PWR_EN`**
the enable line floats, the main buck and the analog converter may come up before
enumeration, and the board draws ~327 mA when the host has only granted 100 mA. Some hosts
will drop the port. This resistor is not optional and must not be value-engineered away.

### R9 — [MED] AD8066 input common-mode range under overload

At ±4.2 V rails the AD8066 input CM range is roughly −4.2 V to +2.7 V. On a +50 V input the
BAV199 clamp holds the buffer input at about +4.7 V — inside the absolute maximum of
(+VS + 0.7 V) = +4.9 V, but well above the linear CM range. AD8066 is specified as free of
output phase reversal; **confirm this in the datasheet phase.** If it is not, the buffer
recovers from overload with an inverted output, which shows as a wrong-polarity glitch, not
damage. Acceptable but should be known.

### R10 — [MED] Switching noise into a 1 MΩ high-impedance node

Three switchers (TLV62569 and TLV62568 at 1.5 MHz, LM27762 at 2 MHz) share a board with a
1 MΩ front end whose tap sits at 82.6 kΩ. Layout instructions:
- Put both bucks and the LM27762 physically distant from the BNC end of the board, on the
  digital side of the plane split.
- Keep all three inductors' switch nodes small and away from the analog section.
- FB2 (ferrite) + 10 µF between VBUS and LM27762's VIN; FB3 on `+3V0A`; FB4 on `+3V3_DRV`.
- Guard-ring the `CHx_TAP` and `CHx_BUFIN` nodes to GND and keep them under ~10 mm.
- LM27762's 2 MHz fundamental sits **above** the 10 Hz–1 MHz band in which P5 is specified;
  that is deliberate and should not be traded away by substituting a slower converter.

### R11 — [MED] 24 ADC data lines cross the board at 10 MHz

`ADC1_D[11:0]` and `ADC2_D[11:0]` run from the ADCs to the FPGA past the analog section.
Route them on an inner layer over a solid, continuous ground reference, keep them off the
analog side entirely, and place the FPGA close enough that no series termination is needed.
If crosstalk shows at bring-up, 33 Ω series resistors at the ADC end are the fix — leave
pads if board area allows.

### R12 — [LOW] One `GND` net in the netlist, two planes on the board

The netlist deliberately carries a single `GND`. The analog/digital plane split, and the
single tie point directly under the ADCs' ground pins, are a layout instruction. Do not
"fix" this by adding an `AGND` net — it produces a floating net at ERC and does not describe
what the board actually needs.

### R13 — [LOW] THS4551 second source is not footprint-compatible

ADA4940-1ARZ-R7 (SOIC-8) is a valid electrical second source but a different footprint from
THS4551IRGTR (QFN-16-EP 3×3). Swapping it is a layout change, not a BOM change.

### R14 — [MED] 909 kΩ attenuator resistor voltage rating

F9 puts ~45 V continuously across the top leg. A standard 0603 thick-film is rated 50–75 V
working, which leaves almost no margin. Use an 0805 or 1206 rated ≥100 V, or two 453 kΩ
0603 in series. This is easy to miss because the *power* dissipation (2.75 mW) looks trivial.

### R15 — [MED] No on-board calibration source

Carried forward from requirements. F8's ±2 % FS assumes a one-time host-side calibration
against an external reference, per channel and per gain path. Nothing on the board can
self-calibrate. A DAC-based self-cal path was considered and not fitted.

### R16 — [LOW] BNC shells tie to board ground; channels are not isolated

Carried forward from requirements. Both BNC shells connect to `GND`. Probing two points at
different ground potentials will short them through the board. If isolated channels are ever
wanted, this design cannot be adapted — it is a different architecture.

### R17 — [LOW] Firmware is out of scope but the hardware must not preclude it

EEPROM fitted (I9), JTAG header fitted (I11). The FPGA's packing engine, trigger comparator,
PSRAM controller and overrun logic, and the FX2LP's slave-FIFO and vendor-control firmware,
are all outside this pipeline. The netlist is complete without them; the board is not
useful without them.
