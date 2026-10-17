---
phase: 05_blocks/adc
agent: skidl-block-coder
circuit: dual_adc_10msps
written: 2026-10-17T00:00:00Z
status: complete
revision: 2
next_phase: 05_coding
---
# Block handoff - adc

## Decisions
1. Signature unchanged: `adc(ain_ap, ain_an, ain_bp, ain_bn, adc_cm, adc_clk, da, db, adc_dva, adc_ovra, adc_ovrb, adc_sel, adc_sen, adc_sclk, adc_sdata, v3v3a, v3v3, gnd)`.
2. `da`, `db` must be indexable 12-wide buses (`Bus('DA', 12)` -> DA0..DA11; index 0 = LSB = D0).
3. Connections exactly per `architecture/net_plan.md` Block 5; U301 wired by pin number (verified against the generated symbol pin table).
4. Drives: `adc_cm` (CM output), `da`/`db` (via 33R), `adc_dva`, `adc_ovra`, `adc_ovrb`. Senses: `ain_*`, `adc_clk`, `adc_sel/sen/sclk/sdata` (inputs, each 10k pull-down to GND). Consumes: `v3v3a`, `v3v3`, `gnd`.
5. Local nets: `+3V3_ADCIO` (FB301 out -> VDRV; `.drive = POWER` set in block), `ADC_REFT`, `ADC_REFB`, `REFT_RC`, `REFB_RC`, `ADC_ISET`, `DA_ADC0..11`, `DB_ADC0..11`.
6. RN mapping: RN301/302/303 = bits 0-3/4-7/8-11 of A, RN304/305/306 same for B; element k: pin k (ADC side) <-> pin 9-k (bus side).

- Rev 2: every MPN-bearing part now also sets `fields['LCSC']` from sourcing/sourced_bom.csv (script-checked per ref: 0 mismatches); helpers that take `mpn` gained an `lcsc` param right after it.
- Rev 2: `#FLG301` PWR_FLAG added on `+3V3_ADCIO` (FB301 output, U301 VDRV 5/8/40/43) alongside `.drive = POWER` (fixes KiCad power_pin_not_driven).

## Artifacts
| File | Contains |
|---|---|
| `circuits/dual_adc_10msps/adc.py` | @SubCircuit adc, 34 parts |

## Next phase must
- Emit: `adc(ain_ap=AIN_AP, ain_an=AIN_AN, ain_bp=AIN_BP, ain_bn=AIN_BN, adc_cm=ADC_CM, adc_clk=ADC_CLK, da=DA, db=DB, adc_dva=ADC_DVA, adc_ovra=ADC_OVRA, adc_ovrb=ADC_OVRB, adc_sel=ADC_SEL, adc_sen=ADC_SEN, adc_sclk=ADC_SCLK, adc_sdata=ADC_SDATA, v3v3a=P3V3A, v3v3=P3V3, gnd=GND, tag='adc')`
  with `DA = Bus('DA', 12)`, `DB = Bus('DB', 12)`, `P3V3A = Net('+3V3A')`, `P3V3 = Net('+3V3')`.
- `+3V3A`, `+3V3`, `GND` only consumed here -> `.drive = POWER` at top level if not driven by power blocks.
- Gateware (not hardware): after supplies, low pulse on SEL, then write reg addr 0011 data xx1x (word 0x32) to disable PLL - required at 10 MSPS.

## Carried forward
- Intentional NC: U301.22 (DVB); DVA clocks both channels.
- OEB (pin 6) tied GND (B outputs always enabled); INT/EXT (56) tied +3V3A (internal ref).
- All ADC decoupling is in-block (C305-C308 AVDD, C309-C313 VDRV, C303/C304 CM). C119/C219 on ADC_CM in afe_channel add 20 nF.
- +3V3A capacitance budget (net plan): C308 4.7u counted here.
- Power sequencing (AVDD vs VDRV within +/-10 ms, |diff| <= 0.3 V) depends on power_analog/power_digital ramp - not enforced in this block.

## Do not redo
- MPNs/footprints verbatim from `sourcing/sourced_bom.csv`.

## Receipt
adc (rev 2): 34 parts (+1 PWR_FLAG #FLG301; U301, FB301, R301-R307, RN301-RN306, C301-C313), 18 interface args (da/db 12-wide), 31 local nets; py_compile OK; footprints from CSV verbatim (hook raised no error); signature changed: no.
