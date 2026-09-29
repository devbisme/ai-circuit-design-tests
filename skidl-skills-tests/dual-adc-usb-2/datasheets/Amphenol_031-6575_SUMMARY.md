# Amphenol RF 031-6575 — BNC jack, right-angle, PCB mount (J2/J3)

SOURCE: WebSearch of distributor listings (element14, DigiKey, Amphenol RF's own product
ID page). **Full mechanical drawing / dimensional PDF NOT retrieved this session** —
amphenolrf.com and digikey.com both returned HTTP 403 (bot-blocked) to automated fetch.
This summary is built from search-result title/spec-sheet fragments only, cross-checked
where possible against the sourced BOM's own footprint choice. Mark this part's
mechanical data **incomplete** — see Carried forward in the phase handoff.

| Spec | Value |
|------|-------|
| Series | Amphenol RF 031-65xx, right-angle BNC jack |
| Termination | Through-hole, right-angle PCB mount |
| Mount style | **"Bulkhead rear mount, isolated"** per one distributor listing title — this phrase suggests a panel-bulkhead-style shell even though it is also PCB-pin-terminated; **flag: confirm whether this part needs a panel cutout in addition to PCB pads**, since "bulkhead" and "PCB right-angle jack" are somewhat contradictory descriptions seen across different distributor listings for this MPN and were not resolved to a single authoritative mechanical drawing this session |
| Impedance | 50 Ω |
| Frequency | Up to ~1 GHz class (typical for BNC family; one listing cites ~1 GHz max) — comfortably covers this design's 5 MHz analog bandwidth |
| Contact material | Phosphor bronze, gold-plated (per one distributor listing) |
| KiCad footprint (sourced) | `Connector_Coaxial.pretty:BNC_Amphenol_031-6575_Horizontal` — confirmed present in the local library by the sourcing phase |
| KiCad symbol | `Connector:Conn_Coaxial` |

## Pinout (from KiCad symbol `Connector:Conn_Coaxial`)

| Pin | Name | Type | Function |
|-----|------|------|----------|
| 1 | In | passive | Center conductor (signal) |
| 2 | Ext | passive | Outer shell/shield (ground) |

## Notes

- J2/J3 in `afe_channel` (×2): center pin → R_top1/attenuator input node; shield → chassis/
  analog ground per the attenuator's ground-referenced topology.
- **`[CRIT][FIXED]` per sourcing, unresolved mechanically:** this part sits on the panel
  edge (BNC jacks are user-facing connectors). The architect's original MPN
  (`031-5431-10RFX`) had no matching footprint in the local library; sourcing substituted
  `031-6575` on footprint-file-existence grounds alone — **no mechanical drawing was
  verified for either part in the sourcing phase, and none was obtained in this datasheet
  phase either.** This is carried forward unresolved: **get the physical part in hand and
  confirm the KiCad footprint's pad/mounting-hole layout matches before committing to
  layout/panel cutout design.**
