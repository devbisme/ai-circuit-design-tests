# 24LC64-I/SN — 64Kbit I2C EEPROM (FX2 boot config, U51)

Datasheet obtained: `datasheets/24LC64-I-SN.pdf` (Microchip DS21189T, verified).

| Spec | Value |
|------|-------|
| Package | SOIC-8 |
| Vcc / Vin range | 2.5–5.5 V |
| Key output spec | 64 Kbit = 8K×8, 2-byte (16-bit) memory addressing |
| Max current / power | 400 kHz I2C, 3 mA active / 1 µA standby |
| Operating temp | −40°C to +85°C |

## Pinout (SOIC-8, standard 24xx64 pinout)
| Pin | Name | Function |
|-----|------|----------|
| 1 | A0 | Address select bit 0 |
| 2 | A1 | Address select bit 1 |
| 3 | A2 | Address select bit 2 |
| 4 | VSS | Ground |
| 5 | SDA | I2C data |
| 6 | SCL | I2C clock |
| 7 | WP | Write protect (active high = protected; tie low to allow writes) |
| 8 | VCC | Supply |

**Verified** directly from the downloaded PDF's pin diagram text: `A0 1 / 8 VCC`,
`A1 2 / 7 WP`, `A2 3 / 6 SCL`, `VSS 4 / 5 SDA` (8-pin SOIC package) — matches the table
above exactly.

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Addressing width | 2-byte (16-bit) internal addressing (8K×8 organization needs 13 address bits, spans 2 bytes) | datasheet, memory organization section — **verified** |
| Control byte format | `1010 A2 A1 A0 R/W` — A2/A1/A0 are the Chip Select bits, compared against the logic levels driven on the A2/A1/A0 pins; must be hard-strapped to VCC or VSS | **VERIFIED** — `datasheets/24LC64-I-SN.pdf`, DS21189T, p.7, §5.0 "Device Addressing", Figure 5-1 |
| FX2LP boot compatibility | The CY7C68013A boot-loader needs a "large EEPROM" (2-byte address) at I2C 7-bit address **0x51 (0xA2 8-bit write)** — see `CY7C68013A-56LTXC_SUMMARY.md` for the full finding | **VERIFIED against a CY7C68013A primary-source document** — confirmed in the CY7C68013A datasheet's own Table 8 "Strap Boot EEPROM Address Lines to These Values" (p.16 of 74), which names "24LC64" explicitly as the 8K-byte example part |
| Required address strap | **A2=0 (GND), A1=0 (GND), A0=1 (VCC)** → control byte `1010 0010` = 0xA2 write / 0x51 7-bit address | **VERIFIED** — cross-confirmed from two primary documents: CY7C68013A datasheet Table 8 (states A2,A1,A0 = 0,0,1 for the 8K/24LC64 boot-EEPROM class) and this part's own control-byte format above (Figure 5-1) |

## Notes
- **This is the exact failure class flagged in the task brief** ("an EEPROM the USB bridge
  explicitly cannot use") — the 24LC64 itself is electrically fine and widely used for FX2
  boot, and its required strap is now **confirmed from two primary-source datasheets** (not
  just community sources, as an earlier revision of this handoff reported): the CY7C68013A
  datasheet's own Table 8, and this part's own control-byte format (Figure 5-1). Both agree.
  If R52-R55 (currently 10 kΩ placeholders, `sourced_bom.md`) are wired as simple pull-downs
  to GND on all three address pins (a common naive default), the part would sit at 0x50 and
  FX2LP would NOT find it as configured for 2-byte-address boot — a hard boot failure.
  **The coder must strap A0=1 (pull to VCC), A1=0, A2=0 (pull to GND)** — this is now a
  verified requirement, not an assumption.
- WP (pin 7) should be tied low (GND) to allow the FX2 to write its config on first
  programming; some designs tie it through a jumper for later write-protection — check
  `net_plan.md`/design intent.
