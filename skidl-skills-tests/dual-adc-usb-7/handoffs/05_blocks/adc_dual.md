---
phase: 05_blocks/adc_dual
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-22T22:05:00Z
status: complete
revision: 2
next_phase: 05_coding
---

# Phase 5 handoff — block `adc_dual`

**Rev.2 is a two-line change against rev.1:** `ovra`/`ovrb` left the signature, U4 pins
39/9 became `NC`. All other rev.1 decisions stand verbatim.

## Decisions

1. **SIGNATURE CHANGED — `ovra`/`ovrb` REMOVED.** Final, as written in the file:
   `adc_dual(inap, inan, inbp, inbn, cm, clk_adc, da, db, dva, sen, sclk, sdata, sel, p3v3a, p3v3d, gnd)`
   Verbatim from architecture rev.3 § Block manifest. **An assembler still passing
   `ovra=`/`ovrb=` raises `TypeError` — drop both keywords.** Nothing else renamed or reordered.
2. **OVRA (pin 39) and OVRB (pin 9) are `NC`** — `u4[39] += NC`, `u4[9] += NC`. ADC
   *outputs*, so left genuinely open: not tied to GND, a rail, or each other. Why (arch
   rev.3 dec.2): BANK3's 23 I/O follow VCCIO3 to 1.8 V for the in-package PSRAM, leaving
   48 3.3 V-capable I/O against 51 required; overrange is in no SPEC line and clipping
   stays visible in firmware as codes 0x000/0xFFF, so it was the cheapest pin to give up.
3. **`da`/`db` are 12-bit Buses.** `da[0..11]` = U4 pins 27..38, `db[0..11]` = pins 10..21;
   index 11 is the MSB.
4. **Drives:** `cm`, `da[*]`, `db[*]`, `dva`. **Senses only:** everything else in the
   signature. **Bidirectional:** none.
5. **UNCHANGED — SEL is a dynamically driven FPGA pin, not a strap.** Re-verified against
   SBAS295A p.19: the low-going pulse resets the serial registers, the PLL powers up
   *enabled*, and only a serial write disables it — the sole path to 10 MSPS (SPEC F3). The
   intermediate strap proposal was overturned; do not re-propose it. Pins 41 = SEN,
   42 = SCLK, 45 = SDATA, all FPGA-driven, **no GND ties**. OEB# (6) is the only static low;
   INT/EXT# (56) → P3V3A; DVB (22) stays NC; R402 stays deleted from code and BOM.

## Artifacts
| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/adc_dual.py` | The `adc_dual` @SubCircuit — U4, R401, C401–C410 | Assembling |

## Next phase must

Addressed to **skidl-assembler**:

1. Emit exactly this call — **note the absent `ovra=`/`ovrb=`**:
```python
adc_dual(inap=ADC_INAP, inan=ADC_INAN, inbp=ADC_INBP, inbn=ADC_INBN,
         cm=ADC_CM, clk_adc=CLK10_ADC, da=ADC_DA, db=ADC_DB, dva=ADC_DVA,
         sen=ADC_SEN, sclk=ADC_SCLK, sdata=ADC_SDATA, sel=ADC_SEL,
         p3v3a=P3V3A, p3v3d=P3V3D, gnd=GND, tag='adc_dual')
```
   with `ADC_DA = Bus('ADC_DA', 12)` and `ADC_DB = Bus('ADC_DB', 12)`.
2. **Do not declare `ADC_OVRA`/`ADC_OVRB` at the top level.** No block touches them now
   (`fpga_core` dropped them in the same rev.3 pass); a leftover Net draws an ERC warning.
3. `P3V3A`, `P3V3D`, `GND` need **`.drive = POWER`** at the top level — this block only
   consumes them (AVDD/VDRV/AGND/GND are all `power_in`).
4. **`R402` must not appear in `sourcing/sourced_bom.csv`** or `validate-bom.py` fails. If
   not yet applied: on row `"R402,R53,R65",0402WGF1002TCE,C25744,10k,…` delete only the
   `R402,` token (R53/R65 stay); same for `sourcing/sourced_bom.md` L52.
5. `symbols/` must be on `KICAD9_SYMBOL_DIR` — U4 is `Part('dual_adc_usb', 'ADS5231IPAGT')`.

## Carried forward

| Item | Note |
|---|---|
| U4 pins 39/9 (OVRA/OVRB) | Intentionally `NC` — outputs, open, never tied. Over-range is unreachable in hardware from rev.3 on; firmware detects clipping from codes 0x000/0xFFF. Restoring them costs 2 pins the budget lacks (margin +2, final). |
| U4 pin 22 (DVB) | Intentionally `NC`. Only channel A's strobe is used; both channels share one clock. |
| `ADC_CM` bypass | Not here — C119/C219 in `afe_driver` are CM's bypass caps. CM drives ±2 mA max, **no resistive load permitted**; hang nothing else on it. |
| PLL-disable firmware | Gateware must raise SEL, pulse it low, then clock `D7..D0 = 0 0 1 1 0 0 1 0` on SDATA (SBAS295A p.8). Without it the part will not run below 20 MSPS. |
| Clock duty cycle | PLL disabled ⇒ 10 MHz clock near 50% duty (SBAS295A p.19), tighter than 45–55%. A `clock_gen` constraint. |
| REFT/REFB | Internal nets, 0.1 µF each to GND. Summary mentions a 2 Ω series element; none sourced, none instantiated. Low risk, flagged. |

## Receipt
- `adc_dual` rev.2: 12 parts (U4, R401, C401–C410) unchanged; interface nets 16 (was 18).
- Scope: signature lost `ovra`/`ovrb`; U4 pins 39/9 → `NC`. Nothing else touched.
- `py_compile` OK; 4 footprints valid, unchanged.
- Signature changed: **YES** — assembler must drop the `ovra=`/`ovrb=` keywords.
