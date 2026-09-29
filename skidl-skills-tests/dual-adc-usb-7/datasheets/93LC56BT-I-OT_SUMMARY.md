# 93LC56BT-I/OT — 2Kbit Microwire EEPROM (usb_bridge, U7)

| Spec | Value |
|------|-------|
| Package | SOT-23-6 |
| Vcc / Vin range | 2.5–5.5V |
| Key output spec | 2Kbit (128 x 16-bit organization — the "B" suffix), 3-wire Microwire/SPI-like interface |
| Max current / power | 2mA operating, 1µA standby |
| Operating temp | −40°C to +85°C (I grade) |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | DO | Serial data output |
| 2 | VSS | Ground |
| 3 | DI | Serial data input |
| 4 | CLK | Serial clock |
| 5 | CS | Chip select |
| 6 | VCC | Supply |

Note: the 8-pin/SOT-23-6 'B'-suffix parts have **no ORG pin** (organization fixed by part
number, not pin strap) — ORG only exists on the 'C'-suffix variant in 8-pin packages.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Memory organization | **128 x 16-bit** (fixed by the "56B" part suffix, no ORG pin needed) | `93LC56BT-I-OT.pdf` p.1, device selection table ("93LC56B: 2.5V-5.5V, no ORG pin, 16-bit") — **verified**. This confirms sourcing's compatibility note: 93LC46/66 are pin-compatible but organization-incompatible; **93LC56B is the correct 16-bit-organization part the FT232H's EEPROM interface requires.** |

## Notes
- `[CRIT]` do not substitute (sourcing decision) — organization-incompatible alternatives (93LC46/66) would silently corrupt the FT232H's EEPROM-programmed configuration (including the ACBUS9=PWREN# strap referenced in `FT232HL-REEL_SUMMARY.md`).
- Symbol is an existing wildcard match (`Memory_EEPROM:93LCxxB`) — sourcing flagged "confirm pin 1 orientation before layout." Pin 1 = DO per the pinout table above (verified from datasheet), matches the SOT-23-6 pin-1 dot convention in most EasyEDA/KiCad libraries, but **the coder should still visually confirm pin-1 marking on the physical symbol against this table before layout**, since this was not independently re-derived from the existing wildcard symbol's own pin-1 assignment.
- Datasheet: `datasheets/93LC56BT-I-OT.pdf` (Microchip 93AA56X/93LC56X/93C56X family datasheet).
