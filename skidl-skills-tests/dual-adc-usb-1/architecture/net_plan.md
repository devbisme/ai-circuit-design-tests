# Net Plan — `dual_adc_usb`

- **Stage:** architecture
- **Date:** 2026-09-06
- **Coding mode:** MODULAR (12 blocks). Every net below is created in `__main__.py` and passed
  into blocks by keyword argument. Block-internal nets are **not** listed here (blocks own them).

Naming per `rules/skidl-syntax.md`: **UPPERCASE** = power rail (`.drive = POWER`),
**camelCase** = signal. Buses use `Bus(...)`.

---

## 1. Global nets created in `__main__.py`

### 1.1 Power rails (all `.drive = POWER`)

| Net | Type | V | Source block | Consumer blocks |
|---|---|---|---|---|
| `GND` | ground | 0 | all | all (single net; split is a layout partition, not a netlist partition) |
| `VBUS_5V` | supply | 4.75–5.25 | `usb_power_input` | `power_digital`, `usb_bridge_ft2232h` (VBUS sense only) |
| `VBUS_A5V` | supply | 4.75–5.25 | `usb_power_input` (post-ferrite branch) | `power_analog`, `vref_2v5`, `clock_40m` |
| `V3V3_D` | supply | 3.30 | `power_digital` (buck) | `fpga_ice40`, `sram_buffer`, `config_flash`, `usb_bridge_ft2232h`, `adc_dual` (OVDD via ferrite), `aux_io` |
| `V1V2_CORE` | supply | 1.20 | `power_digital` (LDO) | `fpga_ice40` |
| `V3V0_AVDD` | supply | 3.00 | `power_analog` (LDO) | `adc_dual` (analog VDD only) |
| `VP4V0` | supply | +4.00 | `power_analog` (LM27762 OUT+) | `afe_channel` A/B, `vref_2v5`, `clock_40m` (osc LDO in) |
| `VN4V0` | supply | −4.00 | `power_analog` (LM27762 OUT−) | `afe_channel` A/B, `vref_2v5` |

> `VBUS_A5V` and `VBUS_5V` are **separate nets** joined only through the split ferrite inside
> `usb_power_input`. This is the SPEC §3.1 "split analog/digital at source" requirement and it must
> survive into the netlist so the layout cannot merge them.

### 1.2 Reference / bias nets

| Net | Type | Driver | Loads |
|---|---|---|---|
| `vref1V0` | analog, 1.000 V | `vref_2v5` (buffered) | `adc_dual` SENSE |
| `adcVcmA` | analog, 1.5 V | `adc_dual` U7.VCMA (pin 61) | `afe_channel('A')` FDA V_OCM |
| `adcVcmB` | analog, 1.5 V | `adc_dual` U7.VCMB (pin 20) | `afe_channel('B')` FDA V_OCM |

> **Correction (2026-09-07):** an earlier revision had a single `adcVcm` net. The LTC2292
> datasheet pin descriptions for VCMA (pin 61) and VCMB (pin 20) each say verbatim
> **"Do not connect to VCMB" / "Do not connect to VCMA"**. They are two separate 1.5 V
> outputs and must stay on two separate nets. `afe_channel`'s signature is unchanged — the
> A instance is passed `adcVcmA`, the B instance `adcVcmB`.

### 1.3 Analog signal nets

| Net | Type | Driver | Load |
|---|---|---|---|
| `ainAP`, `ainAN` | analog diff pair | `afe_channel`(A) FDA | `adc_dual` AIN+A / AIN−A |
| `ainBP`, `ainBN` | analog diff pair | `afe_channel`(B) FDA | `adc_dual` AIN+B / AIN−B |

### 1.4 Clock nets

| Net | Type | Driver | Loads | Notes |
|---|---|---|---|---|
| `encClk40` | clock 40 MHz LVCMOS | `clock_40m` | `adc_dual` ENC only | **shortest trace on the board**; single load |
| `xoClkFpga` | clock 40 MHz LVCMOS | `clock_40m` (2nd tap, R41 100R) | `fpga_ice40` GBIN | **system clock AND the ADC data-capture clock** — see §1.4.1 |
| `ftClk60` | clock 60 MHz | `usb_bridge_ft2232h` ADBUS/CLKOUT | `fpga_ice40` GBIN | sync-245 FIFO clock |

#### 1.4.1 D3 — there is no `adcClkOut`. Capture is on the FALLING edge of `xoClkFpga`.

**Correction (2026-09-07).** An earlier revision of this table defined `adcClkOut` as
`U7.CLKOUT -> fpga_ice40 GBIN`. **The LTC2292 has no CLKOUT pin.** Verified twice: zero
occurrences of the string "CLKOUT" across all 28 pages of
`datasheets/LTC2292_LTC2293_LTC2291_229321fa.pdf`, and the KiCad symbol
`Analog_ADC:LTC2292xUP` has 65 pins with no such pin. The part has CLKA (pin 8) and
CLKB (pin 9), single-ended clock *inputs* only. The claim was inherited from
`ic_selection.md` while the datasheet was unobtainable.

**Resolution (user decision D3):** the FPGA's input registers are clocked from the same
40 MHz XO that drives CLKA/CLKB, via the existing `xoClkFpga` tap. The sample clock is
never routed through the FPGA, so SPEC Q7 ("the FPGA consumes the clock, never
synthesises it") is not violated. The net `adcClkOut` is **deleted**.

**Capture edge: FALLING. Do not change this to rising.**

Datasheet timing, `Timing Characteristics` p.6, LTC2292 column, C_L = 5 pF, full temp range
(the bullet applies over the full operating temperature range) [VERIFIED-PDF]:

| Symbol | Parameter | Min | Typ | Max |
|---|---|---|---|---|
| t_D | CLK to DATA delay | **1.4 ns** | 2.7 ns | **5.4 ns** |
| — | Data access time after OE fall | — | 4.3 ns | 10 ns |
| t_AP | Sample-and-hold aperture delay | — | 0 ns | — |
| — | Pipeline latency | — | 5 cycles | — |

iCE40HX4K input-register requirements, global-buffer clock **without** PLL
(`ICE40HX4K-TQ144.pdf`, "General I/O Pin Parameters (Using Global Buffer Clock without PLL)")
[VERIFIED-PDF]:

| Symbol | Parameter | Value |
|---|---|---|
| t_SU | clock-to-data setup, PIO input register | **-0.43 ns** (negative: data may arrive *after* the clock) |
| t_H | clock-to-data hold, PIO input register | **2.38 ns** |
| t_SKEW_IO | data-bus skew across a bank of I/Os | 290 ps |

At 40 MHz, T = 25 ns. Sample N's data at the ADC pins is valid from t_D(max) = **5.4 ns**
after its launching rising edge until the next rising edge + t_D(min) = **26.4 ns**.
**Valid window = [5.4, 26.4] ns, 21.0 ns wide.**

| Capture edge | Raw setup | Raw hold | Net hold margin after t_H = 2.38 ns, skew 0.29 ns, 0.5 ns trace mismatch | Verdict |
|---|---|---|---|---|
| Rising, t = 25 ns | 19.6 ns | **1.4 ns** | **-1.77 ns** | **FAILS.** The iCE40's own t_H (2.38 ns) alone exceeds t_D(min) (1.4 ns). Not merely tight — impossible. |
| **Falling, t = 12.5 ns** | **7.1 ns** | **13.9 ns** | **+10.73 ns** (setup margin +6.74 ns) | **USE THIS.** |

The 7.1 / 13.9 ns figures are the nominal 50 %-duty numbers. The XO's duty cycle is not
guaranteed to 50 %; at a generic 45/55 % part the falling edge moves to 11.25-13.75 ns:

| XO duty | Falling edge | Raw setup | Raw hold | Net setup margin | Net hold margin |
|---|---|---|---|---|---|
| 45 % | 11.25 ns | 5.85 ns | 15.15 ns | +5.49 ns | +11.98 ns |
| 50 % | 12.50 ns | 7.10 ns | 13.90 ns | +6.74 ns | +10.73 ns |
| 55 % | 13.75 ns | 8.35 ns | 12.65 ns | +7.99 ns | +9.48 ns |

Comfortable on both sides across the whole duty-cycle range, and it needs no PLL. A PLL
phase shift on the *capture* clock would also be legal (the ADC encode clock still comes
straight from the XO) but is unnecessary — and would cost 4.16 ns of t_SU_PLL.

**Consequence for U7.MODE — the clock duty cycle stabiliser must be ON.** The datasheet
(Applications Information, "the CLK signal should have a 50 % (+/-5 %) duty cycle") sets
t_L and t_H minima of **11.8 ns each** with the stabiliser OFF, i.e. the duty cycle must
sit inside 47.2-52.8 %. A generic 45/55 % XO violates that. With the stabiliser ON the
datasheet accepts 40-60 %. `MODE` is therefore biased to **1/3 V_DD** by an external
divider = offset-binary output format + duty cycle stabiliser ON. See §3.6.

### 1.5 ADC parallel data (Bus)

| Bus / net | Width | Driver | Load |
|---|---|---|---|
| `adcDataA = Bus('adcDataA', 12)` | 12 | `adc_dual` | `fpga_ice40` |
| `adcDataB = Bus('adcDataB', 12)` | 12 | `adc_dual` | `fpga_ice40` |
| `adcOfA`, `adcOfB` | 1 each | `adc_dual` | `fpga_ice40` |
| `adcShdn`, `adcOeBar` | 1 each | `fpga_ice40` | `adc_dual` |

### 1.6 SRAM interface

| Bus / net | Width | Direction | Notes |
|---|---|---|---|
| `sramAddr = Bus('sramAddr', 21)` | 21 | FPGA → SRAM | A0..A20, 2 M words |
| `sramData = Bus('sramData', 16)` | 16 | bidirectional | DQ0..DQ15 |
| `sramCeBar` | 1 | FPGA → SRAM | |
| `sramOeBar` | 1 | FPGA → SRAM | |
| `sramWeBar` | 1 | FPGA → SRAM | |
| *(UB#/LB# tied low inside `sram_buffer`)* | — | — | all accesses are 16-bit |

### 1.7 FT2232H channel A — synchronous 245 FIFO

| Bus / net | Width | Direction |
|---|---|---|
| `fifoData = Bus('fifoData', 8)` | 8 | bidirectional (ADBUS0-7) |
| `fifoRxfBar` | 1 | FT2232H → FPGA |
| `fifoTxeBar` | 1 | FT2232H → FPGA |
| `fifoRdBar` | 1 | FPGA → FT2232H |
| `fifoWrBar` | 1 | FPGA → FT2232H |
| `fifoOeBar` | 1 | FPGA → FT2232H |
| *(SIWU# pulled high inside `usb_bridge_ft2232h`)* | — | — |

### 1.8 FPGA configuration / FT2232H channel B (MPSSE)

| Net | Direction | Notes |
|---|---|---|
| `cfgSck` | FT2232H BDBUS0 **or** FPGA SPI_SCK → flash CLK | shared, 100R series in `config_flash` |
| `cfgMosi` | FT2232H BDBUS1 → flash DI / FPGA SPI_SI | shared |
| `cfgMiso` | flash DO → FT2232H BDBUS2 / FPGA SPI_SO | shared |
| `cfgCsBar` | FT2232H BDBUS3 → flash /CS and FPGA SPI_SS_B | shared |
| `fpgaCresetBar` | FT2232H BDBUS4 → FPGA CRESET_B | open-drain-ish; 10k pull-up to V3V3_D |
| `fpgaCdone` | FPGA CDONE → FT2232H BDBUS5 | 470R + LED, 10k pull-up |
| `modeStrap` | JP1 (TH) → FPGA | selects self-boot vs MPSSE-override behaviour in gateware/host |

> Bus arbitration rule (for the gateware/host, recorded here so the schematic gets the resistors):
> while `fpgaCresetBar` is asserted low the FPGA tri-states its SPI pins and the FT2232H owns the
> bus (it can program the flash **or** slave-load the FPGA). After `fpgaCdone` rises the FT2232H
> tri-states BDBUS0-3 and the FPGA may reuse SPI_SCK/SI/SO/SS_B as slow-control user I/O.
> 100 Ω series resistors on all four shared lines are **required**, not optional.

### 1.9 USB

| Net | Type | Between |
|---|---|---|
| `usbDp`, `usbDm` | USB 2.0 HS diff pair, 90 Ω | `usb_power_input` (connector + ESD) ↔ `usb_bridge_ft2232h` |

### 1.10 Auxiliary I/O

| Net | Direction | Notes |
|---|---|---|
| `probeCompDrv` | FPGA → `aux_io` | 3.3 V CMOS, divided to ~1 Vpp at the TH terminal |
| `extTrig` | bidirectional | FPGA ↔ `aux_io` protection ↔ TH header |
| `ledStatus`, `ledActivity` | FPGA → `aux_io` | |
| `ftResetBar` | FPGA or RC → `usb_bridge_ft2232h` RESET# | 10k pull-up + 100n; FPGA drive optional |

---

## 2. Exact `@SubCircuit` signatures

These are the function signatures the skidl-block-coder must implement, verbatim.

```python
# 1
def usb_power_input(vbus_5v, vbus_a5v, gnd, usb_dp, usb_dm): ...

# 2
def power_digital(vbus_5v, v3v3_d, v1v2_core, gnd): ...

# 3
def power_analog(vbus_a5v, v3v0_avdd, vp4v0, vn4v0, gnd): ...

# 4
def vref_2v5(vbus_a5v, vp4v0, vn4v0, gnd, vref_1v0): ...

# 5  — called twice: afe_channel('A', ..., adc_vcm=adcVcmA, ...)
#                    afe_channel('B', ..., adc_vcm=adcVcmB, ...)
def afe_channel(ch, vp4v0, vn4v0, gnd, adc_vcm, ain_p, ain_n): ...

# 6  — REVISED 2026-09-07 (D3): adc_clk_out REMOVED (no such pin on the LTC2292);
#      adc_vcm SPLIT into adc_vcm_a / adc_vcm_b (datasheet forbids joining them).
def adc_dual(v3v0_avdd, v3v3_d, gnd, vref_1v0, adc_vcm_a, adc_vcm_b,
             ain_ap, ain_an, ain_bp, ain_bn,
             enc_clk40,
             adc_data_a, adc_data_b, adc_of_a, adc_of_b,
             adc_shdn, adc_oe_bar): ...

# 7
def clock_40m(vbus_a5v, gnd, enc_clk40, xo_clk_fpga): ...

# 8  — REVISED 2026-09-07 (D3): adc_clk_out REMOVED. xo_clk_fpga is now both the
#      system clock and the ADC capture clock (falling edge). See §1.4.1.
def fpga_ice40(v3v3_d, v1v2_core, gnd,
               adc_data_a, adc_data_b, adc_of_a, adc_of_b,
               adc_shdn, adc_oe_bar, xo_clk_fpga,
               sram_addr, sram_data, sram_ce_bar, sram_oe_bar, sram_we_bar,
               fifo_data, fifo_rxf_bar, fifo_txe_bar, fifo_rd_bar,
               fifo_wr_bar, fifo_oe_bar, ft_clk60,
               cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar,
               fpga_creset_bar, fpga_cdone, mode_strap,
               probe_comp_drv, ext_trig, led_status, led_activity): ...

# 9
def sram_buffer(v3v3_d, gnd, sram_addr, sram_data,
                sram_ce_bar, sram_oe_bar, sram_we_bar): ...

# 10
def config_flash(v3v3_d, gnd, cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar,
                 fpga_creset_bar, fpga_cdone, mode_strap): ...

# 11
def usb_bridge_ft2232h(v3v3_d, gnd, usb_dp, usb_dm,
                       fifo_data, fifo_rxf_bar, fifo_txe_bar, fifo_rd_bar,
                       fifo_wr_bar, fifo_oe_bar, ft_clk60,
                       cfg_sck, cfg_mosi, cfg_miso, cfg_cs_bar,
                       fpga_creset_bar, fpga_cdone, ft_reset_bar): ...

# 12
def aux_io(v3v3_d, gnd, probe_comp_drv, ext_trig,
           led_status, led_activity): ...
```

`afe_channel` is the only parameterised block: `ch` is `'A'` or `'B'` and is used **only** to build
reference designators (`R1xx` for A, `R2xx` for B) and net-name suffixes for the block-internal nets.
Nothing else differs between the two instances.

---

## 3. Net-by-net connection table (netlist-level detail)

### 3.1 `usb_power_input`

| Net | Connected parts / pins |
|---|---|
| `VBUS_5V` | J1.VBUS(A4,A9,B4,B9) → D1(TVS SMAJ5.0A) → Q1 soft-start P-FET S/D → L1 ferrite → C1(10 µF)+C2(100 n) → out |
| `VBUS_A5V` | Q1 drain node → L2 ferrite (600 Ω @100 MHz) → C3(10 µF)+C4(100 n) |
| `GND` | J1.GND(A1,A12,B1,B12), J1 shield, all returns |
| `usbDp` | J1.DP1(A6), J1.DP2(B6) tied → U_esd(USBLC6-2SC6) → out |
| `usbDm` | J1.DN1(A7), J1.DN2(B7) tied → U_esd → out |
| *(internal)* `ccA`, `ccB` | J1.CC1(A5)→R1 5.1k→GND; J1.CC2(B5)→R2 5.1k→GND |
| *(internal)* | R3 (100k) + C5 (100 n) gate RC on Q1; R4 (100k) gate pull-down |

### 3.2 `power_digital`

| Net | Connected parts / pins |
|---|---|
| `VBUS_5V` | U1(TLV62569).VIN, C10 (10 µF), C11 (100 n) |
| *(internal)* `swNode` | U1.SW → L3 (2.2 µH) |
| `V3V3_D` | L3 → C12,C13 (2×22 µF) + C14 (100 n); U1.FB via R10/R11 divider; U2(TLV75512).IN, C15 |
| `V1V2_CORE` | U2.OUT → C16 (10 µF) + C17 (100 n) |
| — | U1.EN → V3V3-independent: tie to VBUS_5V through R12 (100k) — always-on, no post-enum switch |

### 3.3 `power_analog`

| Net | Connected parts / pins |
|---|---|
| `VBUS_A5V` | U3(LP5907-3.0).IN + C20; U4(LM27762).VIN + C21 (2.2 µF); U4.EN+, U4.EN− tied to VIN |
| `V3V0_AVDD` | U3.OUT → L4 ferrite → C22 (10 µF) + C23 (100 n) |
| *(internal)* `cpFly±` | U4.C1+/C1− ↔ C24 (1 µF, X7R, ≥10 V) |
| *(internal)* `cpOut` | U4.CPOUT → C25 (4.7 µF) |
| `VP4V0` | U4.OUT+ → C26 (2.2 µF) → L5 ferrite → C27 (10 µF) + C28 (100 n); FB+ divider R20/R21 |
| `VN4V0` | U4.OUT− → C29 (2.2 µF) → L6 ferrite → C30 (10 µF) + C31 (100 n); FB− divider R22/R23 |

`VP4V0`/`VN4V0` FB dividers set **±4.00 V** (VFB+ = 1.200 V, VFB− = −1.220 V) — see
`ic_selection.md` §4 for the headroom arithmetic and the deviation note vs SPEC §3.1's "±5 V".

### 3.4 `vref_2v5`

| Net | Connected parts / pins |
|---|---|
| `VBUS_A5V` | U5(ADR4525).VIN + C40 (100 n) + C41 (10 µF) |
| *(internal)* `vref2V5` | U5.VOUT + C42 (100 n) + C43 (10 µF); → R30 (1.500 k 0.1% TF) |
| *(internal)* `vrefDiv` | R30/R31 (1.000 k 0.1% TF) junction → U6(OPA192) IN+; C44 (1 µF) to GND |
| `vref1V0` | U6.OUT tied to U6.IN− (unity buffer) → out; C45 (100 n) local |
| `VP4V0`,`VN4V0` | U6.V+ / U6.V− with 100 n each |

### 3.5 `afe_channel` (ch A shown; ch B identical, ref block 2xx)

| Net | Connected parts / pins |
|---|---|
| *(input)* `bncA` | J2 (TH BNC) centre → R101,R102,R103 (3× 300 k 0.1% thin film, series) ‖ C101 (22 pF C0G, ≥250 V) |
| *(node X)* `attOutA` | series-string bottom ↔ R104 (100 k 0.1% TF) ‖ C102 (180 pF C0G) ‖ CV1 (5–30 pF trimmer) to GND |
| `attOutA` clamps | D101 (BAV199) — anode-common to `VN4V0`, cathode-common to `VP4V0`; D102 (12 V bidir TVS) to GND |
| — | **No series resistor between `attOutA` and the buffer.** The 90 kΩ Thévenin *is* the fault current limiter. |
| *(buffer)* | U101A(OPA1656) IN+ ← `attOutA`; OUT tied to IN− (unity) → `bufOutA` |
| *(SK LPF)* | `bufOutA` → R105 (249R) → R106 (249R) → U101B IN+; C103 (C2, to GND), C104 (C1, feedback from U101B OUT to R105/R106 node); U101B OUT tied to IN− → `sk2OutA` |
| *(FDA)* | `sk2OutA` → R107 (249R) → U102(THS4521) IN−; GND → R108 (249R) → U102 IN+; Rf R109/R110 (249R) with Cf C105/C106 (differential 2nd-order); U102.VOCM ← `adcVcm` (+ C107 100 n) |
| `ainAP` | U102.OUT+ → R111 (33R) → out |
| `ainAN` | U102.OUT− → R112 (33R) → out; C108 (22 pF) differential across ainAP/ainAN |
| `VP4V0` | U101.V+ via **R113 (10 Ω)** + C109 (10 µF) + C110 (100 n); U102.VS+ via R114 (10 Ω) + its own 10 µF/100 n |
| `VN4V0` | U101.V− via **R115 (10 Ω)** + C111 (10 µF) + C112 (100 n) |
| `GND` | U102.VS−, all returns |

> The `VP4V0`/`VN4V0` **10 Ω + 10 µF + 100 nF RC at each amp is mandatory**, not decorative — it is
> the mitigation for the LM27762's **2 MHz** in-band switching residue, which is ~40 µV RMS at the
> amplifier output without it. An RC is specified rather than a ferrite because a 600 Ω@100 MHz bead
> has only ~10–30 Ω of impedance at 2 MHz. See `design_risks.md` §2.2.

### 3.6 `adc_dual` — REWRITTEN 2026-09-07 against the datasheet PDF and the KiCad symbol

> The previous revision of this table was written from ADI's product page while the PDF was
> unobtainable and is **wrong in five places**: a CLKOUT pin that does not exist, an ENC+/ENC−
> differential pair that does not exist, a single `VREF` pin that does not exist, single
> `SENSE`/`VCM`/`SHDN`/`OE` pins where the part has independent per-channel pairs, and a MUX
> strap in the wrong state. Everything below is checked against
> `datasheets/LTC2292_LTC2293_LTC2291_229321fa.pdf` "Pin Functions" pp.11-12 [VERIFIED-PDF]
> and against the 65-pin `Analog_ADC:LTC2292xUP` KiCad symbol read off disk.

**Package: QFN-64 (UP), 9x9 mm. Pin 65 is the exposed pad and is ADC power ground — it must be
soldered.** In the KiCad symbol GND appears on pins 17, 64 and 65.

| Net | U7 pin(s) | Connection |
|---|---|---|
| `V3V0_AVDD` | VDD 7, 10, 18, 63 | 0.1 µF at **each** pin (C60-C63) + 10 µF bulk (C64). Datasheet: "Bypass to GND with 0.1 µF ceramic chip capacitors." |
| `GND` | GND 17, 64, **65 (exposed pad)**, OGND 31, 50 | OGND is the output-driver ground; single netlist net, layout partition only |
| *(internal)* `ovdd3V3` | OVDD 32, 49 | `V3V3_D` → **L8** ferrite → `ovdd3V3`; 0.1 µF at each OVDD pin (C65, C66) + 10 µF (C67). Keeps 26 switching outputs off `V3V0_AVDD`. |
| `ainAP` / `ainAN` | AINA+ 1 / AINA− 2 | from `afe_channel('A')` |
| `ainBP` / `ainBN` | AINB+ 16 / AINB− 15 | from `afe_channel('B')` |
| `vref1V0` | **SENSEA 62 and SENSEB 19** | 1.000 V external reference on **both** SENSE pins. Datasheet: "An external reference greater than 0.5 V and less than 1 V applied to SENSE selects an input range of ±V_SENSE" and "For the best channel matching, connect an external reference to SENSEA and SENSEB." 1.000 V → ±1 V = 2 V(P-P) = the design span, from the ADR4525 chain rather than the internal bandgap. Bypass each SENSE pin to GND with **1 µF** as close to the device as possible (C68, C69) — datasheet's explicit requirement for an externally driven SENSE. |
| *(internal)* `refhA` | REFHA 3, 4 | the two pins are shorted (package-inductance split, not two nodes) |
| *(internal)* `reflA` | REFLA 5, 6 | shorted likewise |
| *(internal)* `refhB` | REFHB 13, 14 | shorted |
| *(internal)* `reflB` | REFLB 11, 12 | shorted |
| — | REFHA↔REFLA | **C50 0.1 µF + C51 2.2 µF** between them, 0.1 µF hard against the pins |
| — | REFHA→GND, REFLA→GND | **C52, C53 — 1 µF each** |
| — | REFHB↔REFLB | **C54 0.1 µF + C55 2.2 µF** |
| — | REFHB→GND, REFLB→GND | **C56, C57 — 1 µF each** |
| `adcVcmA` | **VCMA 61** | 1.5 V output; **C58 2.2 µF** to GND. Exported to `afe_channel('A')` V_OCM. |
| `adcVcmB` | **VCMB 20** | 1.5 V output; **C59 2.2 µF** to GND. Exported to `afe_channel('B')` V_OCM. |
| — | — | **VCMA and VCMB MUST NOT be joined.** Datasheet, verbatim, in both pin descriptions: "Do not connect to VCMB" / "Do not connect to VCMA". |
| `encClk40` | **CLKA 8 and CLKB 9** | single-ended LVCMOS, both pins on the same net. There is **no ENC+/ENC− pair**. Datasheet: "It is recommended that CLKA and CLKB are shorted together"; skew must be < 1 ns, which tying them at adjacent package pins satisfies trivially. "The input sample starts on the positive edge." |
| — | **MODE 60** | **1/3 V_DD** via divider **R46 (20 k) from V3V0_AVDD, R47 (10 k) to GND** ⇒ offset-binary output format + **clock duty cycle stabiliser ON**. Required, not optional — see §1.4.1. I_MODE leakage is ±3 µA over a 6.67 kΩ Thévenin = ±20 mV, well inside the 1/3 V_DD window. |
| — | **MUX 21** | strapped **HIGH** to `V3V0_AVDD`. **Correction:** the previous revision strapped it low. Both states are non-multiplexed; MUX only *swaps* the buses. Datasheet: "If MUX is High, Channel A comes out on DA0-DA11, OFA; Channel B comes out on DB0-DB11, OFB. If MUX is Low, the output busses are swapped." HIGH gives the natural A→DA mapping the net names assume. (Multiplexing both channels onto one bus would require MUX, CLKA and CLKB tied together — explicitly not done here.) |
| `adcDataA[0:11]` | DA0-DA11 = pins 43-48, 51-56 | 33 Ω series per line, **RN1-RN3** (3 × 4-element arrays) |
| `adcDataB[0:11]` | DB0-DB11 = pins 26-30, 33-39 | 33 Ω series per line, **RN4-RN6** |
| `adcOfA` | OFA 57 | 33 Ω series, **R44** (discrete — 24 data lines consume RN1-RN6 exactly) |
| `adcOfB` | OFB 40 | 33 Ω series, **R45** |
| `adcShdn` | **SHDNA 59 and SHDNB 22** | one net to both; **R48 10 k pull-down** so the ADC converts even with the FPGA unconfigured. SHDN = GND with OE = GND ⇒ normal operation, outputs enabled. |
| `adcOeBar` | **~OEA 58 and ~OEB 23** | one net to both; **R49 10 k pull-down**. Active-low output-enable: low = outputs driven. |
| — | NC 24, 25, 41, 42 | "Do Not Connect These Pins" — `+= NC` in SKiDL |

**Damping-resistor note.** The datasheet states the output buffers have an internal series
resistor that "makes the output appear as 50 Ω to external circuitry and **may eliminate the
need for external damping resistors**." The 33 Ω arrays are retained anyway: 33 Ω + 50 Ω into
the iCE40's 6 pF input is τ ≈ 0.5 ns against a 21 ns valid window, so they cost nothing and
they cap dI/dt on 26 simultaneously switching lines. They are an EMI/SI measure, not a timing
one, and the §1.4.1 margins are computed **without** crediting them.

**There is no `adcClkOut` row.** See §1.4.1.

### 3.7 `clock_40m`

| Net | Connected parts / pins |
|---|---|
| `VBUS_A5V` | U8 (LP5907-3.3) IN + C80 |
| *(internal)* `vXo3V3` | U8.OUT → L7 ferrite → C81 (10 µF) + C82 (100 n) → U9(XO).VDD, C83 (100 n) at the pin |
| `encClk40` | U9.OUT → R40 (33R) → out — shortest trace on the board, to **U7.CLKA (8) + U7.CLKB (9)**, which are adjacent package pins |
| `xoClkFpga` | U9.OUT → R41 (100R) → out — high-impedance tap, FPGA GBIN only, **also the ADC data-capture clock** (§1.4.1) |
| `GND` | U9.GND, U9.OE tied to `vXo3V3` (always enabled) |

#### 3.7.1 D3 fan-out check — three loads on one XO, no buffer required

| Load | Branch | C_in | Source |
|---|---|---|---|
| U7.CLKA (pin 8) | R40, 33 Ω | 3 pF | LTC2292 "LOGIC INPUTS (CLK, OE, SHDN, MUX)", C_IN = 3 pF typ [VERIFIED-PDF] |
| U7.CLKB (pin 9) | R40, 33 Ω (same net) | 3 pF | same row |
| FPGA GBIN | R41, 100 Ω | 6 pF | iCE40 "I/O Capacitance" = 6 pF typ [VERIFIED-PDF] |
| | | **12 pF + ~2 pF trace** | |

A 3225 CMOS XO is specified into a 15 pF load; **~14 pF total is inside that**, so no fan-out
buffer is added. Dynamic drive current is C·V·f = 14 pF × 3.3 V × 40 MHz ≈ **1.9 mA average** —
trivial for any CMOS XO output. The two branches remain independently series-terminated so the
FPGA branch cannot reflect into the encode net.

**Adding a fan-out buffer would be actively harmful here**, not merely unnecessary: any buffer
inserts its own additive phase jitter directly into the ADC's aperture, and D2 has already
identified XO jitter as the largest unquantified term in the noise budget. The XO drives the
encode pins directly.

**Residual risk, flagged not dismissed:** the populated YXC OT322540MJBA4SL has no published
drive/load specification either (its PDF reports 0 pages — see `datasheets/SUMMARY.md` §3), so
the 15 pF figure is the *class* specification for 3225 CMOS XOs, an **[UNVERIFIED] inference**,
not this part's datasheet number. It is checked at bring-up alongside the jitter measurement
(D2): scope the encode edge at U7 and confirm rise/fall < 3 ns and full-rail swing.

### 3.8 `fpga_ice40`

| Net | Connected parts / pins |
|---|---|
| `V1V2_CORE` | U10.VCC ×4 (bank core), 100 n each + 10 µF bulk |
| `V3V3_D` | U10.VCCIO_0/1/2/3 (all banks at 3.3 V), 100 n per pin + 10 µF; U10.VPP_2V5 (2.30–3.47 V range ⇒ 3.3 V is legal); U10.VCC_SPI |
| `V1V2_CORE` filtered | U10.VCCPLL via R50 (10R) + C90 (100 n) + C91 (10 µF) *(PLL unused but must be powered/filtered)* |
| `xoClkFpga`, `ftClk60` | must land on **GBIN** pins (global clock inputs). Only **two** GBINs are now needed, not three. Available on TQ144: GBIN0=129, GBIN1=128, GBIN2=94, GBIN3=93, GBIN4=52, GBIN5=49, GBIN6=21, GBIN7=20. `xoClkFpga` clocks the ADC input registers on its **FALLING** edge (§1.4.1) as well as the logic core. |
| `adcDataA/B`, `adcOfA/B`, `adcShdn`, `adcOeBar` | 26 general I/O. The 24 data + 2 OF inputs **must be captured in PIO input registers clocked by the `xoClkFpga` global buffer, on the falling edge** (§1.4.1). |
| `sramAddr[0:20]`, `sramData[0:15]`, `sramCeBar/OeBar/WeBar` | 40 general I/O |
| `fifoData[0:7]`, `fifoRxfBar`, `fifoTxeBar`, `fifoRdBar`, `fifoWrBar`, `fifoOeBar` | 13 general I/O |
| `cfgSck/cfgMosi/cfgMiso/cfgCsBar` | bank-3 SPI config pins (reusable post-config) |
| `fpgaCresetBar` | U10.CRESET_B, R51 10k pull-up |
| `fpgaCdone` | U10.CDONE, R52 10k pull-up |
| `modeStrap` | 1 I/O, R53 10k pull-up |
| `probeCompDrv`, `extTrig`, `ledStatus`, `ledActivity` | 4 I/O |

### 3.9 `sram_buffer`

| Net | Connected parts / pins |
|---|---|
| `V3V3_D` | U11.VDD ×2, C120–C122 (100 n each, at each VDD pin) + C123 (10 µF) |
| `sramAddr[0:20]` | U11.A0..A20 |
| `sramData[0:15]` | U11.IO0..IO15 |
| `sramCeBar`,`sramOeBar`,`sramWeBar` | U11.CE#, OE#, WE# |
| `GND` | U11.GND, U11.UB#, U11.LB# (tied low — all accesses are 16-bit) |

### 3.10 `config_flash`

| Net | Connected parts / pins |
|---|---|
| `V3V3_D` | U12(W25Q32JV).VCC + C125 (100 n); U12.WP#, U12.HOLD# tied high via R60,R61 (10k) |
| `cfgSck` | U12.CLK via R62 (100R) |
| `cfgMosi` | U12.DI via R63 (100R) |
| `cfgMiso` | U12.DO via R64 (100R) |
| `cfgCsBar` | U12.CS# via R65 (100R); 10k pull-up |
| `modeStrap` | JP1 (TH 1×3 header) — pos 1 = self-boot from flash, pos 2 = MPSSE override; centre pin → `modeStrap` |
| `fpgaCresetBar`, `fpgaCdone` | pass-through to `usb_bridge_ft2232h` / `fpga_ice40` |

### 3.11 `usb_bridge_ft2232h`

| Net | Connected parts / pins |
|---|---|
| `V3V3_D` | U13(FT2232HL).VCCIO ×4, VREGIN, VPLL (via L9 ferrite + 100 n), VPHY (via L10 ferrite + 100 n); 100 n at every pin |
| *(internal)* `vCore1V8` | U13.VREGOUT → C130 (100 n) + C131 (4.7 µF) → U13.VCORE ×4 |
| `usbDp`,`usbDm` | U13.USBDP, USBDM (10 µF/100 n on VPHY; 12 kΩ REF resistor R70 on U13.REF to GND) |
| — | Y1 12 MHz crystal + C132/C133 (27 pF) on U13.OSCI/OSCO — **its own crystal, not shared** |
| `ftResetBar` | U13.RESET# + R71 (10k) pull-up + C134 (100 n) |
| — | U14 (93LC66B) EEPROM: CS←U13.EECS, CLK←U13.EECLK, DI←U13.EEDATA, DO→U13.EEDATA via R72 (2.2k), DO pull-up R73 (10k) to V3V3_D — **per FT2232H datasheet §3.3.** This EEPROM holds the per-board calibration constants (SPEC §2.1). |
| `fifoData[0:7]` | U13.ADBUS0..7 |
| `fifoRxfBar`,`fifoTxeBar` | U13.ADBUS4? → **use the FT2232H sync-245 pin map**: RXF#=ACBUS0, TXE#=ACBUS1, RD#=ACBUS2, WR#=ACBUS3, OE#=ACBUS6, SIWU#=ACBUS7 (pull high) |
| `ftClk60` | U13.ACBUS5 (CLKOUT, 60 MHz) |
| `cfgSck/cfgMosi/cfgMiso/cfgCsBar` | U13.BDBUS0/1/2/3 (MPSSE) |
| `fpgaCresetBar` | U13.BDBUS4 |
| `fpgaCdone` | U13.BDBUS5 |
| — | U13.PWRSAV# pulled high; U13.TEST tied to GND |

### 3.12 `aux_io`

| Net | Connected parts / pins |
|---|---|
| `probeCompDrv` | FPGA pin → R90 (2.32k 1%) → `probeCompOut`; R91 (1.00k 1%) from `probeCompOut` to GND ⇒ 1.00 V p-p, Zout = 699 Ω |
| — | J4 = 2-pin TH terminal: `probeCompOut` + `GND` |
| `extTrig` | FPGA pin ↔ R92 (100R) ↔ `extTrigPin`; D10 (BAT54S) clamp to V3V3_D/GND; R93 (10k) pull-down; D11 (PESD3V3) ESD |
| — | J5 = 1×3 TH header: `extTrigPin`, `GND`, `GND` |
| `ledStatus` | R94 (1k) → D12 (green LED) → GND |
| `ledActivity` | R95 (1k) → D13 (amber LED) → GND |

---

## 4. Interface-count sanity check (FPGA)

| Group | Pins |
|---|---|
| ADC data A + B | 24 |
| ADC OFA, OFB | 2 |
| ADC SHDN, OE# | 2 |
| SRAM A0–A20 | 21 |
| SRAM DQ0–DQ15 | 16 |
| SRAM CE#, OE#, WE# | 3 |
| FT2232H FIFO data | 8 |
| FT2232H RXF#, TXE#, RD#, WR#, OE# | 5 |
| FT2232H CLKOUT 60 MHz (GBIN) | 1 |
| XO 40 MHz tap (GBIN) — system **and** ADC capture clock | 1 |
| probe comp, ext trig, mode strap | 3 |
| LEDs ×2 | 2 |
| spare / debug | 4 |
| **General I/O** | **92** |
| SPI config (SPI_SCK/SI/SO/SS_B — reusable post-config) | 4 |
| CRESET_B, CDONE (dedicated) | 2 |
| **Total committed of 107 available on TQ144** | **98 (9 spare)** — one pin freed by deleting `adcClkOut` |

Verdict in `ic_selection.md` §2. All four I/O banks run at **VCCIO = 3.3 V** — no mixed-voltage
bank problem, and `VCC_SPI` = 3.3 V matches the W25Q32JV.
