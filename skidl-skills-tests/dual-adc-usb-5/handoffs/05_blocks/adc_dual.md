---
phase: 05_blocks/adc_dual
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-20T13:25:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Phase 5 handoff — block `adc_dual`

## Decisions

1. **Signature unchanged from the work order / architecture block manifest** — no parameter
   was renamed, added, or reordered:
   `adc_dual(in1_p, in1_n, in2_p, in2_n, adc_clk, adc_d1, adc_d2, adc_oe_n, adc_pdwn, vocm, v3v3_a, v3v3_adcd, gnd)`
   `adc_d1` / `adc_d2` must be **12-bit `Bus` objects**, everything else a `Net`.
2. **Net direction**: this block **drives `VOCM`** (from U5.CM pin 52, the design's only
   common-mode source per `net_plan.md`). It **drives `ADC_D1[11:0]` / `ADC_D2[11:0]`**
   (through the 33 Ω arrays). It **senses** `CH1_P/N`, `CH2_P/N`, `ADC_CLK`, `ADC_OE_N`,
   `ADC_PDWN`, `+3V3_A`, `+3V3_ADCD`, `GND`.
3. **Straps per handoff 04 item 1, all hard-tied, nothing floating**: SEL (1) → `GND`;
   INT/EXT (56) → `+3V3_A` (= AVDD, TI Figure 21); MSBI (41) → `GND` → **straight offset
   binary** output format — `fpga_core` and the host must assume that, not two's complement.
4. **OEA#/OEB#/STPD are net-connected, not GND-strapped, plus a pull-down each.**
   `net_plan.md` makes `ADC_OE_N` and `ADC_PDWN` FPGA-driven, and handoff 04 demands
   OEA=OEB=STPD=0 with nothing floating. Both are satisfied: OEA# (42) and OEB# (6) both sit
   on `ADC_OE_N` with **R44 = 10 kΩ to GND**, STPD (45) sits on `ADC_PDWN` with
   **R45 = 10 kΩ to GND**. Default (FPGA unconfigured, IOs high-Z) = outputs enabled,
   normal operation. Hard-tying to GND instead would have left both interface nets
   single-pin and stranded the FPGA drivers.
5. **Three datasheet-mandated parts were not in the sourced BOM and are added here**
   (TI SBAS295A Figure 21 / Pin Functions table): **R41 = 56.2 kΩ ISET** (sets the ~20 µA
   internal bias — a hard functional requirement, not a pull-down; TI: "deviating from this
   resistor value alters and degrades device performance"), and **R42/R43 = 2 Ω** in series
   with the REFT/REFB reservoirs. See `## Carried forward` — these need BOM/sourcing lines.
6. **Ref designators R41–R45 invented** (all five discretes above). Chosen inside the
   **41–55 band this block already owns** via `C41–C55`, precisely to avoid colliding with
   another block coder reaching for `R20+`. No other artifact mentions any R above R19
   outside the `R1xx`/`R2xx` AFE bands.
7. **Reference/CM network follows TI Figure 21 exactly**: 0.1 µF at REFT (C50) and REFB
   (C52) directly at the pins, then 2 Ω (R42/R43) into 2.2 µF reservoirs (C51/C53).
   CM (52) carries 1 µF (C54, per Figure 20's VOCM treatment) + 100 nF (C55).
8. **U5 is wired by pin number, not pin name, throughout.** The generated symbol's names
   contain regex-significant characters (`INA+`, `OEA#/SCLK`, `D0_B(LSB)`, `INT/EXT#`) that
   SKiDL's name lookup would treat as patterns. Every number carries the datasheet name in
   a comment. Do not "clean this up" into name lookups.
9. **Bus↔pin mapping**: `adc_d1` = **channel A** (D0_A..D11_A = pins 27..38, bit 0 = LSB),
   `adc_d2` = **channel B** (pins 10..21). Channel A inputs are `in1_p/in1_n` (pins 50/51),
   channel B `in2_p/in2_n` (pins 63/62). Arrays RA1–RA3 damp ADC_D1, RA4–RA6 damp ADC_D2;
   `Device:R_Pack04` element *n* spans pins *n* and *9−n*.
10. **OVRA (39), OVRB (9), DVA (26), DVB (22) → `NC`**, deliberately: no overrange or
    data-valid line reaches the FPGA in this architecture (capture is on `ADC_CLK`).

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/adc_dual.py` | The block, `@SubCircuit adc_dual(...)` | Assembling `__main__.py` |

## Next phase must

1. Emit exactly this call (keyword form, as written — no positional call):

```python
adc_dual(in1_p=CH1_P, in1_n=CH1_N, in2_p=CH2_P, in2_n=CH2_N,
         adc_clk=ADC_CLK, adc_d1=ADC_D1, adc_d2=ADC_D2,
         adc_oe_n=ADC_OE_N, adc_pdwn=ADC_PDWN, vocm=VOCM,
         v3v3_a=NET_3V3_A, v3v3_adcd=NET_3V3_ADCD, gnd=GND,
         tag='adc_dual')
```
   with `ADC_D1 = Bus('ADC_D1', 12)` and `ADC_D2 = Bus('ADC_D2', 12)`.
2. Set `.drive = POWER` at top level on **`+3V3_A`**, **`+3V3_ADCD`** and **`GND`** — this
   block only consumes all three (they reach U5 as `power_in` pins with no driver here).
3. Do **not** set `.drive` on `VOCM`, and do not add a second VOCM source anywhere: U5.CM
   drives it and `afe_channel` senses it.
4. Expect **27 parts / 24 internal stub nets** from this block (`ADC_D1_S0..S11`,
   `ADC_D2_S0..S11`, plus `ADC_REFT`, `ADC_REFB`, `ADC_REFT_RES`, `ADC_REFB_RES`).
5. The block in isolation reports **0 ERC errors / 39 warnings**, every warning being a
   one-pin or undriven interface net (`CH1_P/N`, `CH2_P/N`, `ADC_D*`, `ADC_CLK`, …) that
   closes once `afe_channel`, `clock_20m` and `fpga_core` are wired in. Anything else on
   these refs is new.

## Carried forward

- **BOM/sourcing gap (must be closed before ordering)**: R41 (56.2 kΩ ±1 %, 0603),
  R42/R43 (2 Ω, 0603), R44/R45 (10 kΩ, 0603) and C51/C53 (**2.2 µF X7R, 0805**) have **no
  MPN or LCSC number** — `sourced_bom.md` § adc_dual lists only U5, RA1–RA6 and a
  100 nF/10 µF/1 µF cap mix. All six values are commodity JLCPCB Basic parts; no MPN is
  asserted here because none was verified. R41 is *not* optional.
- **`net_plan.md` calls `VOCM` "≈1.65 V"; the ADS5231 datasheet says CM is typ +1.50 V**
  and that inputs "should be biased to the recommended common-mode voltage (1.5 V)". The
  ADC's own buffer sets it, so this block cannot be wrong — but `afe_channel`'s output
  common-mode budget and any headroom arithmetic done against 1.65 V should be rechecked.
- **MSBI=0 (offset binary) was not cross-confirmed against `fpga_core`'s capture logic** —
  handoff 04 asked for that confirmation; no block coder can see another block's code.
  It is a strap change (pin 41 to `+3V3_A`), not a layout change, if firmware wants two's
  complement.
- **CM drives 1.1 µF here plus both THS4551 VOCM inputs** in `afe_channel`. TI's Figure 20
  shows 1 µF on that node, so this is datasheet-sanctioned, but the CM buffer is only a
  ±2 mA part — if `afe_channel` adds further bulk on `VOCM`, total capacitance should be
  reviewed for buffer stability.
- Decoupling assumed **entirely local to this block** — the assembler need not add any
  bypass for U5; rail-level bulk on `+3V3_A` / `+3V3_ADCD` belongs to the power blocks.
- The 20 MSPS + host-2:1-decimation clocking scheme was **not re-opened** (work order
  instruction), including the PLL-disabled 10 MSPS alternative flagged in handoff 04.

## Do not redo

- The straps in Decision 3/4 and the Figure-21 reference network (Decision 7) — both come
  straight from TI SBAS295A, verified against `datasheets/ADS5231IPAGT.pdf`.
- Pin-number-based wiring (Decision 8) and the bus↔channel mapping (Decision 9).
- The ADC minimum-clock question — closed in handoff 04 Decision 1.

## Receipt

- Block: `adc_dual` → `circuits/dual_adc_usb/adc_dual.py`
- Parts: **27** (U5, RA1–RA6, R41–R45, C41–C55). Internal nets: **24**.
- Compile: **OK** (`py_compile`). Instantiation smoke test: **OK**, 0 ERC errors.
- Footprints: **6/6 valid** against the KiCad 9 libraries.
- Signature changed: **no**.
- Open: 6 unsourced commodity values (R41–R45, 2.2 µF), listed under Carried forward.
