# Block Diagram — `dual_adc_usb`

- **Stage:** architecture
- **Date:** 2026-09-06
- **Coding mode:** **MODULAR** — 12 blocks, one `@SubCircuit` per block file under `circuits/dual_adc_usb/`
- **Basis:** SPEC.md §1–§6 (user-approved), binding constraints 1–13

Every block below is a clean `@SubCircuit` candidate. Exact function signatures are derived in
`net_plan.md`; block names here are the Python function names (snake_case).

---

## 1. System block diagram

```mermaid
flowchart TB
  subgraph PWR["POWER (physically: USB-C edge / corner)"]
    UPI["<b>usb_power_input</b><br/>USB-C 2.0 recv, 2x5.1k CC pd<br/>ESD, TVS, ferrite split<br/>P-FET soft-start (inrush)"]
    PD["<b>power_digital</b><br/>BUCK 5V-&gt;3V3_D (1.5 MHz)<br/>LDO 3V3_D-&gt;1V2_CORE"]
    PA["<b>power_analog</b><br/>LDO A5V-&gt;3V0_AVDD (low noise)<br/>LM27762 -&gt; +4V0 / -4V0"]
    VR["<b>vref_2v5</b><br/>ADR4525 2.5V 2ppm<br/>0.1% thin-film div -&gt; 1.000V<br/>OPA192 buffer"]
  end

  subgraph AFE["ANALOG FRONT END (BNC edge, over solid GND pour)"]
    A1["<b>afe_channel</b> (ch A)<br/>BNC 1M||20pF DC<br/>3x300k + 22p C0G / 100k + 180p+trim<br/>node-X clamps (BAV199 + TVS)<br/>OPA1656 buffer + 2nd-order SK<br/>THS4521 FDA + 2nd-order diff RC<br/>4th-order Butterworth fc=4.3 MHz"]
    A2["<b>afe_channel</b> (ch B)<br/>identical, ref block offset"]
  end

  subgraph ACQ["ACQUISITION"]
    XO["<b>clock_40m</b><br/>40 MHz LVCMOS XO, &le;1 ps class<br/>own LDO + LC, 33R series<br/><i>FPGA never synthesises this</i>"]
    ADC["<b>adc_dual</b><br/>LTC2292 dual 12-bit 40 MSPS<br/>parallel CMOS, 24 data lines<br/>33R damping arrays<br/>OVDD from 3V3_D via ferrite"]
  end

  subgraph DIG["DIGITAL"]
    FPGA["<b>fpga_ice40</b><br/>iCE40HX4K-TQ144 (HX8K die)<br/>4:1 decimation, trigger,<br/>SRAM burst ctrl, FIFO drain"]
    SRAM["<b>sram_buffer</b><br/>IS61WV204816BLL-10<br/>2M x 16 async, 10 ns<br/>4 MB = 1 MS/ch unpacked"]
    CFG["<b>config_flash</b><br/>W25Q32JV SPI<br/>mode strap (TH jumper)<br/>shared bus w/ MPSSE"]
    USB["<b>usb_bridge_ft2232h</b><br/>FT2232HL<br/>A = sync 245 FIFO (drain)<br/>B = MPSSE (bitstream + ctrl)<br/>93LC66 EEPROM = cal store"]
    AUX["<b>aux_io</b><br/>probe comp 1 kHz 1 Vpp (TH)<br/>ext trigger bidir (TH hdr)<br/>status LEDs"]
  end

  UPI -->|VBUS_5V| PD
  UPI -->|A5V via ferrite| PA
  PA  -->|A5V| VR
  PD  -->|V3V3_D| FPGA
  PD  -->|V1V2_CORE| FPGA
  PD  -->|V3V3_D via ferrite| ADC
  PD  -->|V3V3_D| SRAM
  PD  -->|V3V3_D| USB
  PD  -->|V3V3_D| CFG
  PA  -->|V3V0_AVDD| ADC
  PA  -->|VP4V0 / VN4V0| A1
  PA  -->|VP4V0 / VN4V0| A2
  PA  -->|VP4V0| XO
  VR  -->|VREF_1V0| ADC

  A1 -->|ainAP / ainAN diff| ADC
  A2 -->|ainBP / ainBN diff| ADC
  ADC -->|adcVcmA 1.5 V| A1
  ADC -->|adcVcmB 1.5 V| A2

  XO ==>|encClk 40 MHz, shortest trace| ADC
  XO -->|xoClkFpga = system clk AND ADC capture clk, falling edge| FPGA
  ADC ==>|adcData 24b + OF x2| FPGA

  FPGA <==>|sramAddr 21 / sramData 16 / 3 ctrl| SRAM
  FPGA <==>|fifoData 8 + 5 hs + ftClk60| USB
  FPGA <-->|SPI x4 + CRESET_B + CDONE| CFG
  USB  -->|MPSSE SPI override| CFG
  FPGA <-->|probeComp / extTrig / LEDs| AUX
  UPI  <-->|usbDp / usbDm| USB

  classDef pwr fill:#fff4e0,stroke:#c88
  classDef ana fill:#e8f4ff,stroke:#68a
  classDef dig fill:#eef7ee,stroke:#7a7
  class UPI,PD,PA,VR pwr
  class A1,A2,XO ana
  class ADC,FPGA,SRAM,CFG,USB,AUX dig
```

---

## 2. Signal chain (one channel, left to right)

```mermaid
flowchart LR
  BNC["BNC<br/>vertical TH<br/>1M || 20 pF<br/>DC only"]
  ATT["compensated 10:1<br/>3x300k 0.1% TF + 22p C0G<br/>100k 0.1% TF + 180p + 5-30p trim<br/>Zth = 90k || 222 pF"]
  CLP["node-X protection<br/>BAV199 to +/-4V0<br/>+ 12V bidir TVS<br/><i>no series R: 90k is the limiter</i>"]
  BUF["OPA1656 A<br/>unity JFET buffer<br/>2.9 nV/rtHz, 6 fA/rtHz"]
  SK["OPA1656 B<br/>2nd-order Sallen-Key<br/>R = 249R"]
  FDA["THS4521 FDA<br/>SE-&gt;diff, gain 1<br/>+ 2nd-order diff RC<br/>Vocm = adcVcm"]
  ADCIN["LTC2292 ch<br/>2 Vpp diff<br/>40 MSPS"]
  BNC --> ATT --> CLP --> BUF --> SK --> FDA --> ADCIN
```

**Cumulative analog response: 4th-order Butterworth, fc = 4.3 MHz** (2nd order in the SK stage,
2nd order around the FDA). See `design_risks.md` §3 for why 4.3 MHz and not 4.0 MHz.

---

## 3. Gateware data path (informational — constrains the hardware interface only)

```mermaid
flowchart LR
  D["adcData<br/>2 x 12b @ 40 MSPS"]
  C1["CIC N=4, R=2, M=1<br/>40 -&gt; 20 MHz<br/>gd = 2 in-samples = 50 ns"]
  F1["FIR 21-tap symmetric<br/>R=2, 20 -&gt; 10 MHz<br/>inverse-sinc folded in<br/>gd = 10 samples = 500 ns"]
  TRG["digital trigger<br/>level / slope / either ch<br/>host force<br/>ext trig in/out"]
  SC["SRAM burst ctrl<br/>circular pre-trigger addr<br/>20 M writes/s"]
  S["IS61WV204816<br/>2M x 16"]
  FF["async FIFO<br/>40 -&gt; 60 MHz CDC"]
  U["FT2232H ch A<br/>sync 245 FIFO"]
  D --> C1 --> F1 --> TRG --> SC --> S --> FF --> U
```

**Total decimation-filter group delay = 550 ns = 5.5 decimated samples.** This is the calibratable
trigger offset required by SPEC §8.2. Derivation and alternatives in `design_risks.md` §4.

---

## 4. Block manifest (for the orchestrator's `block_manifest`)

| # | Block (`snake_case`) | File | Instances | Ref prefix range | Notes |
|---|---|---|---|---|---|
| 1 | `usb_power_input` | `usb_power_input.py` | 1 | J1, D1–D3, L1–L2, C1–C6, R1–R4, Q1 | TH: none; USB-C is SMD |
| 2 | `power_digital` | `power_digital.py` | 1 | U1–U2, L3, C10–C19, R10–R12 | buck + 1V2 LDO |
| 3 | `power_analog` | `power_analog.py` | 1 | U3–U4, L4–L6, C20–C39, R20–R25 | AVDD LDO + LM27762 |
| 4 | `vref_2v5` | `vref_2v5.py` | 1 | U5–U6, R30–R33, C40–C45 | ADR4525 + divider + buffer |
| 5 | `afe_channel` | `afe_channel.py` | **2** (A, B) | ch A: 100-block, ch B: 200-block | parameterised; TH BNC |
| 6 | `adc_dual` | `adc_dual.py` | 1 | U7, RN1–RN6, C50–C75 | LTC2292 |
| 7 | `clock_40m` | `clock_40m.py` | 1 | U8–U9, L7, C80–C85, R40–R41 | XO + own LDO |
| 8 | `fpga_ice40` | `fpga_ice40.py` | 1 | U10, C90–C115, R50–R55, L8 | iCE40HX4K-TQ144 |
| 9 | `sram_buffer` | `sram_buffer.py` | 1 | U11, C120–C123 | IS61WV204816 |
| 10 | `config_flash` | `config_flash.py` | 1 | U12, R60–R65, C125, JP1 | TH mode strap |
| 11 | `usb_bridge_ft2232h` | `usb_bridge_ft2232h.py` | 1 | U13–U14, Y1, L9–L10, C130–C150, R70–R80 | FT2232HL + EEPROM |
| 12 | `aux_io` | `aux_io.py` | 1 | J4–J6, R90–R99, D10–D13 | TH trigger hdr + probe-comp terminal |

Assembly file `__main__.py` creates all nets listed in `net_plan.md` §1 and calls the 12 blocks
(with `afe_channel` called twice).

---

## 5. Physical floorplan intent (carried to layout, not to SKiDL)

```
+--------------------------------------------------------------+  ~100 x 80 mm, 4 layer
| BNC A (TH)   [ afe_channel A ]                               |  L1 sig / L2 solid GND /
| BNC B (TH)   [ afe_channel B ]   [adc_dual]  [clock_40m]     |  L3 pwr / L4 sig
|              -- solid uninterrupted GND pour under AFE --    |
|  [vref_2v5]  [power_analog]      [fpga_ice40]  [sram_buffer] |
|                                                              |
| probe-comp TH  ext-trig TH   [config_flash] [usb_bridge]     |
| [power_digital BUCK + keep-out] .................. USB-C     |
+--------------------------------------------------------------+
```

- BNCs on the opposite edge from USB-C and the buck (SPEC §5).
- Buck in the corner with a keep-out; `clock_40m` XO within ~10 mm of the ADC ENC pin.
- `afe_channel` ground return kept on an uninterrupted pour; no digital return current crosses it.
