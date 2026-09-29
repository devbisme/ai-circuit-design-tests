# CAT24C128WI-GT3 — onsemi 128kb I2C CMOS Serial EEPROM, SOIC-8 (U14, usb_controller block)

Source: `datasheets/CAT24C128WI-GT3_real.pdf` (onsemi CAT24C128/D, Rev. 15, Aug 2013, full
16-page datasheet). Note: two other files on disk,
`datasheets/CAT24C128WI-GT3.pdf`/`CAT24C128WI-GT3_v2.pdf`, are both the **LCSC product page
saved as HTML with a `.pdf` extension** (identical content, confirmed via `file`) —
**not usable as a PDF, do not open them as one**; the real PDF was recovered this phase from
a link embedded in that HTML page. `_real.pdf` is the only valid PDF for this part.

| Spec | Value |
|------|-------|
| Package | SOIC-8 (W suffix, CASE 751BD) — matches sourced footprint `Package_SO:SOIC-8_3.9x4.9mm_P1.27mm` |
| Vcc / Vin range | 1.8V–5.5V |
| Key output spec | 128kb (16,384 × 8-bit) I2C serial EEPROM, 64-byte page write buffer, Standard(100kHz)/Fast(400kHz)/Fast-Plus(1MHz) I2C |
| Max current / power | ICCR (read) 1mA typ @ 400kHz; ICCW (write) 3mA typ @ 400kHz |
| Operating temp | Industrial / extended range (part-number-suffix dependent; `WI` suffix = industrial grade per onsemi's own naming, consistent with this design's other industrial-grade parts) |

## Pinout (SOIC-8, exactly as datasheet Fig. "Pin Configuration")

| Pin | Name | Function |
|-----|------|----------|
| 1 | A0 | Device Address Input |
| 2 | A1 | Device Address Input |
| 3 | A2 | Device Address Input |
| 4 | VSS | Ground |
| 5 | SDA | Serial Data Input/Output |
| 6 | SCL | Serial Clock Input |
| 7 | WP | Write Protect Input (active High — pulled down internally to GND if not driven) |
| 8 | VCC | Power Supply |

## Notes

- **A0/A1/A2 (pins 1–3) set the I2C 7-bit device address** — tie each directly to VCC or GND
  per the desired address (standard 24Cxx addressing, 3 bits → 8 possible addresses on one
  bus). If this is the only EEPROM on the FX2LP's I2C bus (the `usb_controller` block's
  boot-config EEPROM, standard Cypress FX2LP pattern), the simplest choice is **tie all
  three to GND (address 0x50)** — confirm no other I2C device on the same bus needs that
  address before finalizing.
- **WP (pin 7) is active-High and internally pulled down to GND if left floating** — so
  floating WP = write-enabled (memory writable) by default, which is fine for a boot-EEPROM
  that gets programmed once and is otherwise read-only in normal operation, but a stray
  glitch could corrupt firmware. Tie WP directly to VCC for permanent write-protection after
  programming, or to GND for always-writable — do not leave genuinely floating on a
  production board even though the internal pull-down makes it electrically safe.
- Standard I2C decoupling: 100nF close to VCC (pin 8)/VSS (pin 4), per universal EEPROM
  practice.
- This part is the FX2LP's serial EEPROM for USB descriptor/firmware boot per the
  `usb_controller` block — SDA/SCL wire directly to the CY7C68013A's I2C pins (see
  `datasheets/CY7C68013A-56LTXC_SUMMARY.md` for the FX2LP's SDA/SCL pin names) with the
  standard 2.2–4.7kΩ pull-ups to VCC on both lines (external to this chip — check
  `sourced_bom.md` for a generic pull-up resistor pair on this net if not already present).
