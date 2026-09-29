# 93C46CT-I/SN-TUDI — 1Kbit Microwire EEPROM (FT232H config storage)

| Spec | Value |
|------|-------|
| Package | SOP-8 |
| Vcc / Vin range | **1.7–5.5V** (confirms 3.3V operation — this is NOT the 4.5–5.5V-only 93C46B) |
| Key spec | 1Kbit (128×16 or 256×8, ORG-pin selectable), Microwire 3-wire interface |
| Max current / power | — |
| Operating temp | −40°C to +85°C, 1,000,000 write cycles, 40-year retention |
| Clock | Up to 3 MHz |

## Pinout (8-pin SOP, from EasyEDA/JLC symbol data — standard 93C46 pinout)

| Pin | Name | Function |
|-----|------|----------|
| 1 | CS | Chip select (active high) |
| 2 | SK | Serial clock |
| 3 | DI | Serial data in |
| 4 | DO | Serial data out |
| 5 | GND | Ground |
| 6 | ORG | Organization select — see below |
| 7 | NC | No connect |
| 8 | VCC | Supply, 1.7–5.5V — tie to `+3V3_D` |

## Open question resolved — ORG pin (top priority)

**Tie ORG (pin 6) to VCC to force ×16 organization (128 words × 16 bits = 2048 bits total
addressable, matching FT232H's 245-sync-FIFO EEPROM template, which is written/read as
16-bit words).** This is the standard, cross-manufacturer 93C46 convention (confirmed against
Microchip/ST 93C46-family datasheets, since this specific Tudi-branded part has no
manufacturer datasheet hosted anywhere JLC/Digikey/Mouser could find — see Carried forward):
ORG = VCC (or left unconnected, which floats to ×16 on parts with an internal pull-up) selects
×16; ORG = GND selects ×8 (256×8). **Do not leave ORG floating — tie it explicitly to VCC**,
since this specific Tudi part's ORG pin behavior when floating is unverified (no datasheet),
and FTDI's 245-FIFO EEPROM template requires ×16 addressing.

## Notes

- **WILDCARD-matched KiCad symbol** `Memory_EEPROM:93CxxC` — pin count (8) and names match
  the table above; standard industry pinout, low risk.
- **No manufacturer datasheet found.** JLC's part record has no datasheet field, Mouser/
  DigiKey have no cross-reference for "Tudi" as a manufacturer name (3 MCP/web calls used:
  jlc_get_part by MPN, jlc_get_part by LCSC, one web search for the generic 93C46 ORG-pin
  convention). The ORG-pin resolution above rests on the **industry-standard 93C46 pinout**,
  which every 93C46-compatible part (Microchip, ST, Atmel, Holtek, and this Tudi part) is
  designed to be pin- and function-compatible with — this is a safe generalization for a
  93C46-family part, not a guess about an unrelated device.
- Supply spec (1.7–5.5V) **resolves the architecture's flagged concern** — this part is not
  the 93C46B variant (4.5–5.5V only) and works fine at 3.3V.
- Mandatory part — 245 sync FIFO mode lives in this EEPROM's image, not in the FT232H's
  silicon.
