# TPS22919DCKR — Single-Channel Load Switch (U2)

**UPDATE (verification pass, 2026-09-21) — PDF obtained, ON polarity and QOD behavior
VERIFIED against TI primary source.** `datasheets/TPS22919DCKR.pdf` — Texas Instruments
**SLVSEN5B, October 2018, Revised May 2019 (Rev. B)**, fetched from
`https://www.ti.com/lit/ds/symlink/tps22919.pdf`.

| Spec | Value |
|------|-------|
| Package | SC-70-6 (TI calls it DCK, 6-Pin SC-70) |
| Vcc / Vin range | 1.6–5.5 V |
| Key output spec | RDS(on) = 89 mΩ typ @5V; **Control Input Logic: Active High — verified** |
| Max current / power | 1.5 A continuous |
| Operating temp | −40°C to +125°C (junction) |

## Pinout (VERIFIED — TI datasheet §5 "Pin Configuration and Functions", p.3)
| Pin | Name | I/O | Function |
|-----|------|-----|----------|
| 1 | IN | I | Switch input |
| 2 | GND | — | Device ground |
| 3 | ON | I | **Active high switch control input. Do not leave floating.** |
| 4 | NC | — | No connect pin, leave floating |
| 5 | QOD | O | Quick Output Discharge pin — see Notes |
| 6 | VOUT | O | Switch output |

Numbers and names match `jlc_get_pinout`/the symbol exactly — no mismatch.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| ON pin polarity | **Active high.** Datasheet text: "Active high switch control input. Do not leave floating." A Smart Pull-Down (RPD ≈ 530 kΩ typ) holds ON low (switch off) until deliberately driven high, then disconnects to save power. | TI SLVSEN5B (Rev. B), §5 Pin Functions table + §1 Features "Smart ON pin pull down", p.1 & p.3 — **verified** |
| QOD left unconnected (floating) | Legitimate and explicitly documented as one of three valid configurations: "Disabling QOD by leaving pin floating." (The other two: external resistor VOUT→QOD, or tie QOD directly to VOUT for the internal 24 Ω discharge path.) Leaving QOD floating means the internal discharge FET is **disabled** — VOUT will NOT be actively discharged when the switch turns off; it decays only through the load's own leakage. | TI SLVSEN5B (Rev. B), §5 Pin Functions table (QOD row) + §1 Features "Internal QOD resistance = 24 Ω", p.1 & p.3 — **verified** |

## Notes
- ON polarity and QOD-floating legitimacy are both confirmed from the TI datasheet — the
  design's use of these two pins (per `usb_front` block in `sourced_bom.md`) needs no
  change.
- Confirmed in code: `circuits/dual_adc_usb/usb_front.py` line 140 does
  `U2['QOD'] += NC` — QOD is left floating, exactly TI's "disable QOD" configuration. This
  is legitimate per the datasheet; the only consequence is VOUT (VBUS_SW) will not be
  actively discharged when U2 turns off (decays through the load's own leakage instead of
  the internal 24 Ω FET). No code change needed unless a fast power-cycle/reset requirement
  surfaces later.
- Drives +3V3A or similar switched rail per `usb_front` block in `sourced_bom.md`.
