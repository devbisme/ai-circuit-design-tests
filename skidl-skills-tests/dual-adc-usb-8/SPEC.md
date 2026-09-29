# SPEC — dual_adc_usb

Source: `dual-adc-prompt.txt` (user). Items tagged *(driver)* were chosen by the pipeline driver
because the user instructed "list options, pick one, do not pause" — they are open to revision.

## Functional
- 2 independent analog input channels, simultaneous sampling. [HARD]
- Input range: −10 V … +10 V per channel (at the board connector). [HARD]
- Sample rate: 10 MSa/s per channel. [HARD]
- Resolution: 12 bits. [HARD]
- Capture depth: ≥ 0.1 s at max rate → ≥ 1,000,000 samples/channel, 2,000,000 total
  (3.0 MB packed 12-bit; 4.0 MB as 16-bit words). [HARD]
- Input impedance ≈ 1 MΩ ‖ ~20 pF so standard 1×/10× oscilloscope probes are compensated correctly. *(driver)* [SOFT]
- Analog bandwidth: ≥ 5 MHz (−3 dB, Nyquist) with anti-alias filtering. *(driver)* [SOFT]
- Input overvoltage survival: ≥ ±30 V continuous without damage. *(driver)* [SOFT]
- Trigger: software/host-started capture minimum; level trigger in digital logic optional. *(driver)* [SOFT]

## Power
- Board is bus-powered from the host USB port. [HARD]
- Budget: USB 2.0 = 5 V / 500 mA (2.5 W) after enumeration. If the architecture's estimated
  draw exceeds ~2.0 W (leave margin), use a USB-C receptacle with CC pull-downs for
  5 V / 1.5 A or 3 A. [HARD — user rule]
- Driver note: even with USB 2.0 data, a USB-C receptacle is acceptable either way *(driver)*;
  architect decides from the power budget.
- Rails derived on-board (bipolar analog rails for ±10 V front end may need a charge pump or
  isolated/inverting converter). No battery, no sleep-mode requirement.

## Interface
- Signal inputs: 2 × BNC female (50 Ω-footprint type used by scope probes), PCB-mount. [HARD — "mate with standard oscilloscope leads"]
- Host: USB 2.0 (High-Speed 480 Mb/s preferred) for power and data. [HARD]
- Data transfer: capture-to-local-memory then upload is acceptable; continuous streaming not
  required (2 ch × 10 MSa/s × 16 bit = 40 MB/s is at the edge of USB 2.0 HS practical throughput). *(driver)* [SOFT]
- Debug/programming header for the controller (SWD/JTAG) *(driver)* [SOFT].

## Physical
- SMD, 2- or 4-layer PCB (4-layer preferred for ADC/USB HS signal integrity). *(driver)* [SOFT]
- Size: no hard limit; target ≤ 100 × 80 mm. *(driver)* [SOFT]
- Temperature: 0 … 50 °C, commercial. *(driver)* [SOFT]
- Regulatory: none (lab instrument prototype). *(driver)* [SOFT]

## Production
- Quantity: prototype, 5–10 boards. *(driver)* [SOFT]
- Assembly: JLCPCB PCBA; prefer basic/extended parts in stock. *(driver)* [SOFT]
- Cost: no target stated; prefer lowest reasonable cost. *(driver)* [SOFT]
- Blank slate: do not reuse results or intermediate files from other designs. [HARD — user]
