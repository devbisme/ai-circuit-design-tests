# Block diagram — dual_adc_usb

Nine blocks (modular coding mode). Solid arrows carry signals; dotted arrows carry power.
Block ids match `handoffs/02_architecture.md` § Block manifest.

```mermaid
flowchart LR
  subgraph ENTRY["usb_power_in"]
    J1["J1 USB-C (USB2 only)<br/>CC 5.1k ×2"] --- U1["U1 USBLC6-2 ESD<br/>D1 SMF5.0A"]
    U1 --- U2["U2 SY6280 load switch<br/>soft-start + I-limit"]
  end

  subgraph PWR["power_rails"]
    U3["U3 TLV1117LV33<br/>VD_3V3"]
    U4["U4 AP2112K-1.2<br/>VD_1V2"]
    U5["U5 TLV75518<br/>VD_1V8"]
    U6["U6 TPS7A2033<br/>VA_3V3 (low noise)"]
  end

  subgraph BIP["bipolar_supply"]
    U7["U7 LM27762<br/>±2.5 V (VA_P2V5 / VA_N2V5)"]
  end

  subgraph AFE["analog_front_end (×2 channels)"]
    BNC["J2/J3 BNC"] --> ATT["906k / 100k compensated<br/>10:1 attenuator, 1 MΩ ∥ ~20 pF<br/>BAV199 clamp"]
    ATT --> BUF["U8/U10 OPA354<br/>unity buffer, ±2.5 V"]
    BUF --> FDA["U9/U11 THS4521<br/>SE→diff, gain 0.91<br/>2-pole AAF, −3 dB ≈ 4.6 MHz"]
  end

  subgraph ADCB["adc"]
    ADC["U12 ADS5231<br/>dual 12-bit, 20 MSPS (PLL on)<br/>33 Ω RN1–RN7 on outputs"]
  end

  subgraph CLK["sample_clock"]
    XO["X1 20 MHz CMOS XO<br/>R57 / R58 series 33 Ω"]
  end

  subgraph FPGA["fpga_core"]
    FP["U15 GW1NR-LV9QN88P<br/>capture, trigger, 2:1 decimate<br/>BSRAM 16k/ch + 8 MB PSRAM FIFO<br/>J4 JTAG (1.8 V)"]
  end

  subgraph USBB["usb_bridge"]
    FT["U13 FT232H<br/>245 sync FIFO @ 60 MHz<br/>Y1 12 MHz, U14 93LC56B"]
  end

  subgraph IOX["io_expansion"]
    LS["U16 SN74LV4T125 (1.8→3.3 V)<br/>U17 SN74LV1T34 (5→1.8 V)<br/>LED2/LED3, J5 ext trigger"]
  end

  FDA -- "AIN_x_P/N" --> ADC
  ADC -- "ADC_VCM (1.5 V)" --> FDA
  XO -- "ADC_CLK" --> ADC
  XO -- "ADC_CLK_FPGA" --> FP
  ADC -- "ADC_DA[11:0], ADC_DB[11:0]<br/>OVRA/OVRB/DVA" --> FP
  FP -- "ADC_SEL/SEN/SCLK/SDATA" --> ADC
  FP <-- "FT_D[7:0] + 6 ctrl + FT_CLKOUT" --> FT
  FT <-- "USB_DP / USB_DM (480 Mb/s)" --> J1
  FP -- "LED/TRIG/GPIO @1.8 V" --> LS
  LS -- "TRIG_IN_1V8" --> FP

  U2 -. VBUS_SW .-> U3 & U6 & U7
  U3 -. VD_3V3 .-> U4 & U5
  U3 -. VD_3V3 .-> FT & FP & LS
  U4 -. VD_1V2 .-> FP
  U5 -. VD_1V8 .-> FP & LS
  U6 -. VA_3V3 .-> ADC & FDA & XO
  U7 -. "VA_P2V5 / VA_N2V5" .-> BUF
```

## Signal flow and data rates

| Path | Rate | Notes |
|---|---|---|
| BNC → ADC | analog, −3 dB ≈ 4.6 MHz | ±10 V → ±0.904 V diff (89.5 % FS) |
| ADC → FPGA | 20 MSPS × 24 bit = 480 Mb/s parallel | 3.3 V CMOS; 6-clock latency; setup ≥ 10 ns / hold ≥ 20 ns at 20 MSPS |
| FPGA DSP | 2:1 half-band decimation → 10 MSPS/ch | gateware (out of scope) |
| FPGA → FT232H | 60 MHz × 8 bit bus; payload 30 MB/s packed (2×12 b → 3 B) | FT232H ceiling "up to 40 MB/s" |
| FT232H → host | USB 2.0 HS bulk | block capture guaranteed; streaming is best effort |

## Clock domains

1. **ADC domain, 20 MHz** — X1 → ADC_CLK (ADC) and ADC_CLK_FPGA (GCLKT_4). This is the only source of sample
   timing. It never passes through the FPGA PLL on its way to the ADC (F12).
2. **USB domain, 60 MHz** — FT232H CLKOUT → GCLKT_3. Present only in sync-FIFO mode.
3. **PSRAM/system** — FPGA rPLL derived from ADC_CLK_FPGA. FPGA-internal only.

CDC between 1 ↔ 3 ↔ 2 uses async FIFOs in gateware (out of scope, but the schematic provides the clocks).
