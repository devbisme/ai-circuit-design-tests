# SY8089AAC — 2A Synchronous Step-Down Regulator, Adjustable (KEYSTONE, sets +3V3D/+1V2 rails, U3/U4)

**No datasheet PDF obtained.** Silergy's own product page (silergy.com, fetched directly)
states this part is marked **"不推薦用於新設計" (Not Recommended for New Design / NRND)**
at the manufacturer — a fact worth flagging to the driver even without a PDF in hand.
7 URL attempts were made across the keystone budget (JLC's datasheet field is null for
this exact MPN; `lcsc.com/datasheet/C78988.pdf` and `C479074.pdf` both returned HTML/anti-bot
pages; Silergy's own site for `SY8089AAAC` lists only an Application Note and unrelated
family docs, no datasheet PDF link surfaced). Given NRND status, a datasheet may simply no
longer be distributed by Silergy for this exact suffix.

| Spec | Value (source: JLC parametric DB only — see caveat) |
|------|------|
| Package | SOT-23-5 |
| Vcc / Vin range | 2.7–5.5 V |
| Key output spec | Output Type: **Adjustable** (not fixed) — confirms a feedback resistor divider sets the output, consistent with `sourced_bom.md`'s R10-R18 divider network for +3V3D/+1V2 |
| Max current / power | 2 A output, 1 MHz switching, synchronous rectifier (built-in high+low side FETs), Iq = 55 µA |
| Operating temp | −40°C to +85°C |

## Pinout — **EasyEDA-sourced (`jlc_get_pinout`), NOT verified against a primary datasheet**
| Pin | Name | Function (inferred from name + standard adjustable-buck SOT23-5 convention) |
|-----|------|----------|
| 1 | EN | Enable (assumed active high, typical for this pin position — **not confirmed**) |
| 2 | GND | Ground |
| 3 | LX | Switch node (inductor connection) |
| 4 | IN | Supply input |
| 5 | FB | Feedback (sets Vout via external resistor divider) |

## Unverified keystone facts (this part contributes rows to the handoff's section of the same name)
| Fact | Best available answer | What would close it |
|---|---|---|
| Feedback reference voltage (VFB) | **Not found.** Cannot compute the R10-R18 divider ratio's target voltage independently of trusting `sourced_bom.md`'s existing 45.3kΩ/10.0kΩ (+3V3D) values as already-correct | A genuine Silergy SY8089A(AC) datasheet — not located this pass; the part may be NRND with no longer-published datasheet |
| EN pin polarity (active-high vs active-low) | Assumed active-high (family convention for this pin position on similar Silergy/generic adjustable bucks) | Same as above |
| Exact pinout (EN/GND/LX/IN/FB order) | EasyEDA tool data only, not cross-checked against a manufacturer pin diagram | Same as above |

## Notes
- **This is a genuine keystone gap** — the part that sets both the +3V3D and +1V2 rails
  has no verified feedback reference or enable polarity. `sourced_bom.md`'s R10 (45.3 kΩ)
  / R11 (10.0 kΩ) values for the +3V3D feedback divider, and R12/R13 (10.0 kΩ) for +1V2,
  were carried from `architecture/ic_selection.md`'s `[calc]` values — **those calculations
  assumed a VFB figure that could not be re-verified from a primary source this pass**.
  Standard Silergy buck family VFB is commonly 0.6V, but that is a family convention only,
  not confirmed for this exact part — do not treat it as fact.
- Given the NRND status, consider flagging this part for re-sourcing in a future pass —
  an actively-produced adjustable buck with a real, obtainable datasheet would close this
  gap permanently rather than requiring repeated unverified-assumption flags.
- This finding is carried to the handoff's `## Unverified keystone facts` table, which
  forces `status: partial`.
