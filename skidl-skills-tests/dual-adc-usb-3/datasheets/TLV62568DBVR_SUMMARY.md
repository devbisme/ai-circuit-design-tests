# TLV62568DBVR — 1A Synchronous Step-Down Buck Converter, SOT-23-5 (used for +1V2 rail)

Source: `datasheets/TLV62568DBVR.txt` (TI datasheet, full document, already extracted).
Same family as TLV62569, identical pinout, same FB-divider equation, slightly different
current rating (1A vs 2A) and tSS spec.

| Spec | Value |
|------|-------|
| Package | SOT-23-5 (DBV) — this BOM's grade |
| Vcc / Vin range | 2.5V–5.5V input — powered from `+3V3` per architecture ("buck off +3V3", block_diagram.md), not directly from VBUS |
| Key output spec | Adjustable 0.6V to VIN via external FB divider; this design sets **+1.2V** (FPGA core, GW1NR-9 VCC) |
| Max current / power | 1A rated switch current; 1.5 MHz switching |
| Operating temp | –40°C to 125°C |

## Pinout (SOT23-5, Top View — identical to TLV62569)

| Pin | Name | Function |
|-----|------|----------|
| 1 | EN | Enable, active high. **Do not leave floating.** Gated by `PWR_EN`. |
| 2 | GND | Ground |
| 3 | SW | Switch node — connect to inductor (L1 or L2, per net plan) |
| 4 | VIN | Power supply input — from `+3V3`, not VBUS |
| 5 | FB | Feedback — external resistor divider |

## Notes — closes remaining 2 of 8 feedback-divider values (`03_sourcing.md` gap item #4,
now fully closed across all 8: 2 here + 2 TLV62569 + 2×2 LM27762 = 8)

`VOUT = 0.6V × (1 + R1/R2)`, same equation and R2 ≤ 200kΩ constraint as TLV62569.

Target +1.2V → R1/R2 = 1 exactly → **R1 = R2 = 100kΩ**, both `0402WGF1003TCE` (same part
already in the BOM elsewhere — reuse, no new MPN needed). VOUT = 0.6 × 2 = **1.200V exactly**
(0% error at nominal resistor values, before ±1% tolerance stack — best case of all 8
dividers computed this phase).

- **Soft-start (R6) resolved:** `tSS = 700µs` typical for the DBV package specifically
  (datasheet splits tSS by package: DBV=700µs, DRL/PDRL/PDDC=900µs). Falls inside the
  architecture's required 0.2–2ms monotonic-ramp window for +1V2 (Gowin VCC core ramp-rate
  limit) — **no soft-start conflict.**
- EN tied to `PWR_EN`.
- Powered from `+3V3` (the TLV62569 output), not directly from VBUS — confirm this cascade
  order in the SKiDL netlist (`power_digital` block wiring: U1 always-on LDO → U2 buck
  +3V3 → U3 buck +1V2 → U4 LDO +1V8, per `block_diagram.md`).
