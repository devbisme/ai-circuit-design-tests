# Block Diagram — dual_adc_usb

Dual-channel, ±10 V, 12-bit, 10 MSPS/channel simultaneous-sampling USB 2.0 acquisition
board. USB bus powered (5 V / 500 mA ceiling), 4-layer PCB, ~100 × 70 mm.

## Top-level signal flow

```mermaid
flowchart LR
    subgraph ANALOG["ANALOG ZONE (left half of PCB)"]
        J2["J2 BNC ch A<br/>1 MOhm"] --> AFEA["afe_channel A<br/>20:1 comp. attenuator<br/>FET buffer + 4th-order<br/>5 MHz AAF + level shift<br/>out 0.5-2.5 V"]
        J3["J3 BNC ch B<br/>1 MOhm"] --> AFEB["afe_channel B<br/>identical"]
        AFEA --> ADCA["adc_channel A<br/>AD9235BRUZ-20<br/>12b / 10 MSPS<br/>parallel CMOS"]
        AFEB --> ADCB["adc_channel B<br/>AD9235BRUZ-20"]
        CLK["clock_gen<br/>10.000 MHz XO<br/>+ 2x LVC1G34 buffer"]
        CLK -->|CLK_ADC_A| ADCA
        CLK -->|CLK_ADC_B| ADCB
    end

    subgraph DIGITAL["DIGITAL ZONE (right half of PCB)"]
        ADCA -->|"ADCA_D[11:0], OTR"| FPGA["fpga_core<br/>iCE40HX4K-TQ144<br/>capture FSM, SRAM ctrl,<br/>decimator, 12-bit packer,<br/>command parser"]
        ADCB -->|"ADCB_D[11:0], OTR"| FPGA
        CLK -->|CLK_10M| FPGA
        FPGA <-->|"A[17:0] / D[15:0] / nCE nOE nWE nUB nLB"| SRAM["sram_buffer<br/>IS61WV25616 256Kx16<br/>512 kB capture RAM<br/>131,072 samples/ch"]
        FPGA <-->|"FIFO_D[7:0], nRXF nTXE nRD nWR nOE"| USBB["usb_bridge<br/>FT232HL<br/>FT245 SYNC FIFO<br/>60 MHz, ~30 MB/s"]
        USBB -->|CLK60| FPGA
        USBB -->|PWREN_N| PWRA
    end

    subgraph POWER["POWER"]
        J1["usb_c_input<br/>USB-C, CC 5k1,<br/>polyfuse, ESD, CM choke"] -->|VBUS| PWRD["power_digital<br/>AP7361C-33E 3V3_D<br/>AP2112K-1.2 1V2"]
        J1 -->|VBUS| PWRA["power_analog<br/>PFET load switch<br/>+5V_A LC filter<br/>LP5907 3V3_A<br/>LM2776 -5V_A<br/>REF3025 2.5 V"]
        J1 -->|"USB_DP / USB_DM"| USBB
    end

    PWRD -.->|3V3_D / 1V2| FPGA
    PWRD -.->|3V3_D| SRAM
    PWRD -.->|3V3_D| USBB
    PWRA -.->|"+5V_A / -5V_A / VREF_0V5"| AFEA
    PWRA -.->|"+5V_A / -5V_A / VREF_0V5"| AFEB
    PWRA -.->|3V3_A| ADCA
    PWRA -.->|3V3_A| ADCB
    PWRA -.->|3V3_CLK| CLK
```

## Analog front end, one channel (detail)

```mermaid
flowchart LR
    BNC["BNC center<br/>+/-10 V"] --> R1["R_top 950k<br/>2x 475k 0805 series<br/>|| C_trim 2-10 pF"]
    R1 --> NODE(("ATTN node<br/>+/-0.5 V<br/>Zth 47.5k"))
    GNDLEG["R_bot 50k || C_fix+C_trim<br/>to GND"] --- NODE
    NODE --> CLAMP["BAV99 clamp to<br/>+5V_A / -5V_A<br/>via 1k series"]
    CLAMP --> A1["A1 AD8066 1/2<br/>FET-input unity buffer<br/>+/-5 V"]
    A1 --> A2["A2 AD8066 2/2<br/>Sallen-Key 2nd order<br/>fc 5 MHz, gain +1<br/>+/-5 V"]
    A2 --> A3["A3 OPA836 single<br/>MFB 2nd order<br/>fc 5 MHz, gain -2<br/>V+ = VREF_0V5<br/>SINGLE SUPPLY +3V3_A"]
    A3 --> RS["33 Ohm + 22 pF"]
    RS --> ADCIN["ADC VIN+<br/>0.5 - 2.5 V<br/>CM 1.5 V, 2.0 Vpp"]
```

Cascade of the two 2nd-order sections gives a **4th-order Butterworth anti-alias
response, fc = 5.0 MHz**: −3 dB at 5 MHz, −38 dB at 15 MHz, −48 dB at 20 MHz — meets the
[HARD] "≥40 dB by 15–20 MHz" requirement (2nd order would only give 19/24 dB, 3rd order
29/36 dB — see `design_risks.md` R-06).

A3 runs from **+3V3_A single supply**, so its output physically cannot exceed the ADC's
AVDD — this is the ADC over-voltage protection, replacing clamp diodes (whose leakage
would cost ~0.7 LSB of offset).

## Data path

```mermaid
flowchart TD
    S1["2 ch x 10 MSPS x 12 bit<br/>= 240 Mbit/s raw"] --> S2{"mode register<br/>set over FIFO"}
    S2 -->|MODE_BURST| S3["write both channels<br/>as 16-bit words into<br/>512 kB SRAM<br/>131,072 samples/ch<br/>13.107 ms gap-free"]
    S2 -->|MODE_CONT_A / _B| S4["1 channel, no decimation<br/>10 MSPS x 12 b<br/>= 15.0 MB/s"]
    S2 -->|MODE_CONT_DUAL| S5["both channels, decimate by N>=2<br/>max 5 MSPS/ch<br/>= 15.0 MB/s"]
    S3 --> P["invert polarity (code = 4095 - raw)<br/>then 12-bit packer<br/>3 bytes per 2 samples"]
    S4 --> P
    S5 --> P
    P --> F["FT232H FT245 sync FIFO<br/>8 bit @ 60 MHz<br/>~30 MB/s sustained"]
    F --> H["USB 2.0 High-Speed host"]
```

Burst readout: 131,072 samples/ch × 2 ch × 1.5 B = **393,216 bytes**, ≈13 ms at 30 MB/s.

## Block list

| # | block_id | Zone | Instances |
|---|----------|------|-----------|
| 1 | `usb_c_input`   | connector/power | 1 |
| 2 | `power_digital` | power   | 1 |
| 3 | `power_analog`  | power   | 1 |
| 4 | `clock_gen`     | analog  | 1 |
| 5 | `afe_channel`   | analog  | 2 (A, B) |
| 6 | `adc_channel`   | analog  | 2 (A, B) |
| 7 | `sram_buffer`   | digital | 1 |
| 8 | `usb_bridge`    | digital | 1 |
| 9 | `fpga_core`     | digital | 1 |

## Ground and zoning

**One continuous GND net / one solid ground plane on layer 2** (no split plane, no
0 Ω link). Isolation is achieved by *placement*: the analog zone (BNCs, attenuators,
op-amps, ADCs, XO) occupies the left half over unbroken ground; the digital zone (FPGA,
SRAM, FT232H) occupies the right half. The ADC packages straddle the boundary with their
analog pins facing left and DRVDD/data pins facing right. This follows the modern
ADI/Kester recommendation and avoids the return-current discontinuities a split plane
creates under the 39-line SRAM bus. See `design_risks.md` R-03/R-04.

## Stackup

| Layer | Use |
|-------|-----|
| L1 | Signal — analog front end (left), digital routing (right) |
| L2 | **Solid GND plane, no splits** |
| L3 | Power: 3V3_D / 3V3_A / 5V_A / −5V_A / 1V2 pours, each fully over the L2 plane |
| L4 | Signal — SRAM/FIFO bus, low-speed routing |
