---
phase: 05_blocks/usb_c_input
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - usb_c_input

## Decisions
1. Signature unchanged: `usb_c_input(v5, usb_dp, usb_dm, gnd)`.
2. Drives `v5` (+5V): enters through F501 (passive), so the block sets `v5.drive = POWER` and adds `#FLG501` PWR_FLAG on it. Bidirectional: `usb_dp`, `usb_dm`. Consumes `gnd`.
3. Local nets: `VBUS` (J501 A4/A9/B4/B9, U501.5, D501.1, C501, F501.1), `CC1`, `CC2` (R501/R502 5.1k Rd to GND).
4. J501: D+ = A6+B6, D- = A7+B7 (both orientations tied); GND A1/A12/B1/B12 + shield `SH` (SHIELD) -> GND (rev 2).
5. U501 USBLC6: I/O1 pins 1&6 = D+, I/O2 pins 3&4 = D-, VBUS 5, GND 2.
6. D501 SMF5.0A uses symbol `Device:D_TVS` (bidirectional symbol, pins A1/A2): pin 1 -> VBUS (footprint pad 1 = cathode/band on SOD-123F), pin 2 -> GND.

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.
- Rev 2: local `VBUS` now `.drive = POWER` + `#FLG502` PWR_FLAG (fixes `#PWR` power_pin_not_driven / DS:USBLC6 U501.5). J501 shield connected as pin `SH` (SKiDL symbol pin number; name SHIELD) to GND -- old `'S1'` matched nothing.

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/usb_c_input.py` | block |

## Next phase must
- Call: `usb_c_input(v5=V5, usb_dp=USB_DP, usb_dm=USB_DM, gnd=GND, tag='usb_c_input')` with nets `+5V`, `USB_DP`, `USB_DM`, `GND`.
- `+5V` needs no top-level drive (block drives/flags it). `GND` drive/flag is the assembler's.

## Carried forward
- J501 SBU1 (A8) / SBU2 (B8) = NC intentionally.
- No VBUS bulk cap beyond C501 1 uF (VBUS-domain budget <= 10 uF total, net plan).
- SMF5.0A VRWM 5.0 V < VBUS max 5.25 V: leakage at high VBUS (librarian note).
- 90 ohm diff routing of USB_DP/DM, U501 at the connector (layout).

## Do not redo
- MPNs/footprints verbatim from sourced_bom.csv.

## Receipt
usb_c_input (rev 2): 7 parts (+2 PWR_FLAGs #FLG501/#FLG502), 7 nets (VBUS, CC1, CC2, +5V, USB_DP, USB_DM, GND); compile OK; footprints from BOM; signature changed: no.
