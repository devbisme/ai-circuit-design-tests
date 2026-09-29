# Block diagram — dual_adc_usb

Dual-channel 12-bit digitizer. **Buffered capture**: burst into the FPGA's in-package
PSRAM, then read out over USB 2.0 HS. 8 functional blocks, 9 instances
(`afe_channel` is instantiated twice).

```mermaid
flowchart LR
  subgraph FE["Analog front end (x2)"]
    BNC1["BNC J2<br/>CH1"] --> DIV1["1 MΩ ÷20<br/>compensated<br/>950k / 50k<br/>+ 5 pF trimmer"]
    DIV1 --> CL1["1k + BAV99<br/>clamp"]
    CL1 --> BUF1["OPA355<br/>unity buffer"]
    BUF1 --> FDA1["THS4551 FDA<br/>G=2, 2nd-order MFB<br/>+ output RC =<br/>3rd-ord Butterworth 6.1 MHz"]
    BNC2["BNC J3<br/>CH2"] --> DIV2["1 MΩ ÷20<br/>compensated"]
    DIV2 --> CL2["1k + BAV99<br/>clamp"] --> BUF2["OPA355"] --> FDA2["THS4551 FDA"]
  end

  subgraph DIG["Capture + host interface"]
    ADC["ADS5231<br/>dual 12-bit<br/>20 MSPS/ch<br/>simultaneous"]
    FPGA["GW1NR-9C FPGA<br/>capture engine<br/>+ 8 MB in-package PSRAM"]
    USB["FT232HL<br/>245 sync FIFO<br/>USB 2.0 HS"]
    JC["USB-C 16P J1<br/>5.1k CC pulldowns"]
  end

  FDA1 -->|CH1_P/N| ADC
  FDA2 -->|CH2_P/N| ADC
  ADC -->|"ADC_D1[11:0]<br/>ADC_D2[11:0]<br/>33Ω damped"| FPGA
  FPGA <-->|"FIFO_D[7:0]<br/>+ handshake"| USB
  USB <-->|USB_DP/DM| JC
  JC -->|VBUS| PWR

  XO["X1 20.000 MHz XO<br/>≤5 ps RMS<br/>on clean +3V3_A"]
  XO -->|ADC_CLK| ADC
  XO -->|FPGA_CLK| FPGA

  subgraph PWR["Power tree"]
    SW["U9 AP2161W load switch<br/>active-low EN = PWREN#<br/>1.5 A limit, 0.6 ms slew"]
    BUCK["SY8089A1AAC<br/>5V→3.3V buck"]
    LDO12["1.2 V LDO<br/>FPGA core"]
    LDOA["TLV75733 LDO<br/>5V→+3V3_A"]
    REF["VBIAS 1.10 V<br/>VREF_FE 1.045 V<br/>dual buffer"]
  end

  SW --> BUCK --> LDO12
  BUCK -->|"+3V3_D"| FPGA
  BUCK -->|"FB2 → +3V3_ADCD"| ADC
  LDO12 -->|"+1V2_D"| FPGA
  SW --> LDOA
  LDOA -->|"+3V3_A"| FE
  LDOA --> ADC
  LDOA --> XO
  LDOA --> REF
  REF -->|VBIAS / VREF_FE| FE
  ADC -->|"VOCM (CM pin)"| FE
  USB -->|PWREN#| SW

  JTAG["J4 JTAG 6-pin"] <--> FPGA
  TRIG["J5 trigger in"] --> FPGA
  FPGA --> LED["D5 capture LED"]
```

## Signal flow, in words

1. **±10 V at the BNC** is divided by 20 **passively** into a 1.20 V bias (not ground), so
   the whole active chain lives on a single +3.3 V rail — no negative rail, no boost.
   Node swing = **1.045 V ± 0.5 V** (rev 3: `VBIAS` 1.200 V → 1.100 V, ERC M-1).
2. A **unity-gain FET-input buffer** presents a high, stable impedance to the divider's
   47.5 kΩ output node; its input capacitance is absorbed into the divider's compensation.
3. A **fully differential amplifier at G = 2** subtracts `VREF_FE` (1.045 V), restores the
   2 V p-p differential full scale, sets the common mode from the ADC's own CM pin, and
   carries the anti-alias filter in its **multiple-feedback (MFB)** network plus one output RC
   — a **3rd-order Butterworth, −3 dB at 6.1 MHz** (rev 3; the rev-1/2 network was
   accidentally 2nd-order, ERC H-1). The MFB is what provides the *complex* pole pair; a
   cascade of plain RC sections cannot give a flat passband and a useful stopband at once.
4. One **dual ADC** samples both channels on the **same clock edge** from one oscillator —
   that single shared edge is what makes the channels simultaneous (requirement F1/D10).
5. The **FPGA** latches 24 parallel data bits at 20 MHz, writes them to its **in-package
   8 MB PSRAM** (104.9 ms of both channels at 20 MSPS), then streams the record out through
   the FT232H's synchronous FIFO.
6. The **host** decimates 2:1 to the required 10.0 MSPS/ch with a digital filter — which is
   also the final anti-alias stage, and is **mandatory, not optional**: it is what suppresses
   the 5–10 MHz octave the analog filter deliberately passes (requirement **S1**, risk
   **R-12**). No FPGA DSP is required to meet any HARD requirement.

<!-- revised: rev3 — FDA block label and signal-chain steps 1/3/6: ERC H-1 (3rd-order MFB
     Butterworth), M-1 (VBIAS 1.100 V), new requirement S1 (host decimation filter). -->

## Clock domains

| Domain | Source | Contents | Crossing |
|---|---|---|---|
| Sample, 20.000 MHz | X1 XO direct | ADC, FPGA input registers | none — ADC and FPGA share the XO, source-synchronous |
| Memory, ~120 MHz | FPGA PLL from `FPGA_CLK` | PSRAM controller | synchronous to sample domain (same PLL root) → rate FIFO only |
| USB FIFO, 60.000 MHz | `FIFO_CLK` from FT232H (own 12 MHz crystal) | FIFO master | **the only true asynchronous boundary** — needs a dual-clock async FIFO in the FPGA |

The ADC clock never passes through the FPGA (requirement F14/D10): `ADC_CLK` goes from X1
straight to the ADC, and a separate series-damped copy goes to the FPGA.
