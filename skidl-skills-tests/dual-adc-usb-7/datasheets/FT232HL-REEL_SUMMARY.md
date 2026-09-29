# FT232HL-REEL — USB 2.0 Hi-Speed to FIFO bridge (usb_bridge, U6)

| Spec | Value |
|------|-------|
| Package | LQFP-48 (7x7mm) |
| Vcc / Vin range | VREGIN 3.3–5.25V (drives internal LDO); VCCIO 1.62–1.98V or 2.97–3.63V (used at 3.3V) |
| Key output spec | USB 2.0 Hi-Speed 480Mbps, synchronous FIFO up to 40MB/s (used at 60MHz FIFO clock per net_plan) |
| Max current / power | 70mA supply current, 10µA quiescent |
| Operating temp | −40°C to +85°C |

## Pinout (cross-verified: JLC/EasyEDA for this exact LCSC#, C51997, **and** the primary FTDI datasheet)
| Pin | Name | Pin | Name | Pin | Name |
|-----|------|-----|------|-----|------|
| 1 | XCSI | 17 | ADBUS4 | 33 | ACBUS9 |
| 2 | XCSO | 18 | ADBUS5 | 34 | RESET# |
| 3 | VPHY | 19 | ADBUS6 | 37 | VCCA |
| 5 | REF | 20 | ADBUS7 | 38 | VCORE |
| 6 | DM | 21 | ACBUS0 | 39 | VCCD |
| 7 | DP | 25 | ACBUS1 | 40 | VREGIN |
| 8 | VPLL | 26 | ACBUS2 | 42 | TEST |
| 12,24,46 | VCCIO | 27 | ACBUS3 | 43 | EEDATA |
| 13–20 | ADBUS0-7 | 28 | ACBUS4 | 44 | EECLK |
| 21,25–32 | ACBUS0-8 | 29 | ACBUS5 | 45 | EECS |
| | | 30 | ACBUS6 | | |
| | | 31 | ACBUS7 | | |
| | | 32 | ACBUS8 | | |

(GND/AGND on pins 4,9,10,11,22,23,35,36,41,47,48 — full list in `symbols/`.)

## Load-bearing facts

| Fact | Value | Source |
|------|-------|--------|
| ACBUS9 (pin 33) is a valid PWREN# assignment | **Confirmed.** Table 3.5 "ACBUS Configuration Control" lists `PWREN#` as available on ACBUS0/1/2/3/4/5/6/8/**9**. Requires the external EEPROM to be fitted (U7, 93LC56B) — without it, ACBUS9 defaults to `TriSt-PU` (tri-state, internal pull-up). Behavior: "Output is low after the device has been configured by USB, then high during USB suspend mode. This output can be used to control power to external logic P-Channel logic level MOSFET switch." | `datasheets/FT232H-farnell.pdf` p.~11 (Table 3.5, ACBUS Configuration Control), and pin table entry "33 ACBUS9 I/O EEPROM. If the external EEPROM is not fitted the default configuration is TriSt-PU." — **verified**, matches `net_plan.md` line 91's "EEPROM-configured PWREN#" exactly. Also independently confirms the U7=93LC56B choice: the same datasheet states "The EEPROM should be a 16 bit wide configuration such as a 93LC56B or equivalent... the 93LC46B is not compatible with the FT232H device." |
| **R65 = the datasheet-mandated PWREN# pull-up, NOT a RESET# pull-up** | Table 3.5's footnote on the `PWREN#` row: **"\* Must be used with a 10kΩ resistor pull up."** R65 is sourced as exactly 10kΩ (0402WGF1002TCE) and sits in the `usb_bridge` block alongside R61–R64 (the other FT232H-mandated resistors). This is a direct, better-supported match than the RESET# guess in the previous revision of this summary. | Same page, Table 3.5 footnote — **verified**. Net: R65 goes on `PWREN_N` (U6.ACBUS9 → R65 → pull-up rail, and the same node drives Q1's gate per `net_plan.md` line 91). Pull-up rail is most likely `FT_3V3` (the only always-on 3.3V rail at U6) — confirm against the app-circuit figure before layout if one exists in the full datasheet; not independently re-derived this pass. |
| RESET# (pin 34) needs no resistor, just a direct tie | "RESET# should be tied to VCCIO (+3.3V) if not being used." No pull-up value specified — a direct wire is sufficient. | `datasheets/FT232H-farnell.pdf`, §"RESET Generator" — **verified**. `net_plan.md` still never mentions this pin; it should be tied directly to `FT_3V3`, not through R65 (that resistor's job is PWREN#, above). This remains a real net_plan gap (a floating pin the architect missed) — the fix is just a direct wire, not a component. |

## Notes
- **Datasheet PDF obtained** this pass via a Farnell-hosted mirror (`farnell.com/datasheets/1913746.pdf`) after `ftdichip.com` (multiple URL variants) kept returning HTTP 403 and `lcsc.com`/`mouser.com` returned HTML/anti-bot pages. Saved as `datasheets/FT232H-farnell.pdf` (also `datasheets/FT232H-glynstore.pdf`, a second working mirror, kept as a backup copy). 65 pages, text-extractable, confirmed the right part (FT232H family datasheet, matches FT232HL-REEL's LQFP-48 single-channel Hi-Speed USB-to-FIFO description).
- `[CRIT]` symbol is a prefix match (`Interface_USB:FT232H`, generic, correct LQFP-48 pinout per sourcing) — **not regenerated**, sourcing's "do not redo" applies.
