---
phase: 05_blocks/usb_c_input
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Wrote `circuits/dual_adc_usb/usb_c_input.py`: USB-C receptacle (J1), CC1/CC2 sink
  pull-downs (R1/R2), SHIELD single-point chassis tie (R3/C2), VBUS fuse + bulk cap + TVS
  (F1/C1/D2), and D+/D- common-mode filtering + dual-line ESD clamp (FB1/D1).
- Function signature matches the work order verbatim: no change needed.
- Compiles clean (`py_compile`) and executes standalone (instantiated with 4 fresh test
  nets): 10 parts, 10 nets, correct pin counts per part (J1=17, D1=6, FB1=4, rest=2).
- Fixed the footprint library-path format (BOM's `Xxx.pretty:Name` syntax errors in SKiDL
  3.0.0 — the trailing `.pretty` must be dropped, e.g. `Resistor_SMD:R_0402_1005Metric`,
  confirmed against `circuits/dual_adc_usb/clock_gen.py`'s existing convention and by a
  local `post-write.sh` footprint-validation hook that initially failed on the
  BOM-literal form and passed after the fix).

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/usb_c_input.py | `usb_c_input` SubCircuit block | skidl-assembler (05_coding) |

## Key facts for the next phase

- **FINAL function signature (verbatim, unchanged from work order):**
  `def usb_c_input(vbus, gnd, usb_dp, usb_dm):`
- **Assembler call:** `usb_c_input(vbus=VBUS, gnd=GND, usb_dp=USB_DP, usb_dm=USB_DM)`
  using whatever net objects the assembler creates for those 4 top-level nets.
- **Net directions:**
  - `vbus` — **output** (driven): this block is the sole source of VBUS power for the
    rest of the board (post-fuse F1, post-bulk-cap C1, post-TVS-clamp D2). It is fed from
    J1's connector pins internally; nothing upstream drives it. No `.drive = POWER`
    needed at top level — F1 (feeding from `vbus_raw`, an internal net) already acts as
    the source-side element and SKiDL's ERC treats a `Part` pin as a legitimate driver;
    if the assembler's own ERC flags `vbus` as undriven (fuses/connectors are sometimes
    typed passive-only), set `vbus.drive = POWER` at the top level as a safe override.
  - `gnd` — bidirectional/shared reference, as usual.
  - `usb_dp` / `usb_dm` — **bidirectional** signal nets: this block's FB1 (choke) output
    IS the node other blocks (usb_bridge's FT232H, U6) connect to; D1 (USBLC6-2SC6) shunts
    ESD current to GND from this same node but does not isolate it. No drive override
    needed — treat as ordinary bidirectional USB2 HS lines.
- **Internal-only nets created in this block** (not visible to the assembler,
  informational only): `usbVbusRaw` (J1 VBUS pins → F1 input), `usbShield` (J1 SHIELD →
  R3‖C2), `usbDpRaw` / `usbDmRaw` (J1 D+/D- → FB1 input side).
- **D1 (USBLC6-2SC6) is a shunt ESD clamp, not a series element** — its I/O1/I/O2 pins
  land directly on `usb_dp`/`usb_dm` (the same node FB1's output side defines and the
  same node that continues to usb_bridge). Do not expect a separate "clamped" net name.
- **FB1 (Device:Filter_EMI_CommonMode) pin pairing** confirmed from the installed KiCad
  symbol: pins 1↔2 are one independent winding, pins 3↔4 are the other (NOT 1↔3/2↔4).
  This block wired winding 1-2 to D+ (`usbDpRaw`→pin1, pin2→`usb_dp`) and winding 3-4 to
  D- (`usbDmRaw`→pin3, pin4→`usb_dm`).

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| B1 | Footprint string format | BOM-literal `Library.pretty:Name` / SKiDL-style `Library:Name` (no `.pretty`) | **`Library:Name`** | SKiDL 3.0.0's footprint search on this system resolves the bare library name (`Resistor_SMD`, not `Resistor_SMD.pretty`); confirmed both by a local validation hook rejecting the `.pretty` form and by matching the existing `clock_gen.py` block's convention |
| B2 | D1 (USBLC6-2SC6) placement relative to FB1 | D1 between J1 and FB1 (clamps raw, pre-choke lines) / D1 after FB1 on the protected node (clamps `usb_dp`/`usb_dm` directly) | **After FB1, on `usb_dp`/`usb_dm`** | Matches net_plan.md's stated signal order "J1 → FB1 → D1 → U6" and the USBLC6 datasheet summary's own placement note ("place tight to J1... for effective ESD clamping" refers to trace-length proximity, not topological position before the choke); clamping the final protected node is the standard, more effective ESD topology |
| B3 | `vbus` net drive typing | Rely on F1/C1 pins as implicit source / explicitly set `.drive = POWER` in this block | **Left undriven here, documented for assembler** | This block's function only receives `vbus` as a parameter (it doesn't create the top-level Net object), so `.drive` must be set where the Net is instantiated (assembler) if ERC needs it — flagged under Key facts rather than guessed here |

## Carried forward

- **J1 mechanical verification unresolved** (carried from datasheets/sourcing): XKB
  U262-16XN-4BVC11 has no confirmed mechanical drawing in this project — verify the
  physical part against `Connector_USB:USB_C_Receptacle_XKB_U262-16XN-4BVC11` before
  layout. Not something this coding block can resolve.
- **Assumed FB1 pin-to-footprint pairing** (pin1↔pin2, pin3↔pin4 per winding) matches the
  generic `Device:Filter_EMI_CommonMode` symbol geometry; the DLW21SN900HQ2L's real
  footprint pin numbering was not independently cross-checked against this symbol's
  numbering (sourcing/datasheets phases did not obtain a DLW21SN900HQ2L pin-map PDF) —
  low risk (standard 0805USB 4-pin choke footprint), but flagged for layout review.
- **No decoupling caps in this block** — correct and intentional: J1/F1/D1/D2/FB1/R1-R3
  are all passive, none has a VCC pin. The next block up the VBUS chain (power_digital)
  is where the first IC decoupling (U1 AP7361C-33E) belongs.
- **`validate-footprints.py` script named in the coder's instructions does not exist in
  this project** (`.claude/scripts/` is absent here) — footprint validation was instead
  performed via the project's own PostToolUse `post-write.sh` hook (which does the same
  library/footprint existence check and caught the `.pretty` suffix issue) plus a manual
  `find` against `/usr/share/kicad/footprints` confirming all 10 footprint files exist.

## Do not redo

- Parts/MPNs/footprints for J1, F1, D1, D2, FB1, R1, R2, R3, C1, C2 are settled per
  `sourcing/sourced_bom.md` Block 1 (lines 34-42) — used verbatim in this block, including
  the sourcing-phase corrections (J1 suffix `U262-16XN-4BVC11`, D2 SOD-323 package, C2
  moved to 1808 case size).
- R1/R2 = 5.1 kΩ ±1% (fixed by USB-C sink spec) and C1 ≤10 µF total on VBUS (USB inrush
  limit) — both binding constraints from the work order — honored exactly (single 10 µF
  C1, no additional VBUS bulk caps added).

## Escalation

none
