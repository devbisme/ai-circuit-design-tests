# GW1NR-LV9QN88PC6/I5 — Gowin LittleBee FPGA, 8640 LUT4, in-package RAM, QN88

| Spec | Value |
|------|-------|
| Package | QFN-88 (QN88), 10×10mm, 0.4mm pitch, exposed pad |
| Vcc / Vin range | VCC (core, LV) **1.14–1.26V** typ 1.2V; VCCX **2.375–3.6V**; VCCOx **1.14–3.6V** |
| Key spec | 8640 LUT4, in-package RAM (see correction below), internal config flash (self-boots) |
| Abs. max | VCC ≤1.32V, VCCX/VCCO ≤3.75V (all −0.5V min) |
| Operating temp | Industrial: Tj −40°C to +100°C (commercial 0°C to +85°C) |

## Open question resolved — supply rails (top priority)

**Confirmed from Gowin datasheet DS117 (Table 4-2, `datasheets/GW1NR-LV9QN88PC6-I5.pdf`)
and package guide UG119E: the architecture's 1.2V + 3.3V-only assumption is correct and
requires no third rail.**

- **VCC (core, LV variant) = 1.2V nominal**, recommended range 1.14–1.26V. This is `+1V2_D`.
- **VCCX must be ≥2.375V** (min) and **VCCOx accepts 1.14–3.6V** — tying every VCCIOx pin
  and VCCX to `+3V3_D` / `+3V3_ADCD` (3.3V) is valid for every I/O bank on this part; no bank
  requires a different voltage.
- **No board-exposed low-voltage memory bank exists to trip over.** The in-package RAM
  interface is entirely internal to the SiP (no RAM signal pins are bonded out — confirmed:
  none of the 89 pins are named for a memory bus), so the "one bank tied to embedded-RAM
  voltage" failure mode that this note warns about in other designs does not apply here.

## Correction to the architecture handoff — SDRAM, not PSRAM

Architecture decision 2 called this "64 Mbit in-package **PSRAM**." Gowin's own package
guide (UG119E) labels the **QN88** package variant of the GW1NR-4/9 family as
**"SDRAM Embedded"** and reserves "PSRAM Embedded" for the **QN88P** variant (different
suffix). This MPN's package code is `QN88` (not `QN88P`), so **the embedded memory is SDR
SDRAM, not PSRAM.** This does not change any pin, rail, or the "no external memory bus"
benefit the architecture relied on — it is a documentation correction only, but the coder's
comments/board silkscreen should say SDRAM, not PSRAM, if either is mentioned.

## Power pin map (from UG119E Table 3-7, "Other pins in GW1NR-9 QN88" — authoritative;
corrects one EasyEDA-derived pin label, see below)

| Net | Pins |
|-----|------|
| VCC (core, 1.2V) | 1, 22, 45, 66 |
| VCCX/VCCIO0 (Bank 0, tie to 3.3V) | 64, 67, 78 |
| VCCIO1 (Bank 1, tie to 3.3V) | 58 |
| VCCIO2 (Bank 2, tie to 3.3V) | 23, 44 |
| VCCIO3 (Bank 3, tie to 3.3V) | 12 |
| VSS (ground) | 2, 21, 24, 43, 46, 65 |
| MODE[1:0] | 87 (MODE1), 88 (MODE0) — boot-mode strap, see below |
| EP (exposed pad) | 89 — **tie to GND/VSS** (confirmed by datasheet note on thermal pad) |

**Correction**: the EasyEDA/JLC pinout service labels pin 12 as `VCCX/VCCO0`. Gowin's own
UG119E pin table gives pin 12 as **VCCIO3** instead — a different bank's supply, not a
duplicate of the pin-64/67/78 net. **Trust UG119E (this file); do not tie pin 12 to the same
net as pins 64/67/78.** (Both are 3.3V in this design, so a wiring mistake here would not
fail electrically, but they are logically separate bank supplies — keep them as separate
SKiDL nets in case a future revision splits bank voltages.)

## Pinout (89 pins total, IOL=left bank(3), IOB=bottom bank(2), IOR=right bank(1),
IOT=top bank(0) — exact names as generated into the symbol; alternate/muxed functions are
part of the same pin name, separated by `/`, exactly as Gowin spells them)

See `symbols/dual_adc_usb.kicad_sym` (symbol `GW1NR-LV9QN88PC6-I5`, 89/89 pins verified) for
the full per-pin list — reproduced here for the pins the block coder is most likely to use:

| Pin | Name | Notes |
|-----|------|-------|
| 5,6,7,8,4 | IOL11A/TMS, IOL11B/TCK, IOL12B/TDI, IOL13A/TDO, IOL5A/JTAGSEL_N/LPLL_T_in | JTAG (`fpga_core` J4 header) — usable as GPIO only if JTAGSEL_N is held low simultaneously with the JTAG pins (see datasheet note, DS117 p.6) |
| 9 | IOL13B/RECONFIG_N | Ties to `fpga_core` R17 pull per sourced BOM |
| 10 | IOL14A/DONE | Configuration-done status |
| 87, 88 | IOT6B/MODE1, IOT5A/MODE0 | Boot-mode strap — see below, **not general-purpose GPIO** |
| 11, 35/36 | IOL15A/GCLKT_6, IOB29A/GCLKT_4, IOB29B/GCLKC_4 | Dedicated global-clock-capable pins — route `FPGA_CLK` from `clock_20m` to one of these, not an arbitrary IO |
| 89 | EP | Thermal/ground pad — **add as its own SKiDL pin, tie to GND** |

## MODE[1:0] boot-strap — carried forward, not fully resolved

Architecture requires the FPGA to self-configure from internal flash (no external config
memory, decision 9/architecture). Gowin's GW1NR family supports 7 config modes (AUTOBOOT,
SSPI, MSPI, CPU, SERIAL, DUAL BOOT, I2C Slave) selected by a MODE[2:0] strap, but **this QN88
package only bonds out 2 of those 3 mode bits (pins 87/88 = MODE1/MODE0)** — the truth table
mapping MODE[1:0] to AUTOBOOT is given as a figure in Gowin's configuration guide (UG289),
which is image-based and did not extract as text in this pass. **Common practice (and the
Sipeed Tang Nano 9K reference design, which uses this exact MPN) ties both MODE0 and MODE1
to GND via pull-down resistors for AUTOBOOT-from-internal-flash** — this is very likely
correct but **the coder must confirm against UG289's MODE truth table (or the Tang Nano 9K
schematic) before finalizing fpga_core**, since a wrong strap means the board "self-configures"
into the wrong mode and looks dead (the exact R-9 risk architecture flagged).

## Notes

- **Symbol generated**: `dual_adc_usb:GW1NR-LV9QN88PC6-I5` (slash sanitized to dash — MPN has
  a literal `/` which KiCad/SKiDL symbol names can't carry) in `symbols/dual_adc_usb.kicad_sym`,
  89/89 pins verified EXACT by `find-symbol.py`. **The coder must reference the part in SKiDL
  by this sanitized name**, `Part('dual_adc_usb', 'GW1NR-LV9QN88PC6-I5')`, not the raw MPN.
- Footprint `Package_DFN_QFN:ArtInChip_QFN-88-1EP_10x10mm_P0.4mm_EP6.74x6.74mm` — pin
  count/pitch/body confirmed against the package; **exact EP size (6.74×6.74mm) was not
  independently verified against Gowin's package outline drawing** (that drawing is a
  graphic in UG119E page ~22, "QN88/QN88P Package Outline", not text-extractable in this
  pass) — carried forward for the layout/footprint-review step.
- Datasheet PDF: `datasheets/GW1NR-LV9QN88PC6-I5.pdf` (Gowin DS117, family datasheet covering
  GW1NR-1/2/4/9 — this MPN is the GW1NR-9C variant. Verified as containing this family by
  `fetch-datasheet.py`).
- Single-source, stock 180 at sourcing time — carried forward unchanged.
