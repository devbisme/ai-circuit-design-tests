---
phase: 05_blocks/adc
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-11T00:10:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 block handoff — adc (ADS5231 dual ADC)

## Decisions
- Signature unchanged, verbatim: `adc(ain_a_p, ain_a_n, ain_b_p, ain_b_n, adc_vcm, adc_clk, adc_da, adc_db, adc_ovra, adc_ovrb, adc_dva, adc_sel, adc_sen, adc_sclk, adc_sdata, va_3v3, gnd)`.
- **Drives:** `adc_vcm` (U12.CM, 1.5 V), `adc_da[0..11]`, `adc_db[0..11]`, `adc_ovra`, `adc_ovrb`, `adc_dva` (all via 33 Ω arrays). **Senses:** `ain_*`, `adc_clk`, `adc_sel/sen/sclk/sdata` (U12 inputs, each with a 10k pull-down). **Consumes:** `va_3v3` (only through FB5/FB6), `gnd`. Nothing is bidirectional.
- **RN1–RN7 use `Device:R_Pack04`, not the BOM's `Device:R_Network04`.** R_Network04 is a bussed 5-pin star network. On the 8-pad `R_Array_Convex_4x0603` it would tie every data line to one common node, and pads 6–8 would get no net. The BOM note says "isolated 4-resistor array", and R_Pack04 is the KiCad symbol for that (8 pins; its fp_filter covers Convex arrays). MPN, LCSC number and footprint are used verbatim.
- **Pin types of the U12 symbol are corrected on this instance only.** The generated symbol types CLK as output and DVA/DVB as power_in. SBAS295A p.11–12 gives CLK = I and DVA/DVB = O. Without the fix, the DVA net (power_in plus a passive) fails ERC for insufficient drive.
- `ADC_AVDD` (VA_3V3→FB6) and `ADC_VDRV` (VA_3V3→FB5) are block-local, with `.drive = POWER` set in the block. VDRV comes from VA_3V3, not VD_3V3, per the architecture.
- Straps per net_plan §5: R53 SEL, R54 MSBI/SEN, R55 OEA#/SCLK, R56 STPD/SDATA, each 10k to GND. OEB# goes to GND and INT/EXT# to ADC_AVDD (internal reference). ISET is R50 56.2k to GND.
- Reference: REFT→R51 2 Ω→ADC_REFT_C→C50 100 nF→GND. REFB→R52→ADC_REFB_C→C51→GND. CM (ADC_VCM) has C52 100 nF and C53 1 µF.
- Decoupling (placement intent): AVDD C54→pin 3, C55→46, C56→57, C57 10 µF bulk. VDRV C58→pin 5, C59→8, C60→40, C61→43, C62 10 µF bulk.
- Array wiring: element k spans pin k (ADC side, nets `ADC_DA_R*` / `ADC_DB_R*` / `ADC_*_R`) to pin 9−k (FPGA side). RN1–RN3 carry DA0–3/4–7/8–11 and RN4–RN6 carry DB0–3/4–7/8–11. RN7 elements 1/2/3 carry OVRA/OVRB/DVA.
- MPN and LCSC go into netlist `fields` on all 30 parts (checked in the emitted netlist).

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/adc.py` | `@SubCircuit adc(...)`: U12 + 29 passives | Assembling; debugging ERC attributed to `adc` |

## Next phase must
1. **skidl-assembler:** emit exactly
   `adc(ain_a_p=AIN_A_P, ain_a_n=AIN_A_N, ain_b_p=AIN_B_P, ain_b_n=AIN_B_N, adc_vcm=ADC_VCM, adc_clk=ADC_CLK, adc_da=ADC_DA, adc_db=ADC_DB, adc_ovra=ADC_OVRA, adc_ovrb=ADC_OVRB, adc_dva=ADC_DVA, adc_sel=ADC_SEL, adc_sen=ADC_SEN, adc_sclk=ADC_SCLK, adc_sdata=ADC_SDATA, va_3v3=VA_3V3, gnd=GND, tag='adc')`
   with `ADC_DA = Bus('ADC_DA', 12)` and `ADC_DB = Bus('ADC_DB', 12)`. Index 0 is the LSB. The block indexes `adc_da[i]`, so a list of 12 nets also works.
2. Set `VA_3V3.drive = POWER` and `GND.drive = POWER` at top level. This block reaches VA_3V3 only through ferrite beads, and it has power_in pins on GND.
3. **Symbol path (seen in my smoke test):** this SKiDL (3.0.0, `~/projects/KiCad/tools/skidl/src`) defaults to tool `kicad10`. It appends `KICAD9_SYMBOL_DIR` as one path and does not split on colons (`tools/kicad9/lib.py:43`), so the colon recipe in `rules/environment.md` did not find `symbols/`. `lib_search_paths[get_default_tool()].append('<project>/symbols')` worked.
4. Expected ERC from this block, instantiated alone with `.drive` on VA_3V3/GND: **0 errors**. The 42 warnings were all single-pin interface nets and go away when the neighbouring blocks are wired.

## Carried forward
- **Intentional NC:** U12.DVB (pin 22). Channel B data is captured on DVA, since both channels sample simultaneously on one clock. RN7 element 4 (pins 4 and 5) is a spare.
- **Symbol library defect still open:** the CLK/DVA/DVB pin types in `symbols/dual_adc_usb.kicad_sym` are wrong; see the TODO in adc.py. MSBI/SEN, OEA#/SCLK and STPD/SDATA are typed bidirectional where the datasheet says inputs. That is harmless for ERC.
- **REFT/REFB/CM bulk caps:** SBAS295A Fig. 21 also shows 2.2 µF on REFT, REFB and CM. The power-down timing note assumes 1 µF on the reference pins. The architecture chose 0.1 µF only, matching the datasheet pin-table text. I added nothing (no refs allotted). Flag for design review: this is a low-risk noise and power-up-time question.
- **Gateware must know:** the pull-down defaults are parallel control (SEL=0), straight offset binary (MSBI=0), both channels' outputs enabled and not powered down. Serial mode needs a low-going SEL pulse after power-up (datasheet p.12). fpga_core must not add pull-ups on SEL/SEN/SCLK/SDATA, because they would fight R53–R56.
- **Neighbour assumptions:** analog_front_end supplies the 49.9 Ω series resistors and the 220 pF across each pair; sample_clock supplies the R57 series resistor on ADC_CLK. This block puts no termination on AIN_* or ADC_CLK.

## Do not redo
- The U12 pin map was checked pin by pin against SBAS295A p.11–12: all 64 pins are connected as intended and verified in the smoke-test dump.
- The R_Pack04 choice for RN1–RN7 (reason above).

## Receipt
Block `adc`: 30 parts (U12, R50–R56, RN1–RN7, C50–C62, FB5, FB6), 73 nets (34 block-local, 39 interface).
`py_compile` OK. Footprints 9/9 valid. Signature changed: **no**. Symbol changed for RN1–RN7 (R_Network04→R_Pack04).
Smoke-instantiated in scratch: 0 ERC errors in isolation; MPN/LCSC fields present in the netlist.
status: complete.
