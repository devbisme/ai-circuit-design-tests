---
phase: 05_blocks/analog_power_ref
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-21T09:10:00Z
status: complete
revision: 3
next_phase: 05_coding
---

# Block handoff — analog_power_ref

**Rev 3 executes architecture rev 3's WO-2 and nothing else: two resistor values.** `VBIAS`
moves 1.200 V → 1.1000 V. No topology, signature, call-site, net or part-count change; no new
or deleted refs. Everything else in the file was already correct as built.

## Decisions

1. **Final signature, unchanged:** `analog_power_ref(v5_sw, v3v3_a, vbias, vref_fe, gnd)`.
2. **`R8` = 21.0k → `22.0k`, `R9` = 12.0k → `11.0k`.** `VBIAS` = 3.3 × 11.0/33.0 = **1.1000 V**
   exactly (11/33 = 1/3, both E24). The sum stays 33 kΩ, so divider current and source
   impedance are unchanged and `R10`/`C12`'s 160 Hz pole is untouched.
3. **`VREF_FE` follows automatically to 0.95025 × 1.100 = 1.0453 V** with no resistor change —
   the front end's zero-input match depends on the `VREF_FE`/`VBIAS` *ratio*, not the absolute
   value. `R19`/`R11`/`R10`/`C12`/`R22`/`U3`/`U4`/`FB3`/`C8`–`C12` were all left alone.
4. **Why 1.100 V** (recorded in the docstring): OPA355's input-CM ceiling is (V+) − 1.5 V =
   1.800 V, and at `VBIAS` = 1.200 V the buffer input reached 1.639 V at +10 V full scale —
   85 mV of worst-case margin (ERC M-1, `design_risks.md` R-3). At 1.100 V it tops out at
   1.544 V, margin ≈180 mV.
5. **The ERC report's `R8` = 23.0k / `VBIAS` = 1.000 V was NOT used**, per architecture decision
   19: 23.0 kΩ is not an E96/E24/E192 value, 1.000 V violates the OPA355 abs-max in the −30 V
   survival case (SPEC I5), and it pushes the THS4551 summing node toward an unverified floor.
   The docstring says so, so nobody "fixes" it back.
6. **Nets driven / sensed unchanged:** drives `+3V3_A` (U3.OUT), `VBIAS` (U4A **through `R22`**,
   so the pin ERC sees on `VBIAS` is a passive resistor pin) and `VREF_FE` (U4B). Consumes only
   `+5V_SW` and `GND`.
7. **Docstring updated**: the ASCII divider diagram (22.0k/11.0k, 1.1000 V, 1.0453 V), the ratio
   paragraph ("12/33 … both E96" → "11/33 = 1/3 exactly, both E24"), the `Args:` entries for
   `vbias`/`vref_fe`, and the summary line. Rev-2 decisions 2–6 (R22 inside the loop, R19 top /
   R11 bottom, U3 EN tie, the generated U3 symbol, the SPEC-P8 pi-filter, both U4 halves used,
   wiring by pin number) stand verbatim and were not touched.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/analog_power_ref.py` | The `analog_power_ref` SubCircuit | Assembling `__main__.py` |

## Next phase must

1. Emit exactly this call — **unchanged from rev 1/2**:
   ```python
   analog_power_ref(v5_sw=V5V_SW, v3v3_a=V3V3_A, vbias=VBIAS, vref_fe=VREF_FE, gnd=GND,
                    tag='analog_power_ref')
   ```
2. **`VBIAS` may still need `.drive = POWER` at the top level** — it is driven through `R22`, a
   passive part, so SKiDL sees no driving pin on it. Fix it at the top level; do **not** move
   U4A's output back onto `VBIAS` (that undoes decision 16). `+3V3_A`/`VREF_FE` are unaffected.
3. **Do not create or pass** `V5_LDO_IN`, `VBIAS_DIV`, `VBIAS_FLT`, `VREF_FE_DIV`, `VBIAS_DRV` —
   all five are local to this block.
4. **No BOM consequence beyond WO-3's row edit:** the `R8`/`R9` row is "generic 1 % 0603,
   sourcer's discretion"; the architect's suggested parts are 22 kΩ = 0603WAF2202T5E (C31850)
   and 11 kΩ = 0603WAF1102T5E (C25950).

## Carried forward

1. **Still no dedicated capacitor on `VBIAS` or `VREF_FE`.** Safe to add on the `VBIAS` side now
   that `R22` exists; if `afe_channel` wants a local AC ground it belongs next to `C_bot`.
   Nobody has decided it is needed.
2. **`VREF_FE` has no isolation resistor.** U4B drives two 499 Ω `R_g2` legs plus trace — much
   lighter than `VBIAS` — so the same question is open at far lower severity. No ref allocated.
3. **U3's EN sits on the unfiltered `+5V_SW`**, not post-`FB3`. DC-identical, deliberate.
4. **U3's PSRR margin rests on the pi-filter whose upstream leg is `C3` in `digital_power`.**
   Re-cut that block's caps and SPEC P8 is what breaks.
5. **TLV9062's pinout was never re-pulled for this LCSC record**; the KiCad symbol is an exact
   match and this block wires by number, so a surprise would be a symbol bug. Low, recorded.
6. **BOM row owed:** `R22` = 10 Ω generic 1 % 0603 (architecture rev 2 WO-1 item 3).

## Do not redo

- **`VBIAS` = 1.100 V, and specifically not `R8` = 23.0k / 1.000 V** — decision 19 and R-3.
- **`R22`'s placement: U4A's feedback is taken INSIDE `R22`.** Taking it on `VBIAS` puts the
  200–250 pF back inside the loop and defeats decision 16.
- **`R19` = 1.00k top / `R11` = 19.1k bottom**, and deriving `VREF_FE` from `VBIAS` rather than
  from `+3V3_A` — the tracking *is* the noise-cancellation mechanism (decision 5).
- `FB3` + `C8` and U3's input/output bulk caps — load-bearing for SPEC P8, not decoupling.
  U3's thermal pad to GND and its active-high EN tie.

## Receipt

- block `analog_power_ref` rev 3: **14 parts** (U3, U4, FB3, R8, R9, R10, R11, R19, R22,
  C8–C12), **11 nets** (5 interface, 5 local, 1 `__NOCONNECT`). Both counts unchanged from rev 2.
- Values changed: **2** (`R8` 21.0k→22.0k, `R9` 12.0k→11.0k). Refs added/removed: **none**.
- `py_compile` OK; instantiation smoke-tested (all pin lookups resolve, 0 unconnected pins,
  `R8`/`R9`/`R22` on `+3V3_A`/`VBIAS_DIV`/`GND`/`VBIAS_DRV`/`VBIAS` as intended);
  `validate-footprints.py` clean (2/2).
- Signature changed: **no**. Call site changed: **no**. Topology changed: **no**.
- status: **complete** — WO-2 items 1–4 done, nothing else in the file touched.
