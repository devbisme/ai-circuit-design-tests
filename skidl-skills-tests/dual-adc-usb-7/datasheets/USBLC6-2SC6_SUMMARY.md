# USBLC6-2SC6 — Low-capacitance USB ESD protection (usb_bridge, U8)

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Vcc / Vin range | Reverse standoff 5V, breakdown 6V |
| Key output spec | Junction capacitance **0.35pF (I/O) / 0.8pF (VBUS)**, clamping voltage 15V |
| Max current / power | Peak pulse current 6A@8/20µs, 150W peak pulse power |
| Operating temp | Not in MCP record; ST original rated −40°C to +85°C typical for this family |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Junction/line capacitance on D+/D− | **0.35pF** (I/O lines), 0.8pF (VBUS line) | `jlc_get_part` electrical specs for this exact LCSC# (C2687116) — this is the value used for USB D+/D− loading, well below any signal-integrity concern at 480Mbps | UNVERIFIED beyond MCP — see below |

## Unverified
Manufacturer listed is "UMW (Youtai Semiconductor)", a clone/functional-equivalent of the
original STMicroelectronics USBLC6-2. **The datasheet PDF could not be obtained** (2 attempts,
ordinary-part budget): `lcsc.com` direct link → HTML page; `st.com/resource/en/datasheet/usblc6-2.pdf`
→ connection timeout. The 0.35pF/0.8pF figure above comes from JLC's own parametric database
for this exact LCSC#, not a datasheet I read — flagging per the phase's own cautionary example
(a similarly-sourced TVS capacitance figure was wrong by 30x in a prior run). This device sits
on USB D+/D− (480Mbps signal lines), not the analog front end, so a capacitance error here is
lower-consequence than on the ADC signal path, but **the coder/reviewer should re-verify this
figure from ST's `usblc6-2.pdf` (or UMW's own datasheet if published) before treating 0.35pF as
load-bearing for USB signal integrity margin.**

## Notes
- Existing symbol used: `Power_Protection:USBLC6-2SC6` — not regenerated.
- Datasheet: not obtained this phase.
