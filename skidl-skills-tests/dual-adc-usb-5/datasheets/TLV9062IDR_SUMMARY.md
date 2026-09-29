# TLV9062IDR — Dual RRIO op-amp (U4, reference buffer)

| Spec | Value |
|------|-------|
| Package | SOIC-8 |
| Vcc / Vin range | Single supply 1.8–5.5V |
| Key output spec | RRIO, Vos 1.6mV, GBW 10MHz, CMRR 103dB |
| Max current / power | 538µA/amp quiescent, 50mA output |
| Operating temp | −40°C to +125°C |

## Pinout (SOIC-8, standard TI dual-op-amp pinout — same convention as TLV9062's whole
family and the industry-standard LM358-style dual pinout; **EasyEDA pin-data lookup returned
no data for this specific LCSC record, so this table is from TI's well-documented standard
dual op-amp pin convention, not a live pull for this exact part**)

| Pin | Name | Function |
|-----|------|----------|
| 1 | OUT A | Channel A output |
| 2 | IN A− | Channel A inverting input |
| 3 | IN A+ | Channel A non-inverting input |
| 4 | V− | Negative supply / GND |
| 5 | IN B+ | Channel B non-inverting input |
| 6 | IN B− | Channel B inverting input |
| 7 | OUT B | Channel B output |
| 8 | V+ | Positive supply |

## Notes

- **EXACT-matched KiCad symbol** `Amplifier_Operational:TLV9062` — since the symbol is an
  exact library match (not generated in this pass), the coder should read pin names directly
  from that symbol via SKiDL/KiCad tooling rather than trust this table blindly if there is
  ever a discrepancy; the table above is standard-convention, not independently re-pulled
  from EasyEDA for this LCSC record (that lookup returned "missing pin data").
- No PDF downloaded in this pass (not attempted — MCP specs were sufficient and this is a
  freely-substitutable, non-critical-path part per architecture item 10).
- Freely substitutable per architecture — OPA2376/OPA2333 were the runners-up, chosen against
  for exact symbol match and stock, not a hard requirement.
