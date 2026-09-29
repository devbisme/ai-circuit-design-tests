# ADS5231IPAGT — Dual 12-bit 40 MSPS pipeline ADC

| Spec | Value |
|------|-------|
| Package | TQFP-64 (10×10mm) |
| Vcc / Vin range | AVDD/VDRV 3.0–3.6 V |
| Key output spec | 70.7 dB SNR (11.4 ENOB), 0.4 LSB INL, 0.3 LSB DNL |
| Max current / power | Iq 97.3 mA (both channels) |
| Operating temp | −40 °C to +85 °C |
| **Clock frequency** | **20 MHz – 40 MHz** (datasheet parametric field, confirmed) |

## Open question resolved — with an important nuance the architecture didn't have

**Confirmed directly from the datasheet's own electrical table** (`datasheets/ADS5231IPAGT.pdf`,
"CLOCK INPUT AND OUTPUTS" section):

```
ADCLK Input Sample Rate
  PLL Enabled  (default):  20 – 40 MSPS
  PLL Disabled:             2 – 30 MSPS
```

**With the PLL enabled (the ADC's power-on default), the minimum clock is 20 MHz — this
makes the architecture's 20.000 MHz direct-clock, host-2:1-decimation scheme legal exactly at
the ADC's minimum.** There is no margin below 20 MHz in this mode, so the clock source
(X1/replacement) must not be pulled low by trimming or thermal drift below ~19.9 MHz.

**Nuance for the record, not a change to this design**: the datasheet also shows the ADC
*can* run as low as 2 MSPS if the internal PLL is disabled — a mode the architecture did not
know about when it concluded "the ADC cannot run at 10 MHz" and built the whole
20 MSPS + host-decimation scheme around that belief. A PLL-disabled 10 MSPS-direct design
was technically possible and would have removed the need for 2:1 host decimation entirely.
**This is not acted on here** — the design is already sourced and partly symbol-generated
around the 20 MSPS/PLL-enabled approach, and re-opening the clocking topology is an
architecture-phase decision, not a datasheet-phase one (per the phase-handoff contract:
disagreements with upstream decisions are escalated, not silently redecided). Flagged in the
phase handoff's Carried Forward for whoever reviews the design next.

Also confirmed: **ADCLK duty cycle spec is 45–55%** with PLL enabled — both the original XO
(SX3M20.000B10F20TNN) and its replacement (OT252020MJBA4SL) publish exactly 45–55% duty
cycle, so this is met either way. The ADC auto-enters a power-down mode if the clock ever
drops below ~2 MSPS-equivalent and auto-resumes above it — a glitch-tolerance detail worth
knowing, not an action item.

## Pinout (64-pin TQFP — pin functions below are transcribed from the TI datasheet's own Pin
Functions table, `datasheets/ADS5231IPAGT.pdf`, not just the EasyEDA symbol)

| Pin | Name | Function |
|-----|------|----------|
| 1 | SEL | Interface select: **0 = parallel-control mode** (pins 41/42/45 = MSBI/OEA/STPD, serial disabled), 1 = serial mode (pins 41/42/45 = SEN/SCLK/SDATA). Also acts as serial-interface RESET when SEL=1. |
| 2,47,48,49,55,58,59,61,64 | AGND | Analog ground |
| 3,46,57 | AVDD | Analog supply 3.0–3.6V |
| 4,7,23,25,44 | GND | Output-buffer ground |
| 5,8,40,43 | VDRV | Output buffer supply |
| 6 | OE B | Output enable, channel B. 0 = Enabled (default), 1 = Tri-state |
| 9 | OVRB | Overrange flag, channel B |
| 10–21 | D0_B(LSB)…D11_B(MSB) | Channel B data output |
| 22 | DVB | Data Valid, channel B |
| 24 | CLK | Sample clock input — drive directly from X1/replacement XO. **Must stay ≥20 MHz** (ADC's own datasheet floor) |
| 26 | DVA | Data Valid, channel A |
| 27–38 | D0_A(LSB)…D11_A(MSB) | Channel A data output |
| 39 | OVRA | Overrange flag, channel A |
| 41 | MSBI/SEN | **When SEL=0:** MSBI — 1 = two's complement, **0 = straight offset binary (default)**. When SEL=1: SEN |
| 42 | OEA/SCLK | **When SEL=0:** OEA — 0 = Enabled (default), 1 = Tri-state. When SEL=1: SCLK |
| 45 | STPD/SDATA | **When SEL=0:** STPD (power-down) — 0 = Normal (default), 1 = power-down. When SEL=1: SDATA |
| 50 | INA | Channel A analog input + |
| 51 | IN A | Channel A analog input − (complementary) |
| 52 | CM | Common-mode reference output (drives THS4551 VOCM in `afe_channel`) |
| 53 | REFT | Top reference I/O — bypass with 2Ω + 0.1µF to ground (both internal and external ref modes) |
| 54 | REFB | Bottom reference I/O — same bypass network as REFT |
| 56 | INT/EXT | Reference select: 0 = External (default), **1 = Internal**. Force high for internal reference |
| 60 | ISET | Bias current set — 56.2kΩ to ground sets the internal bias |
| 62 | IN B | Channel B analog input − (complementary) |
| 63 | INB | Channel B analog input + |

## Strapping recommendation (no dedicated reference IC or serial controller in the sourced BOM)

The sourced BOM has no external voltage reference and no microcontroller talking a serial
protocol to this ADC, so the coder should tie these control pins to fixed CMOS levels rather
than leave them floating (TI's table states *default* behavior, it does not say these pins
have an internal pull — an unterminated CMOS input is undefined):
- **SEL = 0** (tie low) → parallel-control mode, pins 41/42/45 become MSBI/OEA/STPD.
- **INT/EXT = 1** (tie high) → internal reference (no external reference IC exists in the BOM).
- **MSBI = 0** (tie low) → straight offset binary output, unless the FPGA capture logic in
  `fpga_core` expects two's complement — check before wiring, this is a data-format choice,
  not a hardware one.
- **OEA = OE B = 0** (tie low) → outputs always enabled (never tri-stated); ties to a pulldown
  or directly to GND since nothing in this design needs to tri-state the ADC bus.
- **STPD = 0** (tie low) → normal operation, never powered down.
- **ISET, REFT, REFB** are analog bias/reference pins, not logic — bypass per the table above,
  do not tie to a rail.

## Notes

- **Symbol generated**: `dual_adc_usb:ADS5231IPAGT` in `symbols/dual_adc_usb.kicad_sym`
  (64/64 pins verified, `find-symbol.py` reports EXACT). Footprint:
  `Package_QFP:TQFP-64_10x10mm_P0.5mm`.
- CM (pin 52) is the ADC's own common-mode pin the architecture uses to drive VOCM on both
  THS4551 FDAs — do not invent a separate VOCM reference.
- Single-source, stock 154 at run time — carried forward from sourcing, unchanged.
- Datasheet PDF: `datasheets/ADS5231IPAGT.pdf` (TI, verified correct part, text-searchable).
