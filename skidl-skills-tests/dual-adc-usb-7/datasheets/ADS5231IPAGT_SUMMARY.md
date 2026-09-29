# ADS5231IPAGT — Dual 12-bit 40MSPS pipeline ADC (adc_dual, U4)

| Spec | Value |
|------|-------|
| Package | TQFP-64 (10x10mm) |
| Vcc / Vin range | AVDD/VDRV 3.0–3.6V |
| Key output spec | 12-bit, 40MSPS max (20MSPS min with PLL enabled, 2MSPS min with PLL disabled), SNR 70.7dB, DNL 0.3LSB, INL 0.4LSB |
| Max current / power | Iq 97.3mA (both channels, PLL on) |
| Operating temp | −40°C to +85°C |

## Pinout
| Pin | Name | Function |
|-----|------|----------|
| 1 | SEL | Serial-interface select. 0=parallel-strap mode (pins 41/42/45=MSBI/OEA/STPD), 1=serial mode (pins 41/42/45=SEN/SCLK/SDATA). A low pulse on SEL after power-up resets the serial registers (SEL doubles as reset). |
| 6 | OEB# | Output Enable Channel B (0=enabled default, 1=tri-state) — independent pin, not shared |
| 24 | CLK | Sample clock |
| 26 | DVA | Data valid, channel A |
| 22 | DVB | Data valid, channel B |
| 27–38 | D0_A–D11_A | Channel A data (D11=MSB) |
| 10–21 | D0_B–D11_B | Channel B data (D11=MSB) |
| 39 | OVRA | Over-range indicator A |
| 9 | OVRB | Over-range indicator B |
| 41 | MSBI/SEN | SEL=0: MSBI (output format). SEL=1: SEN (serial write enable) |
| 42 | OEA#/SCLK | SEL=0: OEA (0=enabled default, 1=tri-state). SEL=1: SCLK (serial clock) |
| 45 | STPD/SDATA | SEL=0: STPD (power-down, 0=normal default). SEL=1: SDATA (serial write data) |
| 50/51 | INA+/INA- | Channel A differential analog input |
| 62/63 | INB-/INB+ | Channel B differential analog input |
| 52 | CM | Common-mode reference output, +1.5V typ, ±2mA drive |
| 53/54 | REFT/REFB | Top/bottom reference (I/O) — 2Ω + 0.1µF bypass to GND each |
| 56 | INT/EXT# | Reference select: 0=external (default), 1=internal. Force high for internal reference. |
| 60 | ISET | Bias-current-setting resistor, 56.2kΩ to GND (R401) |
| 5,8,40,43 | VDRV | Output buffer supply |
| 3,46,57 | AVDD | Analog supply |
| 2,47–49,55,58,59,61,64 | AGND | Analog ground |
| 4,7,23,25,44 | GND | Output buffer ground |

## Load-bearing facts
| Fact | Value | Source |
|------|-------|--------|
| Differential input voltage window (per pin, VCM=1.5V nominal) | **1.0 V to 2.0 V** (IN/IN̄ each swing 1V–2V around VCM for the default 2VPP differential FSR) | `ADS5231IPAGT.pdf` p.19, "Input Over-Voltage Recovery" — **verified**, matches architecture's stated 1.0–2.0V/pin exactly |
| PLL floors minimum sample rate at 20 MSPS when enabled; PLL disabled → down to 2 MSPS | Confirmed | `ADS5231IPAGT.pdf` p.8 (table) and p.19 "PLL CONTROL" — **verified** |
| PLL-disable serial register write | Serial register, 8-bit word D7..D0 = **0 0 1 1 X X 1 0** (address+data combined; X=don't care, use 0). SEL must =1 first (enables serial iface on pins 41/42/45=SEN/SCLK/SDATA), then a low-going pulse on SEL resets registers, then write this word via SEN/SCLK/SDATA. | `ADS5231IPAGT.pdf` p.8, "SERIAL REGISTER MAP" table, "PLL Disabled" row — **verified** |
| With PLL disabled, clock duty cycle must be held close to 50% (not the 45–55% allowed with PLL on) | Confirmed | `ADS5231IPAGT.pdf` p.19 — **verified** |
| ISET = 56.2kΩ to GND (R401) sets internal bias | Confirmed, matches sourced_bom R401 | `ADS5231IPAGT.pdf` p.11 pin table + p.17 — **verified** |

## SEL pin: static strap vs. dynamic — CRITICAL, answered for the architect (coordinator-directed)

The architect proposed tying SEL to a static strap resistor to free an FPGA pin. **Settled: SEL
must stay dynamically FPGA-driven. A static strap risks leaving the PLL enabled/undisableable,
which would fail the 10MSPS requirement (SPEC F3).**

(a) **Is the low-going pulse REQUIRED, or just a convenience reset? VERIFIED — required.**
Direct quote, `ADS5231IPAGT.pdf` p.19, §"SERIAL INTERFACE": *"When the serial interface is to
be enabled, SEL serves the function of a RESET signal. After the supplies have stabilized, it
is necessary to give the device a low-going pulse on SEL. This results in all internal
registers resetting to their default value of 0 (inactive). **Without a reset, it is possible
that registers may be in their non-default state on power-up. This condition may cause the
device to malfunction.**"* The datasheet's own "RECOMMENDED POWER-UP SEQUENCING" timing diagram
(p.9) also shows a SEL transition as a required step before "Device Ready For Serial Register
Write" — it is documented as mandatory, not optional.

(b) **Power-up default state of the PLL-enable bit? VERIFIED — PLL enabled (disable-bit=0).**
Serial register map (p.8): row `0 0 1 1 X X 0 0` = "PLL Enabled (default)"; the PLL-disable
control is bit D1 of that register, default 0. Matches the electrical table's own "PLL Enabled
(default)" note (p.1/8).

(c) **Can the PLL-disable word be written with SEL held statically high from power-up?
VERIFIED — not reliably, no.** The datasheet gives no supported path for this: the required
pulse (point a) is what brings the registers to a known state before any write is documented as
safe, and TI's own procedure treats it as a precondition, not an option to skip. A static-high
SEL never issues that pulse, so the "may be in non-default state... may malfunction" warning
applies directly — the ADC's post-power-up register state, and thus whether any subsequent
write actually lands as intended, is **undocumented/unguaranteed** without it.

**Conclusion for the architect: keep SEL as a dynamic FPGA-driven pin** (drive low-pulse after
power-up, then hold high while writing SEN/SCLK/SDATA per the existing PLL-disable sequence in
Load-bearing facts above). A static strap is not supported by the datasheet for this use case.

## Notes on R402 (unattributed placeholder, sourcing flagged)
**R402 has no datasheet-justified function.** The ADS5231 needs exactly one bias-setting resistor (ISET, R401=56.2kΩ). `net_plan.md` line 76 already routes `ADC_SEL` as a direct FPGA-driven net (U5→U4), not a static strap resistor — so R402 is not a SEL pull-up either. Checked against the full pin table (64 pins) above: every other pin is either analog input, digital I/O routed to the FPGA (net_plan lines 75–77), a supply/ground pin, or REFT/REFB (which take a fixed 2Ω+0.1µF bypass, not a discrete resistor of arbitrary value). **Recommendation: delete R402 from the BOM** unless the coder wants a safety series resistor somewhere the sourcer didn't intend — there is no ADS5231 pin that needs it.

**Also found while reading the pin table (flag for the coder):** `net_plan.md` line 77 ties `MSBI` and `OEA` statically to GND. But pins 41 and 42 are the *same physical pins* as `SEN` and `SCLK` when `SEL=1` (serial mode) — and R-6/`ADC_SEN`/`ADC_SCLK` explicitly require serial mode to disable the PLL for 10MSPS operation. **These two constraints conflict**: MSBI/OEA cannot be hard-tied to GND *and* be driven dynamically as SEN/SCLK. Only `OEB#` (pin 6, a genuinely separate pin) is safe to tie statically. The coder must drop the GND ties on pins 41/42 and drive them as SEN/SCLK from the FPGA instead.

## Notes
- `[CRIT]` single-source ADC, 154pcs at JLCPCB = entire float (sourcing decision 1).
- Datasheet: `datasheets/ADS5231IPAGT.pdf` (TI SBAS295A, 2004/rev.2007 — old but this is TI's only datasheet for this part, R-8).
- Generated symbol: `dual_adc_usb:ADS5231IPAGT` in `symbols/dual_adc_usb.kicad_sym` (64 pins, `find-symbol.py` reports `EXACT`).
