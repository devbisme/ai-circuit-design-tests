# Skeleton BOM — dual_adc_usb

Quantities are **per board**. The part-sourcer replaces "suggested MPN" with a verified,
in-stock MPN + LCSC number + KiCad footprint, and must re-verify every stock figure in
`ic_selection.md`.

`analog_frontend` is one block instantiated **twice**; its quantities below already account
for both channels.

## Active — critical path

| function | suggested MPN | package | qty | notes |
|---|---|---|---|---|
| 12-bit ADC, 10 MSPS used | AD9235BCPZ-40 | LFCSP-32 5×5 0.5 mm | 2 | **Package fixed.** Same-footprint alternates: AD9235BCPZ-20, AD9235BCPZ-65. TSSOP-28 AD9235BRUZ-xx is *not* a footprint swap |
| FPGA + 64 Mbit PSRAM | GW1NR-LV9QN88PC6/I5 | QFN-88 10×10 0.4 mm | 1 | **Single source, 102 in stock, critical path.** "P" suffix = PSRAM at 1.8 V — do not substitute the QN88 (SDRAM) variant without telling the architect, it changes the power tree. Escalation part: GW2AR-LV18QN88C8/I7 |
| USB 2.0 HS device controller | CY7C68013A-56LTXC | QFN-56-EP 8×8 | 1 | 0–70 °C grade matches X5. SSOP-56 (-56PVXC) is a second source with a different footprint |
| Dual FET-input op amp | AD8066ARZ-R7 | SOIC-8 | 2 | 1 per channel: unity buffer + Sallen-Key section. **Do not substitute below 100 V/µs slew** |
| Fully differential ADC driver | THS4551IRGTR | QFN-16-EP 3×3 | 2 | Rail-to-rail output is required at ±4.2 V. Second source ADA4940-1ARZ-R7 is SOIC-8 — **not** footprint-compatible |
| 10.000 MHz XO, ≤5 ps rms | SiT1602BI-22-33E-10.000000 | SMD3225-4P | 1 | 3.3 V LVCMOS. Any XO ≤10 ps rms integrated jitter is a valid substitute |
| Dual buffer, clock fanout | SN74LVC2G34DBVR | SOT-23-6 | 1 | Both ADC clocks must come from the **same package** (F10 skew) |
| 24.000 MHz crystal | X322524MOB4SI | SMD3225-4P | 1 | CL 12 pF, ±100 ppm — FX2LP requirement, not negotiable |
| I²C boot EEPROM, 16 kB | CAT24C128WI-GT3 | SOIC-8 | 1 | Address strapped to 0xA2 (A0=1). 24LC128 / AT24C128 equivalents fine |

## Active — power

| function | suggested MPN | package | qty | notes |
|---|---|---|---|---|
| ±4.2 V charge pump + integrated ± LDOs | LM27762DSSR | WSON-12-EP 2×3 | 1 | **Do not substitute a part without integrated LDOs** — P5 requires LDO post-regulation on every analog rail. Switching frequency must be ≥2 MHz so ripple lands above the 1 MHz measurement band |
| AVDD 3.0 V LDO, low noise | LP5907MFX-3.0 | SOT-23-5 | 1 | ≤30 µVrms output noise required (P5) |
| +3V3_AON LDO, 300 mA | AP2112K-3.3TRG1 | SOT-23-5 | 1 | Always on; powers the pre-enumeration island only |
| +3V3 buck, EN pin required | TLV62569DBVR | SOT-23-5 | 1 | **EN pin mandatory** (PWR_EN). Soft-start must give a 0.33–5.5 ms monotonic ramp |
| +1V2 buck, EN pin required | TLV62568DBVR | SOT-23-5 | 1 | **EN pin mandatory.** Ramp window 0.2–2 ms (Gowin VCC ramp 0.6–6 mV/µs) |
| +1V8 LDO, 250 mA, EN | LP5907MFX-1.8 | SOT-23-5 | 1 | PSRAM bank VCCIO |
| Buck inductors | 2.2 µH / 1.5 A shielded | 0806/1210 | 2 | One per buck; ≥1.5 A saturation |
| Charge-pump flying + reservoir caps | 1 µF / 10 µF X7R 16 V | 0603/0805 | 4 | Per LM27762 datasheet |

## Passives — analog front end (per-board totals for 2 channels)

| function | value / spec | package | qty | notes |
|---|---|---|---|---|
| Attenuator top leg | 909 kΩ ±0.1 % | 0805 or 2×0603 series | 2 | **≥100 V working voltage** — F9 puts 45 V across it continuously |
| Attenuator bottom leg | 90.9 kΩ ±0.1 % | 0603 | 2 | Sets ÷11 exactly with the 909 k |
| Compensation cap, top | 15 pF C0G ±2 %, ≥100 V | 0603 | 2 | Sets the ~18 pF seen at the BNC |
| Compensation cap, bottom | 150 pF C0G ±2 % (or 120 pF + 6–30 pF trimmer) | 0603 | 2 | See `design_risks.md` R5 — trimmer is the one part that may not source |
| Buffer series protection | 1.00 kΩ ±1 % | 0603 | 2 | Limits clamp current on ±50 V overload |
| Input clamp | BAV199 | SOT-23 | 2 | Low-leakage dual series diode, mid-pin = signal, ends = ±4V2A |
| Sallen-Key resistors | 324 Ω ±1 % | 0603 | 4 | 2 per channel |
| Sallen-Key caps | 330 pF and 47 pF C0G ±2 % | 0603 | 4 | Sets f0 3.95 MHz, Q 1.33 |
| FDA gain-set Rg | 1.00 kΩ ±0.1 % | 0603 | 4 | |
| FDA feedback Rf | 1.10 kΩ ±0.1 % | 0603 | 4 | Rf/Rg = 1.10 restores 2 Vpp differential |
| FDA MFB R3 | 1.00 kΩ ±1 % | 0603 | 4 | |
| FDA MFB caps | 68 pF C0G ×4, 11 pF C0G ×2 (differential) | 0603 | 6 | |
| ADC kickback filter | 33 Ω ±1 % ×4, 22 pF C0G ×2 | 0603 | 6 | Series into VIN±, differential shunt |
| ADC VCM divider | 10.0 kΩ ±0.1 % | 0603 | 2 | 1.50 V from +3V0A, shared by both FDAs |

## Passives — general

| function | value | package | qty | notes |
|---|---|---|---|---|
| VBUS bulk | 10 µF X5R 16 V | 0805 | 1 | **10 µF total at the connector** — USB 2.0 §7.2.4.1 inrush (P7) |
| Rail bulk | 10 µF X5R | 0805 | 8 | One per regulated rail |
| Decoupling | 100 nF X7R 25 V | 0402 | ~45 | One per IC supply pin; FPGA needs ≥12, ADCs ≥6 |
| Decoupling, bulk local | 1 µF X7R | 0603 | ~8 | |
| ADC REFT/REFB | 100 nF ×4, 10 µF differential ×2 | 0603/0805 | 6 | Per AD9235 datasheet |
| Ferrite beads | 600 Ω @ 100 MHz, ≥500 mA | 0603 | 5 | FB1 VBUS, FB2 into LM27762, FB3 +3V0A, FB4 +3V3_DRV, FB5 FX2LP AVCC |
| CC pulldowns | 5.1 kΩ ±1 % | 0402 | 2 | USB-C sink advertisement (I2) |
| I²C pull-ups | 2.2 kΩ | 0402 | 2 | |
| PWR_EN pulldown | 100 kΩ | 0402 | 1 | **Mandatory** — see `design_risks.md` R8 |
| FX2LP reset RC | 100 kΩ + 1 µF | 0402/0603 | 2 | |
| Crystal load caps | 12 pF C0G | 0402 | 2 | |
| Clock series termination | 33 Ω | 0402 | 3 | CLK_ADC1, CLK_ADC2, CLK_FPGA |
| Pull-ups: RECONFIG_N, TMS | 10 kΩ | 0402 | 2 | |
| Feedback dividers | per regulator datasheet | 0402 | 8 | 2 bucks + LM27762 ± outputs |
| LED series | 1 kΩ | 0402 | 2 | |
| Trigger series + ESD | 100 Ω + PESD3V3L1BA | 0402 / SOD-323 | 2 | |

## Connectors, indicators, mechanical

| function | suggested MPN | package | qty | notes |
|---|---|---|---|---|
| BNC jack, female | KH-BNC50-3511 | THT | 2 | THT allowed by X3. Shell ties to GND |
| USB-C receptacle, 2.0 | TYPE-C 16PIN 2MD(073) | SMD | 1 | USB 2.0 wiring only |
| USB ESD array | USBLC6-2SC6 | SOT-23-6 | 1 | On USB_DP / USB_DM |
| VBUS TVS | SMAJ5.0A | DO-214AC | 1 | JLCPCB **Preferred** tier |
| JTAG header | 2×3 0.1" pin header | THT | 1 | Gowin: VCC, GND, TCK, TDO, TDI, TMS |
| Ext trigger header | 1×3 0.1" pin header | THT | 1 | TRIG_IO, GND, +3V3 (I10) |
| LEDs | green (PWR), amber (CAP) | 0603 | 2 | |
| Test points | 1 mm pad / loop | — | ~14 | 8 rails + 4 ADC inputs + spare (N5) |
| Mounting | M3 hole | — | 4 | X7 |

## Cost check against N3 (≤$180/board at qty 5)

Actives ≈ $96 (ADCs $36.8, FPGA $20.9, FX2LP $10.7, amps $15.7, power $1.6, clock $1.3,
EEPROM/crystal $0.5, connectors/protection $2.5, misc $6). Passives, headers, LEDs and test
points ≈ $8. **Estimated ≈ $104/board**, 42 % under the target. The ADC pair and the FPGA are
64 % of it — those are the two lines to attack if the target ever tightens.
