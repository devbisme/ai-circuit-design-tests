# Block diagram — dual_adc_usb

Burst digitizer: 2 ch × 12 bit × 10 MSPS simultaneous → 8 MB in-FPGA PSRAM → USB 2.0 HS read-out.
Bus-powered from USB-C, everything except the USB bridge gated behind a load switch until
enumeration completes.

```mermaid
flowchart LR
  subgraph AFE["Analog front end (×2 channels)"]
    J1["BNC J1/J2<br/>scope probe"] --> DIV["afe_input<br/>1 MΩ ÷11 compensated divider<br/>909k/90.9k + 15p/145p<br/>±55 V clamp"]
    DIV --> BUF["afe_buffer<br/>AD8066 ×1/2 unity buffer<br/>JFET, 6 pA, ±5 V rails"]
    BUF --> FDA["afe_driver<br/>THS4521 FDA, G=1.1<br/>SE→diff, VOCM=1.5 V"]
    FDA --> LPF["5-pole LC anti-alias<br/>per leg: 100Ω-3.3µH-680p-5.6µH-680p<br/>−3 dB 4.247 MHz, −41.3 dB @10 MHz"]
  end

  LPF --> ADC["adc_dual<br/>ADS5231 TQFP-64<br/>dual 12-bit, simultaneous<br/>+3.3 V, PLL disabled @10 MSPS<br/>2 Vpp diff, VCM 1.5 V"]

  XO["clock_gen<br/>10.000 MHz CMOS XO<br/>±30 ppm, ~1 ps RMS"] -->|CLK10| ADC
  XO -->|CLK10| FPGA

  ADC -->|"ADC_DA[11:0], ADC_DB[11:0]<br/>DVA — 25 lines (OVRA/B retired rev.3)"| FPGA
  FPGA -->|"SEL/SEN/SCLK/SDATA (disable PLL) — SEL dynamic"| ADC

  subgraph DIG["Digital core"]
    FPGA["fpga_core<br/>GW1NR-LV9QN88PC6<br/>8640 LUT, 468 kb BSRAM<br/>+ 64 Mbit (8 MB) in-package PSRAM<br/>+ 4 Mbit embedded config Flash (AUTOBOOT)"]
    FPGA <-->|"x8 DDR, internal — 0 board pins"| PSRAM[("embedded PSRAM<br/>8 MB @ ≥100 MB/s")]
  end

  FPGA <-->|"FIFO_D[7:0] + RXF#/TXE#/RD#/WR#/OE#/SIWU#<br/>FIFO_CLK60 (60 MHz, FT is clock master)"| FT["usb_bridge<br/>FT232HL, 245 sync FIFO<br/>USB 2.0 HS PHY on chip"]
  FT <-->|"D+/D−"| UC["USB-C 16P receptacle<br/>CC1/CC2 5.1 kΩ, no PD<br/>USBLC6-2SC6 ESD"]
  FT -->|"PWREN# (ACBUS9)"| PWR

  %% revised: rev.2 — added the 1.8 V LDO feeding U5 VCCIO3 (the embedded-PSRAM bank)
  subgraph PWR["power_tree"]
    LS["TPS22918 load switch<br/>+ BSS138 inverter<br/>EN after enumeration"]
    B1["TLV62569 buck → 3.3 VD"]
    B2["TLV62569 buck → 1.2 V core"]
    LDO["RT9013-33 LDO → 3.3 VA"]
    LDO18["AP2127K-1.8 LDO → 1.8 V<br/>U5 VCCIO3 = PSRAM bank"]
    CP["TPS60403 inverter → −5 VA"]
    FBD["ferrite → +5 VA"]
  end

  UC -->|"VBUS 5 V"| FT
  UC -->|VBUS| LS
  LS -->|VBUS_SW| B1 & B2 & LDO & FBD
  FBD --> CP
  B1 -.->|3.3 VD| FPGA & ADC & XO & FT
  B1 --> LDO18
  LDO18 -.->|"1.8 V → VCCIO3 (pin 12)"| FPGA
  B2 -.->|1.2 V| FPGA
  LDO -.->|3.3 VA| ADC & FDA
  FBD -.->|+5 VA| BUF
  CP -.->|−5 VA| BUF
```

## Signal flow, stage by stage

| # | Stage | In | Out | Why it is there |
|---|---|---|---|---|
| 1 | BNC + compensated divider | ±10 V (±55 V survivable) | ±0.909 V, Z = 1 MΩ ∥ 17.6 pF | Scope-probe-compatible load; the caps carry the signal above 12 kHz so bandwidth is not limited by 909 kΩ |
| 2 | Unity buffer (AD8066, ±5 V) | 82.6 kΩ source | low-Z ±0.909 V | JFET input (6 pA) — a bipolar input would put ~100 mV of offset across 82.6 kΩ |
| 3 | FDA (THS4521, +3.3 VA) | single-ended ±0.909 V | differential 2 Vpp on 1.5 V CM | ADS5231 needs 1.0–2.0 V per pin; single-ended drive cannot reach full scale legally |
| 4 | LC anti-alias, per leg | 2 Vpp diff | band-limited | 4 passive poles (L1,C1,L2,C2 on **two distinct nodes split by L2** — no shared-node collapse) + 1 FDA feedback pole. Recomputed rev.3 from the shipped values: **−3 dB 4.247 MHz, −0.68 dB at 4 MHz, −41.3 dB at 10 MHz** — SPEC F8 (≥3 dB BW 4 MHz, ≥40 dB at 10 MHz) met |
| 5 | ADS5231 | 2 Vpp diff, 10 MSPS | 2 × 12-bit parallel | One package ⇒ channel skew is internal, not a board problem |
| 6 | GW1NR-9 | 24-bit @10 MHz = 40 MB/s | PSRAM burst writes | 8 MB in package: no memory bus on the PCB at all |
| 7 | FT232H sync FIFO | PSRAM read-back | USB 2.0 HS bulk | ≥20 MB/s required, 30–40 MB/s practical |

## Capture / read-out sequence

1. Host opens the FT232H; PWREN# falls; TPS22918 turns on the rest of the board.
2. FPGA AUTOBOOTs from its 4 Mbit on-die configuration Flash (MODE[2:0]=000, DS117 §2.12.2 "instant on" — no dongle, no SPI flash, R-13 closed), then disables the ADC PLL over SEL/SEN/SCLK/SDATA (required below 20 MSPS).
3. Host writes a "capture" command through the FIFO. FPGA streams 24 bits/10 MHz through a BSRAM
   elastic FIFO into PSRAM until 1,000,000 samples/channel are stored (0.1 s).
4. Host reads 4,000,000 bytes back through the sync FIFO at 30–40 MB/s (~0.12 s).
