# Review report — dual_adc_10msps (phase 6, revision 1)

0 errors, 3 warnings, 9 notes. Design is PASS.

## Gate summary
| Gate | Result |
|---|---|
| SKiDL ERC | 0 errors, 1 warning (U1001.73 SUSPEND vs #FLG001, accepted) |
| KiCad ERC | 0 errors; 258 `lib_symbol_mismatch` (generated-library cache, accepted), 1 `pin_to_pin` (same SUSPEND tie, accepted) |
| Parity | ok, 217/217 nets |
| `boardforge review` | WARN: 43 PASS, 0 FAIL, 13 NOT CHECKED (12 `ac_gain` + `DS:coverage`) |
| `ac_gain` HARD/SOFT/ASSUMED, re-evaluated (see W1) | 12/12 PASS with boardforge's own checker; only change is a pin-name alias for the OPA2810 symbol |
| `rail_current` | 5/5 PASS |
| `DS:` supply checks | 17/17 PASS; DS:coverage (LED, Y901) checked by hand, OK |
| `PKG:` | 19/19 PASS (29/29 footprints found) |
| `BOM` | PASS, 239 parts / 75 rows (18 "confirm by hand" package-name notes, all consistent) |
| Netlist stability | components, nets and UUIDs identical across two runs; only the pin order inside 4 multi-unit symbol definitions changes (N1) |

## SPICE path results (channel A = channel B)
These come from `spice_path.check` run on `build/netlist.json`, with `VIN1±/VO1/VIN2±/VO2` added to the op-amp pin-role tables. Script and output: `build/reports/spice_patched/`.
| ID | Tag | Result | Limit |
|---|---|---|---|
| GAIN-A/B | HARD | -20.87 dB | -21.6 … -20.2 |
| FLAT-A/B-1M | SOFT | +0.01 dB | ±0.5 |
| FLAT-A/B-500K | SOFT | +0.01 dB | ±0.5 |
| ALIAS-A/B | HARD | -80.86 dB @5 MHz | ≤ -72 |
| ALIAS-A/B-10M | HARD | -123.3 dB | ≤ -72 |
| ALIAS-A/B-40M | ASSUMED | -211 dB | ≤ -72 |
Cross-check: `architecture/afe_nominal.cir` gives the same values (1 kHz -20.87 dB, 5 MHz -101.7 dB absolute, which is -80.9 dB relative; f-3dB 1.354 MHz). U101_A and U101_B were each modelled separately (`XU101_A`, `XU101_B`). D101/D201 (clamps) and U301 (ADC input) are left open, and J101/J201 are left out.

## Findings (by severity)

### WARNING
**W1 — The official SPICE gate cannot see the OPA2810 halves (tool limitation; not a design fault).**
`spice_path.amp_units`/`role_is_out` only recognise output pins named `""/~/OUT/VOUT`, and `OPAMP_ROLES` has no `VIN1+`-style names. So the custom symbol `dual_adc_10msps:OPA2810IDR` (pins VIN1-/VIN1+/VO1, VIN2+/VIN2-/VO2) is treated as one part with no amplifier unit. A `[review.models] pins` entry can't fix this, because it maps one role set per part, and a dual needs two. That is why no toml entry was added. Re-evaluated as above: all 12 pass. To make `review.json` itself show PASS, do one of these:
(a) **boardforge upstream**: treat any `output`-type pin in a unit as `out`, and accept `VIN\d[+-]` and `VO\d` names. Or
(b) **datasheet-librarian** renames the OPA2810IDR unit pins to `+`, `-`, `~` (KiCad convention, the same as OPA810xDBV). Then the **skidl-block-coder (afe_channel)** changes `U1['VIN1+']`… to pin numbers (3, 2, 1, 5, 6, 7).
Owner: boardforge maintainer (preferred), or librarian + afe_channel coder. Not blocking.

**W2 — ADS5231 AVDD/VDRV power-up skew (circuit-architect).** The abs max for |AVDD−VDRV| is 0.3 V (datasheet p2). AVDD (U701 LP5907, EN tied to +5VA, tON 80–150 µs) is up about 0.65 ms before VDRV (U601 TLV62569 tSS 800 µs → FB301 → +3V3_ADCIO). For that time the difference is up to about 3 V, on every power-up. TI's own recommended sequence (p10 "Recommended power-up sequencing": t3 = -10…+10 ms between the rails, ramps 10–50 ms) allows a larger skew than this, so I don't rate it as a damage risk (MEDIUM, SOFT). Cheap fix: drive U701 EN from `+3V3` instead of `+5VA`, so AVDD starts once VDRV's source is rising: `v3v3 += u701['EN']` (power_analog would need the `+3V3` net added to its signature). Ramps are also faster than the recommended 10 ms minimum. After power-up, use a SEL low pulse (FPGA) to reset the registers, which the gateware already plans.

**W3 — FT232H VREGIN at its minimum (circuit-architect, SOFT).** In 3.3 V mode, FT_000288 gives VREGIN as 3.3 / 3.3 / 3.6 V. +3V3 is 0.6 × (1 + 453k/100k) = 3.318 V nominal. With the FB tolerance and 1 % resistors it can fall to about 3.25 V, below the stated minimum. Raising it is limited by Spartan-6 VCCO/VCCAUX ≤ 3.45 V. Possible change: R601 → 464k (3.38 V nominal). Otherwise accept, since FTDI's own reference designs run from a nominal 3.3 V rail.

### NOTES
- N1 — Netlist: `symbols.<lib_id>.units[*].pins` order varies run to run for OPA2810IDR, THS4551xRGT, 74LVC2G34 and XC6SLX4-TQG144. `components`/`nets` (UUIDs, values, connectivity) are identical, so KiCad placement is preserved. This is tool-side (SKiDL/boardforge symbol export); the coder's claim checked out.
- N2 — ADS5231 PLL: in the default PLL-enabled mode it is specified for 20–40 MSPS only. At 10 MSPS the gateware must write DISABLE_PLL through SEL/SEN/SCLK/SDATA, which the hardware supports (U1001 pins 87/85/84/83, 10k pull-downs R304–R307).
- N3 — J1002 TRIG_IN has only 100 Ω (R1014) + 10k (R1015) in front of U1001.80, with no clamp. 5 V logic would inject about 12 mA into the I/O clamp. Not a SPEC requirement; fit a series 1k or a clamp if external 5 V triggers are expected.
- N4 — DS:coverage, checked by hand. D601/D1002/D1003 PSC-1608U52GC-G4 at 3.3 V via 1k gives ≤1 mA, fine. Y901 TXM12M (no datasheet): Crystal_GND24 pins 1/3 → FT_XI/FT_XO, 2/4 → GND. The pinout is UNVERIFIED and the ±40 ppm total is outside FTDI's ±30 ppm, so eyeball it before fab.
- N5 — Supply spans verified: OPA2810/OPA810 across ±3.98 V = 7.97 V (abs max 28 V); THS4551 0–3.3 V (5.5 V); LM27762 VIN 5 V (5.8 V).
- N6 — Signal levels: every FPGA bank VCCO is +3V3 (VCCO_0..3 all on +3V3, verified pin by pin). The ADC data/DVA/OVR (VDRV 3.3 V), SDRAM, FT232H VCCIO, flash and JTAG are all 3.3 V. ADC_CLK comes from U401 on +3V3_CLK; ADS5231 lists no digital-input abs max, and VIH 2.2 V is met. ADC analog inputs: the THS4551 on 0–3.3 V can't exceed the min[3.3 V, AVDD+0.3] limit, and R114/R115 46.4 Ω ≥ 25 Ω meet the overshoot rule. At a ±30 V input, ATT is ±1.5 V and the FDA outputs are 0.14–2.86 V.
- N7 — THS4551 input common mode: VOCM × 698/1968 ≈ 0.53 V ± 0.16 V, inside -0.1 … VS+ -1.1 V.
- N8 — Enable/reset/config: U601/U602/U701/U702 EN tied to their inputs (always on). THS4551 ~PD is high. ADS5231 STPD/OEA/SEL/SEN are pulled low (parallel mode, running, outputs enabled) and OEB is at GND. FPGA M[1:0] = 01 (Master SPI; R1009 up, R1008 down), HSWAPEN high, PROG_B/INIT_B 4.7k up, DONE 330 Ω up, SUSPEND at GND, CMPCS_B NC. FT232H RESET# 10k up. U702 PGOOD has a 100k pull-up to +4V0A (R705).
- N9 — No other analog path lacks a constraint: the AFE chain (BNC → U1x3 → ADC) is the only op-amp/FDA path, and it is fully constrained.

## Coder false-positive list — disposition
| # | Claim | Verdict |
|---|---|---|
| 1 | Intentional NC pins (U301.22, U103/U203 1/4, U701.4, U602.4, J501 A8/B8, U1001 72/56/66/67/74/75/78, U801.36/40, U901.32/33) | Accepted. Each was checked against its pin function (DVB unused, FB± are internal taps, SBU, A12/NC on 128 Mb, spare I/O). |
| 2 | U702 PGOOD tied to GND | Superseded: rev 2 adds the R705 pull-up and the error is gone. |
| 3 | U1001.73 SUSPEND to GND | Accepted: UG385 says tie it low when unused. Only the bidirectional-vs-PWR_FLAG warning remains. |
| 4 | 255 (now 258) lib_symbol_mismatch | Accepted: generated-library cache. |
| 5 | Netlist "unstable" only in symbol pin order | Accepted after verification (N1). |
| 6 | SPICE NOT CHECKED = model coverage | Rejected as stated. Models and GBW exist; the cause is pin-name role detection (W1). Now evaluated: PASS. |
