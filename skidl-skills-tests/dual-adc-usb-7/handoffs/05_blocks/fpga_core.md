---
phase: 05_blocks/fpga_core
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-23T19:40:00Z
status: complete
revision: 4
next_phase: 05_coding
---

# Phase 5 handoff — block `fpga_core`

## Decisions

1. **Final signature, as written — matches architecture rev.3 verbatim, no adjustment:**
   `fpga_core(clk_fpga, da, db, dva, sen, sclk, sdata, sel, fifo_d, rxf_n, txe_n, rd_n, wr_n, oe_n, fifo_clk60, p1v2, p1v8, p3v3d, gnd)`
   Changes vs rev.1: `ovra`, `ovrb`, `siwu_n` **removed**; `p1v8` **added**.
2. **Driven by this block:** `sen`, `sclk`, `sdata`, `sel`, `rd_n`, `wr_n`, `oe_n`.
   **Sensed only:** `clk_fpga`, `da[*]`, `db[*]`, `dva`, `rxf_n`, `txe_n`, `fifo_clk60`,
   `p1v2`, `p1v8`, `p3v3d`, `gnd`. **Bidirectional:** `fifo_d[*]`.
   `da`/`db` are 12-bit `Bus`es; `fifo_d` is an 8-bit `Bus`.
3. **U5 pin 12 → `p1v8`, wired BY PIN NUMBER against the symbol's label.**
   `symbols/dual_adc_usb.kicad_sym` names pin 12 `VCCX_VCCO0`; Gowin UG803 p.5/17 names it
   **VCCIO3, 1.71–1.89 V, the PSRAM bank supply**, an independent rail. The symbol file was
   **not** edited — the code comment states the defect at the connection. **Pins 64/67/78 are
   the real VCCX/VCCIO0 and stay on `p3v3d` at 3.3 V** (DS117 Table 3-2: VCCX min 2.375 V;
   Table 3-5: VCCX POR trip 1.8–2.0 V). Rev.1's escalation asked for the opposite; it is
   closed and must not be reopened.
4. **All 46 user signals land on IOB\*/IOR\*/IOT\* pins, i.e. 3.3 V rails.** Bank edges were
   read off the symbol's own pin names: `IOL*` = BANK3 (1.8 V, VCCIO3, shared with the PSRAM
   die), `IOB*` = BANK2 (VCCO2 23/44), `IOR*` = BANK1 (VCCIO1 58), `IOT*` = top edge on
   VCCX/VCCIO0 (64/67/78). BANK2 has 23 bonded I/O and `da`+`db` need 24, so `db[11]` spills
   to pin 48 (IOR24B, BANK1) — both at 3.3 V. **At rev.4 this is now true of the IOL pins
   too:** the only IOL pins used are 5–8 (JTAG) and 9 (RECONFIG_N), and all five are
   referenced to `P1V8` = VCCIO3. Every other BANK3 pin (3, 4, 10, 11, 13–16) is `NC`, so
   rev.4 audited the whole bank and **no 3.3 V assumption about a BANK3 pin remains**.
5. **LEDs moved from 57/59 to 49/50.** Pins 49/50 (IOR24A/IOR22B) were freed by retiring
   OVRA/OVRB and are plain I/O; 57/59 are MSPI configuration-shared. The LEDs no longer
   flicker during configuration. `Device:LED` is **pin 1 = K, pin 2 = A** — D51/D52 are wired
   explicitly (`d5x['A']`, `d5x['K']`); a `pin & R & LED & gnd` chain reverse-biases them.
6. **R54 (pin 88, MODE0) and R55 (pin 87, MODE1), 4.7 kΩ to GND — implemented.** MODE[1:0]=00,
   MODE2 unbonded and defaulting to 0 → MODE[2:0]=000 = AUTOBOOT from on-die config Flash
   (UG290 Table 5-1). Pull-**downs**: sampled at power-up, valid before any I/O rail is up.
7. **R53 (pin 9, IOL13B_RECONFIG_N) pulls up to `p1v8`, not `p3v3d`** — a BANK3 pin, abs max
   VCCIO3 + 0.3 = 2.1 V. Per net_plan rev.3 line 167. 180 µA pull-up current.
8. **J3 JTAG pinout, CORRECTED AT REV.4** (build the cable adapter to this): **1=`P1V8`**
   (was `P3V3D` through rev.3 — that was erc_report HIGH-1), 2=`GND`, 3=TCK (U5.6),
   4=TMS (U5.5), 5=TDI (U5.7), 6=TDO (U5.8). Development only — the device boots itself.
   **Pin 1 is the pod's I/O reference and must follow VCCIO3**, because U5 pins 5–8 are
   `IOL*` = BANK3 per Gowin UG803's per-pin table (BANK column = 3; they are typed `I/O`,
   not dedicated VCCX-referenced pins). Three independent reasons: BANK3 abs max is
   VCCIO3 + 0.3 V = **2.1 V**, so a 3.3 V pod overdrives TCK/TMS/TDI by 1.2 V; TDO swings
   to 1.8 V, under a 3.3 V pod's ~2.0 V V_IH, so programming could not work even undamaged;
   and `P1V8` is deliberately the last rail up, so a pod attached at plug-in back-powers
   BANK3 — the rail feeding the in-package PSRAM, i.e. the whole 4 MB sample buffer
   (SPEC F6). Same rail as R53 on pin 9, for the same reason (decision 7).
   **The pod must be a 1.8 V-capable one.** A 3.3 V-only pod is a BOM change (level
   shifter or series resistors) and an architecture decision, not a coder fix.
   One line changed (`p3v3d += j3[1]` → `p1v8 += j3[1]`); no BOM change, no new refdes,
   signature untouched.
9. Supply pins are addressed by number throughout: the symbol repeats `VCC` ×4, `VSS` ×6,
   `VCCX_VCCO0` ×4, so name lookup is ambiguous.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/fpga_core.py` | The `fpga_core` @SubCircuit — U5, J3, D51/D52, R51–R55, C501–C517 | Assembling the circuit |

## Next phase must

Addressed to **skidl-assembler**:

1. Emit exactly this call (keyword form — the parameter names above are final):
```python
fpga_core(clk_fpga=CLK10_FPGA, da=ADC_DA, db=ADC_DB, dva=ADC_DVA, sen=ADC_SEN,
          sclk=ADC_SCLK, sdata=ADC_SDATA, sel=ADC_SEL, fifo_d=FIFO_D,
          rxf_n=FIFO_RXF_N, txe_n=FIFO_TXE_N, rd_n=FIFO_RD_N, wr_n=FIFO_WR_N,
          oe_n=FIFO_OE_N, fifo_clk60=FIFO_CLK60, p1v2=P1V2, p1v8=P1V8,
          p3v3d=P3V3D, gnd=GND, tag='fpga_core')
```
   with `FIFO_D = Bus('FIFO_D', 8)` alongside `adc_dual`'s 12-bit `ADC_DA`/`ADC_DB`.
   **Do not pass `ovra`, `ovrb` or `siwu_n`** — they no longer exist.
2. `P1V2`, **`P1V8`**, `P3V3D`, `GND` all need **`.drive = POWER`** at top level: all 18
   supply pins here are `power_in` and this block only consumes them.
3. `validate-footprints.py` needs `KICAD9_FOOTPRINT_DIR` **unset or a single path** — it does
   not split a colon list, which makes every stock library look missing.

## Carried forward

| Item | Note |
|---|---|
| ~~**[MED] `p1v8` may not be the right net for pin 12 if U15 is added**~~ **CLOSED at rev.3** — `power_tree` decision 2 makes `P1V8` U15's *output* (U14's output is the block-internal `P1V8_PRE`), so pin 12 already lands on the slew-limited side. No signature change. Original text: | `04_datasheets` decision 16 recommends inserting a second TPS22918 (U15 + C87) between U14's VOUT and VCCIO3 to get a ≥180 µs ramp (DS117 Table 3-3, 10 mV/µs max). Architecture rev.3 does **not** include U15 and the BOM has no U15/C87, so pin 12 is wired to `p1v8` as the work order specifies. **If `power_tree` adds U15, pin 12 must move to its output net and this signature gains a parameter.** Decide before the assembler runs. |
| **[LOW] Bonded 3.3 V I/O count exceeds the budget's 48** | The symbol bonds 23 IOB + 15 IOR + 20 IOT = 58 user I/O on 3.3 V rails, plus 9 IOL on 1.8 V. The rev.3 budget credits 48 (BANK1 25 + BANK2 23) and counts the IOT pins as BANK0 = 0. I did **not** act on the difference; the assignment stays inside pins whose rail is 3.3 V either way. 12 unused 3.3 V-capable pins remain (57, 59, 60, 61, 62, 82–86 + 2 spare) if a signal is ever added. **No signal needing a 3.3 V user pin was added by this block.** |
| ~~Decoupling is 4 × 100 nF short of policy~~ | **CLOSED at rev.3.** Sourcing rev.4 funded C514–C517 (`sourced_bom.csv` row 55) in response to rev.2's flag, and they are now wired. Policy is met **exactly**: 11 × 100 nF, one per U5 supply pin. **Per rail, as the rail actually is:** core `P1V2` pins 1/22/45/66 → C501, C502, **C516, C517**; 3.3 V VCCX/VCCIO0 64/67/78 + VCCO2 23/44 + VCCIO1 58 → C503–C506, **C514, C515**; VCCIO3 pin 12 (1.8 V PSRAM bank, decision 3) keeps its own C511 on `P1V8` and gets **none** of C514/C515. |
| **Symbol pin-12 label still wrong** | Left unfixed deliberately (owner: datasheet-librarian). Any future coder touching U5 power must read decision 3 first. |
| 18 intentional `NC` pins | 3, 4 (JTAGSEL_N — internal pull-up assumed to keep JTAG enabled, **unverified**), 10 (DONE), 11, 13–16 (all BANK3/1.8 V, unusable here); 57, 59, 60, 61, 62 (MSPI bus, unused — no external config memory); 82 (freed by R67), 83–86. ERC will report all 18; correct. |
| `sen`/`sclk`/`sdata`/`sel` on config-shared pins 53–56 | Harmless: the PLL-disable write is post-config and overwrites anything the ADC latched during configuration. Only 3 free 3.3 V pins existed when the LEDs were placed; moving all four was not possible. |

## Do not redo
- The BANK3/VCCIO3 = pin 12 resolution (decision 3) and the 64/67/78 = 3.3 V rule.
- `ADC_SEL` as an FPGA-driven pin (SBAS295A p.19); R402 stays deleted.
- R-13 / external config flash — closed, the device has 4 Mbit on-die config Flash.
- The MODE[1:0]=00 encoding, R53's move to `P1V8`, and the `Device:LED` pin-order finding.
- **J3 pin 1 on `P1V8` (decision 8, rev.4).** erc_report HIGH-1 is closed; do not restore
  `P3V3D` there. The old comment claiming "Gowin's dedicated JTAG pins are referenced to
  VCCX = 3.3 V" was wrong and is deleted from the file.

## Receipt
- rev.4: **26 parts** (U5, J3, D51/D52, R51–R55, C501–C517), 59 nets — unchanged from
  rev.3. U5: 71 of 89 pins connected, 18 intentionally `NC`.
- Only change vs rev.3: erc_report **HIGH-1** fixed — `p3v3d += j3[1]` → `p1v8 += j3[1]`,
  plus the wrong JTAG comment and the two docstring lines it rested on. Whole BANK3 audited;
  no other 3.3 V assumption found. Netlist confirms `J3.1 → P1V8`.
- `py_compile` OK; footprint strings all resolve; full-circuit run: **0 ERC errors,
  0 ERC warnings**.
- BOM-vs-code **agrees**: `validate-bom.py` **exit 0**, 170 parts. `sourced_bom.csv` was
  **not** edited.
- Signature changed: **no** at rev.4 (unchanged since rev.2). The assembler's existing
  keyword call still applies verbatim.
