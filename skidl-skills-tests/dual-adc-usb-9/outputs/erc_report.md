0 errors, 2 warnings, 8 notes. Circuit is PASS.

Circuit: `dual_adc_usb` (modular, `circuits/dual_adc_usb/`), SKiDL 3.0.0, reviewed 2026-09-30.
Run: `KICAD9_SYMBOL_DIR="/usr/share/kicad/symbols:$PWD/symbols" python -m circuits.dual_adc_usb`
(5 runs; final run with `PYTHONHASHSEED=0` produced the current `outputs/dual_adc_usb.net` and
`outputs/dual_adc_usb_bom.xml`). 169 parts, 130 nets, 0 single-node nets, no `_1` refdes.

## Gate results

| Gate | Result |
|------|--------|
| ERC | `ERC INFO: No errors or warnings found while running ERC.` |
| Netlist / XML generation | 0 errors, 1 warning each (same root-node message, see W1) |
| `validate-footprints.py` | All 27 footprint strings resolve (incl. `ProjectLocal:KH-BNC50-3511`) |
| `validate-bom.py` | BOM agrees with circuit: 169 parts, 59 rows, 0 mismatches, 14 `?` package notes (all checked by hand, consistent) |
| Exposed pads | U9 QFN-88 pad 89 -> GND; U6 WSON-12 pad 13 -> GND. No other EP packages (U7 TQFP-64 PAG, U10 LQFP-48 have none) |
| Reproducibility | components + nets sections byte-identical across all runs; sheet order varies with hash seed (L1) |

## Findings (by severity)

### MEDIUM

**M1 — U10 FT232H VREGIN below recommended minimum at worst-case tolerance** (owner: `circuit-architect`).
FT232H in 3.3 V mode: VREGIN min 3.3 / typ 3.3 / max 3.6 V (DS_FT232H §5.2). +3V3D = 0.6 x (1 + 100k/22k)
= 3.327 V nominal, but TLV62569 VFB is 0.588-0.612 V and R5/R6 are 1 %, so the rail is 3.21-3.45 V; the
low end is 90 mV under the FT232H minimum. Not abs-max; nominal is in spec; ERC cannot see it.
The setpoint cannot simply be raised: guaranteeing >= 3.30 V needs ~3.42 V nominal (3.55 V max), which
puts |AVDD - VDRV| on U7 at its 0.3 V abs max against a 3.3 V +3V3A. Options for the architect:
(a) accept as-is (risk note: FTDI's typ = min "3.3 V" is a nominal); (b) modest trim, e.g.
```python
# pwr_digital.py — 3.391 V nominal, 3.27-3.52 V worst case (part-sourcer to supply the 21.5k MPN/LCSC)
v3v3d & _r('R5', '100k', '0402WGF1003TCE', 'C25741') & fb_3v3 & _r('R6', '21.5k', '<MPN>', '<LCSC>') & gnd
```
(c) move U10 to VREGIN 5 V mode from VBUS_SW (costs ~90 mW of the 1 %-margin USB budget, P1).

### LOW

**L1 — Netlist sheet order depends on Python hash seed** (owner: export phase; no design change).
Across runs the `(sheet (number N))` entries for `/pwr_analog/` and `/afe_ch_a/` swap (seen in 1 of 3 unseeded
runs). Component `sheetpath`/`tstamps` and all nets are identical, so KiCad "Update PCB" is unaffected, but
the coder's "diff empty apart from date" held by chance. Fix: export with `PYTHONHASHSEED=0`
(two seeded runs diff only in `(date ...)`), or sort sheets in SKiDL's netlister.

### WARNINGS (tool output, accepted)

**W1/W2 — `Missing tag on  instantiated at <frozen importlib._bootstrap>:491`** (netlist and XML, same cause).
Unnamed root hierarchy node created by `python -m`; every part carries a tag (`_stabilize_tags()` + block
`tag=`), and component UUIDs are stable across runs. Coder's justification names the mechanism and checks out.

### NOTES (informational, carried forward)

- **N1** J2/J3 `ProjectLocal:KH-BNC50-3511` is custom, from a not-to-scale drawing. Pad 1 = centre, three pad-2 shell pins; netlist matches. Verify against a physical part before fab.
- **N2** U9 EP (pad 89) = GND is unverified in Gowin docs (UG119 says only "exposed pad"); industry practice.
- **N3** U9 dual-purpose config pins used as user I/O (53 DOUT, 54 DIN, 55 SSPI_CS_N, 56 SO, 57 FASTRD_N, 59 MCLK, 60 MCS_N, 61 MO, 62 MI): enable the matching "use as regular IO" options in Gowin Dual-Purpose Pin settings, or P&R will reject them. Autoboot (MODE=00) leaves them idle during config; weak pull-ups hold FT_RD_N/WR_N/OE_N inactive.
- **N4** UG284 recommends a ferrite bead + 4.7 uF on U9 VCC; design uses 4x100 nF + 10 uF directly on +1V2. Layout/bring-up decision.
- **N5** U7 AVDD (+3V3A, LDO, on with VBUS_SW) leads VDRV (+3V3D, EN-delayed) by ~1-3 ms. ADS5231 recommended sequencing allows -10 ms < t3 < 10 ms (SBAS295A p.10, read from rendered page), so this passes.
- **N6** `outputs/run1.net` is a stale copy of the assembler's run; ignore and delete it.

## Checklist (defects ERC cannot see)

| Check | Result |
|-------|--------|
| Supply span vs abs max | OPA810 U20/U40 ±3.36/-3.42 V = 6.8 V (4.75-27 V) ✓; THS4521 U21/U41 0-3.3 V (≤5.5) ✓; U7 AVDD/VDRV 3.3 V ✓; LM27762, TLV757, TLV62569, TPS22918 on VBUS ≤5.5 V ✓; U9 1.2/3.3/1.8 V ✓ |
| Signal level vs receiver rail | XO (3V3D) -> U7 CLK via 33R, U8 ✓; U7 outputs (VDRV 3.3 V) -> U9 banks 1/2 (3.3 V) ✓; FT232H 3.3 V <-> bank 1 ✓; THS4521 outputs bounded by +3V3A rail; ADC inputs ≤ min(3.3, AVDD+0.3) with 33R series ✓; THS4521 inputs stay 0-1.7 V even with buffer saturated at the AFE rails ✓ |
| FPGA bank voltages | Every U9 signal pin checked against UG803: ADC/FT/clock/LED/trigger on banks 1/2 (VCCO1/2 = +3V3D); JTAG, MODE, JTAGSEL_N, RECONFIG_N on bank 3 (VCCO3 = +1V8, PSRAM bank, 1.8 V only); bank-3 pull-ups and J4 VREF on +1V8 ✓; 15 unused bank-3 pins NC ✓ |
| Active filter topology | MFB per leg: R23->MS, C25 MS->GND, R25 MS->VOUT-, R27 MS->VIN+, C27 VIN+->VOUT-; every cap carries current. From netlist values: f0 8.84 MHz, Q 0.99, plus output RC (2x33R, 270 pF) pole 8.9 MHz = 3rd-order Butterworth, DC gain 0.909, matches net_plan §AAF ✓ |
| Exposed pads | U6 pad 13, U9 pad 89 on GND ✓ |
| Reproducibility | See L1; no `_1` refdes ✓ |

Coder override claims checked: U10 VCCA->PWRIN (DS_FT232H: on-chip 1.8 V LDO drives both VCORE and VCCA) ✓;
U10 EECS/EECLK->OUTPUT ✓; U6 PGOOD->GND (LM27762 pin table: "connect to ground if not used") ✓; all listed NC
pins absent from netlist (U7 9/22/26/39, U5 4, U8 1, J1 A8/B8, U9 3,10,11,13-16,79-86, U10 31-33) ✓.

## Summary

| Severity | Count | Refs | Owner |
|----------|-------|------|-------|
| ERROR | 0 | — | — |
| MEDIUM | 1 | U10 / U3 R5,R6 (+3V3D setpoint) | circuit-architect (disposition) |
| LOW | 1 | netlist sheet order | export (use `PYTHONHASHSEED=0`) |
| WARNING | 2 | root-node missing tag | accepted |
| NOTE | 6 | J2/J3, U9 EP, U9 dual-purpose pins, U9 VCC bead, U7 sequencing, stale run1.net | carried forward |

**PASS**: 0 ERC errors, all footprints resolve, BOM agrees with circuit.
