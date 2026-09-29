# GW1NR-LV9QN88PC6/I5 — Gowin LittleBee FPGA, QN88P PSRAM-embedded (fpga_core, U5)

| Spec | Value |
|------|-------|
| Package | QN88P (QFN-88, 1 exposed pad) — **10.00 x 10.00mm body**, NOT 8x8mm (see Load-bearing facts) |
| Vcc / Vin range | LV version: 1.14–1.26V core (VCC), VCCIO/VCCX per-bank selectable 1.2/1.5/1.8/2.5/3.3V |
| Key output spec | 8640 LUT4-class logic elements, 468kbit BSRAM, embedded 64Mbit/16-bit PSRAM |
| Max current / power | ≈390mW per design_risks.md R-7 thermal budget |
| Operating temp | 0°C to +85°C (I5 = industrial-ish grade per part suffix; confirm exact grade if needed) |

## Pinout
89 pins total (88 signal/power + 1 exposed pad = pin 89 "EP"). Full pin-by-pin list is in
`symbols/dual_adc_usb.kicad_sym` (symbol `GW1NR-LV9QN88PC6-I5`) and was cross-validated two ways:
JLC/EasyEDA's pin list for this exact LCSC# (C5799578) **and** Gowin's own UG119E Figure 3-8
(QN88P physical pin distribution, p.15/31) — both agree on 89 total pins.

Physical layout (confirmed from Figure 3-8 image, UG119E p.15/31): standard QFN counter-clockwise
numbering — **pins 1–22 on the left edge (top to bottom), 23–44 on the bottom edge (left to
right), 45–66 on the right edge (bottom to top), 67–88 on the top edge (right to left)**, 22 pins
per side, 0.4mm pitch. Pin 89 = EP (center exposed pad, 6.8x6.8mm).

Power/ground pins, **corrected against Gowin's own Table 3-8** (see Decisions below — the
generated symbol has a wrong name on pin 12, inherited from JLC/EasyEDA, do not trust the
symbol's pin-12 label): VCC = 1,22,45,66. VSS = 2,21,24,43,46,65. **VCCX/VCCIO0 = 64,67,78
only** (pin-multiplexed, one rail). VCCIO1 = 58. VCCIO2 = 23,44. **VCCIO3 = 12** (its own
independent rail — NOT part of the VCCX/VCCIO0 group). MODE0/MODE1 = 88/87 (dual-function
with IOT5A/IOT6B).

Four banks, each with its own independent VCCIO (`GW1NR-LV9QN88PC6-I5.pdf` p.14/71, §2.4.1:
"Each bank has its own I/O power supply VCCIO") — **verified**. Bank↔VCCIO-rail pairing is now
**verified directly** (not inferred) from `UG803_GW1NR9_Pinout.pdf`'s per-pin table, which
carries an explicit `BANK` column: **BANK0→VCCX/VCCIO0(64,67,78), BANK1→VCCIO1(58) [IOR*
pins], BANK2→VCCIO2(23,44) [IOB* pins], BANK3→VCCIO3(12) [IOL* pins].** This corrects and
upgrades an earlier revision of this file, which had this pairing as an unverified inference.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| **Free user I/O for GW1NR-9 in QN88P package** | **71 total** (bank breakdown: BANK0=0, BANK1=25, BANK2=23, BANK3=23). **But only 48 are cleanly 3.3V-capable** — see § "CORRECTION" below, which supersedes an earlier revision of this row. | `datasheets/GW1NR-9-UG119E.pdf` Table 2-1/Table 2-6 — **verified** for the 71 total. The 48-at-3.3V figure is also **verified**, from `datasheets/UG803_GW1NR9_Pinout.pdf` (see below). |
| PSRAM interface supply/bank voltage | **VCCIO3 (BANK3)**, 1.71–1.89V, "connected to PSRAM and provides power for PSRAM" | `datasheets/UG803_GW1NR9_Pinout.pdf` p.5/17, "Recommended Operating Conditions of QN88P Package Embedded with PSRAM in GW1NR-9" table — **verified, direct quote, supersedes the BANK0 inference in an earlier revision of this file, which was wrong.** |
| Package body size | **10.00mm × 10.00mm**, NOT 8×8mm | `GW1NR-9-UG119E.pdf` Figure 4-2 / dimension table, p.23/31 ("D=10.00, E=10.00, D2=E2=6.8 [exposed pad], e=0.40 [pitch], L=0.85 [lead length], b=0.20 [lead width]") — **verified**. **Sourcing's `sourced_bom.md` and JLC's own part listing label this "QFN-88-1EP(8x8)" — that 8x8mm figure is wrong per Gowin's own package drawing.** The custom footprint built for this phase (see Notes) uses the correct 10x10mm dimensions. |

## CORRECTION (coordinator-directed, UG803 obtained) — my earlier BANK0/PSRAM inference was wrong

An earlier revision of this summary inferred (without UG803 in hand) that BANK0/VCCX-VCCIO0
hosted the PSRAM interface, and concluded the 71-I/O budget was unaffected. **`UG803_GW1NR9_Pinout.pdf`
(the primary Gowin pinout doc for exactly this device, obtained this revision) directly
contradicts that inference and confirms the architect's finding instead:**

- **VCCIO3 (pin 12), not VCCX/VCCIO0, is the PSRAM-connected rail** — direct quote above. Pin 12
  is independently confirmed as VCCIO3 in UG803's own per-pin table (p.13/17: "VCCIO3 Power N/A
  ... 12 12" under the QN88/QN88P columns) — **verified, matches Gowin's own Table 3-8 in
  UG119E, which the generated KiCad symbol mislabels** (see Notes).
- **VCCIO3 supplies BANK3** — confirmed directly from UG803's per-pin table, which carries an
  explicit `BANK` column for every I/O pin: all `IOL*` pins are tagged `BANK 3`, matching
  VCCIO3's ownership of the left package edge. **Verified**, not inferred (UG803's table states
  the bank number per pin explicitly, unlike UG119E which only gives per-bank totals).
- **BANK3 has 23 free user I/O in QN88P (Table 2-6: 23/6/3), NOT zero.** Since "each bank has
  its own I/O power supply VCCIO" (DS117 p.14, verified) — a bank cannot run part at 3.3V and
  part at 1.8V — **all 23 of BANK3's free I/O are forced to the PSRAM's 1.71–1.89V logic level,
  not usable as 3.3V I/O** for FT232H/ADS5231-facing signals without level-shifting.
- **Therefore only BANK1 (25) + BANK2 (23) = 48 I/O are cleanly 3.3V-capable**, not 71.
  Architecture requires 51. **Shortfall: 3 pins.**
- **This is not a re-architecture-triggering failure.** `design_risks.md` R-1's own
  already-documented contingency ladder step 1 ("Drop OVRA/OVRB and the two LEDs, −4") frees 4
  pins from the 51-required list — more than covers the 3-pin gap — **without touching the
  keystone FPGA/PSRAM decision.** BANK0 (VCCX/VCCIO0, pins 64,67,78) is *not* the PSRAM rail;
  it's "Auxiliary voltage," legal 2.375–3.6V (`UG803_GW1NR9_Pinout.pdf` p.5/17) — no conflict
  with the 3.3V `P3V3D` rail net_plan already assigns it. It also has 0 free user I/O regardless
  (Table 2-6), so it was never part of the count either way.
- **`net_plan.md`'s power-tree fix is now scoped to VCCIO3 (pin 12), not VCCX/VCCIO0**: split
  the "U5 VCCIO/VCCX banks → P3V3D" blanket tie (line 17) so VCCIO3 gets its own ~1.8V rail,
  while VCCIO1/VCCIO2/VCCX-VCCIO0 (pins 58, 23/44, 64/67/78) stay on `P3V3D` at 3.3V.
- **Which specific 3 of BANK3's 23 I/O to drop, or apply R-1's LED/OVR contingency instead, is
  a coding-phase/architecture decision, not re-derived here** — the point settled is that the
  budget shortfall is small (3 pins) and R-1's existing mitigation already covers it.

## MODE[2:0] configuration strap (coordinator-directed follow-up, UG290)

The architect set R54/R55 = 4.7kΩ to GND on MODE0/MODE1 (MODE[1:0]=00), copied from a
reference design without the encoding table. **Confirmed correct**: `UG290_Gowin_Config_Guide.pdf`
Table 5-1 (p.34/130, "Configuration Modes") gives MODE[2:0]=000 → **"AUTO BOOT — The FPGA reads
data from the embedded Flash for configuration"** — **verified**, direct quote, correct table for
this device family ("LittleBee Family FPGA Products", which includes GW1NR). MODE2 has no
physical pin on QN88P (only MODE0/MODE1 are bonded out — `UG119E`/`UG803` "Other pins" tables
list just two MODE pins, 87/88); UG290's own note [1] states "unbonded mode pins are grounded by
default," so MODE2=0 without any connection. **MODE[2:0]=000 (AUTOBOOT) is what R54/R55=GND
actually selects — the reference-design copy is correct, no strap change needed.**

## Notes
- `[CRIT]` keystone part — memory architecture and I/O budget both depend on it (sourcing).
- **Custom footprint generated this phase**: `footprints/ProjectLocal.pretty/QFN-88-1EP_10x10mm_P0.4mm_Gowin_QN88P.kicad_mod` — 89 pads (88 leads + EP=pad 89), dimensions from Gowin UG119E Fig 4-1/4-2 (p.22–23/31), pin-1 location and per-side pin ranges confirmed visually against Figure 3-8 (p.15/31). **Pad sizing uses datasheet lead dimensions directly** (lead length 0.85mm exactly; lead width widened from the datasheet's 0.20mm nominal to 0.25mm for solder-toe margin) — not an IPC-7351-expanded land pattern. Recommend the coder/reviewer sanity-check against IPC before fab.
- **Generated symbol**: `dual_adc_usb:GW1NR-LV9QN88PC6-I5` in `symbols/dual_adc_usb.kicad_sym`, footprint field pre-set to the custom footprint above. 89 pins including EP as its own pin (type `passive`), `find-symbol.py` reports `EXACT`. **Pin 12 is still mislabeled `VCCX_VCCO0` in this symbol** (inherited from JLC/EasyEDA) — it must be renamed `VCCIO3` before U5's power pins are wired; not fixed in the symbol file itself this revision.
- Datasheets: `datasheets/GW1NR-LV9QN88PC6-I5.pdf` (DS117-3.2.5E, main datasheet),
  `datasheets/GW1NR-9-UG119E.pdf` (UG119-1.8.4E, Package & Pinout User Guide),
  `datasheets/UG803_GW1NR9_Pinout.pdf` (UG803-1.6.5E, **the authoritative GW1NR-9-specific
  pinout/power doc** — use this one for any bank/VCCIO/PSRAM question), and
  `datasheets/UG290_Gowin_Config_Guide.pdf` (UG290-2.9.1E, MODE strap encoding).
