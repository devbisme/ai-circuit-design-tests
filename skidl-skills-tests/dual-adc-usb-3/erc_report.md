# ERC & footprint review — dual_adc_usb (revision 2, post-fix)

**0 errors, 0 warnings, 1 note. Circuit is PASS.**

Both HIGH findings from revision 1 are fixed and independently re-verified; all four MEDIUM
findings are fixed. Export is unblocked.

| Gate | Result |
|---|---|
| `ERC()` | 0 errors, 0 warnings (`__main__.erc`) |
| Netlist / XML generation | 0 errors, **1** warning (445 in rev 1) — see Note N1 |
| `validate-footprints.py` | **67/67** resolve, 10 files (65 in rev 1; +FB6, +C106) |
| Netlist reproducibility | **byte-identical across two consecutive runs** (md5 `d32d36f1…`) |
| Netlist structure | 218 components, 136 nets, 0 single-node, 0 multi-driver, 0 duplicate refs, **0 non-standard refdes** |
| U12 pin coverage | 70 netted + 19 explicit NC = 89/89 |

---

## H1 — anti-alias filter: FIXED, verified independently

`analog_frontend.py` now builds the classic MFB. Confirmed from the *netlist*, not the source:

* `CH1_MFB_P` = R118 (Rg 1k) + R120 (Rf 1.1k to FB+) + R122 (R3 1k to IN−) + **C141 (30 pF)
  differential to `CH1_MFB_N`** — C1 is across the two node-A's, as it must be.
* `N$41` = C139.1 + R122.2 + U108.3 (IN−), `N$43` = C139.2 + R120.1 + U108.4 (FB+) — **C2
  (22 pF) runs amplifier input → feedback-sense pin**, which is the second-order path that
  was missing. Feedback polarity still correct (FB+ → node A+ → IN−).
* CH2 mirrors it exactly (C239 22 pF, C241 30 pF, R218/R220/R222).

I re-solved the network from scratch — full 6-node differential MNA with an ideal FDA, values
read out of the netlist, not from the handoff — and cascaded it with the Sallen-Key
(R116=R117=324 Ω, C136=330 pF, C137=47 pF):

| f | FDA stage | + Sallen-Key | requirement |
|---|---|---|---|
| 4 MHz | −4.97 dB | **−2.65 dB** | F6: −3 dB at 4 MHz — **met** |
| 10 MHz | −16.23 dB | **−31.43 dB** | F7: ≥30 dB — **met**, 1.4 dB margin |
| 20 MHz | −27.48 dB | **−55.44 dB** | F7: ≥50 dB — **met**, 5.4 dB margin |

Cascade f−3dB = 4.08 MHz, maximum passband peaking +0.19 dB, DC gain 1.10 (unchanged, so the
±10 V → 2 Vpp differential full-scale mapping still holds). The MFB stage alone is genuinely
2nd-order now (f0 = 1/(2π·√(2·C141·C139·R120·R122)) = 4.18 MHz, f−3dB 3.01 MHz, no peaking →
Q ≈ 0.54).

**These numbers reproduce the coder's claim to within 0.05 dB at every frequency, from an
independent model.** The margin at 10 MHz is 1.4 dB and depends on real capacitor tolerance:
C141 and C139 at ±5 % move f0 by roughly ±2.5 %, which is worth ~0.4 dB at 10 MHz. It clears,
but it is not comfortable — `design_risks.md` R4 already called this stopband thin.

## H2 — ADC clock over abs max: FIXED, verified

`CLKBUF_VDD` = FB6.2 + C72 (100 nF) + C106 (10 µF) + U11.5, with FB6.1 on `+3V0A`. The
fanout buffer's rail is now AVDD-referenced, so `CLK_ADC1`/`CLK_ADC2` reach at most 3.00 V
against the AD9235's `CLK ≤ AVDD + 0.3` = 3.30 V — 300 mV of margin where rev 1 had −18 mV.

Both directions of the level question check out against datasheets on disk:

* **3.3 V into a 3.0 V-powered buffer is fine.** SN74LVC2G34: *"Inputs Accept Voltages to
  5.5 V"*, *"Can Be Used as a Down Translator to Translate Inputs From a Maximum of 5.5 V
  Down to the VCC Level"*; VI abs max 6.5 V independent of VCC. Y1 stays on `+3V3`.
* **3.0 V out is still a valid logic high for the only thing it drives.** U11's outputs go
  nowhere but `CLK_ADC1`/`CLK_ADC2` → U9.2/U10.2, and the AD9235 logic-input spec is
  VIH ≥ 2.0 V. No other load exists on those nets.
* **Nothing that needs 3.3 V got demoted.** `CLK_FPGA` is tapped from `CLK_XO` *ahead* of the
  buffer (R32.1 on `CLK_XO`, R32.2 → U12.35), so the FPGA still sees a 3.3 V swing on a
  Bank-2 (3.3 V) global clock pin. `CLK_XO` = Y1.3 (OUTPUT) + U11.1 + U11.3 + R32.1 — one
  driver, three loads, as designed.

## M1-M4 — all fixed, verified

* **M1** — zero non-standard refdes in the netlist. CH1 is the 100-series (U107, U108, J102,
  R113-R125, C134-C147), CH2 the 200-series. No duplicates; no collision with the existing
  C100-C106 range.
* **M2** — 445 generation warnings → 1, and two consecutive runs produce an identical
  netlist (md5 `d32d36f10ff8806884ca025406579136` both times). `_stabilize_tags()` deriving
  the tag from the refdes is the right identity to hang a UUID on: a part keeps it as long
  as its refdes is stable, which is what "update PCB from schematic" needs.
* **M3** — `LED_CAP_N` = D6.2 + **U12.75**. UG803 QN88P: `IOT38A  I/O  1  …  75  75` →
  **Bank 1**, powered from VCCIO1 (pin 58) = `+3V3`. Confirmed the LED's 3.3 V pull-up now
  sits on a 3.3 V bank. Pin 11 (IOL16B, Bank 3) is back in the NC set and is listed as spare
  with its bank annotated. No 3.3 V node touches Bank 3 anywhere in the netlist now.
* **M4** — the duplicate 100 k on PWR_EN is gone; R6 in `power_digital` is the only one.

## Note

* **N1** — the single remaining generation warning is `Missing tag on  instantiated at
  <frozen importlib._bootstrap>:491`: the top-level circuit object, not a component. It does
  not affect the netlist, which is byte-stable. Informational.

## Still open (unchanged from rev 1, none blocking)

| Sev | Item |
|---|---|
| LOW | **L1** VCM divider 10k/10k (~5 kΩ) into two VOCM pins; CM may sit tens of mV off 1.500 V. VOCM input resistance not confirmed from the datasheet — uncertain. |
| LOW | **L2** FB1 (600 R, 500 mA rated) carries the whole board's VBUS current. |
| LOW | **L3** Firmware must assert PWR_EN before enabling FX2 slave-FIFO drivers, or U13 drives an unpowered U12. |
| LOW | **L4** Bead footprint strings inconsistent (`Resistor_SMD:R_0603` on FB1/FB2/FB3/FB6 vs `Inductor_SMD:L_0603` on FB4/FB5). Same land pattern. |
| LOW | **L5 (new)** `sourcing/sourced_bom.md` still names U7/U8/J2/R13-R27/C34-C47 for the front end; the netlist now uses the 100/200-series. Quantities are unaffected (still ×2) — a documentation-sync item for purchasing. |
| LAYOUT | **L6 (new)** U11 now switches on the analog rail. FB6 + 100 nF + 10 µF isolate the supply, but the buffer's ground return shares the single GND plane — keep it away from the ADC reference pins (the coder recorded the same trade-off). |
| LAYOUT | Carried from phase 5: **J2 BNC footprint is wrong** (now J102/J202), SiT1602BI pinout unverified, MODE0/MODE1 straps unconfirmed against DS117E, GW1NR-9 EP 6.8 mm vs footprint 6.74 mm, 1.8 V JTAG programmer setting. |

## Summary table

| Finding (rev 1) | Sev | Status |
|---|---|---|
| H1 AAF 1st-order, SPEC F7 missed | HIGH | **fixed**, re-derived independently: −31.4/−55.4 dB |
| H2 ADC CLK above abs max | HIGH | **fixed**, 300 mV margin, both level directions checked |
| M1 `_1` refdes | MED | **fixed**, 0 non-standard refs |
| M2 unstable netlist UUIDs | MED | **fixed**, byte-identical across runs |
| M3 3.3 V pull-up on Bank-3 pin | MED | **fixed**, moved to pin 75 (Bank 1, confirmed in UG803) |
| M4 duplicate PWR_EN pull-down | MED | **fixed** |
| L1-L4, L5-L6 (new) | LOW | open, none blocking |
