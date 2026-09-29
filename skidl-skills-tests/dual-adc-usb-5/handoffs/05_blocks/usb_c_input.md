---
phase: 05_blocks/usb_c_input
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-20T21:10:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — usb_c_input

## Decisions

1. **Final signature, unchanged from the work order:**
   `usb_c_input(v5_in, usb_dp, usb_dm, gnd)` — no parameter renamed, no extra argument.
2. **`VBUS_RAW` and `SHIELD` are LOCAL nets created inside the block**, not parameters.
   `net_plan.md` lists `VBUS_RAW` in its inter-block table, but every ref on it (J1, D2,
   D1.VBUS, FB1.1) lives in this block, so passing it in would only add a dangling
   top-level net. **The assembler must not pass `VBUS_RAW`.**
3. **Nets driven / sensed:** this block **drives** `+5V_IN` (board power entry, via FB1
   from the connector) and terminates `GND`. `USB_DP` / `USB_DM` are **bidirectional
   pass-throughs** — J1's pads and D1's clamp nodes sit on them; `usb_bridge` owns the
   other end. No net is sense-only.
4. **Reversibility wired as instructed:** A6+B6 → `USB_DP`, A7+B7 → `USB_DM`, all four VBUS
   pads → `VBUS_RAW`, all four GND pads → `GND` (handoff 04's J1 summary).
5. **C1 = C2 = 4.7 uF (9.4 uF total VBUS bulk)**, honouring SPEC P4's 10 uF ceiling and the
   sourced BOM's explicit "do not simply double up two 10 uF parts". **BOM consequence:**
   C1/C2's MPN moves off CL21A106KAYNNNE (10 uF) to a 4.7 uF part in the same Samsung CL21A
   0805 X5R family (e.g. CL21A475KAQNNNE) — same footprint, no re-sourcing risk, but the
   BOM line must be corrected.
6. **D1 (USBLC6-2SC6) wired by pin NUMBER, not name** — the symbol's pin names are `I/O1`
   and `I/O2`, and SKiDL treats the `/` as a regex character. Pins 1+6 are one internal
   node (I/O1) and 3+4 the other (I/O2), so both pads of each pair land on the same data
   net; the part adds no series element. Pin 5 (VBUS) references `VBUS_RAW`, deliberately
   the connector side of FB1, so D1 and D2 clamp to the same node.
7. **SHIELD is RC-terminated (C15 1 nF || R12 1 MOhm), not bonded to GND.** Architecture
   decision 12's single-GND rule is about AGND/DGND, not the connector shell.
8. **J1 A8/B8 (SBU1/SBU2) are explicitly `NC`** — USB 2.0 only, no alt-mode.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/usb_c_input.py` | The `usb_c_input` SubCircuit | Assembling `__main__.py` |

## Next phase must

1. Emit exactly this call (keyword args, plus a stable tag):
   ```python
   usb_c_input(v5_in=V5V_IN, usb_dp=USB_DP, usb_dm=USB_DM, gnd=GND, tag='usb_c_input')
   ```
2. **`+5V_IN` needs `.drive = POWER` at the top level** — this block feeds it from a
   connector pad, which SKiDL sees as a passive pin, so without the flag every consumer
   (Q1, U7.VREGIN) raises "insufficient drive". Same for `GND`.
3. **Do not create or pass `VBUS_RAW`, `SHIELD`, `CC1` or `CC2`** — all four are internal.
4. `USB_DP` / `USB_DM` are also driven from `usb_bridge`; no `.drive` is needed on them.

## Carried forward

- **C1/C2 BOM value change** (decision 5) — sourcing must restate the MPN at 4.7 uF, or
  explicitly bless populating one 10 uF and DNP'ing the other. Either way the board must
  not ship with 20 uF on VBUS.
- **D2's footprint is still the sourcing phase's "closest stocked match"**
  (`Diode_SMD:D_SOD-123F` for a SOD-123FL part) — unchanged here, still owed a lead-form
  check before layout (sourcing decision, carried since phase 3).
- **D1's clamp reference is upstream of FB1 by choice.** If layout instead wants the clamp
  on the filtered rail, move pin 5 to `v5_in`; the ESD path then runs through the ferrite,
  which is worse. Documented so nobody "fixes" it silently.
- No CC/PD logic exists anywhere on the board. If a later revision wants PD, CC1/CC2 must
  be re-exposed through the signature — they are not today.

## Do not redo

- The 5.1 kOhm CC pulldown scheme and USB-2.0-only signalling (architecture "Do not redo").
- The A/B-row tie-together for D+/D- and VBUS/GND (handoff 04's J1 summary, pad-verified
  against the footprint file).
- The J1 symbol/footprint pair — `dual_adc_usb:TYPE-C-16PIN-2MD-073` +
  `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12`, confirmed pin-for-pin in phase 4.

## Receipt

- block: `usb_c_input`; parts: **10** (J1, R1, R2, R12, D1, D2, FB1, C1, C2, C15 — the exact
  work-order set, none added, none dropped).
- nets touched: **9** (4 interface: `+5V_IN`, `USB_DP`, `USB_DM`, `GND`; 4 local:
  `VBUS_RAW`, `SHIELD`, `CC1`, `CC2`; 1 `__NOCONNECT`).
- compile OK (`py_compile`); instantiation smoke-tested with dummy nets, all pin lookups
  resolve; footprints valid (14/14 strings checked against the KiCad libraries).
- signature changed: **no**.
- status: complete
