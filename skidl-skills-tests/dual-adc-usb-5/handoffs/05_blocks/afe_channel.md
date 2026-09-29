---
phase: 05_blocks/afe_channel
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-21T09:10:00Z
status: complete
revision: 3
next_phase: 05_coding
---

# Phase 5 handoff — block `afe_channel`

**Rev 3 = architecture rev 3's WO-1 and nothing else:** the anti-alias filter is now a 2nd-order
MFB around the THS4551 plus the existing output RC = 3rd-order Butterworth. Six values changed,
six refs added, the file's wrong filter comments replaced. Signature, call site, interface nets,
ICs, the /20 divider and the whole DC design are untouched.

## Decisions

1. **Signature unchanged, exactly as the assembler already calls it:** `afe_channel(ain,
   adc_in_p, adc_in_n, vbias, vref_fe, vocm, v3v3_a, gnd, ch=1)`. `ch` still mandatory in
   practice on the 2nd instance. Drives `adc_in_p`/`adc_in_n` only; `vbias`, `vref_fe`, `vocm`,
   `v3v3_a`, `gnd` all sensed/consumed, as before.
2. **MFB rewire per WO-1 item 2**, new local nets `CH<ch>_MFBP`/`CH<ch>_MFBN`. Membership
   verified after the edit: `MFBP={R105.2,R107.1,R111.1,C111.1}`,
   `MFBN={R106.2,R108.1,R112.1,C111.2}`, `FBP={U_fda.4,C103.1}`, `FBN={U_fda.1,C104.1}` —
   `R_f` is off the FB pins, as ordered.
3. **`R107`→OUT− (11), `R108`→OUT+ (10); `C103` FB+→OUT+, `C104` FB−→OUT−.** Versus rev 2 this
   swaps which output R107/R108 land on — identical 1.00 k parts, so a netlist relabel with no
   BOM effect, and the crosswise (negative) sense is preserved.
4. **+3 refs/channel, +6 total:** `R111`/`R112` = 499 (`R_mfb`), `C111` = 68 pF (`C_mfb`), plus
   `R211`/`R212`/`C211`. Nothing deleted; all on the existing `_FP_R0603`/`_FP_C0603`.
   **`C_mfb` is ONE differential cap across the MFB nodes**, never two to GND (CM-loop).
5. **Values:** `C103`/`C104` 27→**10 pF**, `C105` 470→**330 pF**, `C106`/`C107` 220→**100 pF**.
   `R105`–`R110` unchanged (499/499/1k/1k/33/33).
6. **Filter comments rewritten with the architect's synthesis, not recomputed:** MFB f₀ =
   5.93 MHz, Q = 1.012 (C_f eff. 10.6 pF incl. TI's 0.6 pF internal); output RC diff. pole
   6.35 MHz (2×33 Ω into 760 pF), CM pole 48 MHz; overall **−3 dB @ 6.1 MHz, −0.15 dB @
   4.0 MHz, −25.3 dB @ 16 MHz**. Rev 2's "5.1 MHz", "24 dB at 15 MHz" and "poles 2 and 3" are
   **gone from the file**.
7. **DC re-confirmed unchanged:** no DC current in `R_mfb`, DC gain still `R_f/R_g` = 2.004 →
   ±10 V in = 2.0 V p-p differential, zero differential out at 0 V in.
8. **Docstring rails updated to WO-2's:** `VBIAS` 1.100 V, `VREF_FE` 1.0453 V, tap at AIN = 0
   is 1.0452 V, buffer input 0.546…1.544 V. **No divider resistor changed.**

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/afe_channel.py` | The `@SubCircuit`, both channels, MFB filter, pin-number comments | Assembling or reviewing this block |

## Next phase must

1. **Emit exactly these calls — unchanged from rev 1/2.** Omitting `ch` is an unrecoverable
   ref collision:
   ```python
   afe_channel(ain=AIN1, adc_in_p=CH1_P, adc_in_n=CH1_N, vbias=VBIAS, vref_fe=VREF_FE,
               vocm=VOCM, v3v3_a=V3V3_A, gnd=GND, ch=1, tag='afe_channel_ch1')
   afe_channel(ain=AIN2, adc_in_p=CH2_P, adc_in_n=CH2_N, vbias=VBIAS, vref_fe=VREF_FE,
               vocm=VOCM, v3v3_a=V3V3_A, gnd=GND, ch=2, tag='afe_channel_ch2')
   ```
2. `V3V3_A.drive = POWER`, `GND.drive = POWER`, and `VBIAS`/`VREF_FE`/`VOCM` `.drive = POWER`
   if their drivers are not typed OUTPUT — this block only consumes them. `VBIAS` especially:
   it is driven through `R22`, a passive part.
3. **Do not create or pass `CH<ch>_MFBP`/`CH<ch>_MFBN`** — local, like the other six nets.

## Carried forward

- **`C112`/`C212` (L-1, WO-1 item 7) skipped deliberately**, TODO left in the file: rev 3's
  sourced ref delta is exactly R111/R112/C111 per channel. One 100 nF + one 1 µF still serve
  four VS+ pins.
- **The MFB node is now filter-critical** (R-5 closed analytically, never simulated): keep
  `R_g`/`R_f`/`R_mfb`/`C_mfb` tight, legs symmetric, and confirm on a network analyser.
- **Arithmetic nit left as written:** WO-1 gives the AIN = 0 tap as 1.0452 V; 1.100 ×
  950/999.9 = 1.0451 V. 0.1 mV, far inside the ±0.5 % parts — not "corrected", per WO-1.
- Unchanged from rev 2: J2/J3 footprint risk (a 3-hole custom footprint also drops `j[4]`),
  OPA355 top-side CM margin — now ≈180 mV, was 85 mV.

## Do not redo

- **The MFB topology and every value in it** — the architect's synthesis
  (`net_plan.md` § Anti-alias filter). ERC H-1 is arithmetic, not opinion.
- **The real-pole bound:** do not "just add another RC". 0.5 dB at 4 MHz caps you near 8 dB at
  16 MHz at any order. Complex poles or nothing.
- THS4551 PD polarity (active LOW, tied high), the RGT crosswise FB↔input straps, BAV99
  polarity, the OPA355 input-CM check, the sourcing ref-number key, trimmer-stays-a-trimmer.
- The /20 divider, 999.9 kΩ input (I4), ±30 V survival (I5), 2.0 V p-p at ±10 V.

## Receipt

- block `afe_channel` rev 3: 1 file, both channels from one `@SubCircuit`.
- **54 parts / 36 nets** for the two instances (27/channel, was 24); refs `J2,J3,U_buf1/2,
  U_fda1/2,D_clamp1/2,R101-112,R201-212,C101-111,C201-211` — no collisions.
- `py_compile` OK; `validate-footprints.py` clean; 0603 shorthands re-checked on disk;
  smoke-instantiated ×2 with `analog_power_ref`: **0 unconnected pins**, MFB/FB nodes verified.
- Signature changed: **no**. Call site: **no**. Refs added: **6**. Values changed: **6**.
- status: complete — WO-1 items 1–6, 8 done; item 7 skipped with a TODO, as permitted.
