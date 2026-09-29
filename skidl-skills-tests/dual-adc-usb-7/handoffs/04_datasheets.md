---
phase: 04_datasheets
agent: datasheet-librarian
circuit: dual_adc_usb
written: 2026-09-23T09:00:00Z
status: partial
revision: 6
next_phase: 05_coding
---

# Phase 4 handoff — Datasheets

## Decisions

1. **CORRECTED in rev.5 — see Decision 13. GW1NR-9 has 71 total user I/O (Gowin UG119E Table
   2-6, bank breakdown 0/25/23/23), but only 48 of them are cleanly 3.3V-capable.** The PSRAM
   rail (VCCIO3/BANK3) forces its 23 I/O to ~1.8V. 51 required vs 48 at 3.3V = a 3-pin
   shortfall, covered by `design_risks.md` R-1's own existing contingency step 1. **Do not treat
   this row's original "71 available, no risk" claim as current — it was wrong; rev.5 below is
   the corrected version.**
2. **GW1NR-9 QN88P body is 10.00×10.00mm, not 8×8mm as JLC/sourced_bom label it.** Gowin's own
   package outline (UG119E Fig 4-2, p.23) gives D=E=10.00mm, D2=E2=6.8mm (EP), pitch 0.4mm, lead
   0.85×0.20mm. The custom footprint built this phase uses the correct 10×10mm dimensions.
3. **AD8066's EasyEDA/JLC pinout is wrong — do not use it.** It returned only 5 of 8 pins
   (missing the entire second channel: pins 5,6,7). The generated symbol uses the pinout read
   directly from ADI's datasheet pin diagram instead. See `AD8066ARZ-R7_SUMMARY.md`.
4. **TLV62569 VFB = 0.6V (0.588–0.612V), verified from TI's electrical table** (p.4) — the
   R72/R73/R74/R75 divider values in `sourced_bom.md` are confirmed correct.
5. **ADS5231 PLL-disable sequence and differential input window resolved from the primary
   datasheet** (SBAS295A p.8, p.19): input window is 1.0–2.0V per pin (matches architecture
   exactly); PLL-disable is serial register word `00110010` written after SEL=1 + a low pulse
   reset. Full sequence in `ADS5231IPAGT_SUMMARY.md` § Load-bearing facts.
6. **R402 has no datasheet-justified function — recommend deletion.** ADS5231 needs exactly one
   bias resistor (ISET=R401). `net_plan.md` already routes `ADC_SEL` as an FPGA-driven net, not
   a strap. See `ADS5231IPAGT_SUMMARY.md` for the full pin-by-pin elimination.
7. **R65 resolved, and corrected from the previous revision: it is the datasheet-mandated
   PWREN# pull-up, not a RESET# pull-up.** FTDI's datasheet (obtained this revision, see below)
   states PWREN# "must be used with a 10kΩ resistor pull-up" — R65 is exactly 10kΩ and sits on
   the `PWREN_N` net (U6.ACBUS9 → R65 → pull-up rail, same node drives Q1's gate). **Verified**,
   `Unverified keystone facts` no longer carries this row. Separately, RESET# (pin 34) is still
   absent from `net_plan.md` — the datasheet says it "should be tied to VCCIO (+3.3V) if not
   being used," a direct wire, not a resistor. That gap is now in Carried forward, not Decisions.
8. **C82 is most likely the TPS60403's missing input bypass cap (CI)** — TI's app note (p.13)
   calls for three 1µF caps (CI/Cfly/CO); the BOM only names two (C78=fly, C79=out). C82 (100nF
   placeholder) is undersized vs. TI's ≥1µF recommendation for this loading config; recommend
   bumping to ≥1µF if board area allows. See `TPS60403DBVR_SUMMARY.md`.
9. **A real net-plan conflict found while reading ADS5231's pin table**: `net_plan.md` line 77
   ties `MSBI` and `OEA` (pins 41/42) statically to GND, but these are the *same physical pins*
   as `SEN`/`SCLK` when SEL=1 — which R-6 and `ADC_SEN`/`ADC_SCLK` require for the mandatory
   10MSPS PLL-disable write. The coder must drop those two GND ties and drive 41/42 from the
   FPGA; only `OEB#` (pin 6, genuinely separate) is safe to tie statically.
10. TPS22918's first-fetched datasheet was TI's old "PRODUCT PREVIEW" revision (no VIH/VIL
    table) — a second URL got the current production datasheet (`TPS22918DBVR-FULL.pdf`),
    which has the electrical table used to confirm V_IH ≥1.0V.
11. **FT232H datasheet obtained** on a targeted re-attempt (coordinator-directed, not a full
    phase re-run): `digikey_get_part` surfaced a newer `ftdichip.com` URL (still 403'd), but a
    Farnell-hosted mirror (`farnell.com/datasheets/1913746.pdf`) worked. This closed both facts
    ACBUS9=PWREN# (EEPROM-required, confirmed) and R65's true role (PWREN# pull-up per the
    datasheet's own footnote, correcting the prior revision's RESET#-pull-up guess).
12. **SUPERSEDED by Decision 13 — my rev.4 answer to the PSRAM-bank escalation was itself wrong.**
    Rev.4 (without UG803 in hand) inferred BANK0/VCCX-VCCIO0 hosted the PSRAM interface and
    concluded no I/O was lost. That inference was incorrect. Kept here only so the revision
    history is honest; do not use it.
13. **GW1NR-9 PSRAM-bank fact re-settled with UG803 (the authoritative GW1NR-9-specific pinout
    doc, obtained this revision) — the architect's finding is correct, mine in rev.4 was not.**
    `UG803_GW1NR9_Pinout.pdf` p.5/17, "Recommended Operating Conditions of QN88P Package
    Embedded with PSRAM in GW1NR-9": **"VCCIO3 — I/O Bank power supply voltage, connected to
    PSRAM and provides power for PSRAM — 1.71V/1.89V."** Pin 12 = VCCIO3 (confirmed in UG803's
    own per-pin table), and UG803's per-pin table carries an explicit `BANK` column showing all
    `IOL*`-named pins (including pin 12) are **BANK3** — verified directly, not inferred. BANK3
    has 23 free user I/O in QN88P (Table 2-6: 23/6/3), not zero — since each bank shares one
    VCCIO (DS117 p.14, verified), **those 23 pins are forced to the PSRAM's 1.71–1.89V logic
    level**, not usable as 3.3V I/O without level-shifting. **Corrected budget: BANK1(25) +
    BANK2(23) = 48 I/O cleanly 3.3V-capable, not 71. 51 required → 3-pin shortfall.**
    `design_risks.md` R-1's own existing contingency step 1 ("drop OVRA/OVRB + 2 LEDs, −4")
    covers it with margin — **no re-architecture, no new regulator needed for the count itself**,
    but `net_plan.md`'s power split is now correctly scoped to **VCCIO3 (pin 12)**, not
    VCCX/VCCIO0 (which is just "Auxiliary voltage," 2.375–3.6V, no PSRAM role, fine on P3V3D).
    Symbol bug confirmed and still not fixed (pin 12 mislabeled `VCCX_VCCO0`, should be
    `VCCIO3`) — see `GW1NR-LV9QN88PC6-I5_SUMMARY.md` § CORRECTION for full citations.
14. **ADS5231 SEL pin — CRITICAL, settled for the architect: must stay dynamic, not a static
    strap.** TI SBAS295A p.19 §"SERIAL INTERFACE" states the low-going pulse on SEL is required
    ("it is necessary...Without a reset, it is possible that registers may be in their
    non-default state on power-up. This condition may cause the device to malfunction") —
    verified, not a convenience. Power-up default of the PLL-enable bit is "PLL Enabled" (p.8
    register map, verified). No documented path exists for a statically-held-high SEL to
    reliably deliver the PLL-disable write. **A static strap risks leaving the PLL
    undisableable, failing the 10MSPS requirement (SPEC F3) — keep SEL FPGA-driven.** Full
    (a)/(b)/(c) answer with citations in `ADS5231IPAGT_SUMMARY.md` § "SEL pin: static strap vs.
    dynamic."
15. **Gowin UG290 MODE[2:0] encoding confirmed — the architect's R54/R55=4.7kΩ-to-GND strap
    (MODE[1:0]=00) is correct, no change needed.** `UG290_Gowin_Config_Guide.pdf` Table 5-1
    (p.34/130): MODE[2:0]=000 → "AUTO BOOT — reads data from the embedded Flash for
    configuration." MODE2 has no physical pin on QN88P (only MODE0/MODE1 bonded out) and
    defaults to 0 when unbonded (UG290 note [1], verified) — so MODE[2:0]=000 is exactly what
    the existing strap selects.
16. **U14 (AP2127K-1.8TRG1) soft-start escalation resolved — targeted rev.6 pass, no other part
    re-checked.** `datasheets/AP2127K-1.8TRG1.pdf` (DS36478 Rev.7-2, obtained this pass from
    diodes.com — the LCSC-hosted mirror is anti-bot-blocked and could not be downloaded) and
    `datasheets/GW1NR-LV9QN88PC6-I5.pdf` (this file **is** Gowin DS117-3.2.5E) both confirmed:
    - **(1) VERIFIED, real MAX limit, applies to VCCIO3.** DS117 Table 3-3 "Power Supply Ramp
      Rates" (p.43, section 3.1.3): VCCIO Ramp Min 0.1 mV/us, Max **10 mV/us**, note "a
      monotonic ramp is required for all power supplies." The table gives one generic "VCCIO"
      row, not a per-bank one; UG803's per-pin table (rev.5) confirms VCCIO3 (pin 12) is a
      VCCIO-class supply with no separate ramp spec, so the 10 mV/us max applies to it
      directly. 1.8 V / 10 mV/us = **180 us is a real, binding minimum ramp time** — the
      escalation was correctly raised; this does not close with no board change.
    - **(2) VERIFIED: internal fixed-time soft-start, not current/Cout-limited.** DS36478 p.7
      Electrical Characteristics lists "Soft Start Time ... Typ 50 us" with no stated
      dependency on COUT; the separate "Output Capacitor" application note (p.11) addresses
      only stability/transient response, never ramp time. **A bigger COUT is not a fix** — it
      cannot be relied on to stretch the internal 50 us timer to 180 us.
    - **(3) VERIFIED: Shutdown pin is a binary logic enable, not an analog ramp control.**
      DS36478 p.7-8 electrical table specs Shutdown purely as VIH>=1.5V / VIL<=0.5V with a
      pull-down resistance — no soft-start-via-EN-slew behavior is described anywhere in the
      document. **An RC on Shutdown only delays when the 1.5V threshold is crossed; once
      crossed, the internal 50 us timer governs dV/dt regardless.** Sourcing's proposed
      mitigation is a non-fix — confirmed, not implemented.
    - **(4) No in-stock 1.8V LDO with a specified soft-start >=180 us was found** (consistent
      with sourcing rev.3's own check of AP2127K/RT9013-18GB/TLV73318PDBVR — none qualify).
      **TPS22918 (already U9 on this board, `datasheets/TPS22918DBVR-FULL.pdf`) is the fix.**
      Section 8.3.3 "Adjustable Rise Time (CT)" (p.14, **verified**): "A capacitor to GND on
      the CT pin sets the slew rate of VOUT," with Table 2 (measured, VIN=1.8V column) giving a
      10-90% rise time of **260 us at CT=220 pF** (vs. 60 us at CT=0 pF) — a real,
      datasheet-measured analog ramp control, unlike AP2127K's Shutdown pin. 260 us clears the
      180 us floor with ~44% margin. Electrically sound here: TPS22918's 1V-5.5V VIN range and
      53 mOhm RDS(on) handle the PSRAM's <=66 mA transient with negligible drop (<4 mV), and it
      is already a qualified, in-stock, same-footprint part on this BOM.
    - **Recommendation: add a second TPS22918DBVR (new ref, e.g. U15) between U14's VOUT and
      VCCIO3, with a 220 pF 0402 C0G capacitor from its CT pin (new ref, e.g. C87) to GND;
      leave U14 (AP2127K-1.8TRG1) and its existing C84/C85/C86 decoupling unchanged.** Sequence
      U15's ON control to assert at or after U14's enable (U14's own 50 us ramp completes long
      before U15's 260 us CT-controlled ramp begins driving VCCIO3, so no strict interlock is
      required beyond not enabling U15 before U14). This is the single fix for `power_tree`'s
      work order.

## Artifacts

| File | Contains | Read it when |
|------|----------|--------------|
| `datasheets/*_SUMMARY.md` (23 files) | Per-part spec summaries, pinouts, Load-bearing facts for keystones | Always — before writing any code |
| `datasheets/*.pdf` (21 of 22 parts) | Source datasheets, incl. `FT232H-farnell.pdf` (primary FT232H datasheet, obtained rev.3), `UG803_GW1NR9_Pinout.pdf` (**the authoritative GW1NR-9 pinout/power doc**, obtained rev.5), `UG290_Gowin_Config_Guide.pdf` (MODE strap encoding, obtained rev.5), `AP2127K-1.8TRG1.pdf` (DS36478 Rev.7-2, U14 soft-start resolution, obtained rev.6 — note `GW1NR-LV9QN88PC6-I5.pdf` **is** Gowin DS117, used again this pass for Table 3-3) | When a summary references a page number |
| `symbols/dual_adc_usb.kicad_sym` | 6 generated KiCad symbols (176 pins total) | Whenever instantiating U1, U4, U5, U9, U12, or X1 in SKiDL |
| `footprints/ProjectLocal.pretty/QFN-88-1EP_10x10mm_P0.4mm_Gowin_QN88P.kicad_mod` | Custom U5 footprint, 89 pads | When laying out or assigning U5's footprint |

## Summaries by block

| block_id | summary files |
|---|---|
| `afe_input` | `datasheets/BAV199_SUMMARY.md`, `datasheets/KH-BNC50-3511_SUMMARY.md` |
| `afe_buffer` | `datasheets/AD8066ARZ-R7_SUMMARY.md` |
| `afe_driver` | `datasheets/THS4521IDR_SUMMARY.md`, `datasheets/MLF2012A3R3JT000_SUMMARY.md`, `datasheets/FHW0805UF5R6JST_SUMMARY.md`, `datasheets/BAT54S_SUMMARY.md` |
| `adc_dual` | `datasheets/ADS5231IPAGT_SUMMARY.md` |
| `clock_gen` | `datasheets/SX3M10.000M20F30TNN_SUMMARY.md` |
| `fpga_core` | `datasheets/GW1NR-LV9QN88PC6-I5_SUMMARY.md` |
| `usb_bridge` | `datasheets/FT232HL-REEL_SUMMARY.md`, `datasheets/93LC56BT-I-OT_SUMMARY.md`, `datasheets/USBLC6-2SC6_SUMMARY.md`, `datasheets/TYPE-C-16PIN-2MD073_SUMMARY.md`, `datasheets/X322512MOB4SI_SUMMARY.md` |
| `power_tree` | `datasheets/TPS22918DBVR_SUMMARY.md`, `datasheets/TLV62569DBVR_SUMMARY.md`, `datasheets/RT9013-33GB_SUMMARY.md`, `datasheets/TPS60403DBVR_SUMMARY.md`, `datasheets/BSS138_SUMMARY.md`, `datasheets/WIP201610P-2R2ML_SUMMARY.md`, `datasheets/CBW160808U601T_SUMMARY.md`, `datasheets/AP2127K-1.8TRG1_SUMMARY.md` (added rev.6) |

## Next phase must

Addressed to **skidl-block-coder** (via the driver's per-block work orders):

1. **U5 (GW1NR-9)**: use `Part('dual_adc_usb', 'GW1NR-LV9QN88PC6-I5')` from
   `symbols/dual_adc_usb.kicad_sym` (put `symbols/` on `KICAD9_SYMBOL_DIR`), footprint
   `ProjectLocal:QFN-88-1EP_10x10mm_P0.4mm_Gowin_QN88P`. Wire the exposed pad (pin `89`, named
   `EP`) to GND. **Only 48 of the 71 user I/O are 3.3V-capable (BANK1+BANK2); BANK3's 23
   (VCCIO3=pin 12) are forced to ~1.8V for the PSRAM (Decision 13) — 51 required vs 48 at 3.3V
   is a 3-pin shortfall, apply `design_risks.md` R-1 contingency step 1 (drop OVRA/OVRB + 2
   LEDs) to close it.** Rename pin 12 from `VCCX_VCCO0` to `VCCIO3` before wiring power (symbol
   bug). Split U5's power: P3V3D (3.3V) to VCCIO1/VCCIO2/VCCX-VCCIO0 (58, 23/44, 64/67/78), a
   new ~1.8V rail to VCCIO3 (pin 12) only.
2. **U4 (ADS5231)**: use `Part('dual_adc_usb', 'ADS5231IPAGT')`. Drop the GND ties on pins
   41/42 (MSBI/OEA) that `net_plan.md` line 77 specifies — drive them as SEN/SCLK from the FPGA
   instead (SEL must be driven to 1). Delete R402 (no function found) unless the driver decides
   otherwise. Implement the PLL-disable write (register byte `00110010`) per R-6. **SEL must be
   a dynamic FPGA-driven pin — do NOT strap it statically** (Decision 14; a static strap risks
   an undisableable PLL and failing the 10MSPS requirement).
3. **U1 (AD8066)**: use `Part('dual_adc_usb', 'AD8066ARZ-R7')` — pins verified from ADI's
   datasheet, NOT from JLC's EasyEDA data (which is incomplete for this part).
4. **U9/U12/X1**: use `Part('dual_adc_usb', 'TPS22918DBVR')`, `Part('dual_adc_usb',
   'RT9013-33GB')`, `Part('dual_adc_usb', 'SX3M10.000M20F30TNN')` respectively.
5. **C82**: wire as the TPS60403's input bypass cap (CI) on `VA_POS` at U13.IN, not left
   unconnected.
6. **R65**: wire as the PWREN# pull-up — from `PWREN_N` (U6.ACBUS9 / Q1 gate net) to `FT_3V3`
   (datasheet-mandated 10kΩ, `FT232HL-REEL_SUMMARY.md` § Load-bearing facts). Separately, tie
   U6 RESET# (pin 34, absent from `net_plan.md`) directly to `FT_3V3` — no resistor needed.
7. **U14 soft-start (rev.6, Decision 16)**: `power_tree` must add a second TPS22918DBVR
   (new ref, e.g. U15) between U14's VOUT and VCCIO3, with a 220 pF 0402 C0G cap (new ref,
   e.g. C87) from U15's CT pin to GND. U14 (AP2127K-1.8TRG1) and its C84/C85/C86 stay as
   sourced. Do NOT add an RC on U14's Shutdown pin — verified as a non-fix
   (`AP2127K-1.8TRG1_SUMMARY.md` § Load-bearing facts). Enable U15 at or after U14 (no strict
   interlock needed — U14's ramp is much faster than U15's CT-controlled one).

## Carried forward

| Item | Status | Note |
|---|---|---|
| FT232HL-REEL RESET# (pin 34) | Gap in `net_plan.md` | Pin is absent from the net plan entirely. Datasheet says tie directly to `FT_3V3` if unused (no resistor) — not R65, which is the PWREN# pull-up. Coder should add this tie. |
| USBLC6-2SC6 datasheet | Not obtained (ordinary budget, 2 attempts) | 0.35pF/0.8pF junction capacitance is MCP-parametric only, not datasheet-verified. Lower consequence than the analog front end (this part sits on USB D+/D−) but flagged per the phase's own cautionary precedent. |
| X322512MOB4SI datasheet | Not obtained (1 attempt) | MCP spec (12MHz, 12pF load, ±20ppm) is complete enough for this passive crystal; no PDF needed per scope. |
| KH-BNC50-3511 / TYPE-C-16PIN-2MD073 footprint dimensions | PDFs obtained but are mostly graphical (no extractable dimension tables) | Coder/reviewer should visually diff the drawings in the PDFs against the assigned KiCad footprints before layout. Risk low-moderate (both are fairly standardized connector families). |
| L71/L72 footprint (`L_Murata_DFE201610P`) vs INPAQ WIP201610P-2R2ML | Dimensionally consistent by inspection (2.0×1.6mm body/land matches), not pad-by-pad diffed against the actual `.kicad_mod` file | Low risk — same "201610" industry size class. |
| GW1NR-9 symbol pin 12 mislabeled `VCCX_VCCO0` | Confirmed bug, not yet fixed in the symbol file | Gowin's own UG803 per-pin table says pin 12 is `VCCIO3`, independent from VCCX/VCCIO0 (64,67,78). Coder must rename before wiring U5 power (Decision 13). |
| `net_plan.md` power-tree split for U5 | Not yet written into net_plan | **VCCIO3 (pin 12)** needs a new ~1.8V rail for the PSRAM — VCCX/VCCIO0 (64,67,78) stays on P3V3D at 3.3V, no PSRAM role (Decision 13, corrects rev.4's wrong scoping). |
| GW1NR-9 3.3V I/O budget: 48 vs 51 required | 3-pin shortfall, mitigated by existing R-1 contingency step 1 | BANK3's 23 I/O share VCCIO3 with the PSRAM, forced to ~1.8V. Coder must apply R-1's "drop OVRA/OVRB + 2 LEDs" step (or equivalent) when assigning the 51 required signals to banks. |
| THS4521 PD pin polarity | Not fully confirmed this pass | Pin 7 = PD (power-down); standard TI convention is active-low but I did not pull the full electrical table row confirming polarity for this exact part. Confirm before tying PD to a rail. |
| U14 soft-start vs. 180 µs floor | **Closed rev.6** (Decision 16) | Was open since sourcing rev.3, never actually addressed in datasheets rev.3-5 despite being flagged highest-priority. Fix: second TPS22918 + 220 pF CT cap downstream of U14. See Next phase must #7. |

## Unverified keystone facts

| Part | Fact | Best available answer | What would close it |
|---|---|---|---|
| `USBLC6-2SC6` | Junction capacitance 0.35pF (I/O) / 0.8pF (VBUS) | JLC parametric DB only (`jlc_get_part`, LCSC C2687116) | ST `usblc6-2.pdf` (timed out) or UMW's own datasheet |

**All GW1NR-9 pinout/bank facts are now closed as of rev.5** — `UG803_GW1NR9_Pinout.pdf`
(obtained this revision) gave a direct, explicit per-pin `BANK` column and an explicit
PSRAM-voltage statement, removing the need for any inference. This also corrects a wrong
conclusion from rev.4 (see Decisions 12/13) — the PSRAM bank is BANK3/VCCIO3, not BANK0, and
the 3.3V-capable I/O count is 48, not 71. FT232HL-REEL's two facts (ACBUS9=PWREN#, R65's role,
closed rev.3), the ADS5231 SEL question (Decision 14), and the MODE strap question (Decision 15)
are also closed. Only the USBLC6-2SC6 row above remains.

## Do not redo

- FT232HL, THS4521, TLV62569, TPS60403, USBLC6-2SC6, 93LC56, BSS138, BAV199, BAT54S, LED,
  crystal, header, coax/USB-C connector symbols — all confirmed existing matches per sourcing,
  none regenerated.
- The 6 newly-generated symbols (`AD8066ARZ-R7`, `TPS22918DBVR`, `RT9013-33GB`,
  `SX3M10.000M20F30TNN`, `ADS5231IPAGT`, `GW1NR-LV9QN88PC6-I5`) and the QN88P footprint — all
  pin/pad counts verified against source data, `find-symbol.py` confirms `EXACT` for all 6.
- The 148-refdes coverage and sourced part list from `sourced_bom.md`/`sourced_bom.csv` —
  unchanged by this phase except the R402-deletion recommendation and C82/R65 role assignments
  above (values unchanged, only function documented).

## Receipt

- 22/22 significant parts covered: 20 with PDF, 2 summary-only (USBLC6-2SC6, X322512MOB4SI).
  10/10 keystone parts have a verified PDF; 2 extra Gowin docs obtained rev.5 (UG803, UG290).
- 6 KiCad symbols generated (176 pins total) + 1 custom QFN-88 footprint (89 pads); all
  `find-symbol.py`-confirmed `EXACT`.
- **Rev.5 correction: GW1NR-9's 3.3V-capable I/O is 48, not 71** — PSRAM rail is BANK3/VCCIO3
  (pin 12), not BANK0 as rev.4 wrongly concluded. 51 required → 3-pin shortfall, covered by
  R-1's existing contingency. ADS5231 SEL settled CRITICAL: must stay dynamic, not a static
  strap, or the PLL may be undisableable (fails 10MSPS/SPEC F3). MODE[1:0]=00 strap confirmed
  correct (UG290, AUTOBOOT).
- Also closed rev.3/4: TLV62569 VFB, ADS5231 input-window, TPS22918 V_IH, R402 (delete),
  C82 (TPS60403 CI), FT232H ACBUS9=PWREN#+R65=PWREN# pull-up. Symbol bug (U5 pin 12) still
  flagged, not yet fixed in the symbol file.
- **Rev.6 (narrow, single-rail pass): U14 (AP2127K-1.8TRG1) soft-start vs. 180 µs VCCIO3 floor
  closed with citations.** `datasheets/AP2127K-1.8TRG1.pdf` (DS36478 Rev.7-2) obtained this
  pass (diodes.com; LCSC mirror is anti-bot-blocked) + new `AP2127K-1.8TRG1_SUMMARY.md`
  written (none existed before, despite U14 being keystone). Findings: (1) DS117 Table 3-3's
  10 mV/µs VCCIO max is real and applies to VCCIO3 — 180 µs is a genuine floor; (2) AP2127K's
  50 µs t_ss is an internal fixed timer, unaffected by COUT — bigger output cap is not a fix;
  (3) the Shutdown pin is a binary logic enable only — an RC there delays turn-on but does not
  slow the internal ramp, confirming sourcing's proposed mitigation is a non-fix; (4) fix is a
  second TPS22918DBVR (already U9 on this BOM) with a 220 pF CT cap, datasheet-measured at
  260 µs rise time (VIN=1.8V) — clears 180 µs with margin. No other part re-checked this pass.
- 1 unverified keystone fact remains: USBLC6-2SC6 capacitance (doesn't block coding).
- `use_cache=false` — no cache read/written this run. Status: **partial** (2 open items: the
  pre-existing USBLC6-2SC6 row, plus this rev's new U15/CT87 additions not yet reflected in
  `sourced_bom.md`/`net_plan.md` — those are for `power_tree`'s coder/driver to add, not a gap
  in this citation work).
