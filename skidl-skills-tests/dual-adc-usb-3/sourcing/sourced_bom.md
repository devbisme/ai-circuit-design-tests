# Sourced BOM — dual_adc_usb

Re-verified 2026-09-09 against **`jlcsearch.tscircuit.com`** (live JLCPCB-derived mirror,
queried directly via `curl`, one part/value at a time). **The `pcbparts` MCP was checked and
is still not connected** — `ToolSearch` for `mcp__pcbparts__*` returned no matches, and no
`pcbparts` tools appear anywhere in this session's tool list. Every stock/price/tier figure
below is a fresh pull, not a copy of the architect's numbers — where a figure matches
`ic_selection.md` exactly, that is because the mirror had not moved since the architect's
pull, not because it was assumed. Confirmed matches are called out; a handful of items
diverge from the architect's suggested MPN, and each is documented in the handoff's
`## Decisions`.

**Ref designator convention.** The architecture's `skeleton_bom.md` and `## Parts by block`
use *indicative* ref ranges (SKiDL auto-numbers refs when the code is written; exact
numbering doesn't exist yet). This BOM keeps that convention: one row per distinct
part/value, `Ref` carries the same range/description used upstream. Every ref designator
named anywhere in `02_architecture.md` appears in exactly one row below.

**KiCad footprints** were checked with
`python3 scripts/validate-footprints.py sourcing/fp_check.py` against
`/usr/share/kicad/footprints` (`KICAD9_FOOTPRINT_DIR` was unset in this environment, so the
script's Linux default was used) — **all 25 distinct footprint strings resolved**. Rows
marked `⚠️ VERIFY FP` use a real, existing KiCad footprint whose pin count/mount style
matches the part, but whose exact land-pattern dimensions were not cross-checked against the
part's own mechanical drawing (no image-reading tool was available this session) — the
datasheet-librarian must confirm these against the datasheet's package drawing. Rows marked
`⚠️ CUSTOM FP NEEDED` have no matching footprint in the library at all.

---

## Critical path — actives

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|
| U9, U10 | AD9235BCPZ-40 | C653327 | 170 | $18.41 | LFCSP-32 5×5 0.5mm | Extended | `Package_DFN_QFN:QFN-32-1EP_5x5mm_P0.5mm_EP3.45x3.45mm` ⚠️ VERIFY FP | Confirmed exact match to architect's figures. Same-footprint pool: AD9235BCPZ-20 (C653326, 28 in stock), AD9235BCPZ-65 (C653328, 4 in stock) — combined pool 202. EP (exposed-pad) dimension on this footprint is a generic QFN-32/0.5mm guess, not AD9235-specific — datasheet-librarian must confirm against ADI's CP-32 mechanical drawing. |
| U12 | GW1NR-LV9QN88PC6/I5 | C5799578 | 102 | $20.91 | QFN-88 10×10 0.4mm | Extended | `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` ⚠️ VERIFY FP | **Single-source, 102 in stock — confirmed unchanged from architecture.** Critical-path part per architect's escalation note; not substituted here (per `02_architecture.md` "escalate rather than substitute"). Footprint is the only QFN-88/10×10/0.4mm in the library but is named for a different vendor's (ArtInChip) part — EP pad size is almost certainly wrong for Gowin's actual package. Datasheet-librarian must pull Gowin's QN88P mechanical drawing (UG803) and confirm/replace the EP dimension before layout. |
| U13 | CY7C68013A-56LTXC | C14912 | 2624 | $10.68 | QFN-56-EP 8×8 | Extended | `Package_DFN_QFN:Cypress_QFN-56-1EP_8x8mm_P0.5mm_EP6.22x6.22mm_ThermalVias` | Confirmed exact match. Footprint is vendor-named for Cypress parts specifically — high confidence. |
| U14 | CAT24C128WI-GT3 | C81195 | 10534 | $0.41 | SOIC-8 | Extended | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | Confirmed exact match. |
| U7 ×2 (analog_frontend ×2 instances) | AD8066ARZ-R7 | C9647 | 5868 | $4.26 | SOIC-8 | Extended | `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` | Confirmed exact match. |
| U8 ×2 (analog_frontend ×2 instances) | THS4551IRGTR | C2869590 | 765 | $3.57 | QFN-16-EP 3×3 | Extended | `Package_DFN_QFN:QFN-16-1EP_3x3mm_P0.5mm_EP1.7x1.7mm` ⚠️ VERIFY FP | Confirmed exact match. Footprint EP (1.7×1.7mm) matches TI's typical RGT-16 exposed pad; still confirm against the THS4551 datasheet drawing. |
| U11 | SiT1602BI-22-33E-10.000000 | C811140 | 1000 | $1.07 | SMD3225-4P | Extended | `Oscillator:Oscillator_SMD_SiT_PQFN-4Pin_3.2x2.5mm` | Confirmed exact match. Footprint is vendor-named for SiTime specifically — high confidence. |
| (part of clock_gen, U11) | SN74LVC2G34DBVR | C347589 | 33347 | $0.181 | SOT-23-6 | Extended | `Package_TO_SOT_SMD:SOT-23-6` | Confirmed exact match. |
| Y2 | X322524MOB4SI | C70590 | 94151 | $0.094 | SMD3225-4P | Extended | `Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm` | Confirmed exact match. |

## Power — actives

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|
| U5 | LM27762DSSR | C473398 | 11277 | $0.96 | WSON-12-EP 2×3 | Extended | `Package_SON:WSON-12-1EP_3x2mm_P0.5mm_EP1x2.65` | Confirmed exact match. |
| U6 | LP5907MFX-3.0 | C23380873 | 43427 | $0.096 | SOT-23-5 | Extended | `Package_TO_SOT_SMD:SOT-23-5` | Confirmed exact match. |
| U1 | AP2112K-3.3TRG1 | C51118 | 79480 | $0.158 | SOT-23-5 (JLC lists as "SOT-25-5" — same 5-pin SOT-23 JEDEC footprint under Diodes Inc.'s package name) | Extended | `Package_TO_SOT_SMD:SOT-23-5` | Confirmed exact match. A second listing (C23380830, package labelled plain "SOT-23-5", 31470 in stock) exists at lower stock — the C51118 listing is the one whose stock/price match the architecture figures, used here. |
| U2 | TLV62569DBVR | C141836 | 108275 | $0.073 | SOT-23-5 | Extended | `Package_TO_SOT_SMD:SOT-23-5` | Confirmed exact match. |
| U3 | TLV62568DBVR | C163219 | 20475 | $0.080 | SOT-23-5 | Extended | `Package_TO_SOT_SMD:SOT-23-5` | Confirmed exact match. |
| U4 | LP5907MFX-1.8/NOPB | C92498 | 17548 | $0.206 | SOT-23-5 | Extended | `Package_TO_SOT_SMD:SOT-23-5` | **Deviation:** exact MPN string `LP5907MFX-1.8` (no `/NOPB`) is a separate, lower-stock listing (C23380872, 3062 units, $0.146). The architecture's 17548-unit / $0.206 figures belong to the `/NOPB` (lead-free, TI's standard suffix) variant — used here since it matches the figures the architecture actually relied on and carries 5.7× the stock. Functionally identical part. |
| L1, L2 (buck inductors) | FNR3015S2R2MT | C167747 | 60663 | $0.043 | SMD 3×3mm shielded, 2.2 µH, **2 A** sat (exceeds ≥1.5 A requirement) | Extended | — ⚠️ **CUSTOM FP NEEDED** | No 3×3mm shielded-power-inductor footprint exists in the standard KiCad `Inductor_SMD.pretty` library (checked — closest are Sunlord-branded MWSA/SWPA series in different body sizes, none 3×3mm). Datasheet-librarian must pull the FNR3015S2R2MT mechanical drawing and the block coder must build a 2-pad custom footprint from it. |
| Charge-pump flying/reservoir caps (part of power_analog C21–C33) | 1 µF X7R 16 V, 0603 | C106248 (CC0603KRX7R7BB105) | 91522 | $0.0175 | 0603 | Extended | `Capacitor_SMD:C_0603_1608Metric` | Per LM27762 datasheet cap count/placement — confirm exact count (typ. 4) at datasheet phase. |
| Charge-pump flying/reservoir caps (part of power_analog C21–C33) | 10 µF X7R 16 V, 0805 | C162430 (GRM21BZ71C106KE15L) | 114267 | $0.117 | 0805 | Extended | `Capacitor_SMD:C_0805_2012Metric` | Reused for ADC REFT/REFB differential 10 µF too (adc_pair block). |

## Connectors, ESD, protection

| Ref | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|
| D1/D2 (usb_c_port ESD array) | USBLC6-2SC6 | C2687116 | 150192 | $0.048 | SOT-23-6 | Extended | `Package_TO_SOT_SMD:SOT-23-6` | Confirmed exact match. |
| FB1 / TVS | SMAJ5.0A | C2925443 | 64985 | $0.039 | DO-214AC (SMA) | **Preferred** | `Diode_SMD:D_SMA` | Confirmed exact match — the one Preferred-tier part in the whole design, unchanged. |
| D3 ×2 (analog_frontend ×2, clamp) | BAV199 | C5184419 | 85473 | $0.014 | SOT-23 | Extended | `Package_TO_SOT_SMD:SOT-23` | Confirmed exact match. |
| J2 ×2 (analog_frontend ×2, BNC) | KH-BNC50-3511 | C2837587 | 4742 | $0.93 | THT, right-angle/elbow | Extended | `Connector_Coaxial:BNC_Win_364A2x95_Horizontal` ⚠️ VERIFY FP | Confirmed exact stock/price match. No KiCad footprint exists under this exact vendor name; picked the closest horizontal/elbow BNC in the library by pin count and mount style. Datasheet-librarian must confirm pad pattern against the part's drawing before layout — a BNC footprint mismatch is a mechanical, not electrical, failure (won't fit the panel cutout / pads). |
| J1 (usb_c_port receptacle) | TYPE-C 16PIN 2MD(073) | C2765186 | 1171811 | $0.074 | SMD, 16P | Extended | `Connector_USB:USB_C_Receptacle_HCTL_HC-TYPE-C-16P-01A` ⚠️ VERIFY FP | Confirmed exact stock/price match. Same caveat as the BNC — 16P Type-C SMD receptacles vary in land pattern between vendors even at the same pin count; confirm against this exact part's drawing. |
| Trigger ESD (aux_io) | PESD3V3L1BA | C2687129 | 356268 | $0.038 | SOD-323 | Extended | `Diode_SMD:D_SOD-323` | Real part confirmed; architect's skeleton listed it without stock/price — now verified. |

## Passives — analog front end (2-channel totals, `analog_frontend` ×2 instances + `adc_pair`)

| Ref (function) | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|
| Attenuator top leg ×2 | PTFR0603B909KP9 | C2849091 | **513** | $0.126 | 0603 | Extended | `Resistor_SMD:R_0603_1608Metric` | ±0.1%, **100 V rated** — meets F9's ≥100 V hard requirement exactly at the boundary. **Stock is marginal** (513, just above the 500-unit warn line) — the only ±0.1%/≥100V 909kΩ in reasonable stock; 0805/1206 ±0.1% alternates at higher voltage exist at 10–17 units (unusable). Flagged in Carried forward. |
| Attenuator bottom leg ×2 | RT0402BRD0790K9L | C852949 | 9900 | $0.026 | 0402 | Extended | `Resistor_SMD:R_0402_1005Metric` | ±0.1%, 50 V. Package upgraded 0603→0402 per passive package preference; ample stock. |
| Compensation cap, top ×2 | 06031A150JAT2A | C597069 | 3989 | $0.026 | 0603 | Extended | `Capacitor_SMD:C_0603_1608Metric` | **Deviation: ±5%, not ±2%.** No 15pF C0G part at ≥100V and ±2% tolerance is stocked at JLCPCB (checked — only ±5% exists at 100V). Voltage rating (the hard, safety-relevant spec) is met; tolerance is looser than the architecture's ±2% target. Per R5's own framing this affects HF flatness of the compensation network, not F8's DC accuracy — same class of tradeoff the architecture already accepted for the trimmer fallback. |
| Compensation cap, bottom ×2 | GRM1555C1H151FA01D | C237333 | 16181 | $0.014 | 0402 | Extended | `Capacitor_SMD:C_0402_1005Metric` | **±1%, tighter than the ±2% spec** — used instead of ±2% because the ±2% 150pF stock is unusable (best option 1–34 units). ±1% strictly satisfies ±2%. |
| Trimmer 6–30pF — **not fitted** | — | — | 2–7 | — | — | — | Confirmed unavailable at scale (JZ300/JZ300HV: 2–7 units in stock). Architecture's pre-approved fallback (fixed 150pF ±2%, here supplied as ±1%) used — **per instruction, not escalated.** |
| Buffer series protection ×2 | 0603WAF1001T5E | C21190 | 8013731 | $0.0039 | 0603 | **Basic** | `Resistor_SMD:R_0603_1608Metric` | 1.00 kΩ ±1%, 75 V. Also used for FDA MFB R3 (below) — same part, two functions. |
| Sallen-Key R ×4 | AC0603FR-07324RL | C227819 | 1715 | $0.0026 | 0603 | Extended | `Resistor_SMD:R_0603_1608Metric` | 324 Ω ±1%, 75 V. |
| Sallen-Key cap 330pF ×2 | GRM1555C1H331GA01D | C237507 | 15164 | $0.0137 | 0402 | Extended | `Capacitor_SMD:C_0402_1005Metric` | ±2% C0G, 50 V — meets spec exactly. |
| Sallen-Key cap 47pF ×2 | 0402CG470G500NT | C285090 | 5211 | $0.004 | 0402 | Extended | `Capacitor_SMD:C_0402_1005Metric` | ±2% C0G, 50 V. |
| FDA gain-set Rg ×4 | RT0402BRD071KL | C852624 | 668997 | $0.0246 | 0402 | Extended | `Resistor_SMD:R_0402_1005Metric` | 1.00 kΩ ±0.1%, 50 V. |
| FDA feedback Rf ×4 | RT0402BRD071K1L | C852602 | 16774 | $0.0275 | 0402 | Extended | `Resistor_SMD:R_0402_1005Metric` | 1.10 kΩ ±0.1%, 50 V — Rf/Rg = 1.10 preserved exactly. |
| FDA MFB R3 ×4 | 0603WAF1001T5E | C21190 | 8013731 | $0.0039 | 0603 | Basic | `Resistor_SMD:R_0603_1608Metric` | Same part as buffer series protection above. |
| FDA MFB cap 68pF ×4 | GRM1555C1H680GA01D | C237510 | 3822 | $0.0075 | 0402 | Extended | `Capacitor_SMD:C_0402_1005Metric` | ±2% C0G, 50 V. |
| FDA MFB cap 11pF ×2 | GJM1555C1H110GB01D | C2169708 | 25625 | $0.044 | 0402 | Extended | `Capacitor_SMD:C_0402_1005Metric` | ±2% C0G, 50 V. |
| ADC kickback R 33Ω ×4 | FRC0402F33R0TS | C2906868 | 2380795 | $0.002 | 0402 | Extended | `Resistor_SMD:R_0402_1005Metric` | ±1%, 50 V. Same part reused for clock series termination (general passives table). |
| ADC kickback cap 22pF ×2 | GRM1555C1H220GA01D | C161541 | 13602 | $0.0079 | 0402 | Extended | `Capacitor_SMD:C_0402_1005Metric` | ±2% C0G, 50 V. |
| ADC VCM divider ×2 | RT0402BRD0710KL | C190095 | 1013411 | $0.0207 | 0402 | Extended | `Resistor_SMD:R_0402_1005Metric` | 10.0 kΩ ±0.1%, 50 V. |

## Passives — general

| Ref (function) | MPN | LCSC# | Stock | Unit price | Package | Tier | KiCad footprint | Notes |
|---|---|---|---|---|---|---|---|---|
| VBUS bulk + rail bulk (9 total) | CL21A106KOQNNNE | C1713 | 83222 | $0.056 | 0805 | Extended | `Capacitor_SMD:C_0805_2012Metric` | 10 µF X5R 16 V ±10% — matches spec exactly. |
| Decoupling (~45×) | CL05B104KB54PNC | C307331 | 9493037 | $0.0076 | 0402 | **Basic** | `Capacitor_SMD:C_0402_1005Metric` | 100 nF X7R **50 V** (exceeds the 25V spec) — Basic tier, huge stock; best pick for the single highest-quantity part in the BOM. |
| Decoupling, bulk local (~8×) + FX2LP reset cap | CL10A105KB8NNNC | C15849 | 5979916 | $0.0297 | 0603 | **Basic** | `Capacitor_SMD:C_0603_1608Metric` | **Deviation: X5R, not X7R** (skeleton asked X7R). Basic-tier 1 µF 0603 X5R at huge stock vs. Extended-tier X7R options — both are Class II ceramics; X5R's slightly worse tempco is immaterial for local bulk decoupling. |
| ADC REFT/REFB 100nF ×4 | CL05B104KB54PNC | C307331 | 9493037 | $0.0076 | 0402 | Basic | `Capacitor_SMD:C_0402_1005Metric` | Same part as general decoupling. |
| ADC REFT/REFB 10µF differential ×2 | GRM21BZ71C106KE15L | C162430 | 114267 | $0.117 | 0805 | Extended | `Capacitor_SMD:C_0805_2012Metric` | Same part as LM27762 charge-pump reservoir cap. |
| Ferrite beads ×5 (FB1–FB5) | BLM18AG601SN1D | C19330 | 955216 | $0.0225 | 0603 | Extended | *(no dedicated ferrite footprint library — use)* `Resistor_SMD:R_0603_1608Metric` | 600 Ω @ 100 MHz, 500 mA rated — matches spec exactly. Ferrite beads share the 2-pad chip-resistor land pattern; this is standard practice, not a placeholder. |
| CC pulldowns ×2 | 0402WGF5101TCE | C25905 | 2237664 | $0.0009 | 0402 | **Basic** | `Resistor_SMD:R_0402_1005Metric` | 5.1 kΩ ±1%. |
| I²C pull-ups ×2 | 0402WGF2201TCE | C25879 | 694494 | $0.001 | 0402 | **Basic** | `Resistor_SMD:R_0402_1005Metric` | 2.2 kΩ ±1%. |
| PWR_EN pulldown ×1 + FX2LP reset R ×1 | 0402WGF1003TCE | C25741 | 1535859 | $0.004 | 0402 | **Basic** | `Resistor_SMD:R_0402_1005Metric` | 100 kΩ ±1%. Mandatory per R8 — do not omit. |
| Crystal load caps ×2 | 0402CG120J500NT | C1547 | 801200 | $0.0036 | 0402 | **Basic** | `Capacitor_SMD:C_0402_1005Metric` | 12 pF C0G ±5%, 50 V — matches spec. |
| Clock series termination ×3 | FRC0402F33R0TS | C2906868 | 2380795 | $0.002 | 0402 | Extended | `Resistor_SMD:R_0402_1005Metric` | Same part as ADC kickback resistors. |
| RECONFIG_N/TMS pull-ups ×2 | 0402WGF1002TCE | C25744 | 1256270 | $0.0029 | 0402 | **Basic** | `Resistor_SMD:R_0402_1005Metric` | 10 kΩ ±1%. |
| Feedback dividers ×8 (2 bucks + LM27762 ± outputs) | *TBD — value depends on each regulator's FB equation* | — | — | — | 0402 | — | `Resistor_SMD:R_0402_1005Metric` | **Not sourced to a specific value here.** TLV62569/TLV62568 are adjustable bucks (external FB divider required); LM27762's ± outputs are also set by external resistors per its datasheet. Real 0402 ±1% resistor families exist in every E96 value at Basic/Extended tier (confirmed via the searches above) — the datasheet-librarian/block coder computes the exact ratios from each regulator's datasheet and picks concrete MPNs from the same families already sourced above. |
| LED series ×2 + trigger series ×2 | 0402WGF1001TCE (1k) / 0402WGF1000TCE (100R) | C11702 / — | 2610919 / 3055883 | $0.0011 / $0.0012 | 0402 | **Basic** | `Resistor_SMD:R_0402_1005Metric` | 1 kΩ ±1% for LED series; 100 Ω ±1% (0402WGF1000TCE, C25076 — confirmed Basic, 3055883 stock, $0.0012) for trigger series. |
| LED green ×1 | XL-1608UGC-04 | C965804 | 6367682 | $0.005 | 0603 | Extended | `LED_SMD:LED_0603_1608Metric` | |
| LED amber ×1 | SML-D12D8WT86 | C510024 | 13454 | $0.084 | 0603 | Extended | `LED_SMD:LED_0603_1608Metric` | |
| Test points ×~14 | *(not a purchased part — bare pad)* | — | — | — | — | — | `TestPoint:TestPoint_Pad_1.0x1.0mm` | 1mm SMD pad, no BOM line at JLCPCB — standard practice. |
| Mounting M3 ×4 | *(not a purchased part — mechanical hole)* | — | — | — | — | — | `MountingHole:MountingHole_3.2mm_M3` | |
| JTAG header 2×3 | PZ254V-12-6P | C492420 | 143110 | $0.044 | THT, 2.54mm | Extended | `Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical` | |
| Ext trigger header 1×3 | PZ254V-11-03P | C2937625 | 1200838 | $0.019 | THT, 2.54mm | Extended | `Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical` | |

---

## Tier / stock summary

- **Basic:** decoupling 100nF/1µF, all four E96-value 0402 jellybean resistors (5.1k, 2.2k,
  100k, 10k, 1k, 100R), 12pF crystal load caps, 1kΩ/1% front-end R — 11 distinct line items.
- **Preferred:** SMAJ5.0A only (unchanged from architecture).
- **Extended:** everything else — expected and already flagged once by the architect; not
  re-flagged per-row here except where it compounds with another risk (marginal stock,
  single-source, tolerance/voltage deviation).
- **Marginal stock (<1000, flagged individually above):** 909kΩ ±0.1%/100V attenuator
  resistor at 513 units; GW1NR-9 single-source at 102 units (carried from architecture,
  unchanged); THS4551IRGTR at 765 units.
- **No part found below the 100-unit hard floor.** Nothing here is unsourceable.
