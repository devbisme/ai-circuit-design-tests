# Design Review — dual_adc_usb

Reviewed 2026-09-11 by the pipeline driver. Entry point `handoffs/06_erc.md`; every handoff's
`## Carried forward` was traced to a disposition below.

## Summary
ERC: PASS (re-run after review fixes: 0 errors, 0 warnings; 204 parts) | Architecture: OK, 1 accepted risk | Code: OK, minor style
0 HIGH, 3 MEDIUM (2 fixed, 1 accepted risk), 14 LOW/INFO (5 fixed/resolved)

Footprints: `validate-footprints.py circuits/dual_adc_usb` → 34/34 valid.

## Fixes applied in this review
| Ref | Change | Source |
|---|---|---|
| C98, C99 (new) | 2.2 µF 0603 (0603B225K160NT, C43922 — existing BOM line) on ADC_REFT_C / ADC_REFB_C, parallel to C50/C51 | TI SBAS295A Fig. 21 p.19 |
| R70, R71 | 4.7 kΩ → 1 kΩ (0402WGF1001TCE, C11702 — existing BOM line) MODE0/MODE1 pull-downs | Gowin UG290 v2.9.1E, "Dual-purpose Pin Configuration": "4.7K pull-up or 1K pull-down" |
| R75 (new) | 4.7 kΩ DONE (U15.10) → VD_1V8; new net FPGA_DONE | UG290 pin-state tables: DONE "Pullup (Recommended)"; UG803: IOL14A/DONE = QN88P pin 10 |
| C76 | (earlier, driver) moved from FT_VCORE to VD_3V3 | FTDI DS_FT232H v1.81 Fig. 6.3 p.53 |
| `sourcing/sourced_bom.md` | J2/J3 and VC1/VC2 footprints → ProjectLocal; C98/C99, R70/R71, R75 rows | coding handoffs |

## Findings
| # | Severity | Area | Issue | Status / suggested fix |
|---|----------|------|-------|------------------------|
| 1 | MEDIUM | adc | REFT/REFB had only 2 Ω + 0.1 µF; TI Fig. 21 also shows 2.2 µF per node | **Fixed** — C98/C99 |
| 2 | MEDIUM | fpga_core | MODE pull-downs 4.7 kΩ against internal weak pull-ups; Gowin recommends 1 kΩ | **Fixed** — R70/R71 = 1 kΩ. MODE[2:0]=000 = AUTO BOOT confirmed (UG290 Table 5-1; MODE2 unbonded → grounded) |
| 3 | MEDIUM | analog_front_end | 2nd-order anti-alias, −3 dB 4.64 MHz, only −14.5 dB at 15 MHz. At 20 MSPS, input content at 15–20 MHz folds into 0–5 MHz and the FPGA decimator cannot remove it | **Accepted risk** (architect, `design_risks.md`). Options: (a) accept, document that users must band-limit (recommended for a scope-style front end); (b) 4th-order filter after the buffer (+2 op-amps, more noise/offset); (c) run the ADC at 40 MSPS (its max) with 4:1 decimation in the FPGA — first fold-in band moves to 35 MHz (≈ −28 dB); needs a 40 MHz XO, more ADC power, USB rate unchanged |
| 4 | LOW | fpga_core | DONE (pin 10) was NC; Gowin recommends pull-up | **Fixed** — R75 |
| 5 | LOW | fpga_core | PSRAM bank unproven (06_erc N4) | **Resolved** — UG803 "Recommended Operating Conditions of QN88P": VCCIO3 "connected to PSRAM", 1.71–1.89 V. Pins 68–77 = bank 1, 79–88 = bank 3 (UG803 table, UG119 Fig. 3-8) |
| 6 | LOW | fpga_core | GCLK pins unproven (06_erc N5) | **Resolved** — UG803: pin 35 = IOB29A/GCLKT_4, pin 52 = IOR17A/GCLKT_3 |
| 7 | LOW | fpga_core | TCK pull-down value `[VERIFY UG290]` | **Resolved** — UG290: "TCK needs to connect a 4.7K pull-down" = R73 |
| 8 | LOW | sample_clock | X1 jitter undocumented (no datasheet figure) | **Open, low risk.** Jitter-limited SNR = −20·log(2π·f·σ): F11 (ENOB ≥ 10 at 1 MHz) needs σ ≲ 126 ps; full 62 dB at 5 MHz needs ≲ 25 ps. Commodity CMOS XOs are typically single-digit ps phase jitter (general knowledge, not verified for this part). Measure SNR at 1 and 4.9 MHz on first article |
| 9 | LOW | power_rails / io_expansion | LED1/2/3 at ≈0.4–0.8 mA (1 kΩ, Vf 2.5–3.0 V@5 mA, 150–350 mcd@5 mA per JLC C52675989) | **No change** — visible as indicators. Options: keep 1 kΩ (recommended); 330 Ω (C25104 / C23138, Basic) for ~2 mA |
| 10 | LOW | bipolar_supply | ±2.5 V sag through FB3/FB4 (outside LM27762 loop) | **No change** — ~15 mA × ~0.2 Ω ≈ 3 mV DC; OPA354 PSRR absorbs it |
| 11 | LOW | symbols | `symbols/dual_adc_usb.kicad_sym` ADS5231: CLK typed output, DVA/DVB typed power-in (datasheet: input / outputs). Overridden on the U12 instance only | Fix the library pin types before reusing the symbol |
| 12 | LOW | docs | `datasheets/GW1NR-LV9QN88PC6-I5_SUMMARY.md` puts pins 68–88 in Bank 0; `datasheets/ADS5231IPAGT_SUMMARY.md` calls DVA/DVB supplies | Correct the summaries (circuit is right) |
| 13 | LOW | io_expansion | J5.1 exposes VD_3V3 on an external header, unprotected | Optional: series PTC or 10 Ω on J5.1 |
| 14 | LOW | layout | Custom footprints J2/J3 (BNC), VC1/VC2 (trimmer) generated, not library; U15 EP 6.74 mm vs Gowin 6.8 mm nominal | Eyeball against drawings before fab; put VC1/VC2 adjust screw on the BNC side |
| 15 | LOW | sourcing | Single-source/low-stock: ADS5231, GW1NR-9, BNC-KWE-6 (615 in stock) | Buy kits for all prototypes up front |
| 16 | LOW | code | 8/9 blocks pass MPN/LCSC as `Part()` kwargs (lost in SKiDL 3.0.0) and rely on the `__main__` post-pass; `C_DECOUP_*` naming not used (work-order refs mandated) | Works as built; normalise to `part.fields` if blocks are reused standalone |
| 17 | INFO | gateware/firmware | Obligations: U15.72 (ADC_DVA) is an **input**; pulse ADS5231 SEL after power-up if serial I/F used (SBAS295A p.12); 2:1 half-band decimation; program internal flash via J4 (1.8 V JTAG, programmer must follow VREF) before AUTO BOOT; FT232H EEPROM (U14) must be set for 245 FIFO + bus-powered | For the firmware/gateware effort (out of scope) |
| 18 | INFO | docs | `architecture/net_plan.md` §8 still shows DONE NC and MODE 4.7 kΩ | Superseded by this review and the code |
| 19 | INFO | SKiDL | `gen_xml.py:67` iterates `net.pins` unsorted → BOM XML node order unstable; root node `tag=""` trips `check_tags()` (false-positive warning) | Tool issues, not design |

## Requirements check (SPEC.md HARD items)
2 ch, ±10 V, 10 MSPS, 12 b, BNC, 1 MΩ, USB 2.0 HS, bus-powered ≤ 450 mA (364 mA worst-case estimate, FPGA/FT232H ±30 %), simultaneous sampling, ≥16 k samples/ch buffer (PSRAM), ESD, JTAG — all present. Streaming (SOFT) is best-effort at 30 of ~40 MB/s.
