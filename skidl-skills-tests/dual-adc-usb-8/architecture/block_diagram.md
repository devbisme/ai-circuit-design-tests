# Block diagram — dual_adc_usb (revision 1)

Two-channel, simultaneous, 12-bit digitizer. Each ±10 V BNC input goes through a 1 MΩ compensated
÷10.09 attenuator, a CMOS unity-gain buffer and an FDA (2-pole MFB filter) into one dual 12-bit ADC. The ADC
**oversamples at 40 MSa/s**. The FPGA decimates ×4 to 10 MSa/s per channel, stores the result in the
8 MB PSRAM inside the FPGA package, and uploads it through an FT232H USB 2.0 HS sync FIFO.

```mermaid
flowchart LR
  subgraph PWR_IN[usb_power_in]
    J1[USB-C receptacle<br/>USB2.0 data, Rd=5.1k] --> ESD[USBLC6-2SC6]
    J1 --> LS[TPS22919 load switch<br/>soft-start, inrush limit]
  end
  LS -- V5 --> PD
  LS -- V5 --> PA
  subgraph PD[power_digital]
    B33[TLV62569 buck → V3V3D]
    B12[TLV62569 buck → V1V2]
    L18[TLV75518P LDO → V1V8]
    B33 --> L18
  end
  subgraph PA[power_analog]
    LA[TPS7A2033 LDO → V3V3A]
    CP[LM27762 → VP_AFE +3.29 V / VN_AFE −2.01 V]
  end
  subgraph AFEA[afe_ch_a]
    BNC1[BNC J2] --> DIV1[909k/100k compensated divider<br/>Ct 22p / Cb 165p + trim] --> CL1[BAV199 clamp] --> RS1[1k + 8.2p] --> BUF1[OPA356 buffer] --> FDA1[THS4551 MFB 2-pole<br/>G=0.909] --> RC1[49.9Ω + 56p]
  end
  subgraph AFEB[afe_ch_b]
    BNC2[BNC J3] --> DIV2[same as ch A] --> FDA2[OPA356 → THS4551 → RC]
  end
  subgraph CLK[clock]
    XO[40.000 MHz CMOS XO] --> RC_A[33Ω → ADC_CLK]
    XO --> RC_F[33Ω → FPGA_CLK]
  end
  subgraph ADCB[adc]
    ADC[ADS5231 dual 12-bit 40 MSa/s<br/>parallel CMOS 3.3 V]
  end
  subgraph FPGAB[fpga]
    FPGA[GW1NR-LV9QN88P<br/>decimate ×4, trigger,<br/>2×32 Mbit PSRAM in package]
    JTAG[JTAG hdr 1.8 V]
    AUX[aux hdr TRIG_IN/OUT]
  end
  subgraph USBB[usb_bridge]
    FT[FT232HL sync-245 FIFO<br/>12 MHz xtal, 93LC56 EEPROM]
  end
  RC1 -- AIN_A_P/N --> ADC
  FDA2 -- AIN_B_P/N --> ADC
  ADC -- VCM 1.5 V --> FDA1
  ADC -- VCM --> FDA2
  RC_A -- ADC_CLK --> ADC
  RC_F -- FPGA_CLK --> FPGA
  ADC -- DA[11:0], DB[11:0], ADC_DVA --> FPGA
  FPGA -- ADC_STPD --> ADC
  FPGA <-- FT_D[7:0] + 7 ctrl, FT_CLKOUT 60 MHz --> FT
  FT <-- USB_DP/USB_DN --> J1
  PA -- V3V3A --> ADCB
  PA -- V3V3A, VP_AFE, VN_AFE --> AFEA
  PA -- V3V3A, VP_AFE, VN_AFE --> AFEB
  PA -- V3V3A --> CLK
  PD -- V3V3D, V1V2, V1V8 --> FPGAB
  PD -- V3V3D --> USBB
```

## Signal flow and rates
| Stage | Rate / level | Working |
|---|---|---|
| BNC → divider node | ×0.09911 | 100k/(909k+100k) → 0.09911 |
| Buffer (OPA356, G=+1) | ±1.111 V max at ±11.21 V in | 11.21 × 0.09911 → 1.111 V |
| FDA MFB | diff gain 0.909 | R2/R1 = 909/1000 → 0.909 |
| ADC input | 2.02 Vpp diff FS; CM = VCM 1.5 V | 0.09911 × 0.909 → 0.09009 V/V; 1.01/0.09009 → FS ±11.21 V |
| ADC output | 2 × 12 bit @ 40 MSa/s parallel | 24 data lines + DVA |
| FPGA decimator | 40 → 10 MSa/s per channel | ÷4 |
| PSRAM store | 40 MB/s (16-bit words) | 10e6 × 2 ch × 2 B → 40 MB/s |
| USB upload | ≈35 MB/s (FT232H sync FIFO) | 4 MB / 35 MB/s → 0.114 s |

## Ground and domains
One unbroken GND plane (net `GND`); analog parts are placed over their own region and never share
return paths with the FT232H/FPGA. There is no split AGND net. Rails: V5 (switched VBUS),
V3V3D, V1V2, V1V8 (digital); V3V3A, VP_AFE, VN_AFE (analog).
