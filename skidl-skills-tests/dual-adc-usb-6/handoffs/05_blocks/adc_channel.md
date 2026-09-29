---
phase: 05_blocks/adc_channel
agent: skidl-block-coder
circuit: dual_adc_usb
written: 2026-09-21T00:00:00Z
status: complete
revision: 1
next_phase: 05_coding
---

# Block handoff — adc_channel

## Decisions

1. **Signature unchanged from the work order, verbatim:**
   `adc_channel(ch, ain_p, ain_n, clk_adc, data, otr, pdwn, avdd, dvdd, gnd)`.
   No parameter renamed. **One** parameterised file, instantiated twice.
2. **`ch` is the instance selector, `'CH1'`/`'CH2'`** (int `1`/`2` also works).
   Refdes bank `b = 100*n + 50` → 150/250; net prefix `CH1_`/`CH2_`.
3. **Net directions.** `data[11:0]` and `otr` are **driven by this block** (ADC CMOS
   outputs). `ain_p`/`ain_n`, `clk_adc`, `pdwn` are **sensed only** (inputs). `avdd`,
   `dvdd`, `gnd` are **consumed only** — this block never drives a rail.
4. **`data` is indexed `data[0]`…`data[11]`, bit 0 = D0 = LSB.** Pass a 12-wide SKiDL
   `Bus` (any 12-element indexable of Nets works).
5. **DRVDD (pin 16) is fed from `dvdd` (+3V3D), not from `avdd`.** `net_plan.md` is
   self-contradictory here: its power table (line 15) says `+3V3A_ADC → U150 AVDD/DRVDD`,
   but its own block interface list (line 96) and the handed-down signature both carry
   **two** rails, and DRVDD is the only pin in this block that `+3V3D` could reach.
   Took the block-specific statement. It is also the correct choice electrically — the
   12 output drivers switch into the FPGA whose VCCO is `+3V3D`, so keeping that current
   off the 55 mA analog LDO avoids dumping digital switching noise onto the reference
   rail. **If review prefers net_plan's power table, this is a one-line change** (swap
   `dvdd += U[16]` to `avdd += U[16]` and move `C{b+2}`/`C{b+9}` onto `avdd`); `dvdd`
   would then be an unused parameter.
6. **MODE2 (1) and OE (3) share ONE strap node, `CHn_MODE_STRAP`, pulled to GND through
   the single allocated resistor R150/R250 (10 kΩ, BOM value kept).** Sourcing allocated
   exactly one resistor per channel but the mitigation needs *both* pins DNP-able, so
   they were combined: de-populating R150 leaves pins 1 and 3 connected only to each
   other and to one unpopulated pad — no DC tie anywhere. See Carried forward.
7. **R150/R250's function is CONFIRMED as the MODE2/OE strap** (closes phase-4 `Next
   phase must` #5 and the `AD9237BCPZ-40_SUMMARY.md` hypothesis). They are the only
   resistors in the block, and MODE2/OE are the only pins in it that need a strap which
   must be removable for the second source. Nothing else in `net_plan.md`'s
   `adc_channel` net list wants a resistor. Value stays at the 10 kΩ placeholder — these
   are static high-impedance DC inputs, and 10 kΩ puts the node far inside the AGND
   decode band (decode bands are ~AVDD/6 ≈ 550 mV wide).
8. **Strap levels chosen, from the datasheet's own pin-function tables (p. "PIN FUNCTION
   DESCRIPTIONS", read directly this pass):**
   - `MODE2 = AGND` → SHA gain 2, auto power control disabled. With the internal 1.0 V
     reference this gives a **2 Vp-p differential span** — the Analog Input table row
     "Input Span, VREF = 1.0 V; MODE 2 = 0 V → 2 Vp-p". This is exactly the span
     `net_plan.md` specifies and what the `analog_frontend` FDA delivers. `MODE2 = AVDD`
     would give 4 Vp-p and lose 6 dB of range — **do not "simplify" this tie to AVDD.**
   - `OE = AGND` → outputs permanently enabled (active low; each ADC has its own
     dedicated FPGA bus, nothing is multiplexed).
   - `MODE (22) = AGND` → **offset binary**, duty-cycle stabilizer **disabled**. DCS buys
     nothing from a ≤1 ps-jitter XO running the part at 1/4 of its rated rate.
   - `SENSE (23) = AGND` → internal 1.0 V reference.
   MODE and SENSE are real pins on the AD9235 too, so they tie to GND **directly**, with
   no DNP resistor.
9. **`PDWN` is wired as a plain FPGA-driven CMOS net.** The pin is really 3-level
   (AGND = run, 1/3·AVDD = standby, AVDD = full power-down); the FPGA can only reach the
   two rail levels, so standby mode is unreachable by design. Low = running.
10. **Pins 5 and 6 (DNC) are left genuinely unconnected**, per the datasheet and per the
    second-source strategy.
11. **EP (pin 33) tied to `gnd`** — required by the LFCSP thermal/ground pad note.
12. **Cap allocation is mine.** `sourced_bom.md` groups C150–C157/C250–C257 under the
    generic 100 nF bucket and C158–C161/C258–C261 under 10 µF. Assigned as:
    `C{b+0}`/`C{b+1}` 100 nF at AVDD pins 27/32; `C{b+2}` 100 nF at DRVDD 16; `C{b+3}`
    100 nF on VREF; `C{b+4}`/`C{b+5}` 100 nF on REFT/REFB; `C{b+6}` 100 nF **across
    REFT–REFB**; `C{b+7}` 100 nF +3V3A_ADC block entry; `C{b+8}` 10 µF AVDD bulk;
    `C{b+9}` 10 µF DRVDD bulk; `C{b+10}`/`C{b+11}` 10 µF REFT/REFB bulk. This satisfies
    `net_plan.md`'s "VREF + 0.1 µF" and "REFT/REFB decoupling 0.1 µF + 10 µF" exactly.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `circuits/dual_adc_usb/adc_channel.py` | The `@SubCircuit` block — 14 parts / 22 nets per instance | Assembling the circuit |

## Next phase must

1. Emit exactly these two calls (keyword args, `tag` per instance):

```python
adc_channel(ch='CH1', ain_p=CH1_AIN_P, ain_n=CH1_AIN_N, clk_adc=CLK_ADC,
            data=ADC1_D, otr=ADC1_OTR, pdwn=ADC_PDWN,
            avdd=V3V3A_ADC, dvdd=V3V3D, gnd=GND, tag='adc_ch1')
adc_channel(ch='CH2', ain_p=CH2_AIN_P, ain_n=CH2_AIN_N, clk_adc=CLK_ADC,
            data=ADC2_D, otr=ADC2_OTR, pdwn=ADC_PDWN,
            avdd=V3V3A_ADC, dvdd=V3V3D, gnd=GND, tag='adc_ch2')
```

2. `ADC1_D` / `ADC2_D` must be `Bus('ADC1_D', 12)` / `Bus('ADC2_D', 12)`, bit 0 = LSB.
3. **`.drive = POWER` at top level on `GND`, `+3V3A_ADC` and `+3V3D`** — this block only
   consumes all three.
4. **Pass the *same* `CLK_ADC` net object to both instances.** SPEC F13 (≤100 ns
   channel-to-channel skew) is met by the shared clock; do not give each channel its own.
   Likewise `ADC_PDWN` is one net for both ADCs.
5. Run with `KICAD9_SYMBOL_DIR` including `$PWD/symbols` — the ADC comes from the
   project library `dual_adc_usb`.
6. Expect ERC to note **no driving pin on `CH1_VREF`/`CH2_VREF`** if it reads pin 24 as
   passive — VREF is an output of the ADC's internal reference in this mode, not a
   floating node. Same for `CHn_REFT`/`CHn_REFB`.

## Carried forward

- **NAMED ASSUMPTION (unclosed, from `handoffs/04_datasheets.md` § Unverified keystone
  facts): AD9235's DNC pins 1/3 are assumed NOT to tolerate an externally-applied static
  DC tie.** The board is built with AD9237BCPZ-40 (U150/U250); AD9235BCPZ-40 is the
  second source only. Mitigation implemented as agreed: MODE2 and OE reach GND *only*
  through R150/R250, so **an AD9235 build de-populates R150/R250** and both pins float.
  This is an assumption, not a settled fact — ADI has not stated DNC-pin tolerance in
  either datasheet.
- **The mitigation is one resistor short of ideal.** With a single resistor per channel,
  MODE2 and OE must share a strap node, so on an AD9235 build they end up shorted to each
  other (a floating two-pin island) rather than each individually floating. If the
  architect wants them fully independent, allocate a second resistor per channel
  (R151/R251) and re-invoke; I did not invent a refdes to do it unilaterally.
- **DRVDD rail conflict inside `net_plan.md`** — see Decisions #5. Resolved in favour of
  `+3V3D`; flagged for review because net_plan's power-rail table says otherwise and the
  +3V3A_ADC 55 mA budget was sized as if it carried the whole part.
- **No decoupling is assumed to come from elsewhere** — every supply and reference pin in
  this block is bypassed locally here.
- Decoupling values/MPNs taken from the BOM's generic buckets: 100 nF →
  `CL05B104KB54PNC` 0402; 10 µF → `CL21A106KAYNNNE` 0805.

## Do not redo

- The AD9237 strap levels in Decisions #8 — read off the datasheet's own pin-function
  tables this pass, and MODE2 = AGND is load-bearing for the 2 Vp-p span. Do not change.
- R150/R250's function — confirmed, no longer a placeholder question.
- Data-pin numbering: D0–D7 = pins 7–14, D8–D11 = pins 17–20. Addressed by number
  because the symbol names them `D0(LSB)`/`D11(MSB)`.

## Receipt

- Block `adc_channel` — 1 file, parameterised, instantiated twice.
- 14 parts / 22 nets per instance (28 parts total; 16 instance nets + 6 shared).
- `py_compile` OK. Smoke-instantiated twice: refs land exactly on U150/R150/C150–C161
  and U250/R250/C250–C261 — zero SKiDL `_1` uniquification, zero collisions.
- `validate-footprints.py`: ✓ all 4 distinct footprints valid.
- Signature changed: **no**.
- ERC not run (assembler's job).
