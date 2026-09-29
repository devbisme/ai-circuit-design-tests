---
phase: 05_blocks/power_digital
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T02:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 block handoff — power_digital

## Decisions

1. **Final signature, unchanged from the work order:**
   `power_digital(vbus, gnd, pwr_en, v3v3_aon, v3v3, v1v2, v1v8)` — no parameter renamed.
2. **Nets this block DRIVES:** `+3V3_AON` (U1 VOUT), `+3V3` (U2 SW→L1), `+1V2` (U3 SW→L2),
   `+1V8` (U4 OUT). **Sensed only:** `VBUS` (input to U1/U2), `PWR_EN` (EN of U2/U3/U4 plus
   the mandatory pulldown). **Bidirectional:** none. `GND` is the single board ground.
3. **Cascade wired exactly as `block_diagram.md` / `TLV62568DBVR_SUMMARY.md` require:**
   U2 VIN←`VBUS`; **U3 VIN←`+3V3`, not VBUS**; U4 IN←`+3V3`. Do not re-plumb.
4. **U1 EN tied to its own VIN (`VBUS`)** — always-on rail, no gate net exists for it.
   U2/U3/U4 EN all on `PWR_EN` per `net_plan.md` line 79.
5. **Divider values used verbatim from `04_datasheets.md` #4:** R3=453k / R4=100k → 3.318V;
   R5=R7=100k → 1.200V. Not recomputed.
6. **Ref-designator role map inside my allotted range** (net_plan calls refs "indicative";
   its one explicit power_digital ref, `R6` = PWR_EN pulldown, is honoured):
   R3=453k FB top (+3V3), R4=100k FB bottom (+3V3), R5=100k FB top (+1V2),
   **R6=100k PWR_EN pulldown**, R7=100k FB bottom (+1V2), **R8 unused/spare — not placed.**
   L1=+3V3 buck inductor, L2=+1V2 buck inductor.
   C4/C5 U1 in/out 1µF, C6 10µF + C7 100nF `+3V3_AON` bulk; C8 10µF + C9 100nF U2 VIN,
   C10+C11 10µF + C12 100nF `+3V3`; C13 10µF + C14 100nF U3 VIN, C15 10µF + C16 100nF
   `+1V2`; C17/C18 1µF U4 in/out, C19 10µF + C20 100nF `+1V8`.
   **TP2=+3V3, TP3=+1V2, TP4=+1V8, TP5=+3V3_AON** — TP5 replaces net_plan's `TP15` label so
   the ref stays inside this block's range.
7. **Two 10µF on the +3V3 output (C10, C11)** — TLV62569 is the 2A rail feeding the FPGA I/O,
   the +1V2 buck and the +1V8 LDO; one 0805 X5R 10µF derates to well under 10µF at 3.3V.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/power_digital.py` | The block: 32 parts, 4 rails, 7 interface nets | Assembling `__main__.py` |

## Next phase must

1. **Emit exactly this call** (keyword form, names are the contract):
   ```python
   power_digital(vbus=VBUS, gnd=GND, pwr_en=PWR_EN,
                 v3v3_aon=V3V3_AON, v3v3=V3V3, v1v2=V1V2, v1v8=V1V8)
   ```
2. **`.drive = POWER` at top level for `VBUS` and `GND`** — this block only consumes VBUS
   (usb_c_port sources it) and GND is the universal return. `+3V3_AON` / `+3V3` / `+1V2` /
   `+1V8` are driven by real regulator `power_out` pins here — do **not** add PWR_FLAG to
   them, it would create a second driver.
3. `PWR_EN` is driven by usb_controller (U13 PA0). This block adds only R6 (100k pulldown)
   and three EN inputs. If the usb_controller block also places a PWR_EN pulldown, **drop
   theirs, not R6** — R6 is the ref `net_plan.md` names.
4. `+3V3_DRV` (FB4 ferrite off `+3V3`) is **not** in this block — whichever block owns FB4
   (adc_pair) must tap `+3V3`.

## Carried forward

- **R8 is allocated to this block but unused.** Free for the assembler/layout if a strap is
  needed; nothing in this block depends on it.
- **No 6.8pF feed-forward cap across R3** (TI's optional §8.2.2.2 improvement when R2=100k).
  Omitted deliberately: no 6.8pF part exists in `sourced_bom.md` and adding one would
  introduce an unsourced MPN. Transient response on `+3V3` is datasheet-nominal, not
  optimised — add C + MPN in a respin if load-step measurements demand it.
- **`0402WGF4533TCE` (R3, 453k) was never stock-checked** — flagged as such in
  `04_datasheets.md`; same family/vendor as every other 0402 in the BOM. Verify before order.
- **L1/L2 footprint is project-local:** `Inductor_SMD_Custom:L_FNR3015S_3.0x3.0mm`. The user
  must register `${KIPRJMOD}/footprints/Inductor_SMD_Custom.pretty` in KiCad before layout.
- **Pins left NC on purpose:** U1 pin 4 and U4 pin 4 (`NC`, no internal die connection) —
  both explicitly tied to the `NC` net, not floated.
- **Decoupling assumed provided elsewhere:** load-side 100nF-per-VCC-pin for U12/U13/U9/U10
  etc. This block gives each rail one 10µF + one 100nF at the regulator only.

## Do not redo

- The four FB-divider values and the ±rail cascade order (settled in `04_datasheets.md`).
- The custom inductor footprint (built in phase 4).
- MPN/LCSC/footprint strings — copied verbatim from `sourcing/sourced_bom.md`.

## Receipt

- Block `power_digital`, file `circuits/dual_adc_usb/power_digital.py`.
- **32 parts** placed (U1–U4, L1–L2, R3–R7, C4–C20, TP2–TP5); R8 unused.
- **11 nets** touched: 7 interface + 4 block-local (`SW_3V3`, `FB_3V3`, `SW_1V2`, `FB_1V2`).
- `py_compile` OK; `validate-footprints.py` → 11/11 valid, exit 0; instantiation smoke test
  runs clean (no ERC run here — assembler's job).
- **Signature changed: no.**
