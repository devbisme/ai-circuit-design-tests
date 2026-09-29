---
phase: 05_blocks/io_expansion
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-10T23:40:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — io_expansion

## Decisions
- Final signature is **unchanged** from the work order:
  `io_expansion(led_stat_1v8, led_act_1v8, trig_out_1v8, gpio_out_1v8, trig_in_1v8, vd_3v3, vd_1v8, gnd)`
- Net roles:
  - **Sensed (inputs to U16):** led_stat_1v8 → 1A (pin 2), led_act_1v8 → 2A (5), trig_out_1v8 → 3A (9), gpio_out_1v8 → 4A (12).
  - **Driven by this block:** trig_in_1v8, from U17.Y (pin 4).
  - **Consumed:** vd_3v3 (U16 VCC 14, J5 pin 1) and vd_1v8 (U17 VCC 5).
  - **Ground:** gnd.
- U16 SN74LV4T125 runs at VCC = VD_3V3. All four OE# pins (1, 4, 10, 13) go to GND, so the buffers are always enabled. The KiCad symbol's pins are unnamed (`~`), so U16 is wired **by pin number**.
- U17 SN74LV1T34 runs at VCC = VD_1V8. Its input is 5.5 V-tolerant. R84 (1 kΩ) is in series and R85 (100 kΩ) pulls down at the header.
- Block-local nets:
  - LED_STAT and LED_ACT: U16 Y output → R80/R81.
  - LED_STAT_K and LED_ACT_K: R → LED anode. These are the net plan's names.
  - EXT_TRIG_OUT_R/EXT_TRIG_OUT and EXT_GPIO_OUT_R/EXT_GPIO_OUT: U16 side and header side of R82/R83.
  - EXT_TRIG_IN/EXT_TRIG_IN_R: header side and U17 side of R84.
  - `_R` marks the IC side of a series resistor, following the plan's EXT_TRIG_IN_R. The plan named only the header-side output nets, so the `_R` names on the output side are my choice.
- J5 pinout, per net_plan §9: 1 VD_3V3, 2 EXT_TRIG_IN, 3 EXT_TRIG_OUT, 4 EXT_GPIO_OUT, 5 GND, 6 GND.
- LEDs: LED2 = status, LED3 = activity. Both are CT-1608UGC-P4 green, each with 1 kΩ from a 3.3 V push-pull output, about 1 mA.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/io_expansion.py` | `@SubCircuit io_expansion`: U16, U17, LED2, LED3, R80–R85, C96, C97, J5 | Assembling or reviewing this block |

## Next phase must
1. skidl-assembler: call it by keyword, exactly as follows:
   `io_expansion(led_stat_1v8=LED_STAT_1V8, led_act_1v8=LED_ACT_1V8, trig_out_1v8=TRIG_OUT_1V8, gpio_out_1v8=GPIO_OUT_1V8, trig_in_1v8=TRIG_IN_1V8, vd_3v3=VD_3V3, vd_1v8=VD_1V8, gnd=GND, tag='io_expansion')`
2. Set `.drive = POWER` at top level on VD_3V3, VD_1V8 and GND, unless power_rails already drives them. This block has only power_in or passive pins on them.

## Carried forward
- U17 pin 1 (NC) is marked `NC` on purpose, because it has no internal connection.
- Standalone ERC shows "No drivers / Insufficient drive" on the four *_1V8 inputs. The driver is U15 in fpga_core, so these close at assembly. U15's I/O are BIDIR, which counts as a driver.
- U16 and U17 decoupling is in this block (C96, C97). The assembler adds none.
- The 1.8 V → 3.3 V margin rests on the LVxT reduced-threshold inputs. The margin was not re-checked against the TI VIH table at VCC = 3.3 V; the summary only says the part is "level-shifting capable". Low risk, noted.

## Do not redo
- The J5 pinout and U16 channel assignment (1 = STAT, 2 = ACT, 3 = TRIG_OUT, 4 = GPIO_OUT) follow net_plan §9.

## Receipt
- Block `io_expansion`: 13 parts (U16, U17, LED2, LED3, R80–R85, C96, C97, J5).
- 18 nets: 8 interface and 10 local.
- py_compile OK. Footprints valid (validate-footprints.py exit 0, plus a direct file check of all 7 strings).
- Test ERC: 0 errors and 13 warnings. All 13 are open interface nets that close at assembly.
- Signature changed: **no**.
