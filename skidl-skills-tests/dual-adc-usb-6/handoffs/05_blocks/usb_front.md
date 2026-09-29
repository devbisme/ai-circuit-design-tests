---
phase: 05_blocks/usb_front
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-22T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---

# Phase 5 block handoff — `usb_front`

## Decisions

1. **Signature as written — unchanged from the work order, no keyword renamed:**
   `usb_front(vbus, vbus_sw, usb_dp, usb_dm, gnd)`.
2. **Net direction:** `vbus_sw` is **driven** by this block (U2.VOUT is a `power_out`
   pin — a real SKiDL driver). `vbus` is **sensed only**: J1's VBUS pins are `passive`
   in `Connector:USB_C_Receptacle_USB2.0_16P`, so nothing on this net drives it as far as
   ERC is concerned. `usb_dp`/`usb_dm` are **bidirectional** (J1 bidir pins + U1 passive
   clamps; the actual driver is U50 in `usb_bridge`). `gnd` is sensed only.
3. **CC1 and CC2 get one 5.1 kΩ pulldown each (R1, R2), never bridged.** Per architecture
   decision #8 — total draw 293 mA (381 mA at +30 %) is under the 450 mA default-source
   ceiling, so no CC sensing and no PD controller. Bridging CC1/CC2 would make the board
   look like a powered cable to a PD source.
4. **U2.ON is pulled HIGH to raw VBUS through R3 (100 kΩ)** — the TPS22919's control is
   active-high, so the switch self-enables on host attach and its internal fixed soft-start
   limits inrush. `PWR_EN` is an internal net, not exposed on the interface.
5. **J1 shell (S1) tied directly to GND.** `net_plan.md` is silent on the shield; the board
   is a single plane by architecture decision (risk R6), so the usual cap+resistor hybrid
   shell tie has nothing to isolate against. Assumption recorded, easy to change.
6. **SBU1 (A8), SBU2 (B8), U2 pin 4 (NC) and U2 QOD (pin 5) are explicit `NC`.** See
   Carried forward for the QOD reasoning.
7. **J1 now uses a project-local, manufacturer-exact footprint** (rev 2):
   `ProjectLocal:USB_C_Receptacle_TYPE-C-16P-2MD073`, built dimension-by-dimension from
   the SHOU HAN RECOMMENDED PCB LAYOUT (`datasheets/TYPE-C-16PIN-2MD-073.pdf` p.6). This
   is the only change in rev 2; no net, part or signature changed.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/usb_front.py` | The `@SubCircuit usb_front` block — J1, U1, U2, R1–R3, C1–C3 | Assembling the circuit |
| `footprints/ProjectLocal.pretty/USB_C_Receptacle_TYPE-C-16P-2MD073.kicad_mod` | J1 land pattern: 16 SMD contacts + 4 plated shield slots (S1) + 2 NPTH Ø0.65 | Layout / fab review |

## Next phase must

1. **Call it exactly like this** (keyword form, all five are required):

   ```python
   usb_front(vbus=VBUS, vbus_sw=VBUS_SW, usb_dp=USB_DP, usb_dm=USB_DM,
             gnd=GND, tag='usb_front')
   ```

2. **`VBUS` needs `.drive = POWER` at the top level.** This block only consumes it — J1's
   VBUS pins are `passive`, so without the flag ERC reports insufficient drive on the net
   that feeds U2.IN, U1 pin 5 and R3. `GND` likewise. **`VBUS_SW` does not need it** —
   U2.VOUT is a `power_out` pin and drives the net properly.
3. **Do not add capacitance to `VBUS` at the top level.** Architecture decision #11 caps
   raw-VBUS capacitance at 10 µF so the switch absorbs inrush rather than the cable. This
   block places only C1 (100 nF) there.
4. `USB_DP`/`USB_DM` are handed straight to `usb_bridge` (U50.D+/D−). No series resistors
   are placed here and none should be added — USBLC6-2SC6 is a through-path clamp.

## Carried forward

- **U2 (TPS22919DCKR) has no primary-source PDF** — phase 4 could not obtain one
  (`TPS22919DCKR_SUMMARY.md`). Active-high `ON` polarity rests on two independent JLC
  fields (parametric "Control Input Logic: Active High" + the EasyEDA pin name `ON`, not
  `ON#`). If that is ever disproven, the only change needed is moving R3 from VBUS to GND.
- **QOD (pin 5) left `NC`** — leaving it open disables the internal output-discharge FET.
  With 44 µF of downstream bulk a quick discharge is undesirable anyway. This choice is
  **not datasheet-verified** for the same reason as above.
- **C2/C3 placement is a layout dependency for the `power` block.** They are this block's
  VBUS_SW bulk (2 × 22 µF) *and* the only bulk input capacitance U3/U4 have — the `power`
  block places only 100 nF local at each buck VIN pin. C2/C3 must be placed adjacent to
  the U3/U4 VIN pins, not next to U2, or add dedicated buck input bulk. Flagged in both
  block handoffs.
- **J1 footprint: RESOLVED in rev 2.** The pad-by-pad diff was done against the drawing
  (p.6, extracted as vector geometry and scaled off the 0.50 mm contact pitch / 8.64 mm
  slot span; every derived value reproduces a dimensioned callout to ≤0.02 mm). Result:
  the generic HCTL pattern is right in X everywhere (contacts ±0.25/±0.75/±1.25/±1.75/
  ±2.4/±3.2, NPTH Ø0.65 at ±2.89, slots at ±4.32) and wrong in exactly two places —
  (a) **lower shield slot 0.6 × 1.2 mm where SHOU HAN needs 0.6 × 1.4 mm** (pad 1.6 → 1.8);
  the rear mounting tabs would not enter the board. (b) contact pads 1.3 mm long vs the
  1.15 mm the manufacturer recommends. Both are fixed in the new footprint. Note for the
  record: the earlier note in `TYPE-C-16PIN-2MD-073_SUMMARY.md` calling the mounting
  features "round holes Ø1.70/Ø1.80/Ø1.40" misread the drawing — 1.70/1.40 are *slot
  lengths* of 0.60-wide oval, plated slots; only the Ø0.65 locating holes are round/NPTH.
- **J1 land pattern as built** (origin = body centre, KiCad top view, +Y toward the
  connector opening; body 8.94 × 7.35 mm):

  | Feature | X (mm) | Y (mm) | Size | Drill |
  |---|---|---|---|---|
  | Contacts A1/B12, A4/B9, A9/B4, A12/B1 | ∓3.2, ∓2.4 | −3.67 | 0.60 × 1.15 | — |
  | Contacts B8, A5, B7, A6, A7, B6, A8, B5 | ±1.75, ±1.25, ±0.75, ±0.25 | −3.67 | 0.30 × 1.15 | — |
  | Shield slot S1 (front pair) | ±4.32 | −3.105 | 1.0 × 2.1 | oval 0.6 × 1.7 |
  | Shield slot S1 (rear pair) | ±4.32 | +1.075 | 1.0 × 1.8 | oval 0.6 × 1.4 |
  | Locating hole (NPTH) | ±2.89 | −2.605 | Ø0.65 | Ø0.65 |

- **Footprint features that are documented, not verified:** solder-paste apertures are
  1:1 with the copper pads (drawing gives no stencil recommendation), the plated slots
  carry no thermal-relief/heatsink property, and the silkscreen/courtyard were derived
  from the 8.94 × 7.35 mm body views (p.6) rather than a dimensioned keep-out. The drawing
  gives no recommended stencil, no mask-expansion and no board-edge/overhang dimension —
  if the receptacle is meant to overhang a board edge, layout must set that from the
  3.16 mm-high side view, not from this footprint.
- **VIN headroom is tight downstream.** Architecture's worst-case VBUS droop is 4.4 V and
  the AP62200TWU-7 bucks need ≥ 4.2 V, so the drop across U2 (89 mΩ × ~293 mA ≈ 26 mV)
  plus cable/connector IR eats into a 0.2 V margin. Not this block's decision to reopen,
  but it is the reason C2/C3 placement matters.

## Do not redo

- Architecture decision #8 (plain CC pulldowns, no current sensing) and #11 (soft-start
  switch, ≤10 µF raw VBUS, ~47 µF downstream).
- The USBLC6-2SC6 pin-pair mapping — pins 1/6 are one internal node (I/O1) and 3/4 are the
  other (I/O2); the KiCad symbol's duplicate pin names confirm it.
- Part selection and footprint strings — all taken verbatim from `sourcing/sourced_bom.md`,
  **except J1's**, which is now the project-local footprint (see Decisions #7).
- The J1 land-pattern derivation. Every number in the new `.kicad_mod` is traceable to a
  dimension on p.6; the geometry is recorded in Carried forward.

## Receipt

- block_id: `usb_front`; parts: **9** (J1, U1, U2, R1, R2, R3, C1, C2, C3) — every ref in
  the work order placed, none invented.
- nets: **8** (5 interface + 3 internal: `USB_CC1`, `USB_CC2`, `PWR_EN`).
- `python -m py_compile`: **OK**. Instantiation smoke test with real symbol libraries: OK.
- J1 footprint pads: **22** — 16 SMD contacts (all 16 symbol pin numbers A1…B12 covered,
  stacked where the receptacle ties A/B rows), 4 `S1` plated oval slots, 2 unnamed NPTH.
- Full circuit re-run after the footprint change: **0 ERC errors**, 2 known benign
  "insufficient drive" warnings on `LDO_ADC_IN`/`LDO_AMP_IN`. `validate-footprints.py`:
  exit 0, 63 footprints/9 files — *green, but the check only resolves library paths; the
  package match was established by reading the drawing, not by that script.*
- signature changed: **no**.
