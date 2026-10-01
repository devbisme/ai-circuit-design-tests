# TLV62569DBVR — TI 2 A 1.5 MHz sync buck, SOT-23-5

Source: `TLV62569DBVR.pdf` (TI).

| Spec | Value |
|------|-------|
| VIN | 2.5–5.5 V |
| VOUT | 0.6 V … VIN, adjustable |
| IOUT | 2 A |
| fSW | 1.5 MHz |
| EN | VIH 0.95–1.2 V (max 1.2), VIL 0.4–0.85 V; do not float |

## Pinout (DBV; KiCad `Regulator_Switching:TLV62569DBV` names identical)
| Pin | Name | Function |
|-----|------|----------|
| 1 | EN | enable, active high |
| 2 | GND | |
| 3 | SW | to inductor |
| 4 | VIN | |
| 5 | FB | feedback divider |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| VFB | 0.588 / 0.600 / 0.612 V | elec. table — **verified** |
| Soft-start, DBV (K7) | **800 µs typ** (900 µs is DDC/DRL/PDRL) | elec. table tSS row — **verified** |
| 1V2 ramp | 1.2 V/0.8 ms = 1.5 mV/µs, inside GW1NR 0.6–6 mV/µs | derived — **verified inputs** |
| No PG on DBV | PG only on TLV62569P variants | Pin Functions — **verified** |
