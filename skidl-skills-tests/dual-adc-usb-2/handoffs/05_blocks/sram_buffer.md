---
phase: 05_blocks/sram_buffer
status: complete
next_phase: 05_coding
circuit_name: dual_adc_usb
revision: 1
date: 2026-09-08
---

## Receipt

- Wrote `circuits/dual_adc_usb/sram_buffer.py`, a single `@subcircuit` implementing the
  512 kB (256K x 16, 10 ns) async CMOS capture SRAM (U8, IS61WV25616BLL-10TLI) plus its
  6 decoupling caps (C41-C46), per the work order's exact function signature.
- Used the project-local `[GEN]` symbol (`lib/dual_adc_usb.kicad_sym`,
  `IS61WV25616BLL-10TLI`, 44 pins) exactly as instructed -- did not regenerate or edit it.
- Verified all pin names against the loaded symbol directly (not just the datasheet
  summary): `A0`-`A17`, `I/O0`-`I/O15`, `CE#`, `WE#`, `OE#`, `LB#`, `UB#`, two `VDD`
  pins (11, 33), two `GND` pins (12, 34), `NC` (pin 28).
- File compiles standalone and instantiates cleanly with real `Bus(18)`/`Bus(16)` test
  nets (7 parts, all 44 SRAM pins present); footprint validator passes 7/7.

## Artifacts

| Path | What it contains | Who reads it next |
|------|------------------|--------------------|
| circuits/dual_adc_usb/sram_buffer.py | `sram_buffer()` SubCircuit: U8 + C41-C46 | skidl-assembler |

## Key facts for the next phase

- **FINAL function signature (unchanged from work order):**
  `def sram_buffer(v3v3_d, gnd, addr, data, ce_n, oe_n, we_n, ub_n, lb_n):`
  Call it with keyword args matching these exact parameter names.
- **Net directionality for the assembler:**
  - `v3v3_d` (V3V3_D) -- input, power. Consumed only; the assembler/power_digital block
    must set `.drive = POWER` on this net at the top level (this block does not).
  - `gnd` (GND) -- input, power. Same -- `.drive = POWER` set elsewhere.
  - `addr` -- input, 18-bit `Bus`. Must be passed as a SKiDL `Bus` object with >= 18
    lines; `addr[0..17]` map directly to SRAM `A0`-`A17`. Driven by fpga_core (U9).
  - `data` -- bidirectional, 16-bit `Bus`. `data[0..15]` map to SRAM `I/O0`-`I/O15`.
    Driven by fpga_core on writes, by this SRAM on reads.
  - `ce_n`, `oe_n`, `we_n`, `ub_n`, `lb_n` -- inputs, active-LOW single nets, each
    mapped directly (`CE#`, `OE#`, `WE#`, `UB#`, `LB#`). All five are driven externally
    by fpga_core (U9) per net_plan.md section 6 -- this block does not drive or tie
    any of them internally.
- **Judgement call:** `SRAM_UB_N`/`SRAM_LB_N` are passed straight through as external
  inputs (not tied low locally), because net_plan.md section 6 shows the FPGA driving
  them as dedicated control nets, implying active byte-lane control by the capture
  state machine rather than a fixed 16-bit-wide tie-off. If fpga_core in fact ties both
  permanently low, that is equivalent and requires no change here.
- Part count: 7 (U8 + C41, C42, C43, C44, C45, C46). Net count touched: 7 external
  (v3v3_d, gnd, ce_n, oe_n, we_n, ub_n, lb_n) + 2 buses (18 + 16 lines) = 41 external
  connections total, plus internal decoupling nets (none named -- caps go straight to
  v3v3_d/gnd).

## Decisions

| # | Decision | Options considered | Chosen | Why |
|---|---|---|---|---|
| B1 | Decoupling cap ref usage | Rename to `C_DECOUP_U8` per generic ERC-rule convention / keep sourced BOM's fixed refs C41-C46 | **Keep C41-C46** | Work order and sourced_bom.md already fixed these exact ref designators/values (4x100nF + 10uF + 1uF); renaming would break the sourcing handoff's part identity. Rule "use ref designators from the work order — never invent your own" takes priority over the generic naming convention. |
| B2 | C41-C44 placement grouping | 1 cap per VDD/GND pin-pair region (2 total) / 2 caps per region (4 total, matches BOM qty) | **2 per region (C41,C42 at pins 11/12; C43,C44 at pins 33/34)** | Sourced BOM already allocates exactly 4x100nF as two pairs (C41,C42 / C43,C44); matches the datasheet summary's "4x100nF, one per VDD/GND pair region" note read as 2 redundant caps per region for a part with 2 separate VDD/GND pin locations. Electrically equivalent regardless of exact grouping since all VDD pins share one net. |
| B3 | UB#/LB# tie-off vs. pass-through | Tie both permanently LOW inside this block (fixed 16-bit-wide mode, per datasheet summary's suggestion) / pass through as external inputs driven by FPGA | **Pass through** | net_plan.md section 6 explicitly lists `SRAM_UB_N`/`SRAM_LB_N` as FPGA-driven control nets (U9 -> U8), and the work order's function signature carries `ub_n`/`lb_n` as parameters -- tying them locally would contradict both the net plan and the given signature. |
| B4 | Duplicate-named VDD/GND pins | Connect each of the 2 VDD and 2 GND pins individually by number / use `u8['VDD'] +=` and `u8['GND'] +=` (SKiDL returns a `NetPinList` for same-named pins, connecting both at once) | **Use name-based `+=` on both pins at once** | Verified in a live SKiDL 3.0.0 session that `u8['VDD']` returns both pin 11 and pin 33 as a `NetPinList`; a single `+=` connects both cleanly, same for `GND` (pins 12, 34). Simpler and equally correct. |

## Carried forward

- **NC pin:** pin 28 has no function per the ISSI datasheet pin table (confirmed also
  in the generated symbol) -- tied to `NC` intentionally (`u8['NC'] += NC`).
- **Decoupling provided by this block, not assumed from elsewhere:** all 6 caps
  (C41-C46) are instantiated here, not left for the assembler.
- **Assumption about neighbouring blocks:** `v3v3_d` and `gnd` arrive already declared
  and driven (`.drive = POWER`) by whichever block/assembler code creates the top-level
  nets (per net_plan.md, power_digital's U1 output feeds V3V3_D) -- this block only
  consumes them, does not create or drive them.
- **Assumption about fpga_core:** it drives `addr`/`data`/`ce_n`/`oe_n`/`we_n`/`ub_n`/
  `lb_n` as a memory-mapped peripheral within the SRAM's 10 ns access-time budget (no
  timing logic exists in this block since the SRAM itself has no clock pin).

## Do not redo

- **Part/footprint, settled upstream (sourcing/sourced_bom.md, Block 7):**
  U8 = IS61WV25616BLL-10TLI, footprint `Package_SO:TSOP-II-44_10.16x18.41mm_P0.8mm`
  (`.pretty` suffix dropped per the known SKiDL 3.0.0 gotcha).
  C41,C42 = 100nF 0402 (`Capacitor_SMD:C_0402_1005Metric`).
  C43,C44 = 100nF 0402 (`Capacitor_SMD:C_0402_1005Metric`).
  C45 = 10uF 0805 (`Capacitor_SMD:C_0805_2012Metric`).
  C46 = 1uF 0603 (`Capacitor_SMD:C_0603_1608Metric`).
- **Symbol, already generated and verified (do not regenerate):**
  `lib/dual_adc_usb.kicad_sym`, symbol name `IS61WV25616BLL-10TLI`, 44 pins.

## Escalation

none
