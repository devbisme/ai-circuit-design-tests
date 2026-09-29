# ERC + design review — dual_adc_usb (re-gate, revision 2)

**0 errors, 2 warnings, 3 notes. Circuit is PASS.**

Every item behind the revision-1 FAIL is closed and independently verified in the built
netlist — not accepted from the change list. Netlist export is unblocked.

| Gate | rev.1 | rev.2 |
|---|---|---|
| ERC errors | 0 | **0** |
| ERC warnings | 2 (false positives) | **2 — same two, still false positives** |
| Footprints resolve | 25/25 | **25/25** |
| Footprints match the sourced package | **2 mismatches — FAIL** | **0 — PASS** |
| Symbol pins ⊆ footprint pads | ✓ | ✓ (incl. the new J1 ProjectLocal) |
| Refdes hygiene | ✓ 240 parts | ✓ **241 parts / 187 nets** |
| Exposed pads netted | 3/3 | 3/3 |
| Netlist byte-stability | **unaudited** | ✓ **verified identical** |

```
ERC WARNING: Insufficient drive current on net LDO_AMP_IN for pin POWER-IN pin 1/IN of TPS73633DBV/U6.
ERC WARNING: Insufficient drive current on net LDO_ADC_IN for pin POWER-IN pin 1/IN of TPS73633DBV/U5.
ERC INFO: 2 warnings found while running ERC.
ERC INFO: 0 errors found while running ERC.
```

---

## Revision-1 findings — all closed, each verified in the netlist

**HIGH-1 + HIGH-2 (BNC clamp) — CLOSED.** The BNC node is now clean:

```
CH1_BNC:   C100.1, J2.1(OUT), R100.1          <- jack + divider top leg only
CH1_BUFIN: D101.1(K), D100.3(C/A), R102.2, U100.3(+In)
```

Part changed to **ESD9L5.0ST5G** (LCSC C82326, verified live: onsemi, SOD-923, **0.9 pF**,
**unidirectional**, Vrwm 5 V, VBR 5.4 V, 92,164 in stock). Polarity is now load-bearing and
it is correct: `Device:D_Zener` pin 1 carries the name **`K`** in the symbol itself — I
checked the library, not the comment — and it lands on BUFIN with pin 2 on GND. Cathode on
signal is right for a unidirectional TVS; BUFIN's service range is 0.734–2.552 V, far below
the 5 V standoff, so it never conducts in service, and the −0.7 V fault case is pinned by
D100 regardless.

**The architect's justification for changing the part (rather than only relocating it)
checks out.** I recomputed it. Merely relocating the 15 pF part would put ~22.5 pF on BUFIN:

| C_node | −3 dB | 10 MHz | verdict |
|---|---|---|---|
| 22.5 pF — 15 pF part merely relocated | **3.996 MHz** | −34.4 dB | **fails F8 (≥4 MHz)** |
| 9.4 pF — rev.6 as built | **4.322 MHz** | −30.9 dB | **passes F8 and F9** |

3.996 vs a 4.000 MHz floor. The claim was right, and it was right by a hair.

**HIGH-3 (U31) — CLOSED.** `Package_SO:SOIC-8_5.3x5.3mm_P1.27mm` in the built netlist.
Correct 208-mil pattern for W25Q32JVSSIQ. U7 correctly left on the 150-mil body (TLV2372IDR
is the D package) — the fix was applied to the part that needed it and not blanket-applied.

**HIGH-4 (D101/D201 land pattern) — CLOSED.** `Diode_SMD:D_SOD-923` against a SOD-923 part.

**MEDIUM-5 (unsourced TVS) — CLOSED.** C82326, 92,164 live, plus a verified drop-in second
source (C7379964, MSKSEMI, 0.5 pF, same land pattern and polarity). The BOM now carries the
real 0.9 pF and a binding substitution constraint. The "≤0.5 pF" cell that hid a 15 pF part
for four phases is deleted rather than corrected in place — the right call.

**MEDIUM-6 (capacitive load on U7A) — CLOSED, and better than I asked.** I raised this as an
unproven risk. It came back with a datasheet citation (TI SLOS270F §8.3.2 / Figure 34:
RNULL ≥ 20 Ω above 10 pF; that net is 300 nF, 300× past the end of Figure 20's
characterisation). R19 = 22 Ω is placed with the feedback at the op-amp output and all the
capacitance on the load side — verified:

```
VREF_OFF_AMP: R19.1, U7.2(-), U7.1(out)        <- feedback taken here
VREF_OFF:     R19.2, C24.1, C113.1, C213.1, R101.2, R201.2, C101.2, C201.2
```

That is textbook RNULL. The recorded crosstalk consequence is honest: I get −78 to −81 dB
against their stated −75 dB (they used ±8.2 µA; the bottom legs actually swing −11.8/+8.2 µA,
so the real figure is slightly *worse* than their arithmetic but still ≈0.5 LSB). No spec
requires channel isolation. Accepted.

**MEDIUM-7 (J1) — CLOSED.** See note 3 below for the one loose end, which is documentation.

---

## New findings

### MEDIUM — 1. The attenuator compensation is 3.9 % out, and this is my miss from rev.1

Not a regression. It was there before this round of fixes and I did not catch it, because in
revision 1 I modelled the chain from `CHn_BUF` onward and treated the /11 divider as ideal.
The architect is right that R102 does not isolate BUFIN from the divider at the compensation
corner, and the consequence runs further than the −3 dB point.

The divider is compensated when `Rt·Ct = Rb·Cb`. Both are 20.0 µs by design. But C_node on
BUFIN appears across the bottom leg through a 1 kΩ that is negligible against an 82.6 kΩ
source, so the real bottom-leg time constant is `Rb·(Cb + C_node)`:

```
tau_top = 909k x 22p              = 20.00 us
tau_bot = 90.9k x (220p + 9.4p)   = 20.85 us     -> 4.2 % mismatch
```

That is a **−0.345 dB (−3.90 %) gain shelf between DC and ~1 MHz**, with the transition near
the 8.8 kHz corner. SPEC F12 wants gain accuracy within ±2 % FS. It is robust to the
uncertainty in C_node — the shelf is −2.5 % at 6 pF and −5.8 % at 14 pF, so it misses the
±2 % window across the whole plausible range.

**Why this does not block export.** F12 is **SOFT** and explicitly "before host-side
calibration". The error is a single first-order shelf at a known corner, so it is
characterisable and correctable in firmware — unlike a −3 dB point that lands below spec,
which is why F8 was worth blocking on and this is not. Worth recording is that relocating
the TVS *improved* this a lot as a side effect: it was −9.3 % with 22.5 pF on the node.

**Fix, if it is taken:** the bottom leg needs ~9.4 pF less fixed capacitance —
`Rb·(Cb + C_node) = 20.0 µs` gives `Cb = 210.6 pF`.

```python
    C_att_b = _c0603(ref=f'C{b + 1}', value='210pF')   # was 220pF; compensates C_node
```

210 pF is E96 and gives a 0.3 % residual. But a fixed value cannot track C_node's own
spread (BAV199 Cd tolerance, op-amp input C, layout stray), and SPEC I2's wording — "with a
trimmable compensation cap" — points at the better answer: a 200 pF fixed part in parallel
with a 5–20 pF trimmer. **That is an architecture call, not a coder call.** Either way it is
one passive on an existing refdes, and it is cheaper to decide now than after the boards are
made.

### LOW — 2. BOM and code disagree on the TVS symbol

`sourced_bom.md` row 46 specifies `Device:D_TVS`; `analog_frontend.py` instantiates
`Device:D_Zener`. Electrically irrelevant — both are 2-pin, pin 1 = cathode, so the netlist
is identical, and the reasoning for the swap is sound (D_TVS draws a bidirectional glyph
with pins named A1/A2, which lies about polarity on a part where polarity is now
load-bearing). But this is the same stale-row drift as OI-3 (Y1, `Crystal` vs
`Crystal_GND24`) and as the "≤0.5 pF" cell, both of which cost a phase. One-line BOM fix.

### LOW — 3. J1's BOM row still carries a reading that has been retracted

The engineering here is right and internally consistent — I checked all three artefacts
against each other. `datasheets/TYPE-C-16PIN-2MD-073_SUMMARY.md` carries an explicit
correction: the drawing's 1.70/1.40 callouts are the *lengths of 0.60-wide oval slots*, not
round-hole diameters, and the single real interference is the rear shield slot (generic
0.6×1.2 mm, this part 0.6×1.4 mm). The generated footprint matches that exactly — rear slots
drill `oval 0.6 1.4`, front `oval 0.6 1.7`, NPTH Ø0.65 at ±2.89.

`sourced_bom.md` row 26 still repeats the **retracted** "round mounting holes Ø1.70/Ø1.80"
reading and the retracted "oval slots at different offsets" claim, and still describes the
footprint as "(to be generated)" when it exists and is in use. Stale prose on a resolved
row. Fix before export writes a BOM from it.

---

## Re-verified this round

- **The 2 ERC warnings** are the same two, from the same cause, still correct to ignore.
  `LDO_ADC_IN` = {FB1.2, C11.1, U5.3/EN, U5.1/IN(PWRIN)}; ferrite pins are PASSIVE so
  `VBUS_SW.drive = POWER` cannot cross. Still do not suppress them.
- **Driverless census is now 58, and the shift is exactly right.** `VREF_OFF` joined the
  list (its driving pin moved behind R19) and `VREF_OFF_AMP` did not (U7.OUT drives it).
  That is the correct and expected consequence of adding RNULL. `__main__.py` was **not**
  given `VREF_OFF.drive = POWER`, so classification is preserved rather than suppressed —
  and the stale comment claiming U7.OUT drives VREF_OFF has been corrected. Nothing else in
  the census moved.
- **Netlist byte-stability — now audited and clean.** Two consecutive generations into the
  scratchpad (not `outputs/`) are **identical apart from the `(date …)` line**. This closes
  the item I flagged unaudited in rev.1. One benign netlist-generation warning appears —
  `Missing tag on <frozen importlib._bootstrap>`, the unnamed root node — which does not
  affect the output; export should expect it and not chase it.
- **Refdes hygiene:** 241 parts, 187 nets, no duplicates, no `_1` suffixes, no single-pin
  nets. The +1 part / +1 net over rev.1 is R19 and VREF_OFF_AMP. R19 was the spare the power
  block had already reserved, so no refdes churn.
- **Footprints:** all 25 resolve; every symbol pin number has a matching pad, including the
  new 22-pad J1 (17 named pads for 17 symbol pins, 4 stacked S1 shield slots sharing GND,
  2 unnamed NPTH). `validate-footprints.py` prints `✓ All footprints valid (63 checked)` —
  which, as established last round, proves only that paths resolve. The package match is
  what I checked, by hand, against the sourced MPN.
- **Unchanged and still clean** (not re-derived): supply spans, signal levels vs receiver
  rails, FPGA bank voltages, rail sequencing, exposed pads, Sallen-Key topology.

## Summary

| # | Sev | Where | Finding | Owner |
|---|---|---|---|---|
| 1 | MED | `analog_frontend.py` C_att_b / `net_plan.md` | Compensation 4.2 % out → −3.9 % DC-to-1 MHz gain shelf vs F12's ±2 % (SOFT). Pre-existing; my rev.1 miss | circuit-architect |
| 2 | LOW | `sourced_bom.md` row 46 | BOM says `Device:D_TVS`, code uses `Device:D_Zener` | part-sourcer |
| 3 | LOW | `sourced_bom.md` row 26 | J1 row repeats a retracted reading; says "to be generated" of an existing footprint | part-sourcer |
| — | LOW | U5/U6 | 2 ERC warnings — verified false positives, accepted | none |
