---
phase: 05_blocks/adc
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-26T13:10:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — adc

## Decisions
- Final signature (unchanged): `adc(ain_a_p, ain_a_n, ain_b_p, ain_b_n, vcm, adc_clk, da, db, adc_dva, adc_stpd, v3v3a, gnd)`.
- `da`/`db` must be 12-net buses (index 0 = LSB): da[i] = D{i}_A (pins 27..38), db[i] = D{i}_B (pins 10..21).
- **Drives:** vcm (U8.CM pin 52 — symbol pin type **OUTPUT**), da[0..11], db[0..11], adc_dva (all OUTPUT/TRISTATE).
- **Senses:** ain_a_p/n, ain_b_p/n, adc_clk, adc_stpd (INPUT; R15 10k pull-down to gnd). **Consumes:** v3v3a, gnd.
- U8 = `dual_adc_usb:ADS5231IPAGT`. SEL/OEB/MSBI/OEA → gnd; INT/EXT → v3v3a (internal ref).
- VDRV (5,8,40,43) on local net ADC_VDRV fed from v3v3a via FB1.
- Local nets: ADC_VDRV, ADC_ISET (R12 56.2k), ADC_REFT_C / ADC_REFB_C (R13/R14 2 Ω → C18/C19 0.1 µF).
- Decoupling in-block: C22–C24 0.1 µF + C25 10 µF on AVDD; C26–C29 0.1 µF + C30 10 µF on VDRV; C20 0.1 µF + C21 1 µF on VCM.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/adc.py` | block @SubCircuit | Assembly |

## Next phase must
1. skidl-assembler: `adc(ain_a_p=AIN_A_P, ain_a_n=AIN_A_N, ain_b_p=AIN_B_P, ain_b_n=AIN_B_N, vcm=VCM, adc_clk=ADC_CLK, da=DA, db=DB, adc_dva=ADC_DVA, adc_stpd=ADC_STPD, v3v3a=V3V3A, gnd=GND, tag='adc')` with `DA = Bus('DA', 12)`, `DB = Bus('DB', 12)`.
2. **VCM: do NOT set `VCM.drive = POWER`.** U8.CM is an OUTPUT pin and drives VCM; the AFE VOCM inputs are satisfied by it.
3. `GND.drive = POWER` at top (U8 GND/AGND are PWRIN). V3V3A is driven by power_analog (U6.OUT).
4. ADC_VDRV (local, fed from V3V3A through FB1) has `.drive = POWER` set inside the block; nothing needed at top.
5. ADC_REFT_C / ADC_REFB_C / ADC_ISET contain only passive + REF(BIDIR)/ISET pins: no-driver warnings there are false positives.
6. Trial ERC (adc + clock, GND/V3V3A driven): 0 errors; ADC_CLK, VCM, ADC_STPD and all local nets clean. Only warnings were single-pin interface nets whose other ends live in other blocks.

## Carried forward
- NC intentionally: U8 DVB (22), OVRA (39), OVRB (9) per net_plan.
- STPD pull-down R15 is in this block; the FPGA drives ADC_STPD.
- Assumes AFE blocks put their own 49.9 Ω/56 pF RC ahead of the AIN nets (R110/R111, C113 etc.).
- BOM cell correction: U8 symbol `SYMBOL_NEEDED` → `dual_adc_usb:ADS5231IPAGT`.

## Receipt
- Block adc: 19 parts (U8, FB1, R12–R15, C18–C30), 41 nets (4 local), py_compile OK, footprints 5/5 resolve, signature changed: no. Instantiation check: all 64 U8 pins connected except the 3 intentional NC.
