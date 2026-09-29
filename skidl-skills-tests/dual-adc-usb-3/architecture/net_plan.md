# Net plan — dual_adc_usb

The coders' contract. Net names here are used **verbatim** in the SKiDL block files and in
the `## Block manifest` interface lists. Ref designators are indicative: SKiDL auto-numbers,
but every block must connect the nets named here.

**Ground:** one net, `GND`. The analog/digital plane split and its single tie point under
the ADCs is a *layout* instruction (see `design_risks.md` R12), not a netlist one. Do not
create `AGND` — it would only produce a floating-net ERC error.

## Power nets

| net | type | nominal | source | connected refs (function) |
|---|---|---|---|---|
| `VBUS` | power | +5 V (4.4–5.25) | USB-C VBUS | J1 A4/A9/B4/B9, D2 TVS, FB1, C1/C2, U1 IN, U2 IN, FB2→U5 IN, TP1 |
| `+3V3_AON` | power | +3.3 V | U1 AP2112K-3.3 (always on) | U1 OUT, U13 FX2LP VCC/AVCC(via FB5), U14 EEPROM VCC, R37/R38 I2C pullups, D5 PWR LED, TP15 |
| `+3V3` | power | +3.3 V | U2 TLV62569 buck, EN=`PWR_EN` | U2 OUT, U3 IN, U4 IN, FB4, U12 VCCX + 3.3 V bank VCCIO, Y1 VDD, U11 VCC, D6 CAP LED, J4 pin1, TP2 |
| `+3V3_DRV` | power | +3.3 V | FB4 ferrite off `+3V3` | U9 DRVDD, U10 DRVDD, local 0.1 µF each |
| `+1V2` | power | +1.2 V | U3 TLV62568 buck | U3 OUT, U12 VCC (FPGA core), TP3 |
| `+1V8` | power | +1.8 V | U4 LP5907-1.8 | U4 OUT, U12 PSRAM-bank VCCIO pins, TP4 |
| `+4V2A` | power | +4.2 V | U5 LM27762 VOUT+ | U5 VOUT+, U6 IN, U7/U7' AD8066 V+, U8/U8' THS4551 VS+, D3 clamp anode side, TP6 |
| `-4V2A` | power | −4.2 V | U5 LM27762 VOUT− | U5 VOUT−, U7/U7' AD8066 V−, U8/U8' THS4551 VS−, D3 clamp cathode side, TP7 |
| `+3V0A` | power | +3.0 V | U6 LP5907-3.0 | U6 OUT, U9 AVDD, U10 AVDD, R28 VCM divider top, TP8 |
| `GND` | power | 0 V | USB-C GND | every block |

## Analog signal nets (`analog_frontend`, one set per instance — CH1 / CH2)

| net | type | connected refs (function) |
|---|---|---|
| `CH1_IN` / `CH2_IN` | analog | J2 BNC centre, R13 (909 k top leg), C34 (15 pF comp cap) |
| `CH1_TAP` / `CH2_TAP` | analog | R13 bottom, R14 (90.9 k), C34, C35 (150 pF, or 120 pF + CT1 trimmer), R15 (1 k series) |
| `CH1_BUFIN` / `CH2_BUFIN` | analog | R15, D3 BAV199 common pin (clamp to ±4V2A), U7A +IN |
| `CH1_BUF` / `CH2_BUF` | analog | U7A OUT, U7A −IN (unity feedback), R16 (SK first R) |
| `CH1_SKMID` / `CH2_SKMID` | analog | R16, R17, C37 (47 pF to GND) |
| `CH1_SK` / `CH2_SK` | analog | U7B OUT, U7B −IN, C36 (330 pF feedback to `CH1_SKMID`), R18 (FDA Rg) |
| `CH1_MFB_P` / `CH2_MFB_P` | analog | R18, R20 (Rf 1.10 k), R22 (R3 1.00 k), C39 (62 pF across Rf), C41 (11 pF diff) |
| `CH1_MFB_N` / `CH2_MFB_N` | analog | R19 (Rg 1.00 k to GND ref), R21 (Rf 1.10 k), R23 (R3 1.00 k), C40 (62 pF), C41 (11 pF diff) |
| `CH1_ADC_P` / `CH2_ADC_P` | analog | U8 OUT+, R24 (33 Ω) → `CH1_ADCIN_P`, C39, R20 |
| `CH1_ADC_N` / `CH2_ADC_N` | analog | U8 OUT−, R25 (33 Ω) → `CH1_ADCIN_N`, C40, R21 |
| `CH1_ADCIN_P` / `CH2_ADCIN_P` | analog | U9 VIN+, C42 (22 pF differential), TP10 |
| `CH1_ADCIN_N` / `CH2_ADCIN_N` | analog | U9 VIN−, C42, TP11 |
| `VCM` | analog bias | R28/R29 divider off `+3V0A` (10 k/10 k), C58 1 µF + C59 0.1 µF, U8 VOCM (both instances) — 1.50 V |

## ADC nets (`adc_pair`)

| net | type | connected refs |
|---|---|---|
| `ADC1_D0` … `ADC1_D11` | digital out (`Bus` `ADC1_D`) | U9 D0–D11 → U12 FPGA |
| `ADC2_D0` … `ADC2_D11` | digital out (`Bus` `ADC2_D`) | U10 D0–D11 → U12 FPGA |
| `ADC1_OTR`, `ADC2_OTR` | digital out | U9/U10 OTR → U12 (droppable — see R1) |
| `CLK_ADC1`, `CLK_ADC2` | clock | U11 Y1/Y2 outputs (via R33/R34 33 Ω) → U9/U10 CLK |
| `ADC_REFT1`,`ADC_REFB1`,`ADC_REFT2`,`ADC_REFB2` | analog local | U9/U10 REFT/REFB — 0.1 µF each to GND and 10 µF differential across the pair |
| `ADC1_VREF`, `ADC2_VREF` | analog local | U9/U10 VREF, 0.1 µF to GND. SENSE strapped to GND → internal 1.0 V ref, 2 Vpp span |

Mode straps in `adc_pair`, no net needed: `SENSE`→GND, `PDWN`→GND, `OEB`→GND,
`DFS`→GND (offset binary; the FPGA converts).

## Clock nets (`clock_gen`)

| net | type | connected refs |
|---|---|---|
| `CLK_XO` | clock | Y1 OUT → U11 1A, U11 2A |
| `CLK_ADC1` | clock | U11 1Y → R33 33 Ω → U9 CLK |
| `CLK_ADC2` | clock | U11 2Y → R34 33 Ω → U10 CLK |
| `CLK_FPGA` | clock | Y1 OUT → R32 33 Ω → U12 dedicated clock input |

## FPGA ↔ FX2LP slave-FIFO nets

| net | type | connected refs |
|---|---|---|
| `FD0` … `FD7` | bidirectional (`Bus` `FD`) | U13 PB0–PB7 ↔ U12 |
| `IFCLK` | clock | U12 → U13 IFCLK (FPGA sources 48 MHz from its PLL) |
| `SLWR_N` | digital out (FPGA) | U12 → U13 PA1/SLWR |
| `SLRD_N` | digital out (FPGA) | U12 → U13 RDY0/SLRD |
| `SLOE_N` | digital out (FPGA) | U12 → U13 PA2/SLOE |
| `FIFOADR0`, `FIFOADR1` | digital out (FPGA) | U12 → U13 PA4/PA5 |
| `FLAGA`, `FLAGB`, `FLAGC` | digital out (FX2LP) | U13 CTL0/CTL1/CTL2 → U12 |
| `PKTEND_N` | digital out (FPGA) | U12 → U13 PA6 |
| `PWR_EN` | digital out (FX2LP) | U13 PA0 → R6 100 k pulldown, U2 EN, U3 EN, U4 EN, U5 EN |
| `FPGA_RST_N` | digital out (FX2LP) | U13 PA3 → U12 RECONFIG_N (also R35 10 k pullup to `+3V3`) |

## USB / config / aux nets

| net | type | connected refs |
|---|---|---|
| `USB_DP`, `USB_DM` | USB HS diff pair | J1 A6/B6, A7/B7 → D1 USBLC6 → U13 D+/D−. **No series resistors, no external 1.5 k pull-up** — FX2LP integrates both |
| `CC1`, `CC2` | analog | J1 A5, B5 → R1, R2 5.1 kΩ to GND |
| `SCL`, `SDA` | I2C | U13 SCL/SDA ↔ U14 EEPROM, R37/R38 2.2 k to `+3V3_AON` |
| `XTAL_IN`, `XTAL_OUT` | crystal | U13 XTALIN/XTALOUT ↔ Y2 24 MHz, C-load 12 pF each to GND |
| `FX2_RST_N` | reset | U13 RESET#, R39 100 k to `+3V3_AON`, C 1 µF to GND |
| `TCK`, `TMS`, `TDI`, `TDO` | JTAG | U12 dedicated JTAG pins ↔ J3 header; R36 10 k pullup on `TMS` |
| `TRIG_IO` | digital bidir 3V3 | J4 pin 2 → R43 100 Ω → D4 ESD → U12 |
| `LED_CAP_N` | digital out | U12 → R45 1 k → D6 |
| `LED_PWR` | power indicator | `+3V3_AON` → R46 1 k → D5 → GND |

## Bus declarations for the coder

```python
ADC1_D = Bus('ADC1_D', 12)
ADC2_D = Bus('ADC2_D', 12)
FD     = Bus('FD', 8)
FIFOADR = Bus('FIFOADR', 2)
```

`ADC1_D[0]` is the LSB. Both ADCs are strapped for offset binary (`DFS`→GND); the FPGA
converts to two's complement before packing.

## Signal-level budget (why the values are what they are)

| point | full-scale level | note |
|---|---|---|
| BNC, 1× lead | ±10.0 V | F2 |
| divider tap | ±0.909 V | ÷11 exactly: (909 k + 90.9 k)/90.9 k |
| buffer / SK out | ±0.909 V | unity gain through both |
| FDA differential out | ±1.000 V (2.0 Vpp) | gain 1.10 = 1.10 k / 1.00 k |
| ADC input span | 2.0 Vpp differential @ 1.50 V CM | AD9235 internal 1.0 V ref, SENSE→GND |

Input network: 909 k ∥ 15 pF over 90.9 k ∥ 150 pF. Compensated when R_top·C_top =
R_bot·C_bot. Capacitance presented at the BNC = 15·150/165 ≈ 13.6 pF plus ~4 pF connector
and trace stray ≈ **18 pF**, inside the 10–35 pF a standard passive probe compensates for,
and inside the ≤25 pF of requirement I4.

Anti-alias filter, 4th-order Butterworth, fc ≈ 3.9 MHz, split across two stages:

| stage | topology | values | f0 | Q |
|---|---|---|---|---|
| SK (AD8066 B) | Sallen–Key, unity gain | R16=R17=324 Ω, C36=330 pF (fb), C37=47 pF (gnd) | 3.95 MHz | 1.33 |
| MFB (THS4551) | differential multiple-feedback | Rg=1.00 k, Rf=1.10 k, R3=1.00 k, C_diff=11 pF, Cf=68 pF | 3.92 MHz | 0.58 |

Resulting stopband: **32.7 dB at 10 MHz** (≥30 required) and **56.8 dB at 20 MHz**
(≥50 required). Margin is thin at 10 MHz — see `design_risks.md` R4.
