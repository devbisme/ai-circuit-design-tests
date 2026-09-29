---
phase: 05_blocks/usb_bridge
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Wrote `circuits/dual_adc_usb/usb_bridge.py`: FT232HL (U6) in FT245 sync-FIFO mode +
  93LC46B config EEPROM (U7) + 12 MHz crystal (Y1), matching the work order's exact
  function signature.
- Compiles clean (`py_compile`) and instantiates cleanly under SKiDL 3.0.0 with real
  symbols/footprints: 28 parts (U6, U7, Y1, R13-R19, FB4/FB5, C25-C40 -- exact ref-count
  match to the work order's part list), 33 nets.
- No `validate-footprints.py` / `generate-footprint.py` script exists anywhere on this
  machine (checked via `find /`); manually verified all 8 distinct footprint strings used
  exist as `.kicad_mod` files under `/usr/share/kicad/footprints` (see Decisions).

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/usb_bridge.py | `usb_bridge()` SubCircuit: U6 FT232HL, U7 93LC46B, Y1 crystal, R13-R19, FB4/FB5, C25-C40 | skidl-assembler |

## Key facts for the next phase

- **Final signature (unchanged from work order):**
  `usb_bridge(vbus, v3v3_d, gnd, usb_dp, usb_dm, fifo_data, rxf_n, txe_n, rd_n, wr_n, oe_n, clk60, pwren_n)`
- `fifo_data` is an 8-bit `Bus` -- caller must pass a `Bus("FIFO_D", 8)` (or equivalently
  named/sized bus); block wires `fifo_data[0..7]` to U6 ADBUS0-7.
- Net directions for the assembler's keyword call:
  - **Inputs to this block** (driven elsewhere): `vbus`, `v3v3_d`, `gnd`, `usb_dp`/`usb_dm`
    (already ESD-clamped by usb_c_input's D1/FB1 upstream), `rd_n`, `wr_n`, `oe_n` (driven
    by fpga_core/U9).
  - **Outputs from this block** (driven here, consumed elsewhere): `rxf_n`, `txe_n`,
    `clk60` (60.000 MHz FIFO clock, feeds U9 GBIN), `pwren_n` (open-drain-style active-low
    gate, EEPROM-configured on U6 ACBUS9 -- consumed by power_analog's Q1/U3/U4 enables).
  - `fifo_data` is genuinely bidirectional (U6 ADBUS0-7 <-> U9 bank 1 I/O).
  - None of this block's nets need `.drive = POWER` set at the top level -- `vbus`/
    `v3v3_d`/`gnd` are all driven by other blocks (power_digital / usb_c_input), this
    block only consumes them.
- U6's `VCCIO` pin name aliases 3 physical pins (12/24/46) and `AGND`/`GND` alias 3/8
  physical pins respectively -- `u6["VCCIO"] += v3v3_d` etc. connects all aliased pins at
  once (confirmed working via the KiCad symbol's own pin-name reuse, verified by the
  28-part/33-net instantiation test).

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| B1 | FT232H VBUS-sense: net_plan.md calls for a divider into "U6 VBUS_SENSE", but neither the real FT232H nor the installed `Interface_USB:FT232H` KiCad symbol has any such pin | Leave R14/R15 unconnected (drop the divider) / invent a fictitious VBUS_SENSE pin / repurpose a spare ACBUS GPIO | **Repurpose ACBUS8** (unused by the sync-FIFO protocol) as a firmware-read VBUS-sense GPIO, fed by the R14/R15 10k/10k divider (nominal 2.5 V at 5.0 V VBUS, matching net_plan.md's stated nominal) | Preserves the sourced BOM's R14/R15 parts and net_plan's design intent (board-level VBUS presence sensing) without inventing hardware the part doesn't have; ACBUS8 is otherwise idle |
| B2 | FB4/FB5 assignment to VPLL vs VPHY (sourced BOM lists them as an unordered pair "VPLL / VPHY isolation ferrites") | FB4->VPHY,FB5->VPLL / FB4->VPLL,FB5->VPHY | **FB4->VPLL, FB5->VPHY** | Matches the BOM's stated listing order (VPLL first, VPHY second); electrically interchangeable (same MPN, same value) so the assignment is arbitrary but documented for traceability |
| B3 | VCCA/VCCCORE (pins 37/38, internal 1.8 V regulator outputs) | Keep as two isolated nets / tie together on one local net (`FT_VCORE_1V8`) | **Tie together** | Both are outputs of the same internal FT232H 1.8 V regulator in the FTDI reference design; tying them on one local net lets C35/C36/C38 all bypass the same effective rail while still placing 3 physically distinct caps at the 3 physical locations (2 pins + 1 bulk) |
| B4 | 8th 100 nF decoupling cap (C27-C34 covers 7 FT232H supply-input pins: VPHY, VPLL, VCCIO x3, VCCD, VREGIN) | Duplicate a VCCIO cap / assign the 8th to U7's VCC pin | **C34 -> U7 (93LC46B) VCC pin** | The 93LC46B summary explicitly states U7 "shares the usb_bridge block's C27-C34 (100 nF) per-pin decoupling group" -- this is the only unaccounted-for supply pin in the block, so it closes the C27-C34 count to exactly 8 |
| B5 | C37/C38 (4.7 uF bulk x2) and C40 (100 nF extra) placement -- FT232HL summary lists these as an undifferentiated bulk-cap allowance, not pin-assigned | Stack all bulk caps on V3V3_D only / split across V3V3_D and the 1.8 V core rail | **C37 + C39(10uF) + C40(100nF) on V3V3_D; C38(4.7uF) on FT_VCORE_1V8** | Gives the internal 1.8 V core rail (VCCA/VCCCORE) its own bulk cap in addition to the two 1 uF local caps, consistent with net_plan.md Sec.10's FT232H decoupling census calling out "VCORE x2" as a distinct decoupling target from the VCCIO/VPHY/VPLL group |
| B6 | Footprint validation tooling absent (`validate-footprints.py` not found anywhere via `find /`) | Skip validation / manually verify each footprint string against installed `.kicad_mod` files | **Manual verification** | All 8 distinct footprint strings confirmed present under `/usr/share/kicad/footprints`; also confirmed indirectly by a clean SKiDL instantiation run (Part() would raise if a footprint file were missing at netlist-generation time, though SKiDL itself doesn't validate footprints at Part()-creation time -- the `.kicad_mod` file-existence check is the authoritative one here) |

## Carried forward

- **Assumption for the assembler:** `usb_dp`/`usb_dm` passed into this block are assumed
  to already be routed through usb_c_input's FB1 (common-mode choke) and D1
  (USBLC6-2SC6 ESD clamp) upstream -- this block does not add its own ESD protection, per
  net_plan.md Sec.2 (`J1 -> FB1 -> D1 -> U6`).
  the `EE_CS`/`EE_SK`/`EE_DATA` nets between U6 and U7, `FT_VPHY`/`FT_VPLL` (ferrite
  outputs), `FT_VCORE_1V8` (VCCA/VCCCORE tie), `FT_OSCI`/`FT_OSCO` (crystal legs),
  `FT_RESET_N`, `FT_SIWU_N`/`FT_PWRSAV_N` (idle pull-up nets), and `FT_VBUS_SENSE` are
  all internal to this block (created via `Net(...)` inside the function) -- none of them
  are function parameters and the assembler does not need to wire them.
- **EEPROM firmware image is out of schematic scope**: ACBUS9=PWREN#, FT245 sync-FIFO
  mode, and ORG=x16 are all EEPROM-image configuration (FT_PROG), not something SKiDL/
  KiCad can express -- flagged here so the eventual bring-up procedure programs U7
  correctly before the board is expected to enumerate as a sync-FIFO device.
- Datasheets phase flagged X322512MSB4SI's exact load-capacitance spec as
  unconfirmed against its real datasheet; C25/C26=27pF was carried through unchanged
  from the sourced BOM (not re-derived here).

## Escalation

none

---

## Post-hoc correction (2026-09-09, pre-assembly ERC sweep)

**ERC ERROR found and fixed:** `Pin conflict on net FT_VCORE_1V8, POWER-OUT pin 38/VCCCORE
<==> POWER-OUT pin 37/VCCA (POWER-OUT connected to POWER-OUT)`.

This was not an ERC false positive. `datasheets/FT232HL_SUMMARY.md` (pins 37/38) documents
VCCA and VCCCORE as **two separate** internal 1.8 V regulator outputs — VCCA feeds the USB
PHY analog section, VCCCORE feeds the digital core. The original code shorted both onto a
single `FT_VCORE_1V8` net and hung both 1 uF caps (C35, C36) on that shared node, on the
mistaken premise that "both come off the same internal regulator".

**Fix:** split into `FT_VCCA_1V8` (C35) and `FT_VCORE_1V8` (C36) — one 1 uF per rail,
independent decoupling. No BOM change (same two caps, same values). usb_bridge now ERCs
with 0 errors.

**Why it mattered beyond ERC:** shorting two independent LDO outputs makes them fight, and
couples USB PHY switching noise directly into the core rail.
