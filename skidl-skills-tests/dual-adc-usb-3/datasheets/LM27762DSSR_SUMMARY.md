# LM27762DSSR — ±4.2V (adjustable ±1.5V–5V) Charge-Pump Inverter + Dual LDO, WSON-12

Source: `datasheets/LM27762DSSR.txt` (TI SNVSAF7C, full document, already extracted).

| Spec | Value |
|------|-------|
| Package | DSS (WSON), 12-pin, 3mm × 2mm, thermal pad |
| Vcc / Vin range | VIN 2.7–5.5V operating (abs max 5.8V VIN-to-GND) — matches architecture's VBUS-derived positive LDO input, consistent, no conflict |
| Key output spec | OUT+ adjustable +1.5V to +5V; OUT– adjustable –1.5V to –5V; this design targets **±4.2V** (architecture Decision 6) |
| Max current / power | Switching frequency 2 MHz typ (architecture relies on this being ≥2 MHz for P5 — confirmed, "ƒSW ... 2 MHz" at VIN=3.6V) |
| Operating temp | Not extracted from this excerpt |

## Pinout (DSS/WSON-12, Table 4-1)

| Pin | Name | Function |
|-----|------|----------|
| 1 | PGOOD | Power-Good flag, open-drain, Logic 0 = good. **Connect to ground if not used.** |
| 2 | FB+ | Feedback input for positive LDO — external resistor divider between OUT+ and GND. **DO NOT leave unconnected.** |
| 3 | VIN | Positive power supply input |
| 4 | GND | Ground |
| 5 | CP | Negative unregulated charge-pump output |
| 6 | OUT– | Regulated negative output voltage |
| 7 | FB– | Feedback input for negative LDO — external resistor divider between OUT– and GND. **DO NOT leave unconnected.** |
| 8 | EN– | Enable, charge pump + negative LDO, active high |
| 9 | C1– | Negative terminal, flying cap C1 |
| 10 | C1+ | Positive terminal, flying cap C1 |
| 11 | OUT+ | Regulated positive output voltage |
| 12 | EN+ | Enable, positive LDO, active high |
| Thermal Pad | — | Ground. **DO NOT leave unconnected.** |

## Notes — closes 2 of 8 feedback-divider values (`03_sourcing.md` gap item #4)

**Positive output (R1 top / R2 bottom, FB+ = pin 2):**
`VOUT = 1.2V × (R1 + R2) / R2`, **R2 must be ≥ 50kΩ**.
Target +4.2V → R1/R2 = 2.5. Using **R2 = 100kΩ, R1 = 249kΩ** (both E96, both members of the
already-sourced `0402WGFxxxxTCE` ±1% 0402 family — `0402WGF1003TCE` for 100kΩ is *already in
`sourced_bom.md`* for the PWR_EN pulldown, same part number reusable here; 249kΩ would be
`0402WGF2493TCE`, same family/vendor code pattern, **not independently stock-checked this
phase** — pcbparts MCP still unavailable, per every prior phase) gives
VOUT+ = 1.2 × 349/100 = **4.188V** (–0.29% vs. 4.2V target — acceptable).

**Negative output (R3 top / R4 bottom, FB– = pin 7):**
`VOUT = –1.22V × (R3 + R4) / R4`, **R4 must be ≥ 50kΩ**.
Target –4.2V → R3/R4 = 2.4426. Using **R4 = 100kΩ, R3 = 243kΩ** (`0402WGF2433TCE`, same
family) gives VOUT– = –1.22 × 343/100 = **–4.1846V** (–0.37% vs. –4.2V target — acceptable).

- **EN+ and EN– are separate pins** — both active-high, both must be driven (not left
  floating) per the datasheet's own power-sequencing section; architecture gates this whole
  block from `PWR_EN` (Decision 7) — tie both EN+ and EN– to the same `PWR_EN` net unless a
  specific power-up sequencing between the two rails is required (not called out by the
  architecture, so treat as simultaneous).
- **PGOOD**: tie to GND if the coder doesn't want to route it to the FPGA/host; architecture
  doesn't mention using it, so default to grounding per datasheet guidance.
- Flying-cap / reservoir-cap count and placement (C1+/C1–, CP, OUT+/OUT– bulk) — sourced BOM
  already budgets "1µF X7R 16V 0603" and "10µF X7R 16V 0805" for this block (typ. 4 caps per
  TI's application circuit) — confirmed consistent with pin functions above (C1 flying cap
  across pins 9/10, CP and OUT– bulk on pins 5/6, OUT+ bulk on pin 11).
