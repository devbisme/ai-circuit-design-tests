---
phase: 05_blocks/usb_c_port
agent: skidl-block-coder
circuit: dual_adc_usb
block_id: usb_c_port
written: 2026-09-10T00:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — usb_c_port

File: `circuits/dual_adc_usb/usb_c_port.py`

## Decisions

1. **Signature unchanged:** `usb_c_port(vbus, gnd, usb_dp, usb_dm)`. Nothing renamed or added.
2. **Net directions:** `vbus` is **driven by this block** (J1 VBUS → TVS/bulk → FB1 → `vbus`);
   `gnd` consumed; `usb_dp`/`usb_dm` **bidirectional pass-through** — J1 D± and the FX2LP-side
   nets are the same nodes, with D1 (USBLC6-2SC6) shunting across them. No series R, no 1.5 k
   pull-up: the FX2LP integrates both (`net_plan.md`).
3. **Internal node `VBUS_CONN`** (connector-side, unfiltered) is local, not in the interface.
   D2 TVS, C1, C2 and D1 pin 5 sit on it; FB1 separates it from the board rail `vbus`, so
   ESD/TVS return current stays at the connector.
4. **Cap split** (work order gave 3 caps; `net_plan.md` named only C1/C2): C1 = 10 µF 0805 at
   the connector — the *entire* USB 2.0 §7.2.4.1 / P7 allowance and the only bulk cap here;
   C2 = 100 nF at the connector; C3 = 100 nF on the filtered rail. No second 10 µF added.
5. **CC1 and CC2 each get their own 5.1 k pull-down** (R1, R2) — UFP at 5 V default current,
   reversible cable, no PD. Nets named `CC1`/`CC2` verbatim. **SBU1/SBU2 → `NC`**; **shell pad
   S1 → `gnd`** directly (single-GND design, no shell RC).
6. **Symbols:** `Connector:USB_C_Receptacle_USB2.0_16P` on the confirmed
   `Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A` (pads A1…B12 + S1 all match);
   `Power_Protection:USBLC6-2SC6`; `Device:D_TVS` for SMAJ5.0A on `Diode_SMD:D_SMA` — **generic
   bidirectional symbol, real part is unidirectional, pin 1 = cathode/band wired to +5 V**
   (check silk polarity at layout); `Device:FerriteBead` on the 0603 chip-resistor land.

## Next phase must

1. Call exactly: `usb_c_port(vbus=VBUS, gnd=GND, usb_dp=USB_DP, usb_dm=USB_DM)`
2. **Set `VBUS.drive = POWER` (and `GND.drive = POWER`) at the top level.** J1's VBUS pins are
   `passive` in the symbol and FB1 is passive, so nothing here asserts drive on `VBUS`;
   without it ERC flags insufficient drive for U1/U2/FB2 downstream.
3. Do **not** add D± series resistors or a 1.5 k pull-up in `usb_controller` (Decision 2).

## Carried forward

- **FB1 headroom is thin.** BLM18AG601SN1D is rated 500 mA and carries the whole 5 V board
  draw — est. 370–450 mA full load (≈1.56 W of rails ÷ ~85 %), i.e. 75–90 % of rating, where
  impedance and DCR both degrade. Architecture's part choice, unchanged here; flagged for review.
- **§7.2.4.1 counts total VBUS bypass capacitance at the device**, not just ahead of the
  ferrite; the regulator blocks' input caps sit behind a near-zero-DC-impedance bead and add to
  the inrush budget. Architecture-level (P7); this block contributes only the 10 µF.
- Pins left `NC`: J1 A8/B8 (SBU1/SBU2) only. No decoupling assumed from the assembler.

## Receipt

- block_id `usb_c_port`; parts 10 (J1, R1, R2, D1, D2, FB1, C1, C2, C3, TP1 — refs as issued)
- nets 7 (`VBUS`, `GND`, `USB_DP`, `USB_DM` interface + `VBUS_CONN`, `CC1`, `CC2` internal)
- compile OK; instantiates cleanly in a scratch harness; footprints valid (8 checked, exit 0)
- signature changed: **no**
