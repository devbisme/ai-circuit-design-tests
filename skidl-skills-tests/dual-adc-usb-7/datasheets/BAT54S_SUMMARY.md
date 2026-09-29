# BAT54S — Dual series Schottky diode (afe_driver, D111/112/211/212)

| Spec | Value |
|------|-------|
| Package | SOT-23 |
| Vcc / Vin range | VR 30V |
| Key output spec | Vf=400mV@10mA, reverse leakage 2µA@30V |
| Max current / power | 200mA rectified, 600mA surge |
| Operating temp | Not in MCP record for this listing |

## Notes
- ADC input clamp pair (per sourced_bom), D111/D112/D211/D212 — **corrected at phase 6**.

  **The previous wording here claimed the part "holds ADS5231 input pins inside AVDD+0.3V
  during overload recovery." That is arithmetically impossible and has been removed.** The
  ADS5231's input absolute maximum is AVDD + 0.3 V; this part's Vf is 400 mV at 10 mA
  (~320 mV at 1 mA). A Schottky clamp returning to the supply rail can never hold a node
  closer than Vf above that rail, so it cannot meet a +0.3 V limit at any useful current.
  No part in this class can. Do not re-enter that claim.

  **What the clamp actually does, and why it is still the right part (erc_report.md, R-10
  disposition):**
  1. *It tracks AVDD rather than fighting it.* The clamp cathodes and the ADC's AVDD pins
     are the **same net** — `P3V3A` carries `U4.3/46/57` and `D111.2/D112.2/D211.2/D212.2`.
     The excursion is therefore always exactly Vf above AVDD, never a fixed 3.7 V against
     a fixed 3.6 V. The two move together over tolerance, load and temperature.
  2. *It keeps the ADC's internal ESD diode off, which is what the +0.3 V limit exists
     for.* The internal structure is a silicon junction needing ~0.7 V to conduct; this
     Schottky conducts at ~0.4 V and takes the fault current first. The internal diode
     never turns on, so essentially no current enters the ADC pin. That is the protection
     function, and it is met.
  3. *Nothing in this circuit can forward-bias it anyway.* The only device driving these
     nodes is the THS4521 FDA, and it is powered from `P3V3A` too (`U2.3`, `U2.7`, `U3.3`,
     `U3.7`). Its output cannot exceed its own rail, so in every amplifier-driven condition
     the ADC input stays at or below AVDD and these diodes never conduct. They matter only
     for ESD or hot-plug energy coupling through the LC anti-alias filter.

  Net effect: `design_risks.md` R-10 should read "clamp tracks AVDD; no in-circuit source
  can forward-bias it," **not** "negative margin against an absolute maximum."
- Symbol is an exact match (`Diode:BAT54S`) — not regenerated.
- Datasheet: `datasheets/BAT54S.pdf` (hongjiacheng).
