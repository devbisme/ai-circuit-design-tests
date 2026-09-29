# AD9235BRUZ-20 — 12-bit, 20 MSPS pipelined ADC (TSSOP-28)

SOURCE: Analog Devices AD9235 Data Sheet Rev. D (verified via two independent
extractions of the official datasheet text: analog.com PDF cover/spec pages and the
radiolocman.com HTML mirror of the same Rev. D document, cross-checked for
self-consistency). PDF download to `datasheets/` failed (analog.com host timed out from
this sandbox on every attempt — see Phase 2 log); **PDF not retrieved**. Pin table and
electrical facts below are read directly from datasheet text, not guessed. **No KiCad
symbol exists for this part — this pin table is the kipart input for the coding phase.**

| Spec | Value |
|------|-------|
| Package | TSSOP-28 (RU-28 suffix); note the datasheet also offers a 32-lead LFCSP — **this design uses TSSOP-28 only**, do not mix pinouts |
| Resolution / rate | 12-bit, up to 20 MSPS (speed grade "-20") |
| AVDD | 3.0 V (single analog supply, both AVDD pins) |
| DRVDD | 2.5 V or 3.3 V (digital output driver supply — independent of AVDD; this design should tie DRVDD to the 3V3_A/digital rail feeding the FPGA's expected input logic level) |
| Analog input span | **Fixed at 2.0 V p-p differential** in this design (SENSE=AGND mode) — see strapping below |
| Power (at 20 MSPS) | ≈ 148 mW typical (AVDD+DRVDD combined, per datasheet Table 1 at -20 speed grade) |
| Operating temp | −40 °C to +85 °C (industrial) |
| Output coding | Offset binary (default, MODE=AGND) or twos complement (MODE strapped high) — **this design uses offset binary**, confirm FPGA decoder matches |
| Clock input | CLK pin, LVCMOS-compatible, driven from the buffered 10 MHz XO chain (74LVC1G34 buffer + 33 Ω series termination, R10–R12) |

## Pinout (28-lead TSSOP, pin 1 in upper-left with notch, per datasheet Figure "Pin
Configuration—TSSOP")

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | OTR | digital out | Out-of-Range indicator (asserts when input exceeds full scale) |
| 2 | MODE | digital in | Data format (offset binary/twos complement) + duty-cycle-stabilizer (DCS) select |
| 3 | SENSE | analog in | Reference-mode select (strap pin, see below) |
| 4 | VREF | analog I/O | Voltage reference input/output — in internal-reference mode (this design) it is an **output**, decouple only |
| 5 | REFB | analog | Differential reference, negative side — internally generated, do not drive |
| 6 | REFT | analog | Differential reference, positive side — internally generated, do not drive |
| 7 | AVDD | power in | Analog 3.0 V supply |
| 8 | AGND | power in | Analog ground |
| 9 | VIN+ | analog in | Analog input, positive — drives the signal in this single-ended design |
| 10 | VIN− | analog in | Analog input, negative — **DC-biased at 1.500 V** in this design (static, not signal-carrying) |
| 11 | AGND | power in | Analog ground |
| 12 | AVDD | power in | Analog 3.0 V supply |
| 13 | CLK | digital in | Sample clock input |
| 14 | PDWN | digital in | Power-down, active HIGH — tie LOW (AGND) for normal operation |
| 15 | D0 (LSB) | digital out | Data bit 0 |
| 16 | D1 | digital out | Data bit 1 |
| 17 | D2 | digital out | Data bit 2 |
| 18 | D3 | digital out | Data bit 3 |
| 19 | D4 | digital out | Data bit 4 |
| 20 | D5 | digital out | Data bit 5 |
| 21 | D6 | digital out | Data bit 6 |
| 22 | D7 | digital out | Data bit 7 |
| 23 | DGND | power in | Digital output ground |
| 24 | DRVDD | power in | Digital output driver supply |
| 25 | D8 | digital out | Data bit 8 |
| 26 | D9 | digital out | Data bit 9 |
| 27 | D10 | digital out | Data bit 10 |
| 28 | D11 (MSB) | digital out | Data bit 11 |

**Confidence flag:** pins 1–14 and the D-bus/DGND/DRVDD split (23/24 sitting between the
two D-bus groups) are corroborated by two independent datasheet-text extractions and are
high confidence. The individual LSB→MSB ascending assignment across 15–22 and 25–28 is
the standard ADI convention for this pin diagram style but was **not itself pin-by-pin
quoted** in either source — verify against the datasheet's actual Figure before final
layout if a bit-order error would be costly (it is not ERC-visible, only
functionally wrong).

## ⭐ AD9235 SENSE/REFT/REFB strapping — 2 V p-p single-ended span, VIN− = 1.500 V (open item resolved)

This is the specific open item the architecture deferred to this phase. Confirmed from
the datasheet's Reference Configuration Summary (VREF-mode-vs-span table, extracted
directly): **VREF = 1.0 V internal mode → 2.0 V p-p full-scale differential input span**;
VREF = 0.5 V mode → only 1.0 V p-p (not enough — do not use).

**Strapping (RECOMMENDED, apply as follows):**

1. **SENSE (pin 3) → tie directly to AGND** (short trace/via, not through a resistor).
   This selects the internal reference's maximum-span mode: VREF = 1.0 V, REFT−REFB =
   1.0 V, full-scale differential input span = **2.000 V p-p**. This is the only SENSE
   strap that reaches the required 2 V p-p span (SENSE=VREF gives only 1 V p-p; SENSE=AVDD
   disables the internal reference entirely and requires an external reference — not used
   here).
2. **VREF (pin 4):** decouple with a 0.1 µF ceramic cap to AGND, close to the pin. In this
   mode VREF is an **output** of the on-chip band-gap — do not drive it and do not load it
   with anything beyond the bypass cap.
3. **REFT (pin 6) and REFB (pin 5):** each gets its own dedicated 0.1 µF ceramic cap
   directly to AGND, placed as close to the pin as physically possible. These are
   internally-generated low-level analog nodes — **do not drive them externally and do
   not tap them with a resistor divider** (loading REFT/REFB unbalances the reference
   ladder and directly degrades ADC linearity — this is why VIN− bias should NOT be
   derived from REFT/REFB, see next point).
4. **VIN− (pin 10), the 1.500 V DC bias:** derive this from a **dedicated** low-impedance
   source, not from REFT/REFB and not from the same R7/R8 (4.02 kΩ/1.00 kΩ) divider
   already committed in `power_analog` to the AFE's 0.5 V level-shift offset input (that
   divider's output, 2.5 V × 1.00 k/5.02 k ≈ 0.498 V, is a *different* node — it feeds the
   AFE op-amp's (U_b/OPA836) offset-summing input, not the ADC pin, and must not be
   reused here). **Coding-phase action required:** add one more small resistor divider off
   the same REF3025 2.5 V reference (U5) sized for 1.500 V (e.g. ratio 3:2, such as
   1.50 kΩ over 1.00 kΩ, exact values TBD in coding phase — precision isn't critical here
   since this is just a DC bias, not a gain-setting network) and decouple the VIN− pin
   itself heavily (this design's `C_ref` budget of 100 nF×3 / 1 µF×2 / 10 µF×1 should be
   allocated: 100 nF each at VREF/REFT/REFB per point 2–3 above, and the remaining 2×1 µF
   + 1×10 µF at the VIN− bias node — it needs to look like a strong AC ground at the
   20 MSPS sample rate since it absorbs sampling-instant charge kickback just like a real
   signal input would).
5. **VIN+ (pin 9):** driven by the AFE chain's final stage (U_b, OPA836 MFB filter/level
   shift output), AC signal centered at 1.500 V swinging 0.5 V–2.5 V (2 V p-p), matching
   the mid-supply common mode set by VIN− above.
6. **MODE (pin 2):** tie to AGND for the simplest/default configuration — offset binary
   output coding, duty-cycle stabilizer disabled. *(Moderate confidence — this pin is a
   multi-level strap on this ADC family and its exact 2–4-level table was not directly
   quoted from the datasheet in this session; AGND=default is the standard convention
   across the AD922x/AD923x family but confirm against the datasheet's MODE truth table
   before board spin if DCS-on or twos-complement is actually wanted.)*
7. **PDWN (pin 14):** tie LOW (AGND) for normal operation (active-high power-down, per
   datasheet).
8. **OTR (pin 1):** digital output, route to a spare FPGA input if out-of-range flagging
   is wanted; otherwise leave unconnected (NC) — it is a push-pull digital output, safe to
   leave floating.

## Notes

- AVDD needs 4× 100 nF (one per AVDD pin at the pin) + 1× 10 µF bulk (per sourced BOM
  `C_avdd`).
- DRVDD needs 100 nF + 1 µF (per sourced BOM `C_drvdd`).
- FB_drv (ferrite bead) isolates DRVDD from the shared digital rail — keep DRVDD's own
  local decoupling on the ADC side of the bead.
- CLK pin should see a clean, series-terminated (33 Ω, R_s-equivalent per `clock_gen`
  block) LVCMOS edge from the buffered XO chain.
- Data bus (D0–D11 + OTR) drives the FPGA through R_damp series-damping resistors
  (12× 100 Ω, one per data line, per sourced BOM) — connect FPGA-side after the resistor,
  ADC-side pin directly.
- **If a −40, −65, or AD9236BRUZ-80 speed-grade substitution is ever made** (sourcing
  phase flagged these as pin/footprint-compatible alternates), this entire pin table and
  strapping topology is unchanged — only timing specs differ.
