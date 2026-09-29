# FT232HL-REEL — Hi-Speed USB to UART/FIFO bridge, 245 synchronous FIFO mode

| Spec | Value |
|------|-------|
| Package | LQFP-48 (7×7mm) |
| Vcc / Vin range | VCCIO 2.97–3.63V (I/O) or 1.62–1.98V; VREGIN = **5 V from VBUS**, VCORE/VCCD are its regulated 3.3 V outputs; USB 480Mbps |
| Key output spec | 60 MHz FIFO clock output (CLKOUT), 245 sync FIFO up to ~40 MB/s |
| Max current / power | 70 mA active, 10 µA quiescent |
| Operating temp | −40°C to +85°C |

## Pinout (48-pin LQFP, from EasyEDA/JLC symbol data)

| Pin | Name | Function |
|-----|------|----------|
| 1 | XCSI | 12MHz crystal input |
| 2 | XCSO | 12MHz crystal output |
| 3 | VPHY | USB PHY analog supply |
| 4, 9, 41 | AGND | Analog ground |
| 5 | REF | USB reference resistor (external precision resistor to AGND, per FTDI reference design) |
| 6 | DM | USB D− |
| 7 | DP | USB D+ |
| 8 | VPLL | PLL analog supply |
| 10, 11, 22, 23, 35, 36, 47, 48 | GND | Digital ground |
| 12, 24, 46 | VCCIO | I/O supply, 3.3V (or 1.8V) |
| 13–20 | ADBUS0–7 | FIFO data bus D0–D7 (245 sync FIFO mode) → `FIFO_D[7:0]` |
| 21, 25–33 | ACBUS0–9 | Control signals: RXF#, TXE#, RD#, WR#, SIWU, CLKOUT, OE# (exact mapping is set by the EEPROM configuration, not fixed silicon — confirm against FTDI AN_130/AN_167 245 FIFO application note when wiring `usb_bridge`) |
| 34 | RESET# | Active-low reset — R14 (10k, per sourced BOM) pull-up + C16 filter |
| 37 | VCCA | Analog core supply |
| 38 | VCORE | Internal core voltage (decouple, do not drive externally) |
| 39 | VCCD | 3.3 V **output** of the internal regulator (not an input) — decouple with 100 nF; do **not** drive it from another rail |
| 40 | VREGIN | Internal regulator input — **from `+5V_IN` (5 V), NOT from `+3V3_D`** — see the correction note below |
| 42 | TEST | Tie low (normal operation) — do not float |
| 43 | EEDATA | EEPROM data (93C46 DI/DO shared line) |
| 44 | EECLK | EEPROM clock |
| 45 | EECS | EEPROM chip select |

## Open question resolved — crystal load-capacitor recompute (top priority)

The sourced 12 MHz crystal (SX32Y012000BC1T001) specifies **12 pF load capacitance**, not
the ~20 pF the architecture's skeleton BOM assumed. **Recompute, do not use FTDI's generic
27 pF example** (which is explicitly stated in FTDI's own app notes as "good for many
crystals" assuming a higher-CL part, not a rule for every crystal):

```
Cext ≈ 2 × (CL − Cstray)
Cstray ≈ 3–5 pF (board trace + FT232H pin parasitic capacitance)
CL = 12 pF (this crystal's spec) → Cext ≈ 2 × (12 − 4) = 16 pF each
```

**Use 16–18 pF C0G/NP0 0603 caps for C13/C14** (both legs, XCSI/pin1 and XCSO/pin2 to
GND) — matches the sourced BOM's own note. This is lower than the architecture's placeholder
because the actual crystal's load spec is lower, not because of any error — a crystal
sourced with a *higher* CL would need correspondingly larger external caps. **Do not
independently re-derive from FTDI's 27 pF example figure** — that number is for a different
CL crystal.

## Notes

- **PREFIX-matched KiCad symbol** `Interface_USB:FT232H` — pin count/names not independently
  re-verified pin-by-pin against this table in this pass (no valid PDF obtained, both the
  LCSC-hosted URL and FTDI's own site returned non-PDF/403 responses — 2/2 attempts used,
  see Carried forward). The EasyEDA pinout above is internally consistent with the standard
  published FT232H pin function table and should be treated as reliable for pin **names**;
  spot-check pin **numbers** against the KiCad symbol before large modular-block wiring.
- **EEPROM (U8) is mandatory**: 245 sync FIFO mode is selected in the 93C46 EEPROM image, not
  in silicon. Firmware/EEPROM-image programming is out of scope for this pipeline (per
  upstream carried-forward decision) but the coder must still wire EECS/EECLK/EEDATA to U8.
- PWREN# (one of the ACBUS pins, exact number set by EEPROM config, typically ACBUS7 in
  FTDI's default 245 FIFO EEPROM template) drives Q1's gate per architecture decision 9 —
  confirm the exact ACBUS pin assignment against the EEPROM template used when the EEPROM
  image is created (out of scope here, flagged for whoever programs it).
- Lifecycle: confirmed **Active** (DigiKey cross-reference), stock 2048 at sourcing time.
- No PDF obtained — see Carried forward in the phase handoff. Pin table above is from live
  JLC/EasyEDA symbol data plus FTDI's publicly documented 245-FIFO/crystal application notes.

## CORRECTION (architecture rev 3 — ERC finding N-2)

**This summary originally said VREGIN (pin 40) comes from `+3V3_D`. That is wrong.** Per
FTDI **FT_000288 §6.1, "USB Bus Powered Configuration"**, VREGIN is fed from **VBUS 5 V** and
the internal regulator's 3.3 V appears **on VCCD (39)**, which is an *output*. `usb_bridge.py`
already wires it that way — **fix this document, not the code.**

It is load-bearing, not cosmetic: `+3V3_D` is downstream of the **PWREN#-gated load switch
U9**, and PWREN# is generated *by the FT232H*. Feeding VREGIN from `+3V3_D` is a deadlock —
the bridge could never start, so the switch would never close, so SPEC **P4** would be unmet
and the board would look dead at plug-in (architecture decisions 9, 13 and risk R-9).
