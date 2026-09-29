# TPS73633DBVR — 3.3V Fixed, 400mA Cap-Free LDO (KEYSTONE, sets analog rail, U5/U6)

Datasheet obtained: `datasheets/TPS73633DBVR_real.pdf` (TI's current **TPS736** family
datasheet, SBVS038X, Rev. May 2025 — this now-current document covers what used to be a
separate "TPS73633" datasheet; the older per-suffix document no longer exists standalone
at TI). Saved under a `_real` side-name because `fetch-datasheet.py`'s automated verifier
rejected it (the literal string "TPS73633" doesn't appear in the first 3 pages — it's
referred to generically as "TPS736xx"/"TPS736" family throughout). **Manually verified**
via WebFetch + direct page read: page 3's Table 4-1 "Pin Functions" and Figure 4-1 "DBV
Package, 5-Pin SOT-23" explicitly cover the exact SOT-23-5 package this MPN uses, with a
fixed-voltage application circuit — this is unambiguously the correct, current datasheet
for TPS73633DBVR.

| Spec | Value |
|------|-------|
| Package | SOT-23-5 (DBV) |
| Vcc / Vin range | 1.7–5.5 V |
| Key output spec | 3.3 V fixed output, 0.5% initial accuracy, 1% overall (line/load/temp) |
| Max current / power | 400 mA max, 75 mV typ dropout @ 400 mA |
| Operating temp | −40°C to +125°C (Tj) |

## Pinout (SOT-23-5 / DBV package, datasheet Table 4-1)
| Pin | Name | Function |
|-----|------|----------|
| 1 | IN | Input supply |
| 2 | GND | Ground |
| 3 | EN | Enable — **active high**: "Driving the enable pin (EN) high turns on the regulator. Driving this pin low puts the regulator into shutdown mode... EN can be connected to IN if not used." |
| 4 | NR | Noise reduction (fixed-voltage versions only) — optional external cap to this pin bypasses internal bandgap noise; **not FB** on this fixed-3.3V part (the FB function at this same physical pin number only applies to the adjustable-voltage variant, which this MPN is not) |
| 5 | OUT | Regulated output |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| EN polarity | Active-high; tie to IN directly if always-on is desired | datasheet p.3, Table 4-1 EN row — **verified**, read directly from the downloaded PDF |
| Pin 4 function on this exact part | NR (noise reduction), not FB — this is the **fixed 3.3V** version (TPS73633), confirmed by the part's own name and JLC's "Output Voltage: 3.3V / Output Type: Fixed" spec | datasheet p.3 Table 4-1 + JLC parametric spec — **verified** |
| Output accuracy | 0.5% initial accuracy, 1% overall (line, load, temp) | datasheet p.1 Features — **verified** |
| No output capacitor required for stability | "Stable with no output capacitor or any value or type of capacitor" | datasheet p.1 Features — **verified**, though `sourced_bom.md` still places bulk/decoupling caps per standard practice — that's fine, just not load-bearing for stability |

## Notes
- If EN is left unconnected on the schematic (not tied to IN or a control signal), the
  regulator will NOT turn on by default — EN is not internally pulled high. Confirm
  `sourced_bom.md`/`net_plan.md` ties EN to IN (always-on) or to a sequencing signal, per
  decision #1's mention of a "2.74 ms delay" sequencing resistor (R18/C22) elsewhere in the
  power block — if that sequencing signal is meant to gate these LDOs' EN pins, the coder
  must wire it explicitly.
- U5/U6 = two instances (per-channel analog rails, CH1/CH2) — same part, same pinout.
