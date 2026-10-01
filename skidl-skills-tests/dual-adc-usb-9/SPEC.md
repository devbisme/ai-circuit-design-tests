# SPEC — dual_adc_usb

Source: `dual-adc-prompt.txt` (user). Items marked *(driver default)* were not specified by the
user; the prompt directed the pipeline to choose without pausing. Treat them as SOFT.

## Functional
- 2 independent analog input channels, simultaneous sampling.
- Input range: -10 V to +10 V per channel (user).
- Sample rate: 10 MSPS per channel (user). Resolution: 12 bits (user).
- Capture depth: >= 0.1 s at max rate on both channels (user)
  => 2 ch x 1e6 samples x 12 bit = 24 Mbit (3 MB packed, 4 MB at 16 bit/sample) minimum buffer.
- Input impedance: 1 MOhm || ~15-25 pF so standard 1x/10x scope probes compensate correctly *(driver default)*.
- Input coupling: DC *(driver default)*. Overvoltage survival: +/-50 V continuous at 1x *(driver default)*.
- Analog bandwidth: >= 5 MHz (-3 dB), anti-alias filter at Nyquist *(driver default)*.
- Trigger: software/host-initiated capture plus optional level trigger in logic *(driver default)*.

## Power
- Powered from USB VBUS (user). USB 2.0 default budget: 5 V, 500 mA (2.5 W).
- If estimated consumption exceeds the USB 2.0 budget, use a USB-C receptacle (5 V @ 1.5/3 A
  via Rp advertisement, CC 5.1k Rd) (user).
- No battery, no sleep requirement *(driver default)*.

## Interface
- Host link: USB 2.0 High-Speed (480 Mb/s) (user) for both power and data.
  Data rate if streamed: 2 ch x 10 MSPS x 2 B = 40 MB/s — at/above practical USB2 HS bulk
  throughput, hence the on-board buffer is mandatory for the 0.1 s capture.
- Analog connectors: BNC female (mates with standard oscilloscope probes) (user intent; BNC is the driver's interpretation).
- Debug/programming header for any FPGA/MCU *(driver default)*.

## Physical
- SMD preferred, 2-sided assembly allowed; 4-layer PCB *(driver default)*.
- Size: no constraint; target < 100 x 80 mm *(driver default)*.
- Temp: 0-70 C commercial *(driver default)*. No regulatory certification *(driver default)*.

## Production
- Quantity: prototype, 5-10 boards *(driver default)*.
- Assembly: JLCPCB PCBA, prefer Basic/Preferred-extended parts *(driver default)*.
- Cost: no hard target; minimize where it doesn't compromise specs *(driver default)*.
