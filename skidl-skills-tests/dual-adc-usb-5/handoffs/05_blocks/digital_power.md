---
phase: 05_blocks/digital_power
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-20T23:10:00Z
status: complete
revision: 2
next_phase: 05_coding
---

# Block handoff — digital_power

**Revision 2 executes architecture rev 2's WO-2 and nothing else.** `status` moves
`partial` -> **`complete`**: both rev-1 blockers are closed at the source. Q1 is gone —
`U9` = AP2161WG-7 (active-low, GND-referenced EN) replaces it, so SPEC P4 is met in fact,
not claimed; U1's VFB is primary-sourced at 591/600/609 mV, so the 45.3 k/10.0 k divider
is confirmed at 3.318 V with **zero value change**. Nothing else in the file moved.

## Decisions

1. **Final signature, unchanged:**
   `digital_power(v5_in, v5_sw, pwren_n, v3v3_d, v3v3_adcd, v1v2_d, gnd)`.
2. **`U9` = `Part('Power_Management', 'AP2161W', ref='U9', value='AP2161WG-7',
   footprint='Package_TO_SOT_SMD:SOT-23-5')`, wired by pin NUMBER** — the symbol names
   pins `~{EN}` / `~{FLG}` with KiCad overbar markup and name lookup on those is fragile.
   Map as built: 5 = IN -> `+5V_IN`, 1 = OUT -> `+5V_SW`, 2 = GND -> `GND`,
   4 = EN# -> `PWREN_N`, 3 = FLG -> `NC`.
3. **`R3` deleted** (the 100 k gate pull-up). `usb_bridge`'s `R_pwren` (10 k to 3V3) holds
   EN# high = OFF at plug-in and through FT232H reset. **No pull-up on `PWREN_N` exists in
   this block any more** — do not re-add one.
4. **`R6` kept, pad and value unchanged** (0 R DNP, `PWREN_N` -> `GND`); its comment now
   says what it does to U9: populating it pulls EN# LOW = switch permanently ON, which is
   the `design_risks.md` R-9 bring-up escape.
5. **`R4` = 45.3 k / `R5` = 10.0 k unchanged, now documented as confirmed.** The module
   docstring's "GATE DRIVE DEFECT" block and the VFB caveat are **deleted** and replaced by
   the confirmed numbers, so the file no longer reads as a broken-board warning.
6. **Nets driven / sensed:** drives `+5V_SW` (U9's OUT, a `power_out` pin — see below),
   `+3V3_D` (U1+L1), `+3V3_ADCD` (FB2), `+1V2_D` (U2). Consumes only `+5V_IN`. Senses only
   `PWREN_N` (U9's EN# input plus R6's DNP pad).
7. Rev-1 decisions 2, 4, 6, 7, 8 (R20/R21 allocation, U2 divider, self-sequencing, U2 by
   pin number, C3–C7 allocation) stand verbatim and were not touched.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/digital_power.py` | The `digital_power` SubCircuit | Assembling `__main__.py` |

## Next phase must

1. Emit exactly this call — **unchanged from rev 1**:
   ```python
   digital_power(v5_in=V5V_IN, v5_sw=V5V_SW, pwren_n=PWREN_N, v3v3_d=V3V3_D,
                 v3v3_adcd=V3V3_ADCD, v1v2_d=V1V2_D, gnd=GND, tag='digital_power')
   ```
2. **`+5V_IN` still needs `.drive = POWER` at the top level** (consumed only here), and
   `GND` likewise. **`+5V_SW` probably no longer does**: it is now fed by U9 pin 1, a real
   `power_out` pin, where rev 1 fed it from a FET drain (passive). `+3V3_D`, `+3V3_ADCD`,
   `+1V2_D` are still driven through passive elements (inductor, ferrite, LDO out) — add
   `.drive = POWER` at the top level if ERC asks, never by editing this block.
3. No local net is an interface net — `BUCK_LX`, `V3V3D_FB`, `V1V2D_FB`, `LED_PWR_A` must
   not be created or passed by the assembler.

## Carried forward

1. **U9 pin 3 (FLG) is intentionally `NC`** — open-drain fault flag, no consumer on this
   board. It joins U2 pin 5 (DNC) on `__NOCONNECT`; both are deliberate, not omissions.
2. **`R6` must stay a DNP pad** (R-9). Its electrical meaning is the same as rev 1's —
   low = on — but it now acts on an IC enable, not a FET gate.
3. **PWREN# must be enabled on ACBUS8 in the FT232H EEPROM image** (U8, owned by
   `usb_bridge`) or U9 never turns on and the board looks dead. R-9; unchanged, and now the
   single most likely bring-up surprise. `R6` is the escape hatch.
4. **No `+3V3_D` HF cap at U1's input, and no HF cap on `+1V2_D`/`+3V3_ADCD`** — the 5-cap
   budget went to bulk. `fpga_core` (C23–C40) and `adc_dual` (C41–C55) own local HF
   decoupling on those rails.
5. **BOM rows owed are architecture WO-1's, not new**: −Q1, +U9 (C176957), −R3, +R20/R21,
   C3–C7 mix = 4 × 10 µF 0805 + 1 × 100 nF 0402.
6. Rev-1 gap 5 (no inrush/slew control on the switch) is **closed by the part itself** —
   U9 has a 0.6 ms controlled rise, ≈167 mA into the ~20 µF behind it.

## Do not redo

- **`R4`/`R5` = 45.3 k/10.0 k** and **`R20`/`R21` = 11.8 k/10.0 k** — both dividers are now
  verified against primary sources (architecture decisions 15 and handoff-04 decision 8).
- **U9's EN polarity and current-limit bracket.** `AP2171WG-7` is pin-identical with an
  **active-HIGH** enable and silently re-breaks SPEC P4; a 500 mA-class switch fails the
  485 mA worst-case load. U9 is not freely substitutable the way Q1 was listed in rev 1.
- **The gate-drive arithmetic that killed Q1** — arithmetic on published thresholds. Do not
  re-open it with a different P-FET.
- The topology (architecture decision 9), U2's thermal pad to GND and its DNC left floating.

## Receipt

- block: `digital_power`; parts: **17** (18 − R3 − Q1 + U9), exactly the WO-2 count.
- nets touched: **12** (7 interface, 4 local, 1 `__NOCONNECT` carrying U9.FLG + U2.DNC).
- compile OK (`py_compile`); instantiation smoke-tested with both blocks in one circuit,
  all pin lookups resolve; footprint strings validated (`validate-footprints.py`, clean).
- signature changed: **no**. Call site changed: **no**.
- status: **complete** — rev-1 blockers 1 (Q1 gate drive) and 2 (U1 VFB) are both closed.
