# CY7C68013A-56LTXC — EZ-USB FX2LP USB Microcontroller (KEYSTONE, USB bridge, U50)

Datasheet obtained: `datasheets/CY7C68013A-56LTXC.pdf` (Infineon's current full datasheet
for the CY7C68013A/14A/15A/16A family — verified). Symbol already exists locally
(`MCU_Cypress:CY7C68013A-56LTX`, PREFIX match per sourcing) — not regenerated.

| Spec | Value |
|------|-------|
| Package | QFN-56, 8x8mm, exposed pad — confirmed live via JLC (`sourcing` decision #8) |
| Vcc / Vin range | 3.0–3.6 V (VCC); separate VCC_D core rail internally regulated on-chip from VCC |
| Key output spec | 480 Mbps USB 2.0 High-Speed, 8051-core, 24 configurable I/O (GPIF/Slave FIFO/Ports A-E) |
| Max current / power | 48 MHz CPU clock; External oscillator (typ. 24 MHz crystal — matches Y1, DSX321G 24MHz in `sourced_bom.md`) |
| Operating temp | 0°C to +70°C (commercial grade — **not industrial**; flag if the end product needs wider temp range) |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Boot EEPROM addressing requirement | An I2C EEPROM used for FX2LP boot **must use 16-bit (two-byte) addressing** and, for an 8 Kbyte device (the 24LC64 class), sit with strap bits **A2=0, A1=0, A0=1** — giving 7-bit I2C address **0x51 (0xA2, 8-bit write byte)** — NOT the default all-zero/0x50 address used by small 8-bit-address EEPROMs | **VERIFIED — read directly in `datasheets/CY7C68013A-56LTXC.pdf`**, Document Number 38-08032 Rev. AD, printed page 16 of 74 (PDF page 17/75), section "I2C Interface Boot Load Access" and **Table 8, "Strap Boot EEPROM Address Lines to These Values"**. Table 8 lists, by EEPROM size/example part: 16B/24LC00 = N/A; 128B/24LC01 = 0,0,0; 256B/24LC02 = 0,0,0; 4K/24LC32 = 0,0,1; **8K/24LC64 = 0,0,1 (A2,A1,A0)**; 16K/24LC128 = 0,0,1. The preceding text states: "External EEPROM device address pins must be configured properly. See Table 8..." |
| 24LC64 compatibility | 24LC64 (64 Kbit = 8K×8) requires 2-byte (16-bit) addressing — matches the "large EEPROM" boot mode requirement above; its address pins A0/A1/A2 must be strapped A2=0,A1=0,A0=1 (see 24LC64-I/SN summary) | **VERIFIED** — cross-checked against Table 8 above (which names "24LC64" explicitly as the 8K example part) and against 24LC64-I/SN's own datasheet, DS21189T, p.7, §5.0 "Device Addressing" / Figure 5-1 (control byte = `1010 A2 A1 A0 R/W`), confirming A2,A1,A0 = 0,0,1 → control byte write value `1010 0010` = 0xA2 (8-bit), 7-bit address 0x51 |

## Notes — this is the single highest-value catch for this design's `usb_bridge` block
This exact failure mode — "an EEPROM the USB bridge explicitly cannot use" — is called out
as the single most expensive mistake in a prior measured run of this pipeline. **This
design uses the same EEPROM class (24LC64, 2-byte addressing) as that failure case, and the
requirement is now confirmed from two primary sources (the CY7C68013A datasheet's own
Table 8, and the 24LC64 datasheet's own control-byte format) — not just a community source:**
- The 24LC64 (U51) **must** have its address pins strapped **A2=0 (pull to GND), A1=0 (pull
  to GND), A0=1 (pull to VCC)**, giving I2C address 0x51 (0xA2 8-bit write), not the default
  all-GND/0x50, or FX2LP's boot-ROM autodetect will not find/read it correctly at boot. This
  is now a **verified fact**, confirmed identical to what was previously reported from
  community sources (revision 1 of this handoff) — the community answer was correct, and is
  now backed by the primary datasheet's own Table 8.
- `sourced_bom.md`'s `usb_bridge` block lists R52–R55 as "misc bridge pull/series
  resistors — not itemized in net_plan.md." **Four unallocated resistors is exactly the
  right count for 24LC64's A0/A1/A2 address-strap pins plus one WP (write-protect) pull.**
  The coder must strap A2→GND, A1→GND, A0→VCC (direct ties or 0Ω/10kΩ per board convention;
  A2/A1 need no pull-up resistor value beyond a solid tie since they're static DC straps),
  and WP→GND to allow writes, using 24LC64-I/SN's own pin numbers
  (`24LC64-I-SN_SUMMARY.md`).
- R50/R51 (2.2 kΩ) are already correctly identified as SCL/SDA I2C pull-ups in
  `sourced_bom.md` — no action needed there.
- Full CY7C68013A pin-by-pin table not extracted from the datasheet (56-pin QFN); the
  existing local symbol `MCU_Cypress:CY7C68013A-56LTX` was checked directly —
  **confirmed 57 unique pin numbers (1–57 = 56 physical pins + EP)**, matching the
  QFN-56-EP package. Safe to use as-is.
