# ERC Report — dual_adc_usb

**Revision 2** — re-gated after the HIGH-1 and MED-2 fixes. Revision 1's verification of
the two coder claims, the reproducibility check, the exposed-pad check and the anti-alias
recomputation all still hold and were not redone; they are retained below unchanged.

**0 errors, 0 warnings, 5 notes. Circuit is PASS.**

HIGH-1 is closed and independently re-verified — including the coder's *audit* claim, not
just the one line it changed. MED-2 is closed. Nothing remaining blocks export.

| Gate | Result (revision 2) |
|---|---|
| `ERC()` | **0 errors, 0 warnings** — re-run independently |
| Netlist/XML generation | 1 benign warning (root hierarchy node — Claim 2, unchanged) |
| `validate-footprints.py` | exit 0, 61 strings across 9 files — resolution only, not a package gate |
| `validate-bom.py` | exit 0, **170 parts** / 67 rows, same 8 package notes (C88 added none) |
| Reproducibility | two fresh runs **byte-identical** ignoring `(date …)` |
| Refdes integrity | **170 components, 170 unique**, no duplicates, no `_1` suffixes |
| Exposed pads | U5 pad 89 present and on `GND` — unchanged |

---

## Revision 2 — verification of the two fixes

### HIGH-1 — CLOSED. The audit claim is true, verified independently of the coder.

The one-line fix is in place (`fpga_core.py:140` → `p1v8 += j3[1]`), and the netlist agrees:
`P1V8: [C511.1, C512.1, C513.1, **J3.1**, R53.2, U15.6, U5.12]`.

But the instruction was to verify the *audit*, not the line — I found this defect precisely
because the block contradicted itself, so the real question was whether any other 3.3 V
assumption about BANK3 survived. I enumerated **every** IOL pin from the symbol and resolved
each one against the netlist mechanically, rather than reading the coder's list back:

```
pin  3 IOL2A                     -> NC          pin 10 IOL14A_DONE      -> NC
pin  4 IOL5A_JTAGSEL_N_LPLL_T_in -> NC          pin 11 IOL15A_GCLKT_6   -> NC
pin  5 IOL11A_TMS                -> N$34 (J3.4) pin 13 IOL22A           -> NC
pin  6 IOL11B_TCK                -> N$33 (J3.3) pin 14 IOL22B           -> NC
pin  7 IOL12B_TDI                -> N$35 (J3.5) pin 15 IOL26A           -> NC
pin  8 IOL13A_TDO                -> N$36 (J3.6) pin 16 IOL26B           -> NC
pin  9 IOL13B_RECONFIG_N         -> N$37 (R53.1)
VCCIO3 (pin 12) -> P1V8
BANK3 pins on a 3.3 V net: NONE
```

All 13 IOL pins accounted for. Five are used (5–8 JTAG, 9 RECONFIG_N); every one is now
referenced to `P1V8` = VCCIO3, via `J3.1` and `R53.2` respectively. Eight are NC. **Zero
BANK3 pins touch `P3V3D`.** I also swept every U5 signal pin for a 3.3 V/1.8 V rail
mismatch and found none. The audit claim holds.

The three failure modes from revision 1 are all resolved by the same change: the pod now
self-references to 1.8 V, so TCK/TMS/TDI no longer overdrive the 2.1 V abs max; TDO's
1.8 V swing is now matched to a 1.8 V pod reference; and a pod attached at plug-in can no
longer back-power the BANK3 / PSRAM rail, since its reference rises *with* VCCIO3.

The corrected docstring is accurate. One wording nit, not a finding: the line "Every user
signal below lands on an IOB/IOR/IOT pin" is still loose — the JTAG signals land on IOL
pins — but the very next sentence states that explicitly and correctly, so no reader can
be misled.

### MED-2 — CLOSED, implemented as recommended.

`VBUS_SW: [C72.1, C74.1, **C88.1**, FB1.1, U10.1, U10.4, U11.1, U11.4, U12.1, U12.3, U9.6]`
with `C88.2` on `GND`. C88 = 100 nF 0402 at U12's VIN, exactly at the pin U12 shares with
the two 1.5 MHz switchers. U9/U10/U11 correctly left bare per the split in revision 1.

### What the fixes could have disturbed — checked, nothing did

- **`P1V8` gained a load (J3.1).** This rail is behind U15's CT-limited 260 µs ramp, which
  is the subject of the standing bench item, so it was worth checking. A JTAG pod's
  reference pin is a high-impedance sense input (typically well under 1 mA) and a TPS22918
  is a 2 A switch whose ramp is gate-slew-controlled rather than current-limited. No effect
  on the ramp. **One refinement to the bench item below.**
- **`P3V3D` lost a load (J3.1).** Trivial — a buck output with 22 µF of bulk.
- **`VBUS_SW` gained 100 nF (C88)** against ~60 µF already present: +0.17 %. U9's inrush
  arithmetic (60 µF × 5 V / 2 ms = 150 mA, post-enumeration) is unchanged.
- **Net naming did not shift.** `N$33`–`N$43` map to exactly the same pins as in revision 1,
  so LOW-2 is unchanged and the netlist stayed reproducible.
- **ERC stayed 0/0** — no new drive or conflict warning from either edit.

---

## Verification of the coder's claims (revision 1 — retained, still valid)

### Claim 1 — EEPROM bus pin-function override: **ACCEPTED, verified on all three legs**

The claim was that `U6['EECS'].func` / `U6['EECLK'].func = Pin.types.OUTPUT` corrects a
symbol metadata defect rather than silencing a real warning. All three parts hold:

1. **Electrically true.** The FT232H is the Microwire bus master for its configuration
   EEPROM: it generates EECS and EECLK at power-up and reads the 93LC56B. FTDI's own pin
   table types pin 44 (EECLK) and pin 45 (EECS) as *outputs* and pin 43 (EEDATA) as
   bidirectional. The 93LC56B's CLK and CS are device inputs. `Interface_USB:FT232H`
   declaring 44/45 as INPUT is the defect; the code is right and the symbol is wrong.
2. **Nothing was suppressed.** `grep -rn "do_erc\|ERC_OFF\|erc_assert\|no_erc\|skip_erc"`
   over `circuits/` returns exactly one hit — a *comment* in `usb_bridge.py:205` recording
   that `do_erc = False` was rejected. No flag is set anywhere in the package.
3. **The nets remain checked, and the override propagates correctly.** From
   `outputs/dual_adc_usb.net`:
   - `EE_CS`: `U6.45` **OUTPUT** + `U7.5` INPUT
   - `EE_SK`: `U6.44` **OUTPUT** + `U7.4` INPUT
   - `EE_DI`: `U6.43` BIDIRECTIONAL + `U7.3` INPUT (never warned — the control)

   The pin numbers the coder predicted are the numbers the netlist carries. A second
   driver on either net would now raise an OUTPUT–OUTPUT **error** that the stock
   INPUT/INPUT declaration would have hidden, so the override makes ERC *stricter*, not
   quieter. This is the correct idiom and it also exports the right pin type to KiCad.

### Claim 2 — `Missing tag on … <frozen importlib._bootstrap>:491`: **ACCEPTED, benign**

Traced to `skidl/skidlbaseobj.py:262`, reached from `skidl/circuit.py:check_tags()`:

```
748:            part.check_tag(create_if_missing=True)
750:            node.check_tag(create_if_missing=False)
```

Parts get `create_if_missing=True`, which on a miss emits a **second** warning
(`Random tag … generated`). No such message appears, and all 169 parts are uniquely
tagged — so the one warning came from line 750, a **node**, with
`create_if_missing=False`. Its name renders empty (`Missing tag on  instantiated`),
matching the root hierarchy node. Because that path creates no random tag, nothing
non-deterministic enters the netlist, which the byte-identical two-run diff confirms.
Not reachable from `__main__.py`; it is a SKiDL-internal cosmetic warning. Confirmed.

### Claim 3 — the 8 package notes: **6 benign, 2 real**

| Ref | Judgement |
|---|---|
| X1 `SMD3225-4P` → `Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm` | **Benign.** 3225 = 3.2×2.5 mm, 4 pads. Industry-standard land pattern. Accept. |
| J3 `TH-1x6-2.54mm` → `PinHeader_1x06_P2.54mm_Vertical` | **Benign.** Exact match. Accept. |
| L71/L72 `0806-Shielded` → `L_Murata_DFE201610P` | **Benign-ish.** DFE201610P = 2.0×1.6 mm = 0806 imperial; correct size class. Sourced part is Walsin `WIP201610P-2R2ML`, not the Murata — same 2016 body, near-identical land. Low risk; `datasheets/WIP201610P-2R2ML.pdf` is on disk if anyone wants certainty. |
| U5 `QFN-88-8x8mm` → `QFN-88-1EP_10x10mm…` | **Stale BOM cell, code is right.** Gowin's own package drawing (UG119E Fig. 4-2: D=E=10.00, D2=E2=6.8, e=0.40) gives 10×10 mm; JLC's "8x8" string is wrong and `04_datasheets.md` already says so. Correct the BOM cell, never the footprint. |
| **J1/J2** `TH-Right-Angle-BNC` → `BNC_Amphenol_031-6575_Horizontal` | **REAL — see MED-1.** Sourced part is `KH-BNC50-3511`, not the Amphenol. |
| **J4** `SMD-16P-RightAngle` → `USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal` | **REAL — see MED-1.** Sourced part is `TYPE-C-16PIN-2MD073`, not the GCT. |

---

## Findings (revision 1 text, retained for the record — status updated)

HIGH-1 and MED-2 below are **CLOSED at revision 2**; their original analysis is kept
verbatim so the reasoning survives, with the fix verification in the revision 2 section
above. The rest are open and none of them block export.

### HIGH-1 — ✅ **CLOSED at revision 2.** The JTAG header drove 3.3 V into 1.8 V BANK3 pins.

`fpga_core.py` ties the JTAG header's reference pin to the 3.3 V rail and its four signal
pins directly to U5 pins 5/6/7/8. Those four pins are **BANK3 I/O**, powered by
VCCIO3 = pin 12 = `P1V8` = 1.8 V.

Evidence, three independent sources agreeing:

- **`datasheets/UG803_GW1NR9_Pinout.pdf`**, per-pin table (the column after `I/O` is the
  explicit BANK number):
  ```
  IOL11A/TMS   I/O   3   TMS   …  5
  IOL11B/TCK   I/O   3   TCK   …  6
  IOL12B/TDI   I/O   3   TDI   …  7
  IOL13A/TDO   I/O   3   TDO   …  8
  VCCIO3       Power N/A          12
  ```
  They are typed `I/O` — dual-function bank pins, **not** dedicated VCCX-referenced pins.
- **`GW1NR-LV9QN88PC6-I5_SUMMARY.md`**, which states the pairing is *verified, not
  inferred*: "BANK3→VCCIO3(12) [IOL* pins]", and "a bank cannot run part at 3.3 V and part
  at 1.8 V".
- **`outputs/dual_adc_usb.net`** — direct connections, no series resistance:
  `N$33: J3.3 ↔ U5.6` · `N$34: J3.4 ↔ U5.5` · `N$35: J3.5 ↔ U5.7` · `N$36: J3.6 ↔ U5.8`,
  with `J3.1` on `P3V3D` and `U5.12` on `P1V8`.

Three distinct failure modes:

1. **Overvoltage.** Abs max on a BANK3 pin is VCCIO3 + 0.3 V = **2.1 V**. A 3.3 V pod
   overdrives TCK/TMS/TDI by **1.2 V**, forward-biasing the bank's ESD structure.
2. **Programming cannot work even undamaged.** TDO drives out at VCCIO3 = **1.8 V** into a
   3.3 V pod whose V_IH is typically 2.0 V. The pod never reads a logic high.
3. **Back-powering at plug-in, the worst case.** `P1V8` is *deliberately the last rail up*
   (U14 → U15, 260 µs CT-limited). A pod attached at power-on drives 3.3 V into BANK3
   while VCCIO3 is still at 0 V, injecting current into an unpowered bank — the same rail
   that powers the in-package PSRAM die.

**Why this matters beyond the FPGA:** VCCIO3 powers the PSRAM, which *is* the 4 MB sample
buffer. SPEC F5/F6 (≥ 0.1 s at 10 MSPS × 2 ch = 4,000,000 bytes) has no other storage.
Damage here takes out a non-negotiable user number.

**The block contradicts itself**, which is what makes this a clear defect rather than a
judgement call. Forty lines below the JTAG wiring, the same file routes R53 to `P1V8`:

> `# Pin 9 is IOL13B_RECONFIG_N -- an IOL*, i.e. BANK3, pin. Its abs max is`
> `# VCCIO3 + 0.3 V = 2.1 V, so the pull-up goes to P1V8, NOT P3V3D`

Pin 9 is `IOL13B` — the *same bank, adjacent pin* to TDO on pin 8. The rule was applied to
pin 9 and not to pins 5–8, on the strength of a docstring claim ("Gowin's dedicated JTAG
pins are referenced to VCCX = 3.3 V") that UG803 contradicts. The docstring's summary
assertion "**No IOL pin carries a 3.3 V signal**" is false as wired.

**Fix — one line, no BOM change, no new refdes.** In `circuits/dual_adc_usb/fpga_core.py`:

```python
    # J3 pin 1 is the pod's I/O reference. U5 pins 5-8 (TMS/TCK/TDI/TDO) are IOL*
    # = BANK3, whose VCCIO is pin 12 = P1V8 (UG803 per-pin table, BANK column = 3).
    # A 3.3 V reference overdrives their VCCIO3 + 0.3 V = 2.1 V abs max and leaves
    # TDO's 1.8 V swing below a 3.3 V pod's V_IH. Same rail as R53 on pin 9, for
    # exactly the same reason.
    p1v8 += j3[1]
    gnd += j3[2]
```

replacing `p3v3d += j3[1]`. The pod then self-references to 1.8 V. Load is a few mA
through U15, far inside a TPS22918 — no interaction with the VCCIO3 ramp budget.

If a 3.3 V-only pod is a hard requirement instead, that is a BOM change (level shifter or
series resistors) and an architecture decision, not a coder fix.

**Owner: `skidl-block-coder`, `fpga_core` block.**

### MED-1 — Two connector footprints are cross-manufacturer substitutions

`validate-footprints.py` is green here and *cannot* be otherwise: it checks that a library
and a `.kicad_mod` exist, nothing about the sourced part's actual land pattern.

- **J1/J2** — sourced `KH-BNC50-3511` placed on `BNC_Amphenol_031-6575_Horizontal`.
  Right-angle BNC jacks differ between makers in centre-pin position and ground-leg
  spacing. Drawing: `datasheets/KH-BNC50-3511.pdf`.
- **J4** — sourced `TYPE-C-16PIN-2MD073` placed on `USB_C_Receptacle_GCT_USB4105-xx-A_16P`.
  USB-C receptacle land patterns are **not** interchangeable between manufacturers; shield
  leg and SMT pad positions vary. Drawing: `datasheets/TYPE-C-16PIN-2MD073.pdf`.

Both drawings are already on disk. Check before layout; a mismatch here is a scrapped board.

### MED-2 — ✅ **CLOSED at revision 2** (C88 added). U12 had no dedicated input capacitor.

I **agree** with the accepted disposition for U9/U10/U11 and **disagree** for U12.

- U9 is a load switch: its VIN is a DC node with a ~2 ms ramp and no switching currents.
  10 µF is ample. Fine.
- U10/U11: C72/C74 (10 µF 0805) *are* the hot-loop input caps and match TI's recommendation
  for TLV62569. A parallel 100 nF would help loop ESL but the 10 µF dominates. Acceptable.
- **U12 is different.** The netlist shows `VBUS_SW: C72.1, C74.1, FB1.1, U10.1/4, U11.1/4,
  U12.1/3, U9.6` — U12 has **no input cap of its own at all**, only whatever C72/C74 offer
  from across the node, and it sits on the input rail of two 1.5 MHz switchers. RT9013's
  PSRR is ~70 dB at 1 kHz but falls to roughly 20–30 dB by 1.5 MHz. Its output is `P3V3A`,
  which supplies the ADC's AVDD *and* both FDAs. At 12 bits, 1 LSB = 2 V / 4096 = 488 µV,
  so switching residue on this rail lands in the signal path against SPEC F10 (SNR ≥ 60 dB).

Recommend one 100 nF 0402 at U12's VIN, and preferably a 1 µF alongside it. That is 1–2 new
refdes against a "frozen" BOM — but the BOM already went to rev.4, so the freeze is a
convention, not a constraint. **Not a PASS blocker**; a measurable risk to a stated number.

### MED-3 — THS4521 inverting input under front-end overload (bench item, no action)

Under SPEC I3 (±55 V at the BNC), D101/D201 hold the divider tap at roughly ±5.1 V and the
AD8066 follower saturates near −4.5 V. The FDA summing node then sits at approximately
(−4.5 × 1.1 + 3.3) / 2.1 ≈ **−0.79 V**, against a THS4521 input abs max of (V−) − 0.7 V.
The node is held there by the FDA's internal input clamp, with current limited to about
4 mA by Rg = 1.00 kΩ — inside the ±10 mA input-current rating. So it survives *by clamp*,
not *by design*. No change recommended; verify overload recovery time on the bench.

### LOW-1 — VBUS bulk is 11 µF nominal against the 10 µF USB inrush convention

`VBUS` carries C83 (10 µF, `power_tree`) **and** C609 (1 µF, `usb_bridge`). `power_tree`'s
comment states C83 "is the whole 10 uF, so nothing else may be added to VBUS" — `usb_bridge`
added C609 without seeing that. A genuine cross-block coordination miss.

In practice this almost certainly passes: MLCC DC-bias derating at 5 V typically leaves a
0805 10 µF X5R delivering ~6–7 µF, so effective bulk is well under 10 µF. **No change
recommended**, but the two comments should stop contradicting each other.

### LOW-2 — 11 auto-named nets (`N$33`–`N$43`), all inside `fpga_core`

JTAG ×4, RECONFIG_N, MODE0/1, and the two LED chains. `fpga_core`'s docstring calls them
"JTAG_TCK/TMS/TDI/TDO … internal to this block", implying they were meant to be named
`Net(...)` objects. Deterministic today — the two-run diff is byte-identical — but a future
edit that adds a net can renumber them, and `N$34` tells a schematic reader nothing. Naming
them costs nothing.

### LOW-3 — U5's exposed pad is a single 6.8 × 6.8 mm paste aperture

`footprints/ProjectLocal.pretty/QFN-88-1EP_10x10mm_P0.4mm_Gowin_QN88P.kicad_mod` defines
pad 89 as one `6.8 6.8` opening on `F.Paste`. Dimensionally correct per UG119E, and it *is*
on `GND` — but a monolithic aperture that large will float the part and trap voids on
reflow. Segment the stencil (3×3 windows, ~50–60 % area coverage). This footprint is
custom-generated, so it carries no library vetting; call it out to the fabricator.

---

## Dispositions on the three accepted risks

### U15 ON tied to P1V8_PRE — **AGREE, keep as a bench-verify item**

The physical argument is sound, and I would add a mechanism the coder did not state: the
TPS22918's CT ramp is a current source charging C87, and the internal charge pump that
enhances the pass FET is itself powered from VIN — so the FET cannot turn on before VIN
exists, regardless of when ON is asserted. That is why the out-of-scope datasheet condition
does not bite here. The failure mode if it *is* wrong (VCCIO3 ramping faster than DS117's
10 mV/µs ceiling) is real, the bench criterion (≥ 180 µs monotonic) is the right one, and
the named fallback (10 k + 100 nF RC on U15.ON from P3V3D) is correct and cheap. Keep it.

Interaction worth recording: the HIGH-1 fix puts the JTAG pod's reference on `P1V8`, i.e.
downstream of U15. A pod draws a few mA — negligible for a TPS22918 and it loads the rail
only after it is up, so it does not disturb the ramp this risk is about.

### BAT54S clamp headroom (R-10) — **AGREE with accepting; DISAGREE with the framing**

The arithmetic is right and the conclusion is far less alarming than "negative margin
against an absolute maximum" makes it sound. Two things the risk register misses:

1. **The clamp and AVDD are the same net.** `P3V3A` carries `U4.3/46/57` (AVDD) *and*
   `D111.2/D112.2/D211.2/D212.2` (the clamp cathodes). The overshoot is therefore always
   exactly Vf above AVDD — the two **track**. It is never a fixed 3.7 V against a fixed
   3.6 V. No Schottky can satisfy a +0.3 V limit; BAT54S at 0.4 V @ 10 mA is as close as
   the part class goes, and the 0.3 V figure exists to keep the ADC's *internal* ESD diode
   off. A silicon junction needs ~0.7 V; the BAT54S conducts at 0.4 V and takes the current
   first. The clamp does its actual job.
2. **Nothing in the circuit can forward-bias it.** The only device driving these nodes is
   the THS4521, and it is powered from `P3V3A` too (`U2.3`, `U2.7`, `U3.3`, `U3.7`). Its
   output cannot exceed its own rail, so in every FDA-driven condition the ADC input stays
   at or below AVDD and the clamps never conduct at all. They matter only for ESD or
   hot-plug energy coupling through the LC filter.

**Recommend:** downgrade R-10 from "negative margin against an abs-max rating" to "clamp
tracks AVDD; no in-circuit source can forward-bias it," and **correct
`datasheets/BAT54S_SUMMARY.md`**, which currently records as fact that the part "holds
ADS5231 input pins inside AVDD+0.3V during overload." That is arithmetically impossible for
a 0.4 V Schottky and should not sit in a summary file as a verified claim.

### U9/U10/U11/U12 decoupling — **AGREE for U9/U10/U11, DISAGREE for U12.** See MED-2.

---

## Documentation defects

I agree with every disposition in `handoffs/doc_defects.md`. One correction of emphasis:
the U5 pin-12 symbol label (`VCCX_VCCO0` where UG803 says `VCCIO3`) was flagged as "the one
that could bite a future reader" — **it already bit this design**. The symbol carries no
bank information, so the coder reasoned about banks from pin-name prefixes: it got pin 12
right by explicit correction, and got the JTAG bank wrong (HIGH-1). Same root cause.

Recommend fixing the pin-12 name in `symbols/dual_adc_usb.kicad_sym` and, if cheap, adding
bank numbers to the IOL/IOB/IOR/IOT pin names so the next reader cannot repeat HIGH-1.

---

## Summary table (revision 2)

| # | Sev | Finding | Status | Blocks export? |
|---|-----|---------|--------|----------------|
| HIGH-1 | HIGH | JTAG header referenced 3.3 V into BANK3 (1.8 V) pins 5–8 | ✅ **CLOSED** — `p1v8 += j3[1]`; full IOL audit re-verified | — |
| MED-2 | MED | U12 (analog LDO) had no dedicated input cap between two 1.5 MHz switchers | ✅ **CLOSED** — C88 100 nF at U12 VIN | — |
| MED-1 | MED | J1/J2 and J4 on other manufacturers' land patterns | Open | **No** — layout-blocking |
| MED-3 | MED | THS4521 summing node ≈ −0.79 V under ±55 V overload; survives by internal clamp at ~4 mA | Open | **No** — bench item |
| LOW-1 | LOW | VBUS 11 µF nominal vs 10 µF; contradictory comments in two blocks | Open | **No** — doc only |
| LOW-2 | LOW | 11 auto-named nets `N$33`–`N$43` in `fpga_core` | Open | **No** — cosmetic, stable |
| LOW-3 | LOW | U5 EP is one 6.8 mm paste aperture; needs stencil segmentation | Open | **No** — fab note |
| doc | — | `BAT54S_SUMMARY.md` recorded an impossible clamp claim | ✅ **CORRECTED at revision 2** | — |

## Is anything still open export-blocking? No.

The coordinator asked me to say plainly whether the open items block export rather than
layout. They do not, and here is the reasoning rather than the assertion.

- **MED-1 (J1/J2, J4 land patterns) — layout-blocking, not export-blocking. I agree with
  the disposition, with one correction to its stated reason.** The reason given was that it
  "does not affect the netlist, which is what this pipeline exports." That is not quite
  right — the footprint string *is* in the exported netlist (`(footprint "…")` on every
  component) and travels straight into KiCad on import. What makes it non-blocking is
  different and stronger: **nothing downstream of export commits to copper.** A human opens
  the board, and swapping a footprint at that point costs minutes and no money. The error
  is fully recoverable right up until fabrication, and it is recorded in this report and in
  the handoff's Carried forward where the layout step cannot miss it. Export away.
- **MED-3 (THS4521 overload corner) — bench item.** It is a fault-condition margin under
  ±55 V abuse, it survives via the FDA's internal clamp at ~4 mA against a ±10 mA rating,
  and no netlist change would address it short of a BOM change. Not blocking.
- **LOW-1** is a comment contradiction between two blocks with no electrical consequence
  (MLCC DC-bias derating at 5 V almost certainly puts effective bulk under 10 µF anyway).
  **LOW-2** is cosmetic and verified stable across runs. **LOW-3** rides with the footprint
  to the fabricator, not with the netlist. None blocking.

**Verdict: PASS.** 0 ERC errors, 0 ERC warnings, clean `validate-footprints.py`, clean
`validate-bom.py` at 170 parts, netlist reproducible and refdes-unique. The one defect that
made revision 1 a FAIL is closed, and I verified the coder's *audit* — every BANK3 pin,
enumerated from the symbol and resolved mechanically against the netlist — not merely the
line it changed. Export is unblocked. Five open items are carried forward: one must be
resolved before layout, one before the board is trusted at its overload limit, three are
documentation and fabrication notes.
