# dual_adc_usb — Design risks (rev 2)

Severity: H = can fail a requirement, M = degrades a spec, L = nuisance. Each risk carries its working.

## Power integrity / budget

| # | Risk | Sev | Working / mitigation |
|---|---|---|---|
| P1 | USB 2.0 budget <!-- revised: FT232H 112 mA max, +1V8 rail, Y1 5 mA --> | M | Loads (max where a datasheet gives max): **3V3A** 82.1 mA ADC AVDD + 2×5 mA FDA = 92.1 mA (LDO ⇒ 92.1 mA from VBUS). **LM27762** 2×(4.6+1.0) mA per rail + 2 mA → 24.4 mA from VBUS. **3V3D** 40 FPGA VCCX/VCCO1/2 + **112 FT232H** (52 Ireg + 60 Iccphy max, DS Tables 5.3/5.4; 82 typ) + 10 (Y1 5 + LEDs 2.6 + EEPROM 2) + 33 ADC VDRV = **195 mA** → 3.327×0.195/0.88 = 0.737 W. **1V2** 150 mA (K5 estimate) → 0.180/0.80 = 0.225 W. **1V8** 100 mA (K10 assumption) → 0.180/0.82 = 0.220 W. Switch + PTC ≈ 0.05 W. **@4.4 V: 116.5 + 1.232 W/4.4 = 396 mA (1.74 W); ×1.25 = 496 mA < 500 mA. @5.0 V: 363 mA, 1.81 W. @5.25 V: 1.84 W < 2.25 W** → USB 2.0 budget holds; USB-C power trigger not fired (connector already USB-C). Typical (FT232H 82 mA, ADC typ): ≈ 1.6 W. The 1V8-by-LDO-from-3V3D alternative gives 433 mA ×1.25 = 541 mA > 500 → rejected. Margin now 1 % at the ×1.25 line: K5/K10 must be confirmed (Gowin GPA) before adding any load. |
| P2 | Unconfigured-device 100 mA rule | L | Board draws ≈ 200 mA (digital) + analog immediately at attach, before enumeration. Accepted (common for bus-powered FPGA tools). Gateware should hold ADC STPD=1 until the host opens the device (saves ≈ 240 mW ≈ 55 mA @4.4 V) — this is also the first lever if P1 is exceeded. EEPROM MaxPower = 500 mA. |
| P3 | GW1NR power sequencing <!-- revised: +1V8/VCCO3 --> | M | UG284: VCC and VCCO3 drive the internal POR; power-on time 0.2–2 ms; only if >2 ms must VCC precede VCCX/VCCIO. U4 (+1V2) and U12 (+1V8) both enabled by VBUS_SW, tSS 800 µs (DBV, K7 verified) → 0.8 ms each ✓. Ramps 1.50 mV/µs (VCC, 0.6–6 ✓), 2.25 mV/µs (VCCO3, 0.1–10 ✓). +3V3D (VCCX/VCCO0–2) EN-delayed 2.0–3.2 ms, ramp 4.16 mV/µs (0.6–10 ✓). VCCO3 present 1.2–2.4 ms before VCCX: UG284 sets no order between them for ≤2 ms ramps; no bank-3 pin is driven from a 3.3 V source, so no back-powering path. |
| P4 | Buck/charge-pump noise into AFE | M | TLV62569 1.5 MHz and LM27762 2 MHz switching. Bucks feed only digital; AFE rails are LDO outputs (LM27762 internal LDOs, TLV757P). Place U3/U4/U12/L1/L2/L3 on the far side of the FPGA from the AFE; LM27762 next to AFE but with its CP loop (C13, C14) tight. Both switch frequencies are inside the 0–20 MHz ADC band → keep PSRR path: ferrite optional between VBUS_SW and U5/U6 (footprint 0 Ω). |
| P5 | Analog LDO thermal | L | U5 dissipation (5.25 − 3.3) × 92.1 mA = 0.180 W; at θJA 231 °C/W (worst DBV figure in TLV757P table) rise 41.5 °C → Tj 112 °C @ 70 °C ambient < 125 °C. Use DRV (WSON) variant if layout allows. |
| P7 | +1V8 load (K10) <!-- revised: new --> | M | VCCO3 (pin 12) feeds bank 3 *and* (assumed) the in-package PSRAM. Budget 100 mA = 2 dies × 40 mA active (typ. 1.8 V 32 Mb OPI/HyperRAM at 166 MHz) + ≈11 mA bank-3 DDR drivers (24 lines × 3 pF × 1.8 V × 166 MHz × 0.5) + static. U12 is a 2 A part, so only P1 is sensitive. A single VCCO3 pin carrying 100 mA is within QFN bond limits. Confirm with GPA. |
| P6 | Charge-pump headroom at low VBUS | L | VBUS_SW ≥ 4.3 V → CP ≈ −4.3 V + I·ROUT (≈ 23 mA × few Ω) → ≈ −4.2 V; needs ≥ 3.416 + 0.03 V ✓. |

## Analog / signal integrity

| # | Risk | Sev | Working / mitigation |
|---|---|---|---|
| A1 | Divider compensation | M | Mismatch shows as a 7.8 kHz-corner tilt on square waves (corner = 1/(2π·90.1 kΩ·227.5 pF)). Trimmer C21/C41 covers 19.1–24.9 pF vs required 21.2–24.0 pF. Production step: adjust with 1 kHz square wave. |
| A2 | Leakage at the 90 kΩ node | L | 5 nA (BAV199 worst-case class) × 90.1 kΩ = 0.45 mV < 1 LSB at node (2.02 V/0.909/4096 = 0.54 mV). Guard ring around ATT_x on L1 tied to BUF_OUT_x is recommended; no solder-mask-free gaps. |
| A3 | ±50 V input survival | M | Steady state: 50.6 µA into clamp; R20 2.7 mW; C20/C21 rated 100 V; R20 1206 ≥ 150 V working. Fast 50 V edge couples 50 × 22.5/227.5 = 4.9 V onto ATT node, caught by BAV199. No TVS on the BNC (would load 1 MΩ and add leakage); IEC ESD on the BNC centre pin is **not** a design target. |
| A4 | Overload recovery | L | At overload FDA outputs rail at 0.15/3.15 V, outside the 0.5–2.5 V the ADC "handles" (DS: recovery in 3 clocks only within that window). ADC abs-max respected (outputs bounded by +3V3A/GND). Expect a few-sample recovery tail; flag ADC_OVRx in data. |
| A5 | AAF component tolerance | M | Butterworth-like response relies on C0G 12 pF/100 pF/270 pF and 1 % R; ±5 % C shifts f0 ≈ ±5 % (8.4–9.3 MHz) and Q by a few %; droop at 5 MHz stays < 0.3 dB. Do not substitute X7R. |
| A6 | Alias rejection is finite | M | −35.8 dB at 35 MHz (signal energy between 35–45 MHz folds into 0–5 MHz). Out-of-band 5–35 MHz is removed by the gateware FIR, which must have ≥ 70 dB stopband from 6 MHz. Documented spec: analog −3 dB 8.8 MHz; delivered passband 0–4 MHz (flat ±0.1 dB after FIR droop correction). |
| A7 | Channel gain/offset spread | L | ADC gain error ±3.5 %, offset ±0.75 % FS, resistor 1 % → per-channel calibration constants in host software. Worst FS still ±10.72 V > ±10 V. |
| A8 | Clock jitter vs ENOB <!-- revised: Y1 swapped --> | L | SNR_j = −20log(2π·5 MHz·tj). Budget tj ≤ 5.04 ps (SNR_j ≥ 76 dB). Y1 = YXC OT322540MJBA4SL, **0.7 ps rms max (12 kHz–20 MHz), published** → 93.2 dB; combined with ADC 70.7 dB → 70.68 dB (ENOB 11.45; ADS5231 aperture jitter 1.0 ps is inside its own SNR spec). Broadband noise above 20 MHz is not in the 12 k–20 MHz figure; even 5× it (3.5 ps) still gives 79 dB. Do not route ADC_CLK through the FPGA PLL. |

## Timing / digital

| # | Risk | Sev | Working / mitigation |
|---|---|---|---|
| T1 | PSRAM bandwidth | M | Need 2 ch × 10 MSPS × 2 B = 40 MB/s. In-package PSRAM ×16 DDR at ≈ 82 MHz = 330 MB/s peak; ≥ 30 % efficiency (refresh, CS-low limit, latency) still 99 MB/s ✓. Raw 40 MSPS storage (160 MB/s) is *not* guaranteed. Gowin PSRAM IP clock limit = K3. |
| T2 | Capture depth | — | 8 MiB = 8 388 608 B / (2 ch × 2 B × 10 MSPS) = **0.2097 s** ≥ 0.1 s ✓ (2.10× margin). |
| T3 | Decimation FIR resources | L | 64-tap 4:1 polyphase = 16 MAC/output/ch × 10 MSPS × 2 ch = 320 M MAC/s → 4 multipliers at 80 MHz (20 available). |
| T4 | ADC → FPGA capture without DV <!-- revised: DVA/DVB dropped --> | M | ADS5231 @40 MSPS: tDV 13.5–18.5 ns, t1 ≥ 3.7 ns, t2 ≥ 11.5 ns → data stable 14.8–25.0 ns after CLK↑ = 10.2 ns window. FPGA_CLK40 lags ADC_CLK by U8 tpd (spread ≈ 3.2 ns @3.3 V, assumed) + trace; FPGA tSU+tH ≈ 2 ns (assumed) → ≈ 5 ns margin. FPGA_CLK40 enters RPLL_T_in (pin 63) so the right PLL can phase-shift the capture clock ≈ +20 ns; calibrate once at bring-up using the ADS5231 serial-mode test pattern (SEL/SEN/SCLK/SDATA kept for this). Keep ADC_DA/DB traces within ±10 mm. |
| T5 | FT245 sync-FIFO timing | M | 60 MHz CLKOUT from FT232H; FT_* traces ≤ 50 mm, CLKOUT to a GCLK pin. Throughput ≈ 30–40 MB/s → 4 MB readout ≈ 0.1–0.13 s. EEPROM must be programmed to 245-FIFO mode (FT_Prog) before first use — bring-up step. |
| T7 | FPGA I/O fully allocated <!-- revised: new --> | M | 48 of 48 3.3 V-capable I/O used (bank 1 25, bank 2 23). Removed to fit: ADC DVA/DVB, OVRA/OVRB (over-range = saturated codes 0x000/0xFFF in gateware), FT SIWU# (tied high; short packets flush on the latency timer). Reserve: tie ADC_OEB to GND frees 1 pin. Bank 3 (1.8 V) has 15 free I/O for debug. Any new 3.3 V signal requires an architecture change. |
| T6 | Clock-domain crossings | L | 40 MHz (ADC), 60 MHz (FT), PSRAM PLL clock — gateware uses async FIFOs; not a hardware issue. |

## Layout / EMI / mechanical

| # | Risk | Sev | Mitigation |
|---|---|---|---|
| L1 | Ground strategy | M | 4-layer: L1 signal, L2 solid GND, L3 power, L4 signal. Single GND net, no split; AFE + ADC analog half on one side of U7, FPGA/USB/bucks on the other; ADC straddles the boundary per TI guidance. |
| L2 | FPGA QFN-88 0.4 mm + EP | M | JLC capability OK (0.4 mm QFN); needs via-in-pad or EP vias; 0.1 mm/0.1 mm trace/space under escape → confirm JLC 4-layer rules at layout. |
| L3 | USB HS pair | M | 90 Ω differential, ≤ 50 mm, no stubs; USBLC6 at the connector; both USB-C D+/D− pin pairs joined at the connector. |
| L4 | BNC mechanical | L | THT right-angle BNC, 2 per board edge, ≥ 20 mm pitch; JLC THT assembly (selective/hand) adds cost. |
| L6 | JTAG at 1.8 V <!-- revised: new --> | M | JTAG pins are on bank 3 (VCCO3 = 1.8 V). J4 pin 1 = +1V8 VREF. A 3.3 V-only programmer (e.g. many FT2232 Sipeed/clone cables) would overdrive bank 3 — use a VREF-tracking cable (Gowin GWU2X supports 1.2–3.3 V). TCK pulled down 4.7 kΩ (R81, UG284 Fig. 2). |
| L5 | Radiated emissions | L | No certification target; 60 MHz CLKOUT and 40 MHz clock series-terminated (R70, R71); keep clocks on inner-adjacent L1 over solid L2. |

## Sourcing / lifecycle

| # | Risk | Sev | Mitigation |
|---|---|---|---|
| S1 | ADS5231 single-source, stock 235 | H | DigiKey lifecycle Active. Fallback = 2× AD9235BCPZ-40 (not drop-in — needs architecture revision of adc_dual). Buy at sourcing time. |
| S2 | GW1NR-LV9QN88P stock 182, single-source | H | Only FPGA with in-package PSRAM in stock; fallback = XC6SLX9-2TQG144C + W9825G6KH-6 (re-architecture). |
| S3 | FT232H single-source | M | 2353 stock; fallback CY7C68013A requires redesign + firmware. |
| S4 | Extended-tier everywhere | L | No Basic/Preferred equivalents exist for ADC/FPGA/bridge/AFE ICs; accepted for prototype. |
