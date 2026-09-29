# Sourced BOM — dual_adc_usb

All stock/price current 2026-09-20 (`pcbparts` MCP, live JLCPCB; jellybean cross-checked
against the jlcsearch.tscircuit.com mirror via `stock-check.py`). `use_cache: false` —
every part below was looked up fresh in this run, nothing carried from
`dual-adc-usb-1..4`. Sourcing rule: stock > 100 required, < 500 WARN, Basic > Preferred >
Extended, single-source flagged. **Rev 4 (2026-09-21):** the four `afe_channel` filter-cap
rows (C_f, C_mfb new, C_diff, C_cm) and the new R_mfb row were re-verified live this date
per architecture revision 3's WO-3 — see the rev 4 marks below; every other row's stock/price
is still as of 2026-09-20 and was not touched.

Columns: `Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad symbol | KiCad footprint | Notes`

## afe_channel ref-number key (both channels use this pattern)

The architect's `## Parts by block` fixes `R101–R110`/`C101–C110` (ch1) and
`R201–R210`/`C201–C210` (ch2) but leaves the function-to-number mapping to the block
coder. To let this BOM give one price/part per numbered ref, the mapping below is the
sourcer's assignment — **the block coder should keep it** rather than re-deriving it,
and the datasheet/ERC phases can rely on it:

| # (ch1 / ch2) | Function | Value |
|---|---|---|
| 101/201 | R_top_a | 475 kΩ ±0.5% |
| 102/202 | R_top_b | 475 kΩ ±0.5% |
| 103/203 | R_bot | 49.9 kΩ ±0.5% |
| 104/204 | R_prot | 1.00 kΩ ±1% |
| 105/205 | R_g1 | 499 Ω ±0.1% |
| 106/206 | R_g2 | 499 Ω ±0.1% |
| 107/207 | R_f (OUT+) | 1.00 kΩ ±0.1% |
| 108/208 | R_f (OUT−) | 1.00 kΩ ±0.1% |
| 109/209 | R_o (P leg) | 33 Ω |
| 110/210 | R_o (N leg) | 33 Ω |
| **111/211** | **R_mfb (mfb_p → IN+), new rev 4** | **499 Ω ±0.1%** |
| **112/212** | **R_mfb (mfb_n → IN−), new rev 4** | **499 Ω ±0.1%** |
| C101/201 | C_top | 2–6 pF trimmer |
| C102/202 | C_bot | 82 pF ±5% C0G |
| C103/203 | C_f (OUT+) | **10 pF ±5% C0G (rev 4, was 27 pF)** |
| C104/204 | C_f (OUT−) | **10 pF ±5% C0G (rev 4, was 27 pF)** |
| C105/205 | C_diff | **330 pF C0G (rev 4, was 470 pF)** |
| C106/206 | C_cm (P) | **100 pF C0G (rev 4, was 220 pF)** |
| C107/207 | C_cm (N) | **100 pF C0G (rev 4, was 220 pF)** |
| C108/208 | U_buf decoupling | 100 nF |
| C109/209 | U_buf bulk | 1 µF |
| C110/210 | U_fda decoupling | 100 nF |
| **C111/211** | **C_mfb, differential mfb_p↔mfb_n, new rev 4** | **68 pF ±5% C0G** |

## usb_c_input

| Ref | MPN | LCSC# | Stock | Unit $ | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| J1 | TYPE-C 16PIN 2MD(073) | C2765186 | 1,171,811 | 0.074 | SMD | Extended | ⚠️ SYMBOL NEEDED | `Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12` | 16-pin, USB 2.0 only, confirmed. Symbol: generate from JLC/EasyEDA pin table (16-pin USB-C, standard pinout) |
| R1, R2 | 0603WAF5101T5E | C23186 | 3,775,920 | 0.002 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 5.1 kΩ ±1% (exceeds the ±5% spec — no downside) |
| R12 | RC0603FR-071ML | C105578 | 97,812 | 0.002 | 0603 | Extended | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 1 MΩ ±1%, shield bleed |
| D1 | USBLC6-2SC6 | C2687116 | 150,192 | 0.048 | SOT-23-6 | Extended | `Power_Protection:USBLC6-2SC6` (EXACT) | `Package_TO_SOT_SMD:SOT-23-6` | |
| D2 | SMF5.0CA | C19077498 | 791,919 | 0.029 | SOD-123FL | Preferred | `Device:D_TVS` | `Diode_SMD:D_SOD-123F` | 5 V TVS, bidirectional, 200 W. Footprint is the closest stocked match to SOD-123FL — confirm lead form against datasheet |
| FB1 | PBY160808T-601Y-N | C108301 | 841,955 | 0.013 | 0603 | Extended | `Device:FerriteBead` | `Inductor_SMD:L_0603_1608Metric` | 600 Ω@100 MHz, 1 A |
| C1, C2 | CL21A475KAQNNNE | C1779 | 2,930,000 | 0.0346 | 0805 | Basic + Preferred | `Device:C` | `Capacitor_SMD:C_0805_2012Metric` | **rev 3: 10 µF → 4.7 µF each** (was `CL21A106KAYNNNE`/C15850, two 10 µF). 4.7 µF X5R 25V. Sum = 9.4 µF, inside SPEC P4's ≤10 µF total on VBUS_RAW — rev 1's 2×10 µF violated it. Tier upgrade over the outgoing part (Basic+Preferred vs Basic) |
| C15 | CL10B102KB8NNNC | C1588 | 2,777,884 | 0.006 | 0603 | Basic | `Device:C` | `Capacitor_SMD:C_0603_1608Metric` | 1 nF, shield to GND |

## digital_power

| Ref | MPN | LCSC# | Stock | Unit $ | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U1 | SY8089A1AAC | C479074 | 296,811 | 0.090 | SOT-23-5 | Extended | ⚠️ SYMBOL NEEDED | `Package_TO_SOT_SMD:SOT-23-5` | **rev 3 annotation — no part or divider change.** `datasheets/SY8089A1AAC.pdf` primary-sources VREF at 591/600/609 mV (VOUT = 0.6×(1+RH/RL)); R4=45.3k/R5=10.0k → 3.318 V, confirmed. The prior "freely substitutable" note now carries one condition: if this part is ever substituted, the divider must be recomputed for the substitute's own VREF — that is the only thing tied to this row |
| U2 | TLV75801PDRVR | C2876308 | 7,986 | 0.334 | WSON-6-EP(2×2) | Extended | `Regulator_Linear:TLV75801PDRV` (PREFIX — confirm pinout) | `Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm` | **Fills the architecture's spec**: adjustable 0.55–5.5 V, 500 mA, dropout 130 mV@500 mA (≤200 mV@200 mA easily met), thermal-pad WSON. Set FB divider for 1.20 V ±3%. Same TI DRV family as U3 |
| U9 | AP2161WG-7 | C176957 | 8,848 (live, re-verified) | 0.2113 @1 / 0.1654 @50 | SOT-23-5 | Extended | `Power_Management:AP2161W` (EXACT — no generation needed) | `Package_TO_SOT_SMD:SOT-23-5` | **rev 3: replaces the `Q1` row (HL2301A, C7420344) — Q1 could not turn off, see architecture rev 2 decision 13.** Diodes Inc. load switch: active-low, GND-referenced EN (VIH 2.0 V min, VIL 0.8 V max) driven directly by PWREN#, 1.1/1.5/1.9 A over-load limit bracketing the 485 mA worst case, 95 mΩ, 0.6 ms soft-start, reverse-current blocking, UVLO, thermal limiting, 5 V-capable. Second source WS4612EBB-5/TR (C42404603) — passes the substitution test but has no KiCad symbol, so AP2161WG-7 is preferred. **`AP2171WG-7` is pin-identical with an ACTIVE-HIGH enable — never substitute it, it silently re-breaks SPEC P4.** A 500 mA-class part (TPS2041B, STMPS2141) also fails: board draws 485 mA worst case |
| L1 | FNR3015S2R2MT | C167747 | 60,663 | 0.043 | SMD 3×3mm | Extended | ⚠️ SYMBOL NEEDED (generic `Device:L`) | `Inductor_SMD:L_Changjiang_FNR3015S` | 2.2 µH, shielded, 2 A sat |
| FB2 | PBY160808T-601Y-N | C108301 | 841,955 | 0.013 | 0603 | Extended | `Device:FerriteBead` | `Inductor_SMD:L_0603_1608Metric` | same part as FB1 |
| R4–R6 | — generic 1% 0603 | — | — | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | Buck FB divider + EN pulls; exact values from U1 datasheet, sourcer's discretion (Basic 1% series, e.g. Uniroyal 0603WAF). **R3 (100 kΩ gate pull-up) is deleted per architecture rev 2 decision 14/WO-2 — `usb_bridge`'s R_pwren already holds EN high at plug-in; R6 stays as a DNP 0 Ω PWREN_N→GND bring-up escape** |
| R7 | 0603WAF1001T5E-class | — | — | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | Power-LED series resistor, value set by D4 Vf/If, sourcer's discretion |
| R20, R21 | generic 1% 0603 | — | — | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | **Added rev 3** — R20 = 11.8 kΩ, R21 = 10.0 kΩ, U2's FB divider (already built into `digital_power.py`). Jellybean, cheapest Basic 1% 0603 part wins |
| D4 | CT-1608UGC-P4 | C52675989 | 226,054 (mirror) / 572 (live) | 0.002–0.004 | 0603 | Extended | ⚠️ SYMBOL NEEDED (generic `Device:LED`) | `LED_SMD:LED_0603_1608Metric` | Green power LED. Two stock sources disagree (226 k vs 572) — re-verify at order time; qty needed is 5 total, not a real risk |
| C3–C7 | CL21A106KAYNNNE (10 µF 0805, ×4) + CL05B104KO5NNNC (100 nF 0402, ×1) | C15850 / C1525 | huge | 0.077 / 0.005 | 0805 / 0402 | Basic | `Device:C` | `Capacitor_SMD:C_0805_2012Metric` / `C_0402_1005Metric` | **rev 3: quantity mix corrected to 4×10 µF 0805 + 1×100 nF 0402** (rev 1 guessed 4×100 nF + 1×10 µF, the reverse count). Same two MPNs as before — nothing new to source |

## analog_power_ref

| Ref | MPN | LCSC# | Stock | Unit $ | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U3 | TLV75733PDRVR | C2868428 | 19,821 | 0.360 | WSON-6(2×2) | Extended | `Regulator_Linear:TLV75733PDRV` (PREFIX) | `Package_DFN_QFN:DFN-6-1EP_2x2mm_P0.65mm_EP1x1.6mm` | Thermal-pad confirmed. **PSRR 46 dB@100kHz misses P8's ≥50 dB alone** — met with the input π-filter per architecture; do not drop FB3/bulk caps |
| U4 | TLV9062IDR | C398355 | 151,400 | 0.144 | SOIC-8 | Extended | `Amplifier_Operational:TLV9062` (EXACT) | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | Dual RRIO op-amp, Vos ≈300 µV typ, GBW 10 MHz, ≥10 mA — meets all reference-buffer specs with margin. Chosen over OPA2376/OPA2333 for the exact symbol match and 151k stock |
| FB3 | PBY160808T-601Y-N | C108301 | 841,955 | 0.013 | 0603 | Extended | `Device:FerriteBead` | `Inductor_SMD:L_0603_1608Metric` | analog LDO input filter |
| R8, R9 | generic 1% 0603 | — | — | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | **rev 4: R8 = 22.0 kΩ, R9 = 11.0 kΩ** (VBIAS retargeted 1.200 V → 1.100 V, architecture rev 3 decision 19: 3.3·11.0/33.0 = 1.1000 V exactly). Still a generic 1% 0603 row, sourcer's discretion on MPN — no new part number needed. If concrete parts are wanted, architecture names the same Uniroyal `0603WAF` line used elsewhere on this board: 22.0 kΩ = 0603WAF2202T5E (C31850, Basic+Preferred), 11.0 kΩ = 0603WAF1102T5E (C25950, Preferred). **Do not substitute 23.0 kΩ** — not an E96/E24/E192 value, and the design does not want it |
| R10 | generic, TBD | — | — | — | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | Function not fixed by architecture (U4 gain/filter set) — coder to specify value; jellybean either way |
| R11 | RT0603BRD0719K1L | C861184 | 13,105 | 0.036 | 0603 | Extended | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 19.1 kΩ ±0.1% (E96 nearest to the architecture's "19.0 kΩ" — ratio to R19 still ≈0.95, negligible error) |
| R19 | FRH0603B1001TS | C49196685 | 512,314 | 0.010 | 0603 | Extended | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 1.00 kΩ ±0.1% |
| R22 | generic 1% 0603 | — | — | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | **Added rev 3** — 10 Ω, per architecture rev 2 decision 16: isolates U4A's output (`VBIAS_DRV`) from the capacitively-loaded `VBIAS` node (200–250 pF of `C_bot`×2 + stray) so a 10 MHz-GBW RRIO op-amp doesn't lose phase margin driving it directly. Jellybean, cheapest Basic 1% 0603 part wins |
| C8–C12 | CL05B104KO5NNNC / CL21A106KAYNNNE | C1525 / C15850 | huge | — | 0402 / 0805 | Basic | `Device:C` | as above | decoupling + bulk, coder allocates |

## afe_channel × 2 (ch1: J2/U_buf1/U_fda1/D_clamp1/R101-110/C101-110; ch2 mirrors with J3/…/R201-210/C201-210)

| Ref (ch1 / ch2) | MPN | LCSC# | Stock | Unit $ | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| J2 / J3 | KH-BNC50-3511 | C2837587 | 4,742 | 0.932 | THT, board-side elbow | Extended | ⚠️ SYMBOL NEEDED (generic connector) | `Connector_Coaxial:BNC_Amphenol_031-6575_Horizontal` | **Not found by architect — sourced here.** 50 Ω body, board-edge (board-side elbow), through-hole. Footprint is the closest stocked match; confirm pin spacing against the Kinghelm mechanical drawing before layout |
| U_buf1 / U_buf2 | OPA355NA/3K | C2058090 | 489 (live) | 1.769 | SOT-23-6 | Extended | `Amplifier_Operational:OPA355NA` (PREFIX) | `Package_TO_SOT_SMD:SOT-23-6` | **Critical path — CMOS input mandatory, do not substitute for bipolar.** Stock at 489 is WARN (<500); second source OPA355UA/2K5 (C2059993, SOIC-8) confirmed available |
| U_fda1 / U_fda2 | THS4551IRGTR | C2869590 | 588 (live) | 4.356 | QFN-16-EP(3×3) | Extended | `Amplifier_Difference:THS4551xRGT` (WILDCARD) | `Package_DFN_QFN:WQFN-16-1EP_3x3mm_P0.5mm_EP1.6x1.6mm` | **Critical path.** Second source THS4551IRUNR (C2060364, QFN-10, mirror stock 5,475) — footprint not in stock KiCad libs, would need generation if substituted |
| D_clamp1 / D_clamp2 | BAV99 | C916421 | 2,071,820 | 0.008 | SOT-23 | Extended | `Diode:BAV99` (EXACT) | `Package_TO_SOT_SMD:SOT-23` | |
| R101/201, R102/202 | 0805W8D4753T5E | C407442 | 763 | 0.008 | 0805 | Extended | `Device:R` | `Resistor_SMD:R_0805_2012Metric` | 475 kΩ ±0.5%. **Only one exact 475k/0.5%/0805 SKU in the DB — marginal stock, watch for later re-orders** |
| R103/203 | ARG03DTC4992 | C311894 | 38,550 | 0.010 | 0603 | Extended | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 49.9 kΩ ±0.5% (E96 nearest to "50.0 kΩ") |
| R104/204 | 0603WAF1001T5E | C21190 | 26,496,847 | 0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 1.00 kΩ ±1%, clamp current limit |
| R105/205, R106/206 | PTFR0603B499RP9 | C478882 | 28,087 | 0.040 | 0603 | Extended | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 499 Ω ±0.1% matched pair |
| R107/207, R108/208 | FRH0603B1001TS | C49196685 | 512,314 | 0.010 | 0603 | Extended | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 1.00 kΩ ±0.1% matched to R_g |
| R109/209, R110/210 | generic, 33 Ω | — | — | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | Output RC anti-alias, jellybean |
| **R111/211, R112/212** | PTFR0603B499RP9 | C478882 | 28,010 (live, re-verified rev 4) | 0.0401 | 0603 | Extended | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | **New, rev 4** — `R_mfb`, the new 2nd-order-MFB feedback-to-input resistor (architecture rev 3 decision 18 / WO-1). Same MPN as `R105/106` (`R_g`); board-wide `C478882` usage goes from 4 pcs (R105/106/205/206) to **8 pcs total** with this row's 4 added. 499 Ω ±0.1%, matches the gain-setting pair |
| C_top (C101/201) | STC3MA06-T1 | C22468120 | 1,377–4,712 | 0.34–0.49 | SMD 4.5×3.2mm | Extended | ⚠️ SYMBOL NEEDED (generic `Device:C_Trimmer`) | ⚠️ **CUSTOM FP NEEDED** — closest stocked candidate `Capacitor_SMD:C_Trimmer_Murata_TZB4-A`, confirm pad geometry against the JLC/SEHWA mechanical drawing before layout | **Trimmer, per decision 10 — not substitutable with a fixed cap.** 2–6 pF range: with R_top=950 kΩ, R_bot=49.9 kΩ, target C_top = C_bot_total·(R_bot/R_top) ≈ 89 pF/19 ≈ 4.7 pF — sits mid-range, good choice. See "Decisions" below for the alternative considered and rejected |
| C_bot (C102/202) | TCC0603COG820J500CT | C282510 | 31,900 | 0.005 | 0603 | Extended | `Device:C` | `Capacitor_SMD:C_0603_1608Metric` | 82 pF **±5%** (spec wanted ±2% — no ±2% option in stock at this value/package; trimmer nulls the residual, see Decisions) |
| C_f (C103/203, C104/204) | CL10C100JB8NNNC | C1634 | 1,514,480 (live, rev 4) | 0.0076 | 0603 | Basic | `Device:C` | `Capacitor_SMD:C_0603_1608Metric` | **rev 4: 27 pF → 10 pF** — was `FCC0603N270J500CT`/C5137568. Architecture rev 3 decision 18/WO-1: `C_f` moves from a stray provisional value to a fixed 2nd-order MFB pole term (10.6 pF with THS4551's +0.6 pF internal). C0G ±5% 50 V. Tier improved Extended→Basic |
| C_diff (C105/205) | CL10C331JB8NNNC | C1664 | 906,099 (live, rev 4) | 0.0180 | 0603 | Basic | `Device:C` | `Capacitor_SMD:C_0603_1608Metric` | **rev 4: 470 pF → 330 pF** — was C27694. Architecture rev 3 decision 18: output-RC pole retuned for the 3rd-order Butterworth response. C0G ±5% 50 V. Tier improved Extended→Basic |
| C_cm (C106/206, C107/207) | CL10C101JB8NNNC | C14858 | 3,189,308 (live, rev 4) | 0.0085 | 0603 | Basic | `Device:C` | `Capacitor_SMD:C_0603_1608Metric` | **rev 4: 220 pF → 100 pF** — was C27675. Architecture rev 3 decision 18, same retune as `C_diff`. C0G ±5% 50 V. Tier improved Extended→Basic |
| **C_mfb (C111/211)** | CL10C680JB8NNNC | C28262 | 153,120 (live, rev 4) | 0.0188 | 0603 | Preferred | `Device:C` | `Capacitor_SMD:C_0603_1608Metric` | **New, rev 4** — one differential cap between `mfb_p`/`mfb_n` (architecture rev 3 decision 18/WO-1). **One cap between the two nodes, not two caps to GND** — a cap to real ground here couples into the FDA's common-mode loop. 68 pF C0G ±5%, one per channel |
| C108/208–C110/210 | CL05B104KO5NNNC (100 nF) / generic 1 µF | C1525 | huge | — | 0402/0603 | Basic | `Device:C` | as above | U_buf/U_fda local decoupling |

## adc_dual

| Ref | MPN | LCSC# | Stock | Unit $ | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U5 | ADS5231IPAGT | C2670079 | 154 (live) | 31.772 | TQFP-64(10×10) | Extended | ⚠️ SYMBOL NEEDED | `Package_QFP:TQFP-64_10x10mm_P0.5mm` | **Critical path, single-source, stock 154** (below SPEC Q4's 200 but architecture relaxed this to >100 for U5/U6 — do not escalate absent an EOL/stock-collapse signal). NRND status not in mirror data — **datasheet phase must check TI's lifecycle page**. Datasheet must confirm minimum clock ≤20 MHz (R-1) |
| RA1–RA6 | YC124-JR-0733RL | C125323 | 48,381 | 0.010 | 0402×4 | Extended | ⚠️ SYMBOL NEEDED (generic `Device:R_Pack04`) | `Resistor_SMD:R_Array_Concave_4x0402` | 33 Ω 4-element array, ±5%. 6 needed (24 data lines / 4 per array) |
| C41–C55 | CL05B104KO5NNNC (100 nF, bulk) + CL21A106KAYNNNE (bulk) + one C_vocm ~1 µF | C1525 / C15850 | huge | — | 0402/0805 | Basic | `Device:C` | as above | Decoupling incl. REFT/REFB/C_vocm; coder allocates within range |

## clock_20m

| Ref | MPN | LCSC# | Stock | Unit $ | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| X1 | SX3M20.000B10F20TNN | C5452685 | 3,210 | 0.535 | SMD3225-4P | Extended | ⚠️ SYMBOL NEEDED | `Oscillator:Oscillator_SMD_Abracon_ASE-4Pin_3.2x2.5mm` | 20.000 MHz XO. **Jitter unverified** (R-4) — datasheet phase must confirm ≤5 ps RMS or substitute SiTime SiT8008 / Epson SG-210 class. Second source OT252020MJBA4SL (C669067, stock 8,782) |
| R_s1, R_s2 | generic, 33 Ω | — | — | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | series damping to ADC/FPGA |
| FB4 | PBY160808T-601Y-N | C108301 | 841,955 | 0.013 | 0603 | Extended | `Device:FerriteBead` | `Inductor_SMD:L_0603_1608Metric` | XO supply isolation |
| C56, C57 | CL05B104KO5NNNC | C1525 | huge | 0.005 | 0402 | Basic | `Device:C` | `Capacitor_SMD:C_0402_1005Metric` | XO decoupling |

## fpga_core

| Ref | MPN | LCSC# | Stock | Unit $ | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U6 | GW1NR-LV9QN88PC6/I5 | C5799578 | 180 (live) | 23.312 | QFN-88(0.4mm) | Extended | ⚠️ SYMBOL NEEDED | `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` | **Critical path, single-source, stock 180** (relaxed threshold per architecture). Footprint pin count/pitch matches (QFN-88, 10×10mm, 0.4mm) but exposed-pad size (6.74×6.74mm here) is **not yet confirmed against Gowin's package drawing** — datasheet phase must verify EP size before layout. Confirm supply rails per open question 9(b) |
| J4 | generic 1×6 2.54mm header | — | — | ~0.05 | THT | Basic | `Connector_Generic:Conn_01x06` | `Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical` | JTAG, jellybean |
| J5 | generic 1×2 2.54mm header | — | — | ~0.02 | THT | Basic | `Connector_Generic:Conn_01x02` | `Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical` | Trigger, jellybean |
| D5 | KT-0603R | C2286 | 8,154,450 | 0.007 | 0603 | Basic | ⚠️ SYMBOL NEEDED (generic `Device:LED`) | `LED_SMD:LED_0603_1608Metric` | Red capture LED |
| R13 | 0603WAF2201T5E | C4190 | 2,001,135 | 0.001 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | 2.2 kΩ EEDATA pull-up |
| R15–R18 | generic 10 kΩ / LED series | C25804-class | huge | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | RECONFIG#/trigger pulls + LED resistor, jellybean |
| C23–C40 | CL05B104KO5NNNC + CL21A106KAYNNNE | C1525 / C15850 | huge | — | 0402/0805 | Basic | `Device:C` | as above | U6 core/IO decoupling, coder allocates |

## usb_bridge

| Ref | MPN | LCSC# | Stock | Unit $ | Package | Tier | KiCad symbol | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|---|
| U7 | FT232HL-REEL | C51997 | 2,048 (live) | 9.720 | LQFP-48(7×7) | Extended | `Interface_USB:FT232H` (PREFIX) | `Package_QFP:LQFP-48_7x7mm_P0.5mm` | |
| U8 | 93LC56BT-I/SN | C6164 | 2,384 (live, re-verified 2026-09-20) | 0.560 | SOIC-8 | Extended | `Memory_EEPROM:93CxxC` (WILDCARD — unchanged) | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` (unchanged) | **RE-SOURCED (rev 2): replaces 93C46CT-I/SN-TUDI.** FT_000288 v1.81 §4: EEPROM must be "16 bit wide configuration such as a 93LC56B or equivalent"; the 93C46 (64×16, 1 Kbit) is explicitly the incompatible density FTDI names. 93LC56BT-I/SN is the exact part the datasheet cites: 2 Kbit (128×16), 16-bit org, 2.5–5.5 V supply (covers VCCIO 2.97–3.63 V), 3 MHz clock (exceeds FTDI's 1 Mbit/s minimum). **Pinout is identical to the 93C46** (both CS/SCLK/DI/DO/GND/ORG/NC/VCC in the same SOIC-8 pin numbering) — confirmed against the KiCad `Memory_EEPROM:93CxxC` symbol (pin 6 = named "ORG", matching `U8['ORG']` in `usb_bridge.py`); **no circuit code change needed beyond the `value=` string** the block coder already flagged. Symbol/footprint unchanged from the prior sourcing pass. (2nd-source alternative: 93LC66BT-I/SN, C46698, 4 Kbit, SOP-8, stock 1,785, $0.43 — also valid if 56B ever goes short) |
| X2 | SX32Y012000BC1T001 | C7420720 | 557 | 0.085 | SMD3225-4P | Extended | ⚠️ SYMBOL NEEDED (generic `Device:Crystal`) | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` | 12 MHz, 12 pF load cap (spec exactly). **Recompute C13/C14 external load caps for CL=12pF** (≈16–18 pF each), not the ≈27 pF placeholder in skeleton_bom, which assumed a ~20pF-CL crystal |
| R14 | generic 10 kΩ | C25804-class | huge | ~0.003 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | RESET# pull-up |
| C13, C14 | generic ~16-18pF C0G 0603 | — | — | ~0.005 | 0603 | Basic | `Device:C` | `Capacitor_SMD:C_0603_1608Metric` | X2 load caps — **recompute, see X2 note** |
| C16 | generic 100 nF | C1525-class | huge | 0.005 | 0402 | Basic | `Device:C` | `Capacitor_SMD:C_0402_1005Metric` | RESET# filter |
| C17–C22 | CL05B104KO5NNNC | C1525 | huge | 0.005 | 0402 | Basic | `Device:C` | `Capacitor_SMD:C_0402_1005Metric` | U7 decoupling |
| R_ref | 0603WAF1202T5E | C22790 | 1,377,131 | 0.0031 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | **Added rev 2** — 12 kΩ ±1%, FTDI-mandated REF(5)→GND current-setting resistor (FT_000288 Table 3.2, mandatory). Ref not in any prior ref list; block coder instantiated it directly. Jellybean, no availability risk |
| R_eedo | 0603WAF1002T5E | C25804 | 24,640,329 | 0.0027 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | **Added rev 2** — 10 kΩ, EEPROM DO(4)→FT232H_3V3 pull-up (FT_000288 Table 3.3, mandatory alongside R13's 2.2k series). Same MPN as R14/R15–18 generic 10k for consistency. Jellybean |
| R_pwren | 0603WAF1002T5E | C25804 | 24,640,329 | 0.0027 | 0603 | Basic | `Device:R` | `Resistor_SMD:R_0603_1608Metric` | **Added rev 2** — 10 kΩ, PWREN#(ACBUS8) pull-up, mandatory per FT_000288 Table 3.5 note * once PWREN# moved off ACBUS7. Same MPN as R14 for consistency. Jellybean |
| C_vregin | CL05B104KO5NNNC | C1525 | 27,862,177 | 0.0045 | 0402 | Basic | `Device:C` | `Capacitor_SMD:C_0402_1005Metric` | **Added rev 2** — 100 nF, VREGIN(40) decoupling per §6.1 figure. Same MPN as C17–C22/C56–57 decoupling family. Jellybean |
| C_io24 | CL05B104KO5NNNC | C1525 | 27,862,177 | 0.0045 | 0402 | Basic | `Device:C` | `Capacitor_SMD:C_0402_1005Metric` | **Added rev 2** — 100 nF, VCCIO(24) decoupling (ERC decoupling rule / §6.1). Jellybean |
| C_io46 | CL05B104KO5NNNC | C1525 | 27,862,177 | 0.0045 | 0402 | Basic | `Device:C` | `Capacitor_SMD:C_0402_1005Metric` | **Added rev 2** — 100 nF, VCCIO(46) decoupling (ERC decoupling rule / §6.1). Jellybean |
| C_ee | CL05B104KO5NNNC | C1525 | 27,862,177 | 0.0045 | 0402 | Basic | `Device:C` | `Capacitor_SMD:C_0402_1005Metric` | **Added rev 2** — 100 nF, U8 VCC decoupling (ERC decoupling rule). Jellybean |

## Symbol-check summary (`find-symbol.py`, all active parts)

EXACT: `USBLC6-2SC6`, `BAV99`, `TLV9062IDR`, `AP2161WG-7`→`Power_Management:AP2161W` (rev 3, U9, replaces the retired `Q1`/HL2301A row). WILDCARD: `THS4551IRGTR`→`Amplifier_Difference:THS4551xRGT`,
`93LC56BT-I/SN`→`Memory_EEPROM:93CxxC` (rev 2: re-sourced from `93C46CT-I/SN-TUDI`, same symbol/footprint —
pin 6 is named `ORG` on this symbol, confirmed against `usb_bridge.py`'s `U8['ORG']` reference).
PREFIX (confirm pinout before use):
`FT232HL-REEL`→`Interface_USB:FT232H`, `OPA355NA/3K`→`Amplifier_Operational:OPA355NA`,
`TLV75733PDRVR`/`TLV75801PDRVR`→`Regulator_Linear:TLV75733PDRV`/`TLV75801PDRV`.
MISSING (⚠️ SYMBOL NEEDED, generate in datasheet phase from the pin table):
`ADS5231IPAGT`, `GW1NR-LV9QN88PC6/I5`, `SY8089A1AAC`, `SX3M20.000B10F20TNN`,
`TYPE-C 16PIN 2MD(073)`. Discretes (MOSFET, LEDs, diodes, connectors, passives) use
KiCad's generic library symbols (`Transistor_FET:Q_PMOS_GSD`, `Device:LED`, `Device:D_TVS`,
etc.) — normal practice, not flagged as missing.
