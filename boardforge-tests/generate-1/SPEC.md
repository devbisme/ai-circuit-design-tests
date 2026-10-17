# SPEC — dual_adc_10msps

Dual-channel, ±10 V, 12-bit, 10 MSPS USB data-acquisition board.

Source: `design_prompt.txt` (user). The user asked for a fully autonomous run, so every
item below not stated in the prompt is a **driver choice**, tagged `(driver)`. Phase 2 may
revisit driver choices if it states why; user items are fixed.

## Functional
- 2 independent analog input channels. (user)
- Input range: −10 V to +10 V per channel. (user)
- Sample rate: 10 MSPS per channel, both channels simultaneously. (user; simultaneous = driver)
- Resolution: 12 bits. (user)
- Capture depth: ≥ 0.1 s at full rate on both channels = ≥ 1,000,000 samples/channel,
  2,000,000 samples total ≈ 3 MB packed 12-bit, 4 MB as 16-bit words. (user; arithmetic = driver)
- Input impedance: 1 MΩ ∥ ≤ 30 pF, so standard 1×/10× passive scope probes work and can be
  compensated. (driver — follows from "mate with standard oscilloscope leads")
- Input coupling: DC. (driver)
- Anti-alias filter: attenuation ≥ 72 dB (≈ 6.02 × 12) at and above fs/2 = 5 MHz.
  Passband DC–1 MHz flat within ±0.5 dB. (driver; derived from resolution and Nyquist)
- Input protection: survive ±30 V continuous on either input without damage. (driver)
- Analog performance target: ENOB ≥ 10 bits at 1 MHz input. (driver, SOFT)

## Power
- Board powered entirely from the host USB port. (user)
- Target: total draw ≤ 500 mA at 5 V (USB 2.0 default) so any USB 2.0 port suffices. (driver)
- If the budget exceeds 500 mA: use a USB-C receptacle and negotiate 1.5 A/3 A via CC
  (Rd 5.1 kΩ sink advertises; read source current). (user)
- Recommendation (driver): use a USB-C receptacle regardless, with USB 2.0 HS data — it
  satisfies both clauses and is the modern connector. Data stays USB 2.0.
- Analog rails derived on board (e.g. ±5 V or similar for the front end); low noise is
  needed near the ADC: ripple on the ADC reference/analog supply ≤ 1 mV pp. (driver)

## Interface
- Signal inputs: 2 × BNC female, PCB mount (mates with standard scope probes). (user → BNC = driver)
- Host: USB 2.0 High-Speed (480 Mb/s), power + data over one cable. (user)
- Sustained full-rate streaming would need 2 × 10 M × 2 B = 40 MB/s, at or above the
  practical USB 2.0 HS bulk limit (~35–42 MB/s). Therefore: capture to on-board memory,
  then upload. Streaming at reduced rate is a bonus, not a requirement. (driver)
- Triggering: software trigger from host required; level trigger on either channel is
  desirable (SOFT). (driver)
- Debug/programming header for any programmable logic or MCU. (driver)

## Physical
- SMD parts, JLCPCB assembly, top-side assembly preferred. (driver)
- 4-layer board, solid ground plane. (driver)
- Board size: ≤ 100 × 80 mm (SOFT). (driver)
- Operating temperature: 0–50 °C, bench use. (driver)
- No regulatory certification required (prototype). (driver)

## Production
- Quantity: 5 prototypes. (driver)
- Assembler: JLCPCB; prefer Basic/Preferred parts, in-stock. (driver)
- Cost target: ≤ $150 per board in parts at qty 5 (SOFT). (driver)
