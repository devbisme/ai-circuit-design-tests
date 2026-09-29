# Shared coding notes — dual_adc_usb block coders (2026-09-07)

## Environment (there is NO .venv)
Run circuits with:
    KICAD9_SYMBOL_DIR=/usr/share/kicad/symbols python3 <file>
SKiDL 3.0.0 is on the system python3. Footprint validator:
    python3 /home/devb/.claude/plugins/cache/waveguide-marketplace/skidl-skills/1.0.0/scripts/validate-footprints.py <file>

## Block file rules (from rules/skidl-syntax.md)
- `from skidl import *` only. NO cross-block imports. NO ERC(), NO generate_netlist(), NO __main__.
- Decorate with `@subcircuit`. Signature is fixed by the manifest — verbatim, do not change it.
- `+=` is the only connection operator.
- Every Part needs ref=, value=, footprint=.
- Intentional no-connects: `part['NCname'] += NC`.
- Ref designators are pre-assigned per block; do not stray outside your range.
- Docstring with an Args: section, and inline comments citing net_plan.md sections.
- Self-check before finishing:
    python3 -m py_compile <yourfile>
  then instantiate standalone in a scratch file under /tmp and confirm part count.
  DO NOT write scratch files into circuits/, outputs/, datasheets/ or sourcing/ (hook-protected).

## D3 (2026-09-07) — corrections already applied to architecture/net_plan.md
1. **The LTC2292 has NO CLKOUT pin.** Net `adcClkOut` is DELETED. Verified: 0 hits for "CLKOUT"
   in all 28 pages of the datasheet PDF, and the KiCad symbol `Analog_ADC:LTC2292xUP` has 65 pins
   with no such pin.
2. The FPGA capture clock is `xoClkFpga` (the R41 100R tap off the same 40 MHz XO), captured on
   the **FALLING** edge. Margins: 7.1 ns setup / 13.9 ns hold at 50% duty. See net_plan.md §1.4.1.
3. **`adcVcm` is SPLIT into `adcVcmA` and `adcVcmB`.** The datasheet says verbatim, in both pin
   descriptions, "Do not connect to VCMB" / "Do not connect to VCMA".
4. Revised signatures:
     def adc_dual(v3v0_avdd, v3v3_d, gnd, vref_1v0, adc_vcm_a, adc_vcm_b,
                  ain_ap, ain_an, ain_bp, ain_bn, enc_clk40,
                  adc_data_a, adc_data_b, adc_of_a, adc_of_b,
                  adc_shdn, adc_oe_bar)
     def fpga_ice40(v3v3_d, v1v2_core, gnd,
                    adc_data_a, adc_data_b, adc_of_a, adc_of_b,
                    adc_shdn, adc_oe_bar, xo_clk_fpga,
                    sram_addr, sram_data, sram_ce_bar, sram_oe_bar, sram_we_bar,
                    fifo_data, fifo_rxf_bar, fifo_txe_bar, fifo_rd_bar,
                    fifo_wr_bar, fifo_oe_bar, ft_clk60,
                    cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar,
                    fpga_creset_bar, fpga_cdone, mode_strap,
                    probe_comp_drv, ext_trig, led_status, led_activity)
   `afe_channel(ch, vp4v0, vn4v0, gnd, adc_vcm, ain_p, ain_n)` is UNCHANGED — the A instance is
   passed adcVcmA, the B instance adcVcmB.

## KiCad symbols verified present on disk (read with skidl, pin names exact)
| Part | Symbol | Notes |
|---|---|---|
| LTC2292 | `Analog_ADC:LTC2292xUP` | 65 pins. See net_plan.md §3.6 for the full pin map. |
| iCE40HX4K | `FPGA_Lattice:ICE40HX4K-TQ144` | 144 pins, 5 units. Access by pin NUMBER. |
| FT2232HL | `Interface_USB:FT2232HL` | 64 pins. VCORE=12,37,64; VCCIO=20,31,42,56; VREGIN=50; VREGOUT=49; VPLL=9; VPHY=4; AGND=10; REF=6; TEST=13; ~{RESET}=14; ~{SUSPEND}=36; ~{PWREN}=60; EEDATA=61; EECLK=62; EECS=63; OSCI=2; OSCO=3; DM=7; DP=8. |
| THS4521IDR | `Amplifier_Difference:THS4521ID` | 1=IN-, 2=V_{OCM}, 3=V_{S+}, **4=OUT+ (NAME IS EMPTY - use pin number 4)**, **5=OUT- (use pin number 5)**, 6=V_{S-}, 7=~{PD}, 8=IN+ |
| OPA1656IDR | `Amplifier_Operational:OPA1656ID` | 3 units. Pins 1=OUTA,2=INA-,3=INA+,4=V-,5=INB+,6=INB-,7=OUTB,8=V+. Access by NUMBER. |
| ADR4525BRZ | `Reference_Voltage:ADR4525` | 8 pins: 2=IN, 4=GND, 6=OUT; pins 1,3,5,7,8 are all named "NC". |
| OPA192IDBVR | `Amplifier_Operational:OPA197xDBV` | **SYMBOL SUBSTITUTION.** No OPA192 symbol exists in the KiCad 9 library. OPA197xDBV is the same TI SOT-23-5 pinout: 1=OUT, 2=V-, 3=+, 4=-, 5=V+. Set `value='OPA192IDBVR'` and leave an inline comment saying the symbol is a pin-compatible stand-in. |
| W25Q32JVSSIQ | `Memory_Flash:W25Q32JVSS` | 1=~{CS}, 2=DO/IO_{1}, 3=~{WP}/IO_{2}, 4=GND, 5=DI/IO_{0}, 6=CLK, 7=~{HOLD}/~{RESET}/IO_{3}, 8=VCC |
| 93LC66BT-I/OT | `Memory_EEPROM:93LCxxBxxOT` | SOT-23-6: 1=DO, 2=GND, 3=DI, 4=CLK, 5=CS, 6=VCC |
| SRAM | `dual_adc_usb:IS61WV204816BLL` in `lib/dual_adc_usb.kicad_sym` | already used by sram_buffer.py |

## Footprints already proven to resolve in this project
Resistor_SMD:R_0402_1005Metric, R_0603_1608Metric, R_0805_2012Metric
Capacitor_SMD:C_0402_1005Metric, C_0603_1608Metric, C_0805_2012Metric, C_1206_3216Metric
Package_TO_SOT_SMD:SOT-23-5, SOT-23-6, SOT-23, SOT-363_SC-70-6
Package_SO:SOIC-8_3.9x4.9mm_P1.27mm, TSSOP-8_3x3mm_P0.65mm, TSOP-I-48_18.4x12mm_P0.5mm
Package_QFP:LQFP-144_20x20mm_P0.5mm, TQFP-144_20x20mm_P0.5mm
Package_DFN_QFN:QFN-64-1EP_9x9mm_P0.5mm_EP4.7x4.7mm
Inductor_SMD:L_0603_1608Metric, L_0805_2012Metric
Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm
LED_SMD:LED_0603_1608Metric
Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical, PinHeader_1x03_P2.54mm_Vertical
Diode_SMD:D_SOD-323, D_SOD-123
Resistor_SMD:R_Array_Convex_4x0603  <-- for the 4-element 33R arrays (RN1-RN6)
**Run the footprint validator and fix anything it rejects before you finish.**
