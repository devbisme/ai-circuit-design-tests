# Architecture — block diagram (dual_adc_usb)

Burst-capture digitiser: 2 ch x 10.000 MSa/s x 12 bit -> 32 MB SDRAM -> USB 2.0 HS bulk drain.
Topology (b) from the requirements: **two single-channel ADCs sharing one sample clock**.
See `ic_selection.md` for why, `net_plan.md` for the wiring contract.

```mermaid
flowchart LR
  subgraph AFE1["analog_frontend #1 (CH1)"]
    B1[BNC J2<br/>KH-BNC50-3511] --> A1["÷11 compensated attenuator<br/>909k/90.9k + 22p/220p<br/>1 MΩ ∥ 20 pF<br/>bottom leg -> VREF_OFF 1.807 V"]
    A1 --> P1["1 kΩ + BAV199 clamp<br/>to +3V3A_AMP / GND"]
    P1 --> U1["U100 follower<br/>TPH2501 (CMOS, 0.3 pA)"]
    U1 --> S1["U101 Sallen-Key A<br/>f0 4.44 MHz, Q 0.554"]
    S1 --> S2["U102 Sallen-Key B<br/>f0 4.45 MHz, Q 1.304"]
    S2 --> F1["U103 THS4521 FDA<br/>G=1.1, VOCM=1.65 V<br/>single-ended -> differential"]
  end
  subgraph AFE2["analog_frontend #2 (CH2) — identical instance"]
    B2[BNC J3] --> F2["... U203 THS4521"]
  end

  F1 --> R1["33 Ω / 22 pF<br/>kickback filter"] --> ADC1["adc_channel #1<br/>U150 AD9237BCPZ-40<br/>12 bit, 2 Vpp diff"]
  F2 --> R2["33 Ω / 22 pF"] --> ADC2["adc_channel #2<br/>U250 AD9237BCPZ-40"]

  subgraph CLK["clocking"]
    X1["X1 10.000 MHz XO<br/>≤5 ps RMS jitter<br/>NOT an FPGA PLL output"]
    X1 --> RT["33 Ω series"] --> CLKADC(("CLK_ADC"))
    X1 --> BUF["U8 74LVC1G17<br/>isolation buffer"] --> CLKF(("CLK_FPGA"))
  end
  CLKADC --> ADC1
  CLKADC --> ADC2

  ADC1 -->|"ADC1_D[11:0] + OTR"| FPGA
  ADC2 -->|"ADC2_D[11:0] + OTR"| FPGA
  CLKF --> FPGA

  FPGA["fpga_core<br/>U30 XC6SLX9-2TQG144C<br/>capture FSM + SDRAM ctrl<br/>+ slave-FIFO master<br/>U31 W25Q32 config flash"]
  FPGA <-->|"SDR_DQ[15:0], SDR_A[12:0], ctrl<br/>100 MHz, 200 MB/s raw"| MEM["buffer_memory<br/>U40 W9825G6KH-6<br/>32 MB SDRAM<br/>= 0.84 s @ 10 MSa/s"]
  FPGA -->|"FIFO_D[7:0] @48 MHz<br/>= 48 MB/s"| USB["usb_bridge<br/>U50 CY7C68013A-56LTX<br/>slave FIFO, 8-bit<br/>U51 EEPROM, Y1 24 MHz"]
  USB <-->|"USB_DP / USB_DM"| J1

  subgraph PWR["power"]
    J1["usb_front<br/>J1 USB-C 16P<br/>5.1k CC1/CC2<br/>U1 USBLC6-2SC6<br/>U2 TPS22919 soft-start"] --> SW(("VBUS_SW"))
    SW --> BK1["U3 SY8089AAC buck<br/>3.318 V @ 225 mA"]
    SW --> BK2["U4 SY8089AAC buck<br/>1.200 V @ 80 mA"]
    SW --> LD1["U5 TPS73633 LDO<br/>+3V3A_ADC, 55 mA"]
    SW --> LD2["U6 TPS73633 LDO<br/>+3V3A_AMP, 43 mA"]
    LD2 --> REF["U7 ref buffer<br/>VREF_OFF 1.807 V<br/>VCM_REF 1.65 V"]
  end
  BK1 --> FPGA
  BK1 --> MEM
  BK1 --> USB
  BK2 --> FPGA
  LD1 --> ADC1
  LD1 --> ADC2
  LD2 --> AFE1
  REF --> AFE1
```

## Signal flow, in words

1. **Acquire.** Host writes a start command over USB -> FX2 -> FPGA. The FPGA captures both
   12-bit buses on every rising edge of `CLK_FPGA` (the buffered copy of the same 10 MHz
   oscillator that clocks the ADCs), packs the pair into two 16-bit words, and streams them
   into SDRAM. 4 bytes per 100 ns = 40 MB/s written; SDRAM raw is 200 MB/s.
2. **Stop.** Capture ends at the programmed depth (up to 8.388 MSa/channel = 0.839 s).
3. **Drain.** The FPGA reads SDRAM and pushes bytes into the FX2 slave FIFO at 48 MB/s;
   the host pulls them over USB 2.0 HS bulk at ~35–43 MB/s. Full 32 MB drains in ~0.9 s.

Capture and drain never overlap — this is the burst architecture fixed by requirement F6.

## Clock tree (requirement 7, HARD)

```
X1 (10.000 MHz XO) ──33 Ω──┬── CLK_ADC ── U150.CLK  (AD9237 #1)
                           └────────────── U250.CLK  (AD9237 #2)   [matched stubs, ±5 mm]
X1 ──────── U8 74LVC1G17 ── CLK_FPGA ── U30 GCLK pin  (capture domain)
U30 internal DCM/PLL: CLK_FPGA x10 = 100 MHz  -> SDRAM domain only
U50 FX2 IFCLK (48 MHz, from FX2's own 24 MHz crystal) -> U30 (drain domain only)
```

The ADC sample clock is the raw oscillator output. No PLL, no FPGA output, no gate is in
that path. The FPGA's copy is taken through a buffer so that the FPGA's input capacitance
and any reflections on the long trace never appear on the ADC clock node.
